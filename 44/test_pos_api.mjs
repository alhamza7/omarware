/**
 * POS Perfume API — Standalone Test Script
 * =========================================
 * Run with:  node test_pos_api.mjs
 *
 * • Calls Odoo DIRECTLY (no Vite proxy needed).
 * • All IDs (customer, order, line) are created fresh each run — no hardcoded IDs.
 * • Infrastructure-optional tests (WhatsApp, PDF report) are marked as
 *   "expected" so they never count as failures in CI.
 * • Outputs the full JSON result map to stdout at the end.
 */

// ─── Config ────────────────────────────────────────────────────────────────
const ODOO_URL = 'http://localhost:8070';
const BASE     = `${ODOO_URL}/api/pos_perfume/v1`;
const API_KEY  = '569cf0d1b47172b3863460b63368f2d36eb8cff8';

const HEADERS = {
  'Authorization': `Bearer ${API_KEY}`,
  'Content-Type':  'application/json',
};

// ─── Colours ───────────────────────────────────────────────────────────────
const G   = '\x1b[32m';
const R   = '\x1b[31m';
const Y   = '\x1b[33m';
const B   = '\x1b[36m';
const DIM = '\x1b[2m';
const RST = '\x1b[0m';

// ─── Core fetch helper ─────────────────────────────────────────────────────
/**
 * Calls one endpoint and returns a structured result object.
 * Binary responses (PDF) are stored as { _binary: true, status, ok }.
 */
async function call(method, path, body = null) {
  const url = `${BASE}${path}`;
  try {
    const opts = { method, headers: HEADERS };
    if (body) opts.body = JSON.stringify(body);

    const res = await fetch(url, opts);
    const ct  = res.headers.get('content-type') ?? '';

    let response;
    if (ct.includes('application/json')) {
      response = await res.json();
    } else if (ct.includes('application/pdf') || !ct.includes('text')) {
      response = { _binary: true, status: res.status, ok: res.ok };
    } else {
      response = await res.text();
    }

    return { httpStatus: res.status, response };
  } catch (err) {
    return { httpStatus: 0, response: null, _fetchError: err.message };
  }
}

// ─── Result builder ────────────────────────────────────────────────────────
/**
 * Runs one API call and builds the result record in the user-facing format.
 * @param {string}  label      - key for the results map (e.g. "PUT /orders/:id")
 * @param {string}  method     - HTTP method
 * @param {string}  path       - path relative to BASE
 * @param {object}  body       - request body (null for GET/DELETE)
 * @param {boolean} optional   - if true, infrastructure failures don't count as failures
 */
async function test(label, method, path, body, optional = false) {
  const { httpStatus, response, _fetchError } = await call(method, path, body);

  const success =
    !_fetchError &&
    httpStatus >= 200 &&
    httpStatus < 300 &&
    (typeof response === 'object' && response !== null
      ? response?.success !== false
      : true);

  let status, message;
  if (success) {
    status  = 'success';
    message = 'successfully fetched : data';
  } else if (optional) {
    status  = 'expected';
    const reason = _fetchError ?? response?.error ?? response;
    message = `expected failure (infrastructure required) : ${label} -> ${reason}`;
  } else {
    status  = 'failed';
    const reason = _fetchError ?? response?.error ?? response;
    message = `failed to fetch : ${label} -> ${reason}`;
  }

  const record = {
    api:        label,
    payload:    body ?? null,
    httpStatus: httpStatus ?? 0,
    response:   _fetchError ? { error: _fetchError } : response,
    status,
    message,
  };

  printLine(record, optional);
  return record;
}

// ─── Console printer ───────────────────────────────────────────────────────
/** Prints a single test result line with colour. */
function printLine(r, optional) {
  const isOk       = r.status === 'success';
  const isExpected = r.status === 'expected';
  const icon  = isOk ? `${G}✔${RST}` : isExpected ? `${Y}~${RST}` : `${R}✘${RST}`;
  const color = isOk ? G : isExpected ? Y : R;
  const code  = r.httpStatus ? `[${r.httpStatus}]` : '[ERR]';
  console.log(`  ${icon} ${color}${r.api.padEnd(44)}${RST} ${DIM}${code}${RST}`);
  if (!isOk) {
    const reason = r.response?.error ?? r.response?.message ?? JSON.stringify(r.response ?? '').slice(0, 120);
    const tag    = isExpected ? `${Y}~${RST}` : `${R}→${RST}`;
    console.log(`      ${tag} ${reason}`);
  }
}

