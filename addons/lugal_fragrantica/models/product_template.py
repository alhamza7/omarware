# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    # Link to Fragrantica perfume
    fragrantica_perfume_id = fields.Many2one(
        'fragrantica.perfume', 
        string='Fragrantica Perfume',
        help='Link this product to a Fragrantica perfume database entry'
    )
    
    # Override fields (if user wants to customize)
    fragrantica_use_custom = fields.Boolean('Use Custom Data', default=False,
        help='Enable this to override Fragrantica data with custom values')
    
    # Custom overridable fields
    custom_description = fields.Text('Custom Description')
    custom_year = fields.Integer('Custom Year')
    
    # Relations
    custom_note_ids = fields.One2many('product.fragrantica.note', 'product_id', string='Custom Notes')
    custom_accord_ids = fields.One2many('product.fragrantica.accord', 'product_id', string='Custom Accords')
    
    # Pending request for non-existing perfumes
    fragrantica_pending_url = fields.Char('Fragrantica URL (Pending)',
        help='If perfume not found in database, paste Fragrantica URL here for future scraping')
    fragrantica_request_id = fields.Many2one('fragrantica.pending.request', string='Pending Request', readonly=True)
    
    # Computed fields for display
    display_perfume_name = fields.Char('Perfume Name', compute='_compute_fragrantica_display')
    display_perfume_arabic_name = fields.Char('Arabic Name', compute='_compute_fragrantica_display')
    display_brand_name = fields.Char('Brand Name', compute='_compute_fragrantica_display')
    display_year = fields.Integer('Year', compute='_compute_fragrantica_display')
    display_description = fields.Text('Description', compute='_compute_fragrantica_display')
    display_image = fields.Binary('Perfume Image', compute='_compute_fragrantica_display')
    display_brand_logo = fields.Binary('Brand Logo', compute='_compute_fragrantica_display')
    
    # Image URLs for displaying external images temporarily
    display_image_url = fields.Char('Image URL', compute='_compute_fragrantica_display')
    display_brand_logo_url = fields.Char('Brand Logo URL', compute='_compute_fragrantica_display')
    
    # Notes by type (computed)
    display_top_notes_ids = fields.Many2many('fragrantica.note', compute='_compute_fragrantica_notes', string='Top Notes')
    display_middle_notes_ids = fields.Many2many('fragrantica.note', compute='_compute_fragrantica_notes', string='Middle Notes')
    display_base_notes_ids = fields.Many2many('fragrantica.note', compute='_compute_fragrantica_notes', string='Base Notes')
    
    # Accords (computed)
    display_accord_ids = fields.Many2many('fragrantica.accord', compute='_compute_fragrantica_accords', string='Main Accords')
    
    @api.depends('fragrantica_perfume_id', 'fragrantica_use_custom', 'custom_description', 'custom_year')
    def _compute_fragrantica_display(self):
        """Compute display fields based on linked perfume or custom data"""
        for product in self:
            if product.fragrantica_perfume_id:
                perfume = product.fragrantica_perfume_id
                product.display_perfume_name = perfume.name
                product.display_perfume_arabic_name = perfume.arabic_name
                product.display_brand_name = perfume.brand_name
                product.display_year = product.custom_year if product.fragrantica_use_custom and product.custom_year else perfume.year
                product.display_description = product.custom_description if product.fragrantica_use_custom and product.custom_description else perfume.description_full
                product.display_image = perfume.image
                product.display_brand_logo = perfume.brand_logo
                # Always provide URLs for external images
                product.display_image_url = perfume.image_url
                product.display_brand_logo_url = perfume.brand_logo_url
            else:
                product.display_perfume_name = False
                product.display_perfume_arabic_name = False
                product.display_brand_name = False
                product.display_year = product.custom_year if product.fragrantica_use_custom else False
                product.display_description = product.custom_description if product.fragrantica_use_custom else False
                product.display_image = False
                product.display_brand_logo = False
                product.display_image_url = False
                product.display_brand_logo_url = False
    
    @api.depends('fragrantica_perfume_id', 'fragrantica_use_custom', 'custom_note_ids')
    def _compute_fragrantica_notes(self):
        """Compute notes to display"""
        for product in self:
            if product.fragrantica_use_custom and product.custom_note_ids:
                # Use custom notes
                product.display_top_notes_ids = product.custom_note_ids.filtered(lambda n: n.note_type == 'Top').mapped('note_id')
                product.display_middle_notes_ids = product.custom_note_ids.filtered(lambda n: n.note_type == 'Middle').mapped('note_id')
                product.display_base_notes_ids = product.custom_note_ids.filtered(lambda n: n.note_type == 'Base').mapped('note_id')
            elif product.fragrantica_perfume_id:
                # Use Fragrantica data
                product.display_top_notes_ids = product.fragrantica_perfume_id.note_ids.filtered(lambda n: n.note_type == 'Top')
                product.display_middle_notes_ids = product.fragrantica_perfume_id.note_ids.filtered(lambda n: n.note_type == 'Middle')
                product.display_base_notes_ids = product.fragrantica_perfume_id.note_ids.filtered(lambda n: n.note_type == 'Base')
            else:
                product.display_top_notes_ids = False
                product.display_middle_notes_ids = False
                product.display_base_notes_ids = False
    
    @api.depends('fragrantica_perfume_id', 'fragrantica_use_custom', 'custom_accord_ids')
    def _compute_fragrantica_accords(self):
        """Compute accords to display"""
        for product in self:
            if product.fragrantica_use_custom and product.custom_accord_ids:
                # Use custom accords
                product.display_accord_ids = product.custom_accord_ids.mapped('accord_id')
            elif product.fragrantica_perfume_id:
                # Use Fragrantica data
                product.display_accord_ids = product.fragrantica_perfume_id.accord_ids
            else:
                product.display_accord_ids = False
    
    def action_create_pending_request(self):
        """Create a pending request for scraping"""
        self.ensure_one()
        if not self.fragrantica_pending_url:
            return
        
        # Create pending request
        request = self.env['fragrantica.pending.request'].create({
            'fragrantica_url': self.fragrantica_pending_url,
            'product_id': self.id,
            'state': 'pending',
            'notes': f'Requested from product: {self.name}'
        })
        
        self.fragrantica_request_id = request.id
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Request Created',
                'message': 'Pending request created. The perfume will be scraped and added to the database.',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_clear_fragrantica_link(self):
        """Clear Fragrantica link"""
        self.ensure_one()
        self.write({
            'fragrantica_perfume_id': False,
            'fragrantica_pending_url': False,
            'fragrantica_request_id': False,
            'fragrantica_use_custom': False,
        })


class ProductFragranticaNote(models.Model):
    """Custom notes for products (overrides)"""
    _name = 'product.fragrantica.note'
    _description = 'Product Custom Note'
    _order = 'note_type, sequence'
    
    product_id = fields.Many2one('product.template', string='Product', required=True, ondelete='cascade')
    note_id = fields.Many2one('fragrantica.note', string='Note', required=True)
    note_type = fields.Selection(related='note_id.note_type', string='Note Type', store=True)
    sequence = fields.Integer('Sequence', default=10)


class ProductFragranticaAccord(models.Model):
    """Custom accords for products (overrides)"""
    _name = 'product.fragrantica.accord'
    _description = 'Product Custom Accord'
    _order = 'sequence'
    
    product_id = fields.Many2one('product.template', string='Product', required=True, ondelete='cascade')
    accord_id = fields.Many2one('fragrantica.accord', string='Accord', required=True)
    sequence = fields.Integer('Sequence', default=10)

