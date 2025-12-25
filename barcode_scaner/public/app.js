const el = (id) => document.getElementById(id);

// منع الزوم في المتصفح على الموبايل
document.addEventListener('gesturestart', function (e) {
  e.preventDefault();
});

document.addEventListener('gesturechange', function (e) {
  e.preventDefault();
});

document.addEventListener('gestureend', function (e) {
  e.preventDefault();
});

// منع الزوم بالنقر المزدوج
let lastTouchEnd = 0;
document.addEventListener('touchend', function (e) {
  const now = Date.now();
  if (now - lastTouchEnd <= 300) {
    e.preventDefault();
  }
  lastTouchEnd = now;
}, false);

const qEl = el("q");
const btnSearch = el("btnSearch");
const resultsEl = el("results");
const dropdownEl = el("dropdown");

const dlg = el("countDlg");
const dlgTitle = el("dlgTitle");
const dlgMeta = el("dlgMeta");
const qtyEl = el("qty");
const noteEl = el("note");
const btnCancel = el("btnCancel");
const countForm = el("countForm");
const latestCountsEl = el("latestCounts");

let selectedItem = null;
let lastScanValue = null;

async function api(path, opts) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

function renderResults(items) {
  resultsEl.innerHTML = "";
  if (!items.length) {
    resultsEl.innerHTML = `<div class="muted">لا توجد نتائج.</div>`;
    return;
  }

  for (const it of items) {
    const row = document.createElement("div");
    row.className = "result";
    const barcodeText = it.barcode ? `<div class="result__barcode">باركود: ${escapeHtml(it.barcode)}</div>` : "";
    const uomText = it.uom ? ` (${escapeHtml(it.uom)})` : "";
    row.innerHTML = `
      <div class="result__meta">
        <div class="result__code">${escapeHtml(it.item_code)}</div>
        <div class="result__name">${escapeHtml(it.item_name)}${uomText}</div>
        ${barcodeText}
      </div>
    `;
    row.addEventListener("click", async () => {
      hideDropdown();
      // جلب البيانات الكاملة مع sapQuantity
      try {
        const fullData = await api(`/api/items/by-code/${encodeURIComponent(it.item_code)}`);
        openCountDialog(fullData.item, fullData.lastCount || null, fullData.sapQuantity || null);
      } catch (e) {
        openCountDialog(it, it.lastCount || null, null);
      }
    });
    resultsEl.appendChild(row);
  }
}

function showDropdown(items) {
  if (!dropdownEl) return;
  if (!items.length) return hideDropdown();
  dropdownEl.innerHTML = "";
  for (const it of items) {
    const row = document.createElement("div");
    row.className = "result";
    const barcodeText = it.barcode ? `<div class="result__barcode">باركود: ${escapeHtml(it.barcode)}</div>` : "";
    const uomText = it.uom ? ` (${escapeHtml(it.uom)})` : "";
    row.innerHTML = `
      <div class="result__meta">
        <div class="result__code">${escapeHtml(it.item_code)}</div>
        <div class="result__name">${escapeHtml(it.item_name)}${uomText}</div>
        ${barcodeText}
      </div>
    `;
    row.addEventListener("click", async () => {
      hideDropdown();
      // جلب البيانات الكاملة مع sapQuantity
      try {
        const fullData = await api(`/api/items/by-code/${encodeURIComponent(it.item_code)}`);
        openCountDialog(fullData.item, fullData.lastCount || null, fullData.sapQuantity || null);
      } catch (e) {
        openCountDialog(it, it.lastCount || null, null);
      }
    });
    dropdownEl.appendChild(row);
  }
  dropdownEl.style.display = "block";
}

function hideDropdown() {
  if (!dropdownEl) return;
  dropdownEl.style.display = "none";
  dropdownEl.innerHTML = "";
}

