# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
import os

class FragranticaPerfume(models.Model):
    _name = 'fragrantica.perfume'
    _description = 'Fragrantica Perfume'
    _order = 'name'
    
    # Basic Information
    name = fields.Char('Perfume Name (English)', required=True, index=True)
    arabic_name = fields.Char('Perfume Name (Arabic)', index=True)
    brand_name = fields.Char('Brand Name', index=True)
    year = fields.Integer('Release Year')
    
    # URLs
    url = fields.Char('Fragrantica URL')
    image_url = fields.Char('Image URL')
    brand_logo_url = fields.Char('Brand Logo URL')
    
    # Images (stored locally)
    image = fields.Binary('Perfume Image', attachment=True)
    brand_logo = fields.Binary('Brand Logo', attachment=True)
    
    # Description
    description_title = fields.Char('Description Title')
    description_full = fields.Text('Full Description')
    
    # Relations
    note_ids = fields.One2many('fragrantica.note', 'perfume_id', string='Notes')
    accord_ids = fields.One2many('fragrantica.accord', 'perfume_id', string='Main Accords')
    product_ids = fields.One2many('product.template', 'fragrantica_perfume_id', string='Linked Products')
    
    # Computed fields
    top_notes_ids = fields.One2many('fragrantica.note', compute='_compute_notes_by_type', string='Top Notes')
    middle_notes_ids = fields.One2many('fragrantica.note', compute='_compute_notes_by_type', string='Middle Notes')
    base_notes_ids = fields.One2many('fragrantica.note', compute='_compute_notes_by_type', string='Base Notes')
    
    # Metadata
    fragrantica_id = fields.Integer('Original Fragrantica ID', index=True, readonly=True)
    created_at = fields.Datetime('Created At', default=fields.Datetime.now)
    
    _sql_constraints = [
        ('fragrantica_id_unique', 'UNIQUE(fragrantica_id)', 'This perfume already exists in the database!')
    ]
    
    @api.depends('note_ids', 'note_ids.note_type')
    def _compute_notes_by_type(self):
        """Compute notes by type for easier display"""
        for perfume in self:
            perfume.top_notes_ids = perfume.note_ids.filtered(lambda n: n.note_type == 'Top')
            perfume.middle_notes_ids = perfume.note_ids.filtered(lambda n: n.note_type == 'Middle')
            perfume.base_notes_ids = perfume.note_ids.filtered(lambda n: n.note_type == 'Base')
    
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = record.name
            if record.brand_name:
                name = f"{record.brand_name} - {name}"
            if record.year:
                name = f"{name} ({record.year})"
            result.append((record.id, name))
        return result
    
    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        """Enhanced search to include arabic name and brand"""
        args = args or []
        if name:
            domain = ['|', '|', '|',
                ('name', operator, name),
                ('arabic_name', operator, name),
                ('brand_name', operator, name),
                ('description_full', operator, name)
            ]
            return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        return super()._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)
    
    def load_image_from_static(self):
        """Load image from static folder if exists"""
        for perfume in self:
            if perfume.fragrantica_id and not perfume.image:
                # Try multiple image paths
                module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
                # Possible paths for perfume images
                image_paths = [
                    # Path 1: fragrantica_data/images/perfumes/
                    os.path.join(module_path, 'static', 'fragrantica_data', 'images', 'perfumes', f"{perfume.fragrantica_id}.jpg"),
                    # Path 2: fregran/static/images/perfumes/
                    os.path.join(module_path, 'static', 'fregran', 'static', 'images', 'perfumes', f"{perfume.fragrantica_id}.jpg"),
                    # Path 3: /opt/odoo/fregran/static/images/perfumes/
                    f"/opt/odoo/fregran/static/images/perfumes/{perfume.fragrantica_id}.jpg",
                ]
                
                for image_path in image_paths:
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as f:
                            perfume.image = base64.b64encode(f.read())
                        break
            
            # Load brand logo
            if perfume.brand_name and not perfume.brand_logo:
                # Brand images are named by brand name
                brand_filename = perfume.brand_name.lower().replace(' ', '-').replace('.', '') + '.jpg'
                module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
                # Possible paths for brand logos
                brand_paths = [
                    # Path 1: fragrantica_data/images/brands/
                    os.path.join(module_path, 'static', 'fragrantica_data', 'images', 'brands', brand_filename),
                    # Path 2: fregran/static/images/brands/
                    os.path.join(module_path, 'static', 'fregran', 'static', 'images', 'brands', brand_filename),
                    # Path 3: /opt/odoo/fregran/static/images/brands/
                    f"/opt/odoo/fregran/static/images/brands/{brand_filename}",
                ]
                
                for brand_path in brand_paths:
                    if os.path.exists(brand_path):
                        with open(brand_path, 'rb') as f:
                            perfume.brand_logo = base64.b64encode(f.read())
                        break

