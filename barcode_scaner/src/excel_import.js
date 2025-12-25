const ExcelJS = require("exceljs");

function normalizeHeader(v) {
  return String(v || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "");
}

function pickHeaderMap(headers) {
  // يدعم أسماء شائعة: Itemcode / ItemCode / Code / Barcode ... واسم الصنف: Name / ItemName / Description
  const norm = headers.map(normalizeHeader);
  const idx = (candidates) => {
    for (const c of candidates) {
      const i = norm.indexOf(normalizeHeader(c));
      if (i !== -1) return i;
    }
    return -1;
  };

  const itemCodeIdx = idx([
    "itemcode",
    "item_code",
    "code",
    "barcode",
    "barcod",
    "item",
    "itemno",
  ]);
  const itemNameIdx = idx([
    "itemname",
    "item_name",
    "name",
    "description",
    "itemdesc",
    "arabicname",
  ]);

  const uomIdx = idx(["uomcode", "uom", "unit", "unitcode"]);

  // في ملفك: الباركود عنوانه رقم (مثل 6824...) أو قد يكون Barcode
  let barcodeIdx = idx(["barcode", "barcod", "bcd", "bcdcode"]);
  if (barcodeIdx === -1) {
    barcodeIdx = headers.findIndex((h) => typeof h === "number");
  }

  return { itemCodeIdx, itemNameIdx, uomIdx, barcodeIdx };
}

async function readItemsFromExcel(excelPath) {
  const wb = new ExcelJS.Workbook();
  await wb.xlsx.readFile(excelPath);
  const ws = wb.worksheets[0];
  if (!ws) throw new Error("Excel file has no worksheets");

  const headerRow = ws.getRow(1);
  const headers = headerRow.values.slice(1); // ignore first empty
  const { itemCodeIdx, itemNameIdx: rawNameIdx, uomIdx, barcodeIdx } =
    pickHeaderMap(headers);

  // fallback: في ملفك العمود الثالث (index 2) يمثل اسم/كود الصنف بدون عنوان
  const itemNameIdx = rawNameIdx !== -1 ? rawNameIdx : headers.length > 2 ? 2 : -1;

  if (itemCodeIdx === -1 || itemNameIdx === -1) {
    throw new Error(
      `Cannot detect columns. Headers: ${headers
        .map((h) => String(h))
        .join(", ")}`
    );
  }

  const items = [];
  const barcodes = [];
  ws.eachRow((row, rowNumber) => {
    if (rowNumber === 1) return;
    const vals = row.values.slice(1);
    const item_code = String(vals[itemCodeIdx] ?? "").trim();
    const item_name = String(vals[itemNameIdx] ?? "").trim();
    if (!item_code || !item_name) return;
    items.push({ item_code, item_name });

    const barcode =
      barcodeIdx !== -1 ? String(vals[barcodeIdx] ?? "").trim() : "";
    const uom = uomIdx !== -1 ? String(vals[uomIdx] ?? "").trim() : "";
    if (barcode) {
      barcodes.push({ item_code, barcode, uom: uom || null });
    }
  });

  return { items, barcodes };
}

function upsertItems(db, items) {
  const stmt = db.prepare(`
    INSERT INTO items (item_code, item_name)
    VALUES (@item_code, @item_name)
    ON CONFLICT(item_code) DO UPDATE SET item_name = excluded.item_name
  `);
  const tx = db.transaction((rows) => {
    for (const r of rows) stmt.run(r);
  });
  tx(items);
  return items.length;
}

function upsertBarcodes(db, barcodes) {
  const getItemId = db.prepare("SELECT id FROM items WHERE item_code = ?");
  const insert = db.prepare(`
    INSERT INTO barcodes (item_id, barcode, uom)
    VALUES (?, ?, ?)
    ON CONFLICT(item_id, barcode) DO UPDATE SET uom = excluded.uom
  `);
  const tx = db.transaction((rows) => {
    for (const r of rows) {
      const item = getItemId.get(r.item_code);
      if (!item) continue;
      insert.run(item.id, r.barcode, r.uom);
    }
  });
  tx(barcodes);
  return barcodes.length;
}

module.exports = { readItemsFromExcel, upsertItems, upsertBarcodes };


