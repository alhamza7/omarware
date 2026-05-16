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

    def _rest_uom_sales_touch_count(self, uom_rec):
        """How strongly a UoM is used for saleable catalog (templates + SAP sales UoM)."""
        env = request.env
        Pt = env["product.template"].sudo()
        n = Pt.search_count(
            [
                ("uom_id", "=", uom_rec.id),
                ("sale_ok", "=", True),
                ("active", "=", True),
            ]
        )
        if "sap.product.extended" in env:
            n += env["sap.product.extended"].sudo().search_count(
                [("sales_uom_id", "=", uom_rec.id)]
            )
        return n

    def _rest_pick_base_mass_uom(self, Uom, low: str):
        """
        Map ``uom=kg`` / kilo synonyms to a **base** kilogram UoM.

        A naive ``name ilike 'kg'`` can hit ``uom`` id 15 (English ``kg``) first while the
        catalog uses Arabic **كغم** (e.g. id 34); the SAP-aligned id filter then returns
        **zero** rows. We rank candidates so exact ``كغم`` / ``kg`` beats ``500 كغم``, etc.
        """
        if low not in ("kg", "kilo", "kilogram", "kgs"):
            return Uom.browse()
        cand = Uom.search(
            [
                ("active", "=", True),
                "|",
                "|",
                ("name", "ilike", "كغم"),
                ("name", "ilike", "كيلو"),
                ("name", "ilike", "KG"),
            ]
        )

        def _texts(rec):
            n = rec.name
            if isinstance(n, dict):
                for v in n.values():
                    if v:
                        yield str(v).strip().lower()
            elif n:
                yield str(n).strip().lower()

        def _score(rec):
            best = 99
            for t in _texts(rec):
                if t in ("كغم", "kg", "kgs", "kilogram", "kilograms", "kilo"):
                    best = min(best, 0)
                elif any(x in t for x in ("0.25", "500", "1000", "250", "100")):
                    best = min(best, 30)
                elif "كغم" in t:
                    best = min(best, 10)
                elif "kg" in t:
                    best = min(best, 5)
            return best

        def _sort_key(rec):
            """Among equal scores prefer Arabic **كغم** over ASCII-only ``kg`` (DB bulk default)."""
            sc = _score(rec)
            texts = list(_texts(rec))
            has_ar = any("كغم" in t for t in texts)
            return (sc, 0 if has_ar else 1, rec.id)

        if not cand:
            return Uom.browse()
        ranked = sorted(
            cand,
            key=lambda r: (_sort_key(r), -self._rest_uom_sales_touch_count(r), r.id),
        )
        return Uom.browse(ranked[0].id)

    def _rest_price_uom(self, product, get_arg):
        """UoM used for pricing: uom_id / uom query params, else product.uom_id."""
        uid = get_arg("uom_id")
        if uid:
            try:
                u = request.env["uom.uom"].sudo().browse(int(uid))
                if u.exists() and u.active:
                    return u
            except (TypeError, ValueError):
                pass
        raw = (get_arg("uom") or "").strip()
        if not raw:
            return product.uom_id
        low = raw.lower()
        Uom = request.env["uom.uom"].sudo()
        u = self._rest_pick_base_mass_uom(Uom, low)
        if u:
            return u
        if low in ("g", "gram", "grams"):
            u = Uom.search(
                [
                    ("active", "=", True),
                    "|",
                    ("name", "ilike", "غرام"),
                    ("name", "ilike", "gram"),
                ],
                limit=1,
            )
            if u:
                return u
        u = Uom.search([("active", "=", True), ("name", "ilike", raw)], limit=1)
        if u:
            return u
        return product.uom_id

    def _rest_resolve_catalog_uom(self, pget):
        """Resolve ``uom`` / ``uom_id`` query keys to ``uom.uom`` (no product fallback)."""
        uid = pget("uom_id")
        if uid not in (None, ""):
            try:
                u = request.env["uom.uom"].sudo().browse(int(uid))
                if u.exists() and u.active:
                    return u
            except (TypeError, ValueError):
                pass
        raw = (pget("uom") or "").strip()
        if not raw:
            return request.env["uom.uom"].browse()
        low = raw.lower()
        Uom = request.env["uom.uom"].sudo()
        u = self._rest_pick_base_mass_uom(Uom, low)
        if u:
            return u
        if low in ("g", "gram", "grams"):
            u = Uom.search(
                [
                    ("active", "=", True),
                    "|",
                    ("name", "ilike", "غرام"),
                    ("name", "ilike", "gram"),
                ],
                limit=1,
            )
            if u:
                return u
        u = Uom.search([("active", "=", True), ("name", "ilike", raw)], limit=1)
        if u:
            return u
        return request.env["uom.uom"].browse()

    def _rest_product_ids_for_uom_filter(self, env, uom_id, align_sap_sales_unit):
        """
        Variant ids for catalog restriction by UoM — same rules as CRM pricelist API
        (implemented on ``sap.product.extended``).
        """
        if "sap.product.extended" not in env:
            Product = env["product.product"].sudo()
            return Product.search([("uom_id", "=", uom_id)]).ids
        return env["sap.product.extended"].sudo().product_variant_ids_matching_filtered_uom(
            uom_id,
            align_sap_sales_unit=bool(align_sap_sales_unit),
        )

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

    def _rest_product_unit_price(self, product, pl_rec, price_uom,
                                  ext_record=None, pl_items=None):
        """
        Match ``product.product.search_products_for_pos`` (right panel): use Odoo
        ``pricelist._get_product_price`` first on sudo records so API users without
        ``product.pricelist.item`` read rights still get the same numbers as the UI.

        Then fall back to POS UoM-group / packaging mapping (``get_product_data`` path)
        and rule chain when the standard engine returns 0.

        ``ext_record`` — optional pre-fetched ``sap.product.extended`` (avoids N+1).
        ``pl_items``   — optional pre-fetched pricelist items recordset (avoids N+1).
                         When provided, skips the expensive per-product
                         ``pl._get_product_price`` call (uom_in_pricelist) and resolves
                         price directly from pre-computed UoM data.
        """
        prod = product.sudo()
        pu = price_uom or prod.uom_id
        pl = pl_rec.sudo() if pl_rec else False
        ctrl = PosPerfumeController()

        # ── Fast bulk path (pre-fetched data available) ──────────────────────
        # Skip the expensive per-product pl._get_product_price / uom_in_pricelist
        # path entirely; use pre-fetched pricelist items through _get_uoms_from_pricelist.
        if pl_items is not None:
            uoms = ctrl._get_uoms_from_pricelist(
                prod, pl,
                ext_record=ext_record,
                pricelist_items=pl_items,
            )
            target_id = pu.id if pu else None
            price = ctrl._get_default_price_from_uoms(uoms, target_id)
            if price and price > 0:
                return float(price)
            return float(prod.list_price or 0.0)

        # ── Slow single-product path (no pre-fetched data) ───────────────────
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

        uoms = ctrl._get_uoms_from_pricelist(
            prod, pl, ext_record=ext_record,
        )
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

    def _rest_catalog_unit_price(self, product, pl_rec, price_uom, strict=False,
                                  ext_record=None, pl_items=None):
        """
        Catalog price: use ``pl_rec``; if price is 0 and not ``strict``, retry once with
        the POS UI default pricelist when it is a different record (mirrors omitting
        ``pricelist_id`` so ``pricelist_id=1`` does not stick on "Default" with no rules).
        Returns ``(price, pricelist_id_used)``; ``pricelist_id_used`` is None if ``pl_rec`` is empty.
        """
        if not pl_rec:
            p = self._rest_product_unit_price(product, pl_rec, price_uom,
                                              ext_record=ext_record, pl_items=pl_items)
            return float(p or 0.0), None
        p = float(self._rest_product_unit_price(product, pl_rec, price_uom,
                                                 ext_record=ext_record, pl_items=pl_items) or 0.0)
        used_id = pl_rec.id
        if strict or p > 0:
            return p, used_id
        alt = self._rest_default_pricelist()
        if alt and alt.id != pl_rec.id:
            # For the alternative pricelist we don't have pre-fetched items; accept the overhead
            p2 = float(self._rest_product_unit_price(product, alt, price_uom,
                                                      ext_record=ext_record) or 0.0)
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

    def _rest_product_catalog_row(
        self, prod, pl_rec, price_uom, strict_pl, pl_used_id,
        ext_map=None, wh_map=None, pl_items_map=None,
    ):
        """
        One product record matching the legacy **development** catalog JSON shape
        (rich UoMs, warehouses, brand, category_type, has_price, etc.).

        ``ext_map``      — ``{product_id: sap.product.extended record}`` pre-fetched in bulk.
        ``wh_map``       — ``{product_id: [warehouse_dict, …]}`` pre-fetched in bulk.
        ``pl_items_map`` — ``{product_tmpl_id: pricelist.item recordset}`` pre-fetched in bulk.

        When these maps are provided the method skips all per-product ORM/SAP queries that
        would otherwise cause an N+1 problem on large ``fetch_all`` requests.
        """
        # SAP extended: use pre-fetched map (avoids N+1 ORM calls)
        ext_rec = ext_map.get(prod.id, False) if ext_map is not None else None

        # Pricelist items: use pre-fetched map (avoids N+1 ORM calls)
        # Use empty recordset (not None) so fast path stays active even for no-item products
        if pl_items_map is not None:
            tmpl_id = prod.product_tmpl_id.id if prod.product_tmpl_id else None
            _empty_items = request.env["product.pricelist.item"].sudo().browse([])
            pl_items_for_prod = pl_items_map.get(tmpl_id, _empty_items)
        else:
            pl_items_for_prod = None

        catalog_price, priced_pl_id = self._rest_catalog_unit_price(
            prod, pl_rec, price_uom, strict=strict_pl,
            ext_record=ext_rec,
            pl_items=pl_items_for_prod,
        )
        Pl = request.env["product.pricelist"].sudo()
        pl_uom = pl_rec
        if priced_pl_id:
            cand = Pl.browse(priced_pl_id).exists()
            if cand:
                pl_uom = cand

        ctrl = PosPerfumeController()
        raw_uoms = ctrl._get_uoms_from_pricelist(
            prod, pl_uom,
            ext_record=ext_rec,
            pricelist_items=pl_items_for_prod,
        )
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

        # Warehouses: use pre-fetched map when available (avoids N+1 SAP/ORM calls)
        if wh_map is not None:
            warehouses = wh_map.get(prod.id, [])
        else:
            warehouses = ctrl._get_warehouses_simple(prod.id)

        foreign_name = self._rest_foreign_name(prod)
        _, color_class, badge_text = prod._get_product_priority_and_color(prod.default_code)
        categ_name = prod.categ_id.name if prod.categ_id else ""
        brand = {
            "key": color_class or "",
            "name": categ_name,
            "code": badge_text or "",
        }

        # SAP extended: resolve from the pre-fetched ext_rec (already set above)
        ext = ext_rec if ext_rec is not None else False
        if ext is False and ext_map is None and "sap.product.extended" in request.env:
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
        whs = env["stock.warehouse"].search([("active", "=", True)])
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
        # Writing a global financial parameter requires admin
        if not request.env.user.has_group("base.group_system"):
            return self._fail("Forbidden: admin required to update exchange rate", 403)
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
        try:
            body = json.loads(request.httprequest.data.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError) as exc:
            return self._fail(f"Invalid JSON body: {exc}", 400)
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
        try:
            body = json.loads(request.httprequest.data.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError) as exc:
            return self._fail(f"Invalid JSON body: {exc}", 400)
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

        uom_rec = request.env["uom.uom"].browse()
        _uom_is_subunit = False  # shared flag for sap_uom_group_entry block below
        _sub_uom_ids = None       # set when sub-unit UoM requested; used in phase-2 below
        _sub_base_sap_pids = set()  # product IDs from base-UoM + SAP (no pl_rec needed)
        if self._rest_query_bool(pget, "uom_filter_catalog", False):
            uom_rec = self._rest_resolve_catalog_uom(pget)
            if not uom_rec or not uom_rec.exists():
                return self._fail(
                    "uom_filter_catalog=1 requires a resolvable uom or uom_id (e.g. uom=kg).",
                    400,
                )
            # Detect whether the requested UoM is the base kg or a sub-unit.
            _base_kg = self._rest_pick_base_mass_uom(request.env["uom.uom"].sudo(), "kg")
            if _base_kg and uom_rec.id != _base_kg.id:
                _uom_is_subunit = True

            if not _uom_is_subunit:
                # Base kg: standard SAP sales-UoM catalog filter
                align = self._rest_query_bool(pget, "uom_align_sap_sales_unit", True)
                narrowed = self._rest_product_ids_for_uom_filter(
                    request.env, uom_rec.id, align_sap_sales_unit=align
                )
                domain = ["&"] + domain + [("id", "in", narrowed)]
            else:
                # Sub-unit (0.25 كغم, 0.5 كيلو, …): Phase 1 — build the list of
                # same-weight UoM IDs and pre-compute sets that don't need pl_rec.
                # Phase 2 (pricelist items) is deferred to after pl_rec is resolved.
                #
                # This Odoo instance uses a custom tree UoM model where:
                #   - UoMs like "0.25 كغم بلاستك" have factor=0.25 (sub-unit of kg)
                #   - UoMs like "0.25 كغم"           have factor=1.0 (standalone unit)
                # So factor-based matching misses related UoMs. Instead we extract
                # the leading weight number from the name (e.g. "0.25") and find
                # all UoMs whose name starts with that number (name LIKE "0.25%").
                import re as _re
                _Uom = request.env["uom.uom"].sudo()
                _weight_match = _re.match(r'^([\d.]+)', (uom_rec.name or "").strip())
                if _weight_match:
                    _weight_prefix = _weight_match.group(1)
                    _same_weight_uoms = _Uom.search([
                        ("active", "=", True),
                        ("name", "like", _weight_prefix + "%"),
                    ])
                    _sub_uom_ids = _same_weight_uoms.ids or [uom_rec.id]
                else:
                    _sub_uom_ids = [uom_rec.id]

                # Products whose base product UoM (product.uom_id) is this weight
                _base_pids = set(Product.search([("uom_id", "in", _sub_uom_ids)]).ids)

                # Products whose SAP sales UoM is this weight
                _sap_pids = set()
                if "sap.product.extended" in request.env:
                    _sap_pids = set(
                        request.env["sap.product.extended"].sudo()
                        .search([("sales_uom_id", "in", _sub_uom_ids)])
                        .mapped("product_id").ids
                    )
                _sub_base_sap_pids = _base_pids | _sap_pids

        sge_raw = pget("sap_uom_group_entry")
        if sge_raw not in (None, ""):
            # sap_uom_group_entry is an independent AND-filter that restricts products by their
            # SAP UoM group entry (AbsEntry). It is always applied when provided, regardless of
            # whether uom_filter_catalog targets a sub-unit UoM — the two filters are orthogonal.
            if "sap.product.extended" not in request.env:
                return self._fail(
                    "sap_uom_group_entry requires sap_integration (sap.product.extended).",
                    400,
                )
            parts = []
            if isinstance(sge_raw, (list, tuple)):
                for x in sge_raw:
                    parts.extend(str(x).replace(";", ",").split(","))
            else:
                parts = str(sge_raw).replace(";", ",").split(",")
            entries = []
            for p in parts:
                p = str(p).strip()
                if not p:
                    continue
                try:
                    entries.append(int(p))
                except (TypeError, ValueError):
                    return self._fail(
                        "sap_uom_group_entry must be one or more integers (SAP UoMGroupEntry / AbsEntry), "
                        "e.g. 2 or 2,9 for «لك» and «فل بلاستك».",
                        400,
                    )
            if not entries:
                return self._fail(
                    "sap_uom_group_entry was empty after parsing; use e.g. 2 or 2,9.",
                    400,
                )
            entries = list(dict.fromkeys(entries))
            Ext = request.env["sap.product.extended"].sudo()
            pids = Ext.search([("sap_uom_group_entry", "in", entries)]).mapped("product_id").ids
            domain = ["&"] + domain + [("id", "in", pids or [-1])]

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

        # Phase 2: apply sub-unit UoM product filter now that pl_rec is known.
        # _sub_uom_ids is set only when uom_filter_catalog=1 with a sub-unit UoM.
        if _sub_uom_ids is not None:
            _pl_pids = set()
            if pl_rec:
                _pl_items = request.env["product.pricelist.item"].sudo().search([
                    ("pricelist_id", "=", int(pl_rec.id)),
                    ("product_uom_id", "in", _sub_uom_ids),
                ])
                if _pl_items:
                    _tmpl_ids = _pl_items.mapped("product_tmpl_id").ids
                    _pl_pids = set(Product.search(
                        [("product_tmpl_id", "in", _tmpl_ids)]
                    ).ids)
            _sub_narrowed = list(_sub_base_sap_pids | _pl_pids)
            domain = ["&"] + domain + [("id", "in", _sub_narrowed or [-1])]

        def _build_ext_map(prod_ids):
            """Pre-fetch sap.product.extended for all product_ids in one query."""
            if not prod_ids or "sap.product.extended" not in request.env:
                return {}
            all_exts = request.env["sap.product.extended"].sudo().search(
                [("product_id", "in", prod_ids)]
            )
            return {e.product_id.id: e for e in all_exts}

        def _build_wh_map(prod_ids):
            """Pre-fetch sap.product.warehouse.info for all product_ids in one query."""
            result = {}
            if not prod_ids:
                return result
            if "sap.product.warehouse.info" in request.env:
                all_whs = request.env["sap.product.warehouse.info"].sudo().search(
                    [("product_id", "in", prod_ids)]
                )
                for wh_info in all_whs:
                    pid = wh_info.product_id.id
                    qty = wh_info.current_qty_available or wh_info.last_available or 0
                    if qty > 0 and wh_info.warehouse_id:
                        result.setdefault(pid, []).append({
                            "id": wh_info.warehouse_id.id,
                            "name": wh_info.warehouse_id.name,
                            "code": wh_info.sap_warehouse_code or wh_info.warehouse_id.code,
                            "quantity": float(qty),
                        })
                return result
            # Fallback: bulk SQL query across all products in one shot
            placeholders = ",".join(["%s"] * len(prod_ids))
            query = f"""
                SELECT sq.product_id,
                       sw.id   AS wh_id,
                       sw.name AS wh_name,
                       sw.code AS wh_code,
                       COALESCE(SUM(sq.quantity - sq.reserved_quantity), 0) AS available_qty
                FROM stock_warehouse sw
                JOIN stock_location sl ON sl.warehouse_id = sw.id AND sl.usage = 'internal'
                JOIN stock_quant sq ON sq.location_id = sl.id
                             AND sq.product_id IN ({placeholders})
                WHERE sw.active = true
                GROUP BY sq.product_id, sw.id, sw.name, sw.code
                HAVING COALESCE(SUM(sq.quantity - sq.reserved_quantity), 0) > 0
                ORDER BY sw.name
            """
            request.env.cr.execute(query, tuple(prod_ids))
            for row in request.env.cr.dictfetchall():
                result.setdefault(row["product_id"], []).append({
                    "id": row["wh_id"],
                    "name": row["wh_name"],
                    "code": row["wh_code"] or row["wh_name"][:5],
                    "quantity": float(row["available_qty"]),
                })
            return result

        def _build_pl_items_map(tmpl_ids):
            """Pre-fetch pricelist items for all template_ids in one query.
            Returns a dict keyed by tmpl_id where every input tmpl_id is present
            (missing = empty recordset) so the fast path is always used.
            """
            Item = request.env["product.pricelist.item"].sudo()
            if not tmpl_ids or not pl_rec:
                # Populate with empty recordsets so fast path is still taken
                return {tid: Item.browse([]) for tid in tmpl_ids}
            all_items = Item.search(
                [
                    ("pricelist_id", "=", pl_rec.id),
                    ("product_tmpl_id", "in", list(tmpl_ids)),
                ],
                order="write_date asc, id asc",
            )
            # Start with empty recordsets for every template
            result = {tid: Item.browse([]) for tid in tmpl_ids}
            # Group found items by template
            by_tmpl = {}
            for item in all_items:
                by_tmpl.setdefault(item.product_tmpl_id.id, []).append(item.id)
            for tid, ids in by_tmpl.items():
                result[tid] = Item.browse(ids)
            return result

        def _rows_for_products(prod_recs):
            prod_ids = prod_recs.ids
            tmpl_ids = set(prod_recs.mapped("product_tmpl_id").ids)
            ext_map = _build_ext_map(prod_ids)
            wh_map = _build_wh_map(prod_ids)
            pl_items_map = _build_pl_items_map(tmpl_ids)

            # Pre-resolve price UoM once per request batch.
            # When uom / uom_id are fixed params they produce the same UoM for every
            # product — resolving per-product triggers _rest_uom_sales_touch_count
            # (2 DB queries per candidate) multiplied by N products.
            _fixed_price_uom = None
            if (pget("uom_id") or pget("uom")) and prod_ids:
                _fixed_price_uom = self._rest_price_uom(prod_recs[0], pget)

            out = []
            for prod in prod_recs:
                # Use the pre-resolved UoM when available; fall back to product's own UoM
                price_uom = _fixed_price_uom if _fixed_price_uom else prod.uom_id
                row = self._rest_product_catalog_row(
                    prod, pl_rec, price_uom, strict_pl, pl_used_id,
                    ext_map=ext_map, wh_map=wh_map, pl_items_map=pl_items_map,
                )
                out.append(row)
            return out

        if use_python_filters:
            all_recs = Product.search(domain, order="name")
            seq_ids = []
            for prod in all_recs:
                if brand_raw and not self._rest_product_matches_brand_param(prod, brand_raw):
                    continue
                if cat_type_raw and not self._rest_product_matches_category_type_param(
                    prod, cat_type_raw
                ):
                    continue
                seq_ids.append(prod.id)
            # Rebuild a proper Odoo recordset so _rows_for_products can use
            # bulk-fetch helpers (.ids / .mapped / bulk searches).
            seq_recs = Product.browse(seq_ids)
            rows = _rows_for_products(seq_recs)
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

        payload = {
            "items": items,
            "total": total,
            "offset": offset_out,
            "limit": limit_out,
            "returned": len(items),
            "fetch_all": bool(limit is None),
            "pricelist_id": pl_used_id,
        }
        if uom_rec and uom_rec.exists():
            payload["resolved_catalog_uom_id"] = uom_rec.id
            payload["resolved_catalog_uom_name"] = uom_rec.display_name
        return self._ok(payload)

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

    @http.route(
        f"{_PREFIX}/products/by_primary_sales_uom",
        type="http",
        auth="none",
        methods=list(_READ),
        csrf=False,
        cors="*",
    )
    def products_by_primary_sales_uom(self, **kwargs):
        """
        Return products whose **SAP primary sales UoM** name starts with ``weight_prefix``
        (default ``"0.25"``).

        This is a strict filter on ``sap.product.extended.sales_uom_id`` — the unit SAP
        has designated as this product's main sales unit.  It intentionally excludes
        products that merely have a 0.25 kg pricelist item entry but whose primary unit
        is something else (e.g. «لك»).

        Query params
        ────────────
        weight_prefix  str   Name prefix to match UoMs (default "0.25").  Pass "0.5" for
                             half-kg items, "1" for full-kg, etc.
        pricelist_id   int   Pricelist for pricing (omit → POS default).
        categ_id /
        category_id    int   Restrict to a category subtree (child_of).
        query          str   Free-text search (name / default_code / barcode / foreign_name).
        fetch_all      bool  Return all rows (ignores limit/offset).
        limit          int   Page size (default 80).
        offset         int   Page start (default 0).
        """
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)

        if "sap.product.extended" not in request.env:
            return self._fail(
                "by_primary_sales_uom requires the sap_integration addon "
                "(sap.product.extended model not found).",
                400,
            )

        pget = self._rest_products_query_params()

        # ── weight_prefix ──────────────────────────────────────────────────────
        weight_prefix = (pget("weight_prefix") or "0.25").strip()
        if not weight_prefix:
            return self._fail("weight_prefix must not be empty.", 400)

        # Collect all active UoMs whose name starts with the requested prefix.
        Uom = request.env["uom.uom"].sudo()
        matching_uoms = Uom.search([
            ("active", "=", True),
            ("name", "like", weight_prefix + "%"),
        ])
        if not matching_uoms:
            return self._ok({
                "items": [],
                "total": 0,
                "offset": 0,
                "limit": 0,
                "returned": 0,
                "fetch_all": False,
                "pricelist_id": None,
                "weight_prefix": weight_prefix,
                "matched_uom_ids": [],
            })

        # Products whose SAP-designated primary sales UoM is one of these UoMs.
        Ext = request.env["sap.product.extended"].sudo()
        ext_recs = Ext.search([("sales_uom_id", "in", matching_uoms.ids)])
        primary_pids = set(ext_recs.mapped("product_id").ids)

        if not primary_pids:
            return self._ok({
                "items": [],
                "total": 0,
                "offset": 0,
                "limit": 0,
                "returned": 0,
                "fetch_all": False,
                "pricelist_id": None,
                "weight_prefix": weight_prefix,
                "matched_uom_ids": matching_uoms.ids,
            })

        # ── base domain ───────────────────────────────────────────────────────
        Product = request.env["product.product"].sudo()
        domain = [
            ("active", "=", True),
            ("sale_ok", "=", True),
            ("id", "in", list(primary_pids)),
        ]

        # ── optional free-text search ─────────────────────────────────────────
        q = (pget("query") or "").strip()
        if q:
            or_terms = [
                ("name", "ilike", q),
                ("default_code", "ilike", q),
                ("barcode", "ilike", q),
            ]
            if "foreign_name" in Product._fields:
                or_terms.append(("foreign_name", "ilike", q))
            domain = ["&"] + domain + (["|"] * (len(or_terms) - 1)) + or_terms

        # ── optional category filter ──────────────────────────────────────────
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

        # ── pagination ────────────────────────────────────────────────────────
        lim_raw = self._rest_int_param(pget, "limit", None)
        if lim_raw is None:
            lim_raw = 80
        fetch_all = self._rest_query_bool(pget, "fetch_all", False) or lim_raw == 0
        if fetch_all:
            limit = None
        else:
            limit = max(int(lim_raw), 1)
        offset = max(self._rest_int_param(pget, "offset", 0) or 0, 0)

        # ── pricelist ─────────────────────────────────────────────────────────
        pl_id = pget("pricelist_id")
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

        # ── fetch & serialize ─────────────────────────────────────────────────
        # Use the first matching UoM as the display/pricing UoM for all products.
        # The catalog row helper will still use each product's own sales UoM for
        # available_uoms, but the price column will use this UoM for consistency.
        price_uom = matching_uoms[0]

        def _build_ext_map(prod_ids):
            if not prod_ids:
                return {}
            all_exts = Ext.search([("product_id", "in", prod_ids)])
            return {e.product_id.id: e for e in all_exts}

        def _build_wh_map(prod_ids):
            result = {}
            if not prod_ids:
                return result
            if "sap.product.warehouse.info" in request.env:
                for wh_info in request.env["sap.product.warehouse.info"].sudo().search(
                    [("product_id", "in", prod_ids)]
                ):
                    pid = wh_info.product_id.id
                    qty = wh_info.current_qty_available or wh_info.last_available or 0
                    if qty > 0 and wh_info.warehouse_id:
                        result.setdefault(pid, []).append({
                            "id": wh_info.warehouse_id.id,
                            "name": wh_info.warehouse_id.name,
                            "code": wh_info.sap_warehouse_code or wh_info.warehouse_id.code,
                            "quantity": float(qty),
                        })
                return result
            placeholders = ",".join(["%s"] * len(prod_ids))
            request.env.cr.execute(
                f"""
                SELECT sq.product_id,
                       sw.id   AS wh_id,
                       sw.name AS wh_name,
                       sw.code AS wh_code,
                       COALESCE(SUM(sq.quantity - sq.reserved_quantity), 0) AS available_qty
                FROM stock_warehouse sw
                JOIN stock_location sl ON sl.warehouse_id = sw.id AND sl.usage = 'internal'
                JOIN stock_quant sq ON sq.location_id = sl.id
                             AND sq.product_id IN ({placeholders})
                WHERE sw.active = true
                GROUP BY sq.product_id, sw.id, sw.name, sw.code
                HAVING COALESCE(SUM(sq.quantity - sq.reserved_quantity), 0) > 0
                ORDER BY sw.name
                """,
                tuple(prod_ids),
            )
            for row in request.env.cr.dictfetchall():
                result.setdefault(row["product_id"], []).append({
                    "id": row["wh_id"],
                    "name": row["wh_name"],
                    "code": row["wh_code"] or row["wh_name"][:5],
                    "quantity": float(row["available_qty"]),
                })
            return result

        def _build_pl_items_map(tmpl_ids):
            Item = request.env["product.pricelist.item"].sudo()
            if not tmpl_ids or not pl_rec:
                return {tid: Item.browse([]) for tid in tmpl_ids}
            all_items = Item.search(
                [
                    ("pricelist_id", "=", pl_rec.id),
                    ("product_tmpl_id", "in", list(tmpl_ids)),
                ],
                order="write_date asc, id asc",
            )
            result = {tid: Item.browse([]) for tid in tmpl_ids}
            by_tmpl = {}
            for item in all_items:
                by_tmpl.setdefault(item.product_tmpl_id.id, []).append(item.id)
            for tid, ids in by_tmpl.items():
                result[tid] = Item.browse(ids)
            return result

        def _rows_for_products(prod_recs):
            prod_ids = prod_recs.ids
            tmpl_ids = set(prod_recs.mapped("product_tmpl_id").ids)
            ext_map = _build_ext_map(prod_ids)
            wh_map = _build_wh_map(prod_ids)
            pl_items_map = _build_pl_items_map(tmpl_ids)
            out = []
            for prod in prod_recs:
                # Use the ext_map to pick the exact primary sales UoM for this product
                ext_r = ext_map.get(prod.id)
                pu = (ext_r.sales_uom_id if ext_r and ext_r.sales_uom_id else price_uom)
                row = self._rest_product_catalog_row(
                    prod, pl_rec, pu, strict_pl, pl_used_id,
                    ext_map=ext_map, wh_map=wh_map, pl_items_map=pl_items_map,
                )
                # Expose which primary sales UoM was used for transparency
                row["primary_sales_uom"] = {"id": pu.id, "name": pu.name or ""}
                out.append(row)
            return out

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

        return self._ok({
            "items": items,
            "total": total,
            "offset": offset_out,
            "limit": limit_out,
            "returned": len(items),
            "fetch_all": bool(limit is None),
            "pricelist_id": pl_used_id,
            "weight_prefix": weight_prefix,
            "matched_uom_ids": matching_uoms.ids,
        })

    @http.route(f"{_PREFIX}/products/data", type="http", auth="none", methods=["POST"], csrf=False, cors="*")
    def product_data(self, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        try:
            body = json.loads(request.httprequest.data.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError) as exc:
            return self._fail(f"Invalid JSON body: {exc}", 400)
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
        try:
            body = json.loads(request.httprequest.data.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError) as exc:
            return self._fail(f"Invalid JSON body: {exc}", 400)
        pid_raw = body.get("product_id") or 0
        try:
            pid_int = int(pid_raw)
        except (TypeError, ValueError):
            return self._fail("product_id must be an integer", 400)
        if not pid_int:
            return self._fail("product_id required", 400)
        ctrl = PosPerfumeController()
        res = ctrl.get_product_data(
            pid_int,
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
        Order = request.env["pos.perfume.order"].sudo()
        if request.httprequest.method == "GET":
            limit = min(int(request.httprequest.args.get("limit") or 80), 500)
            offset = int(request.httprequest.args.get("offset") or 0)
            domain = [("state", "!=", "cancel")]
            st = request.httprequest.args.get("state")
            if st:
                domain = [("state", "=", st)]
            elif request.httprequest.args.get("include_cancelled") == "1":
                domain = []
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
                    "sale_order_name": o.sale_order_id.name if o.sale_order_id else "",
                    "sap_synced": o.sale_order_id.sap_synced if o.sale_order_id else False,
                    "sap_doc_entry": int(o.sale_order_id.sap_doc_entry or 0) if o.sale_order_id else 0,
                }
                for o in recs
            ]
            return self._ok({"items": items, "total": total})

        # POST — create a new pos.perfume.order
        return self._create_order()

    def _try_sync_sale_to_sap(self, sale_order):
        """
        Attempt to send sale_order to SAP immediately.
        Returns dict: {sap_synced, sap_doc_entry, sap_error}.
        Never raises — SAP failures are non-fatal for the API response.
        """
        if not sale_order or not sale_order.exists():
            return {"sap_synced": False, "sap_doc_entry": 0, "sap_error": "No sale order linked"}
        try:
            sale_order._send_to_sap()
            sale_order.env.cr.flush()
            sale_order.env.cr.execute(
                "SELECT sap_synced, sap_doc_entry, sap_error_message FROM sale_order WHERE id=%s",
                (sale_order.id,)
            )
            row = sale_order.env.cr.fetchone()
            return {
                "sap_synced": bool(row[0]) if row else False,
                "sap_doc_entry": int(row[1] or 0) if row else 0,
                "sap_error": row[2] or None if row else None,
            }
        except Exception as exc:
            _logger.warning("REST API — SAP sync failed for %s: %s", sale_order.name, exc)
            return {"sap_synced": False, "sap_doc_entry": 0, "sap_error": str(exc)}

    def _build_rest_order_line_vals(self, data):
        """
        Build a single order-line vals dict for pos.perfume.order.line.
        Returns (vals_dict, error_str). Uses sudo() — caller already authorised via _pos_rest_auth().
        Mirrors pos_bridge_controller._build_line_vals — both must stay in sync.
        """
        product_id = data.get("product_id")
        warehouse_id = data.get("warehouse_id")
        if not product_id:
            return None, "product_id is required for each order line"
        if not warehouse_id:
            return None, "warehouse_id is required for each order line"

        product = request.env["product.product"].sudo().browse(int(product_id))
        if not product.exists():
            return None, f"Product {product_id} not found"

        warehouse = request.env["stock.warehouse"].sudo().browse(int(warehouse_id))
        if not warehouse.exists():
            return None, f"Warehouse {warehouse_id} not found"

        # Resolve UoM: prefer SAP sales UoM → Odoo product UoM
        uom = product.uom_id
        try:
            ext = request.env["sap.product.extended"].sudo().search(
                [("product_id", "=", product.id)], limit=1
            )
            if ext and ext.sales_uom_id:
                uom = ext.sales_uom_id
        except Exception:
            pass

        if data.get("product_uom_id"):
            override_uom = request.env["uom.uom"].sudo().browse(int(data["product_uom_id"]))
            if not override_uom.exists():
                return None, f"UoM {data['product_uom_id']} not found"
            uom = override_uom

        location_id = warehouse.lot_stock_id.id if warehouse.lot_stock_id else False

        return {
            "product_id": product.id,
            "product_uom_id": uom.id,
            "warehouse_id": warehouse.id,
            "location_id": location_id,
            "quantity": float(data.get("quantity", 1.0)),
            "unit_price": float(data.get("unit_price", product.list_price)),
            "discount_percent": float(data.get("discount_percent", 0.0)),
            "custom_product_name": data.get("custom_product_name") or "",
            "sequence": int(data.get("sequence", 10)),
        }, None

    def _create_order(self):
        """Handle POST /api/pos_perfume/v1/orders — create and optionally confirm a pos.perfume.order."""
        try:
            body = json.loads(request.httprequest.data.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError) as exc:
            return self._fail(f"Invalid JSON body: {exc}", 400)

        partner_id = body.get("partner_id")
        if not partner_id:
            return self._fail("partner_id is required", 400)

        partner = request.env["res.partner"].sudo().browse(int(partner_id))
        if not partner.exists():
            return self._fail(f"Customer {partner_id} not found", 404)

        Order = request.env["pos.perfume.order"].sudo()

        # Resolve pricelist
        pl = None
        if body.get("pricelist_id"):
            pl = request.env["product.pricelist"].sudo().browse(int(body["pricelist_id"]))
            if not pl.exists():
                return self._fail(f"Pricelist {body['pricelist_id']} not found", 404)
        if not pl:
            try:
                default_pl_id = Order._get_default_pricelist()
                if default_pl_id:
                    pl = request.env["product.pricelist"].sudo().browse(default_pl_id)
            except Exception:
                pass
        if not pl or not pl.exists():
            # Last resort: first active pricelist
            pl = request.env["product.pricelist"].sudo().search([("active", "=", True)], limit=1)
        if not pl or not pl.exists():
            return self._fail("No pricelist available", 422)

        order_vals = {
            "partner_id": partner.id,
            "pricelist_id": pl.id,
            "state": "draft",
            "invoice_type": str(body.get("invoice_type") or "1"),
            "user_id": request.env.user.id,
        }

        if body.get("exchange_rate") is not None:
            try:
                order_vals["exchange_rate"] = float(body["exchange_rate"])
            except (TypeError, ValueError):
                return self._fail("exchange_rate must be a number", 400)

        if body.get("note"):
            order_vals["note"] = str(body["note"])

        # Build order lines
        line_vals_list = []
        for idx, line_data in enumerate(body.get("order_lines") or []):
            lv, err = self._build_rest_order_line_vals(line_data)
            if err:
                return self._fail(f"Line {idx}: {err}", 400)
            line_vals_list.append((0, 0, lv))

        if line_vals_list:
            order_vals["order_line_ids"] = line_vals_list

        try:
            order = Order.create(order_vals)
        except Exception as exc:
            _logger.exception("POST /orders — ORM create failed")
            return self._fail(f"Order creation failed: {exc}", 500)

        # Determine intent:
        # send_as_quotation=true → create draft sale.order, push to SAP as Quotation (one-step)
        # create_only=true       → create draft POS order only, no SAP sync (frontend calls /quotation after)
        # default                → confirm order and push to SAP as Sales Order
        send_as_quotation = bool(body.get("send_as_quotation", False))
        create_only = bool(body.get("create_only", False))

        sap_result = {"sap_synced": False, "sap_doc_entry": 0, "sap_error": None}
        if line_vals_list:
            if create_only:
                # --- Draft-only flow: create POS order + draft sale.order, NO SAP sync ---
                # Frontend will call POST /orders/:id/quotation to push to SAP as Quotation
                try:
                    order.with_context(force_quotation=True).action_ensure_sale_order()
                    order.invalidate_recordset()
                except Exception as exc:
                    _logger.warning("POST /orders (create_only) — action_ensure_sale_order failed: %s", exc)
                # Leave state as draft — don't confirm, don't send to SAP

            elif send_as_quotation:
                # --- Quotation flow ---
                # 1. Create a draft sale.order without confirming (no SAP sync via write override)
                try:
                    order.with_context(force_quotation=True).action_ensure_sale_order()
                    order.invalidate_recordset()
                except Exception as exc:
                    _logger.warning("POST /orders — action_ensure_sale_order failed: %s", exc)

                # 2. Push to SAP as Quotation
                if order.sale_order_id:
                    try:
                        order.sale_order_id._send_to_sap(force_as_quotation=True)
                        order.sale_order_id.env.cr.flush()
                        order.sale_order_id.env.cr.execute(
                            "SELECT sap_synced, sap_doc_entry, sap_error_message FROM sale_order WHERE id=%s",
                            (order.sale_order_id.id,)
                        )
                        row = order.sale_order_id.env.cr.fetchone()
                        sap_result = {
                            "sap_synced": bool(row[0]) if row else False,
                            "sap_doc_entry": int(row[1] or 0) if row else 0,
                            "sap_error": row[2] or None if row else None,
                        }
                    except Exception as exc:
                        _logger.warning("POST /orders — SAP quotation sync failed: %s", exc)
                        sap_result = {"sap_synced": False, "sap_doc_entry": 0, "sap_error": str(exc)}

                # 3. Set POS order state to 'quotation'
                try:
                    order.action_quotation()
                except Exception as exc:
                    _logger.warning("POST /orders — action_quotation failed: %s", exc)

            else:
                # --- Confirmed Sales Order flow (default) ---
                try:
                    order.action_confirm()
                except Exception as exc:
                    _logger.warning("POST /orders — action_confirm failed (order %s): %s", order.id, exc)
                    return _json(
                        {
                            "success": True,
                            "message": "Order created as draft; confirmation failed — use /confirm to retry",
                            "warning": str(exc),
                            "data": {
                                "id": order.id,
                                "name": order.name,
                                "state": order.state,
                                "partner_id": order.partner_id.id,
                                "partner_name": order.partner_id.name,
                                "pricelist_id": order.pricelist_id.id,
                                "amount_total": order.amount_total,
                                "sale_order_name": order.sale_order_id.name if order.sale_order_id else "",
                                "invoice_type": order.invoice_type,
                                "note": order.note or "",
                                "sap_synced": False,
                                "sap_doc_entry": 0,
                                "sap_error": None,
                            },
                        },
                        status=207,
                    )
                # Send to SAP immediately as Sales Order
                sap_result = self._try_sync_sale_to_sap(order.sale_order_id)

        return _json(
            {
                "success": True,
                "message": "Order created",
                "data": {
                    "id": order.id,
                    "name": order.name,
                    "state": order.state,
                    "partner_id": order.partner_id.id,
                    "partner_name": order.partner_id.name,
                    "pricelist_id": order.pricelist_id.id,
                    "amount_total": order.amount_total,
                    "sale_order_name": order.sale_order_id.name if order.sale_order_id else "",
                    "invoice_type": order.invoice_type,
                    "note": order.note or "",
                    "sap_synced": sap_result["sap_synced"],
                    "sap_doc_entry": sap_result["sap_doc_entry"],
                    "sap_error": sap_result["sap_error"],
                },
            },
            status=201,
        )

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
        o = request.env["pos.perfume.order"].sudo().browse(order_id).exists()
        if not o:
            return self._fail("Order not found", 404)
        method = request.httprequest.method
        if method == "GET":
            lines = []
            for ln in o.order_line_ids:
                lines.append(
                    {
                        "id": ln.id,
                        "sequence": ln.sequence,
                        "product_id": ln.product_id.id,
                        "product_name": ln.product_id.name,
                        "product_code": ln.product_code or ln.product_id.default_code or "",
                        "product_foreign_name": ln.product_foreign_name or "",
                        "custom_product_name": ln.custom_product_name or "",
                        "quantity": ln.quantity,
                        "product_uom_qty": ln.quantity,
                        "product_uom_id": ln.product_uom_id.id if ln.product_uom_id else None,
                        "product_uom_name": ln.product_uom_id.name if ln.product_uom_id else "",
                        "warehouse_id": ln.warehouse_id.id if ln.warehouse_id else None,
                        "warehouse_name": ln.warehouse_id.name if ln.warehouse_id else "",
                        "price_unit": ln.unit_price,
                        "discount_percent": ln.discount_percent,
                        "line_subtotal": getattr(ln, "line_subtotal", 0.0),
                        "discount_amount": getattr(ln, "discount_amount", 0.0),
                    }
                )
            return self._ok(
                {
                    "id": o.id,
                    "name": o.name,
                    "state": o.state,
                    "date_order": o.date.isoformat() if o.date else None,
                    "partner_id": o.partner_id.id,
                    "partner_name": o.partner_id.name or "",
                    "partner_phone": o.partner_id.phone or o.partner_id.mobile or "",
                    "partner_email": o.partner_id.email or "",
                    "pricelist_id": o.pricelist_id.id if o.pricelist_id else None,
                    "pricelist_name": o.pricelist_id.name if o.pricelist_id else "",
                    "currency_id": o.currency_id.id if o.currency_id else None,
                    "currency_name": o.currency_id.name if o.currency_id else "",
                    "exchange_rate": o.exchange_rate or 0.0,
                    "amount_total": o.amount_total,
                    "amount_total_iqd": getattr(o, "amount_total_iqd", 0.0),
                    "invoice_type": o.invoice_type or "",
                    "note": o.note or "",
                    "user_id": o.user_id.id if o.user_id else None,
                    "user_name": o.user_id.name if o.user_id else "",
                    "sale_order_id": o.sale_order_id.id if o.sale_order_id else None,
                    "sale_order_name": o.sale_order_id.name if o.sale_order_id else "",
                    "sap_synced": o.sap_synced if hasattr(o, "sap_synced") else (o.sale_order_id.sap_synced if o.sale_order_id else False),
                    "sap_doc_entry": int(o.sap_doc_entry or 0) if hasattr(o, "sap_doc_entry") and o.sap_doc_entry else int(o.sale_order_id.sap_doc_entry or 0) if o.sale_order_id else 0,
                    "sap_doc_num": o.sap_doc_num or (o.sale_order_id.sap_doc_num if o.sale_order_id else ""),
                    "sap_error": o.sap_error_message or (o.sale_order_id.sap_error_message if o.sale_order_id else None),
                    "order_line_ids": lines,
                }
            )
        if method == "DELETE":
            try:
                o.action_cancel()
            except Exception as exc:
                return self._fail(str(exc), 409)
            return self._ok({"id": o.id, "state": o.state})
        return self._fail("PUT order: use Odoo or extend endpoint", 501)

    @http.route(
        f"{_PREFIX}/orders/<int:order_id>/confirm",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def order_confirm(self, order_id, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        o = request.env["pos.perfume.order"].sudo().browse(order_id).exists()
        if not o:
            return self._fail("Order not found", 404)
        if o.state not in ("draft", "quotation"):
            # Already confirmed as sale — idempotent
            if o.state == "sale":
                sap_result = {"sap_synced": bool(o.sale_order_id.sap_synced) if o.sale_order_id else False,
                              "sap_doc_entry": int(o.sale_order_id.sap_doc_entry or 0) if o.sale_order_id else 0,
                              "sap_error": None}
                if o.sale_order_id and not o.sale_order_id.sap_synced:
                    sap_result = self._try_sync_sale_to_sap(o.sale_order_id)
                return self._ok(
                    {
                        "id": o.id,
                        "name": o.name,
                        "state": o.state,
                        "amount_total": o.amount_total,
                        "sale_order_name": o.sale_order_id.name if o.sale_order_id else "",
                        "sap_synced": sap_result["sap_synced"],
                        "sap_doc_entry": sap_result["sap_doc_entry"],
                        "sap_error": sap_result["sap_error"],
                    }
                )
            return self._fail(
                f"Cannot confirm order in state '{o.state}'", 409
            )
        try:
            # force_sale_order=True: confirms sale.order and sends to SAP as Sale Order
            o.with_context(force_sale_order=True).action_confirm()
        except Exception as exc:
            _logger.exception("POST /orders/%s/confirm — action_confirm failed", order_id)
            return self._fail(f"Confirm failed: {exc}", 500)
        # Send to SAP immediately after confirmation
        sap_result = self._try_sync_sale_to_sap(o.sale_order_id)
        return self._ok(
            {
                "id": o.id,
                "name": o.name,
                "state": o.state,
                "amount_total": o.amount_total,
                "sale_order_name": o.sale_order_id.name if o.sale_order_id else "",
                "sap_synced": sap_result["sap_synced"],
                "sap_doc_entry": sap_result["sap_doc_entry"],
                "sap_error": sap_result["sap_error"],
            }
        )

    @http.route(
        f"{_PREFIX}/orders/<int:order_id>/quotation",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def order_sync_quotation(self, order_id, **kwargs):
        """Send/re-send the linked sale.order to SAP as a Quotation (force_as_quotation=True).
        Mirrors the POS UI 'Quotation' button (action_sync_as_quotation).
        Works for any order state (draft, sale, done).
        """
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        o = request.env["pos.perfume.order"].sudo().browse(order_id).exists()
        if not o:
            return self._fail("Order not found", 404)
        if not o.sale_order_id:
            # Create the draft sale.order if it doesn't exist yet
            try:
                o.action_ensure_sale_order()
                o.invalidate_recordset()
            except Exception as exc:
                return self._fail(f"Could not create sale order: {exc}", 500)
        if not o.sale_order_id:
            return self._fail("Order has no linked sale order — confirm the order first", 422)

        so = o.sale_order_id

        # If the document is already in SAP (sap_doc_entry set), we do NOT re-push it
        # as a Quotation — the document may already be a Sales Order.  Just reconcile
        # the sap_synced flag and return the existing SAP reference.
        if so.sap_doc_entry and so.sap_doc_entry > 0:
            if not so.sap_synced:
                so.sudo().write({'sap_synced': True, 'sap_error_message': False})
                so.env.cr.flush()
            sap_synced = True
            sap_doc_entry = int(so.sap_doc_entry)
            sap_error = None
        else:
            # No prior SAP document — push as Quotation now
            try:
                so._send_to_sap(force_as_quotation=True)
                so.env.cr.flush()
                so.env.cr.execute(
                    "SELECT sap_synced, sap_doc_entry, sap_error_message FROM sale_order WHERE id=%s",
                    (so.id,)
                )
                row = so.env.cr.fetchone()
                sap_synced = bool(row[0]) if row else False
                sap_doc_entry = int(row[1] or 0) if row else 0
                sap_error = row[2] or None if row else None
            except Exception as exc:
                _logger.warning("POST /orders/%s/quotation — SAP sync failed: %s", order_id, exc)
                sap_synced = False
                sap_doc_entry = 0
                sap_error = str(exc)
        # Update POS order state to 'quotation'
        try:
            o.action_quotation()
        except Exception as exc:
            _logger.warning("POST /orders/%s/quotation — action_quotation failed: %s", order_id, exc)
        return self._ok(
            {
                "id": o.id,
                "name": o.name,
                "state": o.state,
                "sale_order_name": o.sale_order_id.name,
                "sap_synced": sap_synced,
                "sap_doc_entry": sap_doc_entry,
                "sap_error": sap_error,
            }
        )

    @http.route(f"{_PREFIX}/invoice-types", type="http", auth="none", methods=["GET"], csrf=False, cors="*")
    def invoice_types(self, **kwargs):
        if not self._pos_rest_auth():
            return self._fail("Unauthorized", 401)
        env = request.env
        sel = env["pos.perfume.order"]._fields["invoice_type"].selection
        if callable(sel):
            sel = sel(env["pos.perfume.order"])
        items = [{"key": k, "label": v} for k, v in sel]
        return self._ok({"items": items, "total": len(items)})
