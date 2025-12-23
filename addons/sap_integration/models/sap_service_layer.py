# -*- coding: utf-8 -*-

import requests
import json
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SapServiceLayerConnection:
    """SAP Service Layer Connection Class with improved session management"""
    
    # Class-level connection pool (simple cache)
    _connection_pool = {}
    _pool_max_age = 300  # 5 minutes
    
    def __init__(self, base_url, username, password, company_db, timeout=30, verify_ssl=False):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.company_db = company_db
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.verify = verify_ssl  # Disable SSL verification if needed
        self.session_id = None
        self.session_created_at = None
        self.session_expires_at = None
        
        # Suppress SSL warnings if verification is disabled
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with SAP Service Layer with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                auth_url = f"{self.base_url}/Login"
                auth_data = {
                    "UserName": self.username,
                    "Password": self.password,
                    "CompanyDB": self.company_db
                }
                
                _logger.info(f"Authenticating with SAP Service Layer (attempt {attempt + 1}/{max_retries}): {auth_url}")
                response = self.session.post(auth_url, json=auth_data, timeout=self.timeout)
                
                if response.status_code == 200:
                    result = response.json()
                    self.session_id = result.get('SessionId')
                    self.session_created_at = datetime.now()
                    # SAP sessions typically expire after 30 minutes
                    self.session_expires_at = self.session_created_at + timedelta(minutes=28)
                    _logger.info(f"SAP Service Layer authentication successful. Session expires at {self.session_expires_at}")
                    return
                else:
                    error_msg = f"Authentication failed: {response.status_code} - {response.text}"
                    _logger.error(error_msg)
                    
                    if attempt < max_retries - 1:
                        _logger.info(f"Retrying in {retry_delay} seconds...")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        raise Exception(error_msg)
                    
            except requests.exceptions.Timeout as e:
                _logger.error(f"Connection timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise Exception(f"Connection timeout after {max_retries} attempts")
                    
            except Exception as e:
                _logger.error(f"SAP Service Layer authentication error: {str(e)}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise
    
    def _is_session_valid(self):
        """Check if current session is still valid"""
        if not self.session_id:
            return False
        
        if not self.session_expires_at:
            return True  # Assume valid if no expiry set
        
        return datetime.now() < self.session_expires_at
    
    def _ensure_session(self):
        """Ensure we have a valid session, re-authenticate if necessary"""
        if not self._is_session_valid():
            _logger.info("Session expired or invalid, re-authenticating...")
            self.close_session()
            self._authenticate()
    
    def _get_headers(self):
        """Get headers for API requests"""
        return {
            'B1S-SessionId': self.session_id,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get(self, endpoint, params=None, raise_on_error=False):
        """Generic GET method for any SAP Service Layer endpoint
        
        Args:
            endpoint: SAP endpoint to call
            params: Query parameters
            raise_on_error: If True, raise exception on error instead of returning empty data
        """
        try:
            self._ensure_session()  # Ensure session is valid
            
            # Handle both full URLs and endpoint paths
            if endpoint.startswith('http'):
                url = endpoint
            else:
                url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            headers = self._get_headers()
            
            _logger.info(f"GET request to SAP: {url}")
            _logger.info(f"GET request params: {params}")
            response = self.session.get(url, headers=headers, params=params or {}, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                _logger.info(f">>> SAP Response status: 200, Data keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                if isinstance(result, dict) and 'value' in result:
                    _logger.info(f">>> Response has 'value' with {len(result['value'])} items")
                return result
            else:
                error_msg = f"SAP API Error {response.status_code}: {response.text}"
                _logger.error(error_msg)
                if raise_on_error:
                    raise Exception(error_msg)
                return {'value': [], 'error': response.text, 'status_code': response.status_code}
                
        except Exception as e:
            _logger.error(f"Error in GET request: {str(e)}")
            if raise_on_error:
                raise
            return {'value': [], 'error': str(e)}
    
    def post(self, endpoint, data):
        """Generic POST method for any SAP Service Layer endpoint"""
        try:
            self._ensure_session()
            
            if endpoint.startswith('http'):
                url = endpoint
            else:
                url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            headers = self._get_headers()
            
            _logger.info(f"POST request to SAP: {url}")
            response = self.session.post(url, json=data, headers=headers, timeout=self.timeout)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                error_msg = f"Error in POST request: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            _logger.error(f"Error in POST request: {str(e)}")
            raise
    
    def patch(self, endpoint, data):
        """Generic PATCH method for any SAP Service Layer endpoint"""
        try:
            self._ensure_session()
            
            if endpoint.startswith('http'):
                url = endpoint
            else:
                url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            headers = self._get_headers()
            
            _logger.info(f"PATCH request to SAP: {url}")
            response = self.session.patch(url, json=data, headers=headers, timeout=self.timeout)
            
            if response.status_code in [200, 204]:
                return response.json() if response.content else {}
            else:
                error_msg = f"Error in PATCH request: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            _logger.error(f"Error in PATCH request: {str(e)}")
            raise
    
    def get_customers(self, skip=0, top=100, filter_query=None):
        """Get customers from SAP Service Layer"""
        try:
            self._ensure_session()  # Ensure session is valid
            
            url = f"{self.base_url}/BusinessPartners"
            headers = self._get_headers()
            params = {
                '$skip': skip,
                '$top': top,
                '$orderby': 'CardCode'
            }
            
            if filter_query:
                params['$filter'] = filter_query
            
            _logger.info(f"Getting customers from SAP: {url}")
            response = self.session.get(url, headers=headers, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                _logger.error(f"Error getting customers: {response.status_code} - {response.text}")
                return {'value': []}
                
        except Exception as e:
            _logger.error(f"Error getting customers: {str(e)}")
            return {'value': []}
    
    def get_products(self, skip=0, top=100, filter_query=None):
        """Get products from SAP Service Layer"""
        try:
            url = f"{self.base_url}/Items"
            headers = self._get_headers()
            params = {
                '$skip': skip,
                '$top': top,
                '$orderby': 'ItemCode'
            }
            
            if filter_query:
                params['$filter'] = filter_query
            
            _logger.info(f"Getting products from SAP: {url}")
            response = self.session.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                _logger.error(f"Error getting products: {response.status_code} - {response.text}")
                return {'value': []}
                
        except Exception as e:
            _logger.error(f"Error getting products: {str(e)}")
            return {'value': []}
    
    def get_quotations(self, skip=0, top=100, filter_query=None):
        """Get quotations from SAP Service Layer"""
        try:
            url = f"{self.base_url}/Quotations"
            headers = self._get_headers()
            params = {
                '$skip': skip,
                '$top': top,
                '$orderby': 'DocEntry'
            }
            
            if filter_query:
                params['$filter'] = filter_query
            
            _logger.info(f"Getting quotations from SAP: {url}")
            response = self.session.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                _logger.error(f"Error getting quotations: {response.status_code} - {response.text}")
                return {'value': []}
                
        except Exception as e:
            _logger.error(f"Error getting quotations: {str(e)}")
            return {'value': []}
    
    def get_sales_orders(self, skip=0, top=100, filter_query=None):
        """Get sales orders from SAP Service Layer"""
        try:
            url = f"{self.base_url}/Orders"
            headers = self._get_headers()
            params = {
                '$skip': skip,
                '$top': top,
                '$orderby': 'DocEntry'
            }
            
            if filter_query:
                params['$filter'] = filter_query
            
            _logger.info(f"Getting sales orders from SAP: {url}")
            response = self.session.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                _logger.error(f"Error getting sales orders: {response.status_code} - {response.text}")
                return {'value': []}
                
        except Exception as e:
            _logger.error(f"Error getting sales orders: {str(e)}")
            return {'value': []}
    
    def get_invoices(self, skip=0, top=100, filter_query=None):
        """Get invoices from SAP Service Layer"""
        try:
            url = f"{self.base_url}/Invoices"
            headers = self._get_headers()
            params = {
                '$skip': skip,
                '$top': top,
                '$orderby': 'DocEntry'
            }
            
            if filter_query:
                params['$filter'] = filter_query
            
            _logger.info(f"Getting invoices from SAP: {url}")
            response = self.session.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                _logger.error(f"Error getting invoices: {response.status_code} - {response.text}")
                return {'value': []}
                
        except Exception as e:
            _logger.error(f"Error getting invoices: {str(e)}")
            return {'value': []}
    
    def create_business_partner(self, partner_data):
        """Create business partner in SAP Service Layer"""
        try:
            url = f"{self.base_url}/BusinessPartners"
            headers = self._get_headers()
            
            _logger.info(f"Creating business partner in SAP: {url}")
            _logger.info(f"Request data being sent: {json.dumps(partner_data, indent=2, default=str)}")
            response = self.session.post(url, json=partner_data, headers=headers, timeout=30)
            
            _logger.info(f"Response status code: {response.status_code}")
            _logger.info(f"Response text: {response.text[:500]}")  # أول 500 حرف من الاستجابة
            
            if response.status_code in [200, 201]:
                result = response.json()
                _logger.info(f"Business partner created successfully: {result.get('CardCode')}")
                return result
            else:
                error_msg = f"Error creating business partner: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            _logger.error(f"Exception in create_business_partner: {str(e)}", exc_info=True)
            raise
    
    def update_business_partner(self, card_code, partner_data):
        """Update business partner in SAP Service Layer"""
        try:
            url = f"{self.base_url}/BusinessPartners('{card_code}')"
            headers = self._get_headers()
            
            _logger.info(f"Updating business partner in SAP: {url}")
            response = self.session.patch(url, json=partner_data, headers=headers, timeout=30)
            
            if response.status_code in [200, 204]:
                _logger.info(f"Business partner updated: {card_code}")
                return response.json() if response.content else {'CardCode': card_code}
            else:
                error_msg = f"Error updating business partner: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            _logger.error(f"Error updating business partner: {str(e)}")
            raise
    
    def create_item(self, item_data):
        """Create item (product) in SAP Service Layer"""
        try:
            url = f"{self.base_url}/Items"
            headers = self._get_headers()
            
            _logger.info(f"Creating item in SAP: {url}")
            response = self.session.post(url, json=item_data, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                _logger.info(f"Item created: {result.get('ItemCode')}")
                return result
            else:
                error_msg = f"Error creating item: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            _logger.error(f"Error creating item: {str(e)}")
            raise
    
    def update_item(self, item_code, item_data):
        """Update item (product) in SAP Service Layer"""
        try:
            url = f"{self.base_url}/Items('{item_code}')"
            headers = self._get_headers()
            
            _logger.info(f"Updating item in SAP: {url}")
            response = self.session.patch(url, json=item_data, headers=headers, timeout=30)
            
            if response.status_code in [200, 204]:
                _logger.info(f"Item updated: {item_code}")
                return response.json() if response.content else {'ItemCode': item_code}
            else:
                error_msg = f"Error updating item: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            _logger.error(f"Error updating item: {str(e)}")
            raise
    
    def create_quotation(self, quotation_data):
        """Create quotation in SAP Service Layer"""
        try:
            url = f"{self.base_url}/Quotations"
            headers = self._get_headers()
            
            # Log DocumentLines details before sending
            document_lines = quotation_data.get('DocumentLines', [])
            _logger.info(f"Creating quotation in SAP: {url}, DocumentLines count: {len(document_lines)}")
            for idx, line in enumerate(document_lines):
                _logger.info(f"Sending DocumentLine[{idx}]: ItemCode={line.get('ItemCode')}, UoMEntry={line.get('UoMEntry', 'NOT SET')}, Quantity={line.get('Quantity')}, UnitPrice={line.get('UnitPrice')}")
            
            # Log invoice type if present
            if 'U_InvType' in quotation_data:
                _logger.info(f"[SAP Send] U_InvType is present: {quotation_data['U_InvType']}")
            else:
                _logger.info(f"[SAP Send] U_InvType is NOT present in quotation data")
            
            # Log Comments if present
            if 'Comments' in quotation_data:
                comments_preview = quotation_data['Comments'][:200] if len(quotation_data['Comments']) > 200 else quotation_data['Comments']
                _logger.info(f"[SAP Send] Comments preview: {comments_preview}")
            
            # Log full quotation data (especially U_InvType if present)
            import json
            try:
                full_data_json = json.dumps(quotation_data, indent=2, ensure_ascii=False)
                _logger.info(f"[SAP Send] Full quotation data being sent to SAP:\n{full_data_json}")
            except Exception as json_error:
                _logger.warning(f"[SAP Send] Could not serialize quotation data to JSON: {str(json_error)}")
                _logger.info(f"[SAP Send] Quotation data keys: {list(quotation_data.keys())}")
            
            _logger.info(f"[SAP Send] Sending POST request to SAP: {url} (timeout=30s)")
            try:
                response = self.session.post(url, json=quotation_data, headers=headers, timeout=30)
                _logger.info(f"[SAP Send] Received response from SAP: status_code={response.status_code}")
            except Exception as request_error:
                _logger.error(f"[SAP Send] ❌ Request failed (timeout/connection error): {str(request_error)}", exc_info=True)
                raise
            
            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    _logger.info(f"[SAP Send] Response JSON keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                    doc_entry = result.get('DocEntry')
                    doc_num = result.get('DocNum', 'N/A')
                    if doc_entry:
                        # Log success with invoice type info if present
                        inv_type_info = ""
                        if 'U_InvType' in quotation_data:
                            inv_type_info = f", U_InvType={quotation_data['U_InvType']}"
                        _logger.info(f"[SAP Send] ✅ Quotation created successfully: DocEntry={doc_entry}, DocNum={doc_num}{inv_type_info}")
                        return result
                    else:
                        error_msg = f"Quotation creation returned 200/201 but no DocEntry in response: {response.text[:500]}"
                        _logger.error(f"[SAP Send] ❌ {error_msg}")
                        _logger.error(f"[SAP Send] Full response: {response.text}")
                        raise Exception(error_msg)
                except json.JSONDecodeError as json_err:
                    error_msg = f"Failed to parse SAP response as JSON: {str(json_err)}, Response text: {response.text[:500]}"
                    _logger.error(f"[SAP Send] ❌ {error_msg}")
                    raise Exception(error_msg)
            else:
                error_msg = f"Error creating quotation: {response.status_code} - {response.text[:500]}"
                _logger.error(f"[SAP Send] ❌ {error_msg}")
                _logger.error(f"[SAP Send] Full error response: {response.text}")
                raise Exception(error_msg)
                
        except Exception as e:
            _logger.error(f"Error creating quotation: {str(e)}")
            raise
    
    def create_order(self, order_data):
        """Create sales order (draft) in SAP Service Layer"""
        try:
            url = f"{self.base_url}/Orders"
            headers = self._get_headers()
            
            # Log DocumentLines details before sending
            document_lines = order_data.get('DocumentLines', [])
            _logger.info(f"Creating sales order in SAP: {url}, DocumentLines count: {len(document_lines)}")
            for idx, line in enumerate(document_lines):
                _logger.info(f"Sending DocumentLine[{idx}]: ItemCode={line.get('ItemCode')}, UoMEntry={line.get('UoMEntry', 'NOT SET')}, Quantity={line.get('Quantity')}, UnitPrice={line.get('UnitPrice')}")
            
            response = self.session.post(url, json=order_data, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                _logger.info(f"Sales order created: DocEntry {result.get('DocEntry')}")
                return result
            else:
                error_msg = f"Error creating sales order: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            _logger.error(f"Error creating sales order: {str(e)}")
            raise
    
    def update_quotation(self, doc_entry, quotation_data):
        """Update quotation in SAP Service Layer"""
        try:
            url = f"{self.base_url}/Quotations({doc_entry})"
            headers = self._get_headers()
            
            _logger.info(f"[SAP Update] Updating quotation {doc_entry} in SAP: {url}")
            
            # Log DocumentLines to verify ItemDescription is included
            doc_lines = quotation_data.get('DocumentLines', [])
            _logger.info(f"[SAP Update] Sending {len(doc_lines)} DocumentLines")
            for idx, line in enumerate(doc_lines):
                item_desc = line.get('ItemDescription', 'NOT_SET')
                _logger.info(f"[SAP Update] DocumentLine[{idx}]: ItemCode={line.get('ItemCode')}, Quantity={line.get('Quantity')}, ItemDescription='{item_desc}'")
            
            # Log full payload
            import json
            _logger.info(f"[SAP Update] Full quotation data being sent:\n{json.dumps(quotation_data, indent=2, ensure_ascii=False)}")
            
            response = self.session.patch(url, json=quotation_data, headers=headers, timeout=30)
            
            if response.status_code in [200, 204]:
                _logger.info(f"[SAP Update] ✅ Successfully updated quotation {doc_entry}")
                return response.json() if response.content else {}
            else:
                _logger.error(f"[SAP Update] ❌ Error updating quotation {doc_entry}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            _logger.error(f"[SAP Update] ❌ Exception updating quotation {doc_entry}: {str(e)}", exc_info=True)
            return None
    
    def convert_quotation_to_order(self, doc_entry):
        """Convert quotation to sales order in SAP Service Layer
        
        Args:
            doc_entry: The DocEntry of the quotation to convert
            
        Returns:
            dict: The created sales order data with DocNum and DocEntry, or None if failed
        """
        try:
            self._ensure_session()
            
            # Try method 1: Use CopyTo bound action (if available in your SAP system)
            url = f"{self.base_url}/Quotations({doc_entry})/CopyTo"
            headers = self._get_headers()
            data = {
                "DocumentType": "Orders"
            }
            
            _logger.info(f"Converting quotation {doc_entry} to sales order in SAP (method 1 - CopyTo): {url}")
            response = self.session.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json() if response.content else {}
                _logger.info(f"Successfully converted quotation {doc_entry} to sales order using CopyTo. Result: {result}")
                return result
            elif response.status_code == 404:
                # CopyTo action not available, try method 2: Get quotation and create order manually
                _logger.info(f"CopyTo action not available (404), trying method 2: Get quotation and create order manually")
                return self._convert_quotation_to_order_manual(doc_entry)
            else:
                error_msg = f"Error converting quotation to sales order (method 1): {response.status_code} - {response.text}"
                _logger.warning(error_msg)
                # Try method 2 as fallback
                _logger.info(f"Trying method 2: Get quotation and create order manually")
                return self._convert_quotation_to_order_manual(doc_entry)
                
        except Exception as e:
            _logger.error(f"Error converting quotation to sales order: {str(e)}", exc_info=True)
            # Try method 2 as fallback
            try:
                _logger.info(f"Trying method 2: Get quotation and create order manually")
                return self._convert_quotation_to_order_manual(doc_entry)
            except Exception as e2:
                _logger.error(f"Error in fallback method: {str(e2)}", exc_info=True)
                return None
    
    def _convert_quotation_to_order_manual(self, doc_entry):
        """Convert quotation to sales order by retrieving quotation data and creating a new order manually
        
        Args:
            doc_entry: The DocEntry of the quotation to convert
            
        Returns:
            dict: The created sales order data with DocNum and DocEntry, or None if failed
        """
        try:
            self._ensure_session()
            
            # Step 1: Get the quotation data
            url = f"{self.base_url}/Quotations({doc_entry})"
            headers = self._get_headers()
            
            _logger.info(f"Retrieving quotation {doc_entry} from SAP: {url}")
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                error_msg = f"Error retrieving quotation {doc_entry}: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                return None
            
            quotation_data = response.json()
            _logger.info(f"Retrieved quotation data: DocNum={quotation_data.get('DocNum')}, CardCode={quotation_data.get('CardCode')}")
            
            # Log DocumentLines to verify ItemDescription is preserved
            doc_lines = quotation_data.get('DocumentLines', [])
            _logger.info(f"[SAP Convert] Retrieved {len(doc_lines)} DocumentLines from quotation")
            for idx, line in enumerate(doc_lines):
                if 'ItemDescription' in line:
                    _logger.info(f"[SAP Convert] ✅ DocumentLine[{idx}] has ItemDescription: '{line.get('ItemDescription')}'")
                else:
                    _logger.info(f"[SAP Convert] ⚠️ DocumentLine[{idx}] has NO ItemDescription (ItemCode: {line.get('ItemCode')})")
            
            # Step 2: Prepare sales order data from quotation
            order_data = {
                'CardCode': quotation_data.get('CardCode'),
                'DocDate': quotation_data.get('DocDate'),
                'DocDueDate': quotation_data.get('DocDueDate') or quotation_data.get('DocDate'),
                'DocumentLines': doc_lines,
            }
            
            # Copy other relevant fields if they exist
            # إضافة U_InvType (Invoice Type) للحفاظ عليه عند التحويل
            for field in ['Comments', 'NumAtCard', 'Address', 'Address2', 'ShipToCode', 'PayToCode', 'U_InvType']:
                if field in quotation_data:
                    order_data[field] = quotation_data[field]
                    if field == 'U_InvType':
                        _logger.info(f"[SAP Convert] Preserving U_InvType={quotation_data[field]} when converting quotation to order")
                    elif field == 'Comments':
                        _logger.info(f"[SAP Convert] Preserving Comments when converting quotation to order")
            
            # Log final order data DocumentLines
            _logger.info(f"[SAP Convert] Final order_data has {len(order_data.get('DocumentLines', []))} DocumentLines")
            for idx, line in enumerate(order_data.get('DocumentLines', [])):
                if 'ItemDescription' in line:
                    _logger.info(f"[SAP Convert] ✅ Final order DocumentLine[{idx}] has ItemDescription: '{line.get('ItemDescription')}'")
                else:
                    _logger.info(f"[SAP Convert] ⚠️ Final order DocumentLine[{idx}] has NO ItemDescription")
            
            # Step 3: Create the sales order
            url = f"{self.base_url}/Orders"
            _logger.info(f"Creating sales order from quotation {doc_entry} in SAP: {url}")
            _logger.info(f"Order data: CardCode={order_data.get('CardCode')}, DocumentLines={len(order_data.get('DocumentLines', []))} lines")
            
            response = self.session.post(url, json=order_data, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json() if response.content else {}
                _logger.info(f"Successfully created sales order from quotation {doc_entry}. Result: {result}")
                return result
            else:
                error_msg = f"Error creating sales order from quotation {doc_entry}: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                return None
                
        except Exception as e:
            _logger.error(f"Error in manual conversion method: {str(e)}", exc_info=True)
            return None
    
    def close_session(self):
        """Close SAP Service Layer session"""
        try:
            if self.session_id:
                logout_url = f"{self.base_url}/Logout"
                headers = {'B1S-SessionId': self.session_id}
                self.session.post(logout_url, headers=headers, timeout=10)
                _logger.info("SAP Service Layer session closed")
        except Exception as e:
            _logger.error(f"Error closing session: {str(e)}")
    
    def get_numbering_series(self, series_code=None, document_type='BusinessPartners'):
        """Get numbering series information from SAP"""
        try:
            # في SAP Business One Service Layer، يمكن قراءة Numbering Series من DocumentNumberingService
            # أو من خلال DocumentSeriesService
            url = f"{self.base_url}/DocumentSeriesService_GetDocumentSeries"
            headers = self._get_headers()
            
            # محاولة قراءة Numbering Series للـ Business Partners
            # قد نحتاج إلى استخدام endpoint مختلف حسب إصدار SAP
            # بديل: قراءة آخر Business Partner للحصول على آخر CardCode
            if document_type == 'BusinessPartners':
                # قراءة آخر Business Partner للحصول على آخر CardCode
                url = f"{self.base_url}/BusinessPartners"
                params = {
                    '$orderby': 'CardCode desc',
                    '$top': 1,
                    '$select': 'CardCode'
                }
                response = self.session.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'value' in data and len(data['value']) > 0:
                        last_card_code = data['value'][0].get('CardCode', '')
                        _logger.info(f"Last CardCode from SAP: {last_card_code}")
                        return {'last_card_code': last_card_code}
            
            # إذا فشل، نعود إلى قراءة Numbering Series مباشرة
            # هذا يتطلب معرفة DocumentTypeCode للـ Business Partners
            _logger.warning(f"Could not get numbering series from SAP, trying alternative method")
            return None
            
        except Exception as e:
            _logger.error(f"Error getting numbering series: {str(e)}")
            return None
    
    def get_ibg_series_number(self):
        """Get Series number for IBG from SAP (similar to PHP getIBGSeriesNumber)"""
        try:
            # محاولة 1: البحث في Business Partners الموجودين
            url = f"{self.base_url}/BusinessPartners"
            headers = self._get_headers()
            params = {
                '$filter': "startswith(CardCode, 'IBG')",
                '$select': 'CardCode,Series',
                '$top': 1,
                '$orderby': 'CreateDate desc'
            }
            
            response = self.session.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'value' in data and len(data['value']) > 0:
                    series_number = data['value'][0].get('Series')
                    if series_number is not None:
                        _logger.info(f'Found Series number from existing BP: {series_number}')
                        return int(series_number)
            
            # محاولة 2: استخدام SeriesService
            try:
                series_url = f"{self.base_url}/SeriesService_GetDocumentSeries"
                series_data = {
                    'DocumentTypeParams': {
                        'Document': '2'  # 2 = Business Partners
                    }
                }
                series_response = self.session.post(series_url, json=series_data, headers=headers, timeout=30)
                
                if series_response.status_code == 200:
                    series_result = series_response.json()
                    if 'value' in series_result:
                        for series in series_result['value']:
                            # البحث عن السلسلة الافتراضية أو التي تبدأ بـ IBG
                            if series.get('IsDefault') == 'tYES':
                                return int(series.get('Series', 1))
                            if 'IBG' in (series.get('Name') or ''):
                                return int(series.get('Series', 1))
            except Exception as e:
                _logger.warning(f'SeriesService query failed: {e}')
            
            # القيمة الافتراضية
            _logger.info('Using default Series number: 1')
            return 1
            
        except Exception as e:
            _logger.error(f'Failed to get IBG series number: {e}')
            return 1  # قيمة افتراضية
    
    def get_next_card_code(self, series_code='IBG'):
        """Get next CardCode from SAP Numbering Series"""
        try:
            # محاولة قراءة آخر CardCode من SAP
            url = f"{self.base_url}/BusinessPartners"
            headers = self._get_headers()
            
            # فلترة Business Partners التي تبدأ بـ series_code
            params = {
                '$filter': f"startswith(CardCode, '{series_code}')",
                '$orderby': 'CardCode desc',
                '$top': 1,
                '$select': 'CardCode'
            }
            
            response = self.session.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'value' in data and len(data['value']) > 0:
                    last_card_code = data['value'][0].get('CardCode', '')
                    _logger.info(f"Last CardCode from SAP with prefix {series_code}: {last_card_code}")
                    
                    # استخراج الرقم من CardCode
                    import re
                    match = re.search(rf'{series_code}(\d+)', last_card_code)
                    if match:
                        last_number = int(match.group(1))
                        next_number = last_number + 1
                        # استخدام padding لضمان أن CardCode يطابق تنسيق Numbering Series في SAP
                        # SAP يتوقع تنسيق مع padding (IBG05079) وليس بدون padding (IBG5079)
                        # نستخدم 5 أرقام padding كما هو موضح في الصورة (Next No. = 5079)
                        next_card_code = f"{series_code}{str(next_number).zfill(5)}"
                        _logger.info(f"Next CardCode will be: {next_card_code} (with padding, last={last_number}, next={next_number})")
                        return next_card_code
                    else:
                        # إذا لم نجد رقم، نبدأ من 1
                        _logger.info(f"Could not extract number from CardCode, starting from 1")
                        return f"{series_code}00001"
                else:
                    # لا توجد Business Partners بهذا prefix، نبدأ من 1
                    _logger.info(f"No Business Partners found with prefix {series_code}, starting from 1")
                    return f"{series_code}00001"
            else:
                _logger.warning(f"Could not get last CardCode from SAP: {response.status_code}")
                return None
                
        except Exception as e:
            _logger.error(f"Error getting next CardCode: {str(e)}")
            return None
    
    def test_connection(self):
        """Test connection to SAP Service Layer"""
        try:
            # Try to get a simple query to test connection
            url = f"{self.base_url}/BusinessPartners"
            headers = self._get_headers()
            params = {'$top': 1}
            
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def get_user_defined_fields(self, table_name):
        """Get User-Defined Fields (UDFs) for a specific table
        
        Args:
            table_name: The SAP table name (e.g., 'OINV' for Invoices, 'ORDR' for Orders)
            
        Returns:
            list: List of UDF definitions with Name, Type, ValidValues, etc.
        """
        try:
            self._ensure_session()
            
            url = f"{self.base_url}/UserFieldsMD"
            headers = self._get_headers()
            params = {
                '$filter': f"TableName eq '{table_name}'",
                '$select': 'Name,Description,Type,Size,ValidValuesMD,DefaultValue'
            }
            
            _logger.info(f"Fetching User-Defined Fields for table {table_name}")
            response = self.session.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                udfs = result.get('value', [])
                _logger.info(f"Found {len(udfs)} User-Defined Fields for table {table_name}")
                return udfs
            else:
                error_msg = f"Error fetching UDFs: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                return []
                
        except Exception as e:
            _logger.error(f"Error getting User-Defined Fields: {str(e)}", exc_info=True)
            return []
    
    def get_udf_valid_values(self, field_name, table_name='OINV'):
        """Get valid values for a User-Defined Field
        
        Args:
            field_name: The UDF name (e.g., 'InvoiceType')
            table_name: The SAP table name (default: 'OINV' for Invoices)
            
        Returns:
            list: List of valid values [(value, description), ...]
        """
        try:
            self._ensure_session()
            
            # First, get the UDF definition
            url = f"{self.base_url}/UserFieldsMD"
            headers = self._get_headers()
            params = {
                '$filter': f"TableName eq '{table_name}' and Name eq '{field_name}'"
            }
            
            _logger.info(f"Fetching valid values for UDF {field_name} in table {table_name}")
            response = self.session.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                udfs = result.get('value', [])
                
                if udfs:
                    udf = udfs[0]
                    valid_values = udf.get('ValidValuesMD', [])
                    
                    # Convert to list of tuples (value, description)
                    values_list = [(v.get('Value', ''), v.get('Description', '')) for v in valid_values]
                    _logger.info(f"Found {len(values_list)} valid values for {field_name}: {values_list}")
                    return values_list
                else:
                    _logger.warning(f"UDF {field_name} not found in table {table_name}")
                    return []
            else:
                error_msg = f"Error fetching UDF valid values: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                return []
                
        except Exception as e:
            _logger.error(f"Error getting UDF valid values: {str(e)}", exc_info=True)
            return []
    
    def get_invoice_types(self):
        """Get available invoice types from SAP (U_InvoiceType valid values)
        
        Returns:
            list: List of invoice types [(value, description), ...]
        """
        return self.get_udf_valid_values('InvoiceType', 'OINV')
    
    def print_document(self, doc_entry, doc_type='Orders', print_format='DEFAULT LAYOUT', 
                       return_pdf=True, api_gateway_url=None):
        """إرسال طلب طباعة إلى SAP واسترجاع PDF
        
        Args:
            doc_entry (int): رقم DocEntry للمستند في SAP
            doc_type (str): نوع المستند ('Orders', 'Quotations', 'Invoices')
            print_format (str): اسم Layout الطباعة في SAP (default: 'DEFAULT LAYOUT')
            return_pdf (bool): إرجاع PDF؟ (default: True)
            api_gateway_url (str): عنوان API Gateway (اختياري، يستخدم Crystal Reports Service)
            
        Returns:
            dict: {'success': bool, 'pdf_base64': str (إذا return_pdf=True), 'message': str}
        """
        try:
            self._ensure_session()
            
            _logger.info(f"[SAP Print] Starting print request for {doc_type} DocEntry={doc_entry}, Layout={print_format}")
            
            # الطريقة 1: استخدام Service Layer Print Service (إذا كان متوفراً)
            if api_gateway_url:
                try:
                    return self._print_via_api_gateway(
                        doc_entry, doc_type, print_format, return_pdf, api_gateway_url
                    )
                except Exception as e:
                    _logger.warning(f"[SAP Print] API Gateway print failed: {e}, falling back to Crystal Reports")
            
            # الطريقة 2: استخدام Crystal Reports Web Service (الطريقة القياسية)
            return self._print_via_crystal_reports(doc_entry, doc_type, print_format, return_pdf)
            
        except Exception as e:
            error_msg = f"Error sending print request to SAP: {str(e)}"
            _logger.error(f"[SAP Print] {error_msg}", exc_info=True)
            return {
                'success': False,
                'message': error_msg,
                'pdf_base64': None
            }
    
    def _print_via_crystal_reports(self, doc_entry, doc_type, print_format, return_pdf):
        """طباعة عبر Crystal Reports Service"""
        try:
            # استخدام Print Queue في SAP Service Layer
            url = f"{self.base_url}/Print"
            headers = self._get_headers()
            
            # إعداد بيانات الطباعة
            print_data = {
                "TemplateCode": print_format,
                "ObjectId": doc_entry,
                "ObjectType": self._get_object_type_code(doc_type)
            }
            
            _logger.info(f"[SAP Print] Sending print request to SAP: {print_data}")
            response = self.session.post(url, json=print_data, headers=headers, timeout=60)
            
            if response.status_code in [200, 201, 204]:
                _logger.info(f"[SAP Print] ✅ Print request sent successfully to SAP")
                
                # إذا طلب المستخدم PDF، نحتاج لاسترجاعه
                if return_pdf:
                    # محاولة الحصول على PDF من الطابور
                    pdf_data = self._retrieve_printed_pdf(doc_entry, doc_type)
                    return {
                        'success': True,
                        'message': 'Print request sent to SAP successfully',
                        'pdf_base64': pdf_data
                    }
                else:
                    return {
                        'success': True,
                        'message': 'Print request sent to SAP successfully',
                        'pdf_base64': None
                    }
            else:
                error_msg = f"Print request failed: {response.status_code} - {response.text}"
                _logger.error(f"[SAP Print] {error_msg}")
                return {
                    'success': False,
                    'message': error_msg,
                    'pdf_base64': None
                }
                
        except Exception as e:
            error_msg = f"Error in Crystal Reports print: {str(e)}"
            _logger.error(f"[SAP Print] {error_msg}", exc_info=True)
            return {
                'success': False,
                'message': error_msg,
                'pdf_base64': None
            }
    
    def _print_via_api_gateway(self, doc_entry, doc_type, print_format, return_pdf, api_gateway_url):
        """طباعة عبر API Gateway (طريقة بديلة)"""
        try:
            # استخدام API Gateway لإرسال طلب طباعة مباشر
            url = f"{api_gateway_url}/print/{doc_type}/{doc_entry}"
            
            params = {
                'layout': print_format,
                'format': 'pdf' if return_pdf else 'print'
            }
            
            _logger.info(f"[SAP Print] Sending print request to API Gateway: {url}")
            response = requests.get(url, params=params, timeout=60, verify=self.verify_ssl)
            
            if response.status_code == 200:
                _logger.info(f"[SAP Print] ✅ Print request via API Gateway successful")
                
                if return_pdf:
                    import base64
                    pdf_base64 = base64.b64encode(response.content).decode('utf-8')
                    return {
                        'success': True,
                        'message': 'Print request successful via API Gateway',
                        'pdf_base64': pdf_base64
                    }
                else:
                    return {
                        'success': True,
                        'message': 'Print request sent via API Gateway',
                        'pdf_base64': None
                    }
            else:
                error_msg = f"API Gateway print failed: {response.status_code} - {response.text}"
                _logger.error(f"[SAP Print] {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            error_msg = f"Error in API Gateway print: {str(e)}"
            _logger.error(f"[SAP Print] {error_msg}", exc_info=True)
            raise
    
    def _retrieve_printed_pdf(self, doc_entry, doc_type):
        """محاولة استرجاع PDF من SAP بعد الطباعة"""
        try:
            # هذه الطريقة تعتمد على كيفية تكوين SAP
            # في معظم الحالات، يجب استخدام Report Service أو Crystal Reports
            
            # الطريقة 1: استخدام Query لإ getستعلام عن المستند كـ PDF
            url = f"{self.base_url}/{doc_type}({doc_entry})/GetPDF"
            headers = self._get_headers()
            
            _logger.info(f"[SAP Print] Attempting to retrieve PDF from SAP: {url}")
            response = self.session.get(url, headers=headers, timeout=60)
            
            if response.status_code == 200 and response.content:
                import base64
                pdf_base64 = base64.b64encode(response.content).decode('utf-8')
                _logger.info(f"[SAP Print] ✅ PDF retrieved successfully, size: {len(pdf_base64)} bytes")
                return pdf_base64
            else:
                _logger.warning(f"[SAP Print] Could not retrieve PDF: {response.status_code}")
                return None
                
        except Exception as e:
            _logger.warning(f"[SAP Print] Could not retrieve PDF: {str(e)}")
            return None
    
    def _get_object_type_code(self, doc_type):
        """تحويل نوع المستند إلى كود SAP Object Type"""
        object_type_map = {
            'Orders': '17',          # Sales Order
            'Quotations': '23',      # Quotation
            'Invoices': '13',        # A/R Invoice
            'PurchaseOrders': '22',  # Purchase Order
            'DeliveryNotes': '15',   # Delivery
        }
        return object_type_map.get(doc_type, '17')  # Default to Sales Order


