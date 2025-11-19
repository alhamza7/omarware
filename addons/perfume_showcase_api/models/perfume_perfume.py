# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PerfumePerfume(models.Model):
    _name = 'perfume.perfume'
    _description = 'Perfume'
    _order = 'name'

    # All text fields are non-translatable to avoid JSONB translation logic
    # that relies on jsonb_path_query_first on some PostgreSQL versions.
    name = fields.Char(string='Perfume Name', required=True, translate=False)
    code = fields.Char(string='Perfume Code', required=True, help='Unique identifier for API (e.g., lv-1)')
    brand_id = fields.Many2one('perfume.brand', string='Brand', required=True, ondelete='cascade')
    brand_name = fields.Char(string='Brand Name', related='brand_id.name', store=True, readonly=True)
    image = fields.Image(string='Image', max_width=1920, max_height=1920)
    image_url = fields.Char(string='Image URL', help='External image URL (alternative to uploaded image)')

    # Season and Occasion (Many2many for flexibility)
    season_ids = fields.Many2many(
        'perfume.season',
        'perfume_perfume_season_rel',
        'perfume_id',
        'season_id',
        string='Seasons'
    )
    season_display = fields.Char(string='Seasons', compute='_compute_season_display', store=False)
    
    occasion_ids = fields.Many2many(
        'perfume.occasion',
        'perfume_perfume_occasion_rel',
        'perfume_id',
        'occasion_id',
        string='Occasions'
    )
    occasion_display = fields.Char(string='Occasions', compute='_compute_occasion_display', store=False)

    # Tags for filtering and sharing
    tag_ids = fields.Many2many(
        'perfume.tag',
        'perfume_perfume_tag_rel',
        'perfume_id',
        'tag_id',
        string='Tags',
    )

    longevity = fields.Char(string='Longevity', translate=False, help='e.g., 8-10 hours')
    sillage = fields.Char(string='Sillage', translate=False, help='e.g., Heavy, Moderate, Light')
    description = fields.Text(string='Description', translate=False)
    
    # Notes - separated by category
    top_note_ids = fields.Many2many(
        'perfume.note',
        'perfume_perfume_top_note_rel',
        'perfume_id',
        'note_id',
        string='Top Notes',
        domain=[('category', '=', 'top')]
    )
    middle_note_ids = fields.Many2many(
        'perfume.note',
        'perfume_perfume_middle_note_rel',
        'perfume_id',
        'note_id',
        string='Middle Notes',
        domain=[('category', '=', 'middle')]
    )
    base_note_ids = fields.Many2many(
        'perfume.note',
        'perfume_perfume_base_note_rel',
        'perfume_id',
        'note_id',
        string='Base Notes',
        domain=[('category', '=', 'base')]
    )
    
    active = fields.Boolean(string='Active', default=True)
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Perfume code must be unique!'),
    ]

    @api.depends('season_ids')
    def _compute_season_display(self):
        for perfume in self:
            perfume.season_display = ', '.join(perfume.season_ids.mapped('name'))

    @api.depends('occasion_ids')
    def _compute_occasion_display(self):
        for perfume in self:
            perfume.occasion_display = ', '.join(perfume.occasion_ids.mapped('name'))

    def get_api_data(self):
        """Get perfume data formatted for API"""
        self.ensure_one()
        
        # Get image URL
        image_url = self.image_url
        if not image_url and self.image:
            # Generate URL for stored image
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            image_url = f"{base_url}/web/image/perfume.perfume/{self.id}/image"
        
        return {
            'id': self.code,
            'name': self.name,
            'brand': self.brand_id.name,
            'brandId': self.brand_id.code or '',
            'image': image_url or '',
            'season': self.season_ids.mapped('name'),
            'occasion': self.occasion_ids.mapped('name'),
            'longevity': self.longevity or '',
            'sillage': self.sillage or '',
            'description': self.description or '',
            'notes': {
                'top': self.top_note_ids.mapped('name'),
                'middle': self.middle_note_ids.mapped('name'),
                'base': self.base_note_ids.mapped('name'),
            },
            'tags': [
                {
                    'id': tag.code or str(tag.id),
                    'name': tag.name,
                }
                for tag in self.tag_ids
            ],
        }


class PerfumeSeason(models.Model):
    _name = 'perfume.season'
    _description = 'Perfume Season'
    _order = 'name'

    name = fields.Char(string='Season Name', required=True, translate=False)
    # used by many2many_tags color_field in views
    color = fields.Integer(string='Color Index')
    active = fields.Boolean(string='Active', default=True)
    perfumes = fields.Many2many(
        'perfume.perfume',
        'perfume_perfume_season_rel',
        'season_id',
        'perfume_id',
        string='Perfumes',
        readonly=True
    )


class PerfumeOccasion(models.Model):
    _name = 'perfume.occasion'
    _description = 'Perfume Occasion'
    _order = 'name'

    name = fields.Char(string='Occasion Name', required=True, translate=False)
    # used by many2many_tags color_field in views
    color = fields.Integer(string='Color Index')
    active = fields.Boolean(string='Active', default=True)
    perfumes = fields.Many2many(
        'perfume.perfume',
        'perfume_perfume_occasion_rel',
        'occasion_id',
        'perfume_id',
        string='Perfumes',
        readonly=True
    )

