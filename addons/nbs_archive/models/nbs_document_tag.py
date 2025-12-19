# -*- coding: utf-8 -*-

from odoo import models, fields, api


class NBSDocumentTag(models.Model):
    _name = 'nbs.document.tag'
    _description = 'Document Tag'
    _order = 'name'
    
    name = fields.Char(
        string='Tag Name',
        required=True,
        translate=True,
        index=True
    )
    color = fields.Integer(
        string='Color',
        default=0
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Tag name must be unique!'),
    ]
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if name:
            tags = self.search([('name', operator, name)] + args, limit=limit)
            return tags.name_get()
        return super()._name_search(name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)


