# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Product Complete Migration

Complete migration wizard for importing all product-related data from SAP to Odoo.
This includes:
- UoM Groups with conversion factors
- Products with all fields
- Pricelists with UoM-specific pricing
- Warehouse information with stock levels
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class SapProductCompleteMigration(models.TransientModel):
    """Complete Product Migration from SAP"""
    _name = 'sap.product.complete.migration'
    _description = 'Complete Product Migration from SAP'
    
    # ========== Configuration ==========
    backend_id = fields.Many2one(
        'sap.backend',
        string='SAP Backend',
        required=True,
        default=lambda self: self.env['sap.backend'].search([('active', '=', True)], limit=1)
    )
    
    # ========== Migration Options ==========
    stage1_uom_groups = fields.Boolean(
        string='Stage 1: Import UoM Groups',
        default=True,
        help="Import Unit of Measure Groups with conversion factors (e.g., 1kg = 1000g)"
    )
    stage2_products = fields.Boolean(
        string='Stage 2: Import Products',
        default=True,
        help="Import products with basic and extended information"
    )
    stage3_pricelists = fields.Boolean(
        string='Stage 3: Import Pricelists',
        default=True,
        help="Import pricelists with UoM-specific pricing"
    )
    stage4_warehouse_info = fields.Boolean(
        string='Stage 4: Import Warehouse Info',
        default=True,
        help="Import warehouse information and stock levels"
    )
    
    # ========== Advanced Options ==========
    product_limit = fields.Integer(
        string='Product Limit',
        default=0,
        help="Maximum number of products to import (0 = unlimited). Example: 10 for testing"
    )
    batch_size = fields.Integer(
        string='Batch Size',
        default=100,
        help="Number of records to process per batch"
    )
    update_existing = fields.Boolean(
        string='Update Existing Records',
        default=True,
        help="Update existing records or skip them"
    )
    skip_errors = fields.Boolean(
        string='Skip Errors and Continue',
        default=True,
        help="Continue migration even if some records fail"
    )
    
    # ========== State ==========
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('error', 'Error')
    ], string='State', default='draft', readonly=True)
    
    # ========== Progress Tracking ==========
    progress_percentage = fields.Float(
        string='Progress (%)',
        readonly=True,
        default=0.0,
        help="Overall migration progress percentage"
    )
    current_stage = fields.Char(
        string='Current Stage',
        readonly=True,
        help="Current migration stage being processed"
    )
    current_batch = fields.Integer(
        string='Current Batch',
        readonly=True,
        default=0,
        help="Current batch number being processed"
    )
    total_batches = fields.Integer(
        string='Total Batches',
        readonly=True,
        default=0,
        help="Total number of batches to process"
    )
    
    # ========== Results ==========
    migration_log = fields.Text(
        string='Migration Log',
        readonly=True,
        help="Detailed log of the migration process"
    )
    
    start_time = fields.Datetime(string='Start Time', readonly=True)
    end_time = fields.Datetime(string='End Time', readonly=True)
    duration_seconds = fields.Integer(string='Duration (seconds)', readonly=True, compute='_compute_duration')
    
    # Statistics
    total_uom_groups = fields.Integer(string='UoM Groups', readonly=True)
    total_products = fields.Integer(string='Products Imported', readonly=True)
    total_pricelists = fields.Integer(string='Pricelists Created', readonly=True)
    total_prices = fields.Integer(string='Price Records', readonly=True)
    total_warehouses = fields.Integer(string='Warehouse Records', readonly=True)
    
    errors_count = fields.Integer(string='Errors', readonly=True)
    errors_log = fields.Text(
        string='Errors Log',
        readonly=True,
        help="Detailed log of errors encountered"
    )
    
    # ========== Computed ==========
    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for record in self:
            if record.start_time and record.end_time:
                delta = record.end_time - record.start_time
                record.duration_seconds = int(delta.total_seconds())
            else:
                record.duration_seconds = 0
    
    # ========== Progress Update Helper ==========
    def _update_progress(self, percentage, stage, batch=0, total_batches=0, log_msg=None):
        """Update progress and log"""
        vals = {
            'progress_percentage': percentage,
            'current_stage': stage,
            'current_batch': batch,
            'total_batches': total_batches,
        }
        
        if log_msg:
            current_log = self.migration_log or ''
            vals['migration_log'] = current_log + '\n' + log_msg
        
        self.write(vals)
        self.env.cr.commit()
        
        # Send notification to UI
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'sap_migration_progress',
            {
                'wizard_id': self.id,
                'progress': percentage,
                'stage': stage,
                'batch': batch,
                'total_batches': total_batches,
            }
        )
    
    def _log_error(self, error_msg, exception=None):
        """Log error to errors_log"""
        current_errors = self.errors_log or ''
        timestamp = fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        error_entry = f"\n[{timestamp}] {error_msg}"
        if exception:
            import traceback
            error_entry += f"\nTraceback: {traceback.format_exc()}"
        
        self.write({
            'errors_log': current_errors + error_entry,
            'errors_count': self.errors_count + 1
        })
        self.env.cr.commit()
    
    # ========== Main Migration Method ==========
    def run_complete_migration(self):
        """Run the complete migration process"""
        self.ensure_one()
        
        try:
            # Initialize
            self.write({
                'state': 'running',
                'start_time': fields.Datetime.now(),
                'migration_log': '',
                'errors_log': '',
                'progress_percentage': 0.0,
                'current_stage': 'Initializing...',
            })
            self.env.cr.commit()  # حفظ الحالة فوراً
            
            log = []
            log.append("=" * 80)
            log.append(f"SAP Product Complete Migration Started")
            log.append(f"Backend: {self.backend_id.name}")
            log.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            log.append(f"Batch Size: {self.batch_size}")
            log.append("=" * 80)
            log.append("")
            
            # عرض في الـ wizard فوراً
            self.write({'migration_log': "\n".join(log)})
            self.env.cr.commit()
            
            # Stage 1: UoM Groups
            if self.stage1_uom_groups:
                log.append("\n" + "=" * 80)
                log.append("STAGE 1: UoM Groups Migration")
                log.append("=" * 80)
                self._update_progress(10, 'Stage 1: UoM Groups', 0, 1, "\n".join(log))
                
                try:
                    stage1_result = self._stage1_import_uom_groups()
                    log.extend(stage1_result['log'])
                    self.total_uom_groups = stage1_result.get('imported', 0)
                    log.append(f"\n✅ Stage 1 Complete: {self.total_uom_groups} UoM groups imported")
                    
                    self.write({
                        'migration_log': "\n".join(log),
                        'total_uom_groups': self.total_uom_groups
                    })
                    self._update_progress(25, 'Stage 1: Completed', 1, 1)
                except Exception as e:
                    error_msg = f"❌ Stage 1 Error: {str(e)}"
                    log.append(error_msg)
                    self._log_error(error_msg, e)
                    _logger.error(f"Stage 1 failed: {str(e)}", exc_info=True)
                    if not self.skip_errors:
                        raise
                
                self.env.cr.commit()
            
            # Stage 2: Products
            if self.stage2_products:
                log.append("\n\n" + "=" * 80)
                log.append("STAGE 2: Products Migration")
                log.append("=" * 80)
                self._update_progress(30, 'Stage 2: Products', 0, 0, "\n".join(log))
                
                try:
                    stage2_result = self._stage2_import_products()
                    log.extend(stage2_result['log'])
                    self.total_products = stage2_result.get('imported', 0)
                    log.append(f"\n✅ Stage 2 Complete: {self.total_products} products imported")
                    
                    self.write({
                        'migration_log': "\n".join(log),
                        'total_products': self.total_products
                    })
                    self._update_progress(60, 'Stage 2: Completed')
                except Exception as e:
                    error_msg = f"❌ Stage 2 Error: {str(e)}"
                    log.append(error_msg)
                    self._log_error(error_msg, e)
                    _logger.error(f"Stage 2 failed: {str(e)}", exc_info=True)
                    if not self.skip_errors:
                        raise
                
                self.env.cr.commit()
            
            # Stage 3: Pricelists
            if self.stage3_pricelists:
                log.append("\n\n" + "=" * 80)
                log.append("STAGE 3: Pricelists Migration")
                log.append("=" * 80)
                self._update_progress(65, 'Stage 3: Pricelists', 0, 0, "\n".join(log))
                
                try:
                    stage3_result = self._stage3_import_pricelists()
                    log.extend(stage3_result['log'])
                    self.total_pricelists = stage3_result.get('pricelists', 0)
                    self.total_prices = stage3_result.get('prices', 0)
                    log.append(f"\n✅ Stage 3 Complete: {self.total_pricelists} pricelists, {self.total_prices} price records")
                    self._update_progress(80, 'Stage 3: Completed')
                except Exception as e:
                    error_msg = f"❌ Stage 3 Error: {str(e)}"
                    log.append(error_msg)
                    self._log_error(error_msg, e)
                    _logger.error(f"Stage 3 failed: {str(e)}", exc_info=True)
                    if not self.skip_errors:
                        raise
            
            # Stage 4: Warehouse Info
            if self.stage4_warehouse_info:
                log.append("\n\n" + "=" * 80)
                log.append("STAGE 4: Warehouse Information Migration")
                log.append("=" * 80)
                self._update_progress(85, 'Stage 4: Warehouse Info', 0, 0, "\n".join(log))
                
                try:
                    stage4_result = self._stage4_import_warehouse_info()
                    log.extend(stage4_result['log'])
                    self.total_warehouses = stage4_result.get('warehouses', 0)
                    log.append(f"\n✅ Stage 4 Complete: {self.total_warehouses} warehouse records")
                    self._update_progress(95, 'Stage 4: Completed')
                except Exception as e:
                    error_msg = f"❌ Stage 4 Error: {str(e)}"
                    log.append(error_msg)
                    self._log_error(error_msg, e)
                    _logger.error(f"Stage 4 failed: {str(e)}", exc_info=True)
                    if not self.skip_errors:
                        raise
            
            # Final Report
            log.append("\n\n" + "=" * 80)
            log.append("MIGRATION COMPLETE! ✅")
            log.append("=" * 80)
            log.append(f"UoM Groups Imported: {self.total_uom_groups}")
            log.append(f"Products Imported: {self.total_products}")
            log.append(f"Pricelists Created: {self.total_pricelists}")
            log.append(f"Price Records: {self.total_prices}")
            log.append(f"Warehouse Records: {self.total_warehouses}")
            log.append(f"Errors: {self.errors_count}")
            log.append("=" * 80)
            
            # Update state
            self.write({
                'state': 'done',
                'end_time': fields.Datetime.now(),
                'migration_log': "\n".join(log),
                'progress_percentage': 100.0,
                'current_stage': 'Completed ✅',
            })
            
            # Show notification
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Migration Complete! ✅',
                    'message': f'Successfully imported {self.total_products} products with all data',
                    'type': 'success',
                    'sticky': True,
                }
            }
            
        except Exception as e:
            error_msg = f"Migration failed: {str(e)}"
            _logger.error(error_msg, exc_info=True)
            
            self.write({
                'state': 'error',
                'end_time': fields.Datetime.now(),
                'migration_log': self.migration_log + f"\n\n❌ ERROR: {error_msg}"
            })
            
            raise UserError(error_msg)
    
    # ========== Stage 1: UoM Groups ==========
    def _stage1_import_uom_groups(self):
        """Stage 1: Import UoM Groups from SAP"""
        log = []
        try:
            log.append("🔄 Starting UoM Groups import...")
            log.append(f"Backend: {self.backend_id.name}")
            log.append("")
            
            # Update wizard log in real-time
            self.write({'migration_log': "\n".join(log)})
            self.env.cr.commit()
            
            # Import UoM Groups
            log.append("Connecting to SAP...")
            self.write({'migration_log': "\n".join(log)})
            self.env.cr.commit()
            
            uom_sync = self.env['sap.uom.sync']
            result = uom_sync.import_all_uoms_from_sap(self.backend_id)
            
            log.append(f"✓ Imported {result} UoMs from SAP")
            
            # Get some examples
            recent_uoms = self.env['sap.uom.sync'].search([
                ('backend_id', '=', self.backend_id.id),
                ('sync_status', '=', 'success')
            ], order='last_sync desc', limit=5)
            
            if recent_uoms:
                log.append("")
                log.append("Sample UoMs:")
                for uom in recent_uoms:
                    try:
                        log.append(f"  - {uom.sap_uom_id} -> {uom.odoo_uom_id.name}")
                    except:
                        log.append(f"  - {uom.sap_uom_id} -> Error")
            
            # Final update
            self.write({'migration_log': "\n".join(log)})
            self.env.cr.commit()
            
            return {
                'success': True,
                'imported': result,
                'log': log
            }
            
        except Exception as e:
            log.append(f"❌ Error: {str(e)}")
            self.write({'migration_log': "\n".join(log)})
            self.env.cr.commit()
            _logger.error(f"Stage 1 error: {str(e)}", exc_info=True)
            if not self.skip_errors:
                raise
            return {'success': False, 'imported': 0, 'log': log}
    
    # ========== Stage 2: Products ==========
    def _stage2_import_products(self):
        """Stage 2: Import Products with Extended Info"""
        log = []
        try:
            log.append("🔄 Starting Products import...")
            log.append(f"Batch size: {self.batch_size}")
            if self.product_limit > 0:
                log.append(f"Product limit: {self.product_limit} products")
            else:
                log.append("Product limit: Unlimited")
            log.append("")
            
            # Update wizard display
            self.write({'migration_log': "\n".join(log)})
            self.env.cr.commit()
            
            connection = self.backend_id.get_connection()
            
            # Import with $expand to get all data at once
            skip = 0
            total_imported = 0
            total_errors = 0
            batch_number = 0
            
            while True:
                # Check if we reached the product limit
                if self.product_limit > 0 and total_imported >= self.product_limit:
                    log.append(f"✓ Reached product limit ({self.product_limit}), stopping import")
                    break
                
                # Adjust batch size if approaching limit
                current_batch_size = self.batch_size
                if self.product_limit > 0:
                    remaining = self.product_limit - total_imported
                    current_batch_size = min(self.batch_size, remaining)
                
                params = {
                    '$top': current_batch_size,
                    '$skip': skip,
                    '$orderby': 'ItemCode'
                }
                
                log.append(f"📥 Fetching batch from SAP (skip={skip})...")
                self.write({'migration_log': "\n".join(log)})
                self.env.cr.commit()
                
                items_data = connection.get('Items', params)
                batch = items_data.get('value', [])
                
                if not batch:
                    log.append("✓ No more products to fetch")
                    break
                
                batch_number += 1
                log.append(f"")
                log.append(f"📦 Batch {batch_number}: Processing {len(batch)} products (from {skip + 1} to {skip + len(batch)})")
                
                # Calculate progress within Stage 2 (30% to 60%)
                # Estimate total batches if not known
                if not self.total_batches:
                    # Rough estimate based on current batch and items
                    estimated_total = max(batch_number + 10, 75)
                    self.total_batches = estimated_total
                
                batch_progress = 30 + ((batch_number / max(self.total_batches, 1)) * 30)
                self._update_progress(
                    min(batch_progress, 59),  # Cap at 59% to reserve 60% for completion
                    f'Stage 2: Batch {batch_number}/{self.total_batches}',
                    batch_number,
                    self.total_batches,
                    "\n".join(log)
                )
                
                for item_data in batch:
                    item_code = None
                    try:
                        item_code = item_data.get('ItemCode')
                        item_name = item_data.get('ItemName', item_code)
                        
                        # Skip if no item code
                        if not item_code:
                            continue
                        
                        # Import basic product
                        product = self._import_single_product(item_data)
                        
                        if not product:
                            _logger.warning(f"Product {item_code} could not be created/found")
                            total_errors += 1
                            continue
                        
                        # Import extended info (in separate try/catch to isolate errors)
                        try:
                            extended = self.env['sap.product.extended'].create_or_update_from_sap(
                                product, self.backend_id, item_data
                            )
                            total_imported += 1
                            
                            # Update progress every 5 products
                            if total_imported % 5 == 0:
                                log.append(f"  ✓ Progress: {total_imported} products imported, {total_errors} errors")
                                self.write({
                                    'migration_log': "\n".join(log),
                                    'total_products': total_imported,
                                    'errors_count': total_errors,
                                })
                                self.env.cr.commit()
                                
                        except Exception as ext_error:
                            error_msg = f"❌ Error creating extended info for {item_code}: {str(ext_error)[:100]}"
                            _logger.error(error_msg)
                            log.append(f"  {error_msg}")
                            try:
                                self._log_error(error_msg, ext_error)
                            except:
                                pass  # Don't fail if logging fails
                            total_errors += 1
                            # Continue with next product - don't rollback
                            if not self.skip_errors:
                                raise
                        
                    except Exception as e:
                        error_msg = f"❌ Error importing product {item_code}: {str(e)[:100]}"
                        _logger.error(error_msg)
                        log.append(f"  {error_msg}")
                        try:
                            self._log_error(error_msg, e)
                        except:
                            pass  # Don't fail if logging fails
                        total_errors += 1
                        # Continue with next product - commit what we have and continue
                        try:
                            self.env.cr.commit()  # Save progress so far
                        except:
                            pass  # If commit fails, just continue
                        if not self.skip_errors:
                            raise
                
                skip += len(batch)
                
                # Update progress after each batch
                log.append(f"  ✓ Batch {batch_number} complete: {len(batch)} items processed")
                log.append(f"  📊 Total so far: {total_imported} imported, {total_errors} errors")
                self.write({
                    'migration_log': "\n".join(log),
                    'total_products': total_imported,
                    'errors_count': total_errors,
                })
                self.env.cr.commit()
            
            # Final summary
            log.append(f"")
            log.append(f"✅ Stage 2 Complete!")
            log.append(f"  Total Imported: {total_imported} products")
            if total_errors > 0:
                log.append(f"  Errors: {total_errors}")
            
            self.write({
                'migration_log': "\n".join(log),
                'total_products': total_imported,
                'errors_count': total_errors,
            })
            self.env.cr.commit()
            
            self.errors_count += total_errors
            
            return {
                'success': True,
                'imported': total_imported,
                'errors': total_errors,
                'log': log
            }
            
        except Exception as e:
            log.append(f"❌ Error: {str(e)}")
            _logger.error(f"Stage 2 error: {str(e)}", exc_info=True)
            if not self.skip_errors:
                raise
            return {'success': False, 'imported': 0, 'log': log}
    
    def _import_single_product(self, item_data):
        """Import or update a single product with all SAP fields"""
        item_code = item_data.get('ItemCode')
        
        # Validate required fields
        item_name = (item_data.get('ItemName') or '').strip()
        foreign_name = (item_data.get('ForeignName') or '').strip()
        
        # Use ForeignName if ItemName is empty
        if not item_name and foreign_name:
            item_name = foreign_name
        elif not item_name:
            item_name = f"Product {item_code}"
            _logger.warning(f"Item {item_code} has no name, using: {item_name}")
        
        # Search for existing
        product = self.env['product.product'].search([
            ('default_code', '=', item_code)
        ], limit=1)
        
        # ========== Get and Map UoMs ==========
        sales_unit = item_data.get('SalesUnit')
        purchase_unit = item_data.get('PurchaseUnit')
        inventory_uom = item_data.get('InventoryUoM')
        
        # Map to Odoo UoMs
        sales_uom_id = self._map_sap_uom_to_odoo(sales_unit) if sales_unit else None
        purchase_uom_id = self._map_sap_uom_to_odoo(purchase_unit) if purchase_unit else None
        inventory_uom_id = self._map_sap_uom_to_odoo(inventory_uom) if inventory_uom else None
        
        # Use sales UoM as default, fallback to inventory or purchase
        default_uom_id = sales_uom_id or inventory_uom_id or purchase_uom_id
        
        # ========== Prepare basic values ==========
        is_active = item_data.get('Frozen', 'tNO') != 'tYES'
        is_sales_item = item_data.get('SalesItem', 'Y') == 'Y'
        is_purchase_item = item_data.get('PurchaseItem', 'Y') == 'Y'
        
        # Handle prices safely (in case they are None)
        sales_price = item_data.get('SalesUnitPrice', 0) or 0
        purchase_price = item_data.get('PurchaseUnitPrice', 0) or 0
        
        vals = {
            'name': item_name,
            'default_code': item_code,
            'list_price': float(sales_price),  # سعر البيع من SAP
            'standard_price': float(purchase_price),  # سعر الشراء من SAP
            'type': 'consu',  # Consumable = Storable products (displayed as "Goods" in UI)
            'tracking': 'none',  # Enable inventory tracking
            'is_storable': True,  # Enable "Track Inventory" checkbox in UI
            'active': is_active,
            # If product is active, make it available for sale and POS
            'sale_ok': is_active and is_sales_item,
            'purchase_ok': is_active and is_purchase_item,
            'available_in_pos': is_active and is_sales_item,  # Add to POS if active
        }
        
        # ========== Add UoMs ==========
        if default_uom_id:
            vals['uom_id'] = default_uom_id
        # Note: uom_po_id removed in Odoo 19.0
        # Purchase UoM is now handled through product supplier info
        
        # ========== Add optional fields ==========
        if item_data.get('BarCode'):
            vals['barcode'] = item_data['BarCode']
        
        if item_data.get('Weight'):
            try:
                vals['weight'] = float(item_data['Weight'])
            except (ValueError, TypeError):
                pass
        
        if item_data.get('Volume'):
            try:
                vals['volume'] = float(item_data['Volume'])
            except (ValueError, TypeError):
                pass
        
        # Description fields
        if item_data.get('UserText'):
            vals['description'] = item_data['UserText']
        if item_data.get('Remarks'):
            vals['description_sale'] = item_data['Remarks']
        
        # Create or update product
        if product and self.update_existing:
            product.write(vals)
        elif not product:
            product = self.env['product.product'].create(vals)
        
        return product
    
    def _map_sap_uom_to_odoo(self, sap_uom_code):
        """Map SAP UoM code to Odoo UoM ID"""
        if not sap_uom_code:
            return None
        
        # Search for existing mapping
        uom_sync = self.env['sap.uom.sync'].search([
            ('backend_id', '=', self.backend_id.id),
            ('sap_uom_id', '=', sap_uom_code)
        ], limit=1)
        
        if uom_sync and uom_sync.odoo_uom_id:
            return uom_sync.odoo_uom_id.id
        
        # Fallback: search by name
        uom = self.env['uom.uom'].search([
            ('name', '=ilike', sap_uom_code)
        ], limit=1)
        
        return uom.id if uom else None
    
    # ========== Stage 3: Pricelists ==========
    def _stage3_import_pricelists(self):
        """Stage 3: Import Pricelists"""
        log = []
        try:
            log.append("Starting Pricelists import...")
            log.append("")
            
            # Import all pricelists
            pricelist_sync = self.env['sap.product.pricelist.sync']
            result = pricelist_sync.import_all_pricelists_from_sap(
                self.backend_id, self.batch_size
            )
            
            log.append(f"✓ Processed {result['total_products']} products")
            log.append(f"✓ Created/updated {result['created_prices']} price records")
            log.append(f"✓ Successful: {result['successful_products']} products")
            
            if result['failed_products'] > 0:
                log.append(f"⚠ Failed: {result['failed_products']} products")
            
            # Count pricelists created
            pricelists = self.env['product.pricelist'].search([
                ('name', 'like', 'SAP Price List')
            ])
            
            self.errors_count += result['failed_products']
            
            return {
                'success': True,
                'pricelists': len(pricelists),
                'prices': result['created_prices'],
                'log': log
            }
            
        except Exception as e:
            log.append(f"❌ Error: {str(e)}")
            _logger.error(f"Stage 3 error: {str(e)}", exc_info=True)
            if not self.skip_errors:
                raise
            return {'success': False, 'pricelists': 0, 'prices': 0, 'log': log}
    
    # ========== Stage 4: Warehouse Info ==========
    def _stage4_import_warehouse_info(self):
        """Stage 4: Import Warehouse Information"""
        log = []
        try:
            log.append("Starting Warehouse Info import...")
            log.append("")
            
            # Import all warehouse info
            warehouse_info = self.env['sap.product.warehouse.info']
            result = warehouse_info.import_all_warehouse_info_from_sap(
                self.backend_id, self.batch_size
            )
            
            log.append(f"✓ Processed {result['total_products']} products")
            log.append(f"✓ Created/updated {result['created_records']} warehouse records")
            log.append(f"✓ Stock updated in Odoo for products")
            log.append(f"✓ Reorder rules created where applicable")
            
            if result['failed_products'] > 0:
                log.append(f"⚠ Failed: {result['failed_products']} products")
            
            self.errors_count += result['failed_products']
            
            return {
                'success': True,
                'warehouses': result['created_records'],
                'log': log
            }
            
        except Exception as e:
            log.append(f"❌ Error: {str(e)}")
            _logger.error(f"Stage 4 error: {str(e)}", exc_info=True)
            if not self.skip_errors:
                raise
            return {'success': False, 'warehouses': 0, 'log': log}
    
    # ========== Actions ==========
    def action_view_imported_products(self):
        """View imported products"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Imported Products',
            'res_model': 'product.product',
            'view_mode': 'list,form',
            'domain': [('default_code', '!=', False)],
            'context': {'create': False}
        }
    
    def action_view_pricelists(self):
        """View created pricelists"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'SAP Pricelists',
            'res_model': 'product.pricelist',
            'view_mode': 'list,form',
            'domain': [('name', 'like', 'SAP Price List')],
        }
    
    def action_view_extended_info(self):
        """View extended product info"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Extended Product Info',
            'res_model': 'sap.product.extended',
            'view_mode': 'list,form',
            'domain': [('backend_id', '=', self.backend_id.id)],
        }

