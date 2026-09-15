from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pathlib
import secrets
from functools import wraps
import pymysql
import pymysql.cursors
import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "tysa_dessert"),
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": False,
    "charset": "utf8mb4"
}

app = Flask(__name__, static_folder="../")
CORS(app)

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "tysa123")
tokens = {}

def get_db():
    return pymysql.connect(**DB_CONFIG)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "").strip()
        if token not in tokens:
            return jsonify({"error": "Unauthorized - login dulu"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    u = data.get("username","")
    p = data.get("password","")
    if u == ADMIN_USER and p == ADMIN_PASS:
        token = secrets.token_hex(16)
        tokens[token] = u
        return jsonify({"ok": True, "token": token, "user": u})
    return jsonify({"ok": False, "error": "Username / password salah"}), 401

@app.route("/api/logout", methods=["POST"])
def logout():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    tokens.pop(token, None)
    return jsonify({"ok": True})

@app.route("/api/check-auth")
def check_auth():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    return jsonify({"ok": token in tokens})

@app.route("/api/produk")
def api_produk():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM produk WHERE aktif=1")
            rows = cur.fetchall()
    finally:
        conn.close()
    return jsonify(rows)

@app.route("/api/pesanan", methods=["GET", "POST"])
def api_pesanan():
    if request.method == "GET":
        auth = request.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "").strip()
        if token not in tokens:
            return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    try:
        if request.method == "POST":
            data = request.get_json()
            nama = data.get("nama")
            hp = data.get("hp","")
            alamat = data.get("alamat","")
            items = data.get("items", [])
            metode = data.get("metode_bayar","COD")
            catatan = data.get("catatan","")
            if not nama or not items:
                return jsonify({"error":"nama dan items wajib"}), 400
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM pelanggan WHERE hp=%s AND hp!='' LIMIT 1", (hp,))
                row = cur.fetchone()
                if row and hp:
                    pelanggan_id = row["id"]
                    cur.execute("UPDATE pelanggan SET nama=%s, alamat=%s WHERE id=%s", (nama, alamat, pelanggan_id))
                else:
                    cur.execute("INSERT INTO pelanggan (nama,hp,alamat) VALUES (%s,%s,%s)", (nama,hp,alamat))
                    pelanggan_id = cur.lastrowid
                total = 0
                for it in items:
                    cur.execute("SELECT harga FROM produk WHERE id=%s", (it["produk_id"],))
                    prod = cur.fetchone()
                    if not prod: continue
                    harga = prod["harga"]
                    subtotal = harga * int(it["qty"])
                    total += subtotal
                cur.execute("INSERT INTO pesanan (pelanggan_id,total,status,metode_bayar,catatan) VALUES (%s,%s,%s,%s,%s)",
                            (pelanggan_id,total,"pending",metode,catatan))
                pesanan_id = cur.lastrowid
                for it in items:
                    cur.execute("SELECT harga FROM produk WHERE id=%s", (it["produk_id"],))
                    prod = cur.fetchone()
                    if not prod: continue
                    harga = prod["harga"]
                    qty = int(it["qty"])
                    subtotal = harga * qty
                    cur.execute("INSERT INTO pesanan_item (pesanan_id,produk_id,qty,harga_satuan,subtotal) VALUES (%s,%s,%s,%s,%s)",
                                (pesanan_id, it["produk_id"], qty, harga, subtotal))
                conn.commit()
                return jsonify({"ok":True, "pesanan_id": pesanan_id, "total": total})
        else:
            status = request.args.get("status")
            with conn.cursor() as cur:
                q = "SELECT pesanan.*, pelanggan.nama as pelanggan_nama, pelanggan.hp FROM pesanan JOIN pelanggan ON pelanggan.id=pesanan.pelanggan_id"
                params=[]
                if status:
                    q += " WHERE pesanan.status=%s"
                    params.append(status)
                q += " ORDER BY pesanan.tanggal DESC LIMIT 100"
                cur.execute(q, params)
                rows = cur.fetchall()
                result=[]
                for r in rows:
                    cur.execute("SELECT pesanan_item.*, produk.nama as produk_nama FROM pesanan_item JOIN produk ON produk.id=pesanan_item.produk_id WHERE pesanan_id=%s", (r["id"],))
                    items = cur.fetchall()
                    r["items"]=items
                    # serialize datetime
                    for k in ["tanggal","created_at"]:
                        if r.get(k): r[k]=str(r[k])
                    for it in r["items"]:
                        pass
                    result.append(r)
                return jsonify(result)
    finally:
        conn.close()

@app.route("/api/pesanan/<int:pid>/status", methods=["PUT"])
@require_auth
def update_status(pid):
    data=request.get_json()
    status=data.get("status")
    if status not in ["pending","lunas","dikirim","selesai","batal"]:
        return jsonify({"error":"status tidak valid"}),400
    conn=get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE pesanan SET status=%s WHERE id=%s", (status,pid))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok":True})

