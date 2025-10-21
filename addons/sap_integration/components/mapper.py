# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Mappers

These mappers transform data between SAP and Odoo formats
"""

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (
    mapping,
    only_create,
    none,
)
import logging

_logger = logging.getLogger(__name__)


# ===== Partner Mapper =====

class SapPartnerImportMapper(Component):
    """Mapper for importing SAP Business Partners to Odoo"""
    _name = 'sap.partner.import.mapper'
    _inherit = 'base.import.mapper'
    _collection = 'sap.backend'
    _apply_on = 'sap.res.partner'
    
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
    
    @mapping
    def external_id(self, record):
        return {'external_id': record.get('CardCode')}
    
    @mapping
    def name(self, record):
        return {'name': record.get('CardName', '')}
    
    @mapping
    def email(self, record):
        return {'email': record.get('EmailAddress', '')}
    
    @mapping
    def phone(self, record):
        # Map Phone1, Phone, or Cellular to phone field
        phone = record.get('Phone1', '') or record.get('Phone', '') or record.get('Cellular', '')
        if phone:
            return {'phone': phone}
    
    @mapping
    def street(self, record):
        return {'street': record.get('Address', '')}
    
    @mapping
    def street2(self, record):
        return {'street2': record.get('Address2', '')}
    
    @mapping
    def city(self, record):
        return {'city': record.get('City', '')}
    
    @mapping
    def zip(self, record):
        return {'zip': record.get('ZipCode', '')}
    
    @mapping
    def website(self, record):
        return {'website': record.get('Website', '')}
    
    @mapping
    def customer_rank(self, record):
        card_type = record.get('CardType', 'cCustomer')
        return {'customer_rank': 1 if card_type == 'cCustomer' else 0}
    
    @mapping
    def supplier_rank(self, record):
        card_type = record.get('CardType', 'cCustomer')
        return {'supplier_rank': 1 if card_type == 'cSupplier' else 0}
    
    @mapping
    def is_company(self, record):
        return {'is_company': True}
    
    @mapping
    def sap_fields(self, record):
        return {
            'sap_card_name': record.get('CardName', ''),
            'sap_card_type': record.get('CardType', 'cCustomer'),
        }
    
    @mapping
    def country_id(self, record):
        country_code = record.get('Country', '')
        if country_code:
            country = self.env['res.country'].search([
                ('code', '=', country_code)
            ], limit=1)
            if country:
                return {'country_id': country.id}
        return {}
    
    @mapping
    def state_id(self, record):
        state_name = record.get('State', '')
        if state_name:
            state = self.env['res.country.state'].search([
                ('name', 'ilike', state_name)
            ], limit=1)
            if state:
                return {'state_id': state.id}
        return {}


class SapPartnerExportMapper(Component):
    """Mapper for exporting Odoo Partners to SAP"""
    _name = 'sap.partner.export.mapper'
    _inherit = 'base.export.mapper'
    _collection = 'sap.backend'
    _apply_on = 'sap.res.partner'
    
    @mapping
    def card_name(self, record):
        return {'CardName': record.name}
    
    @mapping
    def card_code(self, record):
        if record.external_id:
            return {'CardCode': record.external_id}
        return {}
    
    @mapping
    def email(self, record):
        return {'EmailAddress': record.email or ''}
    
    @mapping
    def phone(self, record):
        return {'Phone1': record.phone or ''}
    
    @mapping
    def mobile(self, record):
        return {'Cellular': record.mobile or ''}
    
    @mapping
    def address(self, record):
        return {
            'Address': record.street or '',
            'Address2': record.street2 or '',
            'City': record.city or '',
            'ZipCode': record.zip or '',
            'State': record.state_id.name if record.state_id else '',
            'Country': record.country_id.code if record.country_id else '',
        }
    
    @mapping
    def card_type(self, record):
        if record.supplier_rank > 0:
            return {'CardType': 'cSupplier'}
        return {'CardType': 'cCustomer'}


# ===== Product Mapper =====

class SapProductImportMapper(Component):
    """Mapper for importing SAP Items to Odoo"""
    _name = 'sap.product.import.mapper'
    _inherit = 'base.import.mapper'
    _collection = 'sap.backend'
    _apply_on = 'sap.product.product'
    
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
    
    @mapping
    def external_id(self, record):
        return {'external_id': record.get('ItemCode')}
    
    @mapping
    def name(self, record):
        return {'name': record.get('ItemName', '')}
    
    @mapping
    def default_code(self, record):
        return {'default_code': record.get('ItemCode', '')}
    
    @mapping
    def list_price(self, record):
        return {'list_price': record.get('SalesUnitPrice', 0.0)}
    
    @mapping
    def standard_price(self, record):
        return {'standard_price': record.get('PurchaseUnitPrice', 0.0)}
    
    @mapping
    def type(self, record):
        item_type = record.get('ItemType', 'itItems')
        if item_type == 'itService':
            return {'type': 'service'}
        # In Odoo 19, use 'consu' for storable products
        return {'type': 'consu'}
    
    @mapping
    def sale_ok(self, record):
        return {'sale_ok': True}
    
    @mapping
    def purchase_ok(self, record):
        return {'purchase_ok': True}
    
    @mapping
    def active(self, record):
        # Normalize various possible SAP 'Valid' representations
        valid_value = record.get('Valid', 'Y')
        if isinstance(valid_value, str):
            normalized = valid_value.strip().upper()
            return {'active': normalized in ('Y', 'YES', 'TRUE', '1')}
        if isinstance(valid_value, (int, float)):
            return {'active': bool(valid_value)}
        if isinstance(valid_value, bool):
            return {'active': valid_value}
        # Default to active when unknown
        return {'active': True}
    
    @mapping
    def description(self, record):
        return {
            'description': record.get('UserText', ''),
            'description_sale': record.get('UserText', ''),
            'description_purchase': record.get('UserText', ''),
        }
    
    @mapping
    def sap_fields(self, record):
        return {
            'sap_item_name': record.get('ItemName', ''),
            'sap_item_type': record.get('ItemType', 'itItems'),
            'sap_items_group_code': record.get('ItemsGroupCode', 0),
        }


class SapProductExportMapper(Component):
    """Mapper for exporting Odoo Products to SAP"""
    _name = 'sap.product.export.mapper'
    _inherit = 'base.export.mapper'
    _collection = 'sap.backend'
    _apply_on = 'sap.product.product'
    
    @mapping
    def item_name(self, record):
        return {'ItemName': record.name}
    
    @mapping
    def item_code(self, record):
        if record.external_id:
            return {'ItemCode': record.external_id}
        elif record.default_code:
            return {'ItemCode': record.default_code}
        return {}
    
    @mapping
    def prices(self, record):
        return {
            'SalesUnitPrice': record.list_price,
            'PurchaseUnitPrice': record.standard_price,
        }
    
    @mapping
    def item_type(self, record):
        if record.type == 'service':
            return {'ItemType': 'itService'}
        return {'ItemType': 'itItems'}
    
    @mapping
    def valid(self, record):
        return {'Valid': 'Y' if record.active else 'N'}


# ===== Sale Order Mapper =====

class SapSaleOrderImportMapper(Component):
    """Mapper for importing SAP Orders to Odoo"""
    _name = 'sap.sale.order.import.mapper'
    _inherit = 'base.import.mapper'
    _collection = 'sap.backend'
    _apply_on = 'sap.sale.order'
    
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
    
    @mapping
    def external_id(self, record):
        return {'external_id': str(record.get('DocEntry', ''))}
    
    @mapping
    def sap_doc_num(self, record):
        return {'sap_doc_num': str(record.get('DocNum', ''))}
    
    @mapping
    def partner_id(self, record):
        card_code = record.get('CardCode', '')
        if card_code:
            # Find binding first
            binder = self.binder_for('sap.res.partner')
            partner_binding = binder.to_internal(card_code)
            if partner_binding:
                return {'partner_id': partner_binding.odoo_id.id}
            
            # Fallback: search by ref
            partner = self.env['res.partner'].search([
                ('ref', '=', card_code)
            ], limit=1)
            if partner:
                return {'partner_id': partner.id}
        return {}
    
    @mapping
    def date_order(self, record):
        return {'date_order': record.get('DocDate', '')}
    
    @mapping
    def validity_date(self, record):
        return {'validity_date': record.get('DocDueDate', '')}
    
    @mapping
    def state(self, record):
        # Set to 'sale' for orders, 'draft' for quotations
        return {'state': 'sale'}


class SapSaleOrderExportMapper(Component):
    """Mapper for exporting Odoo Sale Orders to SAP"""
    _name = 'sap.sale.order.export.mapper'
    _inherit = 'base.export.mapper'
    _collection = 'sap.backend'
    _apply_on = 'sap.sale.order'
    
    @mapping
    def card_code(self, record):
        # Try to get SAP CardCode from binding
        if hasattr(record.partner_id, 'sap_bind_ids'):
            bindings = record.partner_id.sap_bind_ids.filtered(
                lambda b: b.backend_id == self.backend_record
            )
            if bindings:
                return {'CardCode': bindings[0].external_id}
        
        # Fallback to ref
        if record.partner_id.ref:
            return {'CardCode': record.partner_id.ref}
        return {}
    
    @mapping
    def dates(self, record):
        return {
            'DocDate': record.date_order.strftime('%Y-%m-%d') if record.date_order else '',
            'DocDueDate': record.validity_date.strftime('%Y-%m-%d') if record.validity_date else '',
        }
    
    @mapping
    def document_lines(self, record):
        lines = []
        for line in record.order_line:
            line_data = {
                'Quantity': line.product_uom_qty,
                'UnitPrice': line.price_unit,
                'DiscountPercent': line.discount,
            }
            
            # Get ItemCode from product binding
            if hasattr(line.product_id, 'sap_bind_ids'):
                bindings = line.product_id.sap_bind_ids.filtered(
                    lambda b: b.backend_id == self.backend_record
                )
                if bindings:
                    line_data['ItemCode'] = bindings[0].external_id
                elif line.product_id.default_code:
                    line_data['ItemCode'] = line.product_id.default_code
            
            if 'ItemCode' in line_data:  # Only add if we have an ItemCode
                lines.append(line_data)
        
        return {'DocumentLines': lines}
