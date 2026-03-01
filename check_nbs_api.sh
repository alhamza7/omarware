#!/usr/bin/env bash
# NBS Archive API check – runs health + login and reports success/failure

BASE_URL="${1:-http://localhost:8070}"
DB="${2:-lugal_local}"
USER="${3:-admin}"
PASS="${4:-admin}"

echo "=============================================="
echo "  NBS Archive API Check"
echo "=============================================="
echo "  Base URL: $BASE_URL"
echo "  Database: $DB"
echo "  User:     $USER"
echo "=============================================="
echo ""

PASSED=0
FAILED=0

# 1. Health check
echo -n "1. GET /api/health ... "
HTTP=$(curl -s -o /tmp/nbs_api_health.json -w "%{http_code}" "$BASE_URL/api/health" 2>/dev/null || echo "000")
if [ "$HTTP" = "200" ]; then
    if grep -q '"status"' /tmp/nbs_api_health.json 2>/dev/null; then
        echo "OK (200)"
        PASSED=$((PASSED+1))
    else
        echo "FAIL (200 but invalid JSON)"
        FAILED=$((FAILED+1))
    fi
else
    echo "FAIL (HTTP $HTTP)"
    FAILED=$((FAILED+1))
fi

# 2. Login with X-Odoo-Database header
echo -n "2. POST /api/auth/login (X-Odoo-Database header) ... "
HTTP=$(curl -s -o /tmp/nbs_api_login1.json -w "%{http_code}" -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -H "X-Odoo-Database: $DB" \
    -d "{\"username\":\"$USER\",\"password\":\"$PASS\"}" 2>/dev/null || echo "000")
if [ "$HTTP" = "200" ]; then
    if grep -q '"access_token"' /tmp/nbs_api_login1.json 2>/dev/null || grep -q '"success":true' /tmp/nbs_api_login1.json 2>/dev/null; then
        echo "OK (200, token received)"
        PASSED=$((PASSED+1))
    else
        echo "FAIL (200 but no token - check credentials or DB)"
        cat /tmp/nbs_api_login1.json 2>/dev/null | head -c 200
        echo ""
        FAILED=$((FAILED+1))
    fi
else
    echo "FAIL (HTTP $HTTP)"
    cat /tmp/nbs_api_login1.json 2>/dev/null | head -c 200
    echo ""
    FAILED=$((FAILED+1))
fi

# 3. Login with database in body
echo -n "3. POST /api/auth/login (database in body) ... "
HTTP=$(curl -s -o /tmp/nbs_api_login2.json -w "%{http_code}" -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"database\":\"$DB\",\"username\":\"$USER\",\"password\":\"$PASS\"}" 2>/dev/null || echo "000")
if [ "$HTTP" = "200" ]; then
    if grep -q '"access_token"' /tmp/nbs_api_login2.json 2>/dev/null || grep -q '"success":true' /tmp/nbs_api_login2.json 2>/dev/null; then
        echo "OK (200, token received)"
        PASSED=$((PASSED+1))
    else
        echo "FAIL (200 but no token)"
        FAILED=$((FAILED+1))
    fi
else
    echo "FAIL (HTTP $HTTP)"
    FAILED=$((FAILED+1))
fi

echo ""
echo "=============================================="
echo "  Result: $PASSED passed, $FAILED failed"
echo "=============================================="

if [ "$FAILED" -gt 0 ]; then
    echo ""
    echo "Tip: Restart Odoo and ensure nbs_archive is installed:"
    echo "  pkill -f odoo-bin"
    echo "  ./venv/bin/python odoo-bin -c odoo_local.conf -d $DB -i nbs_archive --stop-after-init -p 8079"
    echo "  ./start_local.sh  # or your start command"
    exit 1
fi
exit 0
