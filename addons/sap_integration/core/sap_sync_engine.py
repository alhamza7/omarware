# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Sync Engine

Comprehensive synchronization engine for bidirectional SAP-Odoo integration.
"""

from odoo import models, fields, api
import logging
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import json
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .sap_logger import SapLogger, SapSyncError, SapValidationError, SapConnectionError
from .sap_base_service import SapBaseService
from ..config.sap_config import SYNC_CONFIG, ERROR_MESSAGES


class SapSyncEngine(SapBaseService):
    """Main synchronization engine for SAP-Odoo integration"""
    _name = 'sap.sync.engine'
    _description = 'SAP Synchronization Engine'
    
    _sync_lock = threading.Lock()
    
    @api.model
    def sync_all_entities(self, backend_id, entity_types=None, direction='bidirectional', 
                         batch_size=None, force_full_sync=False):
        """
        Synchronize all entities between SAP and Odoo
        
        :param backend_id: ID of the SAP backend
        :param entity_types: List of entity types to sync (None for all)
        :param direction: 'sap_to_odoo', 'odoo_to_sap', or 'bidirectional'
        :param batch_size: Number of records to process per batch
        :param force_full_sync: Force full sync instead of incremental
        :return: Dictionary with sync results
        """
        try:
            backend = self._get_backend(backend_id)
            batch_size = batch_size or SYNC_CONFIG['default_batch_size']
            
            _logger.info(f"Starting sync for backend {backend.name} - Direction: {direction}")
            
            # Define entity types to sync
            if not entity_types:
                entity_types = ['partners', 'products', 'orders', 'invoices', 'stock']
            
            sync_results = {
                'backend_id': backend_id,
                'start_time': fields.Datetime.now(),
                'direction': direction,
                'entity_types': entity_types,
                'results': {},
                'summary': {
                    'total_processed': 0,
                    'successful': 0,
                    'failed': 0,
                    'skipped': 0,
                    'conflicts': 0
                }
            }
            
            # Process each entity type
            for entity_type in entity_types:
                try:
                    entity_result = self._sync_entity_type(
                        backend_id, entity_type, direction, batch_size, force_full_sync
                    )
                    sync_results['results'][entity_type] = entity_result
                    
                    # Update summary
                    sync_results['summary']['total_processed'] += entity_result.get('total_processed', 0)
                    sync_results['summary']['successful'] += entity_result.get('successful', 0)
                    sync_results['summary']['failed'] += entity_result.get('failed', 0)
                    sync_results['summary']['skipped'] += entity_result.get('skipped', 0)
                    sync_results['summary']['conflicts'] += entity_result.get('conflicts', 0)
                    
                except Exception as e:
                    _logger.error(f"Error syncing entity type {entity_type}: {str(e)}")
                    sync_results['results'][entity_type] = {
                        'error': str(e),
                        'total_processed': 0,
                        'successful': 0,
                        'failed': 1,
                        'skipped': 0,
                        'conflicts': 0
                    }
                    sync_results['summary']['failed'] += 1
            
            sync_results['end_time'] = fields.Datetime.now()
            sync_results['duration'] = (sync_results['end_time'] - sync_results['start_time']).total_seconds()
            
            # Log summary
            _logger.info(f"Sync completed for backend {backend.name} - "
                           f"Processed: {sync_results['summary']['total_processed']}, "
                           f"Success: {sync_results['summary']['successful']}, "
                           f"Failed: {sync_results['summary']['failed']}")
            
            return sync_results
            
        except Exception as e:
            _logger.error(f"Error in sync_all_entities: {str(e)}")
            raise SapSyncError(f"Failed to sync all entities: {str(e)}")
    
    def _sync_entity_type(self, backend_id, entity_type, direction, batch_size, force_full_sync):
        """Sync a specific entity type"""
        try:
            _logger.info(f"Syncing entity type: {entity_type}")
            
            # Get entity configuration
            entity_config = self._get_entity_config(entity_type)
            if not entity_config:
                raise SapValidationError(f"Unknown entity type: {entity_type}")
            
            # Determine sync strategy
            if direction == 'bidirectional':
                # Sync both directions
                sap_to_odoo_result = self._sync_sap_to_odoo(
                    backend_id, entity_type, batch_size, force_full_sync
                )
                odoo_to_sap_result = self._sync_odoo_to_sap(
                    backend_id, entity_type, batch_size, force_full_sync
                )
                
                # Combine results
                return self._combine_sync_results(sap_to_odoo_result, odoo_to_sap_result)
                
            elif direction == 'sap_to_odoo':
                return self._sync_sap_to_odoo(backend_id, entity_type, batch_size, force_full_sync)
                
            elif direction == 'odoo_to_sap':
                return self._sync_odoo_to_sap(backend_id, entity_type, batch_size, force_full_sync)
                
            else:
                raise SapValidationError(f"Invalid sync direction: {direction}")
                
        except Exception as e:
            _logger.error(f"Error syncing entity type {entity_type}: {str(e)}")
            raise
    
    def _sync_sap_to_odoo(self, backend_id, entity_type, batch_size, force_full_sync):
        """Sync data from SAP to Odoo"""
        try:
            backend = self._get_backend(backend_id)
            connection = self._get_connection(backend)
            
            # Get sync configuration
            entity_config = self._get_entity_config(entity_type)
            sap_model = entity_config['sap_model']
            odoo_model = entity_config['odoo_model']
            
            # Get last sync timestamp for incremental sync
            last_sync = None
            if not force_full_sync:
                last_sync = self._get_last_sync_timestamp(backend_id, entity_type, 'sap_to_odoo')
            
            # Build SAP query
            sap_query = self._build_sap_query(sap_model, last_sync, batch_size)
            
            # Fetch data from SAP
            sap_data = connection.query_entities(sap_model, sap_query)
            
            if not sap_data or not sap_data.get('value'):
                return {
                    'total_processed': 0,
                    'successful': 0,
                    'failed': 0,
                    'skipped': 0,
                    'conflicts': 0
                }
            
            # Process records in batches
            results = {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'conflicts': 0
            }
            
            for batch in self._chunk_list(sap_data['value'], batch_size):
                batch_result = self._process_sap_batch(
                    backend_id, entity_type, batch, odoo_model
                )
                
                # Update results
                for key in results:
                    results[key] += batch_result.get(key, 0)
            
            # Update last sync timestamp
            self._update_last_sync_timestamp(backend_id, entity_type, 'sap_to_odoo')
            
            return results
            
        except Exception as e:
            _logger.error(f"Error in _sync_sap_to_odoo: {str(e)}")
            raise
    
    def _sync_odoo_to_sap(self, backend_id, entity_type, batch_size, force_full_sync):
        """Sync data from Odoo to SAP"""
        try:
            backend = self._get_backend(backend_id)
            connection = self._get_connection(backend)
            
            # Get sync configuration
            entity_config = self._get_entity_config(entity_type)
            odoo_model = entity_config['odoo_model']
            sap_model = entity_config['sap_model']
            
            # Get Odoo records to sync
            odoo_domain = self._build_odoo_domain(entity_type, force_full_sync)
            odoo_records = self.env[odoo_model].search(odoo_domain, limit=batch_size)
            
            if not odoo_records:
                return {
                    'total_processed': 0,
                    'successful': 0,
                    'failed': 0,
                    'skipped': 0,
                    'conflicts': 0
                }
            
            # Process records in batches
            results = {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'conflicts': 0
            }
            
            for batch in self._chunk_list(odoo_records, batch_size):
                batch_result = self._process_odoo_batch(
                    backend_id, entity_type, batch, sap_model
                )
                
                # Update results
                for key in results:
                    results[key] += batch_result.get(key, 0)
            
            return results
            
        except Exception as e:
            _logger.error(f"Error in _sync_odoo_to_sap: {str(e)}")
            raise
    
    def _process_sap_batch(self, backend_id, entity_type, sap_records, odoo_model):
        """Process a batch of SAP records"""
        results = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'conflicts': 0
        }
        
        for sap_record in sap_records:
            try:
                results['total_processed'] += 1
                
                # Get external ID
                external_id = sap_record.get(entity_type.upper() + 'Code') or sap_record.get('Code')
                if not external_id:
                    results['skipped'] += 1
                    continue
                
                # Check if record already exists
                synced_data = self.env['sap.synced.data'].search([
                    ('backend_id', '=', backend_id),
                    ('external_id', '=', external_id)
                ])
                
                if synced_data:
                    # Update existing record
                    sync_result = self._update_odoo_record(
                        backend_id, entity_type, synced_data, sap_record
                    )
                else:
                    # Create new record
                    sync_result = self._create_odoo_record(
                        backend_id, entity_type, external_id, sap_record
                    )
                
                # Update results
                if sync_result['status'] == 'success':
                    results['successful'] += 1
                elif sync_result['status'] == 'conflict':
                    results['conflicts'] += 1
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                _logger.error(f"Error processing SAP record {sap_record}: {str(e)}")
                results['failed'] += 1
        
        return results
    
    def _process_odoo_batch(self, backend_id, entity_type, odoo_records, sap_model):
        """Process a batch of Odoo records"""
        results = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'conflicts': 0
        }
        
        for odoo_record in odoo_records:
            try:
                results['total_processed'] += 1
                
                # Get external ID
                external_id = odoo_record.ref or odoo_record.name
                if not external_id:
                    results['skipped'] += 1
                    continue
                
                # Check if record already exists
                synced_data = self.env['sap.synced.data'].search([
                    ('backend_id', '=', backend_id),
                    ('external_id', '=', external_id)
                ])
                
                if synced_data:
                    # Update existing record
                    sync_result = self._update_sap_record(
                        backend_id, entity_type, synced_data, odoo_record
                    )
                else:
                    # Create new record
                    sync_result = self._create_sap_record(
                        backend_id, entity_type, external_id, odoo_record
                    )
                
                # Update results
                if sync_result['status'] == 'success':
                    results['successful'] += 1
                elif sync_result['status'] == 'conflict':
                    results['conflicts'] += 1
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                _logger.error(f"Error processing Odoo record {odoo_record.id}: {str(e)}")
                results['failed'] += 1
        
        return results
    
    def _create_odoo_record(self, backend_id, entity_type, external_id, sap_data):
        """Create new Odoo record from SAP data"""
        try:
            # Get mapper for entity type
            mapper = self._get_mapper(entity_type)
            
            # Map SAP data to Odoo format
            odoo_data = mapper.map_sap_to_odoo(sap_data)
            
            # Create Odoo record
            odoo_model = self._get_entity_config(entity_type)['odoo_model']
            odoo_record = self.env[odoo_model].create(odoo_data)
            
            # Create synced data record
            synced_data = self.env['sap.synced.data'].create_synced_record(
                backend_id=backend_id,
                model_name=odoo_model,
                odoo_id=odoo_record.id,
                external_id=external_id,
                sync_direction='sap_to_odoo',
                sap_data=sap_data,
                odoo_data=odoo_data
            )
            
            # Log success
            self._log_success(
                backend_id=backend_id,
                model_name=odoo_model,
                record_id=odoo_record.id,
                external_id=external_id,
                operation='create',
                message=f'Created Odoo record from SAP data',
                sync_direction='sap_to_odoo'
            )
            
            return {'status': 'success', 'odoo_id': odoo_record.id, 'synced_data_id': synced_data.id}
            
        except Exception as e:
            _logger.error(f"Error creating Odoo record: {str(e)}")
            self._log_error(
                backend_id=backend_id,
                model_name=odoo_model,
                record_id=0,
                external_id=external_id,
                operation='create',
                message=f'Failed to create Odoo record: {str(e)}',
                error_type=type(e).__name__,
                stack_trace=_logger.format_exception(),
                sync_direction='sap_to_odoo'
            )
            return {'status': 'failed', 'error': str(e)}
    
    def _update_odoo_record(self, backend_id, entity_type, synced_data, sap_data):
        """Update existing Odoo record from SAP data"""
        try:
            # Check for conflicts
            conflict = self._detect_conflict(synced_data, sap_data, 'sap')
            if conflict:
                return self._handle_conflict(synced_data, conflict, 'sap')
            
            # Get mapper for entity type
            mapper = self._get_mapper(entity_type)
            
            # Map SAP data to Odoo format
            odoo_data = mapper.map_sap_to_odoo(sap_data)
            
            # Update Odoo record
            odoo_record = synced_data.odoo_record
            odoo_record.write(odoo_data)
            
            # Update synced data record
            synced_data.update_sync_status(
                'success',
                sap_data=sap_data,
                odoo_data=odoo_data
            )
            
            # Log success
            self._log_success(
                backend_id=backend_id,
                model_name=synced_data.model_name,
                record_id=synced_data.odoo_id,
                external_id=synced_data.external_id,
                operation='update',
                message=f'Updated Odoo record from SAP data',
                sync_direction='sap_to_odoo'
            )
            
            return {'status': 'success', 'odoo_id': odoo_record.id}
            
        except Exception as e:
            _logger.error(f"Error updating Odoo record: {str(e)}")
            synced_data.update_sync_status('failed', str(e))
            return {'status': 'failed', 'error': str(e)}
    
    def _create_sap_record(self, backend_id, entity_type, external_id, odoo_record):
        """Create new SAP record from Odoo data"""
        try:
            backend = self._get_backend(backend_id)
            connection = self._get_connection(backend)
            
            # Get mapper for entity type
            mapper = self._get_mapper(entity_type)
            
            # Map Odoo data to SAP format
            sap_data = mapper.map_odoo_to_sap(odoo_record)
            
            # Create SAP record
            sap_model = self._get_entity_config(entity_type)['sap_model']
            sap_result = connection.create_entity(sap_model, sap_data)
            
            # Get SAP external ID from result
            sap_external_id = sap_result.get('Code') or external_id
            
            # Create synced data record
            synced_data = self.env['sap.synced.data'].create_synced_record(
                backend_id=backend_id,
                model_name=odoo_record._name,
                odoo_id=odoo_record.id,
                external_id=sap_external_id,
                sync_direction='odoo_to_sap',
                sap_data=sap_data,
                odoo_data=odoo_record.read()[0]
            )
            
            # Log success
            self._log_success(
                backend_id=backend_id,
                model_name=odoo_record._name,
                record_id=odoo_record.id,
                external_id=sap_external_id,
                operation='create',
                message=f'Created SAP record from Odoo data',
                sync_direction='odoo_to_sap'
            )
            
            return {'status': 'success', 'sap_id': sap_external_id, 'synced_data_id': synced_data.id}
            
        except Exception as e:
            _logger.error(f"Error creating SAP record: {str(e)}")
            self._log_error(
                backend_id=backend_id,
                model_name=odoo_record._name,
                record_id=odoo_record.id,
                external_id=external_id,
                operation='create',
                message=f'Failed to create SAP record: {str(e)}',
                error_type=type(e).__name__,
                stack_trace=_logger.format_exception(),
                sync_direction='odoo_to_sap'
            )
            return {'status': 'failed', 'error': str(e)}
    
    def _update_sap_record(self, backend_id, entity_type, synced_data, odoo_record):
        """Update existing SAP record from Odoo data"""
        try:
            backend = self._get_backend(backend_id)
            connection = self._get_connection(backend)
            
            # Check for conflicts
            conflict = self._detect_conflict(synced_data, odoo_record, 'odoo')
            if conflict:
                return self._handle_conflict(synced_data, conflict, 'odoo')
            
            # Get mapper for entity type
            mapper = self._get_mapper(entity_type)
            
            # Map Odoo data to SAP format
            sap_data = mapper.map_odoo_to_sap(odoo_record)
            
            # Update SAP record
            sap_model = self._get_entity_config(entity_type)['sap_model']
            connection.update_entity(sap_model, synced_data.external_id, sap_data)
            
            # Update synced data record
            synced_data.update_sync_status(
                'success',
                sap_data=sap_data,
                odoo_data=odoo_record.read()[0]
            )
            
            # Log success
            self._log_success(
                backend_id=backend_id,
                model_name=synced_data.model_name,
                record_id=synced_data.odoo_id,
                external_id=synced_data.external_id,
                operation='update',
                message=f'Updated SAP record from Odoo data',
                sync_direction='odoo_to_sap'
            )
            
            return {'status': 'success', 'sap_id': synced_data.external_id}
            
        except Exception as e:
            _logger.error(f"Error updating SAP record: {str(e)}")
            synced_data.update_sync_status('failed', str(e))
            return {'status': 'failed', 'error': str(e)}
    
    def _detect_conflict(self, synced_data, new_data, source):
        """Detect conflicts between existing and new data"""
        try:
            if source == 'sap':
                # Compare with last SAP data
                last_sap_data = json.loads(synced_data.last_sap_data) if synced_data.last_sap_data else {}
                return self._compare_data(last_sap_data, new_data)
            else:
                # Compare with last Odoo data
                last_odoo_data = json.loads(synced_data.last_odoo_data) if synced_data.last_odoo_data else {}
                return self._compare_data(last_odoo_data, new_data)
                
        except Exception as e:
            _logger.error(f"Error detecting conflict: {str(e)}")
            return None
    
    def _compare_data(self, data1, data2):
        """Compare two data sets for conflicts"""
        try:
            # Convert to comparable format
            if isinstance(data1, dict) and isinstance(data2, dict):
                # Compare key fields
                key_fields = ['name', 'code', 'email', 'phone', 'address']
                conflicts = []
                
                for field in key_fields:
                    if field in data1 and field in data2:
                        if str(data1[field]).strip() != str(data2[field]).strip():
                            conflicts.append({
                                'field': field,
                                'old_value': data1[field],
                                'new_value': data2[field]
                            })
                
                return conflicts if conflicts else None
            else:
                return None
                
        except Exception as e:
            _logger.error(f"Error comparing data: {str(e)}")
            return None
    
    def _handle_conflict(self, synced_data, conflict, source):
        """Handle detected conflicts"""
        try:
            # Update synced data with conflict status
            synced_data.write({
                'sync_status': 'conflict',
                'conflict_reason': f"Data conflict detected from {source}",
                'last_error': f"Conflicts in fields: {', '.join([c['field'] for c in conflict])}"
            })
            
            # Log conflict
            self._log_info(
                backend_id=synced_data.backend_id.id,
                model_name=synced_data.model_name,
                record_id=synced_data.odoo_id,
                external_id=synced_data.external_id,
                operation='conflict_detection',
                message=f"Conflict detected: {conflict}",
                sync_direction='bidirectional'
            )
            
            return {'status': 'conflict', 'conflicts': conflict}
            
        except Exception as e:
            _logger.error(f"Error handling conflict: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def _get_entity_config(self, entity_type):
        """Get configuration for entity type"""
        configs = {
            'partners': {
                'sap_model': 'BusinessPartners',
                'odoo_model': 'res.partner',
                'external_id_field': 'CardCode',
                'name_field': 'CardName'
            },
            'products': {
                'sap_model': 'Items',
                'odoo_model': 'product.product',
                'external_id_field': 'ItemCode',
                'name_field': 'ItemName'
            },
            'orders': {
                'sap_model': 'Orders',
                'odoo_model': 'sale.order',
                'external_id_field': 'DocEntry',
                'name_field': 'DocNum'
            },
            'invoices': {
                'sap_model': 'Invoices',
                'odoo_model': 'account.move',
                'external_id_field': 'DocEntry',
                'name_field': 'DocNum'
            },
            'stock': {
                'sap_model': 'StockTransfers',
                'odoo_model': 'stock.picking',
                'external_id_field': 'DocEntry',
                'name_field': 'DocNum'
            }
        }
        return configs.get(entity_type)
    
    def _get_mapper(self, entity_type):
        """Get mapper for entity type"""
        mappers = {
            'partners': self.env['sap.partner.mapper'],
            'products': self.env['sap.product.mapper'],
            'orders': self.env['sap.order.mapper'],
            'invoices': self.env['sap.invoice.mapper'],
            'stock': self.env['sap.stock.mapper']
        }
        return mappers.get(entity_type)
    
    def _build_sap_query(self, sap_model, last_sync, batch_size):
        """Build SAP query for data retrieval"""
        query = {
            'top': batch_size,
            'orderby': 'UpdateDate desc'
        }
        
        if last_sync:
            # Add filter for records modified since last sync
            query['filter'] = f"UpdateDate gt datetime'{last_sync.isoformat()}'"
        
        return query
    
    def _build_odoo_domain(self, entity_type, force_full_sync):
        """Build Odoo domain for record retrieval"""
        domain = []
        
        if not force_full_sync:
            # Add filter for records modified since last sync
            last_sync = self._get_last_sync_timestamp(None, entity_type, 'odoo_to_sap')
            if last_sync:
                domain.append(('write_date', '>=', last_sync))
        
        return domain
    
    def _get_last_sync_timestamp(self, backend_id, entity_type, direction):
        """Get last sync timestamp for incremental sync"""
        try:
            # Get last successful sync record
            domain = [
                ('sync_status', '=', 'success'),
                ('sync_direction', '=', direction)
            ]
            
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            # This would need to be implemented based on your specific needs
            # For now, return None to force full sync
            return None
            
        except Exception as e:
            _logger.error(f"Error getting last sync timestamp: {str(e)}")
            return None
    
    def _update_last_sync_timestamp(self, backend_id, entity_type, direction):
        """Update last sync timestamp"""
        try:
            # This would need to be implemented based on your specific needs
            # For now, just log the update
            _logger.info(f"Updated last sync timestamp for {entity_type} - {direction}")
            
        except Exception as e:
            _logger.error(f"Error updating last sync timestamp: {str(e)}")
    
    def _chunk_list(self, lst, chunk_size):
        """Split list into chunks of specified size"""
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]
    
    def _combine_sync_results(self, result1, result2):
        """Combine two sync results"""
        combined = {
            'total_processed': result1.get('total_processed', 0) + result2.get('total_processed', 0),
            'successful': result1.get('successful', 0) + result2.get('successful', 0),
            'failed': result1.get('failed', 0) + result2.get('failed', 0),
            'skipped': result1.get('skipped', 0) + result2.get('skipped', 0),
            'conflicts': result1.get('conflicts', 0) + result2.get('conflicts', 0)
        }
        return combined
