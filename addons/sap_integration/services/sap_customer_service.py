# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Customer Service

Business logic for customer synchronization between SAP and Odoo.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError

from ..core.sap_base_service import SapBaseService
from ..core.sap_data_mapper import SapDataMapper
from ..core.sap_logger import SapSyncError, SapValidationError


class SapCustomerService(SapBaseService):
    """Service for SAP customer synchronization operations"""
    _name = 'sap.customer.service'
    _description = 'SAP Customer Service'
    
    def sync_customer_from_sap(self, backend_id, sap_customer_data):
        """Sync a single customer from SAP to Odoo"""
        try:
            # Validate input data
            if not sap_customer_data:
                raise SapValidationError("SAP customer data is required")
            
            # DEBUG: Log incoming data type
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info(f"DEBUG: sap_customer_data type = {type(sap_customer_data)}")
            if isinstance(sap_customer_data, dict):
                _logger.info(f"DEBUG: sap_customer_data keys = {list(sap_customer_data.keys())[:10]}")
            else:
                _logger.error(f"DEBUG: sap_customer_data is NOT a dict! It's a {type(sap_customer_data)}")
            
            # Map SAP data to Odoo format
            mapper = self.env['sap.data.mapper']
            odoo_data = mapper.map_sap_partner_to_odoo(sap_customer_data)
            
            # Prepare data for sync
            odoo_data = self._prepare_sync_data(odoo_data, 'partner')
            
            # Find or create partner
            partner = self._find_or_create_partner(odoo_data, sap_customer_data)
            
            # Log successful sync
            self._log_success(
                backend_id=backend_id,
                operation='Import Customer',
                message=f'Successfully synced customer {sap_customer_data.get("CardCode", "Unknown")}',
                model_name='res.partner',
                external_id=sap_customer_data.get('CardCode'),
                odoo_id=partner.id
            )
            
            return {
                'status': 'success',
                'partner_id': partner.id,
                'message': f'Customer {partner.name} synced successfully'
            }
            
        except SapValidationError:
            raise
        except Exception as e:
            error_msg, error_type, error_traceback = self._handle_exception(
                backend_id=backend_id,
                operation='Import Customer',
                exception=e,
                model_name='res.partner',
                external_id=sap_customer_data.get('CardCode') if sap_customer_data else None
            )
            raise SapSyncError(error_msg, error_code=error_type)
    
    def sync_customer_to_sap(self, backend_id, odoo_partner_id):
        """Sync a single customer from Odoo to SAP"""
        try:
            partner = self.env['res.partner'].browse(odoo_partner_id)
            if not partner.exists():
                raise SapValidationError(f"Partner with ID {odoo_partner_id} not found")
            
            # Map Odoo data to SAP format
            mapper = self.env['sap.data.mapper']
            sap_data = mapper.map_odoo_partner_to_sap(partner)
            
            # Get SAP connection
            connection = self._get_backend_connection(backend_id)
            
            # Check if customer already exists in SAP
            existing_customer = self._find_sap_customer(connection, partner.ref)
            
            if existing_customer:
                # Update existing customer
                result = connection.update_business_partner(partner.ref, sap_data)
                operation = 'Update Customer'
            else:
                # Create new customer
                result = connection.create_business_partner(sap_data)
                operation = 'Create Customer'
            
            connection.close_session()
            
            # Log successful sync
            self._log_success(
                backend_id=backend_id,
                operation=operation,
                message=f'Successfully synced customer {partner.name} to SAP',
                model_name='res.partner',
                external_id=partner.ref,
                odoo_id=partner.id
            )
            
            return {
                'status': 'success',
                'sap_card_code': partner.ref,
                'message': f'Customer {partner.name} synced to SAP successfully'
            }
            
        except SapValidationError:
            raise
        except Exception as e:
            error_msg, error_type, error_traceback = self._handle_exception(
                backend_id=backend_id,
                operation='Export Customer',
                exception=e,
                model_name='res.partner',
                odoo_id=odoo_partner_id
            )
            raise SapSyncError(error_msg, error_code=error_type)
    
    def sync_all_customers_from_sap(self, backend_id, filters=None, batch_size=None):
        """Sync all customers from SAP to Odoo"""
        try:
            # Get connection
            connection = self._get_backend_connection(backend_id)
            
            # Get batch size from backend or use default
            if not batch_size:
                backend = self.env['sap.backend'].browse(backend_id)
                batch_size = backend.batch_size
            
            # Initialize sync result
            result = self._create_sync_result('Import All Customers', backend_id)
            start_time = fields.Datetime.now()
            
            # Get customers from SAP
            customers_data = connection.get_customers(
                top=batch_size,
                filter_query=filters
            )
            
            customers = customers_data.get('value', [])
            result['total_processed'] = len(customers)
            
            # Process each customer
            for customer_data in customers:
                try:
                    sync_result = self.sync_customer_from_sap(backend_id, customer_data)
                    if sync_result['status'] == 'success':
                        result['successful'] += 1
                    else:
                        result['failed'] += 1
                        result['errors'].append(sync_result.get('message', 'Unknown error'))
                except Exception as e:
                    result['failed'] += 1
                    result['errors'].append(str(e))
                    self.logger.error(f"Error syncing customer {customer_data.get('CardCode', 'Unknown')}: {str(e)}")
            
            connection.close_session()
            
            # Finalize result
            end_time = fields.Datetime.now()
            result['duration'] = (end_time - start_time).total_seconds()
            result = self._finalize_sync_result(result)
            
            # Log summary
            self._log_success(
                backend_id=backend_id,
                operation='Import All Customers',
                message=f"Synced {result['successful']} customers, {result['failed']} failed",
                records_processed=result['total_processed']
            )
            
            return result
            
        except Exception as e:
            error_msg, error_type, error_traceback = self._handle_exception(
                backend_id=backend_id,
                operation='Import All Customers',
                exception=e
            )
            raise SapSyncError(error_msg, error_code=error_type)
    
    def _find_or_create_partner(self, odoo_data, sap_data):
        """Find existing partner or create new one"""
        # Look for partner by SAP reference
        sap_card_code = sap_data.get('CardCode', '')
        if sap_card_code:
            partner = self.env['res.partner'].search([
                ('ref', '=', sap_card_code)
            ], limit=1)
            
            if partner:
                # Update existing partner
                partner.write(odoo_data)
                self.logger.info(f"Updated existing partner: {partner.name}")
                return partner
        
        # Create new partner
        partner = self.env['res.partner'].create(odoo_data)
        self.logger.info(f"Created new partner: {partner.name}")
        return partner
    
    def _find_sap_customer(self, connection, card_code):
        """Find customer in SAP by card code"""
        if not card_code:
            return None
        
        try:
            result = connection.get_customers(
                filter_query=f"CardCode eq '{card_code}'"
            )
            customers = result.get('value', [])
            return customers[0] if customers else None
        except Exception as e:
            self.logger.warning(f"Error finding SAP customer {card_code}: {str(e)}")
            return None
    
    def get_customer_sync_status(self, backend_id, partner_id):
        """Get sync status for a specific customer"""
        try:
            partner = self.env['res.partner'].browse(partner_id)
            if not partner.exists():
                raise SapValidationError(f"Partner with ID {partner_id} not found")
            
            # Check if partner has SAP reference
            if not partner.ref:
                return {
                    'status': 'not_synced',
                    'message': 'Partner has no SAP reference',
                    'can_sync': False
                }
            
            # Check if partner exists in SAP
            connection = self._get_backend_connection(backend_id)
            sap_customer = self._find_sap_customer(connection, partner.ref)
            connection.close_session()
            
            if sap_customer:
                return {
                    'status': 'synced',
                    'message': 'Partner is synced with SAP',
                    'can_sync': True,
                    'sap_data': sap_customer
                }
            else:
                return {
                    'status': 'not_found_in_sap',
                    'message': 'Partner not found in SAP',
                    'can_sync': True
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'can_sync': False
            }
