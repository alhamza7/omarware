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

const rq = el("rq");
const filterEl = el("filter");
const btnRSearch = el("btnRSearch");
const rtable = el("rtable");
const stats = el("stats");
const btnExport = el("btnExport");
const btnResetWarehouse = el("btnResetWarehouse");
const btnResetAll = el("btnResetAll");

async function api(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderStats(s) {
  stats.innerHTML = `
    <div>إجمالي الأصناف: <strong>${escapeHtml(s.total)}</strong></div>
    <div>المجرودة: <strong>${escapeHtml(s.counted)}</strong></div>
    <div>المتبقية: <strong>${escapeHtml(s.remaining)}</strong></div>
    <div>تم تعديلها بعد الجرد (أكثر من إدخال): <strong>${escapeHtml(
      s.modified
    )}</strong></div>
  `;
}

function renderRows(rows) {
  rtable.innerHTML = "";
  if (!rows.length) {
    rtable.innerHTML = `<div class="muted">لا توجد بيانات.</div>`;
    return;
  }

  for (const r of rows) {
    const row = document.createElement("div");
    row.className = "result";
    const last = r.last_time
      ? `${escapeHtml(r.last_qty)} — ${escapeHtml(r.last_user)} (${escapeHtml(
          r.last_time
        )})`
      : "لم يُجرد بعد";
    const mod = r.count_entries > 1 ? "نعم" : "لا";
    row.innerHTML = `
      <div class="result__meta">
        <div class="result__code">${escapeHtml(r.item_code)}</div>
        <div class="result__name">${escapeHtml(r.item_name)}</div>
        <div class="muted">آخر كمية: ${last} — تعديل بعد الجرد: <strong>${mod}</strong></div>
      </div>
      <a class="btn" href="/items/${encodeURIComponent(r.id)}">تفاصيل</a>
    `;
    rtable.appendChild(row);
  }
}

async function load() {
  const q = rq.value.trim();
  const filter = filterEl.value;
  btnExport.href = `/api/reports/export.xlsx?filter=${encodeURIComponent(
    filter
  )}&q=${encodeURIComponent(q)}`;

  rtable.innerHTML = `<div class="muted">جاري التحميل...</div>`;
  const data = await api(
    `/api/reports/summary?filter=${encodeURIComponent(
      filter
    )}&q=${encodeURIComponent(q)}`
  );
  renderStats(data.stats);
  renderRows(data.items);
  
  // إظهار زر "حذف الكل" للمسؤولين فقط
  try {
    const me = await api("/api/me");
    if (me.user && me.user.role === "admin") {
      btnResetAll.style.display = "inline-block";
    }
  } catch (e) {
    // تجاهل الخطأ
  }
}

btnRSearch.addEventListener("click", load);
rq.addEventListener("keydown", (e) => {
  if (e.key === "Enter") load();
});
filterEl.addEventListener("change", load);

btnResetWarehouse.addEventListener("click", async () => {
  if (!confirm("هل أنت متأكد من حذف جميع الجردات في هذا المخزن؟ لا يمكن التراجع عن هذا الإجراء.")) {
    return;
  }
  
  try {
    const result = await api("/api/counts/reset", { method: "DELETE" });
    alert(`تم حذف ${result.deleted} جردة بنجاح`);
    load();
  } catch (e) {
    alert(`فشل الحذف: ${e.message}`);
  }
});

btnResetAll.addEventListener("click", async () => {
  if (!confirm("⚠️ تحذير: سيتم حذف جميع الجردات في جميع المخازن!\n\nهل أنت متأكد تماماً؟ لا يمكن التراجع عن هذا الإجراء.")) {
    return;
  }
  
  if (!confirm("تأكيد نهائي: هل تريد حقاً حذف جميع الجردات؟")) {
    return;
  }
  
  try {
    const result = await api("/api/counts/reset-all", { method: "DELETE" });
    alert(`تم حذف ${result.deleted} جردة من جميع المخازن بنجاح`);
    load();
  } catch (e) {
    alert(`فشل الحذف: ${e.message}`);
  }
});

load().catch((e) => {
  rtable.innerHTML = `<div class="alert">فشل التحميل: ${escapeHtml(
    String(e.message || e)
  )}</div>`;
});





