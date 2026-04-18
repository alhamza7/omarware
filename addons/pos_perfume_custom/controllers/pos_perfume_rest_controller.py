# -*- coding: utf-8 -*-
"""REST API `/api/pos_perfume/v1/*` for external SPAs (Bearer optional; session `auth='user'`)."""
import json
import logging
import re
from datetime import timedelta

from odoo import fields, http
from odoo.http import request, Response

from .pos_perfume_controller import PosPerfumeController

_logger = logging.getLogger(__name__)

_PREFIX = "/api/pos_perfume/v1"
# Some frontends issue POST instead of GET; allow both on read-only endpoints.
_READ = ("GET", "POST")


def _json(data, status=200):
    body = json.dumps(data, ensure_ascii=False, default=str)
    return Response(
        body,
        status=status,
        headers=[("Content-Type", "application/json; charset=utf-8")],
    )


class PosPerfumeRestController(http.Controller):
    """JSON envelope: {success, message?, data?, error?} — matches `44/src/services/posPerfumeApi.ts`."""

    def _ok(self, data, message="OK"):
        return _json({"success": True, "message": message, "data": data})

    def _fail(self, error, status=400):
        return _json({"success": False, "error": error, "data": None}, status=status)

    def _pos_rest_auth(self):
        """Session cookie, ``Bearer`` JWT (lugal_auth), or ``Bearer`` API key (rpc scope).

        With ``auth='none'``, Odoo does not bind ``request.env`` to ``session.uid`` automatically.
        Without ``update_env``, ``request.env.user`` is empty and ORM ``search()`` raises
        ``ValueError: Expected singleton: res.users()`` during access checks.
        """
        session_uid = getattr(request.session, "uid", None)
        if session_uid:
            request.update_env(user=session_uid)
            if request.env.user and request.env.user.exists():
                return True
        auth = (request.httprequest.headers.get("Authorization") or "").strip()
        if not auth.lower().startswith("bearer "):
            return False
        token = auth[7:].strip()
        if not token:
            return False
        try:
            from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

            jwt_uid = ensure_jwt_user_id()
            if jwt_uid:
                return True
        except Exception:
            pass
        uid = request.env["res.users.apikeys"].sudo()._check_credentials(scope="rpc", key=token)
        if not uid:
            return False
        request.update_env(user=uid)
        if not request.env.user or not request.env.user.exists():
            return False
        return True

    def _rest_pos_ui_default_pricelist(self):
        """
        Same default as Odoo POS screen ``loadPricelists()`` (pos_perfume_screen.js):
        active pricelists ordered by id asc; prefer name containing ``list 1`` (case-insensitive);
        if several, pick the one with the most pricelist items where fixed_price > 0;
        otherwise first active pricelist (lowest id).
        """
        Pl = request.env["product.pricelist"].sudo()
        Item = request.env["product.pricelist.item"].sudo()
        pricelists = Pl.search([("active", "=", True)], order="id asc", limit=100)
        if not pricelists:
            return Pl.browse()
        candidates = pricelists.filtered(
            lambda p: p.name and "list 1" in p.name.lower()
        )
        chosen = Pl.browse()
        if len(candidates) == 1:
            chosen = candidates
        elif len(candidates) > 1:
            best = candidates[0]
            best_n = Item.search_count(
                [("pricelist_id", "=", best.id), ("fixed_price", ">", 0)]
            )
            for p in candidates[1:]:
                n = Item.search_count(
                    [("pricelist_id", "=", p.id), ("fixed_price", ">", 0)]
                )
                if n > best_n:
                    best = p
                    best_n = n
            chosen = best
        if not chosen:
            chosen = pricelists[:1]
        return chosen

    def _rest_default_pricelist(self):
        """Pricelist used by REST catalog when ``pricelist_id`` is omitted — matches POS UI."""
        return self._rest_pos_ui_default_pricelist()

    def _rest_price_uom(self, product, get_arg):
        """UoM used for pricing: uom_id / uom query params, else product.uom_id."""
        uid = get_arg("uom_id")
        if uid:
            try:
                u = request.env["uom.uom"].sudo().browse(int(uid))
                if u.exists():
                    return u
            except (TypeError, ValueError):
                pass
        raw = (get_arg("uom") or "").strip()
        if not raw:
            return product.uom_id
        Uom = request.env["uom.uom"].sudo()
        u = Uom.search([("name", "ilike", raw)], limit=1)
        if u:
            return u
        low = raw.lower()
        if low in ("kg", "kilo", "kilogram", "kgs"):
            u = Uom.search(
                ["|", "|", ("name", "ilike", "كغم"), ("name", "ilike", "كيلو"), ("name", "ilike", "KG")],
                limit=1,
            )
            if u:
                return u
        if low in ("g", "gram", "grams"):
            u = Uom.search(["|", ("name", "ilike", "غرام"), ("name", "ilike", "gram")], limit=1)
            if u:
                return u
        return product.uom_id

    def _rest_price_first_applicable_rule(self, product, pl_rec, price_uom, quantity=1.0):
        """Same rule chain as product.pricelist._compute_price_rule (incl. category / global lines)."""
        if not pl_rec or not product:
            return 0.0
        pu = price_uom or product.uom_id
        if not pu:
            return 0.0
        date = fields.Datetime.now()
        cur = pl_rec.currency_id
        product_uom = product.uom_id
        if pu != product_uom:
            qty_in_product_uom = pu._compute_quantity(
                quantity, product_uom, raise_if_failure=False
            )
            if qty_in_product_uom is False:
                qty_in_product_uom = quantity
        else:
            qty_in_product_uom = quantity
        rules = pl_rec._get_applicable_rules(product, date)
        for rule in rules:
            if not rule._is_applicable_for(product, qty_in_product_uom):
                continue
            try:
                return float(
                    rule._compute_price(product, quantity, pu, date=date, currency=cur)
                )
            except Exception:
                continue
        return 0.0

    def _rest_product_unit_price(self, product, pl_rec, price_uom):
        """
        Match ``product.product.search_products_for_pos`` (right panel): use Odoo
        ``pricelist._get_product_price`` first on sudo records so API users without
        ``product.pricelist.item`` read rights still get the same numbers as the UI.

        Then fall back to POS UoM-group / packaging mapping (``get_product_data`` path)
        and rule chain when the standard engine returns 0.
        """
        prod = product.sudo()
        pu = price_uom or prod.uom_id
        pl = pl_rec.sudo() if pl_rec else False
        company_partner = request.env.company.sudo().partner_id

        if pl:
            try:
                p = pl._get_product_price(prod, 1.0, uom=pu)
                if p and p > 0:
                    return float(p)
            except TypeError:
                pass
            except Exception as ex:
                _logger.debug("REST _get_product_price: %s", ex)
            try:
                p = pl._get_product_price(prod, 1.0, uom=pu, partner=company_partner)
                if p and p > 0:
                    return float(p)
            except Exception as ex:
                _logger.debug("REST _get_product_price (partner): %s", ex)

        ctrl = PosPerfumeController()
        uoms = ctrl._get_uoms_from_pricelist(prod, pl)
        target_id = pu.id if pu else None
        price = ctrl._get_default_price_from_uoms(uoms, target_id)
        if price and price > 0:
            return float(price)

        price = self._rest_price_first_applicable_rule(prod, pl, pu)
        if price and price > 0:
            return float(price)
        if pu and prod.uom_id and pu.id != prod.uom_id.id:
            price = self._rest_price_first_applicable_rule(prod, pl, prod.uom_id)
            if price and price > 0:
                return float(price)

        if pl:
            try:
                p = pl._get_product_price(prod, 1.0, uom=pu, partner=company_partner)
                if p and p > 0:
                    return float(p)
            except TypeError:
                pass
            except Exception as ex:
                _logger.debug("REST late _get_product_price (partner): %s", ex)
            try:
                p = pl._get_product_price(prod, 1.0, uom=pu)
                if p and p > 0:
                    return float(p)
            except Exception as ex:
                _logger.debug("REST late _get_product_price: %s", ex)

        return float(prod.list_price or 0.0)

    def _strict_pricelist_flag(self, get_arg):
        v = (get_arg("strict_pricelist") or "").strip().lower()
        return v in ("1", "true", "yes", "on")

    def _rest_catalog_unit_price(self, product, pl_rec, price_uom, strict=False):
        """
        Catalog price: use ``pl_rec``; if price is 0 and not ``strict``, retry once with
        the POS UI default pricelist when it is a different record (mirrors omitting
        ``pricelist_id`` so ``pricelist_id=1`` does not stick on "Default" with no rules).
        Returns ``(price, pricelist_id_used)``; ``pricelist_id_used`` is None if ``pl_rec`` is empty.
        """
        if not pl_rec:
            p = self._rest_product_unit_price(product, pl_rec, price_uom)
            return float(p or 0.0), None
        p = float(self._rest_product_unit_price(product, pl_rec, price_uom) or 0.0)
        used_id = pl_rec.id
        if strict or p > 0:
            return p, used_id
        alt = self._rest_default_pricelist()
        if alt and alt.id != pl_rec.id:
            p2 = float(self._rest_product_unit_price(product, alt, price_uom) or 0.0)
            if p2 > 0:
                return p2, alt.id
        return p, used_id

    def _rest_foreign_name(self, prod):
        fn = getattr(prod, "foreign_name", None) or ""
        if not fn and prod.product_tmpl_id:
            fn = getattr(prod.product_tmpl_id, "foreign_name", None) or ""
        return fn or ""

    def _rest_category_type_payload(self, prod, ext):
        """Shape used by the development mobile catalog (fragrances + properties)."""
        cap = ((ext.capacity or "").strip()) if ext else ""
        size_ml = None
        if cap:
            m = re.search(r"(\d+(?:\.\d+)?)\s*ML", cap.upper())
            if m:
                try:
                    size_ml = float(m.group(1))
                except ValueError:
                    pass
        size_kg = None
        if cap:
            m2 = re.search(r"(\d+(?:\.\d+)?)\s*KG", cap.upper())
            if m2:
                try:
                    size_kg = float(m2.group(1))
                except ValueError:
                    pass
        is_bulk = False
        if prod.uom_id:
            un = (prod.uom_id.name or "").lower()
            is_bulk = ("كغم" in un or "kg" in un or "كيلو" in un) and (prod.uom_id.factor or 0) >= 0.5
        gender = "Unisex"
        if ext and ext.sap_classification_1:
            g = (ext.sap_classification_1 or "").lower()
            if any(x in g for x in ("men", "رجال", "male", "man")):
                gender = "Men"
            elif any(x in g for x in ("women", "نساء", "female", "ladies", "woman")):
                gender = "Women"
        return {
            "type": "fragrances",
            "name": "Fragrances",
            "name_ar": "عطور",
            "properties": {
                "size_ml": size_ml,
                "size_kg": size_kg,
                "is_bulk": is_bulk,
                "concentration": (ext.sap_classification_2 if ext else None) or None,
                "gender": gender,
                "season": None,
                "longevity": None,
                "sillage": None,
            },
        }

    def _rest_product_catalog_row(self, prod, pl_rec, price_uom, strict_pl, pl_used_id):
        """
        One product record matching the legacy **development** catalog JSON shape
        (rich UoMs, warehouses, brand, category_type, has_price, etc.).

        ``list_price`` prefers the **pricelist-resolved** unit price (same as the slim
        API clients already use); if that is zero, falls back to Odoo ``lst_price``.
        """
        catalog_price, priced_pl_id = self._rest_catalog_unit_price(
            prod, pl_rec, price_uom, strict=strict_pl
        )
        Pl = request.env["product.pricelist"].sudo()
        pl_uom = pl_rec
        if priced_pl_id:
            cand = Pl.browse(priced_pl_id).exists()
            if cand:
                pl_uom = cand

        ctrl = PosPerfumeController()
        raw_uoms = ctrl._get_uoms_from_pricelist(prod, pl_uom)
        available_uoms = [
            {"id": u["id"], "name": u["name"], "price": float(u.get("price") or 0.0)}
            for u in raw_uoms
        ]

        lst_odoo = float(prod.lst_price or 0.0)
        cat = float(catalog_price or 0.0)
        list_price = cat if cat > 0 else lst_odoo
        has_price = bool(list_price > 0) or any(
            (u.get("price") or 0) > 0 for u in available_uoms
        )

        warehouses = ctrl._get_warehouses_simple(prod.id)
        foreign_name = self._rest_foreign_name(prod)
        _, color_class, badge_text = prod._get_product_priority_and_color(prod.default_code)
        categ_name = prod.categ_id.name if prod.categ_id else ""
        brand = {
            "key": color_class or "",
            "name": categ_name,
            "code": badge_text or "",
        }

        ext = False
        if "sap.product.extended" in request.env:
            ext = request.env["sap.product.extended"].sudo().search(
                [("product_id", "=", prod.id)], limit=1
            )
        items_group_code = int(ext.items_group_code or 0) if ext else 0
        items_group_name = (ext.items_group_name or "") if ext else ""

        category_type = self._rest_category_type_payload(prod, ext)

        created_at = prod.create_date.isoformat() if prod.create_date else None
        is_new = False
        if prod.create_date:
            is_new = (fields.Datetime.now() - prod.create_date) <= timedelta(days=45)

        pu = price_uom or prod.uom_id
        uom_payload = {"id": pu.id, "name": pu.name or ""} if pu else {"id": None, "name": ""}
        categ_payload = (
            {"id": prod.categ_id.id, "name": prod.categ_id.name or ""}
            if prod.categ_id
            else {"id": None, "name": ""}
        )

        row = {
            "id": prod.id,
            "name": prod.name or "",
            "default_code": prod.default_code or "",
            "foreign_name": foreign_name,
            "uom_id": uom_payload,
            "uom_name": (pu.name or "") if pu else "",
            "list_price": list_price,
            "qty_available": float(prod.qty_available),
            "color_class": color_class or "",
            "badge_text": badge_text or "",
            "active": bool(prod.active),
            "sale_ok": bool(prod.sale_ok),
            "categ_id": categ_payload,
            "items_group_code": items_group_code,
            "items_group_name": items_group_name,
            "brand": brand,
            "category_type": category_type,
            "available_uoms": available_uoms,
            "has_price": has_price,
            "warehouses": warehouses,
            "created_at": created_at,
            "is_new": is_new,
        }
        if (
            priced_pl_id is not None
            and pl_used_id is not None
            and priced_pl_id != pl_used_id
        ):
            row["priced_pricelist_id"] = priced_pl_id
        return row

    def _rest_products_query_params(self):
        """Merge query string with optional JSON body (POST) for SPA clients."""
        args = request.httprequest.args
        extra = {}
        if request.httprequest.method == "POST" and (request.httprequest.data or b"").strip():
            try:
                extra = json.loads(request.httprequest.data.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                extra = {}
        if not isinstance(extra, dict):
            extra = {}

        def pget(key, default=None):
            v = extra.get(key)
            if v is not None and v != "":
                return v
            return args.get(key, default)

        return pget

    def _rest_query_bool(self, pget, key, default=False):
        v = pget(key)
        if v is None or v == "":
            return default
        s = str(v).strip().lower()
        return s in ("1", "true", "yes", "on")

    def _rest_int_param(self, pget, key, default=None):
        """Parse integer query param; ``default`` when missing or blank."""
        v = pget(key)
        if v is None or v == "":
            return default
        try:
            return int(v)
        except (TypeError, ValueError):
            return default

    _REST_BRAND_ALIASES = {
        "robertet": "royal",
        "amour_de_fleurs": "adf",
        "euro": "european",
    }

    _REST_CATEGORY_TYPE_HINTS = {
        "fragrances": ("عطر", "frag", "perfume", "parfum", "givaudan", "robertet", "essence"),
        "glass": ("زجاج", "glass", "crystal"),
        "samples": ("عينه", "sample", "samples"),
        "pack": ("pack", "set", "طقم"),
        "packaging": ("علب", "packaging", "box", "كرتون", "carton"),
        "alcohol": ("كحول", "alcohol"),
        "accessories": ("اكسسو", "accessory"),
        "devices": ("جهاز", "device"),
        "incense": ("بخور", "incense"),
    }

    def _rest_product_matches_brand_param(self, prod, brand_raw):
        """Align with POS screen brand rules (prefix / special cases)."""
        if not brand_raw:
            return True
        b = str(brand_raw).strip().lower()
        b = self._REST_BRAND_ALIASES.get(b, b)
        sku = (prod.default_code or "").upper()
        name = (prod.name or "").upper()
        if b in ("adf",):
            return sku.startswith("ADF")
        if b in ("royal", "roy"):
            return (
                (sku.startswith("R") and not sku.startswith("ADF") and not sku.startswith("G") and not sku.startswith("EURO"))
                or sku.startswith("ROYAL")
                or sku.startswith("ROY")
            )
        if b in ("givaudan", "giv"):
            return (
                (sku.startswith("G") and not sku.startswith("ADF") and not sku.startswith("R") and not sku.startswith("EURO"))
                or sku.startswith("GIVAUDAN")
                or sku.startswith("GIV")
            )
        if b in ("european", "euro"):
            return "N1" in sku or sku.startswith("EURO") or "EURO" in name
        if b in ("florchem", "fl"):
            return "FLOR" in name or sku.startswith("FL")
        prefix = b.replace(" ", "_").upper()
        return sku.startswith(prefix) or name.startswith(prefix)

    def _rest_product_matches_category_type_param(self, prod, cat_raw):
        """Loose match on category path + product name (no strict SAP taxonomy)."""
        if not cat_raw:
            return True
        k = str(cat_raw).strip().lower()
        hints = self._REST_CATEGORY_TYPE_HINTS.get(k)
        if not hints:
            return True
        hay = " ".join(
            [
                (prod.categ_id.complete_name or "") if prod.categ_id else "",
                prod.name or "",
            ]
        ).lower()
        return any(h.lower() in hay for h in hints)

    def _rest_products_domain_item_codes(self, domain, Product, pget):
        raw = pget("item_codes")
        if not raw:
            return domain
        if isinstance(raw, (list, tuple)):
            codes = [str(x).strip() for x in raw if str(x).strip()][:500]
        else:
            codes = [s.strip() for s in str(raw).split(",") if s.strip()][:500]
        if not codes:
            return domain
        return ["&"] + domain + [("default_code", "in", codes)]

    # --- bootstrap ---------------------------------------------------------

    @http.route(f"{_PREFIX}/sections", type="http", auth="none", methods=list(_READ), csrf=False, cors="*")
    def sections(self, **kwargs):
        """UI navigation sections (static); extend if the app expects more keys."""
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        items = [
            {"id": "pos", "key": "pos", "label": "POS"},
            {"id": "orders", "key": "orders", "label": "Orders"},
            {"id": "catalog", "key": "catalog", "label": "Catalog"},
        ]
        return self._ok({"items": items, "total": len(items)})

    @http.route(f"{_PREFIX}/categories", type="http", auth="none", methods=list(_READ), csrf=False, cors="*")
    def categories(self, **kwargs):
        """Product categories (`product.category`) for POS / CRM lists."""
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        Category = request.env["product.category"]
        recs = Category.search([], order="complete_name")
        items = [
            {
                "id": c.id,
                "name": c.name,
                "parent_id": c.parent_id.id or None,
                "complete_name": c.complete_name,
            }
            for c in recs
        ]
        return self._ok({"items": items, "total": len(items)})

    @http.route(f"{_PREFIX}/session", type="http", auth="none", methods=list(_READ), csrf=False, cors="*")
    def session_info(self, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        u = request.env.user
        rate = request.env["pos.perfume.order"].sudo().get_exchange_rate_from_db()
        return self._ok(
            {
                "user_id": u.id,
                "user_name": u.name,
                "user_login": u.login,
                "company_id": u.company_id.id,
                "company_name": u.company_id.name,
                "uid": u.id,
                "exchange_rate": float(rate) if rate is not None else 0.0,
            }
        )

    @http.route(f"{_PREFIX}/setup", type="http", auth="none", methods=list(_READ), csrf=False, cors="*")
    def setup(self, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        env = request.env
        pls = env["product.pricelist"].search([("active", "=", True)], order="id asc", limit=100)
        whs = env["stock.warehouse"].search([])
        users = env["res.users"].search([("share", "=", False), ("active", "=", True)])
        sel = env["pos.perfume.order"]._fields["invoice_type"].selection
        if callable(sel):
            sel = sel(env["pos.perfume.order"])
        invoice_types = [{"key": k, "label": v} for k, v in sel]
        rate = env["pos.perfume.order"].sudo().get_exchange_rate_from_db()
        default_pl = self._rest_pos_ui_default_pricelist()
        return self._ok(
            {
                "pricelists": [{"id": p.id, "name": p.name, "currency_id": p.currency_id.id} for p in pls],
                "default_pricelist_id": default_pl.id if default_pl else None,
                "warehouses": [{"id": w.id, "name": w.name, "code": w.code or ""} for w in whs],
                "users": [{"id": u.id, "name": u.name} for u in users],
                "invoice_types": invoice_types,
                "exchange_rate": float(rate) if rate is not None else 0.0,
                "currency": "USD",
                "secondary_currency": "IQD",
            }
        )

    @http.route(
        f"{_PREFIX}/settings",
        type="http",
        auth="none",
        methods=["GET", "PUT", "POST"],
        csrf=False,
        cors="*",
    )
    def settings(self, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        ICP = request.env["ir.config_parameter"].sudo()
        param_key = "pos_perfume.default_exchange_rate_usd_iqd"
        method = request.httprequest.method
        body = {}
        if request.httprequest.data:
            try:
                body = json.loads(request.httprequest.data.decode("utf-8") or "{}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                body = {}
        update = method == "PUT" or (method == "POST" and "exchange_rate" in body)
        if not update:
            raw = ICP.get_param(param_key, "0")
            try:
                rate = float(raw)
            except (TypeError, ValueError):
                rate = 0.0
            return self._ok({"exchange_rate": rate})
        rate = body.get("exchange_rate")
        if rate is None:
            return self._fail("exchange_rate required", 400)
        try:
            rate_f = float(rate)
        except (TypeError, ValueError):
            return self._fail("exchange_rate must be a number", 400)
        ICP.set_param(param_key, str(rate_f))
        return self._ok({"exchange_rate": rate_f})

    @http.route(f"{_PREFIX}/pricelists", type="http", auth="none", methods=list(_READ), csrf=False, cors="*")
    def pricelists(self, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        pls = request.env["product.pricelist"].search(
            [("active", "=", True)], order="id asc", limit=100
        )
        default_pl = self._rest_pos_ui_default_pricelist()
        items = [
            {
                "id": p.id,
                "name": p.name,
                "currency_id": p.currency_id.id,
                "currency_name": p.currency_id.name,
            }
            for p in pls
        ]
        return self._ok(
            {
                "items": items,
                "total": len(items),
                "default_pricelist_id": default_pl.id if default_pl else None,
            }
        )

    @http.route(f"{_PREFIX}/warehouses", type="http", auth="none", methods=list(_READ), csrf=False, cors="*")
    def warehouses(self, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        whs = request.env["stock.warehouse"].search([])
        items = [{"id": w.id, "name": w.name, "code": w.code or ""} for w in whs]
        return self._ok({"items": items, "total": len(items)})

    # --- customers ---------------------------------------------------------

    @http.route(f"{_PREFIX}/customers", type="http", auth="none", methods=["GET", "POST"], csrf=False, cors="*")
    def customers(self, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        Partner = request.env["res.partner"]
        if request.httprequest.method == "GET":
            q = request.httprequest.args.get("query") or ""
            limit = min(int(request.httprequest.args.get("limit") or 80), 500)
            offset = int(request.httprequest.args.get("offset") or 0)
            domain = [("customer_rank", ">", 0), ("active", "=", True)]
            if q:
                domain = ["&"] + domain + ["|", "|", ("name", "ilike", q), ("email", "ilike", q), ("phone", "ilike", q)]
            total = Partner.search_count(domain)
            recs = Partner.search(domain, limit=limit, offset=offset, order="name")
            items = [
                {
                    "id": p.id,
                    "name": p.name,
                    "email": p.email or "",
                    "phone": p.phone or p.mobile or "",
                    "street": p.street or "",
                    "city": p.city or "",
                    "country_id": p.country_id.id or None,
                }
                for p in recs
            ]
            return self._ok({"items": items, "total": total})
        body = json.loads(request.httprequest.data.decode("utf-8") or "{}")
        vals = {
            "name": body.get("name") or "Customer",
            "email": body.get("email"),
            "phone": body.get("phone"),
            "street": body.get("street"),
            "city": body.get("city"),
            "customer_rank": 1,
        }
        vals = {k: v for k, v in vals.items() if v is not None}
        p = Partner.create(vals)
        return self._ok(
            {
                "id": p.id,
                "name": p.name,
                "email": p.email or "",
                "phone": p.phone or p.mobile or "",
                "street": p.street or "",
                "city": p.city or "",
                "country_id": p.country_id.id or None,
            }
        )

    @http.route(
        f"{_PREFIX}/customers/<int:partner_id>",
        type="http",
        auth="none",
        methods=["GET", "PUT"],
        csrf=False,
        cors="*",
    )
    def customer_one(self, partner_id, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        p = request.env["res.partner"].browse(partner_id).exists()
        if not p:
            return self._fail("Customer not found", 404)
        if request.httprequest.method == "GET":
            return self._ok(
                {
                    "id": p.id,
                    "name": p.name,
                    "email": p.email or "",
                    "phone": p.phone or p.mobile or "",
                    "street": p.street or "",
                    "city": p.city or "",
                    "country_id": p.country_id.id or None,
                }
            )
        body = json.loads(request.httprequest.data.decode("utf-8") or "{}")
        p.write({k: body[k] for k in ("name", "email", "phone", "street", "city") if k in body})
        return self._ok(
            {
                "id": p.id,
                "name": p.name,
                "email": p.email or "",
                "phone": p.phone or p.mobile or "",
                "street": p.street or "",
                "city": p.city or "",
                "country_id": p.country_id.id or None,
            }
        )

    # --- products ----------------------------------------------------------

    @http.route(f"{_PREFIX}/products", type="http", auth="none", methods=list(_READ), csrf=False, cors="*")
    def products(self, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        Product = request.env["product.product"].sudo()
        pget = self._rest_products_query_params()
        q = (pget("query") or "").strip()

        lim_raw = self._rest_int_param(pget, "limit", None)
        if lim_raw is None:
            lim_raw = 80
        fetch_all = self._rest_query_bool(pget, "fetch_all", False) or lim_raw == 0
        if fetch_all:
            limit = None
        else:
            limit = max(int(lim_raw), 1)
        offset = max(self._rest_int_param(pget, "offset", 0) or 0, 0)

        pl_id = pget("pricelist_id")
        domain = []
        if not self._rest_query_bool(pget, "include_inactive", False):
            domain.append(("active", "=", True))
        if not self._rest_query_bool(pget, "include_non_sale", False):
            domain.append(("sale_ok", "=", True))

        if q:
            or_terms = [
                ("name", "ilike", q),
                ("default_code", "ilike", q),
                ("barcode", "ilike", q),
            ]
            if "foreign_name" in Product._fields:
                or_terms.append(("foreign_name", "ilike", q))
            domain = ["&"] + domain + (["|"] * (len(or_terms) - 1)) + or_terms

        categ_raw = pget("categ_id") or pget("category_id")
        if categ_raw:
            try:
                cid = int(categ_raw)
            except (TypeError, ValueError):
                cid = None
            if cid is not None:
                Cat = request.env["product.category"].sudo().with_context(active_test=False)
                root = Cat.browse(cid)
                if not root.exists():
                    return self._fail(
                        "Unknown product category for categ_id / category_id.",
                        404,
                    )
                subtree = Cat.search([("id", "child_of", root.ids)])
                domain = ["&"] + domain + [("categ_id", "in", subtree.ids)]

        domain = self._rest_products_domain_item_codes(domain, Product, pget)
        pref = (pget("default_code_prefix") or "").strip()
        if pref:
            if not pref.endswith("%"):
                pref = pref + "%"
            domain = ["&"] + domain + [("default_code", "ilike", pref)]

        brand_raw = (pget("brand") or "").strip()
        cat_type_raw = (pget("category_type") or "").strip()
        has_price_only = self._rest_query_bool(pget, "has_price_only", False) or str(
            pget("has_price_only") or ""
        ).strip() == "1"
        use_python_filters = bool(brand_raw or cat_type_raw or has_price_only)

        pl_rec = False
        if pl_id:
            try:
                pl_rec = request.env["product.pricelist"].sudo().browse(int(pl_id)).exists()
            except (TypeError, ValueError):
                pl_rec = False
        if not pl_rec:
            pl_rec = self._rest_default_pricelist()
        pl_used_id = pl_rec.id if pl_rec else None
        strict_pl = self._strict_pricelist_flag(pget)

        def _rows_for_products(prod_recs):
            out = []
            for prod in prod_recs:
                price_uom = self._rest_price_uom(prod, pget)
                row = self._rest_product_catalog_row(
                    prod, pl_rec, price_uom, strict_pl, pl_used_id
                )
                out.append(row)
            return out

        if use_python_filters:
            all_recs = Product.search(domain, order="name")
            seq_prods = []
            for prod in all_recs:
                if brand_raw and not self._rest_product_matches_brand_param(prod, brand_raw):
                    continue
                if cat_type_raw and not self._rest_product_matches_category_type_param(
                    prod, cat_type_raw
                ):
                    continue
                seq_prods.append(prod)
            rows = _rows_for_products(seq_prods)
            if has_price_only:
                rows = [r for r in rows if r.get("has_price")]
            total = len(rows)
            if limit is None:
                items = rows
                offset_out = 0
                limit_out = 0
            else:
                items = rows[offset : offset + limit]
                offset_out = offset
                limit_out = limit
        else:
            total = Product.search_count(domain)
            if limit is None:
                recs = Product.search(domain, order="name")
                items = _rows_for_products(recs)
                offset_out = 0
                limit_out = 0
            else:
                recs = Product.search(domain, limit=limit, offset=offset, order="name")
                items = _rows_for_products(recs)
                offset_out = offset
                limit_out = limit

        return self._ok(
            {
                "items": items,
                "total": total,
                "offset": offset_out,
                "limit": limit_out,
                "returned": len(items),
                "fetch_all": bool(limit is None),
                "pricelist_id": pl_used_id,
            }
        )

    @http.route(
        f"{_PREFIX}/products/<int:product_id>",
        type="http",
        auth="none",
        methods=list(_READ),
        csrf=False,
        cors="*",
    )
    def product_one(self, product_id, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        prod = request.env["product.product"].sudo().browse(product_id).exists()
        if not prod:
            return self._fail("Product not found", 404)
        pget = self._rest_products_query_params()
        pl_id = pget("pricelist_id")
        pl_rec = False
        if pl_id:
            try:
                pl_rec = request.env["product.pricelist"].sudo().browse(int(pl_id)).exists()
            except (TypeError, ValueError):
                pl_rec = False
        if not pl_rec:
            pl_rec = self._rest_default_pricelist()
        price_uom = self._rest_price_uom(prod, pget)
        strict_pl = self._strict_pricelist_flag(pget)
        pl_used_id = pl_rec.id if pl_rec else None
        payload = self._rest_product_catalog_row(
            prod, pl_rec, price_uom, strict_pl, pl_used_id
        )
        return self._ok(payload)

    @http.route(f"{_PREFIX}/products/data", type="http", auth="none", methods=["POST"], csrf=False, cors="*")
    def product_data(self, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        body = json.loads(request.httprequest.data.decode("utf-8") or "{}")
        pid = body.get("product_id")
        if not pid:
            return self._fail("product_id required", 400)
        ctrl = PosPerfumeController()
        res = ctrl.get_product_data(
            int(pid),
            body.get("pricelist_id"),
            body.get("uom_id"),
            body.get("warehouse_id"),
        )
        if isinstance(res, dict) and res.get("success") and "data" in res:
            return self._ok(res["data"])
        if isinstance(res, dict) and res.get("success") is False:
            return self._fail(res.get("error") or "Product data failed", 400)
        return self._ok(res)

    @http.route(f"{_PREFIX}/products/uom_price", type="http", auth="none", methods=["POST"], csrf=False, cors="*")
    def uom_price(self, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        body = json.loads(request.httprequest.data.decode("utf-8") or "{}")
        ctrl = PosPerfumeController()
        res = ctrl.get_product_data(
            int(body.get("product_id") or 0),
            body.get("pricelist_id"),
            body.get("uom_id"),
            body.get("warehouse_id"),
        )
        if not isinstance(res, dict) or not res.get("success"):
            return self._fail(res.get("error") if isinstance(res, dict) else "Failed", 400)
        data = res.get("data") or {}
        uom_id = int(body.get("uom_id") or 0)
        price = data.get("price_unit") or 0.0
        for row in data.get("available_uoms") or []:
            if row.get("id") == uom_id:
                price = row.get("price") or price
                break
        return self._ok({"price_unit": float(price)})

    # --- orders (read list + minimal write stubs) --------------------------

    @http.route(f"{_PREFIX}/orders", type="http", auth="none", methods=["GET", "POST"], csrf=False, cors="*")
    def orders(self, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        Order = request.env["pos.perfume.order"]
        if request.httprequest.method == "GET":
            limit = min(int(request.httprequest.args.get("limit") or 80), 500)
            offset = int(request.httprequest.args.get("offset") or 0)
            domain = []
            st = request.httprequest.args.get("state")
            if st:
                domain.append(("state", "=", st))
            if request.httprequest.args.get("partner_id"):
                try:
                    domain.append(("partner_id", "=", int(request.httprequest.args.get("partner_id"))))
                except ValueError:
                    pass
            total = Order.search_count(domain)
            recs = Order.search(domain, limit=limit, offset=offset, order="id desc")
            items = [
                {
                    "id": o.id,
                    "name": o.name,
                    "partner_id": o.partner_id.id,
                    "partner_name": o.partner_id.name,
                    "state": o.state,
                    "amount_total": o.amount_total,
                    "date_order": o.date.isoformat() if getattr(o, "date", None) else None,
                }
                for o in recs
            ]
            return self._ok({"items": items, "total": total})
        return self._fail("Create order via Odoo POS UI or extend this endpoint", 501)

    @http.route(
        f"{_PREFIX}/orders/<int:order_id>",
        type="http",
        auth="none",
        methods=["GET", "PUT", "DELETE"],
        csrf=False,
        cors="*",
    )
    def order_one(self, order_id, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        o = request.env["pos.perfume.order"].browse(order_id).exists()
        if not o:
            return self._fail("Order not found", 404)
        method = request.httprequest.method
        if method == "GET":
            lines = []
            for ln in o.order_line_ids:
                lines.append(
                    {
                        "id": ln.id,
                        "product_id": ln.product_id.id,
                        "product_name": ln.product_id.name,
                        "product_uom_qty": ln.quantity,
                        "price_unit": ln.unit_price,
                    }
                )
            return self._ok(
                {
                    "id": o.id,
                    "name": o.name,
                    "partner_id": o.partner_id.id,
                    "state": o.state,
                    "amount_total": o.amount_total,
                    "order_line_ids": lines,
                    "invoice_type": o.invoice_type,
                    "note": o.note or "",
                }
            )
        if method == "DELETE":
            o.write({"state": "cancel"})
            return self._ok({"id": o.id, "state": "cancel"})
        return self._fail("PUT order: use Odoo or extend endpoint", 501)
