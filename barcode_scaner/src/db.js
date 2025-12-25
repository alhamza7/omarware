const fs = require("fs");
const path = require("path");
const Database = require("better-sqlite3");
const { DB_PATH } = require("./config");

function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true });
}

function openDb() {
  ensureDir(path.dirname(DB_PATH));
  const db = new Database(DB_PATH);
  db.pragma("journal_mode = WAL");
  return db;
}

function migrate(db) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'user',
      warehouse_id INTEGER NOT NULL DEFAULT 1,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      item_code TEXT UNIQUE NOT NULL,
      item_name TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS barcodes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      item_id INTEGER NOT NULL,
      barcode TEXT NOT NULL,
      uom TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      UNIQUE(item_id, barcode),
      FOREIGN KEY(item_id) REFERENCES items(id)
    );

    CREATE TABLE IF NOT EXISTS counts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      item_id INTEGER NOT NULL,
      user_id INTEGER NOT NULL,
      warehouse_id INTEGER NOT NULL DEFAULT 1,
      qty REAL NOT NULL,
      note TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY(item_id) REFERENCES items(id),
      FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE INDEX IF NOT EXISTS idx_items_code ON items(item_code);
    CREATE INDEX IF NOT EXISTS idx_items_name ON items(item_name);
    CREATE INDEX IF NOT EXISTS idx_barcodes_barcode ON barcodes(barcode);
    CREATE INDEX IF NOT EXISTS idx_counts_item ON counts(item_id);
  `);

  // إضافة عمود المخزن في حال كانت قاعدة البيانات قديمة
  const cols = db.prepare("PRAGMA table_info(counts)").all();
  const hasWarehouse = cols.some((c) => c && c.name === "warehouse_id");
  if (!hasWarehouse) {
    db.exec("ALTER TABLE counts ADD COLUMN warehouse_id INTEGER NOT NULL DEFAULT 1;");
  }
  db.exec("CREATE INDEX IF NOT EXISTS idx_counts_wh_item ON counts(warehouse_id, item_id);");

  // إضافة عمود مخزن افتراضي للمستخدم في حال كانت قاعدة البيانات قديمة
  const userCols = db.prepare("PRAGMA table_info(users)").all();
  const userHasWarehouse = userCols.some((c) => c && c.name === "warehouse_id");
  if (!userHasWarehouse) {
    db.exec("ALTER TABLE users ADD COLUMN warehouse_id INTEGER NOT NULL DEFAULT 1;");
  }

  // إضافة عمود barcode_id للجرد (كل باركود له سجل منفصل)
  const countCols = db.prepare("PRAGMA table_info(counts)").all();
  const hasBarcodeId = countCols.some((c) => c && c.name === "barcode_id");
  if (!hasBarcodeId) {
    db.exec("ALTER TABLE counts ADD COLUMN barcode_id INTEGER;");
    db.exec("CREATE INDEX IF NOT EXISTS idx_counts_barcode ON counts(barcode_id);");
  }

  // إضافة أعمدة SAP لحفظ الكميات وقت الجرد
  const hasSapQty = countCols.some((c) => c && c.name === "sap_qty");
  if (!hasSapQty) {
    db.exec("ALTER TABLE counts ADD COLUMN sap_qty REAL;");
  }
  
  const hasSapCommitted = countCols.some((c) => c && c.name === "sap_committed");
  if (!hasSapCommitted) {
    db.exec("ALTER TABLE counts ADD COLUMN sap_committed REAL;");
  }
  
  const hasSapAvailable = countCols.some((c) => c && c.name === "sap_available");
  if (!hasSapAvailable) {
    db.exec("ALTER TABLE counts ADD COLUMN sap_available REAL;");
  }

  // إضافة عمود الاسم الكامل للمستخدمين
  const userCols2 = db.prepare("PRAGMA table_info(users)").all();
  const hasFullName = userCols2.some((c) => c && c.name === "full_name");
  if (!hasFullName) {
    db.exec("ALTER TABLE users ADD COLUMN full_name TEXT;");
  }

  // إضافة أعمدة الوحدات المتعددة للجرد
  const countCols2 = db.prepare("PRAGMA table_info(counts)").all();
  
  const hasQtyPieces = countCols2.some((c) => c && c.name === "qty_pieces");
  if (!hasQtyPieces) {
    db.exec("ALTER TABLE counts ADD COLUMN qty_pieces REAL DEFAULT 0;");
  }
  
  const hasQtyDozen = countCols2.some((c) => c && c.name === "qty_dozen");
  if (!hasQtyDozen) {
    db.exec("ALTER TABLE counts ADD COLUMN qty_dozen REAL DEFAULT 0;");
  }
  
  const hasQtyCarton = countCols2.some((c) => c && c.name === "qty_carton");
  if (!hasQtyCarton) {
    db.exec("ALTER TABLE counts ADD COLUMN qty_carton REAL DEFAULT 0;");
  }
  
  const hasQtyTotal = countCols2.some((c) => c && c.name === "qty_total");
  if (!hasQtyTotal) {
    db.exec("ALTER TABLE counts ADD COLUMN qty_total REAL DEFAULT 0;");
  }
}

module.exports = { openDb, migrate };


