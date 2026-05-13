# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartnerNbsArchive(models.Model):
    """Extend res.partner to flag companies created through the NBS Archive API.

    This isolates NBS Archive companies from the thousands of general Odoo
    partners (SAP-synced customers, vendors, system companies) so that
    GET /api/companies only returns Archive-managed brands.
    """

    _inherit = "res.partner"

    nbs_archive_company = fields.Boolean(
        string="NBS Archive Company",
        default=False,
        index=True,
        help="Set automatically when a company is created via the NBS Archive "
             "companies API.  Used to scope the /api/companies listing.",
    )
