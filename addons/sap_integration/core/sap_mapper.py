# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Data Mapper

Handles data transformation between SAP and Odoo formats.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError

from ..config.sap_config import (
    SAP_PARTNER_FIELDS, SAP_PRODUCT_FIELDS, SAP_CARD_TYPES, SAP_ITEM_TYPES
)
from .sap_logger import SapValidationError


class SapDataMapper(models.AbstractModel):
    """Base data mapper for SAP integration"""
    _name = 'sap.data.mapper'
    _description = 'SAP Data Mapper'
    
    def map_sap_partner_to_odoo(self, sap_data):
        """Map SAP partner data to Odoo partner format"""
        try:
            odoo_data = {
                'name': sap_data.get(SAP_PARTNER_FIELDS['card_name'], ''),
                'ref': sap_data.get(SAP_PARTNER_FIELDS['card_code'], ''),
                'email': sap_data.get(SAP_PARTNER_FIELDS['email'], ''),
                'phone': sap_data.get(SAP_PARTNER_FIELDS['phone'], ''),
                'mobile': sap_data.get(SAP_PARTNER_FIELDS['mobile'], ''),
                'street': sap_data.get(SAP_PARTNER_FIELDS['address'], ''),
                'street2': sap_data.get(SAP_PARTNER_FIELDS['address2'], ''),
                'city': sap_data.get(SAP_PARTNER_FIELDS['city'], ''),
                'zip': sap_data.get(SAP_PARTNER_FIELDS['zip'], ''),
                'website': sap_data.get(SAP_PARTNER_FIELDS['website'], ''),
                'is_company': True,
                'customer_rank': 1,
                'supplier_rank': 0,
            }
            
            # Handle card type
            card_type = sap_data.get(SAP_PARTNER_FIELDS['card_type'], '')
            if card_type == SAP_CARD_TYPES['supplier']:
                odoo_data['supplier_rank'] = 1
                odoo_data['customer_rank'] = 0
            
            # Handle state and country
            state_name = sap_data.get(SAP_PARTNER_FIELDS['state'], '')
            if state_name:
                state = self.env['res.country.state'].search([
                    ('name', 'ilike', state_name)
                ], limit=1)
                if state:
                    odoo_data['state_id'] = state.id
            
            country_code = sap_data.get(SAP_PARTNER_FIELDS['country'], '')
            if country_code:
                country = self.env['res.country'].search([
                    ('code', '=', country_code)
                ], limit=1)
                if country:
                    odoo_data['country_id'] = country.id
            
            # Add comment with SAP reference
            sap_card_code = sap_data.get(SAP_PARTNER_FIELDS['card_code'], '')
            if sap_card_code:
                odoo_data['comment'] = f"SAP Customer: {sap_card_code}"
            
            return odoo_data
            
        except Exception as e:
            raise SapValidationError(
                f"Error mapping SAP partner to Odoo: {str(e)}",
                error_code='MAPPING_ERROR',
                details={'sap_data': sap_data, 'error': str(e)}
            )
    
    def map_odoo_partner_to_sap(self, odoo_partner):
        """Map Odoo partner data to SAP format"""
        try:
            sap_data = {
                SAP_PARTNER_FIELDS['card_name']: odoo_partner.name or '',
                SAP_PARTNER_FIELDS['card_code']: odoo_partner.ref or '',
                SAP_PARTNER_FIELDS['email']: odoo_partner.email or '',
                SAP_PARTNER_FIELDS['phone']: odoo_partner.phone or '',
                SAP_PARTNER_FIELDS['mobile']: odoo_partner.mobile or '',
                SAP_PARTNER_FIELDS['address']: odoo_partner.street or '',
                SAP_PARTNER_FIELDS['address2']: odoo_partner.street2 or '',
                SAP_PARTNER_FIELDS['city']: odoo_partner.city or '',
                SAP_PARTNER_FIELDS['zip']: odoo_partner.zip or '',
                SAP_PARTNER_FIELDS['website']: odoo_partner.website or '',
            }
            
            # Handle state and country
            if odoo_partner.state_id:
                sap_data[SAP_PARTNER_FIELDS['state']] = odoo_partner.state_id.name
            
            if odoo_partner.country_id:
                sap_data[SAP_PARTNER_FIELDS['country']] = odoo_partner.country_id.code
            
            # Determine card type based on partner type
            if odoo_partner.supplier_rank > 0:
                sap_data[SAP_PARTNER_FIELDS['card_type']] = SAP_CARD_TYPES['supplier']
            else:
                sap_data[SAP_PARTNER_FIELDS['card_type']] = SAP_CARD_TYPES['customer']
            
            return sap_data
            
        except Exception as e:
            raise SapValidationError(
                f"Error mapping Odoo partner to SAP: {str(e)}",
                error_code='MAPPING_ERROR',
                details={'odoo_partner': odoo_partner.id, 'error': str(e)}
            )
    
    def map_sap_product_to_odoo(self, sap_data):
        """Map SAP product data to Odoo product format"""
        try:
            odoo_data = {
                'name': sap_data.get(SAP_PRODUCT_FIELDS['item_name'], ''),
                'default_code': sap_data.get(SAP_PRODUCT_FIELDS['item_code'], ''),
                'type': 'product',
                'sale_ok': True,
                'purchase_ok': True,
            }
            
            # Handle item type
            item_type = sap_data.get(SAP_PRODUCT_FIELDS['item_type'], '')
            if item_type == SAP_ITEM_TYPES['service']:
                odoo_data['type'] = 'service'
            
            # Handle weight
            weight = sap_data.get(SAP_PRODUCT_FIELDS['weight'], 0)
            if weight:
                odoo_data['weight'] = float(weight)
            
            # Handle dimensions
            length = sap_data.get(SAP_PRODUCT_FIELDS['length'], 0)
            width = sap_data.get(SAP_PRODUCT_FIELDS['width'], 0)
            height = sap_data.get(SAP_PRODUCT_FIELDS['height'], 0)
            
            if length:
                odoo_data['length'] = float(length)
            if width:
                odoo_data['width'] = float(width)
            if height:
                odoo_data['height'] = float(height)
            
            return odoo_data
            
        except Exception as e:
            raise SapValidationError(
                f"Error mapping SAP product to Odoo: {str(e)}",
                error_code='MAPPING_ERROR',
                details={'sap_data': sap_data, 'error': str(e)}
            )
    
    def map_odoo_product_to_sap(self, odoo_product):
        """Map Odoo product data to SAP format"""
        try:
            sap_data = {
                SAP_PRODUCT_FIELDS['item_name']: odoo_product.name or '',
                SAP_PRODUCT_FIELDS['item_code']: odoo_product.default_code or '',
            }
            
            # Handle item type
            if odoo_product.type == 'service':
                sap_data[SAP_PRODUCT_FIELDS['item_type']] = SAP_ITEM_TYPES['service']
            else:
                sap_data[SAP_PRODUCT_FIELDS['item_type']] = SAP_ITEM_TYPES['item']
            
            # Handle weight
            if odoo_product.weight:
                sap_data[SAP_PRODUCT_FIELDS['weight']] = odoo_product.weight
            
            # Handle dimensions
            if odoo_product.length:
                sap_data[SAP_PRODUCT_FIELDS['length']] = odoo_product.length
            if odoo_product.width:
                sap_data[SAP_PRODUCT_FIELDS['width']] = odoo_product.width
            if odoo_product.height:
                sap_data[SAP_PRODUCT_FIELDS['height']] = odoo_product.height
            
            return sap_data
            
        except Exception as e:
            raise SapValidationError(
                f"Error mapping Odoo product to SAP: {str(e)}",
                error_code='MAPPING_ERROR',
                details={'odoo_product': odoo_product.id, 'error': str(e)}
            )
    
    def map_sap_quotation_to_odoo(self, sap_data):
        """Map SAP quotation data to Odoo sale order format"""
        try:
            # Find partner by SAP card code
            card_code = sap_data.get('CardCode', '')
            partner = self.env['res.partner'].search([
                ('ref', '=', card_code)
            ], limit=1)
            
            if not partner:
                raise SapValidationError(
                    f"Partner with SAP CardCode {card_code} not found in Odoo",
                    error_code='PARTNER_NOT_FOUND'
                )
            
            odoo_data = {
                'partner_id': partner.id,
                'state': 'draft',
                'client_order_ref': sap_data.get('NumAtCard', ''),
            }
            
            # Map order lines
            order_lines = []
            for line_data in sap_data.get('DocumentLines', []):
                line_vals = self._map_sap_quotation_line_to_odoo(line_data)
                if line_vals:
                    order_lines.append((0, 0, line_vals))
            
            odoo_data['order_line'] = order_lines
            
            return odoo_data
            
        except Exception as e:
            raise SapValidationError(
                f"Error mapping SAP quotation to Odoo: {str(e)}",
                error_code='MAPPING_ERROR',
                details={'sap_data': sap_data, 'error': str(e)}
            )
    
    def _map_sap_quotation_line_to_odoo(self, line_data):
        """Map SAP quotation line to Odoo sale order line"""
        try:
            # Find product by SAP item code
            item_code = line_data.get('ItemCode', '')
            product = self.env['product.product'].search([
                ('default_code', '=', item_code)
            ], limit=1)
            
            if not product:
                # Create a placeholder product if not found
                product = self.env['product.product'].create({
                    'name': line_data.get('ItemDescription', 'Unknown Product'),
                    'default_code': item_code,
                    'type': 'product',
                })
            
            return {
                'product_id': product.id,
                'name': line_data.get('ItemDescription', ''),
                'product_uom_qty': line_data.get('Quantity', 0),
                'price_unit': line_data.get('Price', 0),
            }
            
        except Exception as e:
            raise SapValidationError(
                f"Error mapping SAP quotation line to Odoo: {str(e)}",
                error_code='MAPPING_ERROR',
                details={'line_data': line_data, 'error': str(e)}
            )
    
    def map_odoo_sale_order_to_sap(self, odoo_order):
        """Map Odoo sale order to SAP quotation format"""
        try:
            # Get partner's SAP card code
            partner_ref = odoo_order.partner_id.ref
            if not partner_ref:
                raise SapValidationError(
                    f"Partner {odoo_order.partner_id.name} has no SAP reference",
                    error_code='MISSING_SAP_REFERENCE'
                )
            
            sap_data = {
                'CardCode': partner_ref,
                'NumAtCard': odoo_order.client_order_ref or '',
                'DocumentLines': []
            }
            
            # Map order lines
            for line in odoo_order.order_line:
                line_data = self._map_odoo_sale_order_line_to_sap(line)
                if line_data:
                    sap_data['DocumentLines'].append(line_data)
            
            return sap_data
            
        except Exception as e:
            raise SapValidationError(
                f"Error mapping Odoo sale order to SAP: {str(e)}",
                error_code='MAPPING_ERROR',
                details={'odoo_order': odoo_order.id, 'error': str(e)}
            )
    
    def _map_odoo_sale_order_line_to_sap(self, line):
        """Map Odoo sale order line to SAP quotation line"""
        try:
            # Get product's SAP item code
            item_code = line.product_id.default_code
            if not item_code:
                raise SapValidationError(
                    f"Product {line.product_id.name} has no SAP reference",
                    error_code='MISSING_SAP_REFERENCE'
                )
            
            return {
                'ItemCode': item_code,
                'ItemDescription': line.name,
                'Quantity': line.product_uom_qty,
                'Price': line.price_unit,
            }
            
        except Exception as e:
            raise SapValidationError(
                f"Error mapping Odoo sale order line to SAP: {str(e)}",
                error_code='MAPPING_ERROR',
                details={'line_id': line.id, 'error': str(e)}
            )
