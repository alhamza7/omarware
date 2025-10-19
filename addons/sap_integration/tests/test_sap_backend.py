# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Backend Tests

Unit tests for SAP backend functionality.
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from unittest.mock import patch, MagicMock
import json


class TestSapBackend(TransactionCase):
    """Test SAP Backend functionality"""
    
    def setUp(self):
        super().setUp()
        self.sap_backend = self.env['sap.backend']
        self.test_backend_data = {
            'name': 'Test SAP Backend',
            'host': 'test.sap.com',
            'port': 50000,
            'company_db': 'TEST_DB',
            'username': 'test_user',
            'password': 'test_password',
            'active': True
        }
    
    def test_create_backend(self):
        """Test creating SAP backend"""
        backend = self.sap_backend.create(self.test_backend_data)
        
        self.assertEqual(backend.name, 'Test SAP Backend')
        self.assertEqual(backend.host, 'test.sap.com')
        self.assertEqual(backend.port, 50000)
        self.assertEqual(backend.company_db, 'TEST_DB')
        self.assertTrue(backend.active)
    
    def test_backend_validation(self):
        """Test backend validation"""
        # Test missing required fields
        with self.assertRaises(ValidationError):
            self.sap_backend.create({
                'name': 'Invalid Backend'
            })
        
        # Test invalid port
        with self.assertRaises(ValidationError):
            self.sap_backend.create({
                'name': 'Invalid Port Backend',
                'host': 'test.sap.com',
                'port': 99999,  # Invalid port
                'company_db': 'TEST_DB',
                'username': 'test_user',
                'password': 'test_password'
            })
    
    @patch('requests.post')
    def test_connection_success(self, mock_post):
        """Test successful connection"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'SessionId': 'test_session_id'}
        mock_post.return_value = mock_response
        
        backend = self.sap_backend.create(self.test_backend_data)
        result = backend.test_connection()
        
        self.assertTrue(result)
        self.assertEqual(backend.connection_status, 'connected')
        self.assertIsNotNone(backend.last_connection)
    
    @patch('requests.post')
    def test_connection_failure(self, mock_post):
        """Test connection failure"""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_post.return_value = mock_response
        
        backend = self.sap_backend.create(self.test_backend_data)
        result = backend.test_connection()
        
        self.assertFalse(result)
        self.assertEqual(backend.connection_status, 'error')
        self.assertIsNotNone(backend.error_message)
    
    def test_get_connection_url(self):
        """Test connection URL generation"""
        backend = self.sap_backend.create(self.test_backend_data)
        url = backend.get_connection_url()
        
        expected_url = 'https://test.sap.com:50000/b1s/v1/Login'
        self.assertEqual(url, expected_url)
    
    def test_get_connection_headers(self):
        """Test connection headers generation"""
        backend = self.sap_backend.create(self.test_backend_data)
        headers = backend.get_connection_headers()
        
        self.assertIn('Content-Type', headers)
        self.assertEqual(headers['Content-Type'], 'application/json')
    
    def test_get_connection_data(self):
        """Test connection data generation"""
        backend = self.sap_backend.create(self.test_backend_data)
        data = backend.get_connection_data()
        
        self.assertEqual(data['CompanyDB'], 'TEST_DB')
        self.assertEqual(data['UserName'], 'test_user')
        self.assertEqual(data['Password'], 'test_password')
    
    def test_backend_inactive(self):
        """Test inactive backend behavior"""
        backend = self.sap_backend.create(self.test_backend_data)
        backend.active = False
        
        # Should not be able to test connection when inactive
        with self.assertRaises(ValidationError):
            backend.test_connection()
    
    def test_backend_name_required(self):
        """Test backend name is required"""
        with self.assertRaises(ValidationError):
            self.sap_backend.create({
                'host': 'test.sap.com',
                'port': 50000,
                'company_db': 'TEST_DB',
                'username': 'test_user',
                'password': 'test_password'
            })
    
    def test_backend_host_required(self):
        """Test backend host is required"""
        with self.assertRaises(ValidationError):
            self.sap_backend.create({
                'name': 'Test Backend',
                'port': 50000,
                'company_db': 'TEST_DB',
                'username': 'test_user',
                'password': 'test_password'
            })
    
    def test_backend_port_validation(self):
        """Test backend port validation"""
        # Test valid port
        backend = self.sap_backend.create(self.test_backend_data)
        self.assertEqual(backend.port, 50000)
        
        # Test invalid port
        with self.assertRaises(ValidationError):
            self.sap_backend.create({
                'name': 'Invalid Port Backend',
                'host': 'test.sap.com',
                'port': 0,  # Invalid port
                'company_db': 'TEST_DB',
                'username': 'test_user',
                'password': 'test_password'
            })
    
    def test_backend_company_db_required(self):
        """Test backend company DB is required"""
        with self.assertRaises(ValidationError):
            self.sap_backend.create({
                'name': 'Test Backend',
                'host': 'test.sap.com',
                'port': 50000,
                'username': 'test_user',
                'password': 'test_password'
            })
    
    def test_backend_username_required(self):
        """Test backend username is required"""
        with self.assertRaises(ValidationError):
            self.sap_backend.create({
                'name': 'Test Backend',
                'host': 'test.sap.com',
                'port': 50000,
                'company_db': 'TEST_DB',
                'password': 'test_password'
            })
    
    def test_backend_password_required(self):
        """Test backend password is required"""
        with self.assertRaises(ValidationError):
            self.sap_backend.create({
                'name': 'Test Backend',
                'host': 'test.sap.com',
                'port': 50000,
                'company_db': 'TEST_DB',
                'username': 'test_user'
            })
    
    def test_backend_duplicate_name(self):
        """Test backend duplicate name validation"""
        # Create first backend
        self.sap_backend.create(self.test_backend_data)
        
        # Try to create second backend with same name
        with self.assertRaises(ValidationError):
            self.sap_backend.create(self.test_backend_data)
    
    def test_backend_ssl_enabled(self):
        """Test SSL enabled configuration"""
        backend_data = self.test_backend_data.copy()
        backend_data['ssl_enabled'] = True
        
        backend = self.sap_backend.create(backend_data)
        self.assertTrue(backend.ssl_enabled)
        
        url = backend.get_connection_url()
        self.assertTrue(url.startswith('https://'))
    
    def test_backend_ssl_disabled(self):
        """Test SSL disabled configuration"""
        backend_data = self.test_backend_data.copy()
        backend_data['ssl_enabled'] = False
        
        backend = self.sap_backend.create(backend_data)
        self.assertFalse(backend.ssl_enabled)
        
        url = backend.get_connection_url()
        self.assertTrue(url.startswith('http://'))
    
    def test_backend_timeout_configuration(self):
        """Test timeout configuration"""
        backend_data = self.test_backend_data.copy()
        backend_data['timeout'] = 60
        
        backend = self.sap_backend.create(backend_data)
        self.assertEqual(backend.timeout, 60)
    
    def test_backend_retry_configuration(self):
        """Test retry configuration"""
        backend_data = self.test_backend_data.copy()
        backend_data['retry_attempts'] = 5
        
        backend = self.sap_backend.create(backend_data)
        self.assertEqual(backend.retry_attempts, 5)
    
    def test_backend_batch_size_configuration(self):
        """Test batch size configuration"""
        backend_data = self.test_backend_data.copy()
        backend_data['batch_size'] = 200
        
        backend = self.sap_backend.create(backend_data)
        self.assertEqual(backend.batch_size, 200)
    
    def test_backend_incremental_sync_configuration(self):
        """Test incremental sync configuration"""
        backend_data = self.test_backend_data.copy()
        backend_data['incremental_sync_days'] = 14
        
        backend = self.sap_backend.create(backend_data)
        self.assertEqual(backend.incremental_sync_days, 14)
    
    def test_backend_connection_status_default(self):
        """Test default connection status"""
        backend = self.sap_backend.create(self.test_backend_data)
        self.assertEqual(backend.connection_status, 'disconnected')
    
    def test_backend_last_connection_default(self):
        """Test default last connection"""
        backend = self.sap_backend.create(self.test_backend_data)
        self.assertFalse(backend.last_connection)
    
    def test_backend_error_message_default(self):
        """Test default error message"""
        backend = self.sap_backend.create(self.test_backend_data)
        self.assertFalse(backend.error_message)
    
    def test_backend_active_default(self):
        """Test default active status"""
        backend = self.sap_backend.create(self.test_backend_data)
        self.assertTrue(backend.active)
    
    def test_backend_ssl_enabled_default(self):
        """Test default SSL enabled status"""
        backend = self.sap_backend.create(self.test_backend_data)
        self.assertTrue(backend.ssl_enabled)
    
    def test_backend_timeout_default(self):
        """Test default timeout"""
        backend = self.sap_backend.create(self.test_backend_data)
        self.assertEqual(backend.timeout, 30)
    
    def test_backend_retry_attempts_default(self):
        """Test default retry attempts"""
        backend = self.sap_backend.create(self.test_backend_data)
        self.assertEqual(backend.retry_attempts, 3)
    
    def test_backend_batch_size_default(self):
        """Test default batch size"""
        backend = self.sap_backend.create(self.test_backend_data)
        self.assertEqual(backend.batch_size, 100)
    
    def test_backend_incremental_sync_days_default(self):
        """Test default incremental sync days"""
        backend = self.sap_backend.create(self.test_backend_data)
        self.assertEqual(backend.incremental_sync_days, 7)
