# -*- coding: utf-8 -*-
"""
Shared helpers for the POS Perfume External API v1.

Provides:
  - JSON response builders  : _json_response, _success, _error
  - Request body parser     : _get_json_body
  - Record serialisers      : _serialize_order, _serialize_line,
                              _serialize_customer, _serialize_product
  - Line builder            : _build_line_vals
"""

import copy
import json
import logging
import re
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------
# WHY auth='none' + _check_auth()?
# ─────────────────────────────────────────────────────────────────────────────
# auth='user'  → Odoo middleware handles auth via session cookie only.
#                If the session is invalid it redirects to /web/login (303 HTML).
#                Bearer tokens are NOT processed by this middleware.
#
# auth='none'  → Odoo does nothing. We call _check_auth() manually.
#                On success: request.update_env(user=uid) sets the user env.
#                On failure: we return JSON 401 — never HTML, never redirect.
# ─────────────────────────────────────────────────────────────────────────────

def _json_response(data, status=200):
    """Return a Werkzeug Response with JSON body and CORS headers."""
    body = json.dumps(data, default=str)
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
    }
    return Response(body, status=status, headers=headers)


def _success(data=None, message='OK'):
    """Wrap a successful payload into the standard envelope."""
    return _json_response({'success': True, 'message': message, 'data': data})


def _error(message, status=400):
    """Wrap an error message into the standard envelope."""
    return _json_response({'success': False, 'error': message}, status=status)


# ---------------------------------------------------------------------------
# Request body parser
# ---------------------------------------------------------------------------

def _get_json_body():
    """
    Parse JSON from the incoming HTTP request body.
    Odoo type='http' controllers must read body from request.httprequest.data.
    Returns an empty dict on any parsing failure.
    """
    try:
        raw = request.httprequest.data
        if not raw:
            return {}
        return json.loads(raw.decode('utf-8'))
    except Exception as e:
        _logger.warning('[POS API] Failed to parse JSON request body: %s', e)
        return {}


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def _check_auth():
    """
    Authenticate the request via Bearer API key OR active session cookie.

    Called manually at the top of every route handler (routes use auth='none'
    so Odoo never redirects to /web/login — we always return JSON 401 instead).

    On success  → calls request.update_env(user=uid) and returns None.
    On failure  → returns a JSON 401 Response (caller must return it immediately).

    How to use in a route:
        auth_err = _check_auth()
        if auth_err:
            return auth_err
        # ... rest of handler
    """
    # 1. Bearer token (API key) — stateless, recommended for external apps ----
    auth_header = request.httprequest.headers.get('Authorization', '')
    if auth_header.lower().startswith('bearer '):
        token = auth_header[7:].strip()
        try:
            uid = request.env['res.users.apikeys'].sudo()._check_credentials(
                scope='rpc', key=token
            )
            if not uid:
                return _error('Invalid API key', 401)
            request.update_env(user=uid)
            return None  # success
        except Exception as e:
            return _error(f'API key authentication failed: {e}', 401)

    # 2. Session cookie — for browser-based apps -------------------------------
    uid = request.session.uid
    if uid and uid not in (None, False, 0, 1):
        request.update_env(user=uid)
        return None  # success

    return _error(
        'Authentication required. '
        'Use "Authorization: Bearer <api_key>" header '
        'or log in via POST /web/session/authenticate.',
        401,
    )


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _serialize_order(order):
    """Serialise a pos.perfume.order record to a plain dict."""
    return {
        'id': order.id,
        'name': order.name,
        'date': order.date.isoformat() if order.date else None,
        'state': order.state,
        'user_id': {
            'id': order.user_id.id,
            'name': order.user_id.name,
        } if order.user_id else None,
        'partner_id': {
            'id': order.partner_id.id,
            'name': order.partner_id.name,
            'phone': order.partner_id.phone or '',
            'mobile': getattr(order.partner_id, 'mobile', '') or '',
            'email': order.partner_id.email or '',
        } if order.partner_id else None,
        'pricelist_id': {
            'id': order.pricelist_id.id,
            'name': order.pricelist_id.name,
        } if order.pricelist_id else None,
        'currency_id': {
            'id': order.currency_id.id,
            'name': order.currency_id.name,
        } if order.currency_id else None,
        'exchange_rate': order.exchange_rate,
        'amount_subtotal': order.amount_subtotal,
        'amount_discount': order.amount_discount,
        'amount_tax': order.amount_tax,
        'amount_total': order.amount_total,
        'amount_total_iqd': order.amount_total_iqd,
        'invoice_type': order.invoice_type or '',
        'note': order.note or '',
        'sale_order_id': {
            'id': order.sale_order_id.id,
            'name': order.sale_order_id.name,
            'state': order.sale_order_id.state,
        } if order.sale_order_id else None,
        'sap_doc_num': order.sap_doc_num or '',
        'sap_doc_entry': order.sap_doc_entry or 0,
        'sap_synced': order.sap_synced,
        'sap_error_message': order.sap_error_message or '',
        'sap_last_sync_date': order.sap_last_sync_date.isoformat() if order.sap_last_sync_date else None,
        'order_lines': [_serialize_line(l) for l in order.order_line_ids],
    }


