# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SapAutoSync(models.Model):
    """SAP Automatic Synchronization"""
    _name = 'sap.auto.sync'
    _description = 'SAP Automatic Synchronization'

    name = fields.Char(string='Name', required=True, default='SAP Auto Sync')
    backend_id = fields.Many2one('sap.backend', string='SAP Backend', required=True)
    active = fields.Boolean(string='Active', default=True)
    
    # Sync Options
    sync_products = fields.Boolean(string='Sync Products', default=True)
    sync_pricelists = fields.Boolean(string='Sync Pricelists', default=True)
    sync_warehouse = fields.Boolean(string='Sync Warehouse Info', default=False)
    sync_uom_groups = fields.Boolean(string='Sync UoM Groups', default=False)
    sync_commercial_flags = fields.Boolean(
        string='Sync Sales/Purchase/POS flags (cron)',
        default=True,
        help="When enabled, the scheduled job updates active, sale_ok, purchase_ok, "
             "and available_in_pos from SAP Items (Valid, Frozen, SalesItem, PurchaseItem)."
    )
    force_enable_sales_pos = fields.Boolean(
        string='Force Sales & POS for all active items',
        default=False,
        help="If set, ignores SAP SalesItem for sale_ok/POS during auto-sync and flag sync."
    )
    deactivate_odoo_not_in_sap = fields.Boolean(
        string='Deactivate Odoo-only products (cron)',
        default=False,
        help="When commercial flags sync runs: also archive templates whose default_code is not "
             "an SAP ItemCode. Dangerous for local-only products; leave off unless Odoo must mirror SAP only.",
    )

    # Batch Settings
    batch_size = fields.Integer(string='Batch Size', default=100)
    product_limit = fields.Integer(string='Product Limit', default=0, help="0 = No limit")
    
    # Last Sync Info
    last_sync_date = fields.Datetime(string='Last Sync Date', readonly=True)
    last_sync_status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('running', 'Running')
    ], string='Last Sync Status', readonly=True)
    last_sync_log = fields.Text(string='Last Sync Log', readonly=True)
    
    # Statistics
    total_synced = fields.Integer(string='Total Products Synced', readonly=True)
    total_errors = fields.Integer(string='Total Errors', readonly=True)

    @api.model
    def run_daily_sync(self):
        """Run daily synchronization for all active sync configurations"""
        _logger.info("=" * 80)
        _logger.info("🔄 Starting SAP Daily Auto-Sync")
        _logger.info("=" * 80)
        
        sync_configs = self.search([('active', '=', True)])
        
        if not sync_configs:
            _logger.warning("⚠️ No active SAP auto-sync configurations found!")
            return
        
        for config in sync_configs:
            _logger.info(f"\n🔄 Processing sync config: {config.name}")
            config.execute_sync()
        
        _logger.info("=" * 80)
        _logger.info("✅ SAP Daily Auto-Sync Completed")
        _logger.info("=" * 80)

    @api.model
    def run_commercial_flags_sync(self):
        """Cron: refresh Odoo product flags from SAP Items for each active config."""
        configs = self.search([('active', '=', True), ('sync_commercial_flags', '=', True)])
        if not configs:
            _logger.info("SAP commercial flags cron: no active configs with sync_commercial_flags.")
            return
        Migration = self.env['sap.product.complete.migration']
        for config in configs:
            try:
                wiz = Migration.create({
                    'backend_id': config.backend_id.id,
                    'batch_size': max(config.batch_size, 1),
                    'product_limit': config.product_limit,
                    'force_enable_sales_pos': config.force_enable_sales_pos,
                    'deactivate_odoo_not_in_sap': config.deactivate_odoo_not_in_sap,
                })
                res = wiz.sync_commercial_flags_from_sap()
                _logger.info(
                    "SAP commercial flags [%s]: updated=%s not_in_odoo=%s errors=%s deactivated=%s",
                    config.name,
                    res.get('updated'),
                    res.get('not_in_odoo'),
                    res.get('errors'),
                    res.get('deactivated_not_in_sap'),
                )
            except Exception:
                _logger.exception(
                    "SAP commercial flags cron failed for config %s", config.name
                )
            finally:
                self.env.cr.commit()

    def execute_sync(self):
        """Execute synchronization for this configuration"""
        self.ensure_one()
        
        _logger.info(f"🔄 Starting sync for: {self.name}")
        _logger.info(f"Backend: {self.backend_id.name}")
        
        # Mark as running
        self.write({
            'last_sync_status': 'running',
            'last_sync_date': fields.Datetime.now()
        })
        self.env.cr.commit()
        
        log_lines = []
        total_synced = 0
        total_errors = 0
        
        try:
            # Stage 1: UoM Groups (if enabled)
            if self.sync_uom_groups:
                _logger.info("📦 Syncing UoM Groups...")
                log_lines.append("=" * 50)
                log_lines.append("Stage 1: UoM Groups")
                log_lines.append("=" * 50)
                try:
                    uom_model = self.env['sap.uom.group']
                    result = uom_model.import_uom_groups_from_sap(self.backend_id)
                    log_lines.append(f"✅ UoM Groups: {result.get('created', 0)} created, {result.get('updated', 0)} updated")
                except Exception as e:
                    error_msg = f"❌ UoM Groups Error: {str(e)}"
                    log_lines.append(error_msg)
                    _logger.error(error_msg, exc_info=True)
                    total_errors += 1
            
            # Stage 2: Products (if enabled)
            if self.sync_products:
                _logger.info("📦 Syncing Products...")
                log_lines.append("\n" + "=" * 50)
                log_lines.append("Stage 2: Products")
                log_lines.append("=" * 50)
                try:
                    # Use the wizard model but in auto mode
                    wizard = self.env['sap.product.complete.migration'].create({
                        'backend_id': self.backend_id.id,
                        'batch_size': self.batch_size,
                        'product_limit': self.product_limit,
                        'stage1_uom_groups': False,
                        'stage2_products': True,
                        'stage3_pricelists': False,
                        'stage4_warehouse_info': False,
                        'force_enable_sales_pos': self.force_enable_sales_pos,
                    })
                    
                    # Run stages
                    wizard._stage2_import_products()
                    
                    total_synced += wizard.total_products
                    total_errors += wizard.errors_count
                    
                    log_lines.append(f"✅ Products: {wizard.total_products} synced")
                    if wizard.errors_count > 0:
                        log_lines.append(f"⚠️ Errors: {wizard.errors_count}")
                        
                except Exception as e:
                    error_msg = f"❌ Products Error: {str(e)}"
                    log_lines.append(error_msg)
                    _logger.error(error_msg, exc_info=True)
                    total_errors += 1
            
            # Stage 3: Pricelists (if enabled)
            if self.sync_pricelists:
                _logger.info("💰 Syncing Pricelists...")
                log_lines.append("\n" + "=" * 50)
                log_lines.append("Stage 3: Pricelists")
                log_lines.append("=" * 50)
                try:
                    pricelist_sync = self.env['sap.product.pricelist.sync']
                    result = pricelist_sync.import_all_pricelists_from_sap(
                        self.backend_id,
                        batch_size=self.batch_size
                    )
                    log_lines.append(f"✅ Pricelists: {result.get('pricelists_created', 0)} created")
                    log_lines.append(f"✅ Price Items: {result.get('items_created', 0)} created, {result.get('items_updated', 0)} updated")
                except Exception as e:
                    error_msg = f"❌ Pricelists Error: {str(e)}"
                    log_lines.append(error_msg)
                    _logger.error(error_msg, exc_info=True)
                    total_errors += 1
            
            # Stage 4: Warehouse Info (if enabled)
            if self.sync_warehouse:
                _logger.info("🏭 Syncing Warehouse Info...")
                log_lines.append("\n" + "=" * 50)
                log_lines.append("Stage 4: Warehouse Info")
                log_lines.append("=" * 50)
                try:
                    warehouse_info = self.env['sap.product.warehouse.info']
                    result = warehouse_info.import_all_warehouse_info_from_sap(
                        self.backend_id,
                        batch_size=self.batch_size
                    )
                    log_lines.append(f"✅ Warehouse Records: {result.get('created', 0)} created, {result.get('updated', 0)} updated")
                except Exception as e:
                    error_msg = f"❌ Warehouse Error: {str(e)}"
                    log_lines.append(error_msg)
                    _logger.error(error_msg, exc_info=True)
                    total_errors += 1
            
            # Success
            log_lines.append("\n" + "=" * 50)
            log_lines.append("✅ Sync Completed Successfully!")
            log_lines.append("=" * 50)
            log_lines.append(f"Total Synced: {total_synced}")
            log_lines.append(f"Total Errors: {total_errors}")
            log_lines.append(f"Time: {fields.Datetime.now()}")
            
            self.write({
                'last_sync_status': 'success',
                'last_sync_log': '\n'.join(log_lines),
                'total_synced': self.total_synced + total_synced,
                'total_errors': self.total_errors + total_errors
            })
            
            _logger.info(f"✅ Sync completed for: {self.name}")
            
        except Exception as e:
            # Failed
            error_msg = f"❌ Sync failed: {str(e)}"
            log_lines.append("\n" + "=" * 50)
            log_lines.append(error_msg)
            log_lines.append("=" * 50)
            
            self.write({
                'last_sync_status': 'failed',
                'last_sync_log': '\n'.join(log_lines),
                'total_errors': self.total_errors + 1
            })
            
            _logger.error(f"❌ Sync failed for: {self.name}", exc_info=True)
        
        finally:
            self.env.cr.commit()

    def action_manual_sync(self):
        """Manual sync button"""
        self.ensure_one()
        self.execute_sync()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'SAP Sync',
                'message': f'Sync completed! Status: {self.last_sync_status}',
                'type': 'success' if self.last_sync_status == 'success' else 'warning',
                'sticky': False,
            }
        }

