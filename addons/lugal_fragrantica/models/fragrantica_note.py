# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
import os

class FragranticaNote(models.Model):
    _name = 'fragrantica.note'
    _description = 'Fragrantica Perfume Note'
    _order = 'perfume_id, note_type, note_order'
    
    perfume_id = fields.Many2one('fragrantica.perfume', string='Perfume', required=True, ondelete='cascade', index=True)
    
    note_type = fields.Selection([
        ('Top', 'Top Notes'),
        ('Middle', 'Middle Notes'),
        ('Base', 'Base Notes')
    ], string='Note Type', required=True)
    
    note_name = fields.Char('Note Name', required=True)
    note_image_url = fields.Char('Note Image URL')
    note_image = fields.Binary('Note Image', attachment=True)
    note_opacity = fields.Float('Opacity', help='Visual opacity/intensity of the note')
    note_order = fields.Integer('Display Order', default=0)
    
    # Display URL if image not loaded
    display_note_image_url = fields.Char('Display Note Image URL', compute='_compute_display_image_url')
    
    @api.depends('note_image', 'note_image_url')
    def _compute_display_image_url(self):
        """Return image URL if local image not available"""
        for note in self:
            note.display_note_image_url = note.note_image_url if not note.note_image and note.note_image_url else False
    
    def load_image_from_static(self):
        """Load note image from static folder if exists"""
        for note in self:
            if note.note_name and not note.note_image:
                module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                # Note images are named by note name
                note_filename = note.note_name.lower().replace(' ', '-').replace('.', '') + '.jpg'
                
                # Possible paths for note images
                module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                project_root = os.path.dirname(os.path.dirname(module_path))
                
                note_paths = [
                    # Path 1: fragrantica_data/images/notes/
                    os.path.join(module_path, 'static', 'fragrantica_data', 'images', 'notes', note_filename),
                    # Path 2: fregran/static/images/notes/
                    os.path.join(module_path, 'static', 'fregran', 'static', 'images', 'notes', note_filename),
                    # Path 3: Project root / fregran
                    os.path.join(project_root, 'fregran', 'static', 'images', 'notes', note_filename),
                    # Path 4: /opt/odoo/fregran (alternative)
                    f"/opt/odoo/fregran/static/images/notes/{note_filename}",
                ]
                
                for note_path in note_paths:
                    if os.path.exists(note_path):
                        with open(note_path, 'rb') as f:
                            note.note_image = base64.b64encode(f.read())
                        break
    
    def download_image_from_url(self):
        """Download note image from external URL"""
        import requests
        
        for note in self:
            if not note.note_image and note.note_image_url:
                try:
                    response = requests.get(note.note_image_url, timeout=10)
                    if response.status_code == 200:
                        note.note_image = base64.b64encode(response.content)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Failed to download note image for {note.note_name}: {e}")
    
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"{record.note_type}: {record.note_name}"
            result.append((record.id, name))
        return result

