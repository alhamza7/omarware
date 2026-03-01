#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive NBS Archive API Test Suite
Tests all major endpoints: folders, documents, departments, auth, etc.
Usage: python3 test_all_nbs_apis.py [BASE_URL] [DB] [USER] [PASS]
"""
import json
import sys
import urllib.request
import urllib.error
import base64
from datetime import datetime

# Configuration
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

# Global state
PASSED = 0
FAILED = 0
TOKEN = None
DEPARTMENT_ID = None
FOLDER_ID = None
DOCUMENT_ID = None
CREATED_FOLDER_IDS = []
CREATED_DOCUMENT_IDS = []


def colorize(text, color):
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def req(method, path, body=None, headers=None, is_jsonrpc=False):
    """Make HTTP request"""
    url = f"{BASE_URL}{path}"
    h = {"Content-Type": "application/json", "X-Odoo-Database": DB}
    if headers:
        h.update(headers)
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    
    data = None
    if body is not None:
        if is_jsonrpc:
            # JSON-RPC format
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": body,
                "id": 1
            }
            data = json.dumps(payload).encode("utf-8")
        else:
            data = json.dumps(body).encode("utf-8")
    
    req_obj = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req_obj, timeout=15) as r:
            raw = r.read().decode("utf-8")
            result = json.loads(raw) if raw else None
            # Extract result from JSON-RPC response
            if is_jsonrpc and result and isinstance(result, dict):
                if 'result' in result:
                    return r.getcode(), result['result']
                elif 'error' in result:
                    return r.getcode(), {'success': False, 'error': result['error']}
            return r.getcode(), result
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        try:
            body_err = json.loads(raw) if raw else None
        except:
            body_err = {"error": raw or str(e)}
        return e.code, body_err
    except Exception as e:
        return 0, {"error": str(e)}


def test(name, method, path, body=None, headers=None, expect_status=200, is_jsonrpc=False, check_success=True):
    """Run a test"""
    global PASSED, FAILED
    print(f"\n{'='*80}")
    print(f"TEST: {name}")
    print(f"{'='*80}")
    print(f"→ {method} {path}")
    if body:
        print(f"  Body: {json.dumps(body, indent=2)[:200]}...")
    
    status, resp = req(method, path, body, headers, is_jsonrpc)
    
    passed = False
    if status == expect_status:
        if check_success and isinstance(resp, dict):
            if resp.get('success') in (True, None) or resp.get('status') == 'healthy':
                passed = True
            elif resp.get('success') is False:
                print(colorize(f"✗ FAILED: API returned success=False", 'red'))
                print(f"  Error: {resp.get('error', 'Unknown')}")
        else:
            passed = True
    else:
        print(colorize(f"✗ FAILED: Expected {expect_status}, got {status}", 'red'))
        if resp:
            print(f"  Response: {json.dumps(resp, indent=2)[:300]}")
    
    if passed:
        PASSED += 1
        print(colorize(f"✓ PASSED", 'green'))
        if resp and isinstance(resp, dict):
            if 'data' in resp:
                print(f"  Data: {json.dumps(resp['data'], indent=2)[:300]}...")
            elif 'count' in resp:
                print(f"  Count: {resp['count']}")
    else:
        FAILED += 1
        if resp:
            print(f"  Full response: {json.dumps(resp, indent=2)[:500]}")
    
    return passed, resp


def run_tests():
    """Run all API tests"""
    global TOKEN, DEPARTMENT_ID, FOLDER_ID, DOCUMENT_ID
    
    print(colorize(f"\n{'='*80}", 'blue'))
    print(colorize(f"  NBS ARCHIVE API - COMPREHENSIVE TEST SUITE", 'blue'))
    print(colorize(f"{'='*80}\n", 'blue'))
    print(f"Base URL: {BASE_URL}")
    print(f"Database: {DB}")
    print(f"User: {USER}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ========== 1. HEALTH CHECK ==========
    print(colorize("\n\n[1] HEALTH CHECK", 'yellow'))
    test("Health check", "GET", "/api/health", check_success=False)
    
    # ========== 2. AUTHENTICATION ==========
    print(colorize("\n\n[2] AUTHENTICATION", 'yellow'))
    passed, resp = test("Login", "POST", "/api/auth/login", {
        "db": DB,
        "username": USER,
        "password": PASS
    })
    print(f"  → Full login response: {json.dumps(resp, indent=2)[:500]}")
    if passed and resp:
        # Token might be 'token', 'access_token', or in 'data'
        TOKEN = resp.get('access_token') or resp.get('token') or (resp.get('data') or {}).get('access_token') or (resp.get('data') or {}).get('token')
        if TOKEN:
            print(colorize(f"  → Token: {TOKEN[:50]}...", 'green'))
        else:
            print(colorize(f"  → Warning: No token found in response", 'yellow'))
    
    if TOKEN:
        test("Get current user info", "POST", "/api/auth/me", {})
    
    # ========== 3. DEPARTMENTS ==========
    print(colorize("\n\n[3] DEPARTMENTS", 'yellow'))
    passed, resp = test("List departments", "POST", "/api/departments", {}, is_jsonrpc=True)
    if passed and resp and resp.get('data'):
        depts = resp['data']
        if depts:
            DEPARTMENT_ID = depts[0]['id']
            print(colorize(f"  → Using department_id: {DEPARTMENT_ID} ({depts[0].get('name', 'N/A')})", 'green'))
    
    if not DEPARTMENT_ID:
        print(colorize("  Warning: No department found, using ID=1", 'yellow'))
        DEPARTMENT_ID = 1
    
    test("Get single department", "POST", f"/api/departments/{DEPARTMENT_ID}", {}, is_jsonrpc=True)
    
    # ========== 4. DOCUMENT TYPES ==========
    print(colorize("\n\n[4] DOCUMENT TYPES", 'yellow'))
    test("List document types", "POST", "/api/document-types", {"department_id": DEPARTMENT_ID}, is_jsonrpc=True)
    
    # ========== 5. TAGS ==========
    print(colorize("\n\n[5] TAGS", 'yellow'))
    test("List tags", "POST", "/api/tags", {}, is_jsonrpc=True)
    
    # ========== 6. FOLDERS (MAIN FOCUS) ==========
    print(colorize("\n\n[6] FOLDERS - COMPREHENSIVE TESTS", 'yellow'))
    
    # List folders
    passed, resp = test("List all folders", "POST", "/api/folders", {"department_id": DEPARTMENT_ID}, is_jsonrpc=True)
    existing_folders = []
    if passed and resp and resp.get('data'):
        existing_folders = resp['data']
        print(f"  → Found {len(existing_folders)} existing folders")
    
    # Create folder (proper object)
    new_folder_data = {
        "name": f"Test Folder {datetime.now().strftime('%H%M%S')}",
        "code": f"TF{datetime.now().strftime('%H%M%S')}",
        "department_id": DEPARTMENT_ID,
        "description": "Test folder created by API test suite",
        "icon": "fa-folder",
        "color": 3,
        "sequence": 10
    }
    passed, resp = test("Create folder (proper object)", "POST", "/api/folders/create", 
                        new_folder_data, is_jsonrpc=True)
    if passed and resp and resp.get('data'):
        FOLDER_ID = resp['data'].get('id')
        if FOLDER_ID:
            CREATED_FOLDER_IDS.append(FOLDER_ID)
            print(colorize(f"  → Created folder ID: {FOLDER_ID}", 'green'))
    
    # Create folder (single dict as first arg - test the new controller logic)
    single_dict_folder = {
        "name": f"Single Dict Folder {datetime.now().strftime('%H%M%S')}",
        "code": f"SDF{datetime.now().strftime('%H%M%S')}",
        "department_id": DEPARTMENT_ID,
        "description": "Folder created with single dict param"
    }
    passed, resp = test("Create folder (single dict param)", "POST", "/api/folders/create",
                        single_dict_folder, is_jsonrpc=True)
    if passed and resp and resp.get('data'):
        fid = resp['data'].get('id')
        if fid:
            CREATED_FOLDER_IDS.append(fid)
    
    # Get folder details
    if FOLDER_ID:
        test("Get folder details", "POST", f"/api/folders/{FOLDER_ID}", {}, is_jsonrpc=True)
        
        # Update folder
        test("Update folder", "POST", f"/api/folders/{FOLDER_ID}/update", {
            "description": "Updated by API test",
            "color": 5
        }, is_jsonrpc=True)
        
        # Move folder
        test("Move folder to root", "POST", f"/api/folders/{FOLDER_ID}/move", {
            "target_parent_id": None
        }, is_jsonrpc=True)
    
    # Get folder tree
    test("Get folder tree", "POST", "/api/folders/tree", {"department_id": DEPARTMENT_ID}, is_jsonrpc=True)
    
    # List folders with parent_id filter
    test("List root folders", "POST", "/api/folders", {
        "department_id": DEPARTMENT_ID,
        "parent_id": 0
    }, is_jsonrpc=True)
    
    # ========== 7. DOCUMENTS ==========
    print(colorize("\n\n[7] DOCUMENTS", 'yellow'))
    
    # List documents
    passed, resp = test("List documents", "POST", "/api/documents", {
        "department_id": DEPARTMENT_ID,
        "page": 1,
        "per_page": 10
    }, is_jsonrpc=True)
    existing_docs = []
    if passed and resp and resp.get('data'):
        existing_docs = resp['data']
        if existing_docs:
            DOCUMENT_ID = existing_docs[0]['id']
            print(f"  → Found {len(existing_docs)} documents, using ID: {DOCUMENT_ID}")
    
    # Get document details
    if DOCUMENT_ID:
        test("Get document details", "POST", f"/api/documents/{DOCUMENT_ID}", {}, is_jsonrpc=True)
        test("Get document versions", "POST", f"/api/documents/{DOCUMENT_ID}/versions", {}, is_jsonrpc=True)
    
    # List trash
    test("List trashed documents", "POST", "/api/documents/trash", {"page": 1, "per_page": 10}, is_jsonrpc=True)
    
    # ========== 8. RELATIONS ==========
    print(colorize("\n\n[8] DOCUMENT RELATIONS", 'yellow'))
    if DOCUMENT_ID:
        test("Get document relations", "POST", f"/api/documents/{DOCUMENT_ID}/relations", {}, is_jsonrpc=True)
    
    # Get folders via relations endpoint
    test("Get folders (relations)", "POST", "/api/folders", {
        "department_id": DEPARTMENT_ID,
        "state": "active"
    }, is_jsonrpc=True)
    
    if FOLDER_ID:
        test("Get folder documents (relations)", "POST", f"/api/folders/{FOLDER_ID}/documents", {}, is_jsonrpc=True)
    
    # ========== 9. SEARCH ==========
    print(colorize("\n\n[9] SEARCH", 'yellow'))
    test("Advanced search", "POST", "/api/search/advanced", {
        "query": "test",
        "department_ids": [DEPARTMENT_ID],
        "page": 1,
        "per_page": 10
    }, is_jsonrpc=True)
    
    # ========== 10. TEMPLATES ==========
    print(colorize("\n\n[10] TEMPLATES", 'yellow'))
    test("List templates", "POST", "/api/templates", {"department_id": DEPARTMENT_ID}, is_jsonrpc=True)
    
    # ========== 11. BATCH OPERATIONS ==========
    print(colorize("\n\n[11] BATCH OPERATIONS", 'yellow'))
    if len(existing_docs) >= 2:
        doc_ids = [d['id'] for d in existing_docs[:2]]
        test("Batch move to folder", "POST", "/api/documents/batch/move-folder", {
            "document_ids": doc_ids,
            "target_folder_id": FOLDER_ID or 1
        }, is_jsonrpc=True, check_success=False)
    
    # ========== 12. MOBILE API ==========
    print(colorize("\n\n[12] MOBILE API", 'yellow'))
    test("Mobile sync", "POST", "/api/mobile/sync", {
        "last_sync_date": None
    }, is_jsonrpc=True, check_success=False)
    
    # ========== 13. DASHBOARD & STATS ==========
    print(colorize("\n\n[13] DASHBOARD & STATS", 'yellow'))
    test("Dashboard stats", "POST", "/api/stats/dashboard", {}, is_jsonrpc=True)
    
    # ========== 14. AUDIT LOGS ==========
    print(colorize("\n\n[14] AUDIT LOGS", 'yellow'))
    test("List audit logs", "POST", "/api/audit-logs", {
        "page": 1,
        "per_page": 10
    }, is_jsonrpc=True)
    
    # ========== 15. BULK UPLOAD ==========
    print(colorize("\n\n[15] BULK UPLOAD", 'yellow'))
    test("List bulk upload jobs", "POST", "/api/documents/bulk-upload/jobs", {}, is_jsonrpc=True)
    
    # ========== 16. WEBSOCKET POLLING ==========
    print(colorize("\n\n[16] WEBSOCKET POLLING", 'yellow'))
    test("Poll notifications", "POST", "/api/ws/poll", {"last_poll_id": 0}, is_jsonrpc=True, check_success=False)
    
    # ========== CLEANUP ==========
    print(colorize("\n\n[CLEANUP] Deleting created test folders", 'yellow'))
    for fid in CREATED_FOLDER_IDS:
        try:
            status, resp = req("DELETE", f"/api/folders/{fid}")
            if status == 200:
                print(colorize(f"  ✓ Deleted folder {fid}", 'green'))
            else:
                print(colorize(f"  ✗ Failed to delete folder {fid}: {resp.get('error', 'Unknown')}", 'red'))
        except Exception as e:
            print(colorize(f"  ✗ Error deleting folder {fid}: {e}", 'red'))


def main():
    """Main entry point"""
    try:
        run_tests()
    except KeyboardInterrupt:
        print(colorize("\n\nTests interrupted by user", 'yellow'))
    except Exception as e:
        print(colorize(f"\n\nFatal error: {e}", 'red'))
        import traceback
        traceback.print_exc()
    finally:
        print(colorize(f"\n\n{'='*80}", 'blue'))
        print(colorize(f"  TEST SUMMARY", 'blue'))
        print(colorize(f"{'='*80}", 'blue'))
        print(f"  Total tests: {PASSED + FAILED}")
        print(colorize(f"  Passed: {PASSED}", 'green'))
        print(colorize(f"  Failed: {FAILED}", 'red'))
        if FAILED == 0:
            print(colorize(f"\n  ✓ ALL TESTS PASSED!", 'green'))
        else:
            print(colorize(f"\n  ✗ Some tests failed. Review output above.", 'red'))
        print(colorize(f"{'='*80}\n", 'blue'))


if __name__ == '__main__':
    main()
