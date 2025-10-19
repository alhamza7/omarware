# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Integration Tests

End-to-end integration tests for SAP integration module.
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from unittest.mock import patch, MagicMock
import json


class TestSapIntegration(TransactionCase):
    """Test SAP Integration end-to-end functionality"""
    
    def setUp(self):
        super().setUp()
        self.sap_backend = self.env['sap.backend']
        self.sap_sync_engine = self.env['sap.sync.engine']
        self.sap_data_mapper = self.env['sap.data.mapper']
        self.sap_uom_converter = self.env['sap.uom.converter']
        self.sap_plugin_manager = self.env['sap.plugin.manager']
        self.sap_api_framework = self.env['sap.api.framework']
        self.sap_webhook_system = self.env['sap.webhook.system']
        self.sap_customization_engine = self.env['sap.customization.engine']
        
        # Create test backend
        self.test_backend = self.sap_backend.create({
            'name': 'Test SAP Backend',
            'host': 'test.sap.com',
            'port': 50000,
            'company_db': 'TEST_DB',
            'username': 'test_user',
            'password': 'test_password',
            'active': True
        })
    
    def test_full_sync_workflow(self):
        """Test complete sync workflow from SAP to Odoo"""
        # Mock SAP connection and data
        with patch.object(self.test_backend, 'get_connection') as mock_connection:
            mock_conn = MagicMock()
            mock_conn.get_entity.return_value = {
                'CardCode': 'TEST001',
                'CardName': 'Test Partner',
                'EmailAddress': 'test@example.com',
                'Phone1': '+1234567890'
            }
            mock_connection.return_value = mock_conn
            
            # Mock data mapping
            with patch.object(self.sap_data_mapper, 'map_sap_to_odoo') as mock_map:
                mock_map.return_value = {
                    'name': 'Test Partner',
                    'ref': 'TEST001',
                    'email': 'test@example.com',
                    'phone': '+1234567890',
                    'is_company': True,
                    'customer_rank': 1
                }
                
                # Execute sync
                result = self.sap_sync_engine.sync_entity(
                    backend_id=self.test_backend.id,
                    entity_type='partner',
                    external_id='TEST001',
                    direction='sap_to_odoo'
                )
                
                # Verify result
                self.assertEqual(result['status'], 'success')
                mock_conn.get_entity.assert_called_once_with('partner', 'TEST001')
                mock_conn.close_session.assert_called_once()
                mock_map.assert_called_once()
    
    def test_bidirectional_sync_workflow(self):
        """Test bidirectional sync workflow"""
        # Mock SAP connection
        with patch.object(self.test_backend, 'get_connection') as mock_connection:
            mock_conn = MagicMock()
            mock_conn.get_entity.return_value = {
                'CardCode': 'TEST001',
                'CardName': 'Test Partner'
            }
            mock_connection.return_value = mock_conn
            
            # Mock data mapping
            with patch.object(self.sap_data_mapper, 'map_sap_to_odoo') as mock_sap_to_odoo, \
                 patch.object(self.sap_data_mapper, 'map_odoo_to_sap') as mock_odoo_to_sap:
                
                mock_sap_to_odoo.return_value = {'name': 'Test Partner', 'ref': 'TEST001'}
                mock_odoo_to_sap.return_value = {'CardName': 'Test Partner', 'CardCode': 'TEST001'}
                
                # Mock Odoo record
                with patch.object(self.env, '__getitem__') as mock_env:
                    mock_model = MagicMock()
                    mock_record = MagicMock()
                    mock_record.exists.return_value = True
                    mock_model.browse.return_value = mock_record
                    mock_env.return_value = mock_model
                    
                    # Execute bidirectional sync
                    result = self.sap_sync_engine.sync_entity(
                        backend_id=self.test_backend.id,
                        entity_type='partner',
                        external_id='TEST001',
                        record_id=1,
                        direction='bidirectional'
                    )
                    
                    # Verify result
                    self.assertEqual(result['status'], 'success')
                    mock_sap_to_odoo.assert_called_once()
                    mock_odoo_to_sap.assert_called_once()
    
    def test_uom_conversion_workflow(self):
        """Test UoM conversion workflow"""
        # Create UoM mapping
        uom_mapping = self.env['sap.uom.mapping'].create({
            'sap_uom_code': 'PC',
            'odoo_uom_id': self.env.ref('uom.product_uom_unit').id,
            'conversion_factor': 1.0
        })
        
        # Test conversion
        result = self.sap_uom_converter.convert_quantity(
            quantity=10,
            from_uom_code='PC',
            to_uom_code='PC',
            product_id=None
        )
        
        self.assertEqual(result, 10.0)
    
    def test_plugin_workflow(self):
        """Test plugin workflow"""
        # Create test plugin
        class TestPlugin:
            PLUGIN_ID = 'test_plugin'
            PLUGIN_NAME = 'Test Plugin'
            PLUGIN_VERSION = '1.0.0'
            PLUGIN_DESCRIPTION = 'Test plugin for integration testing'
            PLUGIN_AUTHOR = 'Test Author'
            PLUGIN_CATEGORY = 'test'
            PLUGIN_DEPENDENCIES = []
            PLUGIN_CONFIG_SCHEMA = {}
            
            def __init__(self, env):
                self.env = env
            
            def initialize(self):
                pass
            
            def execute(self, context=None):
                return {'status': 'success', 'message': 'Plugin executed'}
            
            def cleanup(self):
                pass
        
        # Register plugin
        result = self.sap_plugin_manager.register_plugin(
            plugin_class=TestPlugin,
            plugin_info={
                'id': 'test_plugin',
                'name': 'Test Plugin',
                'version': '1.0.0',
                'description': 'Test plugin for integration testing',
                'author': 'Test Author',
                'category': 'test',
                'dependencies': [],
                'config_schema': {}
            }
        )
        
        self.assertEqual(result['status'], 'success')
        
        # Execute plugin
        result = self.sap_plugin_manager.execute_plugin(
            plugin_id='test_plugin',
            context={'test': True}
        )
        
        self.assertEqual(result['status'], 'success')
    
    def test_api_workflow(self):
        """Test API workflow"""
        # Create API endpoint
        endpoint = self.sap_api_framework.create_endpoint(
            name='Test Sync Endpoint',
            path='/api/v1/sync',
            method='POST',
            handler_function='sync_data',
            requires_authentication=True,
            rate_limit_requests=100,
            rate_limit_window=60
        )
        
        self.assertEqual(endpoint.name, 'Test Sync Endpoint')
        self.assertEqual(endpoint.path, '/api/v1/sync')
        self.assertEqual(endpoint.method, 'POST')
        
        # Create API key
        api_key = self.sap_api_framework.create_api_key(
            name='Test API Key',
            user_id=self.env.user.id,
            endpoint_ids=[endpoint.id]
        )
        
        self.assertEqual(api_key.name, 'Test API Key')
        self.assertIn(endpoint.id, api_key.endpoint_ids.ids)
    
    def test_webhook_workflow(self):
        """Test webhook workflow"""
        # Create webhook endpoint
        webhook = self.sap_webhook_system.create_webhook(
            name='Test Webhook',
            url='https://test.example.com/webhook',
            event_types=['sync_start', 'sync_complete'],
            secret_key='test_secret_key',
            requires_authentication=True
        )
        
        self.assertEqual(webhook.name, 'Test Webhook')
        self.assertEqual(webhook.url, 'https://test.example.com/webhook')
        self.assertIn('sync_start', webhook.event_types)
        self.assertIn('sync_complete', webhook.event_types)
        
        # Test webhook sending
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = 'OK'
            mock_post.return_value = mock_response
            
            result = self.sap_webhook_system.send_webhook(
                webhook_id=webhook.id,
                event_type='sync_complete',
                data={'sync_id': 123, 'status': 'success'}
            )
            
            self.assertTrue(result['success'])
            mock_post.assert_called_once()
    
    def test_customization_workflow(self):
        """Test customization workflow"""
        # Create customization rule
        rule = self.sap_customization_engine.create_rule(
            name='Test Validation Rule',
            rule_type='validation',
            rule_code='''
# Test validation rule
if input_data.get("amount", 0) > 1000:
    result = {
        "success": True,
        "valid": True,
        "message": "Amount is valid"
    }
else:
    result = {
        "success": True,
        "valid": False,
        "message": "Amount must be greater than 1000"
    }
''',
            trigger_model='sap.sync.log',
            trigger_condition='input_data.get("status") == "failed"'
        )
        
        self.assertEqual(rule.name, 'Test Validation Rule')
        self.assertEqual(rule.rule_type, 'validation')
        
        # Execute rule
        result = self.sap_customization_engine.execute_rule(
            rule_id=rule.id,
            input_data={'amount': 1500}
        )
        
        self.assertTrue(result['success'])
        self.assertTrue(result['valid'])
    
    def test_error_handling_workflow(self):
        """Test error handling workflow"""
        # Test with invalid backend
        with self.assertRaises(ValidationError):
            self.sap_sync_engine.sync_entity(
                backend_id=99999,
                entity_type='partner',
                external_id='TEST001',
                direction='sap_to_odoo'
            )
        
        # Test with connection error
        with patch.object(self.test_backend, 'get_connection') as mock_connection:
            mock_connection.side_effect = Exception("Connection failed")
            
            result = self.sap_sync_engine.sync_entity(
                backend_id=self.test_backend.id,
                entity_type='partner',
                external_id='TEST001',
                direction='sap_to_odoo'
            )
            
            self.assertEqual(result['status'], 'failed')
            self.assertIn('Connection failed', result['message'])
    
    def test_logging_workflow(self):
        """Test logging workflow"""
        # Execute sync with logging
        with patch.object(self.test_backend, 'get_connection') as mock_connection:
            mock_conn = MagicMock()
            mock_conn.get_entity.return_value = {'CardCode': 'TEST001', 'CardName': 'Test Partner'}
            mock_connection.return_value = mock_conn
            
            with patch.object(self.sap_data_mapper, 'map_sap_to_odoo') as mock_map:
                mock_map.return_value = {'name': 'Test Partner', 'ref': 'TEST001'}
                
                # Check that logs are created
                initial_log_count = self.env['sap.sync.log'].search_count([])
                
                self.sap_sync_engine.sync_entity(
                    backend_id=self.test_backend.id,
                    entity_type='partner',
                    external_id='TEST001',
                    direction='sap_to_odoo'
                )
                
                final_log_count = self.env['sap.sync.log'].search_count([])
                self.assertGreater(final_log_count, initial_log_count)
    
    def test_performance_workflow(self):
        """Test performance workflow"""
        # Test batch processing
        with patch.object(self.test_backend, 'get_connection') as mock_connection:
            mock_conn = MagicMock()
            mock_conn.get_all_entities.return_value = {
                'value': [
                    {'CardCode': 'TEST001', 'CardName': 'Partner 1'},
                    {'CardCode': 'TEST002', 'CardName': 'Partner 2'},
                    {'CardCode': 'TEST003', 'CardName': 'Partner 3'}
                ]
            }
            mock_connection.return_value = mock_conn
            
            with patch.object(self.sap_data_mapper, 'map_sap_to_odoo') as mock_map:
                mock_map.return_value = {'name': 'Test Partner', 'ref': 'TEST001'}
                
                result = self.sap_sync_engine.sync_all_entities(
                    backend_id=self.test_backend.id,
                    entity_types=['partner'],
                    direction='sap_to_odoo'
                )
                
                self.assertIn('successful', result)
                self.assertIn('failed', result)
                self.assertEqual(result['successful'], 3)
    
    def test_security_workflow(self):
        """Test security workflow"""
        # Test API key validation
        api_key = self.sap_api_framework.create_api_key(
            name='Test API Key',
            user_id=self.env.user.id
        )
        
        # Test valid API key
        valid = self.sap_api_framework.validate_api_key(
            api_key.key_value,
            '/api/v1/sync'
        )
        self.assertTrue(valid)
        
        # Test invalid API key
        invalid = self.sap_api_framework.validate_api_key(
            'invalid_key',
            '/api/v1/sync'
        )
        self.assertFalse(invalid)
        
        # Test webhook signature validation
        webhook = self.sap_webhook_system.create_webhook(
            name='Test Webhook',
            url='https://test.example.com/webhook',
            event_types=['sync_complete'],
            secret_key='test_secret_key'
        )
        
        # Test signature generation
        signature = self.sap_webhook_system._generate_signature(
            'test_secret_key',
            {'test': 'data'}
        )
        
        self.assertTrue(signature.startswith('sha256='))
        self.assertEqual(len(signature), 71)  # sha256= + 64 hex chars
    
    def test_configuration_workflow(self):
        """Test configuration workflow"""
        # Test backend configuration
        backend = self.sap_backend.create({
            'name': 'Config Test Backend',
            'host': 'config.test.sap.com',
            'port': 50000,
            'company_db': 'CONFIG_DB',
            'username': 'config_user',
            'password': 'config_password',
            'timeout': 60,
            'retry_attempts': 5,
            'batch_size': 200,
            'incremental_sync_days': 14
        })
        
        self.assertEqual(backend.timeout, 60)
        self.assertEqual(backend.retry_attempts, 5)
        self.assertEqual(backend.batch_size, 200)
        self.assertEqual(backend.incremental_sync_days, 14)
        
        # Test plugin configuration
        plugin_config = self.sap_plugin_manager.get_plugin_configuration('test_plugin')
        self.assertIn('plugin_id', plugin_config)
        self.assertIn('config_schema', plugin_config)
        
        # Test webhook configuration
        webhook_config = self.sap_webhook_system.create_webhook(
            name='Config Test Webhook',
            url='https://config.test.example.com/webhook',
            event_types=['sync_start'],
            timeout=45,
            retry_attempts=5,
            retry_delay=10
        )
        
        self.assertEqual(webhook_config.timeout, 45)
        self.assertEqual(webhook_config.retry_attempts, 5)
        self.assertEqual(webhook_config.retry_delay, 10)
