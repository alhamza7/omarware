# -*- coding: utf-8 -*-

import logging
from datetime import timedelta

from odoo import http, fields
from odoo.http import request
from odoo.osv import expression

from ._auth import ensure_jwt_user_id
from ._error import crm_error

_logger = logging.getLogger(__name__)


def _get_sales_uom(product):
    """
    Return the sales UoM for a product.
    Priority: sap.product.extended.sales_uom_id → product.uom_id (Odoo default).
    """
    try:
        ext = request.env['sap.product.extended'].sudo().search(
            [('product_id', '=', product.id)], limit=1
        )
        if ext and ext.sales_uom_id:
            return ext.sales_uom_id
    except Exception:
        pass
    return product.uom_id


def _product_to_dict(product, pricelist=None, available_uoms=None):
    """
    Serialize product.product to a dict for the CRM price-list view.
    The main `price` field is always fetched using the product's sales UoM so
    the returned value matches the SAP-linked sales-unit price, not the raw list_price.
    """
    sales_uom = _get_sales_uom(product)

    price = product.list_price
    if pricelist and pricelist.exists():
        try:
            price = pricelist._get_product_price(product, 1.0, uom=sales_uom) or product.list_price
        except Exception:
            price = product.list_price

    uom_name = sales_uom.name if sales_uom else ''
    categ_name = product.categ_id.name if product.categ_id else ''
    foreign_name = getattr(product, 'foreign_name', '') or getattr(product.product_tmpl_id, 'foreign_name', '') or ''

    return {
        'id': product.id,
        'name': product.name or '',
        'foreign_name': foreign_name,
        'item_code': product.default_code or '',
        'category_id': product.categ_id.id if product.categ_id else None,
        'category_name': categ_name,
        'uom_id': sales_uom.id if sales_uom else None,
        'uom_name': uom_name,
        'price': price,
        'list_price': product.list_price,
        'currency': pricelist.currency_id.name if pricelist and pricelist.exists() else 'USD',
        'image_url': f'/web/image/product.product/{product.id}/image_128' if product.image_128 else '',
        'available_uoms': available_uoms or [],
        'active': product.active,
    }


def _get_uoms_for_product(product, pricelist):
    """
    Collect all UoMs for a product from pricelist items, with their prices.
    Ensures the sales UoM (from sap.product.extended) is always included first,
    even when the pricelist item has uom_id = False (base price linked to sales unit).
    """
    if not pricelist or not pricelist.exists():
        return []

    sales_uom = _get_sales_uom(product)
    seen_uom_ids = set()
    result = []

    # All fixed-price pricelist items for this product.
    # Items are stored against product_tmpl_id (applied_on=1_product), not product_id.
    # Order: zero-price rows first so that if a non-zero row exists for the same UoM,
    # it wins (seen_uom_ids de-duplication keeps only the first encounter per UoM,
    # so we process zero-price rows first and let non-zero rows overwrite them).
    items = request.env['product.pricelist.item'].search([
        ('pricelist_id', '=', pricelist.id),
        ('product_tmpl_id', '=', product.product_tmpl_id.id),
        ('compute_price', '=', 'fixed'),
    ], order='fixed_price asc, write_date asc, id asc')

    # Build a dict keyed by uom_id so non-zero prices overwrite zeros for the same UoM
    uom_price_map = {}
    for item in items:
        uom = item.product_uom_id if item.product_uom_id else sales_uom
        if not uom:
            continue
        try:
            uom_price = pricelist._get_product_price(product, 1.0, uom=uom)
        except Exception:
            uom_price = product.list_price
        # Always keep the higher price for the same UoM
        if uom.id not in uom_price_map or uom_price > uom_price_map[uom.id]['price']:
            uom_price_map[uom.id] = {'uom_id': uom.id, 'uom_name': uom.name, 'price': uom_price}

    result = list(uom_price_map.values())

    # Guarantee the sales UoM is in the list even with no explicit pricelist items
    if sales_uom and sales_uom.id not in uom_price_map:
        try:
            uom_price = pricelist._get_product_price(product, 1.0, uom=sales_uom)
        except Exception:
            uom_price = product.list_price
        result.insert(0, {'uom_id': sales_uom.id, 'uom_name': sales_uom.name, 'price': uom_price})

    return result


def _resolve_pricelist(pricelist_id):
    """Return a pricelist record; fallback to 'Price list 1' then first active pricelist."""
    if pricelist_id:
        pl = request.env['product.pricelist'].browse(pricelist_id)
        if pl.exists():
            return pl

    for name_hint in ['Price list 1', 'Pricelist 1', 'Standard']:
        pl = request.env['product.pricelist'].search([('name', 'ilike', name_hint), ('active', '=', True)], limit=1)
        if pl:
            return pl

    return request.env['product.pricelist'].search([('active', '=', True)], limit=1)


