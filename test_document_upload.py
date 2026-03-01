#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test document upload to verify filestore path fix
"""
import json
import urllib.request
import base64

BASE_URL = "http://localhost:8070"
DB = "lugal_local"
USER = "admin"
PASS = "admin"

def req(method, path, body=None, headers=None, is_jsonrpc=False):
    """Make HTTP request"""
    url = f"{BASE_URL}{path}"
    h = {"Content-Type": "application/json", "X-Odoo-Database": DB}
    if headers:
        h.update(headers)
    data = None
    if body is not None:
        if is_jsonrpc:
            payload = {"jsonrpc": "2.0", "method": "call", "params": body, "id": 1}
            data = json.dumps(payload).encode("utf-8")
        else:
            data = json.dumps(body).encode("utf-8")
    req_obj = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req_obj, timeout=15) as r:
            raw = r.read().decode("utf-8")
            result = json.loads(raw) if raw else None
            # Extract result from JSON-RPC
            if is_jsonrpc and result and isinstance(result, dict) and 'result' in result:
                return r.getcode(), result['result']
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


def main():
    print("="*80)
    print("Testing Document Upload - Filestore Path Fix")
    print("="*80)
    
    # 1. Login
    print("\n[1] Logging in...")
    status, resp = req("POST", "/api/auth/login", {
        "db": DB,
        "username": USER,
        "password": PASS
    })
    
    if status != 200 or not resp or not resp.get('access_token'):
        print(f"✗ Login failed: {resp}")
        return
    
    token = resp['access_token']
    print(f"✓ Login successful, token: {token[:50]}...")
    
    # 2. Get departments
    print("\n[2] Getting departments...")
    status, resp = req("POST", "/api/departments", {}, {
        "Authorization": f"Bearer {token}"
    }, is_jsonrpc=True)
    
    if status != 200 or not resp or not resp.get('data'):
        print(f"✗ Failed to get departments: {resp}")
        return
    
    dept_id = resp['data'][0]['id']
    print(f"✓ Using department ID: {dept_id}")
    
    # 3. Get document types
    print("\n[3] Getting document types...")
    status, resp = req("POST", "/api/document-types", {
        "department_id": dept_id
    }, {
        "Authorization": f"Bearer {token}"
    }, is_jsonrpc=True)
    
    if status != 200 or not resp or not resp.get('data'):
        print(f"✗ Failed to get document types: {resp}")
        return
    
    doc_type_id = resp['data'][0]['id']
    print(f"✓ Using document type ID: {doc_type_id}")
    
    # 4. Create a test file (simple text file as base64)
    print("\n[4] Preparing test file...")
    test_content = "This is a test document to verify filestore path fix.\nUpload date: 2026-02-08"
    file_data = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
    file_name = "test_upload_filestore.txt"
    print(f"✓ Test file prepared: {file_name}")
    
    # 5. Upload document
    print("\n[5] Uploading document...")
    upload_data = {
        "department_id": dept_id,
        "document_type_id": doc_type_id,
        "title": "Test Document - Filestore Path Fix",
        "file_data": file_data,
        "file_name": file_name,
        "confidentiality_level": "internal",
        "upload_kind": "main"
    }
    
    status, resp = req("POST", "/api/documents/upload", upload_data, {
        "Authorization": f"Bearer {token}"
    })
    
    print(f"\n{'='*80}")
    if status == 200 and resp and resp.get('success'):
        print("✓ SUCCESS: Document uploaded successfully!")
        print(f"  Document ID: {resp['data']['id']}")
        print(f"  Barcode: {resp['data']['barcode']}")
        print(f"  Message: {resp['data']['message']}")
        print("\n✓ Filestore path fix verified - no permission errors!")
        print(f"{'='*80}")
        return True
    else:
        print("✗ FAILED: Document upload failed")
        print(f"  Status: {status}")
        print(f"  Response: {json.dumps(resp, indent=2)}")
        if resp and 'error' in resp:
            error_msg = resp['error']
            if 'Permission denied' in error_msg:
                print("\n✗ PERMISSION ERROR STILL EXISTS:")
                print(f"  {error_msg}")
                print("\n  Possible solutions:")
                print("  1. Verify odoo_local.conf has: data_dir = /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai/filestore_local")
                print("  2. Verify filestore_local directory exists and has write permissions")
                print("  3. Restart Odoo to apply config changes")
            else:
                print(f"\n  Error: {error_msg}")
        print(f"{'='*80}")
        return False


if __name__ == '__main__':
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
