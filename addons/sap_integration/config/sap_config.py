# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Integration Configuration

This module contains all configuration constants and settings
for the SAP integration module.
"""

# SAP Service Layer Configuration
SAP_SERVICE_LAYER_ENDPOINTS = {
    'login': '/Login',
    'logout': '/Logout',
    'business_partners': '/BusinessPartners',
    'items': '/Items',
    'quotations': '/Quotations',
    'orders': '/Orders',
    'invoices': '/Invoices',
}

# SAP Field Mappings
SAP_PARTNER_FIELDS = {
    'card_code': 'CardCode',
    'card_name': 'CardName',
    'card_type': 'CardType',
    'email': 'EmailAddress',
    'phone': 'Phone1',
    'mobile': 'Cellular',
    'address': 'Address',
    'address2': 'Address2',
    'city': 'City',
    'zip': 'ZipCode',
    'state': 'State',
    'country': 'Country',
    'website': 'Website',
}

SAP_PRODUCT_FIELDS = {
    'item_code': 'ItemCode',
    'item_name': 'ItemName',
    'item_type': 'ItemType',
    'items_group_code': 'ItemsGroupCode',
    'sales_unit': 'SalesUnit',
    'purchase_unit': 'PurchaseUnit',
    'inventory_unit': 'InventoryUnit',
    'weight': 'Weight',
    'weight_unit': 'WeightUnit',
    'length': 'Length',
    'width': 'Width',
    'height': 'Height',
    'dimension_unit': 'DimensionUnit',
}

# Sync Configuration
SYNC_CONFIG = {
    'default_batch_size': 100,
    'max_batch_size': 1000,
    'default_timeout': 30,
    'max_timeout': 300,
    'default_retry_attempts': 3,
    'max_retry_attempts': 10,
    'session_timeout_minutes': 28,
    'incremental_sync_days': 7,
}

# Sync Status Values
SYNC_STATUS = {
    'pending': 'pending',
    'success': 'success',
    'error': 'error',
    'cancelled': 'cancelled',
}

# Sync Direction Values
SYNC_DIRECTION = {
    'sap_to_odoo': 'sap_to_odoo',
    'odoo_to_sap': 'odoo_to_sap',
    'bidirectional': 'bidirectional',
}

# SAP Card Types
SAP_CARD_TYPES = {
    'customer': 'cCustomer',
    'supplier': 'cSupplier',
    'lead': 'cLid',
}

# SAP Item Types
SAP_ITEM_TYPES = {
    'item': 'itItems',
    'service': 'itService',
}

# Error Messages
ERROR_MESSAGES = {
    'connection_failed': 'Failed to connect to SAP Service Layer',
    'authentication_failed': 'SAP authentication failed',
    'record_not_found': 'Record not found in SAP',
    'sync_failed': 'Synchronization failed',
    'max_retries_exceeded': 'Maximum retry attempts exceeded',
    'invalid_data': 'Invalid data provided for synchronization',
    'backend_inactive': 'SAP backend is not active',
}

# Logging Configuration
LOG_CONFIG = {
    'logger_name': 'sap_integration',
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
}

# Field Validation Rules
VALIDATION_RULES = {
    'required_fields': {
        'partner': ['name', 'ref'],
        'product': ['name', 'default_code'],
        'sale_order': ['partner_id', 'order_line'],
        'invoice': ['partner_id', 'invoice_line_ids'],
    },
    'max_lengths': {
        'card_code': 20,
        'item_code': 20,
        'doc_entry': 20,
        'email': 254,
        'phone': 20,
    },
}

# Default Values
DEFAULT_VALUES = {
    'partner': {
        'is_company': True,
        'customer_rank': 1,
        'supplier_rank': 0,
    },
    'product': {
        'type': 'product',
        'sale_ok': True,
        'purchase_ok': True,
    },
    'sale_order': {
        'state': 'draft',
    },
    'invoice': {
        'move_type': 'out_invoice',
        'state': 'draft',
    },
}
