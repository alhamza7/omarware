const path = require("path");
const express = require("express");
const cookieParser = require("cookie-parser");
const bcrypt = require("bcryptjs");
const ExcelJS = require("exceljs");
const multer = require("multer");
const fs = require("fs");

// تحميل متغيرات البيئة
require('dotenv').config();

const { PORT } = require("./config");
const { openDb, migrate } = require("./db");
const { signUser, requireAuth, requireAuthApi, requireAdmin, requireAdminPage } = require("./auth");
const sapClient = require("./sap_client");
const sapConfig = require("./sap_config");

const app = express();
const db = openDb();
migrate(db);

// إعداد multer لرفع الملفات
const upload = multer({
  dest: path.join(__dirname, "..", "uploads"),
  limits: { fileSize: 50 * 1024 * 1024 }, // 50MB max
  fileFilter: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    if (ext === '.xlsx' || ext === '.xls') {
      cb(null, true);
    } else {
      cb(new Error('Only Excel files are allowed'));
    }
  }
});

// إنشاء مجلد uploads إذا لم يكن موجوداً
const uploadsDir = path.join(__dirname, "..", "uploads");
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

app.set("views", path.join(__dirname, "..", "views"));
app.set("view engine", "ejs");

app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(cookieParser());
app.use("/static", express.static(path.join(__dirname, "..", "public")));

function getWarehouseId(req) {
  const v = req.cookies && req.cookies.wh;
  const n = Number(v);
  if (!Number.isFinite(n)) return null;
  if (n < 1 || n > 18) return null;
  return n;
}

function getUserWarehouseId(userId) {
  const row = db.prepare("SELECT warehouse_id FROM users WHERE id = ?").get(userId);
  const n = Number(row && row.warehouse_id);
  if (!Number.isFinite(n)) return 1;
  if (n < 1 || n > 18) return 1;
  return n;
}

function ensureWarehouseCookie(req, res) {
  const wh = getWarehouseId(req);
  if (wh) return wh;
  const userId = req.user && req.user.sub;
  if (!userId) return null;
  const uwh = getUserWarehouseId(userId);
  res.cookie("wh", String(uwh), { httpOnly: true, sameSite: "lax" });
  return uwh;
}

function requireWarehouse(req, res, next) {
  // استخدام المخزن المحدد في قاعدة البيانات فقط
  const userId = req.user && req.user.sub;
  if (!userId) return res.redirect("/warehouse");
  
  const wh = getUserWarehouseId(userId);
  req.warehouseId = wh;
  
  return next();
}

function requireWarehouseApi(req, res, next) {
  // استخدام المخزن المحدد في قاعدة البيانات فقط - تجاهل ما يرسله التطبيق
  const userId = req.user && req.user.sub;
  if (!userId) return res.status(400).json({ error: "user_required" });
  
  const wh = getUserWarehouseId(userId);
  req.warehouseId = wh;
  
  return next();
}

app.get("/", requireAuth, (req, res) => {
  res.redirect("/inventory");
});

app.get("/login", (req, res) => {
  res.render("login", { error: null });
});

app.post("/login", (req, res) => {
  const { username, password } = req.body;
  const user = db
    .prepare(
      "SELECT id, username, password_hash, role, warehouse_id FROM users WHERE username = ?"
    )
    .get(String(username || "").trim());

  if (!user) return res.status(401).render("login", { error: "بيانات الدخول غير صحيحة" });
  const ok = bcrypt.compareSync(String(password || ""), user.password_hash);
  if (!ok) return res.status(401).render("login", { error: "بيانات الدخول غير صحيحة" });

  const token = signUser(user);
  res.cookie("auth", token, { httpOnly: true, sameSite: "lax" });
  // اضبط المخزن الافتراضي للمستخدم في الكوكي (لأداء أسرع) أو اطلب اختياره إن لم يكن مضبوطاً
  const uwh = Number(user.warehouse_id);
  if (Number.isFinite(uwh) && uwh >= 1 && uwh <= 18) {
    res.cookie("wh", String(uwh), { httpOnly: true, sameSite: "lax" });
    return res.redirect("/inventory");
  }
  return res.redirect("/warehouse");
});

// API login for mobile apps (returns JWT)
app.post("/api/auth/login", (req, res) => {
  const username = String(req.body.username || "").trim();
  const password = String(req.body.password || "");
  const user = db
    .prepare(
      "SELECT id, username, password_hash, role, warehouse_id FROM users WHERE username = ?"
    )
    .get(username);

  if (!user) return res.status(401).json({ error: "invalid_credentials" });
  const ok = bcrypt.compareSync(password, user.password_hash);
  if (!ok) return res.status(401).json({ error: "invalid_credentials" });

  const token = signUser(user);
  
  // المخزن المحدد من قاعدة البيانات فقط - لا يمكن تغييره من التطبيق
  const actualWarehouse = Number(user.warehouse_id) || 1;
  
  return res.json({
    token,
    user: { id: user.id, username: user.username, role: user.role },
    warehouse_id: actualWarehouse,
    locked_warehouse: true, // علامة أن المخزن مقفل من الإدارة
    warehouse_message: "تم تحديد المخزن من قبل الإدارة"
  });
});

app.post("/logout", (req, res) => {
  res.clearCookie("auth");
  res.redirect("/login");
});

app.get("/inventory", requireAuth, (req, res) => {
  const wh = ensureWarehouseCookie(req, res);
  if (!wh) return res.redirect("/warehouse");
  res.render("inventory", { username: req.user.username, warehouseId: wh, userRole: req.user.role });
});

app.get("/reports", requireAuth, (req, res) => {
  const wh = ensureWarehouseCookie(req, res);
  if (!wh) return res.redirect("/warehouse");
  res.render("reports", { username: req.user.username, warehouseId: wh, userRole: req.user.role });
});

app.get("/admin", requireAuth, requireAdminPage, (req, res) => {
  const wh = ensureWarehouseCookie(req, res);
  if (!wh) return res.redirect("/warehouse");
  res.render("admin", { username: req.user.username, warehouseId: wh });
});

app.get("/items/:id", requireAuth, (req, res) => {
  const wh = ensureWarehouseCookie(req, res);
  if (!wh) return res.redirect("/warehouse");
  const id = Number(req.params.id);
  if (!Number.isFinite(id)) return res.status(400).send("invalid id");
  const item = db
    .prepare("SELECT id, item_code, item_name FROM items WHERE id = ?")
    .get(id);
  if (!item) return res.status(404).send("not found");
  res.render("item", { username: req.user.username, warehouseId: wh, item });
});

