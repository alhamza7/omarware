# -*- coding: utf-8 -*-
"""SAP Warehouse Adapters"""

from odoo.addons.component.core import Component
import logging

_logger = logging.getLogger(__name__)


class SapWarehouseAdapter(Component):
    """Adapter for SAP Warehouses"""
    _name = 'sap.warehouse.adapter'
    _inherit = 'sap.adapter.crud'
    _apply_on = 'sap.warehouse'
    _sap_model = 'Warehouses'
    
    def search(self, filters=None, skip=0, top=100):
        """Search Warehouses in SAP"""
        connection = self._get_connection()
        try:
            url = f"{connection.base_url}/Warehouses"
            headers = connection._get_headers()
            params = {'$skip': skip, '$top': top}
            
            if filters:
                params['$filter'] = filters
            
            response = connection.session.get(url, headers=headers, params=params, timeout=connection.timeout)
            
            if response.status_code == 200:
                return response.json().get('value', [])
            
            _logger.error(f"Error searching warehouses: {response.status_code}")
            return []
        except Exception as e:
            _logger.error(f"Error searching warehouses in SAP: {str(e)}")
            raise
    
    def read(self, external_id):
        """Read a Warehouse from SAP"""
        connection = self._get_connection()
        try:
            url = f"{connection.base_url}/Warehouses('{external_id}')"
            headers = connection._get_headers()
            
            response = connection.session.get(url, headers=headers, timeout=connection.timeout)
            
            if response.status_code == 200:
                return response.json()
            
            return None
        except Exception as e:
            _logger.error(f"Error reading warehouse {external_id} from SAP: {str(e)}")
            raise

