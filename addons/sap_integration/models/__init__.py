# -*- coding: utf-8 -*-

from . import sap_backend
from . import sap_binding
from . import sap_connector
from . import sap_customer
from . import sap_customer_direct
from . import sap_product_brand  # product.brand model — must load before sap_product
from . import sap_product
from . import sap_product_direct
from . import sap_quotation
from . import sap_sale
from . import sap_invoice
from . import sap_uom
from . import sap_uom_group
from . import sap_pricelist
from . import sap_service_layer
from . import sap_dashboard
from . import sap_dashboard_enhanced
from . import sap_synced_data
from . import sap_uom_mapping
from . import sap_product_uom
from . import sap_dashboard_control
from . import sap_user_management
from . import sap_warehouse

# Import core models
from ..core.sap_logger import SapSyncLog
from ..core.sap_alert_system import SapAlertRule, SapAlert
from ..core.sap_performance_monitor import SapPerformanceMetrics

# New comprehensive product migration models
from . import sap_product_extended
from . import sap_product_pricelist_sync
from . import sap_product_warehouse_info
from . import product_template_uom  # UoM Group fields for products
from . import sale_order_line_uom  # UoM restriction for sale orders
from . import sap_order_mixin      # Shared SAP fields + helpers for sale/purchase orders
from . import sale_order_sap       # SAP integration for sale orders
from . import purchase_order_sap   # SAP integration for purchase orders
from . import sale_order_line_procurement  # Compatibility shim for procurement group
from . import res_partner_sap  # SAP integration for partners/customers
from . import ir_asset  # Patch for ir.asset to handle None manifest

# Auto Sync
from . import sap_auto_sync
from . import sap_realtime_sync
from . import sap_exchange_rate_sync

# Custom Report Designer
from . import custom_report_template
from . import custom_report_qweb_generator
from . import custom_report_pos_integration

# Invoice Visual Designer moved to separate module 'invoice_designer'


