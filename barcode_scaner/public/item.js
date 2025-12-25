const el = (id) => document.getElementById(id);

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function load() {
  const data = await api(`/api/items/${encodeURIComponent(ITEM_ID)}/detail`);

  const barcodesEl = el("barcodes");
  const countsEl = el("counts");
  const modifiedEl = el("modified");

  if (!data.barcodes.length) barcodesEl.textContent = "لا يوجد باركودات مسجلة.";
  else {
    barcodesEl.innerHTML = data.barcodes
      .map((b) => `<div>${escapeHtml(b.barcode)}${b.uom ? ` — ${escapeHtml(b.uom)}` : ""}</div>`)
      .join("");
  }

  const counts = data.counts || [];
  modifiedEl.innerHTML =
    counts.length > 1
      ? `<div class="alert">تم تعديل هذا الصنف بعد الجرد (عدد الإدخالات: ${escapeHtml(
          counts.length
        )})</div>`
      : `<div class="muted">عدد الإدخالات: <strong>${escapeHtml(
          counts.length
        )}</strong></div>`;

  if (!counts.length) countsEl.textContent = "لم يتم جرد هذا الصنف بعد.";
  else {
    countsEl.innerHTML = counts
      .map(
        (c) =>
          `<div>(${escapeHtml(c.created_at)}) <strong>${escapeHtml(
            c.username
          )}</strong>: ${escapeHtml(String(c.qty))} ${
            c.note ? `— ${escapeHtml(c.note)}` : ""
          }</div>`
      )
      .join("");
  }
}

load().catch((e) => {
  el("counts").innerHTML = `<div class="alert">فشل التحميل: ${escapeHtml(
    String(e.message || e)
  )}</div>`;
});












