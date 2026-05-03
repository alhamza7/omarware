#!/usr/bin/env bash
# Runtime integration test for Supply Chain JSON-RPC APIs (same as FE: POST + Bearer JWT).
#
# Usage:
#   ./scripts/runtime_test_supply_chain_apis.sh [BASE_URL] [DATABASE] [USERNAME] [PASSWORD]
#
# Defaults target local Odoo when docker-compose exposes port 8070:
#   BASE_URL=http://127.0.0.1:8070  DATABASE=lugal_local  USERNAME=admin  PASSWORD=admin
#
# Requires: curl, python3 (for JSON parsing; optional jq)
#
# Note: All routes below are type=jsonrpc → HTTP POST (not GET), including .../<id>/get.

set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8070}"
DB="${2:-lugal_local}"
USER="${3:-admin}"
PASS="${4:-admin}"

die() { echo "ERROR: $*" >&2; exit 1; }

command -v curl >/dev/null || die "curl required"
command -v python3 >/dev/null || die "python3 required"

jsonrpc() {
  local path="$1"
  local params_json="$2"
  curl -sS -X POST "${BASE_URL}${path}" \
    -H "Content-Type: application/json" \
    -H "X-Odoo-Database: ${DB}" \
    -H "Authorization: Bearer ${JWT:-}" \
    -d "{\"jsonrpc\":\"2.0\",\"method\":\"call\",\"params\":${params_json},\"id\":1}"
}

echo "=============================================="
echo "  Supply Chain API runtime test"
echo "  Base URL: ${BASE_URL}"
echo "  Database: ${DB}"
echo "  User:     ${USER}"
echo "=============================================="

echo -n "Health (Odoo web) ... "
CODE=$(curl -sS -o /dev/null -w "%{http_code}" --connect-timeout 3 "${BASE_URL}/web/health" 2>/dev/null || echo "000")
CODE=$(echo "$CODE" | tr -d '\r\n')
echo "HTTP ${CODE}"
if [[ "$CODE" != "200" ]]; then
  echo "Odoo does not respond at ${BASE_URL}. Start Odoo (e.g. docker compose up) and re-run."
  exit 1
fi

echo -n "Login POST /lugal/auth/login ... "
LOGIN_RAW=$(curl -sS -X POST "${BASE_URL}/lugal/auth/login" \
  -H "Content-Type: application/json" \
  -H "X-Odoo-Database: ${DB}" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"call\",\"params\":{\"username\":\"${USER}\",\"password\":\"${PASS}\"},\"id\":1}" \
  --connect-timeout 5) || LOGIN_RAW=""

JWT=$(echo "$LOGIN_RAW" | python3 -c "import sys,json; r=json.load(sys.stdin); t=r.get('result') or {}; d=t.get('data') or {}; print(d.get('access_token',''))" 2>/dev/null || true)
if [[ -z "${JWT}" ]]; then
  echo "FAIL"
  echo "$LOGIN_RAW" | head -c 400
  echo ""
  die "Could not obtain JWT. Check DB name, credentials, and that lugal_auth is installed."
fi
echo "OK (token received)"

pass=0
fail=0

check_list() {
  local name="$1"
  local path="$2"
  local raw
  raw=$(jsonrpc "$path" '{"page":1,"per_page":50}')
  local ok
  ok=$(echo "$raw" | python3 -c "
import sys,json
r=json.load(sys.stdin)
res=r.get('result') or {}
ok = res.get('success') is True and res.get('data') is not None
data = res.get('data') or {}
items = data.get('items')
if items is None:
  items = data.get('items')  # po uses 'items'
cnt = len(items) if isinstance(items, list) else -1
print('1' if ok and cnt >= 0 else '0', cnt)
" 2>/dev/null || echo "0 -1")
  local flag="${ok%% *}"
  local cnt="${ok##* }"
  if [[ "$flag" == "1" ]]; then
    echo "PASS  ${name}  (items=${cnt})"
    pass=$((pass+1))
  else
    echo "FAIL  ${name}"
    echo "$raw" | head -c 300
    echo ""
    fail=$((fail+1))
  fi
}

check_detail() {
  local name="$1"
  local path="$2"
  local raw
  raw=$(jsonrpc "$path" "{}")
  local ok
  ok=$(echo "$raw" | python3 -c "
import sys,json
r=json.load(sys.stdin)
res=r.get('result') or {}
print('1' if res.get('success') is True and res.get('data') else '0')
" 2>/dev/null || echo "0")
  if [[ "$ok" == "1" ]]; then
    echo "PASS  ${name}"
    pass=$((pass+1))
  else
    echo "FAIL  ${name}"
    echo "$raw" | head -c 400
    echo ""
    fail=$((fail+1))
  fi
}

# --- Resolve demo ids from list responses (first row)
first_id() {
  local path="$1"
  local key="$2"
  local raw
  raw=$(jsonrpc "$path" '{"page":1,"per_page":5}')
  echo "$raw" | python3 -c "
import sys,json
r=json.load(sys.stdin)
res=r.get('result') or {}
data=res.get('data') or {}
items=data.get('items') or []
if not items:
  sys.exit(1)
row=items[0]
print(row.get('${key}', row.get('id','')))
" 2>/dev/null || true
}

check_list "item_requests/list" "/api/crm/supply/item_requests/list"
IR_ID=$(first_id "/api/crm/supply/item_requests/list" "id")
if [[ -n "${IR_ID}" ]]; then
  check_detail "item_requests/${IR_ID}/get (POST)" "/api/crm/supply/item_requests/${IR_ID}/get"
else
  echo "SKIP detail item_requests/get — no id from list"
  fail=$((fail+1))
fi

check_list "negotiations/list" "/api/crm/supply/negotiations/list"
NEG_ID=$(first_id "/api/crm/supply/negotiations/list" "id")
if [[ -n "${NEG_ID}" ]]; then
  check_detail "negotiations/${NEG_ID}/get (POST)" "/api/crm/supply/negotiations/${NEG_ID}/get"
else
  echo "SKIP detail negotiations/get — no id from list"
  fail=$((fail+1))
fi

check_list "po/list" "/api/crm/supply/po/list"
PO_ID=$(first_id "/api/crm/supply/po/list" "id")
if [[ -n "${PO_ID}" ]]; then
  check_detail "po/${PO_ID}/get (POST)" "/api/crm/supply/po/${PO_ID}/get"
else
  echo "SKIP detail po/get — no id from list"
  fail=$((fail+1))
fi

check_list "payments/list" "/api/crm/supply/payments/list"
PAY_ID=$(first_id "/api/crm/supply/payments/list" "id")
if [[ -n "${PAY_ID}" ]]; then
  check_detail "payments/${PAY_ID}/get (POST)" "/api/crm/supply/payments/${PAY_ID}/get"
else
  echo "SKIP detail payments/get — no id from list"
  fail=$((fail+1))
fi

check_list "shipments/list" "/api/crm/supply/shipments/list"
SHIP_ID=$(first_id "/api/crm/supply/shipments/list" "id")
if [[ -n "${SHIP_ID}" ]]; then
  check_detail "shipments/${SHIP_ID}/get (POST)" "/api/crm/supply/shipments/${SHIP_ID}/get"
else
  echo "SKIP detail shipments/get — no id from list"
  fail=$((fail+1))
fi

echo ""
echo "=============================================="
echo "  Passed: ${pass}  Failed: ${fail}"
echo "=============================================="
[[ "$fail" -eq 0 ]]
