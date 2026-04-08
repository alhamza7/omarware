# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Sync Engine Tests

Unit tests for SAP sync engine functionality.
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from unittest.mock import patch, MagicMock
import json


class TestSapSyncEngine(TransactionCase):
    """Test SAP Sync Engine functionality"""
    
    def setUp(self):
        super().setUp()
        self.sap_sync_engine = self.env['sap.sync.engine']
        self.sap_backend = self.env['sap.backend']
        self.sap_data_mapper = self.env['sap.data.mapper']
        
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
    
    def test_sync_entity_success(self):
        """Test successful entity sync"""
        with patch.object(self.sap_sync_engine, '_sync_sap_to_odoo') as mock_sync:
            mock_sync.return_value = None
            
            result = self.sap_sync_engine.sync_entity(
                backend_id=self.test_backend.id,
                entity_type='partner',
                external_id='TEST001',
                direction='sap_to_odoo'
            )
            
            self.assertEqual(result['status'], 'success')
            self.assertIn('Successfully synchronized', result['message'])
    
    def test_sync_entity_validation_error(self):
        """Test sync entity with validation error"""
        with patch.object(self.sap_sync_engine, '_sync_sap_to_odoo') as mock_sync:
            mock_sync.side_effect = ValidationError("Validation failed")
            
            result = self.sap_sync_engine.sync_entity(
                backend_id=self.test_backend.id,
                entity_type='partner',
                external_id='TEST001',
                direction='sap_to_odoo'
            )
            
            self.assertEqual(result['status'], 'failed')
            self.assertIn('Validation failed', result['message'])
    
    def test_sync_entity_general_error(self):
        """Test sync entity with general error"""
        with patch.object(self.sap_sync_engine, '_sync_sap_to_odoo') as mock_sync:
            mock_sync.side_effect = Exception("General error")
            
            result = self.sap_sync_engine.sync_entity(
                backend_id=self.test_backend.id,
                entity_type='partner',
                external_id='TEST001',
                direction='sap_to_odoo'
            )
            
            self.assertEqual(result['status'], 'failed')
            self.assertIn('General error', result['message'])
    
    def test_sync_entity_bidirectional(self):
        """Test bidirectional sync"""
        with patch.object(self.sap_sync_engine, '_sync_sap_to_odoo') as mock_sap_to_odoo, \
             patch.object(self.sap_sync_engine, '_sync_odoo_to_sap') as mock_odoo_to_sap:
            
            mock_sap_to_odoo.return_value = None
            mock_odoo_to_sap.return_value = None
            
            result = self.sap_sync_engine.sync_entity(
                backend_id=self.test_backend.id,
                entity_type='partner',
                external_id='TEST001',
                record_id=1,
                direction='bidirectional'
            )
            
            self.assertEqual(result['status'], 'success')
            mock_sap_to_odoo.assert_called_once()
            mock_odoo_to_sap.assert_called_once()
    
    def test_sync_entity_sap_to_odoo_only(self):
        """Test SAP to Odoo sync only"""
        with patch.object(self.sap_sync_engine, '_sync_sap_to_odoo') as mock_sync:
            mock_sync.return_value = None
            
            result = self.sap_sync_engine.sync_entity(
                backend_id=self.test_backend.id,
                entity_type='partner',
                external_id='TEST001',
                direction='sap_to_odoo'
            )
            
            self.assertEqual(result['status'], 'success')
            mock_sync.assert_called_once()
    
    def test_sync_entity_odoo_to_sap_only(self):
        """Test Odoo to SAP sync only"""
        with patch.object(self.sap_sync_engine, '_sync_odoo_to_sap') as mock_sync:
            mock_sync.return_value = None
            
            result = self.sap_sync_engine.sync_entity(
                backend_id=self.test_backend.id,
                entity_type='partner',
                record_id=1,
                direction='odoo_to_sap'
            )
            
            self.assertEqual(result['status'], 'success')
            mock_sync.assert_called_once()
    
    def test_sync_entity_missing_external_id(self):
        """Test sync entity with missing external ID"""
        result = self.sap_sync_engine.sync_entity(
            backend_id=self.test_backend.id,
            entity_type='partner',
            direction='sap_to_odoo'
        )
        
        self.assertEqual(result['status'], 'success')
        # Should log warning about missing external_id
    
    def test_sync_entity_missing_record_id(self):
        """Test sync entity with missing record ID"""
        result = self.sap_sync_engine.sync_entity(
            backend_id=self.test_backend.id,
            entity_type='partner',
            direction='odoo_to_sap'
        )
        
        self.assertEqual(result['status'], 'success')
        # Should log warning about missing record_id
    
    def test_sync_all_entities_success(self):
        """Test successful sync all entities"""
        with patch.object(self.sap_sync_engine, '_sync_sap_to_odoo') as mock_sync:
            mock_sync.return_value = None
            
            result = self.sap_sync_engine.sync_all_entities(
                backend_id=self.test_backend.id,
                entity_types=['partner', 'product'],
                direction='sap_to_odoo'
            )
            
            self.assertIn('successful', result)
            self.assertIn('failed', result)
    
    def test_sync_all_entities_error(self):
        """Test sync all entities with error"""
        with patch.object(self.sap_sync_engine, '_sync_sap_to_odoo') as mock_sync:
            mock_sync.side_effect = Exception("Sync error")
            
            result = self.sap_sync_engine.sync_all_entities(
                backend_id=self.test_backend.id,
                entity_types=['partner'],
                direction='sap_to_odoo'
            )
            
            self.assertIn('successful', result)
            self.assertIn('failed', result)
            self.assertEqual(result['failed'], 1)
    
    def test_get_backend_valid(self):
        """Test getting valid backend"""
        backend = self.sap_sync_engine._get_backend(self.test_backend.id)
        self.assertEqual(backend.id, self.test_backend.id)
    
    def test_get_backend_invalid(self):
        """Test getting invalid backend"""
        with self.assertRaises(ValidationError):
            self.sap_sync_engine._get_backend(99999)
    
    def test_sync_sap_to_odoo_success(self):
        """Test successful SAP to Odoo sync"""
        with patch.object(self.test_backend, 'get_connection') as mock_connection:
            # Mock connection
            mock_conn = MagicMock()
            mock_conn.get_entity.return_value = {'CardCode': 'TEST001', 'CardName': 'Test Partner'}
            mock_connection.return_value = mock_conn
            
            with patch.object(self.sap_data_mapper, 'map_sap_to_odoo') as mock_map:
                mock_map.return_value = {'name': 'Test Partner', 'ref': 'TEST001'}
                
                self.sap_sync_engine._sync_sap_to_odoo(
                    self.test_backend,
                    'partner',
                    'TEST001'
                )
                
                mock_conn.get_entity.assert_called_once_with('partner', 'TEST001')
                mock_conn.close_session.assert_called_once()
                mock_map.assert_called_once()
    
    def test_sync_sap_to_odoo_not_found(self):
        """Test SAP to Odoo sync with record not found"""
        with patch.object(self.test_backend, 'get_connection') as mock_connection:
            # Mock connection
            mock_conn = MagicMock()
            mock_conn.get_entity.return_value = None
            mock_connection.return_value = mock_conn
            
            with self.assertRaises(ValidationError):
                self.sap_sync_engine._sync_sap_to_odoo(
                    self.test_backend,
                    'partner',
                    'TEST001'
                )
    
    def test_sync_odoo_to_sap_success(self):
        """Test successful Odoo to SAP sync"""
        with patch.object(self.test_backend, 'get_connection') as mock_connection:
            # Mock connection
            mock_conn = MagicMock()
            mock_connection.return_value = mock_conn
            
            with patch.object(self.sap_data_mapper, 'map_odoo_to_sap') as mock_map:
                mock_map.return_value = {'CardName': 'Test Partner', 'CardCode': 'TEST001'}
                
                # Mock Odoo record
                with patch.object(self.env, '__getitem__') as mock_env:
                    mock_model = MagicMock()
                    mock_record = MagicMock()
                    mock_record.exists.return_value = True
                    mock_model.browse.return_value = mock_record
                    mock_env.return_value = mock_model
                    
                    self.sap_sync_engine._sync_odoo_to_sap(
                        self.test_backend,
                        'partner',
                        1
                    )
                    
                    mock_conn.send_entity.assert_called_once()
                    mock_conn.close_session.assert_called_once()
                    mock_map.assert_called_once()
    
    def test_sync_odoo_to_sap_not_found(self):
        """Test Odoo to SAP sync with record not found"""
        with patch.object(self.env, '__getitem__') as mock_env:
            mock_model = MagicMock()
            mock_record = MagicMock()
            mock_record.exists.return_value = False
            mock_model.browse.return_value = mock_record
            mock_env.return_value = mock_model
            
            with self.assertRaises(ValidationError):
                self.sap_sync_engine._sync_odoo_to_sap(
                    self.test_backend,
                    'partner',
                    1
                )
    
    def test_sync_entity_invalid_backend(self):
        """Test sync entity with invalid backend ID"""
        with self.assertRaises(ValidationError):
            self.sap_sync_engine.sync_entity(
                backend_id=99999,
                entity_type='partner',
                external_id='TEST001',
                direction='sap_to_odoo'
            )
    
    def test_sync_entity_invalid_direction(self):
        """Test sync entity with invalid direction"""
        result = self.sap_sync_engine.sync_entity(
            backend_id=self.test_backend.id,
            entity_type='partner',
            external_id='TEST001',
            direction='invalid_direction'
        )
        
        self.assertEqual(result['status'], 'success')
        # Should handle invalid direction gracefully
    
    def test_sync_entity_logging(self):
        """Test sync entity logging"""
        with patch.object(self.sap_sync_engine, '_sync_sap_to_odoo') as mock_sync:
            mock_sync.return_value = None
            
            # Check that sync log is created
            with patch.object(self.env['sap.sync.log'], 'log_success') as mock_log:
                self.sap_sync_engine.sync_entity(
                    backend_id=self.test_backend.id,
                    entity_type='partner',
                    external_id='TEST001',
                    direction='sap_to_odoo'
                )
                
                mock_log.assert_called_once()
    
    def test_sync_entity_error_logging(self):
        """Test sync entity error logging"""
        with patch.object(self.sap_sync_engine, '_sync_sap_to_odoo') as mock_sync:
            mock_sync.side_effect = Exception("Test error")
            
            # Check that error log is created
            with patch.object(self.env['sap.sync.log'], 'log_error') as mock_log:
                self.sap_sync_engine.sync_entity(
                    backend_id=self.test_backend.id,
                    entity_type='partner',
                    external_id='TEST001',
                    direction='sap_to_odoo'
                )
                
                mock_log.assert_called_once()
    
    def test_sync_all_entities_empty_entity_types(self):
        """Test sync all entities with empty entity types"""
        result = self.sap_sync_engine.sync_all_entities(
            backend_id=self.test_backend.id,
            entity_types=[],
            direction='sap_to_odoo'
        )
        
        self.assertEqual(result['successful'], 0)
        self.assertEqual(result['failed'], 0)
    
    def test_sync_all_entities_none_entity_types(self):
        """Test sync all entities with None entity types"""
        result = self.sap_sync_engine.sync_all_entities(
            backend_id=self.test_backend.id,
            entity_types=None,
            direction='sap_to_odoo'
        )
        
        self.assertEqual(result['successful'], 0)
        self.assertEqual(result['failed'], 0)