def _variant_ids_with_percentage_discount(env, pricelist):
    """
    Return:
      None — a global percentage rule exists (every product may be discounted).
      set() — no matching rules.
      non-empty set — variant ids explicitly covered by template/variant/category rules.
    """
    items = env['product.pricelist.item'].search([
        ('pricelist_id', '=', pricelist.id),
        ('compute_price', '=', 'percentage'),
        ('percent_price', '>', 0),
    ])
    if not items:
        return set()
    variant_ids = set()
    Product = env['product.product'].sudo()
    for rule in items:
        if rule.applied_on == '3_global':
            return None
        if rule.applied_on == '0_product_variant' and rule.product_id:
            variant_ids.add(rule.product_id.id)
        elif rule.applied_on == '1_product' and rule.product_tmpl_id:
            variant_ids.update(rule.product_tmpl_id.product_variant_ids.ids)
        elif rule.applied_on == '2_product_category' and rule.categ_id:
            categ_ids = env['product.category'].sudo().search([('id', 'child_of', rule.categ_id.id)]).ids
            if categ_ids:
                prods = Product.search([('categ_id', 'in', categ_ids)])
                variant_ids.update(prods.ids)
    return variant_ids


def _normalize_int_list(raw, max_len=100):
    if not raw:
        return []
    if isinstance(raw, (list, tuple, set)):
        seq = list(raw)
    else:
        seq = [raw]
    out = []
    for x in seq[:max_len]:
        try:
            out.append(int(x))
        except (TypeError, ValueError):
            continue
    return out


def _normalize_str_list(raw, max_len=500):
    if not raw:
        return []
    if isinstance(raw, (list, tuple, set)):
        seq = list(raw)
    else:
        seq = [raw]
    return [str(x).strip() for x in seq[:max_len] if x and str(x).strip()]