// ─── Test state ────────────────────────────────────────────────────────────
let customerId  = null;
let orderId     = null;
let lineId      = null;
let productId   = null;
let warehouseId = null;

// ─── Run ───────────────────────────────────────────────────────────────────
async function run() {
  console.log(`\n${B}══════════════════════════════════════════════════${RST}`);
  console.log(`${B}  POS Perfume API — Test Runner${RST}`);
  console.log(`${B}  Target : ${ODOO_URL}${RST}`);
  console.log(`${B}══════════════════════════════════════════════════${RST}\n`);

  const results = {};

  /** Shorthand: run a test, store in results map, return the record. */
  const t = async (label, method, path, body, optional = false) => {
    const r = await test(label, method, path, body, optional);
    results[label] = r;
    return r;
  };

  // ── 1. Auth / Session ──────────────────────────────────────────────────
  console.log(`${DIM}── Auth / Session ─────────────────────────────────────${RST}`);
  await t('GET /session', 'GET', '/session');

  // ── 2. Setup ───────────────────────────────────────────────────────────
  console.log(`${DIM}── Setup ──────────────────────────────────────────────${RST}`);
  await t('GET /setup', 'GET', '/setup');

  // ── 3. Settings ────────────────────────────────────────────────────────
  console.log(`${DIM}── Settings ───────────────────────────────────────────${RST}`);
  await t('GET /settings', 'GET', '/settings');
  await t('PUT /settings', 'PUT', '/settings', { exchange_rate: 1500 });

  // ── 4. Customers ────────────────────────────────────────────────────────
  console.log(`${DIM}── Customers ──────────────────────────────────────────${RST}`);
  await t('GET /customers', 'GET', '/customers?limit=10');

  const newCust = await t('POST /customers', 'POST', '/customers', {
    name:  'API Test Customer',
    phone: '07700000000',
  });
  if (newCust.status === 'success' && newCust.response?.data?.id) {
    customerId = newCust.response.data.id;
    console.log(`      ${DIM}→ created customer id=${customerId}${RST}`);
  }

  if (customerId) {
    await t('GET /customers/:id', 'GET',  `/customers/${customerId}`);
    await t('PUT /customers/:id', 'PUT',  `/customers/${customerId}`, { name: 'API Test Customer Updated' });
  } else {
    console.log(`  ${Y}⚠  Skipping GET/PUT customer — creation failed${RST}`);
  }

  // ── 5. Products ─────────────────────────────────────────────────────────
  console.log(`${DIM}── Products ───────────────────────────────────────────${RST}`);
  const prods = await t('GET /products', 'GET', '/products?limit=10');
  productId   = prods.response?.data?.items?.[0]?.id ?? 1;

  await t('GET /products/:id',        'GET',  `/products/${productId}`);
  await t('POST /products/data',      'POST', '/products/data',      { product_id: productId });
  await t('POST /products/uom_price', 'POST', '/products/uom_price', {
    product_id:   productId,
    pricelist_id: 1,
    uom_id:       1,
  });

  // ── 6. Pricelists & Warehouses ──────────────────────────────────────────
  console.log(`${DIM}── Pricelists & Warehouses ────────────────────────────${RST}`);
  const whs   = await t('GET /warehouses', 'GET', '/warehouses');
  await t('GET /pricelists', 'GET', '/pricelists');
  warehouseId = whs.response?.data?.items?.[0]?.id ?? 1;

  // ── 7. Create a fresh order (draft) ─────────────────────────────────────
  console.log(`${DIM}── Orders ─────────────────────────────────────────────${RST}`);
  await t('GET /orders', 'GET', '/orders?limit=10');

  const newOrder = await t('POST /orders', 'POST', '/orders', {
    partner_id: customerId ?? 1,
  });
  if (newOrder.status === 'success' && newOrder.response?.data?.id) {
    orderId = newOrder.response.data.id;
    console.log(`      ${DIM}→ created order id=${orderId} (state: draft)${RST}`);
  }

  if (!orderId) {
    console.log(`  ${R}✘  Cannot continue order tests — order creation failed${RST}`);
  } else {
    // ── 8. Order read & update (order is in DRAFT) ─────────────────────
    await t('GET /orders/:id', 'GET', `/orders/${orderId}`);
    await t('PUT /orders/:id', 'PUT', `/orders/${orderId}`, { note: 'API test update' });

    // ── 9. Order Lines (DRAFT) ─────────────────────────────────────────
    console.log(`${DIM}── Order Lines ────────────────────────────────────────${RST}`);
    const newLine = await t('POST /orders/:id/lines', 'POST', `/orders/${orderId}/lines`, {
      product_id:   productId,
      warehouse_id: warehouseId,
      quantity:     1,
    });
    if (newLine.status === 'success' && newLine.response?.data?.id) {
      lineId = newLine.response.data.id;
      console.log(`      ${DIM}→ created line id=${lineId}${RST}`);
    }

    if (lineId) {
      await t('PUT /orders/:id/lines/:lid',    'PUT',    `/orders/${orderId}/lines/${lineId}`, { quantity: 2 });
      await t('DELETE /orders/:id/lines/:lid', 'DELETE', `/orders/${orderId}/lines/${lineId}`);
    } else {
      console.log(`  ${Y}⚠  Skipping line update/delete — line creation failed${RST}`);
    }

    // ── 10. Order Actions (still DRAFT) ───────────────────────────────
    console.log(`${DIM}── Order Actions ──────────────────────────────────────${RST}`);
    await t('PUT /orders/:id/exchange_rate', 'PUT',  `/orders/${orderId}/exchange_rate`, { exchange_rate: 1500 });

    // quotation → cancel → back to draft  (tests all 3 state transitions)
    await t('POST /orders/:id/quotation', 'POST', `/orders/${orderId}/quotation`);
    await t('POST /orders/:id/cancel',    'POST', `/orders/${orderId}/cancel`);
    await t('POST /orders/:id/draft',     'POST', `/orders/${orderId}/draft`);

    // ── 11. Comms / Report / SAP (order back in DRAFT) ────────────────
    // These are optional — they need system dependencies / external config.
    console.log(`${DIM}── Comms / Report / SAP (infrastructure-optional) ───${RST}`);
    await t('POST /orders/:id/send_whatsapp',       'POST', `/orders/${orderId}/send_whatsapp`,       null, true);
    await t('POST /orders/:id/send_whatsapp_image', 'POST', `/orders/${orderId}/send_whatsapp_image`, null, true);
    await t('GET /orders/:id/report',               'GET',  `/orders/${orderId}/report`,              null, true);
    await t('POST /orders/:id/sync_sap',            'POST', `/orders/${orderId}/sync_sap`,            null, true);

    // ── 12. Re-add a line, then confirm (DRAFT with at least one line) ─
    console.log(`${DIM}── Confirm ────────────────────────────────────────────${RST}`);
    await t('POST /orders/:id/lines (re-add)', 'POST', `/orders/${orderId}/lines`, {
      product_id:   productId,
      warehouse_id: warehouseId,
      quantity:     1,
    });
    await t('POST /orders/:id/confirm', 'POST', `/orders/${orderId}/confirm`);

    // ── 13. Cleanup ────────────────────────────────────────────────────
    console.log(`${DIM}── Cleanup ────────────────────────────────────────────${RST}`);
    await t('DELETE /orders/:id', 'DELETE', `/orders/${orderId}`);
  }

  // ─── Summary ─────────────────────────────────────────────────────────────
  const all      = Object.values(results);
  const passed   = all.filter(r => r.status === 'success').length;
  const failed   = all.filter(r => r.status === 'failed').length;
  const expected = all.filter(r => r.status === 'expected').length;
  const total    = all.length;

  console.log(`\n${B}══════════════════════════════════════════════════${RST}`);
  console.log(
    `  Results: ${G}${passed} passed${RST}` +
    `  ${failed ? R : DIM}${failed} failed${RST}` +
    `  ${Y}${expected} expected (infra)${RST}` +
    `  ${DIM}(${total} total)${RST}`
  );

  if (failed > 0) {
    console.log(`\n  ${R}Failed endpoints:${RST}`);
    all
      .filter(r => r.status === 'failed')
      .forEach(r => {
        const reason = r.response?.error ?? r.message ?? '';
        console.log(`    ${R}✘ ${r.api}${RST}  ${DIM}[${r.httpStatus}] ${String(reason).slice(0, 120)}${RST}`);
      });
  }

  if (expected > 0) {
    console.log(`\n  ${Y}Expected (requires infrastructure setup):${RST}`);
    all
      .filter(r => r.status === 'expected')
      .forEach(r => {
        const reason = r.response?.error ?? '';
        console.log(`    ${Y}~ ${r.api}${RST}  ${DIM}[${r.httpStatus}] ${String(reason).slice(0, 120)}${RST}`);
      });
  }

  console.log(`${B}══════════════════════════════════════════════════${RST}\n`);

  // Emit the full JSON result map (piped to file or parsed by CI)
  console.log('\n--- JSON RESULTS ---');
  console.log(JSON.stringify(results, null, 2));
}

run().catch(console.error);