app.get("/warehouse", requireAuth, (req, res) => {
  const current = ensureWarehouseCookie(req, res);
  res.render("warehouse", { username: req.user.username, currentWarehouseId: current });
});

app.post("/warehouse/select", requireAuth, (req, res) => {
  const wh = Number(req.body.warehouse_id);
  if (!Number.isFinite(wh) || wh < 1 || wh > 18) return res.redirect("/warehouse");
  // حفظ دائم للمستخدم + حفظ كوكي للأداء
  db.prepare("UPDATE users SET warehouse_id = ? WHERE id = ?").run(wh, req.user.sub);
  res.cookie("wh", String(wh), { httpOnly: true, sameSite: "lax" });
  res.redirect("/inventory");
});

// API: get current user settings (mobile)
app.get("/api/me", requireAuthApi, (req, res) => {
  const row = db
    .prepare("SELECT id, username, role, warehouse_id, full_name FROM users WHERE id = ?")
    .get(req.user.sub);
  if (!row) return res.status(404).json({ error: "not_found" });
  
  const actualWarehouse = Number(row.warehouse_id) || 1;
  
  res.json({
    user: { 
      id: row.id, 
      username: row.username, 
      role: row.role,
      full_name: row.full_name 
    },
    warehouse_id: actualWarehouse,
    locked_warehouse: true, // المخزن مقفل من الإدارة
    warehouse_message: "المخزن محدد من قبل الإدارة ولا يمكن تغييره"
  });
});

// API: update warehouse (mobile) - سيتم التحديث في DB لكن التطبيق سيستخدم دائماً المخزن المحدد
app.post("/api/me/warehouse", requireAuthApi, (req, res) => {
  const wh = Number(req.body.warehouse_id);
  if (!Number.isFinite(wh) || wh < 1 || wh > 18) {
    return res.status(400).json({ error: "invalid_warehouse" });
  }
  
  // تحديث في قاعدة البيانات
  db.prepare("UPDATE users SET warehouse_id = ? WHERE id = ?").run(wh, req.user.sub);
  
  // إرجاع المخزن المحدد في DB (الذي سيتم استخدامه دائماً)
  const actualWarehouse = getUserWarehouseId(req.user.sub);
  
  res.json({ 
    ok: true, 
    warehouse_id: actualWarehouse,
    message: "تم تحديث المخزن المحدد لك من قبل الإدارة"
  });
});

// API: search by code or name (partial) - returns barcodes too + last count info
app.get("/api/items/search", requireAuthApi, requireWarehouseApi, (req, res) => {
  const q = String(req.query.q || "").trim();
  if (!q) return res.json({ items: [] });
  const wh = req.warehouseId;

  const items = db
    .prepare(
      `
      SELECT DISTINCT i.id, i.item_code, i.item_name, 
             NULL as barcode_id, 
             NULL as barcode,
             (SELECT b2.uom FROM barcodes b2 WHERE b2.item_id = i.id LIMIT 1) as uom
      FROM items i
      WHERE i.item_code LIKE ? OR i.item_name LIKE ?
      UNION
      SELECT i.id, i.item_code, i.item_name, b.id as barcode_id, b.barcode, b.uom
      FROM barcodes b
      JOIN items i ON i.id = b.item_id
      WHERE b.barcode LIKE ?
      ORDER BY item_code, barcode
      LIMIT 20
    `
    )
    .all(`%${q}%`, `%${q}%`, `%${q}%`);

  // أضف معلومات آخر جرد لكل نتيجة
  const itemsWithCounts = items.map((it) => {
    let lastCount = null;
    if (it.barcode_id != null) {
      // إذا كان له باركود، ابحث عن آخر جرد لهذا الباركود
      lastCount = db
        .prepare(
          `
          SELECT c.id, c.qty, c.note, c.created_at, u.username
          FROM counts c
          JOIN users u ON u.id = c.user_id
          WHERE c.barcode_id = ? AND c.warehouse_id = ?
          ORDER BY c.id DESC
          LIMIT 1
        `
        )
        .get(it.barcode_id, wh);
    } else {
      // إذا لم يكن له باركود، ابحث عن آخر جرد للصنف (بدون باركود محدد)
      lastCount = db
        .prepare(
          `
          SELECT c.id, c.qty, c.note, c.created_at, u.username
          FROM counts c
          JOIN users u ON u.id = c.user_id
          WHERE c.item_id = ? AND c.warehouse_id = ? AND c.barcode_id IS NULL
          ORDER BY c.id DESC
          LIMIT 1
        `
        )
        .get(it.id, wh);
    }
    return { ...it, lastCount: lastCount || null };
  });

  res.json({ items: itemsWithCounts });
});

// API: get one item by exact barcode/code - returns item info + last count by item_id
app.get("/api/items/by-code/:code", requireAuthApi, requireWarehouseApi, async (req, res) => {
  const code = String(req.params.code || "").trim();
  const wh = req.warehouseId;
  
  // أولاً جرب البحث بالباركود
  const byBarcode = db
    .prepare(
      `
      SELECT i.id, i.item_code, i.item_name, b.id as barcode_id, b.barcode, b.uom
      FROM barcodes b
      JOIN items i ON i.id = b.item_id
      WHERE b.barcode = ?
      LIMIT 1
    `
    )
    .get(code);
  
  if (byBarcode) {
    // ابحث عن آخر جرد لهذا الصنف (item_id) في نفس المخزن - بغض النظر عن الباركود
    const lastCount = db
      .prepare(
        `
        SELECT c.id, c.qty, c.note, c.created_at, u.username,
               c.sap_qty, c.sap_committed, c.sap_available
        FROM counts c
        JOIN users u ON u.id = c.user_id
        WHERE c.item_id = ? AND c.warehouse_id = ?
        ORDER BY c.id DESC
        LIMIT 1
      `
      )
      .get(byBarcode.id, wh);
    
    // جلب الكمية من SAP (إن كان مفعلاً)
    let sapQuantity = null;
    if (sapConfig.SAP_ENABLED) {
      try {
        // البحث بكود الصنف فقط
        sapQuantity = await sapClient.getItemQuantity(byBarcode.item_code, wh);
      } catch (error) {
        console.error('Error fetching SAP quantity:', error.message);
        // نستمر بدون كمية SAP في حالة الخطأ
      }
    }
    
    return res.json({ 
      item: byBarcode,
      lastCount: lastCount || null,
      sapQuantity: sapQuantity || null
    });
  }
  
  // إذا لم يوجد، جرب البحث بالكود
  const byCode = db
    .prepare(`
      SELECT i.id, i.item_code, i.item_name, 
             NULL as barcode_id, 
             NULL as barcode,
             (SELECT b.uom FROM barcodes b WHERE b.item_id = i.id LIMIT 1) as uom
      FROM items i 
      WHERE i.item_code = ?
    `)
    .get(code);
  if (!byCode) return res.status(404).json({ error: "not_found" });
  
  // ابحث عن آخر جرد لهذا الصنف (item_id) في نفس المخزن
  const lastCount = db
    .prepare(
      `
      SELECT c.id, c.qty, c.note, c.created_at, u.username,
             c.sap_qty, c.sap_committed, c.sap_available
      FROM counts c
      JOIN users u ON u.id = c.user_id
      WHERE c.item_id = ? AND c.warehouse_id = ?
      ORDER BY c.id DESC
      LIMIT 1
    `
    )
    .get(byCode.id, wh);
  
  // جلب الكمية من SAP (إن كان مفعلاً)
  let sapQuantity = null;
  if (sapConfig.SAP_ENABLED) {
    try {
      sapQuantity = await sapClient.getItemQuantity(byCode.item_code, wh);
    } catch (error) {
      console.error('Error fetching SAP quantity:', error.message);
    }
  }
  
  res.json({ 
    item: byCode,
    lastCount: lastCount || null,
    sapQuantity: sapQuantity || null
  });
});

