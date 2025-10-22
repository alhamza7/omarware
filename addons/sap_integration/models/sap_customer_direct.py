# -*- coding: utf-8 -*-
"""
SAP Customer Direct Import - Simplified Version
This bypasses the complex service layer and imports directly
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SapCustomerDirectImport(models.TransientModel):
    """Direct SAP Customer Import Helper"""
    _name = 'sap.customer.direct.import'
    _description = 'SAP Customer Direct Import'
    
    @api.model
    def import_customer_direct(self, backend, card_code, customer_data):
        """
        Import a single customer directly without service layer complexity
        
        Args:
            backend: SAP backend record
            card_code: SAP customer card code
            customer_data: Dictionary with customer data from SAP
        
        Returns:
            res.partner record
        """
        try:
            # Validate input
            if not isinstance(customer_data, dict):
                raise UserError(f"Customer data must be a dictionary, got {type(customer_data)}")
            
            # Extract basic info
            card_name = customer_data.get('CardName', card_code)
            
            # Check if partner already exists
            partner = self.env['res.partner'].search([
                ('ref', '=', card_code)
            ], limit=1)
            
            # Prepare partner data
            partner_vals = {
                'name': card_name,
                'ref': card_code,
                'is_company': True,
                'customer_rank': 1,
                'supplier_rank': 0,
            }
            
            # Add optional fields safely
            if customer_data.get('EmailAddress'):
                partner_vals['email'] = customer_data['EmailAddress']
            
            if customer_data.get('Phone1'):
                partner_vals['phone'] = customer_data['Phone1']
            
            if customer_data.get('Cellular'):
                partner_vals['mobile'] = customer_data['Cellular']
            
            if customer_data.get('Website'):
                partner_vals['website'] = customer_data['Website']
            
            # Handle BPAddresses collection (array of addresses)
            if 'BPAddresses' in customer_data and isinstance(customer_data['BPAddresses'], list):
                if customer_data['BPAddresses']:
                    addr = customer_data['BPAddresses'][0]
                    if addr.get('Street'):
                        partner_vals['street'] = addr['Street']
                    if addr.get('Block'):
                        partner_vals['street2'] = addr['Block']
                    if addr.get('City'):
                        partner_vals['city'] = addr['City']
                    if addr.get('ZipCode'):
                        partner_vals['zip'] = addr['ZipCode']
                    if addr.get('Country'):
                        country = self.env['res.country'].search([
                            ('code', '=', addr['Country'])
                        ], limit=1)
                        if country:
                            partner_vals['country_id'] = country.id
            
            # Handle direct address fields (fallback)
            elif customer_data.get('Address'):
                partner_vals['street'] = customer_data['Address']
            
            if customer_data.get('City'):
                partner_vals['city'] = customer_data['City']
            
            if customer_data.get('ZipCode'):
                partner_vals['zip'] = customer_data['ZipCode']
            
            # Create or update partner
            if partner:
                partner.write(partner_vals)
                _logger.info(f"Updated existing partner: {partner.name} ({card_code})")
            else:
                partner = self.env['res.partner'].create(partner_vals)
                _logger.info(f"Created new partner: {partner.name} ({card_code})")
            
            # Create or update sync record
            sync_record = self.env['sap.customer.sync'].search([
                ('backend_id', '=', backend.id),
                ('sap_customer_id', '=', card_code)
            ], limit=1)
            
            sync_vals = {
                'backend_id': backend.id,
                'sap_customer_id': card_code,
                'sap_customer_name': card_name,
                'odoo_partner_id': partner.id,
                'sync_status': 'success',
                'last_sync': fields.Datetime.now(),
                'error_message': False,
            }
            
            if sync_record:
                sync_record.write(sync_vals)
            else:
                self.env['sap.customer.sync'].create(sync_vals)
            
            return partner
            
        except Exception as e:
            _logger.error(f"Error in direct customer import for {card_code}: {str(e)}", exc_info=True)
            raise

