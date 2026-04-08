# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Binders

These binders link Odoo records with SAP records
"""

from odoo.addons.component.core import Component
import logging

_logger = logging.getLogger(__name__)


class SapBinder(Component):
    """Generic SAP Binder"""
    _name = 'sap.binder'
    _inherit = 'base.binder'
    _collection = 'sap.backend'
    _external_field = 'external_id'
    _backend_field = 'backend_id'
    _odoo_field = 'odoo_id'
    _sync_date_field = 'sync_date'


class SapPartnerBinder(Component):
    """Binder for SAP Business Partners"""
    _name = 'sap.res.partner.binder'
    _inherit = 'sap.binder'
    _apply_on = 'sap.res.partner'
    _external_field = 'external_id'  # SAP CardCode


class SapProductBinder(Component):
    """Binder for SAP Items"""
    _name = 'sap.product.product.binder'
    _inherit = 'sap.binder'
    _apply_on = 'sap.product.product'
    _external_field = 'external_id'  # SAP ItemCode


class SapSaleOrderBinder(Component):
    """Binder for SAP Orders"""
    _name = 'sap.sale.order.binder'
    _inherit = 'sap.binder'
    _apply_on = 'sap.sale.order'
    _external_field = 'external_id'  # SAP DocEntry


class SapInvoiceBinder(Component):
    """Binder for SAP Invoices"""
    _name = 'sap.account.move.binder'
    _inherit = 'sap.binder'
    _apply_on = 'sap.account.move'
    _external_field = 'external_id'  # SAP DocEntry