// API: save count (inventory qty) - linked to item_code only (not barcode)
app.post("/api/counts", requireAuthApi, requireWarehouseApi, (req, res) => {
  const item_id = Number(req.body.item_id);
  const qty = Number(req.body.qty); // الكمية الإجمالية (للتوافق مع الإصدارات القديمة)
  const note = req.body.note == null ? null : String(req.body.note);
  
  // بيانات الوحدات المتعددة
  const qty_pieces = req.body.qty_pieces != null ? Number(req.body.qty_pieces) : 0;
  const qty_dozen = req.body.qty_dozen != null ? Number(req.body.qty_dozen) : 0;
  const qty_carton = req.body.qty_carton != null ? Number(req.body.qty_carton) : 0;
  
  // حساب الإجمالي بناءً على وحدة القياس
  let qty_total = qty; // القيمة الافتراضية
  
  // إذا كانت هناك وحدات متعددة، احسب الإجمالي
  if (qty_pieces > 0 || qty_dozen > 0 || qty_carton > 0) {
    // 1 درزن = 12 قطعة/باكيت/سيت
    // 1 كارتون = 12 درزن = 144 قطعة
    qty_total = qty_pieces + (qty_dozen * 12) + (qty_carton * 144);
  }
  
  // بيانات SAP (إن وجدت)
  const sap_qty = req.body.sap_qty != null ? Number(req.body.sap_qty) : null;
  const sap_committed = req.body.sap_committed != null ? Number(req.body.sap_committed) : null;
  const sap_available = req.body.sap_available != null ? Number(req.body.sap_available) : null;

  if (!Number.isFinite(item_id)) {
    return res.status(400).json({ error: "invalid_payload" });
  }

  const item = db.prepare("SELECT id FROM items WHERE id = ?").get(item_id);
  if (!item) return res.status(404).json({ error: "item_not_found" });

  // الجرد يُحفظ على مستوى الصنف فقط (barcode_id = null دائماً)
  const r = db
    .prepare(
      `INSERT INTO counts (
        item_id, barcode_id, user_id, warehouse_id, qty, note,
        qty_pieces, qty_dozen, qty_carton, qty_total,
        sap_qty, sap_committed, sap_available
      ) VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
    .run(
      item_id, req.user.sub, req.warehouseId, qty_total, note,
      qty_pieces, qty_dozen, qty_carton, qty_total,
      sap_qty, sap_committed, sap_available
    );

  res.json({ 
    ok: true, 
    id: r.lastInsertRowid,
    qty_total: qty_total
  });
});

// API: get SAP quantity for an item
app.get("/api/sap/item-quantity/:itemCode", requireAuthApi, requireWarehouseApi, async (req, res) => {
  if (!sapConfig.SAP_ENABLED) {
    return res.status(503).json({ 
      error: "sap_disabled", 
      message: "SAP integration is not enabled" 
    });
  }

  const itemCode = String(req.params.itemCode || "").trim();
  const wh = req.warehouseId;

  if (!itemCode) {
    return res.status(400).json({ error: "item_code_required" });
  }

  try {
    const sapQuantity = await sapClient.getItemQuantity(itemCode, wh);
    
    if (!sapQuantity) {
      return res.status(404).json({ 
        error: "not_found_in_sap", 
        message: "Item not found in SAP" 
      });
    }

    res.json({ 
      ok: true, 
      data: sapQuantity 
    });
  } catch (error) {
    console.error('Error fetching SAP quantity:', error);
    res.status(500).json({ 
      error: "sap_error", 
      message: error.message 
    });
  }
});

// API: get SAP quantity by barcode
app.get("/api/sap/item-by-barcode/:barcode", requireAuthApi, requireWarehouseApi, async (req, res) => {
  if (!sapConfig.SAP_ENABLED) {
    return res.status(503).json({ 
      error: "sap_disabled", 
      message: "SAP integration is not enabled" 
    });
  }

  const barcode = String(req.params.barcode || "").trim();
  const wh = req.warehouseId;

  if (!barcode) {
    return res.status(400).json({ error: "barcode_required" });
  }

  try {
    const sapItem = await sapClient.getItemByBarcode(barcode, wh);
    
    if (!sapItem) {
      return res.status(404).json({ 
        error: "not_found_in_sap", 
        message: "Item not found in SAP" 
      });
    }

    res.json({ 
      ok: true, 
      data: sapItem 
    });
  } catch (error) {
    console.error('Error fetching SAP item by barcode:', error);
    res.status(500).json({ 
      error: "sap_error", 
      message: error.message 
    });
  }
});

// API: get SAP connection status
app.get("/api/sap/status", requireAuthApi, (req, res) => {
  res.json({
    enabled: sapConfig.SAP_ENABLED,
    connected: sapClient.sessionId != null,
    serviceLayerUrl: sapConfig.SAP_ENABLED ? sapConfig.SAP_SERVICE_LAYER_URL : null,
  });
});

// API: latest counts for an item
app.get("/api/items/:id/counts", requireAuthApi, requireWarehouseApi, (req, res) => {
  const id = Number(req.params.id);
  if (!Number.isFinite(id)) return res.status(400).json({ error: "invalid_id" });
  const rows = db
    .prepare(
      `
      SELECT c.id, c.qty, c.note, c.created_at, u.username
      FROM counts c
      JOIN users u ON u.id = c.user_id
      WHERE c.item_id = ? AND c.warehouse_id = ?
      ORDER BY c.id DESC
      LIMIT 10
    `
    )
    .all(id, req.warehouseId);
  res.json({ counts: rows });
});

function reportQuery(whereSql, params) {
  // استعلام جديد: كل باركود في سطر منفصل، وإذا لم يكن هناك باركود، الصنف في سطر منفصل
  const wh = params[0]; // warehouse_id هو أول parameter
  const searchQuery = params.length > 1 ? params[1] : null;
  const searchPattern = searchQuery ? searchQuery.replace(/%/g, '') : null;
  
  // بناء استعلام الأصناف
  // params[0] هو warehouse_id ولا نحتاجه في استعلام items
  // المعاملات من params[1] فما بعد هي معاملات البحث
  const queryParams = params.slice(1); // تخطي warehouse_id
  
  let itemsQuery = `
    SELECT DISTINCT i.id, i.item_code, i.item_name
    FROM items i
    ${whereSql}
    ORDER BY i.item_code
    LIMIT 5000
  `;
  
  const items = db.prepare(itemsQuery).all(...queryParams);
  return processItemsForReport(items, wh, searchPattern);
}

function processItemsForReport(items, warehouseId, searchPattern) {
  const results = [];
  
  for (const item of items) {
    // الحصول على جميع الباركودات لهذا الصنف
    const barcodes = db
      .prepare("SELECT id, barcode, uom FROM barcodes WHERE item_id = ? ORDER BY barcode")
      .all(item.id);
    
    if (barcodes.length > 0) {
      // إذا كان للصنف باركودات، عرض كل باركود في سطر منفصل
      for (const barcode of barcodes) {
        // تطبيق البحث على الباركود إذا كان موجوداً
        if (searchPattern && !barcode.barcode.includes(searchPattern)) {
          continue;
        }
        
        const countAgg = db
          .prepare(
            `
            SELECT 
              COUNT(*) AS count_entries,
              MIN(id) AS first_id,
              MAX(id) AS last_id
            FROM counts
            WHERE barcode_id = ? AND warehouse_id = ?
          `
          )
          .get(barcode.id, warehouseId);
        
        const lastCount = countAgg && countAgg.last_id
          ? db
              .prepare(
                `
                SELECT c.qty, c.created_at, u.username,
                       c.sap_qty, c.sap_committed, c.sap_available,
                       c.qty_pieces, c.qty_dozen, c.qty_carton, c.qty_total
                FROM counts c
                JOIN users u ON u.id = c.user_id
                WHERE c.id = ?
              `
              )
              .get(countAgg.last_id)
          : null;
        
        const firstCount = countAgg && countAgg.first_id
          ? db.prepare("SELECT created_at FROM counts WHERE id = ?").get(countAgg.first_id)
          : null;
        
        results.push({
          id: item.id,
          item_code: item.item_code,
          item_name: item.item_name,
          barcode_id: barcode.id,
          barcode: barcode.barcode,
          uom: barcode.uom,
          count_entries: countAgg ? countAgg.count_entries : 0,
          last_qty: lastCount ? lastCount.qty : null,
          qty_pieces: lastCount ? lastCount.qty_pieces : null,
          qty_dozen: lastCount ? lastCount.qty_dozen : null,
          qty_carton: lastCount ? lastCount.qty_carton : null,
          qty_total: lastCount ? lastCount.qty_total : null,
          sap_qty: lastCount ? lastCount.sap_qty : null,
          sap_committed: lastCount ? lastCount.sap_committed : null,
          sap_available: lastCount ? lastCount.sap_available : null,
          last_time: lastCount ? lastCount.created_at : null,
          last_user: lastCount ? lastCount.username : null,
          first_time: firstCount ? firstCount.created_at : null,
        });
      }
      
      // أيضاً، إذا كان هناك جرد للصنف بدون باركود محدد، أضفه كسطر منفصل
      const itemCountAgg = db
        .prepare(
          `
          SELECT 
            COUNT(*) AS count_entries,
            MIN(id) AS first_id,
            MAX(id) AS last_id
          FROM counts
          WHERE item_id = ? AND warehouse_id = ? AND barcode_id IS NULL
        `
        )
        .get(item.id, warehouseId);
      
      if (itemCountAgg && itemCountAgg.count_entries > 0) {
        const lastCount = itemCountAgg.last_id
          ? db
              .prepare(
                `
                SELECT c.qty, c.created_at, u.username,
                       c.sap_qty, c.sap_committed, c.sap_available,
                       c.qty_pieces, c.qty_dozen, c.qty_carton, c.qty_total
                FROM counts c
                JOIN users u ON u.id = c.user_id
                WHERE c.id = ?
              `
              )
              .get(itemCountAgg.last_id)
          : null;
        
        const firstCount = itemCountAgg.first_id
          ? db.prepare("SELECT created_at FROM counts WHERE id = ?").get(itemCountAgg.first_id)
          : null;
        
        results.push({
          id: item.id,
          item_code: item.item_code,
          item_name: item.item_name,
          barcode_id: null,
          barcode: null,
          uom: null,
          count_entries: itemCountAgg.count_entries,
          last_qty: lastCount ? lastCount.qty : null,
          qty_pieces: lastCount ? lastCount.qty_pieces : null,
          qty_dozen: lastCount ? lastCount.qty_dozen : null,
          qty_carton: lastCount ? lastCount.qty_carton : null,
          qty_total: lastCount ? lastCount.qty_total : null,
          sap_qty: lastCount ? lastCount.sap_qty : null,
          sap_committed: lastCount ? lastCount.sap_committed : null,
          sap_available: lastCount ? lastCount.sap_available : null,
          last_time: lastCount ? lastCount.created_at : null,
          last_user: lastCount ? lastCount.username : null,
          first_time: firstCount ? firstCount.created_at : null,
        });
      }
    } else {
      // إذا لم يكن للصنف باركودات، عرض الصنف في سطر واحد
      const countAgg = db
        .prepare(
          `
          SELECT 
            COUNT(*) AS count_entries,
            MIN(id) AS first_id,
            MAX(id) AS last_id
          FROM counts
          WHERE item_id = ? AND warehouse_id = ? AND barcode_id IS NULL
        `
        )
        .get(item.id, warehouseId);
      
      const lastCount = countAgg && countAgg.last_id
        ? db
            .prepare(
              `
              SELECT c.qty, c.created_at, u.username,
                     c.sap_qty, c.sap_committed, c.sap_available,
                     c.qty_pieces, c.qty_dozen, c.qty_carton, c.qty_total
              FROM counts c
              JOIN users u ON u.id = c.user_id
              WHERE c.id = ?
            `
            )
            .get(countAgg.last_id)
        : null;
      
      const firstCount = countAgg && countAgg.first_id
        ? db.prepare("SELECT created_at FROM counts WHERE id = ?").get(countAgg.first_id)
        : null;
      
      results.push({
        id: item.id,
        item_code: item.item_code,
        item_name: item.item_name,
        barcode_id: null,
        barcode: null,
        uom: null,
        count_entries: countAgg ? countAgg.count_entries : 0,
        last_qty: lastCount ? lastCount.qty : null,
        qty_pieces: lastCount ? lastCount.qty_pieces : null,
        qty_dozen: lastCount ? lastCount.qty_dozen : null,
        qty_carton: lastCount ? lastCount.qty_carton : null,
        qty_total: lastCount ? lastCount.qty_total : null,
        sap_qty: lastCount ? lastCount.sap_qty : null,
        sap_committed: lastCount ? lastCount.sap_committed : null,
        sap_available: lastCount ? lastCount.sap_available : null,
        last_time: lastCount ? lastCount.created_at : null,
        last_user: lastCount ? lastCount.username : null,
        first_time: firstCount ? firstCount.created_at : null,
      });
    }
  }
  
  return results;
}

// API: reports summary
app.get("/api/reports/summary", requireAuthApi, requireWarehouseApi, (req, res) => {
  const filter = String(req.query.filter || "all");
  const q = String(req.query.q || "").trim();
  const like = `%${q}%`;

  let where = "WHERE 1=1";
  const params = [req.warehouseId];
  if (q) {
    where +=
      " AND (i.item_code LIKE ? OR i.item_name LIKE ? OR EXISTS (SELECT 1 FROM barcodes b WHERE b.item_id=i.id AND b.barcode LIKE ?))";
    params.push(like, like, like);
  }

  let items = reportQuery(where, params);
  
  // إذا كان الفلتر "counted" أو "all"، تأكد من تضمين جميع الأصناف التي لها جردات في هذا المخزن
  // حتى لو لم تكن في قائمة الأصناف المطابقة للفلتر
  if (filter === "counted" || filter === "all") {
    // الحصول على جميع الأصناف التي لها جردات في هذا المخزن
    const itemsWithCounts = db
      .prepare(
        `
        SELECT DISTINCT i.id, i.item_code, i.item_name
        FROM items i
        INNER JOIN counts c ON c.item_id = i.id
        WHERE c.warehouse_id = ?
        ORDER BY i.item_code
      `
      )
      .all(req.warehouseId);
    
    // معالجة الأصناف التي لها جردات
    const countedItemsData = processItemsForReport(itemsWithCounts, req.warehouseId, null);
    
    // دمج النتائج مع النتائج الحالية (تجنب التكرار)
    const existingKeys = new Set(items.map(i => `${i.id}-${i.barcode_id || 'null'}`));
    for (const item of countedItemsData) {
      const key = `${item.id}-${item.barcode_id || 'null'}`;
      if (!existingKeys.has(key) && item.count_entries > 0) {
        items.push(item);
        existingKeys.add(key);
      }
    }
  }
  
  // تطبيق الفلتر على النتائج
  if (filter === "counted") {
    items = items.filter(item => item.count_entries > 0);
  } else if (filter === "remaining") {
    items = items.filter(item => item.count_entries === 0);
  }

  // حساب الإحصائيات بشكل صحيح
  // إجمالي الأصناف: عدد جميع الأصناف في قاعدة البيانات
  const total = db.prepare("SELECT COUNT(*) as count FROM items").get().count;
  
  // الأصناف المجرودة: عدد الأصناف التي لها جردات في هذا المخزن
  const countedItemsCount = db
    .prepare(
      `
      SELECT COUNT(DISTINCT item_id) as count
      FROM counts
      WHERE warehouse_id = ?
    `
    )
    .get(req.warehouseId).count;
  
  // الأصناف المتبقية: إجمالي - مجرودة
  const remaining = total - countedItemsCount;
  
  // الأصناف المعدلة: عدد الأصناف/الباركودات التي لها أكثر من جردة واحدة
  // نحسب لكل باركود منفصل، وإذا لم يكن هناك باركود، نحسب للصنف
  const modifiedBarcodes = db
    .prepare(
      `
      SELECT COUNT(*) as count
      FROM (
        SELECT barcode_id
        FROM counts
        WHERE warehouse_id = ? AND barcode_id IS NOT NULL
        GROUP BY barcode_id
        HAVING COUNT(*) > 1
      )
    `
    )
    .get(req.warehouseId).count;
  
  const modifiedItems = db
    .prepare(
      `
      SELECT COUNT(*) as count
      FROM (
        SELECT item_id
        FROM counts
        WHERE warehouse_id = ? AND barcode_id IS NULL
        GROUP BY item_id
        HAVING COUNT(*) > 1
      )
    `
    )
    .get(req.warehouseId).count;
  
  const totalModified = modifiedBarcodes + modifiedItems;

  const statsRow = {
    total,
    counted: countedItemsCount,
    remaining,
    modified: totalModified
  };

  res.json({ items, stats: statsRow });
});

// API: item details (barcodes + counts)
app.get("/api/items/:id/detail", requireAuthApi, requireWarehouseApi, (req, res) => {
  const id = Number(req.params.id);
  if (!Number.isFinite(id)) return res.status(400).json({ error: "invalid_id" });
  const item = db
    .prepare("SELECT id, item_code, item_name FROM items WHERE id = ?")
    .get(id);
  if (!item) return res.status(404).json({ error: "not_found" });

  const barcodes = db
    .prepare("SELECT barcode, uom FROM barcodes WHERE item_id = ? ORDER BY barcode")
    .all(id);
  const counts = db
    .prepare(
      `
      SELECT c.id, c.qty, c.note, c.created_at, u.username
      FROM counts c
      JOIN users u ON u.id = c.user_id
      WHERE c.item_id = ? AND c.warehouse_id = ?
      ORDER BY c.id DESC
      LIMIT 100
    `
    )
    .all(id, req.warehouseId);

  res.json({ item, barcodes, counts });
});

// API: delete all counts for current warehouse
app.delete("/api/counts/reset", requireAuthApi, requireWarehouseApi, (req, res) => {
  const result = db
    .prepare("DELETE FROM counts WHERE warehouse_id = ?")
    .run(req.warehouseId);
  
  res.json({ ok: true, deleted: result.changes });
});

// API: delete all counts (all warehouses) - admin only
app.delete("/api/counts/reset-all", requireAuthApi, (req, res) => {
  // تحقق من أن المستخدم admin
  if (req.user.role !== 'admin') {
    return res.status(403).json({ error: "admin_only" });
  }
  
  const result = db.prepare("DELETE FROM counts").run();
  
  res.json({ ok: true, deleted: result.changes });
});

// Admin API: Get system statistics
app.get("/api/admin/stats", requireAuthApi, requireAdmin, (req, res) => {
  const totalItems = db.prepare("SELECT COUNT(*) as count FROM items").get().count;
  const totalBarcodes = db.prepare("SELECT COUNT(*) as count FROM barcodes").get().count;
  const totalUsers = db.prepare("SELECT COUNT(*) as count FROM users").get().count;
  const totalCounts = db.prepare("SELECT COUNT(*) as count FROM counts").get().count;
  
  res.json({
    totalItems,
    totalBarcodes,
    totalUsers,
    totalCounts
  });
});

// Admin API: Get all items
app.get("/api/admin/items", requireAuthApi, requireAdmin, (req, res) => {
  const items = db.prepare("SELECT id, item_code, item_name, created_at FROM items ORDER BY item_code LIMIT 1000").all();
  res.json({ items });
});

// Admin API: Add new item
app.post("/api/admin/items", requireAuthApi, requireAdmin, (req, res) => {
  const { item_code, item_name } = req.body;
  
  if (!item_code || !item_name) {
    return res.status(400).json({ error: "item_code and item_name required" });
  }
  
  try {
    const result = db.prepare(
      "INSERT INTO items (item_code, item_name) VALUES (?, ?)"
    ).run(item_code, item_name);
    
    res.json({ ok: true, id: result.lastInsertRowid });
  } catch (error) {
    if (error.message.includes('UNIQUE')) {
      res.status(400).json({ error: "item_code_exists" });
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// Admin API: Update item
app.put("/api/admin/items/:id", requireAuthApi, requireAdmin, (req, res) => {
  const id = Number(req.params.id);
  const { item_code, item_name } = req.body;
  
  if (!Number.isFinite(id)) {
    return res.status(400).json({ error: "invalid_id" });
  }
  
  if (!item_code || !item_name) {
    return res.status(400).json({ error: "item_code and item_name required" });
  }
  
  try {
    db.prepare("UPDATE items SET item_code = ?, item_name = ? WHERE id = ?")
      .run(item_code, item_name, id);
    
    res.json({ ok: true });
  } catch (error) {
    if (error.message.includes('UNIQUE')) {
      res.status(400).json({ error: "item_code_exists" });
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// Admin API: Delete item
app.delete("/api/admin/items/:id", requireAuthApi, requireAdmin, (req, res) => {
  const id = Number(req.params.id);
  
  if (!Number.isFinite(id)) {
    return res.status(400).json({ error: "invalid_id" });
  }
  
  // حذف الباركودات والجردات المرتبطة أولاً
  db.prepare("DELETE FROM barcodes WHERE item_id = ?").run(id);
  db.prepare("DELETE FROM counts WHERE item_id = ?").run(id);
  db.prepare("DELETE FROM items WHERE id = ?").run(id);
  
  res.json({ ok: true });
});

// Admin API: Get all users
app.get("/api/admin/users", requireAuthApi, requireAdmin, (req, res) => {
  const users = db.prepare("SELECT id, username, role, warehouse_id, full_name, created_at FROM users ORDER BY id").all();
  res.json({ users });
});

// Admin API: Add new user
app.post("/api/admin/users", requireAuthApi, requireAdmin, (req, res) => {
  const { username, password, role, warehouse_id, full_name } = req.body;
  
  if (!username || !password) {
    return res.status(400).json({ error: "username and password required" });
  }
  
  try {
    const password_hash = bcrypt.hashSync(password, 10);
    const result = db.prepare(
      "INSERT INTO users (username, password_hash, role, warehouse_id, full_name) VALUES (?, ?, ?, ?, ?)"
    ).run(username, password_hash, role || 'user', warehouse_id || 1, full_name || null);
    
    res.json({ ok: true, id: result.lastInsertRowid });
  } catch (error) {
    if (error.message.includes('UNIQUE')) {
      res.status(400).json({ error: "username_exists" });
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// Admin API: Update user
app.put("/api/admin/users/:id", requireAuthApi, requireAdmin, (req, res) => {
  const id = Number(req.params.id);
  const { username, password, role, warehouse_id, full_name } = req.body;
  
  if (!Number.isFinite(id)) {
    return res.status(400).json({ error: "invalid_id" });
  }
  
  try {
    let query = "UPDATE users SET username = ?, role = ?, warehouse_id = ?, full_name = ?";
    let params = [username, role || 'user', warehouse_id || 1, full_name || null];
    
    if (password) {
      const password_hash = bcrypt.hashSync(password, 10);
      query += ", password_hash = ?";
      params.push(password_hash);
    }
    
    query += " WHERE id = ?";
    params.push(id);
    
    db.prepare(query).run(...params);
    res.json({ ok: true });
  } catch (error) {
    if (error.message.includes('UNIQUE')) {
      res.status(400).json({ error: "username_exists" });
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// Admin API: Delete user
app.delete("/api/admin/users/:id", requireAuthApi, requireAdmin, (req, res) => {
  const id = Number(req.params.id);
  
  if (!Number.isFinite(id)) {
    return res.status(400).json({ error: "invalid_id" });
  }
  
  // لا يمكن حذف نفسك
  if (id === req.user.sub) {
    return res.status(400).json({ error: "cannot_delete_yourself" });
  }
  
  db.prepare("DELETE FROM users WHERE id = ?").run(id);
  res.json({ ok: true });
});

// Admin API: Get all barcodes
app.get("/api/admin/barcodes", requireAuthApi, requireAdmin, (req, res) => {
  const barcodes = db.prepare(`
    SELECT b.id, b.barcode, b.uom, i.item_code, i.item_name, b.item_id
    FROM barcodes b
    JOIN items i ON i.id = b.item_id
    ORDER BY b.id DESC
    LIMIT 1000
  `).all();
  res.json({ barcodes });
});

// Admin API: Add new barcode
app.post("/api/admin/barcodes", requireAuthApi, requireAdmin, (req, res) => {
  const { item_id, barcode, uom } = req.body;
  
  if (!item_id || !barcode) {
    return res.status(400).json({ error: "item_id and barcode required" });
  }
  
  try {
    const result = db.prepare(
      "INSERT INTO barcodes (item_id, barcode, uom) VALUES (?, ?, ?)"
    ).run(item_id, barcode, uom || null);
    
    res.json({ ok: true, id: result.lastInsertRowid });
  } catch (error) {
    if (error.message.includes('UNIQUE')) {
      res.status(400).json({ error: "barcode_exists" });
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// Admin API: Update barcode
app.put("/api/admin/barcodes/:id", requireAuthApi, requireAdmin, (req, res) => {
  const id = Number(req.params.id);
  const { barcode, uom } = req.body;
  
  if (!Number.isFinite(id) || !barcode) {
    return res.status(400).json({ error: "invalid_parameters" });
  }
  
  try {
    db.prepare("UPDATE barcodes SET barcode = ?, uom = ? WHERE id = ?")
      .run(barcode, uom || null, id);
    
    res.json({ ok: true });
  } catch (error) {
    if (error.message.includes('UNIQUE')) {
      res.status(400).json({ error: "barcode_exists" });
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// Admin API: Delete barcode
app.delete("/api/admin/barcodes/:id", requireAuthApi, requireAdmin, (req, res) => {
  const id = Number(req.params.id);
  
  if (!Number.isFinite(id)) {
    return res.status(400).json({ error: "invalid_id" });
  }
  
  db.prepare("DELETE FROM barcodes WHERE id = ?").run(id);
  res.json({ ok: true });
});

// Admin API: Get all counts with details
app.get("/api/admin/counts", requireAuthApi, requireAdmin, (req, res) => {
  const counts = db.prepare(`
    SELECT c.id, c.qty, c.note, c.created_at, c.warehouse_id,
           i.item_code, i.item_name,
           u.username, u.full_name,
           c.sap_qty, c.sap_committed, c.sap_available
    FROM counts c
    JOIN items i ON i.id = c.item_id
    JOIN users u ON u.id = c.user_id
    ORDER BY c.id DESC
    LIMIT 500
  `).all();
  res.json({ counts });
});

// Admin API: Update count
app.put("/api/admin/counts/:id", requireAuthApi, requireAdmin, (req, res) => {
  const id = Number(req.params.id);
  const { qty, note } = req.body;
  
  if (!Number.isFinite(id) || !Number.isFinite(qty)) {
    return res.status(400).json({ error: "invalid_parameters" });
  }
  
  db.prepare("UPDATE counts SET qty = ?, note = ? WHERE id = ?")
    .run(qty, note || null, id);
  
  res.json({ ok: true });
});

// Admin API: Delete count
app.delete("/api/admin/counts/:id", requireAuthApi, requireAdmin, (req, res) => {
  const id = Number(req.params.id);
  
  if (!Number.isFinite(id)) {
    return res.status(400).json({ error: "invalid_id" });
  }
  
  db.prepare("DELETE FROM counts WHERE id = ?").run(id);
  res.json({ ok: true });
});

// Admin API: Test SAP connection
app.get("/api/admin/test-sap", requireAuthApi, requireAdmin, async (req, res) => {
  if (!sapConfig.SAP_ENABLED) {
    return res.json({ success: false, error: "SAP integration is disabled in configuration" });
  }
  
  try {
    const result = await sapClient.testConnection();
    res.json(result);
  } catch (error) {
    res.json({ success: false, error: error.message });
  }
});

// Admin API: Import Excel file
app.post("/api/admin/import-excel", requireAuthApi, requireAdmin, upload.single('file'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "no_file", message: "No file uploaded" });
  }

  const filePath = req.file.path;
  let imported = 0;
  let errors = [];

  try {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(filePath);
    
    const worksheet = workbook.worksheets[0];
    if (!worksheet) {
      throw new Error("No worksheet found in Excel file");
    }

    // البحث عن الرؤوس
    let headerRow = null;
    let itemCodeCol = -1;
    let itemNameCol = -1;
    let barcodeCol = -1;
    let uomCol = -1;

    // البحث في أول 10 صفوف عن الرؤوس
    for (let rowNum = 1; rowNum <= Math.min(10, worksheet.rowCount); rowNum++) {
      const row = worksheet.getRow(rowNum);
      const values = [];
      
      row.eachCell({ includeEmpty: true }, (cell, colNumber) => {
        const val = String(cell.value || "").trim().toLowerCase();
        values.push(val);
        
        if (val.includes("itemcode") || val.includes("item_code") || val.includes("كود")) {
          itemCodeCol = colNumber;
        }
        if (val.includes("itemname") || val.includes("item_name") || val.includes("اسم")) {
          itemNameCol = colNumber;
        }
        if (val.includes("barcode") || val.includes("باركود")) {
          barcodeCol = colNumber;
        }
        if (val.includes("uom") || val.includes("وحدة")) {
          uomCol = colNumber;
        }
      });
      
      if (itemCodeCol > 0 && itemNameCol > 0) {
        headerRow = rowNum;
        break;
      }
    }

    if (!headerRow || itemCodeCol < 0 || itemNameCol < 0) {
      throw new Error("Could not find required columns (ItemCode, ItemName) in Excel file");
    }

    console.log(`📊 Found headers at row ${headerRow}: ItemCode=${itemCodeCol}, ItemName=${itemNameCol}, Barcode=${barcodeCol}, UOM=${uomCol}`);

    // معالجة البيانات
    const insertItem = db.prepare("INSERT OR IGNORE INTO items (item_code, item_name) VALUES (?, ?)");
    const getItemId = db.prepare("SELECT id FROM items WHERE item_code = ?");
    const insertBarcode = db.prepare("INSERT OR IGNORE INTO barcodes (item_id, barcode, uom) VALUES (?, ?, ?)");

    for (let rowNum = headerRow + 1; rowNum <= worksheet.rowCount; rowNum++) {
      const row = worksheet.getRow(rowNum);
      
      const itemCode = String(row.getCell(itemCodeCol).value || "").trim();
      const itemName = String(row.getCell(itemNameCol).value || "").trim();
      const barcode = barcodeCol > 0 ? String(row.getCell(barcodeCol).value || "").trim() : "";
      const uom = uomCol > 0 ? String(row.getCell(uomCol).value || "").trim() : "";

      if (!itemCode || !itemName) continue;

      try {
        // إدراج الصنف
        insertItem.run(itemCode, itemName);
        
        // إدراج الباركود إذا وجد
        if (barcode) {
          const itemRow = getItemId.get(itemCode);
          if (itemRow) {
            insertBarcode.run(itemRow.id, barcode, uom || null);
          }
        }
        
        imported++;
      } catch (error) {
        errors.push(`Row ${rowNum}: ${error.message}`);
        console.error(`Error importing row ${rowNum}:`, error.message);
      }
    }

    // حذف الملف المؤقت
    fs.unlinkSync(filePath);

    console.log(`✅ Imported ${imported} items from ${req.file.originalname}`);
    
    res.json({
      ok: true,
      imported,
      errors: errors.length > 0 ? errors : undefined,
      filename: req.file.originalname
    });

  } catch (error) {
    // حذف الملف المؤقت في حالة الخطأ
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
    
    console.error('Excel import error:', error);
    res.status(500).json({
      error: "import_failed",
      message: error.message
    });
  }
});

// API: export reports to Excel (Admin only)
app.get("/api/reports/export.xlsx", requireAuthApi, requireWarehouseApi, requireAdmin, async (req, res) => {
  const filter = String(req.query.filter || "all");
  const q = String(req.query.q || "").trim();
  const like = `%${q}%`;

  let where = "WHERE 1=1";
  const params = [req.warehouseId];
  if (q) {
    where +=
      " AND (i.item_code LIKE ? OR i.item_name LIKE ? OR EXISTS (SELECT 1 FROM barcodes b WHERE b.item_id=i.id AND b.barcode LIKE ?))";
    params.push(like, like, like);
  }

  let rows = reportQuery(where, params);
  
  // تطبيق الفلتر على النتائج
  if (filter === "counted") {
    rows = rows.filter(item => item.count_entries > 0);
  } else if (filter === "remaining") {
    rows = rows.filter(item => item.count_entries === 0);
  }

  console.log(`📊 Exporting ${rows.length} items to Excel...`);

  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet("Inventory Report");
  ws.columns = [
    { header: "Warehouse", key: "warehouse", width: 10 },
    { header: "ItemCode", key: "item_code", width: 18 },
    { header: "ItemName", key: "item_name", width: 32 },
    { header: "Barcode", key: "barcode", width: 20 },
    { header: "UOM", key: "uom", width: 10 },
    { header: "Qty_Pieces", key: "qty_pieces", width: 12 },
    { header: "Qty_Dozen", key: "qty_dozen", width: 12 },
    { header: "Qty_Carton", key: "qty_carton", width: 12 },
    { header: "Qty_Total", key: "qty_total", width: 12 },
    { header: "CountedQty", key: "last_qty", width: 12 },
    { header: "SAP_AtCount", key: "sap_at_count", width: 14 },
    { header: "SAP_Current", key: "sap_current", width: 14 },
    { header: "Difference", key: "difference", width: 12 },
    { header: "UpdatedQty", key: "updated_qty", width: 12 },
    { header: "LastUser", key: "last_user", width: 14 },
    { header: "LastTime", key: "last_time", width: 22 },
    { header: "CountEntries", key: "count_entries", width: 14 },
    { header: "Modified", key: "modified", width: 12 },
  ];

  // جلب بيانات SAP الحالية لكل صنف
  console.log('🔄 Fetching current SAP quantities...');
  const rowsWithSapData = [];
  
  for (const row of rows) {
    let sapAtCount = row.sap_available; // الكمية في SAP وقت الجرد (من DB)
    let sapCurrent = null; // الكمية في SAP الآن (جلب مباشر)
    let difference = null;
    let updatedQty = null;
    
    // جلب الكمية الحالية من SAP (وقت التصدير)
    if (sapConfig.SAP_ENABLED) {
      try {
        const sapData = await sapClient.getItemQuantity(row.item_code, req.warehouseId);
        if (sapData) {
          sapCurrent = sapData.available; // الكمية الحالية في SAP
          
          // حساب الفرق على أساس SAP وقت الجرد
          if (row.last_qty !== null && sapAtCount !== null) {
            difference = row.last_qty - sapAtCount; // الفرق = الجرد - SAP وقت الجرد
            // الكمية النهائية = SAP الحالي + الفرق
            updatedQty = sapCurrent + difference;
          } else if (row.last_qty !== null && sapCurrent !== null) {
            // إذا لم يكن هناك بيانات SAP وقت الجرد، نحسب من الحالي
            difference = row.last_qty - sapCurrent;
            updatedQty = sapCurrent + difference;
          }
        }
      } catch (error) {
        console.error(`⚠️ Failed to fetch SAP data for ${row.item_code}:`, error.message);
      }
    }
    
    rowsWithSapData.push({
      ...row,
      sap_at_count: sapAtCount,
      sap_current: sapCurrent,
      difference: difference,
      updated_qty: updatedQty,
    });
  }

  // كل سطر في rows يمثل باركود منفصل أو صنف بدون باركود
  for (const row of rowsWithSapData) {
    ws.addRow({
      warehouse: req.warehouseId,
      item_code: row.item_code,
      item_name: row.item_name,
      barcode: row.barcode || "",
      uom: row.uom || "",
      qty_pieces: row.qty_pieces ?? "",
      qty_dozen: row.qty_dozen ?? "",
      qty_carton: row.qty_carton ?? "",
      qty_total: row.qty_total ?? "",
      last_qty: row.last_qty ?? "",
      sap_at_count: row.sap_at_count ?? "",
      sap_current: row.sap_current ?? "",
      difference: row.difference ?? "",
      updated_qty: row.updated_qty ?? "",
      last_user: row.last_user ?? "",
      last_time: row.last_time ?? "",
      count_entries: row.count_entries,
      modified: row.count_entries > 1 ? "YES" : "NO",
    });
  }

  // إضافة ورقة ملخص
  const summaryWs = wb.addWorksheet("Summary");
  summaryWs.columns = [
    { header: "Metric", key: "metric", width: 30 },
    { header: "Value", key: "value", width: 15 },
  ];
  
  summaryWs.addRow({ metric: "Export Date", value: new Date().toISOString() });
  summaryWs.addRow({ metric: "Exported By", value: req.user.username });
  summaryWs.addRow({ metric: "Warehouse", value: req.warehouseId });
  summaryWs.addRow({ metric: "Total Items", value: rowsWithSapData.length });
  summaryWs.addRow({ metric: "Items with Counts", value: rowsWithSapData.filter(r => r.count_entries > 0).length });
  summaryWs.addRow({ metric: "SAP Integration", value: sapConfig.SAP_ENABLED ? "Enabled" : "Disabled" });

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
  const filename = `inventory-report-wh${req.warehouseId}-${timestamp}.xlsx`;

  res.setHeader(
    "Content-Type",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  );
  res.setHeader(
    "Content-Disposition",
    `attachment; filename="${filename}"`
  );
  
  console.log(`✅ Export completed: ${filename}`);
  await wb.xlsx.write(res);
  res.end();
});

app.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});


