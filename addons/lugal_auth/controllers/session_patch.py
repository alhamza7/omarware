# -*- coding: utf-8 -*-
"""Single-DB friendly /web/session/authenticate (empty db or case mismatch)."""
import odoo.http as odoo_http
from odoo import http
from odoo.addons.web.controllers.session import Session


class Session(Session):
    @http.route("/web/session/authenticate", type="jsonrpc", auth="none", readonly=False)
    def authenticate(self, db, login, password, base_location=None):
        # list_db=False would make db_list() deny listing; force=True is server-side only
        dbs = odoo_http.db_list(force=True)
        if len(dbs) == 1:
            canonical = dbs[0]
            raw = db.strip() if isinstance(db, str) else db
            if raw is None or raw == "":
                db = canonical
            elif isinstance(raw, str) and raw.lower() == canonical.lower():
                db = canonical
        return super().authenticate(db, login, password, base_location=base_location)
