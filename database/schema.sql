-- Database Tysa Dessert - Rekap Pesanan
-- SQLite - jalankan: sqlite3 tysa.db < schema.sql
PRAGMA foreign_keys = ON;

-- 1. Pelanggan / Pemesan
CREATE TABLE IF NOT EXISTS pelanggan (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nama TEXT NOT NULL,
  hp TEXT,
  alamat TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Produk (7 menu Tysa Dessert x Segokolet)
CREATE TABLE IF NOT EXISTS produk (
  id INTEGER PRIMARY KEY,
  nama TEXT NOT NULL,
  harga INTEGER NOT NULL,
  kategori TEXT NOT NULL, -- salad / segar / nasi
  aktif INTEGER DEFAULT 1
);

-- 3. Pesanan (header)
CREATE TABLE IF NOT EXISTS pesanan (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pelanggan_id INTEGER NOT NULL,
  tanggal DATETIME DEFAULT (datetime('now','localtime')),
  total INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending', -- pending, lunas, dikirim, selesai, batal
  metode_bayar TEXT DEFAULT 'COD', -- COD, Transfer, QRIS
  catatan TEXT,
  created_at DATETIME DEFAULT (datetime('now','localtime')),
  FOREIGN KEY (pelanggan_id) REFERENCES pelanggan(id)
);

-- 4. Detail Pesanan (items)
CREATE TABLE IF NOT EXISTS pesanan_item (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pesanan_id INTEGER NOT NULL,
  produk_id INTEGER NOT NULL,
  qty INTEGER NOT NULL,
  harga_satuan INTEGER NOT NULL,
  subtotal INTEGER NOT NULL,
  FOREIGN KEY (pesanan_id) REFERENCES pesanan(id) ON DELETE CASCADE,
  FOREIGN KEY (produk_id) REFERENCES produk(id)
);

-- Index untuk laporan cepat
CREATE INDEX IF NOT EXISTS idx_pesanan_tanggal ON pesanan(tanggal);
CREATE INDEX IF NOT EXISTS idx_pesanan_status ON pesanan(status);
CREATE INDEX IF NOT EXISTS idx_item_pesanan ON pesanan_item(pesanan_id);
CREATE INDEX IF NOT EXISTS idx_item_produk ON pesanan_item(produk_id);

-- Seed Produk Tysa Dessert
INSERT OR REPLACE INTO produk (id, nama, harga, kategori) VALUES
(1, 'Salad Buah Premium', 25000, 'salad'),
(2, 'Salad Sayur (Veggie Salad)', 22000, 'salad'),
(3, 'Asinan Buah Segar', 20000, 'segar'),
(4, 'Puding Tysa Lumer', 15000, 'segar'),
(5, 'Sop Buah Tropical', 18000, 'segar'),
(6, 'Kimbab Segokolet', 20000, 'nasi'),
(7, 'Nasi Kulit Segokolet', 15000, 'nasi');

-- Contoh data dummy untuk testing laporan (hapus jika tidak perlu)
-- Pelanggan dummy
INSERT OR IGNORE INTO pelanggan (id, nama, hp, alamat) VALUES
(1, 'Dinda', '081234567890', 'Surabaya'),
(2, 'Sinta', '082345678901', 'Sidoarjo'),
(3, 'Andi', '083456789012', 'Gresik');

-- Pesanan dummy bulan ini
INSERT OR IGNORE INTO pesanan (id, pelanggan_id, tanggal, total, status, metode_bayar) VALUES
(1, 1, datetime('now','localtime'), 50000, 'selesai', 'QRIS'),
(2, 2, datetime('now','localtime','-1 day'), 43000, 'selesai', 'Transfer'),
(3, 3, datetime('now','start of month','+5 days'), 35000, 'selesai', 'COD');

INSERT OR IGNORE INTO pesanan_item (pesanan_id, produk_id, qty, harga_satuan, subtotal) VALUES
(1, 1, 2, 25000, 50000),
(2, 3, 1, 20000, 20000),
(2, 4, 1, 15000, 15000),
(2, 6, 1, 20000, 8000), -- contoh diskon
(3, 7, 1, 15000, 15000),
(3, 5, 1, 18000, 18000);

-- ================= VIEW & QUERY LAPORAN =================

-- VIEW rekap harian (bisa dipakai: SELECT * FROM v_laporan_harian;)
CREATE VIEW IF NOT EXISTS v_laporan_harian AS
SELECT 
  date(tanggal) as tanggal,
  COUNT(*) as jumlah_pesanan,
  SUM(total) as omzet,
  SUM(CASE WHEN status='batal' THEN 0 ELSE 1 END) as pesanan_valid
FROM pesanan
WHERE status != 'batal'
GROUP BY date(tanggal)
ORDER BY tanggal DESC;

-- VIEW rekap bulanan
CREATE VIEW IF NOT EXISTS v_laporan_bulanan AS
SELECT 
  strftime('%Y-%m', tanggal) as bulan,
  COUNT(*) as jumlah_pesanan,
  SUM(total) as omzet
FROM pesanan
WHERE status != 'batal'
GROUP BY strftime('%Y-%m', tanggal)
ORDER BY bulan DESC;

-- VIEW rekap tahunan
CREATE VIEW IF NOT EXISTS v_laporan_tahunan AS
SELECT 
  strftime('%Y', tanggal) as tahun,
  COUNT(*) as jumlah_pesanan,
  SUM(total) as omzet
FROM pesanan
WHERE status != 'batal'
GROUP BY strftime('%Y', tanggal)
ORDER BY tahun DESC;

-- VIEW produk terlaris
CREATE VIEW IF NOT EXISTS v_produk_terlaris AS
SELECT 
  p.nama,
  p.kategori,
  SUM(pi.qty) as total_qty,
  SUM(pi.subtotal) as total_omzet,
  COUNT(DISTINCT pi.pesanan_id) as jumlah_transaksi
FROM pesanan_item pi
JOIN produk p ON p.id = pi.produk_id
JOIN pesanan ps ON ps.id = pi.pesanan_id
WHERE ps.status != 'batal'
GROUP BY p.id
ORDER BY total_qty DESC;