def _serialize_line(line):
    """Serialise a pos.perfume.order.line record to a plain dict."""
    return {
        'id': line.id,
        'sequence': line.sequence,
        'product_id': {
            'id': line.product_id.id,
            'name': line.product_id.name,
            'default_code': line.product_id.default_code or '',
            'foreign_name': getattr(line.product_id, 'foreign_name', '') or '',
        } if line.product_id else None,
        'product_uom_id': {
            'id': line.product_uom_id.id,
            'name': line.product_uom_id.name,
        } if line.product_uom_id else None,
        'warehouse_id': {
            'id': line.warehouse_id.id,
            'name': line.warehouse_id.name,
            'code': line.warehouse_id.code,
        } if line.warehouse_id else None,
        'location_id': {
            'id': line.location_id.id,
            'name': line.location_id.name,
        } if line.location_id else None,
        'quantity': line.quantity,
        'unit_price': line.unit_price,
        'discount_percent': line.discount_percent,
        'price_after_discount': line.price_after_discount,
        'line_subtotal': line.line_subtotal,
        'discount_amount': line.discount_amount,
        'line_total': line.line_total,
        'available_qty': line.available_qty,
        'custom_product_name': line.custom_product_name or '',
    }


def _serialize_customer(partner):
    """Serialise a res.partner record to a plain dict."""
    return {
        'id': partner.id,
        'name': partner.name,
        'ref': partner.ref or '',
        'phone': partner.phone or '',
        'mobile': getattr(partner, 'mobile', '') or '',
        'email': partner.email or '',
        'street': partner.street or '',
        'city': partner.city or '',
        'country_id': {
            'id': partner.country_id.id,
            'name': partner.country_id.name,
        } if partner.country_id else None,
        'pricelist_id': {
            'id': partner.property_product_pricelist.id,
            'name': partner.property_product_pricelist.name,
        } if partner.property_product_pricelist else None,
    }


# ---------------------------------------------------------------------------
# Brand detection
# ---------------------------------------------------------------------------

# Maps items_group_code (from sap_product_extended) → brand info.
# Derived from the DB analysis: items_group_code is the most reliable source.
_ITEMS_GROUP_BRAND_MAP = {
    106: {'key': 'premium',         'name': 'Premium',          'code': 'PRM'},
    107: {'key': 'givaudan',         'name': 'Givaudan',         'code': 'G'},
    108: {'key': 'adf',             'name': 'Amour de Fleurs',  'code': 'ADF'},
    109: {'key': 'robertet',        'name': 'Robertet',         'code': 'R'},
    110: {'key': 'european',        'name': 'European',         'code': 'EU'},
    111: {'key': 'florchem',        'name': 'Florchem',         'code': 'FL'},
    112: {'key': 'european',        'name': 'European / Euro',  'code': 'N1'},
    113: {'key': 'exp',             'name': 'EXP',              'code': 'EXP'},
    116: {'key': 'mix',             'name': 'Mix',              'code': 'MIX'},
    117: {'key': 'crystal_glass',   'name': 'Crystal / Glass',  'code': 'CS'},
    118: {'key': 'samples',         'name': 'Samples',          'code': 'S'},
    119: {'key': 'alcohol',         'name': 'Alcohol',          'code': 'ALC'},
    120: {'key': 'pack',            'name': 'Pack',             'code': 'PK'},
    122: {'key': 'dye',             'name': 'Dye / Colour',     'code': 'DY'},
    123: {'key': 'firmenic',        'name': 'Firmenic',         'code': 'FF'},
    124: {'key': 'af',              'name': 'AF Series',        'code': 'AF'},
    125: {'key': 'box',             'name': 'Box / Packaging',  'code': 'B'},
    131: {'key': 'maison',          'name': 'Maison',           'code': 'MA'},
    132: {'key': 'local',           'name': 'Local',            'code': 'LOC'},
    134: {'key': 'cm',              'name': 'CM Series',        'code': 'CM'},
    135: {'key': 'p_series',        'name': 'P Series',         'code': 'P'},
    137: {'key': 'mac',             'name': 'MAC',              'code': 'MAC'},
}

