# -*- coding: utf-8 -*-
"""
SAP Realtime Sync — Fast Delta Synchronization

Polls SAP every 2 minutes for changed items (prices, stock, product data)
using the UpdateDate/UpdateTime OData filter so only changed records are fetched.
Each run stores the last-sync timestamp per entity to minimize SAP load.
"""

from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

# How many seconds to subtract from last-sync time as an overlap buffer
# to avoid missing records due to clock skew between Odoo and SAP servers
OVERLAP_SECONDS = 30


class SapRealtimeSync(models.Model):
    """Tracks the last successful fast-poll timestamp per entity per backend"""
    _name = 'sap.realtime.sync'
    _description = 'SAP Realtime Fast-Poll Sync'
    _order = 'backend_id, entity_type'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    backend_id = fields.Many2one(
        'sap.backend',
        string='SAP Backend',
        required=True,
        ondelete='cascade',
        index=True,
    )
    entity_type = fields.Selection([
        ('prices', 'Prices (ItemPrices)'),
        ('stock', 'Stock (Warehouse Info)'),
        ('products', 'Product Data'),
        ('customers', 'Customers (BusinessPartners)'),
        ('all', 'All (Prices + Stock + Products + Customers + Barcodes)'),
    ], string='Entity Type', required=True, default='all')
    active = fields.Boolean(default=True)
    # When enabled, items that exist in SAP but not yet in Odoo will be created automatically
    auto_create_products = fields.Boolean(
        string='Auto-Create New Products',
        default=True,
        help='If enabled, items added to SAP that do not exist in Odoo will be created automatically.',
    )
    auto_create_customers = fields.Boolean(
        string='Auto-Create New Customers',
        default=True,
        help='If enabled, BusinessPartners added to SAP that do not exist in Odoo will be created as res.partner.',
    )

    # Populated after each successful run
    last_sync_at = fields.Datetime(string='Last Sync At', readonly=True)
    last_sync_status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('running', 'Running'),
    ], string='Last Status', readonly=True)
    last_sync_log = fields.Text(string='Last Run Log', readonly=True)
    last_items_changed = fields.Integer(string='Items Changed (Last Run)', readonly=True, default=0)
    total_runs = fields.Integer(string='Total Runs', readonly=True, default=0)
    total_errors = fields.Integer(string='Total Errors', readonly=True, default=0)

    _sql_constraints = [
        ('unique_backend_entity', 'unique(backend_id, entity_type)',
         'There can only be one realtime sync config per backend and entity type.'),
    ]

    @api.depends('backend_id', 'entity_type')
    def _compute_name(self):
        """Build a human-readable name from backend + entity."""
        for rec in self:
            backend_name = rec.backend_id.name if rec.backend_id else 'N/A'
            entity_label = dict(rec._fields['entity_type'].selection).get(rec.entity_type, '')
            rec.name = f'{backend_name} — {entity_label}'

    # ------------------------------------------------------------------
    # Cron entry points
    # ------------------------------------------------------------------

    @api.model
    def cron_run_fast_sync(self):
        """
        Called by the 2-minute cron job.
        Iterates all active realtime sync configs and runs delta sync for each.
        """
        configs = self.search([('active', '=', True)])
        if not configs:
            _logger.debug('SAP Realtime Sync: no active configs, skipping.')
            return

        for config in configs:
            try:
                config._run_delta_sync()
            except Exception as exc:
                _logger.error(
                    'SAP Realtime Sync: unhandled error for config %s: %s',
                    config.name, exc, exc_info=True,
                )

    # ------------------------------------------------------------------
    # Manual trigger (button)
    # ------------------------------------------------------------------

    def action_run_now(self):
        """Manual sync button — runs delta sync immediately."""
        self.ensure_one()
        self._run_delta_sync()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'SAP Realtime Sync',
                'message': f'Sync finished — status: {self.last_sync_status}',
                'type': 'success' if self.last_sync_status == 'success' else 'warning',
                'sticky': False,
            },
        }

    def action_reset_timestamp(self):
        """
        Reset last_sync_at so the next run will fetch all items from the past 24h.
        Useful after an outage to re-sync missed changes.
        """
        self.ensure_one()
        self.write({'last_sync_at': False})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Timestamp Reset',
                'message': 'Next run will re-sync changes from the last 24 hours.',
                'type': 'info',
                'sticky': False,
            },
        }

    # ------------------------------------------------------------------
    # Core delta sync logic
    # ------------------------------------------------------------------

    def _run_delta_sync(self):
        """
        Main delta sync entry point.
        Fetches only SAP items changed since last_sync_at using UpdateDate/UpdateTime.
        """
        self.ensure_one()
        backend = self.backend_id

        # Mark as running
        self.write({'last_sync_status': 'running'})
        self.env.cr.commit()

        log_lines = []
        items_changed = 0

        try:
            connection = backend.get_connection()
            since_dt = self._get_since_datetime()
            log_lines.append(f'Delta sync from: {since_dt.strftime("%Y-%m-%d %H:%M:%S")}')

            entity_type = self.entity_type
            changed_items = []
            if entity_type in ('prices', 'stock', 'products', 'all'):
                changed_items = self._fetch_changed_items(connection, since_dt)
                log_lines.append(f'Changed items found in SAP: {len(changed_items)}')

            changed_partners = []
            if entity_type in ('customers', 'all'):
                changed_partners = self._fetch_changed_business_partners(connection, since_dt)
                log_lines.append(f'Changed BusinessPartners found in SAP: {len(changed_partners)}')

            if changed_items:
                if entity_type in ('products', 'all'):
                    updated, created = self._sync_product_data(backend, changed_items)
                    items_changed += updated + created
                    log_lines.append(f'  Products updated: {updated}')
                    if created:
                        log_lines.append(f'  Products created (new from SAP): {created}')

                if entity_type in ('prices', 'all'):
                    count = self._sync_prices(backend, changed_items)
                    items_changed += count
                    log_lines.append(f'  Price records updated: {count}')

                if entity_type in ('stock', 'all'):
                    count = self._sync_stock(backend, changed_items)
                    items_changed += count
                    log_lines.append(f'  Stock records updated: {count}')

                if entity_type in ('all',):
                    count = self._sync_barcodes(backend, changed_items)
                    items_changed += count
                    if count:
                        log_lines.append(f'  Alternative barcodes updated: {count}')

            if changed_partners:
                updated_p, created_p = self._sync_customers(backend, changed_partners)
                items_changed += updated_p + created_p
                log_lines.append(f'  Customers updated: {updated_p}')
                if created_p:
                    log_lines.append(f'  Customers created (new from SAP): {created_p}')

            self.write({
                'last_sync_status': 'success',
                'last_sync_at': fields.Datetime.now(),
                'last_sync_log': '\n'.join(log_lines),
                'last_items_changed': items_changed,
                'total_runs': self.total_runs + 1,
            })
            _logger.info('SAP Realtime Sync [%s]: %d items updated.', self.name, items_changed)

        except Exception as exc:
            log_lines.append(f'ERROR: {exc}')
            self.write({
                'last_sync_status': 'failed',
                'last_sync_log': '\n'.join(log_lines),
                'total_runs': self.total_runs + 1,
                'total_errors': self.total_errors + 1,
            })
            _logger.error(
                'SAP Realtime Sync [%s] failed: %s', self.name, exc, exc_info=True,
            )
        finally:
            self.env.cr.commit()

    def _get_since_datetime(self):
        """
        Returns the datetime from which to look for changes.
        Falls back to 24 hours ago on first run, and applies an overlap buffer
        to avoid missing records due to clock skew.
        """
        if self.last_sync_at:
            since = self.last_sync_at - timedelta(seconds=OVERLAP_SECONDS)
        else:
            # First-ever run: go back 24 hours to avoid missing anything
            since = datetime.now() - timedelta(hours=24)
        return since

    def _fetch_changed_items(self, connection, since_dt):
        """
        Fetch SAP Items changed since since_dt using the UpdateDate + UpdateTime OData filter.

        SAP B1 Service Layer specifics:
        - UpdateDate is a datetime field  → filter with datetime'YYYY-MM-DDTHH:MM:SS'
        - UpdateTime is an integer        → e.g. 143000 means 14:30:00
        - The combined filter pattern:
            UpdateDate ge datetime'DATE' and
            (UpdateDate gt datetime'DATE' or UpdateTime ge HHMMSS)
          catches all items updated on the same date at or after the given time,
          plus any item updated on a later date regardless of time.
        - $select must NOT be used together with $expand — SAP drops the expanded
          collections when $select is present unless each collection is also listed.
          Omitting $select returns all fields including the expanded ones.
        """
        date_str = since_dt.strftime('%Y-%m-%d')
        # SAP UpdateTime filter uses 'HH:MM:SS' string format (not integer)
        time_str = since_dt.strftime('%H:%M:%S')

        # Two-part filter: same-day items at/after the given time, OR any later date
        odata_filter = (
            f"UpdateDate ge datetime'{date_str}T00:00:00' and "
            f"(UpdateDate gt datetime'{date_str}T00:00:00' or UpdateTime ge '{time_str}')"
        )

        params = {
            '$filter': odata_filter,
            # ItemPrices and ItemWarehouseInfoCollection are returned by SAP automatically
            # Do NOT use $expand — SAP B1 returns a 400 error for these navigation properties
            '$top': 500,
        }

        all_items = []
        skip = 0

        while True:
            params['$skip'] = skip
            response = connection.get('Items', params=params)

            if not response or 'value' not in response:
                break

            batch = response['value']
            all_items.extend(batch)

            # SAP returns fewer than $top records when there are no more pages
            if len(batch) < 500:
                break
            skip += 500

        return all_items

    def _fetch_changed_business_partners(self, connection, since_dt):
        """
        Fetch SAP BusinessPartners changed since since_dt.
        Tries UpdateDate filter first; if it fails or returns empty, fetches the most recently
        created/updated partners so new customers are always included.
        """
        date_str = since_dt.strftime('%Y-%m-%d')
        time_str = since_dt.strftime('%H:%M:%S')
        odata_filter = (
            f"UpdateDate ge datetime'{date_str}T00:00:00' and "
            f"(UpdateDate gt datetime'{date_str}T00:00:00' or UpdateTime ge '{time_str}')"
        )
        params = {'$filter': odata_filter, '$top': 500}
        all_partners = []
        skip = 0
        try:
            while True:
                params['$skip'] = skip
                response = connection.get('BusinessPartners', params=params)
                if not response or 'value' not in response:
                    break
                batch = response.get('value', [])
                all_partners.extend(batch)
                if len(batch) < 500:
                    break
                skip += 500
        except Exception as exc:
            _logger.debug(
                'SAP Realtime Sync: BusinessPartners UpdateDate filter failed (%s), using fallback',
                exc,
            )
            all_partners = []

        # Fallback when filter not supported or returned 0: get most recently updated/created
        # customers so new customers are always in the list (order by UpdateDate or CreateDate desc)
        if not all_partners:
            # Prefer only customers (cCustomer); if filter not supported, fetch without type filter
            fallback_filters = [
                "CardType eq 'cCustomer'",
                None,
            ]
            for filter_customer in fallback_filters:
                for orderby in ('UpdateDate desc', 'CreateDate desc', 'CardCode'):
                    try:
                        params_fb = {'$top': 500, '$orderby': orderby}
                        if filter_customer:
                            params_fb['$filter'] = filter_customer
                        response = connection.get('BusinessPartners', params=params_fb)
                        if response and response.get('value'):
                            all_partners = response['value']
                            _logger.info(
                                'SAP Realtime Sync: BusinessPartners fallback fetched %d (orderby=%s)',
                                len(all_partners), orderby,
                            )
                            break
                    except Exception as fallback_exc:
                        _logger.debug(
                            'SAP Realtime Sync: BusinessPartners orderby=%s failed: %s',
                            orderby, fallback_exc,
                        )
                if all_partners:
                    break
            if not all_partners:
                _logger.warning('SAP Realtime Sync: could not fetch any BusinessPartners')
        return all_partners

    # ------------------------------------------------------------------
    # Per-entity sync helpers
    # ------------------------------------------------------------------

    def _sync_product_data(self, backend, sap_items):
        """
        Upsert product data from SAP into Odoo:
        - If the product exists (matched by default_code = ItemCode): update name/active flag.
        - If it does not exist AND auto_create_products is enabled: create a new product.template
          with type=consu so it is immediately available in POS/Sales.
        Returns a tuple (updated_count, created_count).
        """
        updated = 0
        created = 0
        Product = self.env['product.product']
        ProductTemplate = self.env['product.template']

        for sap_item in sap_items:
            item_code = sap_item.get('ItemCode')
            item_name = sap_item.get('ItemName') or item_code
            if not item_code:
                continue
            try:
                product = Product.search([('default_code', '=', item_code)], limit=1)

                if product:
                    # --- UPDATE existing product ---
                    vals = {}
                    if item_name and product.name != item_name:
                        vals['name'] = item_name
                    if sap_item.get('Canceled') == 'tYES' and product.active:
                        vals['active'] = False
                    if vals:
                        product.sudo().write(vals)
                        updated += 1

                elif self.auto_create_products:
                    # --- CREATE new product from SAP ---
                    # In this Odoo version product.template.type accepts: consu, service, combo
                    # Storable/inventory tracking is enabled via is_storable=True (not detailed_type).
                    template_vals = {
                        'name': item_name,
                        'default_code': item_code,
                        'type': 'consu',
                        'is_storable': True,
                        'active': sap_item.get('Canceled') != 'tYES',
                        'sale_ok': True,
                        'purchase_ok': True,
                    }
                    # Carry over SAP sales UoM name if present
                    sap_uom_name = sap_item.get('SalesUnit')
                    if sap_uom_name:
                        uom = self.env['uom.uom'].search(
                            [('name', 'ilike', sap_uom_name)], limit=1
                        )
                        if uom:
                            template_vals['uom_id'] = uom.id

                    new_template = ProductTemplate.sudo().create(template_vals)
                    _logger.info(
                        'SAP Realtime Sync: created new product [%s] %s (Odoo ID: %s)',
                        item_code, item_name, new_template.id,
                    )
                    created += 1

            except Exception as exc:
                _logger.warning(
                    'SAP Realtime Sync: failed to upsert product %s: %s', item_code, exc,
                )

        return updated, created

    def _sync_prices(self, backend, sap_items):
        """
        Sync SAP ItemPrices for changed items into Odoo pricelists.
        Delegates to the existing sap.product.pricelist.sync model.
        Skips items that have no matching Odoo product (not yet created or excluded).
        Returns total price records updated.
        """
        PricelistSync = self.env['sap.product.pricelist.sync']
        Product = self.env['product.product']
        updated = 0

        for sap_item in sap_items:
            item_code = sap_item.get('ItemCode')
            sap_prices = sap_item.get('ItemPrices', [])
            if not item_code or not sap_prices:
                continue
            try:
                product = Product.search([('default_code', '=', item_code)], limit=1)
                if not product:
                    continue
                PricelistSync.sync_product_prices_from_sap(product, backend, sap_prices)
                updated += len(sap_prices)
            except Exception as exc:
                _logger.warning(
                    'SAP Realtime Sync: failed to sync prices for %s: %s', item_code, exc,
                )

        return updated

    def _sync_stock(self, backend, sap_items):
        """
        Sync SAP ItemWarehouseInfoCollection for changed items into Odoo stock.quant.
        Delegates to the existing sap.product.warehouse.info model.
        Skips items that have no matching Odoo product.
        Returns total warehouse records updated.
        """
        WarehouseInfo = self.env['sap.product.warehouse.info']
        Product = self.env['product.product']
        updated = 0

        for sap_item in sap_items:
            item_code = sap_item.get('ItemCode')
            warehouse_data = sap_item.get('ItemWarehouseInfoCollection', [])
            if not item_code or not warehouse_data:
                continue
            try:
                product = Product.search([('default_code', '=', item_code)], limit=1)
                if not product:
                    continue
                WarehouseInfo.sync_warehouse_info_from_sap(product, backend, warehouse_data)
                updated += len(warehouse_data)
            except Exception as exc:
                _logger.warning(
                    'SAP Realtime Sync: failed to sync stock for %s: %s', item_code, exc,
                )

        return updated

    def _sync_customers(self, backend, sap_partners):
        """
        Create or update res.partner from SAP BusinessPartners.
        Match by ref = CardCode. If not found and auto_create_customers: create new customer.
        Returns (updated_count, created_count).
        """
        updated = 0
        created = 0
        Partner = self.env['res.partner']

        for bp in sap_partners:
            card_code = (bp.get('CardCode') or '').strip()
            card_name = (bp.get('CardName') or card_code or '').strip()
            if not card_code:
                continue
            try:
                partner = Partner.search([('ref', '=', card_code)], limit=1)

                if partner:
                    vals = {}
                    if card_name and partner.name != card_name:
                        vals['name'] = card_name
                    if bp.get('EmailAddress') and partner.email != bp.get('EmailAddress'):
                        vals['email'] = bp.get('EmailAddress')
                    if bp.get('Phone1') and partner.phone != bp.get('Phone1'):
                        vals['phone'] = bp.get('Phone1')
                    addr = bp.get('Address') or bp.get('Street')
                    if addr and partner.street != addr:
                        vals['street'] = addr
                    if bp.get('City') and partner.city != bp.get('City'):
                        vals['city'] = bp.get('City')
                    if bp.get('ZipCode') and partner.zip != bp.get('ZipCode'):
                        vals['zip'] = bp.get('ZipCode')
                    if bp.get('Country'):
                        country = self.env['res.country'].search(
                            [('code', '=', bp.get('Country'))], limit=1
                        )
                        if country and partner.country_id != country:
                            vals['country_id'] = country.id
                    if vals:
                        partner.sudo().write(vals)
                        partner.sudo().write({'sap_synced': True})
                        updated += 1

                elif self.auto_create_customers:
                    country_id = None
                    if bp.get('Country'):
                        country = self.env['res.country'].search(
                            [('code', '=', bp.get('Country'))], limit=1
                        )
                        if country:
                            country_id = country.id
                    partner_vals = {
                        'name': card_name or card_code,
                        'ref': card_code,
                        'customer_rank': 1,
                        'sap_synced': True,
                        'email': bp.get('EmailAddress') or False,
                        'phone': bp.get('Phone1') or False,
                        'street': bp.get('Address') or bp.get('Street') or False,
                        'city': bp.get('City') or False,
                        'zip': bp.get('ZipCode') or False,
                        'country_id': country_id,
                    }
                    Partner.sudo().create(partner_vals)
                    _logger.info(
                        'SAP Realtime Sync: created new customer [%s] %s',
                        card_code, card_name,
                    )
                    created += 1

            except Exception as exc:
                _logger.warning(
                    'SAP Realtime Sync: failed to upsert customer %s: %s',
                    card_code, exc,
                )

        return updated, created

    def _sync_barcodes(self, backend, sap_items):
        """
        Sync alternative barcodes (ItemBarCodeCollection) for changed items.
        SAP does not return ItemBarCodeCollection in batch responses, so we fetch
        each changed item individually using $expand to get the full barcode list.
        UoM is resolved via sap.uom.sync (by UoMEntry ID) with a name-based fallback.
        Returns total barcode records synced.
        """
        if 'product.barcode.alternative' not in self.env:
            return 0

        AltBarcode = self.env['product.barcode.alternative']
        Product = self.env['product.product']
        connection = backend.get_connection()
        synced = 0

        for sap_item in sap_items:
            item_code = (sap_item.get('ItemCode') or '').strip()
            if not item_code:
                continue

            product = Product.search([('default_code', '=', item_code)], limit=1)
            if not product:
                continue

            try:
                # ItemBarCodeCollection may not be in batch response — fetch item directly
                # Note: $expand=ItemBarCodeCollection is NOT supported in all SAP B1 versions
                barcodes_collection = sap_item.get('ItemBarCodeCollection', [])

                if not barcodes_collection:
                    try:
                        full_item = connection.get(f"Items('{item_code}')")
                        barcodes_collection = full_item.get('ItemBarCodeCollection', [])
                    except Exception:
                        pass

                if not barcodes_collection:
                    continue

                # Rebuild alternative barcodes: delete existing and recreate from SAP
                existing = AltBarcode.search([('product_id', '=', product.id)])
                if existing:
                    existing.unlink()

                main_barcode = product.barcode
                item_synced = 0

                for bc_entry in barcodes_collection:
                    barcode_val = bc_entry.get('Barcode') or bc_entry.get('BarcodeValue')
                    if not barcode_val or barcode_val == main_barcode:
                        continue

                    uom_entry = bc_entry.get('UoMEntry') or bc_entry.get('UomEntry')
                    free_text = bc_entry.get('FreeText') or bc_entry.get('UoMName', '')

                    # Resolve UoM: prefer sap.uom.sync by UoMEntry (accurate),
                    # fall back to name search
                    uom_id = None
                    if uom_entry:
                        uom_sync = self.env['sap.uom.sync'].search([
                            ('backend_id', '=', backend.id),
                            ('sap_uom_entry', '=', uom_entry),
                        ], limit=1)
                        if uom_sync and uom_sync.odoo_uom_id:
                            uom_id = uom_sync.odoo_uom_id.id

                    if not uom_id and free_text:
                        odoo_uom = self.env['uom.uom'].search([
                            ('name', '=ilike', free_text)
                        ], limit=1)
                        if odoo_uom:
                            uom_id = odoo_uom.id

                    AltBarcode.create({
                        'product_id': product.id,
                        'barcode': barcode_val,
                        'uom_name': free_text,
                        'uom_id': uom_id,
                        'sap_uom_entry': uom_entry,
                        'active': True,
                        'last_sync': fields.Datetime.now(),
                    })
                    item_synced += 1

                synced += item_synced
                if item_synced:
                    _logger.debug(
                        'SAP Realtime Sync: %d barcode(s) synced for %s', item_synced, item_code
                    )

            except Exception as exc:
                _logger.warning(
                    'SAP Realtime Sync: failed to sync barcodes for %s: %s', item_code, exc,
                )

        return synced