async function search() {
  const q = qEl.value.trim();
  if (!q) {
    resultsEl.innerHTML = `<div class="muted">اكتب الباركود أو الاسم للبحث.</div>`;
    hideDropdown();
    return;
  }
  resultsEl.innerHTML = `<div class="muted">جاري البحث...</div>`;
  try {
    const data = await api(`/api/items/search?q=${encodeURIComponent(q)}`);
    renderResults(data.items || []);
    showDropdown(data.items || []);

    // افتح الديالوج مباشرة إذا كان هناك تطابق تام بالكود، أو إذا كانت نتيجة واحدة (مفيد للباركود)
    const items = data.items || [];
    const exact = items.find((x) => x.item_code === q);
    if (exact) openCountDialog(exact, exact.lastCount || null);
    else if (items.length === 1) openCountDialog(items[0], items[0].lastCount || null);
  } catch (e) {
    resultsEl.innerHTML = `<div class="alert">فشل البحث: ${escapeHtml(String(e.message || e))}</div>`;
    hideDropdown();
  }
}

async function loadLatestCounts(itemId) {
  latestCountsEl.textContent = "جاري التحميل...";
  try {
    const data = await api(`/api/items/${itemId}/counts`);
    const rows = data.counts || [];
    if (!rows.length) {
      latestCountsEl.textContent = "لا توجد عمليات إدخال سابقة لهذا الصنف.";
      return;
    }
    latestCountsEl.innerHTML = rows
      .map(
        (r) =>
          `<div>(${escapeHtml(r.created_at)}) <strong>${escapeHtml(
            r.username
          )}</strong>: ${escapeHtml(String(r.qty))} ${r.note ? `— ${escapeHtml(r.note)}` : ""}</div>`
      )
      .join("");
  } catch {
    latestCountsEl.textContent = "تعذر تحميل السجل.";
  }
}

async function openCountDialog(item, lastCount = null, sapQuantity = null) {
  console.log('🔍 openCountDialog called with:', { item, lastCount, sapQuantity });
  
  let addMode = false;
  let lastQty = 0;
  
  // إذا كان مجرود مسبقاً، اعرض دايلوج "تم الجرد - هل تريد التعديل؟"
  if (lastCount != null) {
    const result = await showAlreadyCountedDialog(item, lastCount, sapQuantity);
    if (result.action === 'cancel') {
      window.resumeScanning?.();
      return;
    }
    if (result.action === 'add') {
      addMode = true;
      lastQty = parseFloat(result.lastQty) || 0;
    }
  }

  selectedItem = item;
  selectedItem._addMode = addMode;
  selectedItem._lastQty = lastQty;
  selectedItem._sapQuantity = sapQuantity; // حفظ بيانات SAP
  
  dlgTitle.textContent = addMode ? "إضافة كمية إضافية" : "إضافة كمية جرد";
  const barcodeText = item.barcode ? ` (باركود: ${item.barcode})` : "";
  const uomText = item.uom ? ` - ${item.uom}` : "";
  
  let metaHtml = `<div style="font-size: 16px; margin-bottom: 12px;">${escapeHtml(item.item_code)} — ${escapeHtml(item.item_name)}${uomText}${barcodeText}</div>`;
  
  if (addMode) {
    metaHtml += `<div style="color: #4CAF50; font-weight: bold; margin-bottom: 12px;">الكمية الحالية: ${lastQty}</div>`;
  }
  
  // عرض كمية SAP إن وجدت
  console.log('☁️ SAP Quantity:', sapQuantity);
  if (sapQuantity) {
    console.log('✅ Showing SAP quantity box');
    metaHtml += `
      <div style="background: #E3F2FD; border: 2px solid #2196F3; border-radius: 12px; padding: 16px; margin: 16px 0; text-align: right;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; border-bottom: 2px solid #2196F3; padding-bottom: 8px;">
          <span style="font-size: 20px;">☁️</span>
          <strong style="color: #1976D2; font-size: 18px;">كمية SAP الحالية:</strong>
        </div>
        <div style="display: grid; gap: 8px;">
          <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(255,255,255,0.5); border-radius: 6px;">
            <span style="color: #1565C0; font-weight: 500;">الكمية الموجودة:</span>
            <strong style="color: #1976D2; font-size: 18px;">${escapeHtml(String(sapQuantity.quantity || 0))}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(255,255,255,0.5); border-radius: 6px;">
            <span style="color: #E65100; font-weight: 500;">الكمية المحجوزة:</span>
            <strong style="color: #F57C00; font-size: 18px;">${escapeHtml(String(sapQuantity.committed || 0))}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; padding: 10px; background: rgba(76, 175, 80, 0.15); border-radius: 6px; border: 2px solid #4CAF50;">
            <span style="color: #2E7D32; font-weight: bold;">✅ الكمية المتاحة:</span>
            <strong style="color: #4CAF50; font-size: 20px; font-weight: bold;">${escapeHtml(String(sapQuantity.available || 0))}</strong>
          </div>
        </div>
      </div>
    `;
  } else {
    console.log('❌ No SAP quantity available');
  }
  
  dlgMeta.innerHTML = metaHtml;
  
  qtyEl.value = "";
  noteEl.value = "";
  await loadLatestCounts(item.id);
  dlg.showModal();
  qtyEl.focus();
}