# Fallback brand detection from default_code prefix when SAP extended is unavailable
_CODE_PREFIX_BRAND_MAP = [
    ('ADF', {'key': 'adf',           'name': 'Amour de Fleurs', 'code': 'ADF'}),
    ('FF',  {'key': 'firmenic',      'name': 'Firmenic',        'code': 'FF'}),
    ('FL',  {'key': 'florchem',      'name': 'Florchem',        'code': 'FL'}),
    ('N1',  {'key': 'european',      'name': 'European / Euro', 'code': 'N1'}),
    ('R',   {'key': 'robertet',      'name': 'Robertet',        'code': 'R'}),
    ('G',   {'key': 'givaudan',      'name': 'Givaudan',        'code': 'G'}),
    ('CS',  {'key': 'crystal_glass', 'name': 'Crystal / Glass', 'code': 'CS'}),
    ('LOC', {'key': 'local',         'name': 'Local',           'code': 'LOC'}),
    ('PRM', {'key': 'premium',       'name': 'Premium',         'code': 'PRM'}),
    ('MA',  {'key': 'maison',        'name': 'Maison',          'code': 'MA'}),
    ('MIX', {'key': 'mix',           'name': 'Mix',             'code': 'MIX'}),
    ('S',   {'key': 'samples',       'name': 'Samples',         'code': 'S'}),
    ('PK',  {'key': 'pack',          'name': 'Pack',            'code': 'PK'}),
    ('B',   {'key': 'box',           'name': 'Box / Packaging', 'code': 'B'}),
    ('CM',  {'key': 'cm',            'name': 'CM Series',       'code': 'CM'}),
    ('P',   {'key': 'p_series',      'name': 'P Series',        'code': 'P'}),
]


def _get_brand(product, sap_ext=None):
    """
    Return brand info dict for a product.

    Strategy:
      1. Use items_group_code from pre-fetched sap_ext (avoids extra DB query)
      2. Fall back to default_code prefix pattern
    Returns: { key, name, code }
    """
    # Strategy 1: SAP items_group_code from pre-fetched record
    try:
        if sap_ext and sap_ext.items_group_code:
            brand = _ITEMS_GROUP_BRAND_MAP.get(sap_ext.items_group_code)
            if brand:
                return brand
    except Exception:
        pass

    # Strategy 2: default_code prefix fallback
    code = (product.default_code or '').upper()
    for prefix, brand in _CODE_PREFIX_BRAND_MAP:
        if code.startswith(prefix):
            return brand

    return {'key': 'other', 'name': 'Other', 'code': ''}


# ---------------------------------------------------------------------------
# Category type detection
# ---------------------------------------------------------------------------

# Category type definitions with their inner properties.
# Each category has a type key, display name, and a properties dict
# describing the attributes relevant to that category type.

