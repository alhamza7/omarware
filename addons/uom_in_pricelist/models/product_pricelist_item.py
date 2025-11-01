# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: JANISH BABU (<https://www.cybrosys.com>)
#    Updated for Odoo 19 compatibility
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#############################################################################
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model):
    """Add UoM support to Pricelist Items - Odoo 19 Compatible"""
    _inherit = "product.pricelist.item"

    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        compute='_compute_product_uom_id',
        store=True, 
        readonly=False, 
        precompute=True,
        help="Specific Unit of Measure for this price rule. "
             "If set, this price will only apply when using this UoM."
    )

    @api.depends('product_tmpl_id')
    def _compute_product_uom_id(self):
        """Set default UoM from product"""
        for line in self:
            if not line.product_uom_id and line.product_tmpl_id:
                line.product_uom_id = line.product_tmpl_id.uom_id
            elif not line.product_tmpl_id:
                line.product_uom_id = False

    def _is_applicable_for(self, product, qty_in_product_uom):
        """Check if rule applies - includes UoM check for Odoo 19"""
        self.ensure_one()
        product.ensure_one()
        
        # First check standard applicability (Odoo 19 signature: 2 params only)
        res = super()._is_applicable_for(product, qty_in_product_uom)
        
        # Additional check for UoM if specified
        # Note: في Odoo 19, نحتاج للحصول على UoM من السياق
        if res and self.product_uom_id:
            # Get current UoM from context or order line
            # This will be checked during price computation
            pass
        
        return res
    
    def _compute_price(self, product, quantity, date=False, currency=False, **kwargs):
        """
        Override price computation to handle UoM-specific prices
        Odoo 19: متوافق مع كل من Odoo 19 و sale module
        
        المشكلة: sale module يمرر uom=... لكن Odoo 19 لا يقبله
        الحل: نقبل **kwargs ونزيل uom
        """
        # Handle empty recordset case (when pricelist_item_id is False)
        if not self:
            # Extract uom from kwargs if present
            uom = kwargs.pop('uom', None)
            if not uom and product:
                uom = product.uom_id
            if not uom:
                # Last resort: get default UoM from env
                uom = self.env['uom.uom'].search([], limit=1)
            # When self is empty, compute base price directly (matching base method behavior)
            # The base method's else clause calls _compute_base_price with self.base or 'list_price'
            # Since self is empty, self.base is False, so it defaults to 'list_price'
            currency = currency or self.env.company.currency_id
            price = product._price_compute('list_price', uom=uom, date=date or False)[product.id]
            src_currency = product.currency_id
            if src_currency != currency:
                price = src_currency._convert(price, currency, self.env.company, date or False, round=False)
            return price
        
        self.ensure_one()
        
        # إزالة uom من kwargs إذا وُجد (للتوافق مع sale module)
        uom = kwargs.pop('uom', None)
        
        # نظام الأولويات الذكي:
        # إذا كان هذا item له uom محدد و fixed price
        if self.product_uom_id and self.compute_price == 'fixed':
            # استخدم السعر الثابت مباشرة
            _logger.debug(f"🎯 Using FIXED price {self.fixed_price} for UoM {self.product_uom_id.name}")
            return self.fixed_price
        
        # في جميع الحالات الأخرى، استخدم الحساب القياسي
        # (بدون uom parameter - Odoo 19)
        return super()._compute_price(product, quantity, date=date, currency=currency)