async function showAlreadyCountedDialog(item, lastCount, sapQuantity = null) {
  return new Promise((resolve) => {
    const qty = lastCount.qty || "";
    const username = lastCount.username || "";
    const createdAt = lastCount.created_at || "";
    const note = lastCount.note || "";
    const uomText = item.uom ? ` (${item.uom})` : "";

    // إنشاء دايلوج مخصص بدلاً من confirm
    const dialogOverlay = document.createElement('div');
    dialogOverlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0,0,0,0.6);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
      padding: 20px;
    `;

    const dialogBox = document.createElement('div');
    dialogBox.style.cssText = `
      background: white;
      border-radius: 12px;
      padding: 24px;
      max-width: 500px;
      width: 100%;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      max-height: 90vh;
      overflow-y: auto;
    `;

    // بناء محتوى كمية SAP إن وجدت
    let sapHtml = '';
    if (sapQuantity) {
      sapHtml = `
        <div style="margin-bottom: 16px; padding: 16px; background: #E3F2FD; border: 2px solid #2196F3; border-radius: 12px; text-align: right;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; border-bottom: 2px solid #2196F3; padding-bottom: 8px;">
            <span style="font-size: 20px;">☁️</span>
            <strong style="color: #1976D2; font-size: 18px;">كمية SAP الحالية:</strong>
          </div>
          <div style="display: grid; gap: 8px;">
            <div style="display: flex; justify-content: space-between; padding: 6px; background: rgba(255,255,255,0.5); border-radius: 6px;">
              <span style="color: #1565C0; font-weight: 500;">الموجود:</span>
              <strong style="font-size: 16px;">${escapeHtml(String(sapQuantity.quantity || 0))}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 6px; background: rgba(255,255,255,0.5); border-radius: 6px;">
              <span style="color: #E65100; font-weight: 500;">المحجوز:</span>
              <strong style="font-size: 16px;">${escapeHtml(String(sapQuantity.committed || 0))}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(76, 175, 80, 0.15); border-radius: 6px; border: 2px solid #4CAF50;">
              <span style="color: #2E7D32; font-weight: bold;">✅ المتاح:</span>
              <strong style="color: #4CAF50; font-size: 18px; font-weight: bold;">${escapeHtml(String(sapQuantity.available || 0))}</strong>
            </div>
          </div>
        </div>
      `;
    }

    dialogBox.innerHTML = `
      <div style="margin-bottom: 16px; text-align: right;">
        <strong style="font-size: 18px; color: #FF9800;">⚠️ تم الجرد مسبقاً</strong>
      </div>
      <div style="margin-bottom: 12px; text-align: right;">
        <strong style="font-size: 16px;">${escapeHtml(item.item_code)} — ${escapeHtml(item.item_name)}${uomText}</strong>
        ${item.barcode ? `<br><small style="color: #666;">باركود: ${escapeHtml(item.barcode)}</small>` : ""}
      </div>
      ${sapHtml}
      <div style="margin-bottom: 20px; padding: 12px; background: #f5f5f5; border-radius: 8px; text-align: right;">
        <strong style="display: block; margin-bottom: 8px; color: #333;">آخر جرد:</strong>
        <div style="color: #555;">الكمية: <strong>${escapeHtml(String(qty))}</strong></div>
        <div style="color: #555;">المستخدم: ${escapeHtml(username)}</div>
        <div style="color: #555;">الوقت: ${escapeHtml(createdAt)}</div>
        ${note ? `<div style="color: #555;">ملاحظة: ${escapeHtml(note)}</div>` : ""}
      </div>
      <div style="margin-bottom: 20px; text-align: right; font-size: 16px;">
        هل تريد تعديل أو إضافة كمية؟
      </div>
      <div style="display: flex; gap: 8px; justify-content: flex-end; flex-wrap: wrap;">
        <button id="btnDialogCancel" style="padding: 10px 20px; border: 1px solid #ddd; background: white; border-radius: 6px; cursor: pointer; font-size: 14px;">
          إلغاء
        </button>
        <button id="btnDialogAdd" style="padding: 10px 20px; border: none; background: #4CAF50; color: white; border-radius: 6px; cursor: pointer; font-size: 14px;">
          إضافة كمية إضافية
        </button>
        <button id="btnDialogReplace" style="padding: 10px 20px; border: none; background: #2196F3; color: white; border-radius: 6px; cursor: pointer; font-size: 14px;">
          تعديل الكمية
        </button>
      </div>
    `;

    dialogOverlay.appendChild(dialogBox);
    document.body.appendChild(dialogOverlay);

    const cleanup = () => {
      document.body.removeChild(dialogOverlay);
    };

    document.getElementById('btnDialogCancel').onclick = () => {
      cleanup();
      resolve({ action: 'cancel' });
    };

    document.getElementById('btnDialogAdd').onclick = () => {
      cleanup();
      resolve({ action: 'add', lastQty: qty });
    };

    document.getElementById('btnDialogReplace').onclick = () => {
      cleanup();
      resolve({ action: 'replace' });
    };
  });
}

// يتم استدعاؤها من scan.js عند قراءة باركود/QR
window.onBarcodeScanned = async function onBarcodeScanned(raw) {
  const code = String(raw || "").trim();
  if (!code) return;
  lastScanValue = code;
  try {
    const data = await api(`/api/items/by-code/${encodeURIComponent(code)}`);
    await openCountDialog(data.item, data.lastCount || null, data.sapQuantity || null);
  } catch {
    // المنتج غير موجود: أعرض رسالة سريعة وأكمل المسح
    resultsEl.innerHTML = `<div class="alert">باركود غير موجود: ${escapeHtml(code)}</div>`;
    window.resumeScanning?.();
  }
};

btnCancel.addEventListener("click", () => dlg.close());
btnSearch.addEventListener("click", search);
qEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") search();
});

// بحث سريع أثناء الكتابة (بدون ضغط زر)
let t = null;
qEl.addEventListener("input", () => {
  clearTimeout(t);
  t = setTimeout(() => search(), 120);
});

document.addEventListener("click", (e) => {
  if (!dropdownEl) return;
  if (e.target === qEl) return;
  if (dropdownEl.contains(e.target)) return;
  hideDropdown();
});

// عند استخدام البحث اليدوي: أوقف المسح مؤقتاً لتفادي قراءة باركود أثناء الكتابة
qEl.addEventListener("focus", () => window.pauseScanning?.());
qEl.addEventListener("blur", () => window.resumeScanning?.());

countForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!selectedItem) return;

  let qty = Number(qtyEl.value);
  if (!Number.isFinite(qty)) return;
  
  // إذا كان في وضع الإضافة، أضف الكمية المدخلة للكمية السابقة
  if (selectedItem._addMode && selectedItem._lastQty) {
    qty = qty + selectedItem._lastQty;
  }
  
  const note = noteEl.value.trim();

  try {
    const payload = {
      item_id: selectedItem.id,
      qty,
      note: note || null,
    };
    
    // إضافة بيانات SAP إن وجدت
    if (selectedItem._sapQuantity) {
      payload.sap_qty = selectedItem._sapQuantity.quantity || null;
      payload.sap_committed = selectedItem._sapQuantity.committed || null;
      payload.sap_available = selectedItem._sapQuantity.available || null;
    }
    
    await api("/api/counts", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    // بعد الحفظ: أغلق الديالوج وارجع للمسح مباشرة
    dlg.close();
    qtyEl.value = "";
    noteEl.value = "";
    selectedItem = null;
    window.resumeScanning?.();
  } catch (e2) {
    alert(`فشل الحفظ: ${String(e2.message || e2)}`);
  }
});

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

resultsEl.innerHTML = `<div class="muted">ابدأ بالبحث…</div>`;