_CATEGORY_PROPERTIES = {
    'fragrances': {
        'type':        'fragrances',
        'name':        'Fragrances',
        'name_ar':     'عطور',
        'properties':  {
            'size_ml':        None,   # e.g. 100, 50, 30, 25, 10
            'size_kg':        None,   # e.g. 1.0, 0.5, 0.25 (bulk)
            'is_bulk':        False,  # true if sold by weight (kg)
            'concentration':  None,   # EDP, EDT, EAU, OIL, etc.
            'gender':         None,   # M, W, Unisex
            'season':         None,   # Summer, Winter, All seasons
            'longevity':      None,   # hours
            'sillage':        None,   # light, moderate, heavy
        },
    },
    'glass': {
        'type':        'glass',
        'name':        'Glass',
        'name_ar':     'زجاج',
        'properties':  {
            'glass_type':     None,   # bottle, spray, roll-on, atomizer, jar
            'capacity_ml':    None,   # volume in ml
            'cover_box':      False,  # whether it comes with a cover/cap box
            'cap_type':       None,   # plastic, metal, wooden, none
            'shape':          None,   # round, square, oval, custom
            'color':          None,   # clear, frosted, amber, blue, etc.
        },
    },
    'packaging': {
        'type':        'packaging',
        'name':        'Packaging',
        'name_ar':     'تغليف',
        'properties':  {
            'box_type':       None,   # luxury, gift, plain, display
            'is_luxury_box':  False,
            'is_gift_box':    False,
            'size':           None,   # S, M, L, XL or dimensions
            'material':       None,   # cardboard, velvet, wood, plastic
            'color':          None,
            'units_per_box':  None,   # how many bottles fit
        },
    },
    'devices': {
        'type':        'devices',
        'name':        'Devices',
        'name_ar':     'أجهزة',
        'properties':  {
            'device_type':    None,   # electric_diffuser, nebulizer, car_diffuser, humidifier
            'power_type':     None,   # USB, battery, plug, solar
            'coverage_area':  None,   # m²
            'timer':          False,
            'color':          None,
        },
    },
    'accessories': {
        'type':        'accessories',
        'name':        'Accessories',
        'name_ar':     'اكسسوارات',
        'properties':  {
            'accessory_type': None,   # funnel, atomizer, pump, label, seal, dropper
            'material':       None,   # plastic, metal, glass, silicone
            'color':          None,
            'size':           None,
        },
    },
    'incense': {
        'type':        'incense',
        'name':        'Incense',
        'name_ar':     'بخور',
        'properties':  {
            'incense_type':   None,   # wood, resin, coal, stick, cone, powder, oil
            'weight_g':       None,   # grams
            'is_charcoal':    False,
            'scent_family':   None,   # oud, musk, rose, sandalwood, etc.
            'burn_time_hrs':  None,
        },
    },
    'samples': {
        'type':        'samples',
        'name':        'Samples',
        'name_ar':     'عينات',
        'properties':  {
            'size_ml':        None,
            'is_tester':      True,
            'version':        None,   # e.g. "v1", "v2"
        },
    },
    'pack': {
        'type':        'pack',
        'name':        'Pack / Set',
        'name_ar':     'باكيج',
        'properties':  {
            'units_in_pack':  None,
            'pack_type':      None,   # gift_set, bundle, trial_kit
        },
    },
    'alcohol': {
        'type':        'alcohol',
        'name':        'Alcohol',
        'name_ar':     'كحول',
        'properties':  {
            'concentration_pct': None,  # e.g. 95, 70
            'volume_liters':     None,
        },
    },
    'other': {
        'type':    'other',
        'name':    'Other',
        'name_ar': 'أخرى',
        'properties': {},
    },
}

# Maps items_group_code → category type key
_ITEMS_GROUP_CATEGORY_MAP = {
    106: 'fragrances',   # PRM – mixed fragrances / Premium
    107: 'fragrances',   # Givaudan fragrances
    108: 'fragrances',   # ADF fragrances
    109: 'fragrances',   # Robertet fragrances
    110: 'fragrances',   # European fragrances
    111: 'fragrances',   # Florchem fragrances
    112: 'fragrances',   # European/Euro N1 fragrances
    113: 'fragrances',   # EXP fragrances
    116: 'fragrances',   # Mix fragrances
    117: 'glass',        # CS – Crystal/Glass (bottles, jars)
    118: 'samples',      # S – Samples
    119: 'alcohol',      # ALC – Alcohol
    120: 'pack',         # PK – Packs/Sets
    122: 'accessories',  # DY – Dyes/Colours
    123: 'fragrances',   # Firmenic fragrances
    124: 'fragrances',   # AF Series fragrances
    125: 'packaging',    # B – Boxes/Packaging
    131: 'fragrances',   # Maison fragrances
    132: 'fragrances',   # Local fragrances
    134: 'accessories',  # CM – CM accessories
    135: 'accessories',  # P Series accessories
    137: 'accessories',  # MAC accessories
}

