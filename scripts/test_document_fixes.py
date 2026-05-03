#!/usr/bin/env python3
"""
Test script for document API fixes
Tests the following fixes:
1. Document role fields in API response
2. Move folder API for secondary documents
3. Duplicate name validation
4. Auto-folder deletion on main document delete

Usage:
    python3 test_document_fixes.py --base-url http://localhost:8069 --token YOUR_JWT_TOKEN
"""

import requests
import json
import sys
import argparse
from typing import Dict, Any, Optional


class DocumentAPITester:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        self.test_results = []
    
    def log(self, message: str, success: bool = True):
        """Log test result"""
        status = "✓" if success else "✗"
        color = "\033[92m" if success else "\033[91m"
        reset = "\033[0m"
        print(f"{color}{status}{reset} {message}")
        self.test_results.append({'message': message, 'success': success})
    
    def jsonrpc_call(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make JSON-RPC call"""
        url = f"{self.base_url}{endpoint}"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": params,
            "id": 1
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        
        result = response.json()
        if 'error' in result:
            raise Exception(f"RPC Error: {result['error']}")
        
        return result.get('result', {})
    
    def test_document_role_fields(self):
        """Test 1: Verify new document role fields in API response"""
        print("\n" + "="*60)
        print("TEST 1: Document Role Fields in API Response")
        print("="*60)
        
        try:
            # Get list of documents
            result = self.jsonrpc_call('/api/documents', {
                'page': 1,
                'per_page': 5
            })
            
            if not result.get('success'):
                self.log(f"Failed to get documents: {result.get('error')}", False)
                return
            
            documents = result.get('data', [])
            if not documents:
                self.log("No documents found to test", False)
                return
            
            # Check first document
            doc = documents[0]
            
            # Check for required fields
            required_fields = ['is_main_document', 'document_role', 'relation_type']
            missing_fields = [f for f in required_fields if f not in doc]
            
            if missing_fields:
                self.log(f"Missing fields: {missing_fields}", False)
                return
            
            self.log("All new fields present in response")
            
            # Verify field values
            if isinstance(doc['is_main_document'], bool):
                self.log("is_main_document is boolean")
            else:
                self.log(f"is_main_document is not boolean: {type(doc['is_main_document'])}", False)
            
            valid_roles = ['main', 'sub', 'attachment', 'other']
            if doc['document_role'] in valid_roles:
                self.log(f"document_role has valid value: {doc['document_role']}")
            else:
                self.log(f"document_role has invalid value: {doc['document_role']}", False)
            
            valid_relations = ['main', 'secondary_document', 'attachment']
            if doc['relation_type'] in valid_relations:
                self.log(f"relation_type has valid value: {doc['relation_type']}")
            else:
                self.log(f"relation_type has invalid value: {doc['relation_type']}", False)
            
            # Check consistency
            if doc['is_main_document'] and doc['relation_type'] == 'main':
                self.log("Main document fields are consistent")
            elif not doc['is_main_document'] and doc['relation_type'] in ['secondary_document', 'attachment']:
                self.log("Secondary document fields are consistent")
            else:
                self.log(f"Field inconsistency: is_main={doc['is_main_document']}, relation_type={doc['relation_type']}", False)
            
            # Display sample
            print(f"\nSample Document:")
            print(f"  ID: {doc['id']}")
            print(f"  Title: {doc['title']}")
            print(f"  is_main_document: {doc['is_main_document']}")
            print(f"  document_role: {doc['document_role']}")
            print(f"  relation_type: {doc['relation_type']}")
            print(f"  parent_document_id: {doc.get('parent_document_id')}")
            
        except Exception as e:
            self.log(f"Test failed with exception: {str(e)}", False)
    
    def test_duplicate_name_validation(self):
        """Test 2: Verify duplicate name validation"""
        print("\n" + "="*60)
        print("TEST 2: Duplicate Name Validation")
        print("="*60)
        
        try:
            # This test would require creating a document and then trying to create another with same name
            # Skipping actual creation to avoid side effects
            self.log("Test skipped - would require document creation", None)
            print("To test manually:")
            print("1. Create a document with name 'test-duplicate.pdf'")
            print("2. Try creating another document with same name in same dept/type")
            print("3. Should receive error about duplicate name")
            
        except Exception as e:
            self.log(f"Test failed with exception: {str(e)}", False)
    
    def test_move_folder_api(self):
        """Test 3: Verify move folder API handles secondary documents correctly"""
        print("\n" + "="*60)
        print("TEST 3: Move Folder API for Secondary Documents")
        print("="*60)
        
        try:
            # This test would require:
            # 1. Finding a secondary document
            # 2. Moving it to another folder
            # 3. Verifying it didn't replace the main document
            # Skipping actual move to avoid side effects
            self.log("Test skipped - would require document move operation", None)
            print("To test manually:")
            print("1. Find a secondary/sub document (is_main_document=false)")
            print("2. Move it to another folder using batch/move-folder API")
            print("3. Verify:")
            print("   - Document parent_document_id points to target folder's main doc")
            print("   - Document folder_role remains 'sub' or 'attachment'")
            print("   - Target folder's main document was NOT replaced")
            
        except Exception as e:
            self.log(f"Test failed with exception: {str(e)}", False)
    
    def test_folder_auto_deletion(self):
        """Test 4: Verify folder auto-deletion when main document deleted"""
        print("\n" + "="*60)
        print("TEST 4: Folder Auto-Deletion on Main Document Delete")
        print("="*60)
        
        try:
            # This test would require:
            # 1. Creating a folder with only a main document
            # 2. Deleting the main document
            # 3. Verifying folder was auto-deleted
            # Skipping to avoid side effects
            self.log("Test skipped - would require document deletion", None)
            print("To test manually:")
            print("1. Create a folder with only 1 main document (no secondary docs)")
            print("2. Delete the main document using /api/documents/<id>/trash")
            print("3. Verify the folder is automatically deleted")
            print("4. Check logs for: 'Auto-deleting empty folder...'")
            
        except Exception as e:
            self.log(f"Test failed with exception: {str(e)}", False)
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("DOCUMENT API FIXES - TEST SUITE")
        print("="*60)
        
        self.test_document_role_fields()
        self.test_duplicate_name_validation()
        self.test_move_folder_api()
        self.test_folder_auto_deletion()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.test_results if r['success'])
        failed = sum(1 for r in self.test_results if r['success'] is False)
        skipped = sum(1 for r in self.test_results if r['success'] is None)
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"✓ Passed: {passed}")
        print(f"✗ Failed: {failed}")
        print(f"⊘ Skipped: {skipped}")
        
        if failed > 0:
            print("\nFailed Tests:")
            for r in self.test_results:
                if r['success'] is False:
                    print(f"  - {r['message']}")
            return 1
        
        return 0


def main():
    parser = argparse.ArgumentParser(description='Test document API fixes')
    parser.add_argument('--base-url', default='http://localhost:8069',
                       help='Base URL of the API (default: http://localhost:8069)')
    parser.add_argument('--token', required=True,
                       help='JWT authentication token')
    
    args = parser.parse_args()
    
    tester = DocumentAPITester(args.base_url, args.token)
    exit_code = tester.run_all_tests()
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
