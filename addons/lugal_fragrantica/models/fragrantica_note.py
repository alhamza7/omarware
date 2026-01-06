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
    
    def load_image_from_static(self):
        """Load note image from static folder if exists"""
        for note in self:
            if note.note_name and not note.note_image:
                module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                # Note images are named by note name
                note_filename = note.note_name.lower().replace(' ', '-').replace('.', '') + '.jpg'
                
                # Possible paths for note images
                note_paths = [
                    # Path 1: fragrantica_data/images/notes/
                    os.path.join(module_path, 'static', 'fragrantica_data', 'images', 'notes', note_filename),
                    # Path 2: fregran/static/images/notes/
                    os.path.join(module_path, 'static', 'fregran', 'static', 'images', 'notes', note_filename),
                    # Path 3: /opt/odoo/fregran/static/images/notes/
                    f"/opt/odoo/fregran/static/images/notes/{note_filename}",
                ]
                
                for note_path in note_paths:
                    if os.path.exists(note_path):
                        with open(note_path, 'rb') as f:
                            note.note_image = base64.b64encode(f.read())
                        break
    
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"{record.note_type}: {record.note_name}"
            result.append((record.id, name))
        return result

