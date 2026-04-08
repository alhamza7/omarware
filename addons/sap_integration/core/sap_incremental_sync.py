# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Incremental Sync

Incremental synchronization system with change detection and delta updates.
"""

from odoo import models, fields, api
import logging
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import json
import hashlib
import threading

from .sap_logger import SapLogger, SapSyncError, SapValidationError
from .sap_base_service import SapBaseService
from ..config.sap_config import SYNC_CONFIG


class SapIncrementalSync(SapBaseService):
    """Incremental synchronization system"""
    _name = 'sap.incremental.sync'
    _description = 'SAP Incremental Synchronization'
    
    _sync_lock = threading.Lock()
    
    @api.model
    def sync_incremental(self, backend_id, entity_types=None, days_back=7):
        """
        Perform incremental synchronization
        
        :param backend_id: ID of the SAP backend
        :param entity_types: List of entity types to sync
        :param days_back: Number of days to look back for changes
        :return: Dictionary with sync results
        """
        try:
            backend = self._get_backend(backend_id)
            
            if not entity_types:
                entity_types = ['partners', 'products', 'orders', 'invoices', 'stock']
            
            _logger.info(f"Starting incremental sync for backend {backend.name}")
            
            sync_results = {
                'backend_id': backend_id,
                'start_time': fields.Datetime.now(),
                'entity_types': entity_types,
                'results': {},
                'summary': {
                    'total_processed': 0,
                    'successful': 0,
                    'failed': 0,
                    'skipped': 0,
                    'new_records': 0,
                    'updated_records': 0,
                    'deleted_records': 0
                }
            }
            
            # Process each entity type
            for entity_type in entity_types:
                try:
                    entity_result = self._sync_entity_incremental(
                        backend_id, entity_type, days_back
                    )
                    sync_results['results'][entity_type] = entity_result
                    
                    # Update summary
                    sync_results['summary']['total_processed'] += entity_result.get('total_processed', 0)
                    sync_results['summary']['successful'] += entity_result.get('successful', 0)
                    sync_results['summary']['failed'] += entity_result.get('failed', 0)
                    sync_results['summary']['skipped'] += entity_result.get('skipped', 0)
                    sync_results['summary']['new_records'] += entity_result.get('new_records', 0)
                    sync_results['summary']['updated_records'] += entity_result.get('updated_records', 0)
                    sync_results['summary']['deleted_records'] += entity_result.get('deleted_records', 0)
                    
                except Exception as e:
                    _logger.error(f"Error in incremental sync for {entity_type}: {str(e)}")
                    sync_results['results'][entity_type] = {
                        'error': str(e),
                        'total_processed': 0,
                        'successful': 0,
                        'failed': 1,
                        'skipped': 0,
                        'new_records': 0,
                        'updated_records': 0,
                        'deleted_records': 0
                    }
                    sync_results['summary']['failed'] += 1
            
            sync_results['end_time'] = fields.Datetime.now()
            sync_results['duration'] = (sync_results['end_time'] - sync_results['start_time']).total_seconds()
            
            # Log summary
            _logger.info(f"Incremental sync completed for backend {backend.name} - "
                           f"Processed: {sync_results['summary']['total_processed']}, "
                           f"New: {sync_results['summary']['new_records']}, "
                           f"Updated: {sync_results['summary']['updated_records']}, "
                           f"Deleted: {sync_results['summary']['deleted_records']}")
            
            return sync_results
            
        except Exception as e:
            _logger.error(f"Error in sync_incremental: {str(e)}")
            raise SapSyncError(f"Failed to perform incremental sync: {str(e)}")
    
    def _sync_entity_incremental(self, backend_id, entity_type, days_back):
        """Perform incremental sync for a specific entity type"""
        try:
            _logger.info(f"Starting incremental sync for entity type: {entity_type}")
            
            # Get entity configuration
            entity_config = self._get_entity_config(entity_type)
            if not entity_config:
                raise SapValidationError(f"Unknown entity type: {entity_type}")
            
            # Get last sync timestamp
            last_sync = self._get_last_sync_timestamp(backend_id, entity_type)
            
            # Calculate sync window
            sync_window_start = last_sync or (fields.Datetime.now() - timedelta(days=days_back))
            sync_window_end = fields.Datetime.now()
            
            # Sync from SAP to Odoo
            sap_to_odoo_result = self._sync_sap_to_odoo_incremental(
                backend_id, entity_type, sync_window_start, sync_window_end
            )
            
            # Sync from Odoo to SAP
            odoo_to_sap_result = self._sync_odoo_to_sap_incremental(
                backend_id, entity_type, sync_window_start, sync_window_end
            )
            
            # Combine results
            combined_result = self._combine_incremental_results(sap_to_odoo_result, odoo_to_sap_result)
            
            # Update last sync timestamp
            self._update_last_sync_timestamp(backend_id, entity_type, sync_window_end)
            
            return combined_result
            
        except Exception as e:
            _logger.error(f"Error in _sync_entity_incremental: {str(e)}")
            raise
    
    def _sync_sap_to_odoo_incremental(self, backend_id, entity_type, start_time, end_time):
        """Sync changes from SAP to Odoo"""
        try:
            backend = self._get_backend(backend_id)
            connection = self._get_connection(backend)
            
            # Get entity configuration
            entity_config = self._get_entity_config(entity_type)
            sap_model = entity_config['sap_model']
            odoo_model = entity_config['odoo_model']
            
            # Build SAP query for incremental sync
            sap_query = self._build_incremental_sap_query(sap_model, start_time, end_time)
            
            # Fetch changed records from SAP
            sap_data = connection.query_entities(sap_model, sap_query)
            
            if not sap_data or not sap_data.get('value'):
                return {
                    'total_processed': 0,
                    'successful': 0,
                    'failed': 0,
                    'skipped': 0,
                    'new_records': 0,
                    'updated_records': 0,
                    'deleted_records': 0
                }
            
            # Process changed records
            results = {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'new_records': 0,
                'updated_records': 0,
                'deleted_records': 0
            }
            
            for sap_record in sap_data['value']:
                try:
                    results['total_processed'] += 1
                    
                    # Get external ID
                    external_id = sap_record.get(entity_config['external_id_field'])
                    if not external_id:
                        results['skipped'] += 1
                        continue
                    
                    # Check if record exists in synced data
                    synced_data = self.env['sap.synced.data'].search([
                        ('backend_id', '=', backend_id),
                        ('external_id', '=', external_id)
                    ])
                    
                    if synced_data:
                        # Check if record has changed
                        if self._has_record_changed(synced_data, sap_record):
                            # Update existing record
                            update_result = self._update_odoo_record_incremental(
                                backend_id, entity_type, synced_data, sap_record
                            )
                            
                            if update_result['status'] == 'success':
                                results['updated_records'] += 1
                                results['successful'] += 1
                            else:
                                results['failed'] += 1
                        else:
                            results['skipped'] += 1
                    else:
                        # Create new record
                        create_result = self._create_odoo_record_incremental(
                            backend_id, entity_type, external_id, sap_record
                        )
                        
                        if create_result['status'] == 'success':
                            results['new_records'] += 1
                            results['successful'] += 1
                        else:
                            results['failed'] += 1
                            
                except Exception as e:
                    _logger.error(f"Error processing SAP record {sap_record}: {str(e)}")
                    results['failed'] += 1
            
            return results
            
        except Exception as e:
            _logger.error(f"Error in _sync_sap_to_odoo_incremental: {str(e)}")
            raise
    
    def _sync_odoo_to_sap_incremental(self, backend_id, entity_type, start_time, end_time):
        """Sync changes from Odoo to SAP"""
        try:
            backend = self._get_backend(backend_id)
            connection = self._get_connection(backend)
            
            # Get entity configuration
            entity_config = self._get_entity_config(entity_type)
            odoo_model = entity_config['odoo_model']
            sap_model = entity_config['sap_model']
            
            # Build Odoo domain for incremental sync
            odoo_domain = self._build_incremental_odoo_domain(odoo_model, start_time, end_time)
            
            # Get changed records from Odoo
            odoo_records = self.env[odoo_model].search(odoo_domain)
            
            if not odoo_records:
                return {
                    'total_processed': 0,
                    'successful': 0,
                    'failed': 0,
                    'skipped': 0,
                    'new_records': 0,
                    'updated_records': 0,
                    'deleted_records': 0
                }
            
            # Process changed records
            results = {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'new_records': 0,
                'updated_records': 0,
                'deleted_records': 0
            }
            
            for odoo_record in odoo_records:
                try:
                    results['total_processed'] += 1
                    
                    # Get external ID
                    external_id = odoo_record.ref or odoo_record.name
                    if not external_id:
                        results['skipped'] += 1
                        continue
                    
                    # Check if record exists in synced data
                    synced_data = self.env['sap.synced.data'].search([
                        ('backend_id', '=', backend_id),
                        ('external_id', '=', external_id)
                    ])
                    
                    if synced_data:
                        # Check if record has changed
                        if self._has_odoo_record_changed(synced_data, odoo_record):
                            # Update existing record
                            update_result = self._update_sap_record_incremental(
                                backend_id, entity_type, synced_data, odoo_record
                            )
                            
                            if update_result['status'] == 'success':
                                results['updated_records'] += 1
                                results['successful'] += 1
                            else:
                                results['failed'] += 1
                        else:
                            results['skipped'] += 1
                    else:
                        # Create new record
                        create_result = self._create_sap_record_incremental(
                            backend_id, entity_type, external_id, odoo_record
                        )
                        
                        if create_result['status'] == 'success':
                            results['new_records'] += 1
                            results['successful'] += 1
                        else:
                            results['failed'] += 1
                            
                except Exception as e:
                    _logger.error(f"Error processing Odoo record {odoo_record.id}: {str(e)}")
                    results['failed'] += 1
            
            return results
            
        except Exception as e:
            _logger.error(f"Error in _sync_odoo_to_sap_incremental: {str(e)}")
            raise
    
    def _has_record_changed(self, synced_data, new_sap_data):
        """Check if SAP record has changed since last sync"""
        try:
            if not synced_data.last_sap_data:
                return True
            
            # Get last SAP data
            last_sap_data = json.loads(synced_data.last_sap_data)
            
            # Calculate hash of both datasets
            last_hash = self._calculate_data_hash(last_sap_data)
            new_hash = self._calculate_data_hash(new_sap_data)
            
            return last_hash != new_hash
            
        except Exception as e:
            _logger.error(f"Error checking record change: {str(e)}")
            return True  # Assume changed if error
    
    def _has_odoo_record_changed(self, synced_data, odoo_record):
        """Check if Odoo record has changed since last sync"""
        try:
            if not synced_data.last_odoo_data:
                return True
            
            # Get last Odoo data
            last_odoo_data = json.loads(synced_data.last_odoo_data)
            
            # Get current Odoo data
            current_odoo_data = odoo_record.read()[0]
            
            # Calculate hash of both datasets
            last_hash = self._calculate_data_hash(last_odoo_data)
            new_hash = self._calculate_data_hash(current_odoo_data)
            
            return last_hash != new_hash
            
        except Exception as e:
            _logger.error(f"Error checking Odoo record change: {str(e)}")
            return True  # Assume changed if error
    
    def _calculate_data_hash(self, data):
        """Calculate hash of data for change detection"""
        try:
            # Convert data to JSON string and calculate hash
            data_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.md5(data_str.encode()).hexdigest()
            
        except Exception as e:
            _logger.error(f"Error calculating data hash: {str(e)}")
            return ''
    
    def _build_incremental_sap_query(self, sap_model, start_time, end_time):
        """Build SAP query for incremental sync"""
        query = {
            'orderby': 'UpdateDate desc'
        }
        
        # Add time filter
        if start_time and end_time:
            start_str = start_time.strftime('%Y-%m-%dT%H:%M:%S')
            end_str = end_time.strftime('%Y-%m-%dT%H:%M:%S')
            query['filter'] = f"UpdateDate ge datetime'{start_str}' and UpdateDate le datetime'{end_str}'"
        
        return query
    
    def _build_incremental_odoo_domain(self, odoo_model, start_time, end_time):
        """Build Odoo domain for incremental sync"""
        domain = []
        
        # Add time filter
        if start_time and end_time:
            domain.append(('write_date', '>=', start_time))
            domain.append(('write_date', '<=', end_time))
        
        return domain
    
    def _create_odoo_record_incremental(self, backend_id, entity_type, external_id, sap_data):
        """Create new Odoo record from SAP data (incremental)"""
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
                operation='create_incremental',
                message=f'Created Odoo record from SAP data (incremental)',
                sync_direction='sap_to_odoo'
            )
            
            return {'status': 'success', 'odoo_id': odoo_record.id, 'synced_data_id': synced_data.id}
            
        except Exception as e:
            _logger.error(f"Error creating Odoo record (incremental): {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def _update_odoo_record_incremental(self, backend_id, entity_type, synced_data, sap_data):
        """Update existing Odoo record from SAP data (incremental)"""
        try:
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
                operation='update_incremental',
                message=f'Updated Odoo record from SAP data (incremental)',
                sync_direction='sap_to_odoo'
            )
            
            return {'status': 'success', 'odoo_id': odoo_record.id}
            
        except Exception as e:
            _logger.error(f"Error updating Odoo record (incremental): {str(e)}")
            synced_data.update_sync_status('failed', str(e))
            return {'status': 'failed', 'error': str(e)}
    
    def _create_sap_record_incremental(self, backend_id, entity_type, external_id, odoo_record):
        """Create new SAP record from Odoo data (incremental)"""
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
                operation='create_incremental',
                message=f'Created SAP record from Odoo data (incremental)',
                sync_direction='odoo_to_sap'
            )
            
            return {'status': 'success', 'sap_id': sap_external_id, 'synced_data_id': synced_data.id}
            
        except Exception as e:
            _logger.error(f"Error creating SAP record (incremental): {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def _update_sap_record_incremental(self, backend_id, entity_type, synced_data, odoo_record):
        """Update existing SAP record from Odoo data (incremental)"""
        try:
            backend = self._get_backend(backend_id)
            connection = self._get_connection(backend)
            
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
                operation='update_incremental',
                message=f'Updated SAP record from Odoo data (incremental)',
                sync_direction='odoo_to_sap'
            )
            
            return {'status': 'success', 'sap_id': synced_data.external_id}
            
        except Exception as e:
            _logger.error(f"Error updating SAP record (incremental): {str(e)}")
            synced_data.update_sync_status('failed', str(e))
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
    
    def _get_last_sync_timestamp(self, backend_id, entity_type):
        """Get last sync timestamp for entity type"""
        try:
            # Get last successful sync record
            domain = [
                ('backend_id', '=', backend_id),
                ('sync_status', '=', 'success'),
                ('model_name', '=', self._get_entity_config(entity_type)['odoo_model'])
            ]
            
            last_sync = self.env['sap.synced.data'].search(domain, order='last_sync_date desc', limit=1)
            
            if last_sync:
                return last_sync.last_sync_date
            else:
                # Return timestamp from days_back if no previous sync
                return fields.Datetime.now() - timedelta(days=SYNC_CONFIG['incremental_sync_days'])
                
        except Exception as e:
            _logger.error(f"Error getting last sync timestamp: {str(e)}")
            return fields.Datetime.now() - timedelta(days=SYNC_CONFIG['incremental_sync_days'])
    
    def _update_last_sync_timestamp(self, backend_id, entity_type, timestamp):
        """Update last sync timestamp for entity type"""
        try:
            # This could be stored in a dedicated model or system parameter
            # For now, we'll just log the update
            _logger.info(f"Updated last sync timestamp for {entity_type} to {timestamp}")
            
        except Exception as e:
            _logger.error(f"Error updating last sync timestamp: {str(e)}")
    
    def _combine_incremental_results(self, result1, result2):
        """Combine two incremental sync results"""
        combined = {
            'total_processed': result1.get('total_processed', 0) + result2.get('total_processed', 0),
            'successful': result1.get('successful', 0) + result2.get('successful', 0),
            'failed': result1.get('failed', 0) + result2.get('failed', 0),
            'skipped': result1.get('skipped', 0) + result2.get('skipped', 0),
            'new_records': result1.get('new_records', 0) + result2.get('new_records', 0),
            'updated_records': result1.get('updated_records', 0) + result2.get('updated_records', 0),
            'deleted_records': result1.get('deleted_records', 0) + result2.get('deleted_records', 0)
        }
        return combined
