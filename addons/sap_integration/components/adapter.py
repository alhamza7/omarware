# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Backend Adapters

These adapters interact with SAP Service Layer API
"""

from odoo.addons.component.core import AbstractComponent, Component
import logging

_logger = logging.getLogger(__name__)


class SapAdapter(AbstractComponent):
    """Generic SAP Adapter"""
    _name = 'sap.adapter'
    _inherit = 'base.backend.adapter'
    _usage = 'backend.adapter'
    _collection = 'sap.backend'
    
    def _get_connection(self):
        """Get SAP Service Layer connection"""
        from ..models.sap_service_layer import SapServiceLayerConnection
        
        backend = self.backend_record
        return SapServiceLayerConnection(
            backend.base_url,
            backend.username,
            backend.password,
            backend.company_db
        )


class SapCRUDAdapter(SapAdapter):
    """Generic CRUD Adapter for SAP"""
    _name = 'sap.adapter.crud'
    _inherit = 'sap.adapter'
    _usage = 'backend.adapter'
    
    _sap_model = None  # Override in subclasses
    
    def search(self, filters=None, skip=0, top=100):
        """Search records in SAP"""
        raise NotImplementedError
    
    def read(self, external_id):
        """Read a single record from SAP"""
        raise NotImplementedError
    
    def create(self, data):
        """Create a record in SAP"""
        raise NotImplementedError
    
    def write(self, external_id, data):
        """Update a record in SAP"""
        raise NotImplementedError
    
    def delete(self, external_id):
        """Delete a record in SAP"""
        raise NotImplementedError


# ===== Business Partner (Customer/Supplier) Adapter =====

class SapPartnerAdapter(Component):
    """Adapter for SAP Business Partners"""
    _name = 'sap.partner.adapter'
    _inherit = 'sap.adapter.crud'
    _apply_on = 'sap.res.partner'
    _sap_model = 'BusinessPartners'
    
    def search(self, filters=None, skip=0, top=100):
        """Search Business Partners in SAP"""
        connection = self._get_connection()
        try:
            result = connection.get_customers(
                skip=skip,
                top=top,
                filter_query=filters
            )
            return result.get('value', [])
        except Exception as e:
            _logger.error(f"Error searching partners in SAP: {str(e)}")
            raise
        finally:
            connection.close_session()
    
    def read(self, external_id):
        """Read a Business Partner from SAP"""
        connection = self._get_connection()
        try:
            result = connection.get_customers(
                filter_query=f"CardCode eq '{external_id}'"
            )
            partners = result.get('value', [])
            if partners:
                return partners[0]
            return None
        except Exception as e:
            _logger.error(f"Error reading partner {external_id} from SAP: {str(e)}")
            raise
        finally:
            connection.close_session()
    
    def create(self, data):
        """Create a Business Partner in SAP"""
        connection = self._get_connection()
        try:
            result = connection.create_business_partner(data)
            return result.get('CardCode')
        except Exception as e:
            _logger.error(f"Error creating partner in SAP: {str(e)}")
            raise
        finally:
            connection.close_session()
    
    def write(self, external_id, data):
        """Update a Business Partner in SAP"""
        connection = self._get_connection()
        try:
            result = connection.update_business_partner(external_id, data)
            return True
        except Exception as e:
            _logger.error(f"Error updating partner {external_id} in SAP: {str(e)}")
            raise
        finally:
            connection.close_session()


# ===== Product (Item) Adapter =====

class SapProductAdapter(Component):
    """Adapter for SAP Items"""
    _name = 'sap.product.adapter'
    _inherit = 'sap.adapter.crud'
    _apply_on = 'sap.product.product'
    _sap_model = 'Items'
    
    def search(self, filters=None, skip=0, top=100):
        """Search Items in SAP"""
        connection = self._get_connection()
        try:
            result = connection.get_products(
                skip=skip,
                top=top,
                filter_query=filters
            )
            return result.get('value', [])
        except Exception as e:
            _logger.error(f"Error searching products in SAP: {str(e)}")
            raise
        finally:
            connection.close_session()
    
    def read(self, external_id):
        """Read an Item from SAP"""
        connection = self._get_connection()
        try:
            result = connection.get_products(
                filter_query=f"ItemCode eq '{external_id}'"
            )
            products = result.get('value', [])
            if products:
                return products[0]
            return None
        except Exception as e:
            _logger.error(f"Error reading product {external_id} from SAP: {str(e)}")
            raise
        finally:
            connection.close_session()
    
    def create(self, data):
        """Create an Item in SAP"""
        connection = self._get_connection()
        try:
            result = connection.create_item(data)
            return result.get('ItemCode')
        except Exception as e:
            _logger.error(f"Error creating product in SAP: {str(e)}")
            raise
        finally:
            connection.close_session()
    
    def write(self, external_id, data):
        """Update an Item in SAP"""
        connection = self._get_connection()
        try:
            result = connection.update_item(external_id, data)
            return True
        except Exception as e:
            _logger.error(f"Error updating product {external_id} in SAP: {str(e)}")
            raise
        finally:
            connection.close_session()


# ===== Sale Order Adapter =====

class SapSaleOrderAdapter(Component):
    """Adapter for SAP Orders"""
    _name = 'sap.sale.order.adapter'
    _inherit = 'sap.adapter.crud'
    _apply_on = 'sap.sale.order'
    _sap_model = 'Orders'
    
    def search(self, filters=None, skip=0, top=100):
        """Search Orders in SAP"""
        connection = self._get_connection()
        try:
            result = connection.get_sales_orders(
                skip=skip,
                top=top,
                filter_query=filters
            )
            return result.get('value', [])
        except Exception as e:
            _logger.error(f"Error searching orders in SAP: {str(e)}")
            raise
        finally:
            connection.close_session()
    
    def read(self, external_id):
        """Read an Order from SAP"""
        connection = self._get_connection()
        try:
            result = connection.get_sales_orders(
                filter_query=f"DocEntry eq {external_id}"
            )
            orders = result.get('value', [])
            if orders:
                return orders[0]
            return None
        except Exception as e:
            _logger.error(f"Error reading order {external_id} from SAP: {str(e)}")
            raise
        finally:
            connection.close_session()
    
    def create(self, data):
        """Create an Order in SAP"""
        connection = self._get_connection()
        try:
            result = connection.create_quotation(data)  # Uses quotation endpoint
            return result
        except Exception as e:
            _logger.error(f"Error creating order in SAP: {str(e)}")
            raise
        finally:
            connection.close_session()
    
    def write(self, external_id, data):
        """Update an Order in SAP"""
        connection = self._get_connection()
        try:
            result = connection.update_quotation(external_id, data)
            return result
        except Exception as e:
            _logger.error(f"Error updating order {external_id} in SAP: {str(e)}")
            raise
        finally:
            connection.close_session()


# ===== Invoice Adapter =====

class SapInvoiceAdapter(Component):
    """Adapter for SAP Invoices"""
    _name = 'sap.invoice.adapter'
    _inherit = 'sap.adapter.crud'
    _apply_on = 'sap.account.move'
    _sap_model = 'Invoices'
    
    def search(self, filters=None, skip=0, top=100):
        """Search Invoices in SAP"""
        connection = self._get_connection()
        try:
            result = connection.get_invoices(
                skip=skip,
                top=top,
                filter_query=filters
            )
            return result.get('value', [])
        except Exception as e:
            _logger.error(f"Error searching invoices in SAP: {str(e)}")
            raise
        finally:
            connection.close_session()
    
    def read(self, external_id):
        """Read an Invoice from SAP"""
        connection = self._get_connection()
        try:
            result = connection.get_invoices(
                filter_query=f"DocEntry eq {external_id}"
            )
            invoices = result.get('value', [])
            if invoices:
                return invoices[0]
            return None
        except Exception as e:
            _logger.error(f"Error reading invoice {external_id} from SAP: {str(e)}")
            raise
        finally:
            connection.close_session()