# Fallback: category detection from default_code prefix
_CODE_PREFIX_CATEGORY_MAP = [
    ('ADF', 'fragrances'),
    ('FF',  'fragrances'),
    ('FL',  'fragrances'),
    ('N1',  'fragrances'),
    ('R',   'fragrances'),
    ('G',   'fragrances'),
    ('PRM', 'fragrances'),
    ('MA',  'fragrances'),
    ('MIX', 'fragrances'),
    ('CS',  'glass'),
    ('S',   'samples'),
    ('PK',  'pack'),
    ('B',   'packaging'),
    ('ALC', 'alcohol'),
    ('LOC', 'fragrances'),
    ('CM',  'accessories'),
    ('P',   'accessories'),
    ('DY',  'accessories'),
    ('HS',  'accessories'),
    ('DV',  'devices'),
    ('INC', 'incense'),
    ('BKH', 'incense'),
]


def _get_category_type(product, sap_ext=None):
    """
    Return category type info with populated inner properties for a product.

    Strategy:
      1. items_group_code from pre-fetched sap_ext (avoids extra DB query)
      2. default_code prefix fallback
      3. Populate known properties from product fields / UoM group name

    Returns a dict: { type, name, name_ar, properties: {...} }
    """
    # --- Determine category type key ---
    cat_key = 'other'

    # Strategy 1: SAP items_group_code from pre-fetched record
    try:
        if sap_ext and sap_ext.items_group_code:
            cat_key = _ITEMS_GROUP_CATEGORY_MAP.get(sap_ext.items_group_code, 'other')
    except Exception:
        pass

    # Strategy 2: default_code prefix fallback
    if cat_key == 'other':
        code = (product.default_code or '').upper()
        for prefix, key in _CODE_PREFIX_CATEGORY_MAP:
            if code.startswith(prefix):
                cat_key = key
                break

    # Get the base definition and deep-copy so we can populate it
    cat_def = copy.deepcopy(_CATEGORY_PROPERTIES.get(cat_key, _CATEGORY_PROPERTIES['other']))
    props = cat_def['properties']

    # --- Populate properties from product data ---

    # UoM Group name contains size info, e.g. "درزن", "1KG", "100ML", "ك 12 ق"
    uom_group_name = ''
    try:
        if hasattr(product, 'sap_uom_group_id') and product.sap_uom_group_id:
            uom_group_name = product.sap_uom_group_id.name or ''
        elif sap_ext and sap_ext.sap_uom_group_id:
            uom_group_name = sap_ext.sap_uom_group_id.name or ''
    except Exception:
        pass

    product_name_upper = (product.name or '').upper()
    code_upper = (product.default_code or '').upper()
    combined = f"{product_name_upper} {code_upper} {uom_group_name.upper()}"

    if cat_key == 'fragrances':
        # Size in ml
        ml_match = re.search(r'(\d+)\s*ML', combined)
        if ml_match:
            props['size_ml'] = int(ml_match.group(1))
        # Size in kg
        kg_match = re.search(r'(\d+(?:\.\d+)?)\s*KG', combined)
        if kg_match:
            props['size_kg'] = float(kg_match.group(1))
            props['is_bulk'] = True
        elif re.search(r'1KG|0\.5|0\.25|KILO|كيلو|كيلوغرام', combined):
            props['is_bulk'] = True
        # Gender from name hints
        if re.search(r'\bW\b|\bWOMEN\b|\bنسائي\b|\bWOMAN\b', combined):
            props['gender'] = 'W'
        elif re.search(r'\bM\b|\bMEN\b|\bرجالي\b', combined):
            props['gender'] = 'M'
        else:
            props['gender'] = 'Unisex'

    elif cat_key == 'glass':
        # Capacity from UoM or name
        ml_match = re.search(r'(\d+)\s*ML', combined)
        if ml_match:
            props['capacity_ml'] = int(ml_match.group(1))
        # Glass type hints
        if re.search(r'SPRAY|رش', combined):
            props['glass_type'] = 'spray'
        elif re.search(r'ROLL.?ON|رول', combined):
            props['glass_type'] = 'roll-on'
        elif re.search(r'ATOMIZER|اتوميزر', combined):
            props['glass_type'] = 'atomizer'
        elif re.search(r'JAR|برطمان', combined):
            props['glass_type'] = 'jar'
        else:
            props['glass_type'] = 'bottle'
        # Cover box detection
        if re.search(r'BOX|COVER|غطاء|صندوق|علبة', combined):
            props['cover_box'] = True

    elif cat_key == 'packaging':
        # Box type
        if re.search(r'LUXURY|فاخر|فخم', combined):
            props['is_luxury_box'] = True
            props['box_type'] = 'luxury'
        elif re.search(r'GIFT|هدية|هدايا', combined):
            props['is_gift_box'] = True
            props['box_type'] = 'gift'
        else:
            props['box_type'] = 'plain'
        # Size hints
        size_match = re.search(r'\b(XS|S|M|L|XL|XXL)\b', combined)
        if size_match:
            props['size'] = size_match.group(1)
        # Units per box from UoM group name, e.g. "ك 12 ق"
        units_match = re.search(r'ك\s*(\d+)\s*ق|(\d+)\s*PCS|(\d+)\s*UNITS', combined)
        if units_match:
            props['units_per_box'] = int(
                units_match.group(1) or units_match.group(2) or units_match.group(3)
            )

    elif cat_key == 'incense':
        if re.search(r'COAL|فحم|CHARCOAL', combined):
            props['incense_type'] = 'coal'
            props['is_charcoal'] = True
        elif re.search(r'STICK|عود|WOOD', combined):
            props['incense_type'] = 'wood'
        elif re.search(r'RESIN|راتنج', combined):
            props['incense_type'] = 'resin'
        elif re.search(r'POWDER|مسحوق', combined):
            props['incense_type'] = 'powder'
        else:
            props['incense_type'] = 'other'
        # Weight
        g_match = re.search(r'(\d+)\s*(?:GM|G\b|GRAM)', combined)
        if g_match:
            props['weight_g'] = int(g_match.group(1))

    elif cat_key == 'samples':
        ml_match = re.search(r'(\d+)\s*ML', combined)
        if ml_match:
            props['size_ml'] = int(ml_match.group(1))
        # Sample version from product field
        try:
            if hasattr(product, 'sample_version') and product.sample_version:
                props['version'] = product.sample_version
        except Exception:
            pass

    return cat_def


