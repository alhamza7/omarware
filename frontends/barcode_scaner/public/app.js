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

// تحديد نوع الوحدة من UOM
function getUnitType(uom) {
  if (!uom) return 'default';
  
  const normalized = uom.toLowerCase().trim();
  
  // قطعة
  if (normalized === 'قطعة' || normalized === 'قطعه' || 
      normalized === 'piece' || normalized === 'pcs') {
    return 'piece';
  }
  
  // باكيت
  if (normalized === 'باكيت' || normalized === 'packet' || normalized === 'pack') {
    return 'packet';
  }
  
  // سيت
  if (normalized === 'سيت' || normalized === 'set') {
    return 'set';
  }
  
  // درزن
  if (normalized === 'درزن' || normalized === 'dozen') {
    return 'dozen';
  }
  
  // كارتون
  if (normalized === 'كارتون' || normalized === 'carton') {
    return 'carton';
  }
  
  return 'default';
}

// الحصول على اسم الوحدة بالعربي
function getUnitLabel(unitType) {
  switch (unitType) {
    case 'piece':
      return 'قطعة';
    case 'packet':
      return 'باكيت';
    case 'set':
      return 'سيت';
    case 'dozen':
      return 'درزن';
    case 'carton':
      return 'كارتون';
    default:
      return 'الكمية';
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

  // تحديد نوع الوحدة
  const unitType = getUnitType(item.uom);
  
  // إذا كان النوع متعدد الوحدات، استخدم dialog خاص
  if (unitType !== 'default') {
    await openMultiUnitDialog(item, addMode, lastQty, sapQuantity, unitType);
    return;
  }

  // Dialog العادي (للوحدات الافتراضية)
  selectedItem = item;
  selectedItem._addMode = addMode;
  selectedItem._lastQty = lastQty;
  selectedItem._sapQuantity = sapQuantity;
  
  dlgTitle.textContent = addMode ? "إضافة كمية إضافية" : "إضافة كمية جرد";
  const barcodeText = item.barcode ? ` (باركود: ${item.barcode})` : "";
  const uomText = item.uom ? ` - ${item.uom}` : "";
  
  let metaHtml = `<div style="font-size: 16px; margin-bottom: 12px;">${escapeHtml(item.item_code)} — ${escapeHtml(item.item_name)}${uomText}${barcodeText}</div>`;
  
  if (addMode) {
    metaHtml += `<div style="color: #4CAF50; font-weight: bold; margin-bottom: 12px;">الكمية الحالية: ${lastQty}</div>`;
  }
  
  // عرض كمية SAP إن وجدت
  if (sapQuantity) {
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
  }
  
  dlgMeta.innerHTML = metaHtml;
  
  qtyEl.value = "";
  noteEl.value = "";
  await loadLatestCounts(item.id);
  dlg.showModal();
  qtyEl.focus();
}

// Dialog الوحدات المتعددة
async function openMultiUnitDialog(item, addMode, lastQty, sapQuantity, unitType) {
  return new Promise((resolve) => {
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
      text-align: right;
    `;

    const barcodeText = item.barcode ? `<br><small style="color: #666;">باركود: ${escapeHtml(item.barcode)}</small>` : "";
    const unitLabel = getUnitLabel(unitType);

    // بناء محتوى كمية SAP إن وجدت
    let sapHtml = '';
    if (sapQuantity) {
      sapHtml = `
        <div style="margin: 20px 0; padding: 20px; background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border: 3px solid #2196F3; border-radius: 12px; box-shadow: 0 4px 12px rgba(33, 150, 243, 0.2);">
          <div style="display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 3px solid #2196F3;">
            <span style="font-size: 28px;">☁️</span>
            <strong style="color: #1976D2; font-size: 20px;">كمية SAP الحالية</strong>
          </div>
          <div style="display: grid; gap: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: white; border-radius: 8px; border-right: 5px solid #1976D2;">
              <span style="color: #1565C0; font-weight: 600; font-size: 16px;">📦 الموجود:</span>
              <strong style="font-size: 22px; color: #1976D2;">${escapeHtml(String(sapQuantity.quantity || 0))}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: white; border-radius: 8px; border-right: 5px solid #F57C00;">
              <span style="color: #E65100; font-weight: 600; font-size: 16px;">🔒 المحجوز:</span>
              <strong style="font-size: 22px; color: #F57C00;">${escapeHtml(String(sapQuantity.committed || 0))}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px; background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%); border-radius: 10px; border: 3px solid #4CAF50; box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);">
              <span style="color: #2E7D32; font-weight: bold; font-size: 18px;">✅ المتاح:</span>
              <strong style="color: #2E7D32; font-size: 26px; font-weight: bold;">${escapeHtml(String(sapQuantity.available || 0))}</strong>
            </div>
          </div>
        </div>
      `;
    }

    let addModeHtml = '';
    if (addMode) {
      addModeHtml = `
        <div style="margin: 16px 0; padding: 16px; background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%); border: 3px solid #4CAF50; border-radius: 12px; box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2);">
          <div style="display: flex; align-items: center; justify-content: center; gap: 10px;">
            <span style="font-size: 24px;">➕</span>
            <div>
              <div style="color: #2E7D32; font-weight: bold; font-size: 16px;">وضع الإضافة</div>
              <div style="color: #1B5E20; font-size: 20px; font-weight: bold; margin-top: 4px;">
                الكمية الحالية: ${lastQty}
              </div>
            </div>
          </div>
        </div>
      `;
    }

    dialogBox.innerHTML = `
      <div style="margin-bottom: 20px; text-align: center; padding: 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white;">
        <div style="font-size: 24px; font-weight: bold; margin-bottom: 8px;">
          📦 ${addMode ? 'إضافة كمية إضافية' : 'إضافة كمية'}
        </div>
        <div style="font-size: 14px; opacity: 0.9;">الوحدات المتعددة</div>
      </div>
      
      <div style="margin-bottom: 16px; padding: 16px; background: #f8f9fa; border-radius: 10px; border-right: 5px solid #667eea;">
        <div style="font-size: 18px; font-weight: bold; color: #333; margin-bottom: 4px;">
          ${escapeHtml(item.item_code)}
        </div>
        <div style="font-size: 16px; color: #666;">
          ${escapeHtml(item.item_name)}
        </div>
        ${barcodeText}
      </div>
      
      ${addModeHtml}
      ${sapHtml}
      
      <div style="margin: 20px 0; padding: 16px; background: linear-gradient(to right, #e3f2fd, #f3e5f5); border-radius: 12px; border: 3px solid #2196F3;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
          <span style="font-size: 24px;">📦</span>
          <label style="font-size: 18px; font-weight: bold; color: #1976D2;">
            ${unitLabel}
          </label>
        </div>
        <input type="number" id="multiPieces" 
          style="width: 100%; padding: 16px; border: 3px solid #2196F3; border-radius: 10px; font-size: 22px; text-align: center; font-weight: bold; background: white;"
          placeholder="أدخل عدد ${unitLabel}" step="any" min="0">
      </div>

      <div style="margin: 20px 0; padding: 16px; background: linear-gradient(to right, #fff3e0, #fce4ec); border-radius: 12px; border: 3px solid #FF9800;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
          <span style="font-size: 24px;">📊</span>
          <label style="font-size: 18px; font-weight: bold; color: #F57C00;">
            درزن (Dozen)
          </label>
        </div>
        <input type="number" id="multiDozen" 
          style="width: 100%; padding: 16px; border: 3px solid #FF9800; border-radius: 10px; font-size: 22px; text-align: center; font-weight: bold; background: white;"
          placeholder="أدخل عدد الدرزن" step="any" min="0">
      </div>

      <div style="margin: 20px 0; padding: 16px; background: linear-gradient(to right, #e8f5e9, #f1f8e9); border-radius: 12px; border: 3px solid #4CAF50;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
          <span style="font-size: 24px;">📦</span>
          <label style="font-size: 18px; font-weight: bold; color: #388E3C;">
            كارتون (Carton)
          </label>
        </div>
        <input type="number" id="multiCarton" 
          style="width: 100%; padding: 16px; border: 3px solid #4CAF50; border-radius: 10px; font-size: 22px; text-align: center; font-weight: bold; background: white;"
          placeholder="أدخل عدد الكراتين" step="any" min="0">
      </div>

      <div style="margin-top: 24px; padding: 12px; background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; text-align: center; color: #856404;">
        <strong>💡 ملاحظة:</strong> أدخل الكميات بشكل منفصل - لا يتم الجمع تلقائياً
      </div>

      <div style="display: flex; gap: 12px; justify-content: center; margin-top: 24px;">
        <button id="btnMultiCancel" 
          style="flex: 1; padding: 16px 24px; border: 2px solid #f44336; background: white; color: #f44336; border-radius: 10px; cursor: pointer; font-size: 18px; font-weight: bold; transition: all 0.3s;"
          onmouseover="this.style.background='#f44336'; this.style.color='white';"
          onmouseout="this.style.background='white'; this.style.color='#f44336';">
          ❌ إلغاء
        </button>
        <button id="btnMultiSave" 
          style="flex: 2; padding: 16px 24px; border: none; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; cursor: pointer; font-size: 18px; font-weight: bold; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); transition: all 0.3s;"
          onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(102, 126, 234, 0.6)';"
          onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(102, 126, 234, 0.4)';">
          ✅ حفظ الكميات
        </button>
      </div>
    `;

    dialogOverlay.appendChild(dialogBox);
    document.body.appendChild(dialogOverlay);

    const piecesInput = document.getElementById('multiPieces');
    const dozenInput = document.getElementById('multiDozen');
    const cartonInput = document.getElementById('multiCarton');

    // Focus على الحقل الأول
    setTimeout(() => piecesInput.focus(), 100);

    const cleanup = () => {
      document.body.removeChild(dialogOverlay);
    };

    document.getElementById('btnMultiCancel').onclick = () => {
      cleanup();
      window.resumeScanning?.();
      resolve(null);
    };

    document.getElementById('btnMultiSave').onclick = async () => {
      const pieces = parseFloat(piecesInput.value) || 0;
      const dozen = parseFloat(dozenInput.value) || 0;
      const carton = parseFloat(cartonInput.value) || 0;

      if (pieces <= 0 && dozen <= 0 && carton <= 0) {
        alert('يجب إدخال كمية واحدة على الأقل');
        return;
      }

      let finalQty = pieces; // نحفظ القطع كإجمالي
      if (addMode && lastQty) {
        finalQty = finalQty + lastQty;
      }

      try {
        const payload = {
          item_id: item.id,
          qty: finalQty,
          qty_pieces: pieces,
          qty_dozen: dozen,
          qty_carton: carton,
        };
        
        // إضافة بيانات SAP إن وجدت
        if (sapQuantity) {
          payload.sap_qty = sapQuantity.quantity || null;
          payload.sap_committed = sapQuantity.committed || null;
          payload.sap_available = sapQuantity.available || null;
        }
        
        await api("/api/counts", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        
        cleanup();
        window.resumeScanning?.();
        resolve({ success: true });
      } catch (e) {
        alert(`فشل الحفظ: ${String(e.message || e)}`);
      }
    };
  });
}

async function showAlreadyCountedDialog(item, lastCount, sapQuantity = null) {
  return new Promise((resolve) => {
    const qty = lastCount.qty || "";
    const username = lastCount.username || "";
    const createdAt = lastCount.created_at || "";
    const note = lastCount.note || "";
    const uomText = item.uom ? ` (${item.uom})` : "";
    
    // جلب بيانات الوحدات المتعددة إن وجدت
    const qtyPieces = lastCount.qty_pieces;
    const qtyDozen = lastCount.qty_dozen;
    const qtyCarton = lastCount.qty_carton;
    const hasMultiUnits = (qtyPieces && qtyPieces > 0) || 
                          (qtyDozen && qtyDozen > 0) || 
                          (qtyCarton && qtyCarton > 0);
    
    const unitType = getUnitType(item.uom);
    const unitLabel = getUnitLabel(unitType);

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

    // بناء عرض الوحدات المتعددة إن وجدت
    let multiUnitsHtml = '';
    if (hasMultiUnits) {
      multiUnitsHtml = `
        <div style="margin: 16px 0; padding: 16px; background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%); border: 3px solid #9C27B0; border-radius: 12px;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #9C27B0;">
            <span style="font-size: 20px;">📦</span>
            <strong style="color: #7B1FA2; font-size: 16px;">الوحدات المسجلة:</strong>
          </div>
          <div style="display: grid; gap: 8px;">
            ${qtyPieces && qtyPieces > 0 ? `
              <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; border-radius: 6px; border-right: 4px solid #2196F3;">
                <span style="color: #1976D2; font-weight: 600;">📦 ${escapeHtml(unitLabel)}:</span>
                <strong style="font-size: 18px; color: #1976D2;">${escapeHtml(String(qtyPieces))}</strong>
              </div>
            ` : ''}
            ${qtyDozen && qtyDozen > 0 ? `
              <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; border-radius: 6px; border-right: 4px solid #FF9800;">
                <span style="color: #F57C00; font-weight: 600;">📊 درزن:</span>
                <strong style="font-size: 18px; color: #F57C00;">${escapeHtml(String(qtyDozen))}</strong>
              </div>
            ` : ''}
            ${qtyCarton && qtyCarton > 0 ? `
              <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; border-radius: 6px; border-right: 4px solid #4CAF50;">
                <span style="color: #388E3C; font-weight: 600;">📦 كارتون:</span>
                <strong style="font-size: 18px; color: #388E3C;">${escapeHtml(String(qtyCarton))}</strong>
              </div>
            ` : ''}
          </div>
        </div>
      `;
    }

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
      <div style="margin-bottom: 20px; padding: 12px; background: #f5f5f5; border-radius: 8px; text-align: right;">
        <strong style="display: block; margin-bottom: 8px; color: #333;">آخر جرد:</strong>
        ${hasMultiUnits ? multiUnitsHtml : `<div style="color: #555;">الكمية: <strong>${escapeHtml(String(qty))}</strong></div>`}
        <div style="color: #555;">المستخدم: ${escapeHtml(username)}</div>
        <div style="color: #555;">الوقت: ${escapeHtml(createdAt)}</div>
        ${note ? `<div style="color: #555;">ملاحظة: ${escapeHtml(note)}</div>` : ""}
      </div>
      ${sapHtml}
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


