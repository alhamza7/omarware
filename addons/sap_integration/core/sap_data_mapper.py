# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Data Mapper

Comprehensive data mapping system between SAP and Odoo formats.
"""

from odoo import models, fields, api
import logging
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import json
import re

from .sap_logger import SapLogger, SapValidationError


class SapDataMapper(models.AbstractModel):
    """Enhanced data mapper with comprehensive SAP-Odoo mapping"""
    _name = 'sap.data.mapper'
    _description = 'SAP Data Mapper'
    
    def _setup(self):
        super()._setup()
        _logger = SapLogger(f"sap_integration.{self._name}")
    
    # Partner Mapping
    def map_sap_partner_to_odoo(self, sap_data):
        """Map SAP Business Partner to Odoo Partner"""
        try:
            if not sap_data:
                raise SapValidationError("SAP partner data is required")
            
            # Basic mapping
            partner_data = {
                'name': sap_data.get('CardName', ''),
                'ref': sap_data.get('CardCode', ''),
                'email': sap_data.get('EmailAddress', ''),
                'phone': sap_data.get('Phone1', ''),
                'mobile': sap_data.get('Cellular', ''),
                'website': sap_data.get('Website', ''),
                'is_company': True,
                'customer_rank': 1 if sap_data.get('CardType') == 'cCustomer' else 0,
                'supplier_rank': 1 if sap_data.get('CardType') == 'cSupplier' else 0,
                'comment': f"SAP Partner: {sap_data.get('CardCode', '')}",
            }
            
            # Address mapping - Handle both direct fields and BPAddresses collection
            # Try BPAddresses collection first (array of addresses)
            if 'BPAddresses' in sap_data and isinstance(sap_data['BPAddresses'], list) and sap_data['BPAddresses']:
                # Get the first address from the collection
                address_data = sap_data['BPAddresses'][0]
                partner_data.update({
                    'street': address_data.get('Street', '') or address_data.get('AddressName', ''),
                    'street2': address_data.get('Block', '') or address_data.get('AddressName2', ''),
                    'city': address_data.get('City', ''),
                    'zip': address_data.get('ZipCode', ''),
                    'state_id': self._get_state_id(address_data.get('State', '')),
                    'country_id': self._get_country_id(address_data.get('Country', '')),
                })
            # Fallback to direct address fields
            elif 'Address' in sap_data and isinstance(sap_data['Address'], str):
                partner_data.update({
                    'street': sap_data.get('Address', ''),
                    'street2': sap_data.get('Address2', ''),
                    'city': sap_data.get('City', ''),
                    'zip': sap_data.get('ZipCode', ''),
                    'state_id': self._get_state_id(sap_data.get('State', '')),
                    'country_id': self._get_country_id(sap_data.get('Country', '')),
                })
            
            # Contact person mapping - Handle as array
            if 'ContactEmployees' in sap_data and isinstance(sap_data['ContactEmployees'], list) and sap_data['ContactEmployees']:
                contact = sap_data['ContactEmployees'][0]
                if 'Name' in contact:
                    partner_data['contact_name'] = contact.get('Name', '')
                if 'E_Mail' in contact or 'EmailAddress' in contact:
                    partner_data['contact_email'] = contact.get('E_Mail', '') or contact.get('EmailAddress', '')
                if 'Phone1' in contact:
                    partner_data['contact_phone'] = contact.get('Phone1', '')
            
            # Tax information
            if 'TaxIdNum' in sap_data:
                partner_data['vat'] = sap_data['TaxIdNum']
            
            # Payment terms
            if 'PayTermsGrpCode' in sap_data:
                partner_data['property_payment_term_id'] = self._get_payment_term_id(
                    sap_data['PayTermsGrpCode']
                )
            
            # Currency
            if 'Currency' in sap_data:
                partner_data['property_account_position_id'] = self._get_fiscal_position_id(
                    sap_data['Currency']
                )
            
            return partner_data
            
        except Exception as e:
            _logger.error(f"Error mapping SAP partner to Odoo: {str(e)}")
            raise SapValidationError(f"Failed to map SAP partner: {str(e)}")
    
    def map_odoo_partner_to_sap(self, odoo_partner):
        """Map Odoo Partner to SAP Business Partner (الطريقة الموصى بها: لا CardCode عند الإنشاء، Notes+Address إلزاميان كنص)"""
        try:
            if not odoo_partner:
                raise SapValidationError("Odoo partner is required")
            
            # Notes و Address إلزاميان معاً كنص غير فارغ (حل validation في SAP)
            _notes = (odoo_partner.city or odoo_partner.street or odoo_partner.name or "—").strip() or "—"
            _address = (odoo_partner.street or odoo_partner.city or odoo_partner.name or "—").strip() or "—"
            
            # Basic mapping - لا نرسل CardCode (SAP ينشئه عند الإنشاء؛ وعند التحديث يُستخدم في URL فقط)
            sap_data = {
                'CardName': odoo_partner.name,
                'EmailAddress': odoo_partner.email or '',
                'Phone1': odoo_partner.phone or '',
                'Cellular': odoo_partner.mobile or '',
                'Website': odoo_partner.website or '',
                'CardType': 'cCustomer' if odoo_partner.customer_rank > 0 else 'cSupplier',
                'Notes': _notes,
                'Address': _address,
                'Series': 72,
                'GroupCode': 100,
                'Country': (odoo_partner.country_id and odoo_partner.country_id.code) or 'IQ',
            }
            
            # Contact person mapping
            if odoo_partner.contact_name:
                sap_data['ContactPersons'] = [{
                    'Name': odoo_partner.contact_name,
                    'EmailAddress': odoo_partner.contact_email or '',
                    'Phone1': odoo_partner.contact_phone or '',
                }]
            
            # Tax information
            if odoo_partner.vat:
                sap_data['TaxIdNum'] = odoo_partner.vat
            
            # Payment terms
            if odoo_partner.property_payment_term_id:
                sap_data['PayTermsGrpCode'] = self._get_sap_payment_term_code(
                    odoo_partner.property_payment_term_id
                )
            
            # Currency
            if odoo_partner.property_account_position_id:
                sap_data['Currency'] = self._get_sap_currency_code(
                    odoo_partner.property_account_position_id
                )
            
            return sap_data
            
        except Exception as e:
            _logger.error(f"Error mapping Odoo partner to SAP: {str(e)}")
            raise SapValidationError(f"Failed to map Odoo partner: {str(e)}")
    
    # Product Mapping
    def map_sap_product_to_odoo(self, sap_data):
        """Map SAP Item to Odoo Product"""
        try:
            if not sap_data:
                raise SapValidationError("SAP product data is required")
            
            # Basic mapping
            product_data = {
                'name': sap_data.get('ItemName', ''),
                'default_code': sap_data.get('ItemCode', ''),
                'description': sap_data.get('ItemDescription', ''),
                'sale_ok': True,
                'purchase_ok': True,
                'available_in_pos': True,  # Make product available in Point of Sale
                'type': 'consu',  # Consumable = Storable products (displayed as "Goods" in UI)
                'tracking': 'none',  # Enable inventory tracking
                'is_storable': True,  # Enable "Track Inventory" checkbox in UI
                'categ_id': self._get_product_category_id(sap_data.get('ItemsGroupCode', '')),
                'list_price': float(sap_data.get('SalesUnitPrice', 0)),
                'standard_price': float(sap_data.get('PurchaseUnitPrice', 0)),
                'weight': float(sap_data.get('Weight', 0)),
                'volume': float(sap_data.get('Volume', 0)),
                'sale_delay': float(sap_data.get('SalesDeliveryDays', 0)),
                'purchase_delay': float(sap_data.get('PurchaseDeliveryDays', 0)),
            }
            
            # UoM mapping
            if 'SalesUnit' in sap_data:
                product_data['uom_id'] = self._get_uom_id(sap_data['SalesUnit'])
                # Note: uom_po_id removed in Odoo 19.0
            
            # Tax information
            if 'TaxCode' in sap_data:
                product_data['taxes_id'] = [(6, 0, self._get_tax_ids(sap_data['TaxCode']))]
                product_data['supplier_taxes_id'] = [(6, 0, self._get_tax_ids(sap_data['TaxCode']))]
            
            # Inventory information
            if 'InventoryUoM' in sap_data:
                product_data['uom_id'] = self._get_uom_id(sap_data['InventoryUoM'])
            
            # Barcode
            if 'BarCode' in sap_data:
                product_data['barcode'] = sap_data['BarCode']
            
            # Active status
            product_data['active'] = sap_data.get('Valid', 'Y') == 'Y'
            
            return product_data
            
        except Exception as e:
            _logger.error(f"Error mapping SAP product to Odoo: {str(e)}")
            raise SapValidationError(f"Failed to map SAP product: {str(e)}")
    
    def map_odoo_product_to_sap(self, odoo_product):
        """Map Odoo Product to SAP Item"""
        try:
            if not odoo_product:
                raise SapValidationError("Odoo product is required")
            
            # Basic mapping
            sap_data = {
                'ItemName': odoo_product.name,
                'ItemCode': odoo_product.default_code or '',
                'ItemDescription': odoo_product.description or '',
                'ItemsGroupCode': self._get_sap_item_group_code(odoo_product.categ_id),
                'SalesUnitPrice': float(odoo_product.list_price),
                'PurchaseUnitPrice': float(odoo_product.standard_price),
                'Weight': float(odoo_product.weight),
                'Volume': float(odoo_product.volume),
                'SalesDeliveryDays': float(odoo_product.sale_delay),
                'PurchaseDeliveryDays': float(odoo_product.purchase_delay),
                'Valid': 'Y' if odoo_product.active else 'N',
            }
            
            # UoM mapping
            if odoo_product.uom_id:
                sap_data['SalesUnit'] = self._get_sap_uom_code(odoo_product.uom_id)
                sap_data['InventoryUoM'] = self._get_sap_uom_code(odoo_product.uom_id)
                # Use same UoM for purchase in Odoo 19.0
                sap_data['PurchaseUnit'] = self._get_sap_uom_code(odoo_product.uom_id)
            
            # Tax information
            if odoo_product.taxes_id:
                sap_data['TaxCode'] = self._get_sap_tax_code(odoo_product.taxes_id[0])
            
            # Barcode
            if odoo_product.barcode:
                sap_data['BarCode'] = odoo_product.barcode
            
            return sap_data
            
        except Exception as e:
            _logger.error(f"Error mapping Odoo product to SAP: {str(e)}")
            raise SapValidationError(f"Failed to map Odoo product: {str(e)}")
    
    # Order Mapping
    def map_sap_order_to_odoo(self, sap_data):
        """Map SAP Order to Odoo Sale Order"""
        try:
            if not sap_data:
                raise SapValidationError("SAP order data is required")
            
            # Basic mapping
            order_data = {
                'name': sap_data.get('DocNum', ''),
                'client_order_ref': sap_data.get('NumAtCard', ''),
                'date_order': self._parse_sap_date(sap_data.get('DocDate')),
                'validity_date': self._parse_sap_date(sap_data.get('DocDueDate')),
                'payment_term_id': self._get_payment_term_id(sap_data.get('PayTermsGrpCode')),
                'partner_id': self._get_partner_id(sap_data.get('CardCode')),
                'currency_id': self._get_currency_id(sap_data.get('DocCurrency')),
                'amount_total': float(sap_data.get('DocTotal', 0)),
                'amount_tax': float(sap_data.get('VatSum', 0)),
                'amount_untaxed': float(sap_data.get('DocTotal', 0)) - float(sap_data.get('VatSum', 0)),
                'state': 'draft',
            }
            
            # Order lines mapping
            if 'DocumentLines' in sap_data:
                order_lines = []
                for line in sap_data['DocumentLines']:
                    line_data = {
                        'product_id': self._get_product_id(line.get('ItemCode')),
                        'name': line.get('ItemDescription', ''),
                        'product_uom_qty': float(line.get('Quantity', 0)),
                        'price_unit': float(line.get('Price', 0)),
                        'discount': float(line.get('DiscountPercent', 0)),
                        'tax_id': [(6, 0, self._get_tax_ids(line.get('TaxCode')))],
                    }
                    order_lines.append((0, 0, line_data))
                
                order_data['order_line'] = order_lines
            
            return order_data
            
        except Exception as e:
            _logger.error(f"Error mapping SAP order to Odoo: {str(e)}")
            raise SapValidationError(f"Failed to map SAP order: {str(e)}")
    
    def map_odoo_order_to_sap(self, odoo_order):
        """Map Odoo Sale Order to SAP Order"""
        try:
            if not odoo_order:
                raise SapValidationError("Odoo order is required")
            
            # Basic mapping
            sap_data = {
                'DocNum': odoo_order.name,
                'NumAtCard': odoo_order.client_order_ref or '',
                'DocDate': self._format_sap_date(odoo_order.date_order),
                'DocDueDate': self._format_sap_date(odoo_order.validity_date),
                'PayTermsGrpCode': self._get_sap_payment_term_code(odoo_order.payment_term_id),
                'CardCode': odoo_order.partner_id.ref or '',
                'DocCurrency': odoo_order.currency_id.name,
                'DocTotal': float(odoo_order.amount_total),
                'VatSum': float(odoo_order.amount_tax),
            }
            
            # Order lines mapping
            if odoo_order.order_line:
                document_lines = []
                for line in odoo_order.order_line:
                    line_data = {
                        'ItemCode': line.product_id.default_code or '',
                        'ItemDescription': line.name,
                        'Quantity': float(line.product_uom_qty),
                        'Price': float(line.price_unit),
                        'DiscountPercent': float(line.discount),
                        'TaxCode': self._get_sap_tax_code(line.tax_id[0]) if line.tax_id else '',
                    }
                    document_lines.append(line_data)
                
                sap_data['DocumentLines'] = document_lines
            
            return sap_data
            
        except Exception as e:
            _logger.error(f"Error mapping Odoo order to SAP: {str(e)}")
            raise SapValidationError(f"Failed to map Odoo order: {str(e)}")
    
    # Invoice Mapping
    def map_sap_invoice_to_odoo(self, sap_data):
        """Map SAP Invoice to Odoo Account Move"""
        try:
            if not sap_data:
                raise SapValidationError("SAP invoice data is required")
            
            # Basic mapping
            invoice_data = {
                'name': sap_data.get('DocNum', ''),
                'ref': sap_data.get('NumAtCard', ''),
                'invoice_date': self._parse_sap_date(sap_data.get('DocDate')),
                'invoice_date_due': self._parse_sap_date(sap_data.get('DocDueDate')),
                'partner_id': self._get_partner_id(sap_data.get('CardCode')),
                'currency_id': self._get_currency_id(sap_data.get('DocCurrency')),
                'amount_total': float(sap_data.get('DocTotal', 0)),
                'amount_tax': float(sap_data.get('VatSum', 0)),
                'amount_untaxed': float(sap_data.get('DocTotal', 0)) - float(sap_data.get('VatSum', 0)),
                'move_type': 'out_invoice',
                'state': 'draft',
            }
            
            # Invoice lines mapping
            if 'DocumentLines' in sap_data:
                invoice_lines = []
                for line in sap_data['DocumentLines']:
                    line_data = {
                        'product_id': self._get_product_id(line.get('ItemCode')),
                        'name': line.get('ItemDescription', ''),
                        'quantity': float(line.get('Quantity', 0)),
                        'price_unit': float(line.get('Price', 0)),
                        'discount': float(line.get('DiscountPercent', 0)),
                        'tax_ids': [(6, 0, self._get_tax_ids(line.get('TaxCode')))],
                    }
                    invoice_lines.append((0, 0, line_data))
                
                invoice_data['invoice_line_ids'] = invoice_lines
            
            return invoice_data
            
        except Exception as e:
            _logger.error(f"Error mapping SAP invoice to Odoo: {str(e)}")
            raise SapValidationError(f"Failed to map SAP invoice: {str(e)}")
    
    def map_odoo_invoice_to_sap(self, odoo_invoice):
        """Map Odoo Account Move to SAP Invoice"""
        try:
            if not odoo_invoice:
                raise SapValidationError("Odoo invoice is required")
            
            # Basic mapping
            sap_data = {
                'DocNum': odoo_invoice.name,
                'NumAtCard': odoo_invoice.ref or '',
                'DocDate': self._format_sap_date(odoo_invoice.invoice_date),
                'DocDueDate': self._format_sap_date(odoo_invoice.invoice_date_due),
                'CardCode': odoo_invoice.partner_id.ref or '',
                'DocCurrency': odoo_invoice.currency_id.name,
                'DocTotal': float(odoo_invoice.amount_total),
                'VatSum': float(odoo_invoice.amount_tax),
            }
            
            # Invoice lines mapping
            if odoo_invoice.invoice_line_ids:
                document_lines = []
                for line in odoo_invoice.invoice_line_ids:
                    line_data = {
                        'ItemCode': line.product_id.default_code or '' if line.product_id else '',
                        'ItemDescription': line.name or '',
                        'Quantity': float(line.quantity),
                        'Price': float(line.price_unit),
                        'UnitPrice': float(line.price_unit),
                        'DiscountPercent': float(line.discount),
                        'TaxCode': self._get_sap_tax_code(line.tax_ids[0]) if line.tax_ids else '',
                    }
                    document_lines.append(line_data)
                
                sap_data['DocumentLines'] = document_lines
            
            return sap_data
            
        except Exception as e:
            _logger.error(f"Error mapping Odoo invoice to SAP: {str(e)}")
            raise SapValidationError(f"Failed to map Odoo invoice: {str(e)}")
    
    # Helper Methods
    def _get_state_id(self, state_name):
        """Get Odoo state ID by name"""
        if not state_name:
            return False
        state = self.env['res.country.state'].search([('name', 'ilike', state_name)], limit=1)
        return state.id if state else False
    
    def _get_country_id(self, country_code):
        """Get Odoo country ID by code"""
        if not country_code:
            return False
        country = self.env['res.country'].search([('code', '=', country_code)], limit=1)
        return country.id if country else False
    
    def _get_partner_id(self, card_code):
        """Get Odoo partner ID by SAP CardCode"""
        if not card_code:
            return False
        partner = self.env['res.partner'].search([('ref', '=', card_code)], limit=1)
        return partner.id if partner else False
    
    def _get_product_id(self, item_code):
        """Get Odoo product ID by SAP ItemCode"""
        if not item_code:
            return False
        product = self.env['product.product'].search([('default_code', '=', item_code)], limit=1)
        return product.id if product else False
    
    def _get_currency_id(self, currency_code):
        """Get Odoo currency ID by code"""
        if not currency_code:
            return False
        currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
        return currency.id if currency else False
    
    def _get_payment_term_id(self, sap_payment_term_code):
        """Get Odoo payment term ID by SAP code"""
        if not sap_payment_term_code:
            return False
        # This would need to be implemented based on your payment term mapping
        return False
    
    def _get_sap_payment_term_code(self, odoo_payment_term):
        """Get SAP payment term code from Odoo payment term"""
        if not odoo_payment_term:
            return ''
        # This would need to be implemented based on your payment term mapping
        return ''
    
    def _get_fiscal_position_id(self, currency_code):
        """Get Odoo fiscal position ID by currency"""
        if not currency_code:
            return False
        # This would need to be implemented based on your fiscal position mapping
        return False
    
    def _get_sap_currency_code(self, fiscal_position):
        """Get SAP currency code from Odoo fiscal position"""
        if not fiscal_position:
            return ''
        # This would need to be implemented based on your fiscal position mapping
        return ''
    
    def _get_product_category_id(self, sap_item_group_code):
        """Get Odoo product category ID by SAP item group code"""
        if not sap_item_group_code:
            return False
        # This would need to be implemented based on your category mapping
        return False
    
    def _get_sap_item_group_code(self, odoo_category):
        """Get SAP item group code from Odoo category"""
        if not odoo_category:
            return ''
        # This would need to be implemented based on your category mapping
        return ''
    
    def _get_uom_id(self, sap_uom_code):
        """Get Odoo UoM ID by SAP code"""
        if not sap_uom_code:
            return False
        # This would need to be implemented based on your UoM mapping
        return False
    
    def _get_sap_uom_code(self, odoo_uom):
        """Get SAP UoM code from Odoo UoM"""
        if not odoo_uom:
            return ''
        # This would need to be implemented based on your UoM mapping
        return ''
    
    def _get_tax_ids(self, sap_tax_code):
        """Get Odoo tax IDs by SAP tax code"""
        if not sap_tax_code:
            return []
        # This would need to be implemented based on your tax mapping
        return []
    
    def _get_sap_tax_code(self, odoo_tax):
        """Get SAP tax code from Odoo tax"""
        if not odoo_tax:
            return ''
        # This would need to be implemented based on your tax mapping
        return ''
    
    def _parse_sap_date(self, sap_date):
        """Parse SAP date format to Odoo date"""
        if not sap_date:
            return False
        try:
            # SAP dates are typically in format: /Date(1234567890000)/
            if sap_date.startswith('/Date('):
                timestamp = int(sap_date[6:-2]) / 1000
                return datetime.fromtimestamp(timestamp).date()
            else:
                return datetime.strptime(sap_date, '%Y-%m-%d').date()
        except:
            return False
    
    def _format_sap_date(self, odoo_date):
        """Format Odoo date to SAP format"""
        if not odoo_date:
            return ''
        try:
            return odoo_date.strftime('%Y-%m-%d')
        except:
            return ''
    
    def _validate_data(self, data, required_fields):
        """Validate if all required fields are present in the data"""
        missing_fields = [f for f in required_fields if not data.get(f)]
        if missing_fields:
            raise SapValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        return True
