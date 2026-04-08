# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Product Extended Information

Extended product model with all SAP-specific fields not available in standard Odoo.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class SapProductExtended(models.Model):
    """Extended SAP Product Information"""
    _name = 'sap.product.extended'
    _description = 'SAP Product Extended Information'
    _order = 'product_id'
    
    # ========== Basic Relations ==========
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        ondelete='cascade',
        index=True
    )
    backend_id = fields.Many2one(
        'sap.backend',
        string='SAP Backend',
        required=True,
        ondelete='restrict',
        index=True
    )
    sap_item_code = fields.Char(
        string='SAP Item Code',
        related='product_id.default_code',
        store=True,
        index=True
    )
    
    # ========== Foreign Names & Translations ==========
    foreign_name = fields.Char(
        string='Foreign Name',
        help="Product name in foreign language from SAP"
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to sync foreign_name to product.product"""
        records = super().create(vals_list)
        
        # Sync foreign_name to product.product
        for record, vals in zip(records, vals_list):
            if 'foreign_name' in vals and vals['foreign_name'] and record.product_id:
                self._sync_foreign_name_to_product(record.product_id, vals['foreign_name'])
        
        return records
    
    def write(self, vals):
        """Override write to sync foreign_name to product.product"""
        result = super().write(vals)
        
        # If foreign_name was updated, sync it to product.product
        if 'foreign_name' in vals:
            foreign_name_value = vals['foreign_name']
            for record in self:
                if record.product_id:
                    # Use the new value if provided, otherwise use the current value
                    sync_value = foreign_name_value if foreign_name_value else record.foreign_name
                    if sync_value:
                        self._sync_foreign_name_to_product(record.product_id, sync_value)

        # Keep the product's base UoM aligned with SAP once the extended mapping is known.
        if any(field_name in vals for field_name in ('sales_uom_id', 'inventory_uom_id', 'purchase_uom_id')):
            self._sync_product_uom_to_product()
        
        return result
    
    def _sync_foreign_name_to_product(self, product, foreign_name):
        """Sync foreign_name from sap.product.extended to product.product"""
        try:
            # Update product.template foreign_name (which will update product.product via related field)
            if product.product_tmpl_id:
                product.product_tmpl_id.write({'foreign_name': foreign_name})
                _logger.info(f"Synced foreign_name '{foreign_name}' from sap.product.extended to product {product.id}")
        except Exception as e:
            _logger.warning(f"Error syncing foreign_name to product.product: {e}")

    def _sync_product_uom_to_product(self):
        """Replace the generic Units UoM with SAP's mapped stock or sales UoM."""
        for record in self:
            try:
                product = record.product_id
                if not product or not product.product_tmpl_id or product.uom_id.id != 1:
                    continue

                target_uom = record.inventory_uom_id or record.sales_uom_id or record.purchase_uom_id
                if not target_uom or target_uom.id == 1:
                    continue

                product.product_tmpl_id.write({'uom_id': target_uom.id})
                _logger.info(
                    "Updated product %s base UoM from Units to %s based on SAP extended info",
                    product.default_code,
                    target_uom.name,
                )
            except Exception as sync_error:
                _logger.warning(
                    "Could not sync product base UoM for %s: %s",
                    record.product_id.default_code if record.product_id else 'unknown',
                    sync_error,
                )
    foreign_name_2 = fields.Char(
        string='Foreign Name 2',
        help="Additional foreign language name"
    )
    
    # ========== Unit of Measure Group from SAP ==========
    sap_uom_group_id = fields.Many2one(
        'sap.uom.group',
        string='SAP UoM Group',
        help="SAP Unit of Measure Group that this product belongs to. "
             "Defines which UoMs are allowed for this product."
    )
    sap_uom_group_entry = fields.Integer(
        string='SAP UoM Group Entry',
        help="SAP UoMGroupEntry number from SAP B1"
    )
    
    # ========== Unit of Measure Codes from SAP ==========
    sales_unit = fields.Char(
        string='Sales Unit (SAP)',
        help="SAP Sales Unit of Measure Code"
    )
    purchase_unit = fields.Char(
        string='Purchase Unit (SAP)',
        help="SAP Purchase Unit of Measure Code"
    )
    inventory_uom = fields.Char(
        string='Inventory UoM (SAP)',
        help="SAP Inventory Unit of Measure Code"
    )
    
    # ========== Mapped Odoo UoMs ==========
    sales_uom_id = fields.Many2one(
        'uom.uom',
        string='Sales UoM (Odoo)',
        help="Mapped Odoo UoM for sales"
    )
    purchase_uom_id = fields.Many2one(
        'uom.uom',
        string='Purchase UoM (Odoo)',
        help="Mapped Odoo UoM for purchases"
    )
    inventory_uom_id = fields.Many2one(
        'uom.uom',
        string='Inventory UoM (Odoo)',
        help="Mapped Odoo UoM for inventory"
    )
    
    # ========== Manufacturer Information ==========
    manufacturer_id = fields.Many2one(
        'res.partner',
        string='Manufacturer',
        domain=[('is_company', '=', True)]
    )
    manufacturer_catalog_no = fields.Char(
        string='Manufacturer Catalog #',
        help="Manufacturer's catalog number for this product"
    )
    
    # ========== Supplier Information ==========
    supplier_catalog_no = fields.Char(
        string='Supplier Catalog #',
        help="Supplier's catalog number for this product"
    )
    default_supplier_id = fields.Many2one(
        'res.partner',
        string='Default Supplier',
        domain=[('supplier_rank', '>', 0)]
    )
    
    # ========== Dimensions (Set 1) ==========
    length1 = fields.Float(
        string='Length 1',
        digits=(16, 4),
        help="Primary length dimension"
    )
    width1 = fields.Float(
        string='Width 1',
        digits=(16, 4),
        help="Primary width dimension"
    )
    height1 = fields.Float(
        string='Height 1',
        digits=(16, 4),
        help="Primary height dimension"
    )
    
    # ========== Dimensions (Set 2) ==========
    length2 = fields.Float(
        string='Length 2',
        digits=(16, 4),
        help="Alternative length dimension"
    )
    width2 = fields.Float(
        string='Width 2',
        digits=(16, 4),
        help="Alternative width dimension"
    )
    height2 = fields.Float(
        string='Height 2',
        digits=(16, 4),
        help="Alternative height dimension"
    )
    
    # ========== Units ==========
    dimension_unit_id = fields.Many2one(
        'uom.uom',
        string='Dimension Unit',
        help="Unit of measure for dimensions"
    )
    weight_unit_id = fields.Many2one(
        'uom.uom',
        string='Weight Unit',
        help="Unit of measure for weight"
    )
    volume_unit_id = fields.Many2one(
        'uom.uom',
        string='Volume Unit',
        help="Unit of measure for volume"
    )
    
    # ========== Inventory Management ==========
    manage_batch_numbers = fields.Boolean(
        string='Manage Batch Numbers',
        default=False,
        help="Track products by batch/lot numbers"
    )
    manage_serial_numbers = fields.Boolean(
        string='Manage Serial Numbers',
        default=False,
        help="Track products by unique serial numbers"
    )
    manage_stock_by_warehouse = fields.Boolean(
        string='Manage Stock by Warehouse',
        default=True,
        help="Track stock levels separately for each warehouse"
    )
    
    # ========== Stock Levels ==========
    min_level = fields.Float(
        string='Minimum Level',
        digits=(16, 4),
        help="Minimum stock level - triggers reorder"
    )
    max_level = fields.Float(
        string='Maximum Level',
        digits=(16, 4),
        help="Maximum stock level"
    )
    reorder_quantity = fields.Float(
        string='Reorder Quantity',
        digits=(16, 4),
        help="Quantity to order when minimum level is reached"
    )
    lead_time = fields.Integer(
        string='Lead Time (Days)',
        help="Number of days between order and delivery"
    )
    
    # ========== Default Warehouse ==========
    default_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Default Warehouse',
        help="Default warehouse for this product"
    )
    default_warehouse_code = fields.Char(
        string='Default Warehouse Code (SAP)',
        help="SAP warehouse code"
    )
    
    # ========== Item Types ==========
    purchase_item = fields.Boolean(
        string='Purchase Item',
        default=True,
        help="Item can be purchased"
    )
    sales_item = fields.Boolean(
        string='Sales Item',
        default=True,
        help="Item can be sold"
    )
    inventory_item = fields.Boolean(
        string='Inventory Item',
        default=True,
        help="Item is tracked in inventory"
    )
    
    # ========== Tax Information ==========
    tax_code_ar = fields.Char(
        string='Tax Code AR (Sales)',
        help="Tax code for sales (Accounts Receivable)"
    )
    tax_code_ap = fields.Char(
        string='Tax Code AP (Purchase)',
        help="Tax code for purchases (Accounts Payable)"
    )
    
    # ========== Commission & Customs ==========
    commission_group_code = fields.Integer(
        string='Commission Group',
        help="Commission group code from SAP"
    )
    commission_percent = fields.Float(
        string='Commission Percentage',
        digits=(5, 2),
        help="Commission percentage for sales"
    )
    customs_group_code = fields.Char(
        string='Customs Group Code',
        help="Customs classification code"
    )
    
    # ========== Shipping ==========
    ship_type = fields.Selection([
        ('item', 'By Item'),
        ('order', 'By Order'),
        ('row', 'By Row')
    ], string='Ship Type', default='item')
    
    # ========== Item Group Information ==========
    items_group_code = fields.Integer(
        string='Items Group Code',
        help="SAP items group code"
    )
    items_group_name = fields.Char(
        string='Items Group Name',
        help="SAP items group name"
    )
    
    # ========== Additional Information ==========
    user_text = fields.Text(
        string='User Text',
        help="Additional user text from SAP"
    )
    remarks = fields.Text(
        string='Remarks',
        help="Internal remarks"
    )

    # ========== SAP User-Defined Fields (U_ST_*) - Fragrance/Brand Info ==========
    main_brand = fields.Char(
        string='Main Brand (SAP raw)',
        help="SAP field U_ST_MainBrand raw text — linked brand is in brand_id"
    )
    brand_id = fields.Many2one(
        'product.brand',
        string='Brand',
        index=True,
        help="Brand linked from SAP U_ST_MainBrand"
    )
    eng_name = fields.Char(
        string='English Name',
        help="SAP field U_ST_EngName — English product name"
    )
    capacity = fields.Char(
        string='Capacity',
        help="SAP field U_ST_Capacity — e.g. 100ML, 200ML"
    )
    packaging = fields.Char(
        string='Packaging',
        help="SAP field U_ST_Packaging — packaging description"
    )
    country_origin = fields.Char(
        string='Country of Origin',
        help="SAP field U_ST_CountryOrigine"
    )
    fragrance_top_notes = fields.Text(
        string='Top Notes',
        help="SAP field U_ST_Starting — opening/top fragrance notes"
    )
    fragrance_middle_notes = fields.Text(
        string='Middle Notes (Heart)',
        help="SAP field U_ST_Inside — middle/heart fragrance notes"
    )
    fragrance_base_notes = fields.Text(
        string='Base Notes',
        help="SAP field U_ST_Base — base fragrance notes"
    )
    fragrance_description = fields.Text(
        string='Fragrance Description',
        help="SAP field U_ST_Lines — full fragrance description"
    )
    fragrantica_link = fields.Char(
        string='Fragrantica Link',
        help="SAP field U_ST_LINKS — link to Fragrantica page"
    )
    sap_classification_1 = fields.Char(
        string='Classification 1 (U_ST_IMD06)',
        help="SAP user-defined classification field IMD06"
    )
    sap_classification_2 = fields.Char(
        string='Classification 2 (U_ST_IMD07)',
        help="SAP user-defined classification field IMD07"
    )
    sap_classification_3 = fields.Char(
        string='Classification 3 (U_ST_IMD08)',
        help="SAP user-defined classification field IMD08"
    )
    sap_classification_4 = fields.Char(
        string='Classification 4 (U_ST_IMD12)',
        help="SAP user-defined classification field IMD12"
    )
    brand_id = fields.Many2one(
        'product.brand',
        string='Brand',
        index=True,
        help="Brand linked from SAP U_ST_MainBrand"
    )
    sap_category_id = fields.Many2one(
        'product.category',
        string='SAP Category',
        index=True,
        help="Odoo product.category linked from SAP ItemsGroupName"
    )
    
    # ========== SAP Specific Fields ==========
    sap_item_type = fields.Selection([
        ('itItems', 'Items'),
        ('itService', 'Service'),
        ('itLabor', 'Labor'),
        ('itTravel', 'Travel')
    ], string='SAP Item Type', default='itItems')
    
    valid_for_sale_from = fields.Date(
        string='Valid for Sale From',
        help="Start date for sales validity"
    )
    valid_for_sale_to = fields.Date(
        string='Valid for Sale To',
        help="End date for sales validity"
    )
    
    # ========== Sync Information ==========
    last_sync_date = fields.Datetime(
        string='Last Sync Date',
        readonly=True
    )
    sync_status = fields.Selection([
        ('synced', 'Synced'),
        ('pending', 'Pending'),
        ('error', 'Error')
    ], string='Sync Status', default='pending', readonly=True)
    sync_error_message = fields.Text(
        string='Sync Error',
        readonly=True
    )
    
    # ========== Computed Fields ==========
    total_volume = fields.Float(
        string='Total Volume',
        compute='_compute_total_volume',
        store=True,
        digits=(16, 6),
        help="Calculated volume (Length × Width × Height)"
    )
    
    # ========== Constraints ==========
    _sql_constraints = [
        ('unique_product_backend', 'UNIQUE(product_id, backend_id)',
         'Extended information already exists for this product and backend!'),
    ]
    
    # ========== Computed Methods ==========
    @api.depends('length1', 'width1', 'height1')
    def _compute_total_volume(self):
        """Calculate total volume from dimensions"""
        for record in self:
            if record.length1 and record.width1 and record.height1:
                record.total_volume = record.length1 * record.width1 * record.height1
            else:
                record.total_volume = 0.0
    
    # ========== CRUD Methods ==========
    @api.model
    def create_or_update_from_sap(self, product, backend, sap_data):
        """
        Create or update extended information from SAP data
        
        Args:
            product: product.product record
            backend: sap.backend record
            sap_data: Dictionary with SAP item data
            
        Returns:
            sap.product.extended record
        """
        try:
            # Search for existing record
            extended = self.search([
                ('product_id', '=', product.id),
                ('backend_id', '=', backend.id)
            ], limit=1)
            
            # Prepare values
            vals = self._prepare_extended_values_from_sap(sap_data, backend)
            vals.update({
                'product_id': product.id,
                'backend_id': backend.id,
                'last_sync_date': fields.Datetime.now(),
                'sync_status': 'synced'
            })
            
            if extended:
                # Update existing
                extended.write(vals)
                _logger.info(f"✏️ Updated extended info for: {product.name}")
            else:
                # Create new
                extended = self.create(vals)
                _logger.info(f"✅ Created extended info for: {product.name}")
                _logger.info(f"Created extended info for product: {product.name}")

            extended._sync_product_uom_to_product()
            
            return extended
            
        except Exception as e:
            _logger.error(f"Error creating/updating extended info: {str(e)}")
            # Try to update sync status
            if extended:
                extended.write({
                    'sync_status': 'error',
                    'sync_error_message': str(e)
                })
            raise
    
    def _prepare_extended_values_from_sap(self, sap_data, backend=None):
        """Prepare extended values from SAP data
        
        Args:
            sap_data: Dictionary with SAP data
            backend: sap.backend record (optional, for UoM Group linking)
        """
        vals = {}
        backend_id = backend.id if backend else False
        
        # Foreign names
        if 'ForeignName' in sap_data:
            vals['foreign_name'] = sap_data['ForeignName']
        
        # ========== UoM Codes from SAP ==========
        # UoM Group Entry - Link product to its UoM Group
        if 'UoMGroupEntry' in sap_data:
            uom_group_entry = sap_data['UoMGroupEntry']
            vals['sap_uom_group_entry'] = uom_group_entry
            
            # Try to find or create the UoM Group
            if uom_group_entry and uom_group_entry != -1 and backend:
                # Search for existing UoM Group by AbsEntry
                uom_group = self.env['sap.uom.group'].search([
                    ('sap_abs_entry', '=', uom_group_entry),
                    ('backend_id', '=', backend.id)
                ], limit=1)
                
                if uom_group:
                    vals['sap_uom_group_id'] = uom_group.id
                    _logger.info(f"Linked product to UoM Group: {uom_group.name} (Entry: {uom_group_entry})")
                else:
                    _logger.warning(f"UoM Group with Entry {uom_group_entry} not found - will be synced later")
        
        if 'SalesUnit' in sap_data:
            sales_unit_code = sap_data['SalesUnit']
            vals['sales_unit'] = sales_unit_code
            # Try to map to Odoo UoM
            uom_sync = self.env['sap.uom.sync'].search([
                ('backend_id', '=', backend_id),
                ('sap_uom_id', '=', sales_unit_code)
            ], limit=1)
            if uom_sync and uom_sync.odoo_uom_id:
                vals['sales_uom_id'] = uom_sync.odoo_uom_id.id
        
        if 'PurchaseUnit' in sap_data:
            purchase_unit_code = sap_data['PurchaseUnit']
            vals['purchase_unit'] = purchase_unit_code
            # Try to map to Odoo UoM
            uom_sync = self.env['sap.uom.sync'].search([
                ('backend_id', '=', backend_id),
                ('sap_uom_id', '=', purchase_unit_code)
            ], limit=1)
            if uom_sync and uom_sync.odoo_uom_id:
                vals['purchase_uom_id'] = uom_sync.odoo_uom_id.id
        
        inventory_uom_code = sap_data.get('InventoryUoM', sap_data.get('InventoryUOM'))
        if inventory_uom_code is not None:
            vals['inventory_uom'] = inventory_uom_code
            # Try to map to Odoo UoM
            uom_sync = self.env['sap.uom.sync'].search([
                ('backend_id', '=', backend_id),
                ('sap_uom_id', '=', inventory_uom_code)
            ], limit=1)
            if uom_sync and uom_sync.odoo_uom_id:
                vals['inventory_uom_id'] = uom_sync.odoo_uom_id.id
        
        # Manufacturer
        if 'ManufacturerCatalogNo' in sap_data:
            vals['manufacturer_catalog_no'] = sap_data['ManufacturerCatalogNo']
        
        # Supplier
        if 'SupplierCatalogNo' in sap_data:
            vals['supplier_catalog_no'] = sap_data['SupplierCatalogNo']
        
        # Dimensions (Set 1)
        if 'Length1' in sap_data:
            vals['length1'] = float(sap_data['Length1'] or 0)
        if 'Width1' in sap_data:
            vals['width1'] = float(sap_data['Width1'] or 0)
        if 'Height1' in sap_data:
            vals['height1'] = float(sap_data['Height1'] or 0)
        
        # Dimensions (Set 2)
        if 'Length2' in sap_data:
            vals['length2'] = float(sap_data['Length2'] or 0)
        if 'Width2' in sap_data:
            vals['width2'] = float(sap_data['Width2'] or 0)
        if 'Height2' in sap_data:
            vals['height2'] = float(sap_data['Height2'] or 0)
        
        # Inventory management
        if 'ManageBatchNumbers' in sap_data:
            vals['manage_batch_numbers'] = sap_data['ManageBatchNumbers'] == 'Y'
        if 'ManageSerialNumbers' in sap_data:
            vals['manage_serial_numbers'] = sap_data['ManageSerialNumbers'] == 'Y'
        if 'ManageStockByWarehouse' in sap_data:
            vals['manage_stock_by_warehouse'] = sap_data['ManageStockByWarehouse'] == 'Y'
        
        # Stock levels
        if 'MinLevel' in sap_data:
            vals['min_level'] = float(sap_data['MinLevel'] or 0)
        if 'MaxLevel' in sap_data:
            vals['max_level'] = float(sap_data['MaxLevel'] or 0)
        if 'ReorderQuantity' in sap_data:
            vals['reorder_quantity'] = float(sap_data['ReorderQuantity'] or 0)
        if 'LeadTime' in sap_data:
            vals['lead_time'] = int(sap_data['LeadTime'] or 0)
        
        # Default warehouse
        if 'DefaultWarehouseCode' in sap_data:
            vals['default_warehouse_code'] = sap_data['DefaultWarehouseCode']
        
        # Item types
        # Normalize SAP boolean-like flags to robust booleans
        def _to_bool_flag(value, default_true=True):
            if value is None or value == '':
                return bool(default_true)
            if isinstance(value, bool):
                return value
            v = str(value).strip().upper()
            return v in ('Y', 'YES', 'TYES', '1', 'TRUE')

        if 'PurchaseItem' in sap_data:
            vals['purchase_item'] = _to_bool_flag(sap_data['PurchaseItem'], default_true=True)
        if 'SalesItem' in sap_data:
            vals['sales_item'] = _to_bool_flag(sap_data['SalesItem'], default_true=True)
        if 'InventoryItem' in sap_data:
            vals['inventory_item'] = _to_bool_flag(sap_data['InventoryItem'], default_true=True)
        
        # Tax codes
        if 'TaxCodeAR' in sap_data:
            vals['tax_code_ar'] = sap_data['TaxCodeAR']
        if 'TaxCodeAP' in sap_data:
            vals['tax_code_ap'] = sap_data['TaxCodeAP']
        
        # Commission & Customs
        if 'CommissionGroup' in sap_data:
            vals['commission_group_code'] = int(sap_data['CommissionGroup'] or 0)
        if 'CommissionPercent' in sap_data:
            vals['commission_percent'] = float(sap_data['CommissionPercent'] or 0)
        if 'CustomsGroupCode' in sap_data:
            vals['customs_group_code'] = sap_data['CustomsGroupCode']
        
        # Ship type
        if 'ShipType' in sap_data:
            ship_type_map = {
                '0': 'item',
                '1': 'order',
                '2': 'row'
            }
            vals['ship_type'] = ship_type_map.get(str(sap_data['ShipType']), 'item')
        
        # Item group
        if 'ItemsGroupCode' in sap_data:
            vals['items_group_code'] = int(sap_data['ItemsGroupCode'] or 0)
        if 'ItemsGroupName' in sap_data:
            vals['items_group_name'] = sap_data['ItemsGroupName']
        
        # Additional info
        if 'UserText' in sap_data:
            vals['user_text'] = sap_data['UserText']
        if 'Remarks' in sap_data:
            vals['remarks'] = sap_data['Remarks']
        
        # Item type
        if 'ItemType' in sap_data:
            vals['sap_item_type'] = sap_data['ItemType']

        # ========== SAP User-Defined Fields (U_ST_*) ==========
        udf_mapping = {
            'U_ST_MainBrand': 'main_brand',
            'U_ST_EngName': 'eng_name',
            'U_ST_Capacity': 'capacity',
            'U_ST_Packaging': 'packaging',
            'U_ST_CountryOrigine': 'country_origin',
            'U_ST_Starting': 'fragrance_top_notes',
            'U_ST_Inside': 'fragrance_middle_notes',
            'U_ST_Base': 'fragrance_base_notes',
            'U_ST_Lines': 'fragrance_description',
            'U_ST_LINKS': 'fragrantica_link',
            'U_ST_IMD06': 'sap_classification_1',
            'U_ST_IMD07': 'sap_classification_2',
            'U_ST_IMD08': 'sap_classification_3',
            'U_ST_IMD12': 'sap_classification_4',
        }
        for sap_key, odoo_field in udf_mapping.items():
            if sap_key in sap_data and sap_data[sap_key]:
                vals[odoo_field] = sap_data[sap_key]

        # Auto-create/link Brand record from U_ST_MainBrand
        sap_brand_name = sap_data.get('U_ST_MainBrand', '').strip() if sap_data.get('U_ST_MainBrand') else ''
        if sap_brand_name:
            brand = self.env['product.brand'].get_or_create_by_sap_name(sap_brand_name)
            if brand:
                vals['brand_id'] = brand.id

        # Auto-create/link product.category from ItemsGroupCode + ItemsGroupName
        items_group_name = sap_data.get('ItemsGroupName', '').strip() if sap_data.get('ItemsGroupName') else ''
        items_group_code = sap_data.get('ItemsGroupCode')
        if items_group_name:
            category = self._get_or_create_product_category(items_group_name, items_group_code)
            if category:
                vals['sap_category_id'] = category.id

        return vals

    def _get_or_create_product_category(self, group_name, group_code=None):
        """
        Find or create a product.category matching the SAP ItemsGroup.
        Categories are placed under a parent 'SAP Groups' category.
        """
        try:
            # Ensure parent category exists
            parent = self.env['product.category'].search([
                ('name', '=', 'SAP Groups'),
                ('parent_id', '=', False),
            ], limit=1)
            if not parent:
                parent = self.env['product.category'].create({'name': 'SAP Groups'})

            # Search by name under the parent
            category = self.env['product.category'].search([
                ('name', '=', group_name),
                ('parent_id', '=', parent.id),
            ], limit=1)

            if not category:
                category = self.env['product.category'].create({
                    'name': group_name,
                    'parent_id': parent.id,
                })
                _logger.info("Created product.category '%s' from SAP group code %s", group_name, group_code)

            return category
        except Exception as e:
            _logger.warning("Could not create product.category for '%s': %s", group_name, e)
            return False
    
    # ========== Action Methods ==========
    def action_view_product(self):
        """Open the related product"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product',
            'res_model': 'product.product',
            'res_id': self.product_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_sync_from_sap(self):
        """Sync extended information from SAP"""
        self.ensure_one()
        try:
            # Get connection
            connection = self.backend_id.get_connection()
            
            # Get item data
            item_data = connection.get('Items', {
                '$filter': f"ItemCode eq '{self.sap_item_code}'"
            })
            
            if not item_data.get('value'):
                raise UserError(f"Item {self.sap_item_code} not found in SAP")
            
            sap_data = item_data['value'][0]
            
            # Update extended info
            self.create_or_update_from_sap(self.product_id, self.backend_id, sap_data)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success!',
                    'message': f'Extended information synced from SAP for {self.product_id.name}',
                    'type': 'success',
                }
            }
            
        except Exception as e:
            _logger.error(f"Error syncing extended info: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error!',
                    'message': f'Failed to sync: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }

