#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test folder 34 documents after Many2many fix"""
import json
import urllib.request

BASE_URL = "http://localhost:8070"
DB = "lugal_local"

def req(method, path, body=None, headers=None, is_jsonrpc=False):
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
print("Testing Folder 34 Documents - After Many2many Fix")
print("="*80)

# Login
status, resp = req("POST", "/api/auth/login", {"db": DB, "username": "admin", "password": "admin"})
token = resp.get('access_token') if resp else None
if not token:
    print("✗ Login failed")
    exit(1)
print(f"✓ Login successful")

# Test folder 34 documents
print("\n" + "="*80)
print("Getting documents from folder 34:")
print("="*80)
status, resp = req("POST", "/api/folders/34/documents", {}, {"Authorization": f"Bearer {token}"}, is_jsonrpc=True)
print(json.dumps(resp, indent=2, ensure_ascii=False))

if resp and resp.get('success'):
    folder = resp.get('folder', {})
    docs = resp.get('data', [])
    print("\n" + "="*80)
    print("SUMMARY:")
    print("="*80)
    print(f"Folder: {folder.get('name')} (ID: {folder.get('id')})")
    print(f"Document Count: {folder.get('document_count')}")
    print(f"Documents Returned: {len(docs)}")
    if docs:
        print("\nDocuments:")
        for doc in docs:
            print(f"  - ID {doc.get('id')}: {doc.get('title')}")
        print("\n✅ SUCCESS: Documents are now showing!")
    else:
        print("\n❌ FAILED: Still no documents showing")
