# -*- coding: utf-8 -*-
"""REST API `/api/pos_perfume/v1/*` for external SPAs (Bearer optional; session `auth='user'`)."""
import json
import logging

from odoo import http
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
        """Logged-in session (e.g. Vite proxy + cookie) or ``Authorization: Bearer <API key>`` (rpc scope)."""
        if request.session.uid:
            return True
        auth = (request.httprequest.headers.get("Authorization") or "").strip()
        if not auth.lower().startswith("bearer "):
            return False
        key = auth[7:].strip()
        if not key:
            return False
        uid = request.env["res.users.apikeys"].sudo()._check_credentials(scope="rpc", key=key)
        if not uid:
            return False
        request.update_env(user=uid)
        return True

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
        pls = env["product.pricelist"].search([("active", "=", True)])
        whs = env["stock.warehouse"].search([])
        users = env["res.users"].search([("share", "=", False), ("active", "=", True)])
        sel = env["pos.perfume.order"]._fields["invoice_type"].selection
        if callable(sel):
            sel = sel(env["pos.perfume.order"])
        invoice_types = [{"key": k, "label": v} for k, v in sel]
        rate = env["pos.perfume.order"].sudo().get_exchange_rate_from_db()
        default_pl = pls[:1]
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
        pls = request.env["product.pricelist"].search([("active", "=", True)])
        items = [
            {
                "id": p.id,
                "name": p.name,
                "currency_id": p.currency_id.id,
                "currency_name": p.currency_id.name,
            }
            for p in pls
        ]
        return self._ok({"items": items, "total": len(items)})

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
        Product = request.env["product.product"]
        q = request.httprequest.args.get("query") or ""
        limit = min(int(request.httprequest.args.get("limit") or 80), 500)
        offset = int(request.httprequest.args.get("offset") or 0)
        pl_id = request.httprequest.args.get("pricelist_id")
        domain = [("sale_ok", "=", True), ("active", "=", True)]
        if q:
            domain = (
                ["&"]
                + domain
                + [
                    "|",
                    "|",
                    ("name", "ilike", q),
                    ("default_code", "ilike", q),
                    ("barcode", "ilike", q),
                ]
            )
        total = Product.search_count(domain)
        recs = Product.search(domain, limit=limit, offset=offset, order="name")
        items = []
        pl_rec = False
        if pl_id:
            try:
                pl_rec = request.env["product.pricelist"].browse(int(pl_id)).exists()
            except (TypeError, ValueError):
                pl_rec = False
        for prod in recs:
            price = prod.list_price
            if pl_rec:
                price = pl_rec._get_product_price(prod, 1.0, uom=prod.uom_id)
            items.append(
                {
                    "id": prod.id,
                    "name": prod.name,
                    "default_code": prod.default_code or "",
                    "list_price": price,
                    "uom_id": prod.uom_id.id,
                    "uom_name": prod.uom_id.name,
                }
            )
        return self._ok({"items": items, "total": total})

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
        prod = request.env["product.product"].browse(product_id).exists()
        if not prod:
            return self._fail("Product not found", 404)
        pl_id = request.httprequest.args.get("pricelist_id")
        price = prod.list_price
        if pl_id:
            try:
                pl_rec = request.env["product.pricelist"].browse(int(pl_id)).exists()
                if pl_rec:
                    price = pl_rec._get_product_price(prod, 1.0, uom=prod.uom_id)
            except (TypeError, ValueError):
                pass
        return self._ok(
            {
                "id": prod.id,
                "name": prod.name,
                "default_code": prod.default_code or "",
                "list_price": price,
                "uom_id": prod.uom_id.id,
                "uom_name": prod.uom_id.name,
            }
        )

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
