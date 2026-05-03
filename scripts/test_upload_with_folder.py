#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test document upload and show full response with folder information"""
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
            if is_jsonrpc and result and isinstance(result, dict) and 'result' in result:
                return r.getcode(), result['result']
            return r.getcode(), result
    except Exception as e:
        return 0, {"error": str(e)}

print("="*80)
print("Test Document Upload - Full Response with Folder Info")
print("="*80)

# Login
print("\n[1] Login...")
status, resp = req("POST", "/api/auth/login", {"db": DB, "username": USER, "password": PASS})
token = resp.get('access_token') if resp else None
if not token:
    print(f"✗ Login failed")
    exit(1)
print(f"✓ Token: {token[:50]}...")

# Get department
status, resp = req("POST", "/api/departments", {}, {"Authorization": f"Bearer {token}"}, is_jsonrpc=True)
dept_id = resp['data'][0]['id'] if resp and resp.get('data') else None
print(f"✓ Department ID: {dept_id}")

# Get document type
status, resp = req("POST", "/api/document-types", {"department_id": dept_id}, {"Authorization": f"Bearer {token}"}, is_jsonrpc=True)
doc_type_id = resp['data'][0]['id'] if resp and resp.get('data') else None
print(f"✓ Document Type ID: {doc_type_id}")

# Test 1: Upload without folder
print("\n" + "="*80)
print("TEST 1: Upload document WITHOUT folder")
print("="*80)
test_content = "Test document without folder"
file_data = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
upload_data = {
    "department_id": dept_id,
    "document_type_id": doc_type_id,
    "title": "Test Doc - No Folder",
    "file_data": file_data,
    "file_name": "test_no_folder.txt",
    "confidentiality_level": "internal",
    "upload_kind": "main"
}
status, resp = req("POST", "/api/documents/upload", upload_data, {"Authorization": f"Bearer {token}"})
print(f"\nResponse:")
print(json.dumps(resp, indent=2, ensure_ascii=False))

# Test 2: Upload with auto-create folder
print("\n" + "="*80)
print("TEST 2: Upload document WITH auto-create folder")
print("="*80)
test_content = "Test document with auto-created folder"
file_data = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
upload_data = {
    "department_id": dept_id,
    "document_type_id": doc_type_id,
    "title": "Test Doc - Auto Folder",
    "file_data": file_data,
    "file_name": "test_with_folder.txt",
    "confidentiality_level": "internal",
    "upload_kind": "main",
    "create_folder": True,
    "folder_name": "My Test Folder",
    "folder_code": "MTF001"
}
status, resp = req("POST", "/api/documents/upload", upload_data, {"Authorization": f"Bearer {token}"})
print(f"\nResponse:")
print(json.dumps(resp, indent=2, ensure_ascii=False))

# Test 3: Upload with existing folder_id
print("\n" + "="*80)
print("TEST 3: Upload document TO existing folder")
print("="*80)

# Get existing folders
status, folders_resp = req("POST", "/api/folders", {"department_id": dept_id}, {"Authorization": f"Bearer {token}"}, is_jsonrpc=True)
existing_folder_id = folders_resp['data'][0]['id'] if folders_resp and folders_resp.get('data') else None

if existing_folder_id:
    print(f"✓ Using existing folder ID: {existing_folder_id}")
    test_content = "Test document linked to existing folder"
    file_data = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
    upload_data = {
        "department_id": dept_id,
        "document_type_id": doc_type_id,
        "title": "Test Doc - Existing Folder",
        "file_data": file_data,
        "file_name": "test_existing_folder.txt",
        "confidentiality_level": "internal",
        "upload_kind": "main",
        "folder_id": existing_folder_id
    }
    status, resp = req("POST", "/api/documents/upload", upload_data, {"Authorization": f"Bearer {token}"})
    print(f"\nResponse:")
    print(json.dumps(resp, indent=2, ensure_ascii=False))
else:
    print("✗ No existing folders found, skipping test 3")

print("\n" + "="*80)
print("✓ All tests completed!")
print("="*80)
