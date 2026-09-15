# Deploy Tysa Dessert ke Internet

## Opsi 1: Railway (Rekomendasi, gratis, Flask+MySQL langsung jadi)

1. Push project ke GitHub:
   ```
   cd D:\Sandy\Data\umkm-landing
   git init
   git add .
   git commit -m "Tysa Dessert"
   git branch -M main
   gh repo create tysa-dessert --public --source=. --push
   ```
2. Buka https://railway.app → New Project → Deploy from GitHub → pilih repo
3. Railway auto-detect Procfile (Flask via gunicorn)
4. Tambah MySQL: New → Database → MySQL → copy ENV:
   - `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_NAME` (dari Railway Variables)
5. Set Variables di Service Flask: `ADMIN_USER=admin`, `ADMIN_PASS=tysa123`, `PORT=3000`
6. Deploy → dapat URL `https://xxx.up.railway.app` → buka `/admin` untuk rekap
7. Import DB awal: Railway MySQL → Data → Query → paste `database/schema.sql` versi MySQL (atau `C:\Users\sandy\AppData\Local\Temp\opencode\mysql_schema.sql`)

## Opsi 2: Render

1. Push ke GitHub seperti di atas
2. https://dashboard.render.com → New Web Service → Connect repo
3. Build: `pip install -r requirements.txt`, Start: `gunicorn --chdir backend app:app --bind 0.0.0.0:$PORT`
4. Add MySQL: Render tidak ada MySQL gratis, pakai PlanetScale/Neon lalu set ENV DB_*

## Opsi 3: Cepat test tanpa hosting (ngrok)

```
pip install pyngrok
ngrok http 3000
```
Dapat URL https://xxxx.ngrok.io → share ke pembeli, tapi laptop harus nyala

## ENV yang wajib di hosting

```
DB_HOST=xxx.railway.internal
DB_PORT=3306
DB_USER=root
DB_PASS=xxx
DB_NAME=tysa_dessert
ADMIN_USER=admin
ADMIN_PASS=tysa123
PORT=3000
```

## Cek setelah deploy

- Landing: https://xxx.up.railway.app/
- Admin: https://xxx.up.railway.app/admin (login admin/tysa123)
- API: https://xxx.up.railway.app/api/produk