def _truthy_api_param(value, default=True):
    """JSON-RPC often sends booleans as strings; treat missing as *default*."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ('0', 'false', 'no', 'off', ''):
        return False
    if s in ('1', 'true', 'yes', 'on'):
        return True
    return default


def _product_ids_for_uom_filter(env, uom_id, align_sap_sales_unit):
    """
    Variant ids matching a pricelist ``uom_id`` filter.

    When *align_sap_sales_unit* is True and ``sap.product.extended`` exists, exclude the
    common SAP/Odoo drift case: template ``uom_id`` is kg but SAP ``SalesUnit`` was empty
    on the Item (stored as blank ``sales_unit`` on extended) while ``sales_uom_id`` was
    never mapped — SAP reports that filter on SalesUnit text under-count vs Odoo.

    Always keep rows where ``extended.sales_uom_id`` matches (explicit SAP sales UoM map).
    """
    if not align_sap_sales_unit or 'sap.product.extended' not in env:
        return None
    Extended = env['sap.product.extended'].sudo()
    Product = env['product.product'].sudo()
    ids_sales = set(Extended.search([('sales_uom_id', '=', uom_id)]).mapped('product_id').ids)
    tpl_products = Product.search([('uom_id', '=', uom_id)])
    if not tpl_products:
        return list(ids_sales)
    ext_by_pid = {
        e.product_id.id: e
        for e in Extended.search([('product_id', 'in', tpl_products.ids)])
    }
    ids_tpl_ok = set()
    for p in tpl_products:
        ext = ext_by_pid.get(p.id)
        if ext is None:
            ids_tpl_ok.add(p.id)
        else:
            su = ext.sales_unit
            if su and str(su).strip():
                ids_tpl_ok.add(p.id)
    return list(ids_sales | ids_tpl_ok)


class PriceListController(http.Controller):

    @http.route('/api/crm/pricelist/categories', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_categories(self, **kwargs):
        """List product categories (brands) available in the pricelist — for filter dropdowns."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            # Categories that have active products
            products = request.env['product.product'].search([
                ('active', '=', True), ('sale_ok', '=', True),
            ])
            categ_ids = products.mapped('categ_id')
            items = [{'id': c.id, 'name': c.name, 'parent_id': c.parent_id.id if c.parent_id else None}
                     for c in categ_ids.sorted('name')]
            return {'success': True, 'data': {'items': items}}
        except Exception as e:
            return crm_error(e, 'list_categories')

    @http.route('/api/crm/pricelist/products', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_products(
        self,
        page=1,
        per_page=50,
        search=None,
        query=None,
        category_id=None,
        category_ids=None,
        uom_id=None,
        pricelist_id=None,
        new_releases_only=False,
        new_within_days=60,
        discount_only=False,
        fetch_all=False,
        include_inactive=False,
        sale_ok=True,
        item_codes=None,
        default_code_prefix=None,
        product_ids=None,
        branch_id=None,
        uom_align_sap_sales_unit=True,
        **kwargs,
    ):
        """
        List products for the CRM price-list view with optional strong server-side filters.

        Pagination:
          - Default ``per_page=50`` (backward compatible).
          - ``fetch_all=True`` or ``per_page=0`` returns every matching row (no server-side row cap).

        Text search: pass ``search`` or ``query`` (both accepted).

        ``branch_id`` is reserved for future branch-specific pricelist mapping (currently ignored).

        Extra filters: ``category_ids`` (list[int]), ``item_codes`` (exact default_code list),
        ``default_code_prefix``, ``product_ids`` (variant ids), ``include_inactive``,
        ``sale_ok`` (bool, default True).

        ``uom_align_sap_sales_unit`` (bool, default True): when ``uom_id`` is set, restrict
        matches so template UoM alone does not count if ``sap.product.extended`` exists with
        an empty SAP ``sales_unit`` (SalesUnit not set in SAP). Set to False for the legacy
        ``(uom_id = X) OR (extended.sales_uom_id = X)`` behaviour without that guard.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            pricelist = _resolve_pricelist(pricelist_id)

            text = (search or query or '').strip()
            domain = []

            if not include_inactive:
                domain.append(('active', '=', True))
            if sale_ok is not False and sale_ok is not None:
                domain.append(('sale_ok', '=', True))

            cat_ids = _normalize_int_list(category_ids, max_len=200)
            if cat_ids:
                domain.append(('categ_id', 'in', cat_ids))
            elif category_id:
                try:
                    domain.append(('categ_id', '=', int(category_id)))
                except (TypeError, ValueError):
                    pass

            codes = _normalize_str_list(item_codes, max_len=500)
            if codes:
                domain.append(('default_code', 'in', codes))

            if default_code_prefix:
                pref = str(default_code_prefix).strip()
                if pref:
                    if not pref.endswith('%'):
                        pref = pref + '%'
                    domain.append(('default_code', 'ilike', pref))

            pids = _normalize_int_list(product_ids, max_len=2000)
            if pids:
                domain.append(('id', 'in', pids))

            if text:
                ProductMeta = request.env['product.product']
                if ProductMeta._fields.get('foreign_name'):
                    domain += ['|', '|',
                               ('name', 'ilike', text),
                               ('default_code', 'ilike', text),
                               ('foreign_name', 'ilike', text)]
                else:
                    domain += ['|', ('name', 'ilike', text), ('default_code', 'ilike', text)]

            if new_releases_only:
                try:
                    days = max(1, int(new_within_days))
                except (TypeError, ValueError):
                    days = 60
                since = fields.Datetime.now() - timedelta(days=days)
                domain.append(('create_date', '>=', since))

            if uom_id:
                try:
                    uid = int(uom_id)
                except (TypeError, ValueError):
                    uid = None
                if uid:
                    align = _truthy_api_param(uom_align_sap_sales_unit, default=True)
                    narrowed = _product_ids_for_uom_filter(request.env, uid, align)
                    if narrowed is not None:
                        domain = expression.AND([domain, [('id', 'in', narrowed)]]) if domain else [('id', 'in', narrowed)]
                    else:
                        ext_pids = request.env['sap.product.extended'].sudo().search([
                            ('sales_uom_id', '=', uid),
                        ]).mapped('product_id').ids
                        if ext_pids:
                            uom_domain = ['|', ('uom_id', '=', uid), ('id', 'in', ext_pids)]
                        else:
                            uom_domain = [('uom_id', '=', uid)]
                        domain = expression.AND([domain, uom_domain]) if domain else uom_domain

            if discount_only and pricelist:
                disc = _variant_ids_with_percentage_discount(request.env, pricelist)
                if disc is not None:
                    if not disc:
                        return {
                            'success': True,
                            'data': {
                                'items': [],
                                'total': 0,
                                'page': int(page) if page else 1,
                                'per_page': int(per_page) if per_page else 0,
                                'returned': 0,
                            },
                        }
                    domain.append(('id', 'in', list(disc)))

            Product = request.env['product.product']
            total = Product.search_count(domain)

            try:
                page_n = max(1, int(page or 1))
            except (TypeError, ValueError):
                page_n = 1

            fetch_all_flag = bool(fetch_all) or kwargs.get('fetch_all') is True
            try:
                per_n = int(per_page) if per_page is not None else 50
            except (TypeError, ValueError):
                per_n = 50

            if fetch_all_flag or per_n <= 0:
                products = Product.search(domain, order='name asc') if total else Product.browse()
                per_out = 0
            else:
                per_n = max(per_n, 1)
                offset = (page_n - 1) * per_n
                products = Product.search(domain, limit=per_n, offset=offset, order='name asc')
                per_out = per_n

            items = []
            for p in products:
                uoms = _get_uoms_for_product(p, pricelist)
                items.append(_product_to_dict(p, pricelist, uoms))

            return {
                'success': True,
                'data': {
                    'items': items,
                    'total': total,
                    'page': page_n,
                    'per_page': per_out,
                    'returned': len(items),
                },
            }
        except Exception as e:
            return crm_error(e, 'list_products')

    @http.route('/api/crm/pricelist/products/<int:product_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def get_product(self, product_id, pricelist_id=None, **kwargs):
        """Get full product detail with all UoM prices and stock info."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            product = request.env['product.product'].browse(product_id)
            if not product.exists() or not product.active:
                return {'success': False, 'error': 'Product not found'}

            pricelist = _resolve_pricelist(pricelist_id)
            uoms = _get_uoms_for_product(product, pricelist)
            data = _product_to_dict(product, pricelist, uoms)

            # Stock qty
            try:
                data['qty_on_hand'] = product.qty_available
                data['qty_reserved'] = product.virtual_available
            except Exception:
                data['qty_on_hand'] = 0
                data['qty_reserved'] = 0

            return {'success': True, 'data': data}
        except Exception as e:
            return crm_error(e, 'get_product')

    @http.route('/api/crm/pricelist/pricelists', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_pricelists(self, **kwargs):
        """List available pricelists (for dropdown in the CRM UI)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            pricelists = request.env['product.pricelist'].search([('active', '=', True)], order='name asc')
            items = [{'id': p.id, 'name': p.name, 'currency': p.currency_id.name} for p in pricelists]
            return {'success': True, 'data': {'items': items}}
        except Exception as e:
            return crm_error(e, 'list_pricelists')

    @http.route('/api/crm/pricelist/requested_items/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def create_requested_item(self, customer_id, product_name, notes=None, **kwargs):
        """
        Customer requests an item not currently in the price list.
        Creates a crm.requested.item record linked to the customer.
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not customer_id or not product_name:
                return {'success': False, 'error': 'customer_id and product_name are required'}
            item = request.env['lugal.crm.requested.item'].create({
                'customer_id': customer_id,
                'product_name': product_name,
                'notes': notes or '',
                'requested_by_id': request.env.uid,
            })
            return {'success': True, 'data': {'id': item.id, 'product_name': item.product_name}}
        except Exception as e:
            return crm_error(e, 'create_requested_item')

    @http.route('/api/crm/pricelist/requested_items', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_requested_items(self, page=1, per_page=50, customer_id=None, status=None, **kwargs):
        """List requested (out-of-catalog) items."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False)]
            if customer_id:
                domain.append(('customer_id', '=', customer_id))
            if status:
                domain.append(('status', '=', status))
            RI = request.env['lugal.crm.requested.item']
            total = RI.search_count(domain)
            items_rec = RI.search(domain, limit=per_page, offset=(page - 1) * per_page, order='create_date desc')
            items = [{
                'id': r.id,
                'customer_id': r.customer_id.id if r.customer_id else None,
                'customer_name': r.customer_id.name if r.customer_id else '',
                'product_name': r.product_name or '',
                'status': r.status,
                'notes': r.notes or '',
                'created_at': r.create_date.isoformat() if r.create_date else None,
            } for r in items_rec]
            return {'success': True, 'data': {'items': items, 'total': total}}
        except Exception as e:
            return crm_error(e, 'list_requested_items')

    @http.route('/api/crm/pricelist/requested_items/<int:item_id>/update_status', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def update_requested_item_status(self, item_id, status, **kwargs):
        """Update status of a requested item: pending / notified / fulfilled / cancelled."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            item = request.env['lugal.crm.requested.item'].browse(item_id)
            if not item.exists() or item.is_deleted:
                return {'success': False, 'error': 'Requested item not found'}
            item.write({'status': status})
            return {'success': True, 'data': {'id': item.id, 'status': item.status}}
        except Exception as e:
            return crm_error(e, 'update_requested_item_status')

    @http.route('/api/crm/pricelist/requested_items/<int:item_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def delete_requested_item(self, item_id, **kwargs):
        """Soft-delete a requested item."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            item = request.env['lugal.crm.requested.item'].browse(item_id)
            if not item.exists():
                return {'success': False, 'error': 'Requested item not found'}
            item.write({'is_deleted': True})
            return {'success': True}
        except Exception as e:
            return crm_error(e, 'delete_requested_item')
