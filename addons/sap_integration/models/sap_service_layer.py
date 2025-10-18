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
            response = self.session.post(url, json=partner_data, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                _logger.info(f"Business partner created: {result.get('CardCode')}")
                return result
            else:
                error_msg = f"Error creating business partner: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            _logger.error(f"Error creating business partner: {str(e)}")
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
            
            _logger.info(f"Creating quotation in SAP: {url}")
            response = self.session.post(url, json=quotation_data, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                _logger.info(f"Quotation created: DocEntry {result.get('DocEntry')}")
                return result
            else:
                error_msg = f"Error creating quotation: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            _logger.error(f"Error creating quotation: {str(e)}")
            raise
    
    def update_quotation(self, doc_entry, quotation_data):
        """Update quotation in SAP Service Layer"""
        try:
            url = f"{self.base_url}/Quotations({doc_entry})"
            headers = self._get_headers()
            
            _logger.info(f"Updating quotation in SAP: {url}")
            response = self.session.patch(url, json=quotation_data, headers=headers, timeout=30)
            
            if response.status_code in [200, 204]:
                return response.json() if response.content else {}
            else:
                _logger.error(f"Error updating quotation: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            _logger.error(f"Error updating quotation: {str(e)}")
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


