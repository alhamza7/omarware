# -*- coding: utf-8 -*-

from odoo import models, fields

class FragranticaAccord(models.Model):
    _name = 'fragrantica.accord'
    _description = 'Fragrantica Main Accord'
    _order = 'perfume_id, accord_order'
    
    perfume_id = fields.Many2one('fragrantica.perfume', string='Perfume', required=True, ondelete='cascade', index=True)
    
    accord_name = fields.Char('Accord Name', required=True)
    accord_width = fields.Float('Width (%)', help='Visual width/percentage of the accord')
    accord_color = fields.Char('Color Code', help='Hex color code for visual display')
    accord_order = fields.Integer('Display Order', default=0)
    
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = record.accord_name
            if record.accord_width:
                name = f"{name} ({record.accord_width}%)"
            result.append((record.id, name))
        return result