def _get_warehouses_batch(product_ids):
    """
    Return a dict mapping product_id → list of warehouse stock dicts.

    Fetches stock for ALL given product IDs in a single SQL query using
    stock.quant joined to stock_warehouse — far cheaper than one query
    per product when listing search results.

    Only warehouses with available_qty > 0 are included.
    Falls back to an empty dict on any error.
    """
    if not product_ids:
        return {}
    try:
        # Try SAP warehouse info first (same model used by _get_warehouses_simple)
        result = {pid: [] for pid in product_ids}
        if 'sap.product.warehouse.info' in request.env:
            sap_infos = request.env['sap.product.warehouse.info'].sudo().search(
                [('product_id', 'in', product_ids)]
            )
            if sap_infos:
                for info in sap_infos:
                    qty = float(info.current_qty_available or info.last_available or 0)
                    if qty > 0 and info.warehouse_id:
                        result.setdefault(info.product_id.id, []).append({
                            'id':       info.warehouse_id.id,
                            'name':     info.warehouse_id.name,
                            'code':     info.sap_warehouse_code or info.warehouse_id.code,
                            'quantity': qty,
                        })
                # If SAP data found for at least one product, return it
                if any(result.values()):
                    return result

        # Fallback: single batch SQL against stock.quant
        query = """
            SELECT
                sq.product_id,
                sw.id    AS warehouse_id,
                sw.name  AS warehouse_name,
                sw.code  AS warehouse_code,
                COALESCE(SUM(sq.quantity - sq.reserved_quantity), 0) AS available_qty
            FROM stock_quant sq
            JOIN stock_location sl
                ON sl.id = sq.location_id
               AND sl.usage = 'internal'
            JOIN stock_warehouse sw
                ON sw.id = sl.warehouse_id
               AND sw.active = true
            WHERE sq.product_id = ANY(%s)
            GROUP BY sq.product_id, sw.id, sw.name, sw.code
            HAVING COALESCE(SUM(sq.quantity - sq.reserved_quantity), 0) > 0
            ORDER BY sq.product_id, sw.name
        """
        request.env.cr.execute(query, (list(product_ids),))
        for row in request.env.cr.dictfetchall():
            pid = row['product_id']
            result.setdefault(pid, []).append({
                'id':       row['warehouse_id'],
                'name':     row['warehouse_name'],
                'code':     row['warehouse_code'],
                'quantity': float(row['available_qty']),
            })
        return result
    except Exception:
        return {}


