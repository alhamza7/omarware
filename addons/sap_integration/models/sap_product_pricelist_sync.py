# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Product Pricelist Sync

Sync SAP ItemPrices with Odoo Pricelists using native product.pricelist system.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class SapProductPricelistSync(models.Model):
    """Sync SAP ItemPrices with Odoo Pricelists"""
    _name = 'sap.product.pricelist.sync'
    _description = 'SAP Product Pricelist Synchronization'
    _order = 'product_id, sap_pricelist_num'
    
    # ========== Relations ==========
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
    
    # ========== SAP Pricelist Data ==========
    sap_pricelist_num = fields.Integer(
        string='SAP Price List Number',
        required=True,
        index=True,
        help="SAP price list number (e.g., 1, 2, 3)"
    )
    sap_pricelist_name = fields.Char(
        string='SAP Price List Name',
        help="Name of the price list in SAP"
    )
    
    # ========== Odoo Pricelist Mapping ==========
    odoo_pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Odoo Pricelist',
        required=True,
        ondelete='restrict',
        index=True,
        help="Mapped Odoo pricelist"
    )
    odoo_pricelist_item_id = fields.Many2one(
        'product.pricelist.item',
        string='Pricelist Item',
        ondelete='set null',
        help="Specific pricelist item rule in Odoo"
    )
    
    # ========== Price Details ==========
    price = fields.Float(
        string='Price',
        required=True,
        digits='Product Price',
        help="Price from SAP"
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help="Price currency"
    )
    
    # ========== UoM Specific Pricing ==========
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        help="Specific UoM for this price (if applicable)"
    )
    uom_code = fields.Char(
        string='SAP UoM Code',
        help="SAP UoM code for this price"
    )
    
    # ========== Additional SAP Fields ==========
    base_num = fields.Integer(
        string='Base Number',
        help="SAP BaseNum field"
    )
    factor = fields.Float(
        string='Factor',
        default=1.0,
        digits=(16, 6),
        help="Conversion factor from SAP"
    )
    
    # ========== Validity Period ==========
    date_start = fields.Date(
        string='Valid From',
        help="Price validity start date"
    )
    date_end = fields.Date(
        string='Valid To',
        help="Price validity end date"
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
    ], string='Sync Status', default='pending', readonly=True, index=True)
    
    sync_error_message = fields.Text(
        string='Sync Error',
        readonly=True
    )
    
    # ========== Computed Fields ==========
    product_name = fields.Char(
        string='Product Name',
        related='product_id.name',
        readonly=True
    )
    product_code = fields.Char(
        string='Product Code',
        related='product_id.default_code',
        store=True
    )
    
    # ========== Constraints ==========
    _sql_constraints = [
        ('unique_product_pricelist_uom', 'UNIQUE(product_id, backend_id, sap_pricelist_num, uom_id)',
         'A price already exists for this product, pricelist, and UoM!'),
    ]
    
    # ========== CRUD Methods ==========
    @api.model
    def sync_product_prices_from_sap(self, product, backend, sap_prices_data):
        """
        Sync all prices for a product from SAP ItemPrices
        
        Args:
            product: product.product record
            backend: sap.backend record
            sap_prices_data: List of SAP ItemPrices data
            
        Returns:
            Dictionary with sync results
        """
        try:
            results = {
                'total': 0,
                'created': 0,
                'updated': 0,
                'errors': 0,
                'error_messages': []
            }
            
            for price_data in sap_prices_data:
                try:
                    results['total'] += 1
                    
                    # Extract price information
                    pricelist_num = int(price_data.get('PriceList', 0))
                    
                    # Handle None price - skip if price is None
                    price_value = price_data.get('Price')
                    if price_value is None or price_value == '':
                        _logger.warning(f"Skipping price for {product.name} in pricelist {pricelist_num}: Price is None")
                        continue
                    
                    price = float(price_value)
                    currency_code = price_data.get('Currency', self.env.company.currency_id.name)
                    uom_code = price_data.get('UoMCode', '')
                    
                    # Get or create Odoo pricelist
                    odoo_pricelist = self._get_or_create_pricelist(
                        backend, pricelist_num, currency_code
                    )
                    
                    # Get UoM if specified
                    uom = None
                    if uom_code:
                        uom = self._get_uom_by_code(uom_code)
                    
                    # Search for existing sync record
                    sync_record = self.search([
                        ('product_id', '=', product.id),
                        ('backend_id', '=', backend.id),
                        ('sap_pricelist_num', '=', pricelist_num),
                        ('uom_id', '=', uom.id if uom else False)
                    ], limit=1)
                    
                    # Prepare values
                    vals = self._prepare_sync_values(
                        product, backend, odoo_pricelist, price_data, uom
                    )
                    
                    if sync_record:
                        # Update existing
                        sync_record.write(vals)
                        results['updated'] += 1
                        _logger.info(f"Updated price for {product.name} in pricelist {pricelist_num}")
                    else:
                        # Create new
                        sync_record = self.create(vals)
                        results['created'] += 1
                        _logger.info(f"Created price for {product.name} in pricelist {pricelist_num}")
                    
                    # Create or update pricelist item in Odoo
                    self._create_or_update_pricelist_item(sync_record, product, odoo_pricelist, price, uom)
                    
                    # ========== NEW: Process UoM-specific prices ==========
                    uom_prices = price_data.get('UoMPrices', [])
                    if uom_prices:
                        _logger.info(f"Processing {len(uom_prices)} UoM-specific prices for {product.name}")
                        for uom_price_data in uom_prices:
                            try:
                                # Get UoM entry
                                uom_entry = uom_price_data.get('UoMEntry')
                                uom_price_value = uom_price_data.get('Price')
                                
                                if not uom_price_value or uom_entry is None:
                                    continue
                                
                                # Find UoM by SAP UoMEntry (ID in SAP)
                                uom_sync = self.env['sap.uom.sync'].search([
                                    ('backend_id', '=', backend.id),
                                    ('sap_uom_entry', '=', uom_entry)
                                ], limit=1)
                                
                                if not uom_sync or not uom_sync.odoo_uom_id:
                                    _logger.warning(f"UoM Entry {uom_entry} not found in sync, skipping")
                                    continue
                                
                                # ========== AUTO-LINK UoM to Group from Product Data ==========
                                self._auto_link_uom_to_group(uom_sync, uom_price_data, product, backend)
                                
                                uom_specific = uom_sync.odoo_uom_id
                                uom_price = float(uom_price_value)
                                
                                # Search for existing UoM-specific price
                                uom_sync_record = self.search([
                                    ('product_id', '=', product.id),
                                    ('backend_id', '=', backend.id),
                                    ('sap_pricelist_num', '=', pricelist_num),
                                    ('uom_id', '=', uom_specific.id)
                                ], limit=1)
                                
                                # Prepare UoM-specific values
                                uom_vals = self._prepare_sync_values(
                                    product, backend, odoo_pricelist, uom_price_data, uom_specific
                                )
                                uom_vals['price'] = uom_price  # Override with UoM-specific price
                                
                                if uom_sync_record:
                                    uom_sync_record.write(uom_vals)
                                    results['updated'] += 1
                                else:
                                    uom_sync_record = self.create(uom_vals)
                                    results['created'] += 1
                                
                                # Create pricelist item for this UoM
                                self._create_or_update_pricelist_item(
                                    uom_sync_record, product, odoo_pricelist, uom_price, uom_specific
                                )
                                
                            except Exception as uom_error:
                                _logger.error(f"Error processing UoM price: {str(uom_error)}")
                    
                except Exception as e:
                    results['errors'] += 1
                    error_msg = f"Error syncing price {price_data}: {str(e)}"
                    results['error_messages'].append(error_msg)
                    _logger.error(error_msg)
            
            _logger.info(f"Price sync completed for {product.name}: {results}")
            return results
            
        except Exception as e:
            _logger.error(f"Error syncing product prices: {str(e)}")
            raise
    
    def _prepare_sync_values(self, product, backend, odoo_pricelist, price_data, uom=None):
        """Prepare values for sync record"""
        currency = self.env['res.currency'].search([
            ('name', '=', price_data.get('Currency', self.env.company.currency_id.name))
        ], limit=1)
        
        if not currency:
            currency = self.env.company.currency_id
        
        # Handle None price safely
        price_value = price_data.get('Price', 0.0)
        price = 0.0 if price_value is None else float(price_value)
        
        return {
            'product_id': product.id,
            'backend_id': backend.id,
            'sap_pricelist_num': int(price_data.get('PriceList', 0)),
            'sap_pricelist_name': price_data.get('PriceListName', f"Price List {price_data.get('PriceList')}"),
            'odoo_pricelist_id': odoo_pricelist.id,
            'price': price,
            'currency_id': currency.id,
            'uom_id': uom.id if uom else False,
            'uom_code': price_data.get('UoMCode', ''),
            'base_num': int(price_data.get('BaseNum', 0)),
            'factor': float(price_data.get('Factor', 1.0)),
            'last_sync_date': fields.Datetime.now(),
            'sync_status': 'synced',
            'sync_error_message': False,
        }
    
    def _get_or_create_pricelist(self, backend, pricelist_num, currency_code):
        """Get or create Odoo pricelist"""
        # Search for existing pricelist with this number
        pricelist_name = f"SAP Price List {pricelist_num}"
        
        # Get currency
        currency = self.env['res.currency'].search([
            ('name', '=', currency_code)
        ], limit=1)
        
        if not currency:
            currency = self.env.company.currency_id
        
        # Search for pricelist
        pricelist = self.env['product.pricelist'].search([
            ('name', '=', pricelist_name),
            ('currency_id', '=', currency.id)
        ], limit=1)
        
        if not pricelist:
            # Create new pricelist
            pricelist = self.env['product.pricelist'].create({
                'name': pricelist_name,
                'currency_id': currency.id,
                'active': True,
                'company_id': self.env.company.id,
            })
            _logger.info(f"Created new pricelist: {pricelist_name}")
        
        return pricelist
    
    def _get_uom_by_code(self, uom_code):
        """Get UoM by SAP code"""
        if not uom_code:
            return None
        
        # Try to find in sap.uom.sync
        uom_sync = self.env['sap.uom.sync'].search([
            ('sap_uom_id', '=', uom_code)
        ], limit=1)
        
        if uom_sync and uom_sync.odoo_uom_id:
            return uom_sync.odoo_uom_id
        
        # Try to find directly in uom.uom
        uom = self.env['uom.uom'].search([
            ('name', '=', uom_code)
        ], limit=1)
        
        return uom
    
    def _create_or_update_pricelist_item(self, sync_record, product, pricelist, price, uom=None):
        """Create or update product.pricelist.item in Odoo"""
        try:
            # Search for existing pricelist item
            # Use product_tmpl_id instead of product_id for template-level pricing
            domain = [
                ('pricelist_id', '=', pricelist.id),
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('applied_on', '=', '1_product'),
            ]
            
            # Add UoM to domain if specified
            if uom:
                domain.append(('product_packaging_id', '=', uom.id))
            else:
                domain.append(('product_packaging_id', '=', False))
            
            pricelist_item = self.env['product.pricelist.item'].search(domain, limit=1)
            
            # Prepare values - use product_tmpl_id for template-level pricing
            item_vals = {
                'pricelist_id': pricelist.id,
                'product_tmpl_id': product.product_tmpl_id.id,
                'applied_on': '1_product',  # Apply to product template, not variant
                'compute_price': 'fixed',
                'fixed_price': price,
                'min_quantity': 1,
            }
            
            # Add UoM/packaging if specified
            if uom:
                item_vals['product_packaging_id'] = uom.id
                _logger.info(f"Adding UoM {uom.name} to pricelist item")
            
            # Add date validity if present
            if sync_record.date_start:
                item_vals['date_start'] = sync_record.date_start
            if sync_record.date_end:
                item_vals['date_end'] = sync_record.date_end
            
            if pricelist_item:
                # Update existing
                pricelist_item.write(item_vals)
                _logger.info(f"Updated pricelist item for {product.name}")
            else:
                # Create new
                pricelist_item = self.env['product.pricelist.item'].create(item_vals)
                _logger.info(f"Created pricelist item for {product.name}")
            
            # Link back to sync record
            sync_record.write({
                'odoo_pricelist_item_id': pricelist_item.id
            })
            
            return pricelist_item
            
        except Exception as e:
            _logger.error(f"Error creating/updating pricelist item: {str(e)}")
            sync_record.write({
                'sync_status': 'error',
                'sync_error_message': str(e)
            })
            raise
    
    @api.model
    def import_all_pricelists_from_sap(self, backend, batch_size=100):
        """
        Import all pricelists from SAP for all products
        
        Args:
            backend: sap.backend record or ID
            batch_size: Number of products to process per batch
            
        Returns:
            Dictionary with import results
        """
        try:
            # Support both backend ID (int) and backend object
            if isinstance(backend, int):
                backend = self.env['sap.backend'].browse(backend)
            
            _logger.info(f"Importing all pricelists from SAP backend {backend.name}")
            
            connection = backend.get_connection()
            if not connection:
                raise UserError("Could not establish connection to SAP backend")
            
            results = {
                'total_products': 0,
                'successful_products': 0,
                'failed_products': 0,
                'total_prices': 0,
                'created_prices': 0,
                'updated_prices': 0,
                'errors': []
            }
            
            # Get all items with their prices
            skip = 0
            has_more = True
            
            while has_more:
                # Fetch batch WITHOUT expand (SAP doesn't support it)
                params = {
                    '$top': batch_size,
                    '$skip': skip,
                    '$orderby': 'ItemCode'
                }
                
                items_data = connection.get('Items', params)
                batch = items_data.get('value', [])
                
                if not batch:
                    has_more = False
                    break
                
                _logger.info(f"Processing batch: {skip + 1} to {skip + len(batch)}")
                
                # Process each item
                for item_data in batch:
                    try:
                        results['total_products'] += 1
                        
                        item_code = item_data.get('ItemCode')
                        
                        # Fetch prices AND UoM Group info from Items endpoint
                        try:
                            # SAP returns ItemPrices with UoMPrices ONLY when we don't use $select!
                            # We must fetch the full item to get ItemPrices with nested UoMPrices
                            price_params = {
                                '$filter': f"ItemCode eq '{item_code}'"
                            }
                            item_with_prices = connection.get('Items', price_params)
                            items_value = item_with_prices.get('value', [])
                            
                            if items_value:
                                full_item_data = items_value[0]
                                item_prices = full_item_data.get('ItemPrices', [])
                                
                                _logger.info(f"Fetched {len(item_prices)} price lists for {item_code}")
                            else:
                                full_item_data = {}
                                item_prices = []
                        except Exception as price_error:
                            _logger.warning(f"Could not fetch prices for {item_code}: {str(price_error)}")
                            full_item_data = {}
                            item_prices = []
                        
                        if not item_prices:
                            _logger.info(f"No prices found for item {item_code}, skipping")
                            continue
                        
                        # Find product in Odoo
                        product = self.env['product.product'].search([
                            ('default_code', '=', item_code)
                        ], limit=1)
                        
                        if not product:
                            _logger.warning(f"Product {item_code} not found in Odoo, skipping prices")
                            results['failed_products'] += 1
                            continue
                        
                        # ========== AUTO-LINK: Link product's UoMs to Group ==========
                        if full_item_data:
                            self.link_product_uoms_to_group(product, full_item_data, backend)
                        
                        # Sync prices for this product
                        price_result = self.sync_product_prices_from_sap(
                            product, backend, item_prices
                        )
                        
                        results['total_prices'] += price_result['total']
                        results['created_prices'] += price_result['created']
                        results['updated_prices'] += price_result['updated']
                        
                        if price_result['errors'] > 0:
                            results['errors'].extend(price_result['error_messages'])
                            results['failed_products'] += 1
                        else:
                            results['successful_products'] += 1
                        
                    except Exception as e:
                        results['failed_products'] += 1
                        error_msg = f"Error processing item {item_code}: {str(e)}"
                        results['errors'].append(error_msg)
                        _logger.error(error_msg)
                
                skip += len(batch)
            
            _logger.info(f"Pricelist import completed: {results}")
            return results
            
        except Exception as e:
            _logger.error(f"Error importing all pricelists: {str(e)}")
            raise
    
    # ========== Action Methods ==========
    def action_view_pricelist(self):
        """Open the related Odoo pricelist"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pricelist',
            'res_model': 'product.pricelist',
            'res_id': self.odoo_pricelist_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_pricelist_item(self):
        """Open the related pricelist item"""
        self.ensure_one()
        if not self.odoo_pricelist_item_id:
            raise UserError("No pricelist item linked yet!")
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pricelist Item',
            'res_model': 'product.pricelist.item',
            'res_id': self.odoo_pricelist_item_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_sync_from_sap(self):
        """Re-sync this price from SAP"""
        self.ensure_one()
        try:
            connection = self.backend_id.get_connection()
            
            # Get item prices
            params = {
                '$filter': f"ItemCode eq '{self.product_id.default_code}'",
                '$expand': 'ItemPrices'
            }
            items_data = connection.get('Items', params)
            
            if not items_data.get('value'):
                raise UserError(f"Item {self.product_id.default_code} not found in SAP")
            
            item_prices = items_data['value'][0].get('ItemPrices', [])
            
            # Find matching price
            matching_price = None
            for price_data in item_prices:
                if int(price_data.get('PriceList', 0)) == self.sap_pricelist_num:
                    matching_price = price_data
                    break
            
            if not matching_price:
                raise UserError(f"Price not found in SAP for pricelist {self.sap_pricelist_num}")
            
            # Re-sync
            result = self.sync_product_prices_from_sap(
                self.product_id, self.backend_id, [matching_price]
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success!',
                    'message': f'Price synced from SAP: {result}',
                    'type': 'success',
                }
            }
            
        except Exception as e:
            _logger.error(f"Error syncing price: {str(e)}")
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
    
    def _auto_link_uom_to_group(self, uom_sync, uom_price_data, product, backend):
        """
        Automatically link UoM to its Group and calculate conversion factors
        from product UoMPrices data
        
        This is the SMART solution that extracts relationships from actual product data!
        """
        try:
            # Get conversion data from UoMPrices
            base_quantity = float(uom_price_data.get('BaseQuantity', 1.0))
            alternate_quantity = float(uom_price_data.get('AlternateQuantity', 1.0))
            uom_code = uom_price_data.get('UoMCode', '')
            
            # Calculate conversion factor
            # In SAP: base_quantity (base UoM) = alternate_quantity (this UoM)
            # In Odoo: factor = how many base units in 1 of this unit
            # Example: 1 Box = 12 Pieces ΓåÆ factor = 12.0
            factor = base_quantity / alternate_quantity if alternate_quantity != 0 else 1.0
            
            _logger.info(f"Γ£ô UoM {uom_code}: {alternate_quantity} = {base_quantity} base (factor = {factor:.4f})")
            
            # Try to get UoMGroupEntry from product if available
            # This will be added when we have access to full product data
            product_sap_data = getattr(product, 'sap_data', None)
            if product_sap_data:
                try:
                    import json
                    sap_dict = json.loads(product_sap_data) if isinstance(product_sap_data, str) else product_sap_data
                    uom_group_entry = sap_dict.get('UoMGroupEntry')
                    
                    if uom_group_entry:
                        # Find the group with this AbsEntry
                        group = self.env['sap.uom.group'].search([
                            ('sap_abs_entry', '=', uom_group_entry),
                            ('backend_id', '=', backend.id)
                        ], limit=1)
                        
                        if group and group.id not in uom_sync.sap_group_ids.ids:
                            uom_sync.write({
                                'sap_group_ids': [(4, group.id)]  # Add to Many2many
                            })
                            _logger.info(f"Γ£ô Linked UoM {uom_code} to Group {group.name}")
                except Exception as e:
                    _logger.debug(f"Could not extract UoMGroupEntry: {str(e)}")
            
            # Update UoM factor if different from 1.0
            if uom_sync.odoo_uom_id and abs(factor - 1.0) > 0.001:
                try:
                    # Try to update the factor
                    # Important: In Odoo 19, we need to be careful with UoMs already in use
                    current_factor = uom_sync.odoo_uom_id.factor
                    
                    if abs(current_factor - factor) > 0.001:
                        # Only update if factor actually changed
                        uom_sync.odoo_uom_id.sudo().write({'factor': factor})
                        _logger.info(f"Γ£ô Updated {uom_sync.odoo_uom_id.name} factor: {current_factor} ΓåÆ {factor}")
                except Exception as e:
                    _logger.warning(f"Cannot update UoM factor for {uom_sync.odoo_uom_id.name}: {str(e)}")
                    # This is expected if UoM is already used in products/stock
                    # We'll handle this differently later
            
            return True
            
        except Exception as e:
            _logger.error(f"Error auto-linking UoM to group: {str(e)}")
            return False
    
    @api.model
    def link_product_uoms_to_group(self, product, product_sap_data, backend):
        """
        Link all product UoMs to their SAP Group based on product's UoMGroupEntry
        
        Call this when importing a product with full SAP data
        """
        try:
            uom_group_entry = product_sap_data.get('UoMGroupEntry')
            if not uom_group_entry:
                return False
            
            # Find the group
            group = self.env['sap.uom.group'].search([
                ('sap_abs_entry', '=', uom_group_entry),
                ('backend_id', '=', backend.id)
            ], limit=1)
            
            if not group:
                _logger.warning(f"Group with AbsEntry {uom_group_entry} not found")
                return False
            
            # Get all UoM entries used by this product from ItemPrices
            item_prices = product_sap_data.get('ItemPrices', [])
            uom_entries_found = set()
            
            for price_data in item_prices:
                uom_prices = price_data.get('UoMPrices', [])
                for uom_price in uom_prices:
                    uom_entry = uom_price.get('UoMEntry')
                    if uom_entry:
                        uom_entries_found.add(uom_entry)
            
            # Also add main UoM entries
            for field in ['InventoryUoMEntry', 'SalesUoMEntry', 'PurchaseUoMEntry']:
                entry = product_sap_data.get(field)
                if entry:
                    uom_entries_found.add(entry)
            
            _logger.info(f"Product {product.default_code}: Found {len(uom_entries_found)} UoM entries, linking to Group {group.name}")
            
            # Link all these UoMs to the group
            linked_count = 0
            for uom_entry in uom_entries_found:
                uom_sync = self.env['sap.uom.sync'].search([
                    ('sap_uom_entry', '=', uom_entry),
                    ('backend_id', '=', backend.id)
                ], limit=1)
                
                if uom_sync and group.id not in uom_sync.sap_group_ids.ids:
                    uom_sync.write({
                        'sap_group_ids': [(4, group.id)]  # Add to Many2many
                    })
                    linked_count += 1
            
            if linked_count > 0:
                _logger.info(f"Γ£ô Linked {linked_count} UoMs to Group {group.name}")
            
            return True
            
        except Exception as e:
            _logger.error(f"Error linking product UoMs to group: {str(e)}")
            return False
    
    @api.model
    def sync_product_prices_for_item(self, backend, item_code):
        """
        Sync prices for a single item by ItemCode
        Useful for testing and manual syncing
        """
        try:
            # Support both backend ID (int) and backend object
            if isinstance(backend, int):
                backend = self.env['sap.backend'].browse(backend)
            
            connection = backend.get_connection()
            if not connection:
                raise UserError("Could not establish connection to SAP backend")
            
            # Get full item data
            params = {
                '$filter': f"ItemCode eq '{item_code}'",
                '$select': 'ItemCode,ItemPrices,UoMGroupEntry,InventoryUoMEntry'
            }
            items_data = connection.get('Items', params)
            items = items_data.get('value', [])
            
            if not items:
                raise UserError(f"Item {item_code} not found in SAP")
            
            full_item_data = items[0]
            item_prices = full_item_data.get('ItemPrices', [])
            
            # Find product in Odoo
            product = self.env['product.product'].search([
                ('default_code', '=', item_code)
            ], limit=1)
            
            if not product:
                raise UserError(f"Product {item_code} not found in Odoo")
            
            # Link UoMs to Group
            if full_item_data:
                self.link_product_uoms_to_group(product, full_item_data, backend)
            
            # Sync prices
            if item_prices:
                result = self.sync_product_prices_from_sap(product, backend, item_prices)
                return result
            else:
                return {'total': 0, 'created': 0, 'updated': 0, 'errors': 0}
                
        except Exception as e:
            _logger.error(f"Error syncing prices for item {item_code}: {str(e)}")
            raise






