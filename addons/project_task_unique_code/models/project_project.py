# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#
###############################################################################
from odoo import api, fields, models


class Project(models.Model):
    """ Inherits project.project """
    _inherit = 'project.project'

    project_short_code = fields.Char(
        string='Short Code', required=False,
        help="Set a short code here and this will be used to generate"
        "serial number for the project's tasks.")
    sequence_id = fields.Many2one(
        'ir.sequence', 'Reference Sequence', check_company=True, copy=False,
        help='The sequence that will be used for the project.')

    _project_short_code_uniq = models.Constraint(
        'unique(project_short_code, company_id)',
        'The project code must be unique per company!'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """ Extends the create method to create the sequence """
        for vals in vals_list:
            short_code = vals.get('project_short_code')
            if not short_code:
                # Auto-generate a short code from the project name when not provided
                name = vals.get('name', 'PRJ')
                short_code = ''.join(
                    w[0].upper() for w in name.split() if w
                )[:6] or 'PRJ'
                # Ensure uniqueness within the company
                company_id = vals.get('company_id') or self.env.company.id
                existing = self.search_count([
                    ('project_short_code', '=', short_code),
                    ('company_id', '=', company_id),
                ])
                if existing:
                    short_code = short_code + str(existing + 1)
                vals['project_short_code'] = short_code
            if 'sequence_id' not in vals or not vals['sequence_id']:
                vals['sequence_id'] = self.env['ir.sequence'].sudo().create({
                    'name': vals['name'] + ' Project Sequence',
                    'prefix': short_code + '-',
                    'padding': 3,
                    'company_id': vals.get('company_id') or self.env.company.id,
                }).id
        return super().create(vals_list)