def _get_sap_extended_batch(product_ids):
    """
    Fetch sap.product.extended records for a list of product IDs in one query.
    Returns a dict: { product_id → sap.product.extended record (or None) }
    """
    if not product_ids:
        return {}
    try:
        exts = request.env['sap.product.extended'].sudo().search(
            [('product_id', 'in', list(product_ids))]
        )
        return {ext.product_id.id: ext for ext in exts}
    except Exception:
        return {}


def _serialize_product(product, warehouses=None, available_uoms=None, sap_ext=None):
    """
    Serialise a product.product record to a summary dict.

    ``warehouses``    — pre-fetched warehouse stock list (from _get_warehouses_batch).
    ``available_uoms``— pre-fetched UoM+price list (from _get_uoms_from_pricelist).
    ``sap_ext``       — pre-fetched sap.product.extended record (from _get_sap_extended_batch).
                        Pass None to let the function fetch it individually (single-product
                        endpoints).  Pass False to skip SAP extended lookup entirely.
    """
    foreign_name = getattr(product, 'foreign_name', '') or ''
    priority, color_class, badge_text = product._get_product_priority_and_color(
        product.default_code
    )

    if available_uoms is None:
        available_uoms = [{'id': product.uom_id.id, 'name': product.uom_id.name, 'price': product.list_price}]

    # Resolve sap.product.extended — use pre-fetched value when available
    if sap_ext is None:
        try:
            sap_ext = request.env['sap.product.extended'].sudo().search(
                [('product_id', '=', product.id)], limit=1
            ) or False
        except Exception:
            sap_ext = False

    items_group_code = 0
    items_group_name = ''
    if sap_ext:
        items_group_code = sap_ext.items_group_code or 0
        items_group_name = sap_ext.items_group_name or ''

    return {
        'id': product.id,
        'name': product.name,
        'default_code': product.default_code or '',
        'foreign_name': foreign_name,
        'uom_id': {'id': product.uom_id.id, 'name': product.uom_id.name},
        'list_price': product.list_price,
        'qty_available': product.qty_available,
        'color_class': color_class,
        'badge_text': badge_text,
        'active': product.active,
        'sale_ok': product.sale_ok,
        'categ_id': {
            'id': product.categ_id.id,
            'name': product.categ_id.name,
        } if product.categ_id else None,
        'items_group_code': items_group_code,
        'items_group_name': items_group_name,
        'brand': _get_brand(product, sap_ext=sap_ext),
        'category_type': _get_category_type(product, sap_ext=sap_ext),
        'available_uoms': available_uoms,
        'warehouses': warehouses if warehouses is not None else [],
    }


# ---------------------------------------------------------------------------
# Order line builder
# ---------------------------------------------------------------------------

def _build_line_vals(data):
    """
    Build a field-value dict for creating/updating a pos.perfume.order.line.
    Returns a dict on success, or an error string on validation failure.
    """
    product_id = data.get('product_id')
    product_uom_id = data.get('product_uom_id')
    warehouse_id = data.get('warehouse_id')

    if not product_id:
        return 'product_id is required for each order line'
    if not warehouse_id:
        return 'warehouse_id is required for each order line'

    product = request.env['product.product'].browse(int(product_id))
    if not product.exists():
        return f'Product {product_id} not found'

    # Default UoM to product's base UoM if not provided
    if product_uom_id:
        uom = request.env['uom.uom'].browse(int(product_uom_id))
        if not uom.exists():
            return f'UoM {product_uom_id} not found'
    else:
        uom = product.uom_id

    warehouse = request.env['stock.warehouse'].browse(int(warehouse_id))
    if not warehouse.exists():
        return f'Warehouse {warehouse_id} not found'

    # Default location to the main stock location of the warehouse
    location_id = data.get('location_id')
    if location_id:
        location_id = int(location_id)
    else:
        location_id = warehouse.lot_stock_id.id if warehouse.lot_stock_id else False

    return {
        'product_id': product.id,
        'product_uom_id': uom.id,
        'warehouse_id': warehouse.id,
        'location_id': location_id,
        'quantity': float(data.get('quantity', 1.0)),
        'unit_price': float(data.get('unit_price', product.list_price)),
        'discount_percent': float(data.get('discount_percent', 0.0)),
        'custom_product_name': data.get('custom_product_name') or False,
        'sequence': int(data.get('sequence', 10)),
    }
