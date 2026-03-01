#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NBS Archive API – Full endpoint check.
Tests health, auth, documents, departments, folders, search, notifications, etc.
Uses only stdlib (json, urllib). Run: python3 check_nbs_api_full.py [BASE_URL] [DB] [USER] [PASS]
"""
import json
import sys
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8070"
DB = "lugal_local"
USER = "admin"
PASS = "admin"

if len(sys.argv) >= 2:
    BASE_URL = sys.argv[1].rstrip("/")
if len(sys.argv) >= 3:
    DB = sys.argv[2]
if len(sys.argv) >= 4:
    USER = sys.argv[3]
if len(sys.argv) >= 5:
    PASS = sys.argv[4]

PASSED = 0
FAILED = 0
TOKEN = None


def req(method, path, body=None, headers=None, is_jsonrpc=False):
    url = f"{BASE_URL}{path}"
    h = {"Content-Type": "application/json", "X-Odoo-Database": DB}
    if headers:
        h.update(headers)
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req_obj = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req_obj, timeout=15) as r:
            raw = r.read().decode("utf-8")
            return r.getcode(), json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        try:
            body = json.loads(raw) if raw else None
        except Exception:
            body = None
        return e.code, body
    except Exception as e:
        return 0, {"error": str(e)}


def jsonrpc(path, params=None):
    body = {"jsonrpc": "2.0", "method": "call", "params": params or {}, "id": 1}
    code, out = req("POST", path, body, is_jsonrpc=True)
    if code != 200:
        return code, out
    # Odoo jsonrpc returns { "jsonrpc": "2.0", "result": {...}, "id": 1 } or direct result
    if out and "result" in out:
        out = out["result"]
    return code, out


def ok(name, code, data, want_200=True, want_success=True):
    global PASSED, FAILED
    if want_200 and code != 200:
        print(f"  FAIL {name}: HTTP {code} (expected 200)")
        FAILED += 1
        return
    if data is None:
        print(f"  FAIL {name}: no response body")
        FAILED += 1
        return
    if want_success and isinstance(data, dict) and data.get("success") is False:
        err = data.get("error", "unknown")
        print(f"  FAIL {name}: success=false, error={err}")
        FAILED += 1
        return
    print(f"  OK   {name}")
    PASSED += 1


def main():
    global TOKEN
    print("==============================================")
    print("  NBS Archive API – Full check")
    print("==============================================")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Database: {DB}")
    print(f"  User:     {USER}")
    print("==============================================")

    # 1. Health
    code, data = req("GET", "/api/health")
    ok("GET /api/health", code, data, want_success=False)
    if code != 200:
        print("  Cannot continue without health. Is Odoo running with nbs_archive?")
        print(f"  Result: {PASSED} passed, {FAILED} failed")
        sys.exit(1)

    # 2. Login (plain JSON)
    code, data = req("POST", "/api/auth/login", {"username": USER, "password": PASS})
    ok("POST /api/auth/login", code, data, want_success=False)
    if data and data.get("access_token"):
        TOKEN = data["access_token"]
    elif data and data.get("success") and data.get("access_token"):
        TOKEN = data["access_token"]
    else:
        print("  No token; authenticated endpoints will fail.")
        TOKEN = None

    # 3. Me (plain JSON)
    code, data = req("POST", "/api/auth/me", {})
    ok("POST /api/auth/me", code, data)

    # 4. Documents list (jsonrpc)
    code, data = jsonrpc("/api/documents", {"page": 1, "per_page": 5})
    ok("POST /api/documents (list)", code, data)

    # 5. Departments (jsonrpc)
    code, data = jsonrpc("/api/departments")
    ok("POST /api/departments", code, data)

    # 6. Document types (jsonrpc)
    code, data = jsonrpc("/api/document-types")
    ok("POST /api/document-types", code, data)

    # 7. Folders list (jsonrpc) – same path as folder_controller
    code, data = jsonrpc("/api/folders", {"department_id": None, "parent_id": None})
    ok("POST /api/folders", code, data)

    # 8. Folders tree (jsonrpc)
    code, data = jsonrpc("/api/folders/tree", {"department_id": None})
    ok("POST /api/folders/tree", code, data)

    # 9. Search (jsonrpc)
    code, data = jsonrpc("/api/search", {"q": "", "page": 1, "per_page": 5})
    ok("POST /api/search", code, data)

    # 10. Advanced search (jsonrpc)
    code, data = jsonrpc("/api/search/advanced", {"page": 1, "per_page": 5})
    ok("POST /api/search/advanced", code, data)

    # 11. Notifications (jsonrpc)
    code, data = jsonrpc("/api/notifications", {"page": 1, "per_page": 10})
    ok("POST /api/notifications", code, data)

    # 12. Notifications unread count (jsonrpc)
    code, data = jsonrpc("/api/notifications/unread-count")
    ok("POST /api/notifications/unread-count", code, data)

    # 13. Tags (jsonrpc)
    code, data = jsonrpc("/api/tags")
    ok("POST /api/tags", code, data)

    # 14. Stats dashboard (jsonrpc)
    code, data = jsonrpc("/api/stats/dashboard")
    ok("POST /api/stats/dashboard", code, data)

    # 15. Edit requests list (jsonrpc)
    code, data = jsonrpc("/api/edit-requests", {"page": 1, "per_page": 10})
    ok("POST /api/edit-requests", code, data)

    # 16. Pending approvals (jsonrpc)
    code, data = jsonrpc("/api/edit-requests/pending-approvals")
    ok("POST /api/edit-requests/pending-approvals", code, data)

    # 17. Audit logs (jsonrpc)
    code, data = jsonrpc("/api/audit-logs", {"page": 1, "per_page": 5})
    ok("POST /api/audit-logs", code, data)

    # 18. Templates list (jsonrpc)
    code, data = jsonrpc("/api/templates")
    ok("POST /api/templates", code, data)

    # 19. Workflows list (jsonrpc)
    code, data = jsonrpc("/api/workflows")
    ok("POST /api/workflows", code, data)

    # 20. Bulk upload jobs (jsonrpc)
    code, data = jsonrpc("/api/documents/bulk-upload/jobs")
    ok("POST /api/documents/bulk-upload/jobs", code, data)

    # 21. Mobile sync (jsonrpc)
    code, data = jsonrpc("/api/mobile/sync", {"last_sync": None})
    ok("POST /api/mobile/sync", code, data)

    print("")
    print("==============================================")
    print(f"  Result: {PASSED} passed, {FAILED} failed")
    print("==============================================")
    if FAILED > 0:
        print("")
        print("If you see 'deleted_by' or 'folder_id' does not exist:")
        print("  psql -d", DB, "-f addons/nbs_archive/scripts/add_deleted_by_id.sql")
        print("If you see 'document_number' or singleton/templates/bulk-upload errors:")
        print("  Restart Odoo so new controller code is loaded, then run this check again.")
        print("See addons/nbs_archive/NBS_API_VERIFICATION.md for full steps.")
    sys.exit(1 if FAILED > 0 else 0)


if __name__ == "__main__":
    main()