@app.route("/api/laporan/harian")
@require_auth
def lap_harian():
    d_from = request.args.get("from")
    d_to = request.args.get("to")
    conn=get_db()
    try:
        with conn.cursor() as cur:
            q="SELECT DATE(tanggal) as tanggal, COUNT(*) as jumlah_pesanan, SUM(total) as omzet FROM pesanan WHERE status!='batal'"
            params=[]
            if d_from:
                q+=" AND DATE(tanggal) >= %s"; params.append(d_from)
            if d_to:
                q+=" AND DATE(tanggal) <= %s"; params.append(d_to)
            q+=" GROUP BY DATE(tanggal) ORDER BY tanggal DESC"
            cur.execute(q,params)
            rows=cur.fetchall()
            for r in rows:
                r["tanggal"]=str(r["tanggal"])
                r["omzet"]=int(r["omzet"] or 0)
            return jsonify(rows)
    finally:
        conn.close()

@app.route("/api/laporan/bulanan")
@require_auth
def lap_bulanan():
    year=request.args.get("year")
    conn=get_db()
    try:
        with conn.cursor() as cur:
            q="SELECT DATE_FORMAT(tanggal, '%%Y-%%m') as bulan, COUNT(*) as jumlah_pesanan, SUM(total) as omzet FROM pesanan WHERE status!='batal'"
            params=[]
            if year:
                q+=" AND DATE_FORMAT(tanggal, '%%Y')=%s"; params.append(year)
            q+=" GROUP BY DATE_FORMAT(tanggal, '%%Y-%%m') ORDER BY bulan DESC"
            cur.execute(q,params)
            rows=cur.fetchall()
            for r in rows: r["omzet"]=int(r["omzet"] or 0)
            return jsonify(rows)
    finally:
        conn.close()

@app.route("/api/laporan/tahunan")
@require_auth
def lap_tahunan():
    conn=get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DATE_FORMAT(tanggal, '%%Y') as tahun, COUNT(*) as jumlah_pesanan, SUM(total) as omzet FROM pesanan WHERE status!='batal' GROUP BY DATE_FORMAT(tanggal, '%%Y') ORDER BY tahun DESC")
            rows=cur.fetchall()
            for r in rows: r["omzet"]=int(r["omzet"] or 0)
            return jsonify(rows)
    finally:
        conn.close()

@app.route("/api/laporan/produk")
@require_auth
def lap_produk():
    d_from=request.args.get("from")
    d_to=request.args.get("to")
    conn=get_db()
    try:
        with conn.cursor() as cur:
            q="""SELECT p.id, p.nama, p.kategori, SUM(pi.qty) as total_qty, SUM(pi.subtotal) as total_omzet
                 FROM pesanan_item pi JOIN produk p ON p.id=pi.produk_id JOIN pesanan ps ON ps.id=pi.pesanan_id
                 WHERE ps.status!='batal'"""
            params=[]
            if d_from:
                q+=" AND DATE(ps.tanggal) >= %s"; params.append(d_from)
            if d_to:
                q+=" AND DATE(ps.tanggal) <= %s"; params.append(d_to)
            q+=" GROUP BY p.id ORDER BY total_qty DESC"
            cur.execute(q,params)
            rows=cur.fetchall()
            for r in rows:
                r["total_qty"]=int(r["total_qty"] or 0)
                r["total_omzet"]=int(r["total_omzet"] or 0)
            return jsonify(rows)
    finally:
        conn.close()

@app.route("/api/laporan/ringkas")
@require_auth
def lap_ringkas():
    conn=get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as j, COALESCE(SUM(total),0) as omzet FROM pesanan WHERE DATE(tanggal)=CURDATE() AND status!='batal'")
            harian=cur.fetchone()
            cur.execute("SELECT COUNT(*) as j, COALESCE(SUM(total),0) as omzet FROM pesanan WHERE DATE_FORMAT(tanggal,'%Y-%m')=DATE_FORMAT(CURDATE(),'%Y-%m') AND status!='batal'")
            bulanan=cur.fetchone()
            cur.execute("SELECT COUNT(*) as j, COALESCE(SUM(total),0) as omzet FROM pesanan WHERE DATE_FORMAT(tanggal,'%Y')=DATE_FORMAT(CURDATE(),'%Y') AND status!='batal'")
            tahunan=cur.fetchone()
            return jsonify({
                "hari_ini": {"j": int(harian["j"]), "omzet": int(harian["omzet"])},
                "bulan_ini": {"j": int(bulanan["j"]), "omzet": int(bulanan["omzet"])},
                "tahun_ini": {"j": int(tahunan["j"]), "omzet": int(tahunan["omzet"])}
            })
    finally:
        conn.close()

@app.route("/")
def idx():
    return send_from_directory(str(pathlib.Path(__file__).parent.parent), "index.html")

@app.route("/admin")
def admin():
    return send_from_directory(str(pathlib.Path(__file__).parent.parent), "admin.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(str(pathlib.Path(__file__).parent.parent), path)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "3000"))
    try:
        c=get_db()
        c.close()
        print(f"MySQL OK: {DB_CONFIG['database']} @ {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    except Exception as e:
        print("MySQL GAGAL:", e)
    print(f"Login admin -> username: {ADMIN_USER} password: {ADMIN_PASS}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
