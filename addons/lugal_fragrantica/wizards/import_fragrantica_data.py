# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import sqlite3
import os
import base64
import logging

_logger = logging.getLogger(__name__)


class ImportFragranticaData(models.TransientModel):
    _name = 'import.fragrantica.data'
    _description = 'Import Fragrantica Data from SQLite'
    
    state = fields.Selection([
        ('start', 'Start'),
        ('progress', 'In Progress'),
        ('done', 'Done')
    ], default='start', string='State')
    
    db_path = fields.Char('Database Path', 
        help='Path to perfumes.db file. Leave empty to use default location.')
    
    import_images = fields.Boolean('Import Images', default=True,
        help='Import images from static folder to Odoo database')
    
    batch_size = fields.Integer('Batch Size', default=500,
        help='Number of records to import per batch (lower = slower but safer)')
    
    # Progress tracking
    total_perfumes = fields.Integer('Total Perfumes', readonly=True)
    imported_perfumes = fields.Integer('Imported Perfumes', readonly=True)
    total_notes = fields.Integer('Total Notes', readonly=True)
    imported_notes = fields.Integer('Imported Notes', readonly=True)
    total_accords = fields.Integer('Total Accords', readonly=True)
    imported_accords = fields.Integer('Imported Accords', readonly=True)
    
    log_message = fields.Text('Import Log', readonly=True)
    
    def _get_db_path(self):
        """Get the path to perfumes.db"""
        if self.db_path and os.path.exists(self.db_path):
            return self.db_path
        
        # Try multiple default paths
        module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Path 1: module/static/fragrantica_data/perfumes.db
        path1 = os.path.join(module_path, 'static', 'fragrantica_data', 'perfumes.db')
        if os.path.exists(path1):
            return path1
        
        # Path 2: module/static/fregran/perfumes.db
        path2 = os.path.join(module_path, 'static', 'fregran', 'perfumes.db')
        if os.path.exists(path2):
            return path2
        
        # Path 3: Project root / fregran (most common)
        # Get to project root (go up from addons/lugal_fragrantica/)
        project_root = os.path.dirname(os.path.dirname(module_path))
        path3 = os.path.join(project_root, 'fregran', 'perfumes.db')
        if os.path.exists(path3):
            return path3
        
        # Path 4: /opt/odoo/fregran/perfumes.db (alternative installation)
        path4 = '/opt/odoo/fregran/perfumes.db'
        if os.path.exists(path4):
            return path4
        
        raise UserError(
            "Database file not found!\n\n"
            f"Looked in:\n"
            f"  - {path1}\n"
            f"  - {path2}\n"
            f"  - {path3}\n"
            f"  - {path4}\n\n"
            "Please:\n"
            "1. Make sure fregran folder exists in project root\n"
            "2. Or copy perfumes.db to addons/lugal_fragrantica/static/fragrantica_data/\n"
            "3. Or specify the full path: /home/lugalai/Lugal-ai/fregran/perfumes.db"
        )
    
    def _log(self, message, save_to_field=True):
        """Add message to log"""
        # Always log to logger
        _logger.info(message)
        
        # Only save important messages to field (to avoid MemoryError)
        if save_to_field and (
            '===' in message or 
            '---' in message or 
            '✓' in message or 
            'ERROR' in message or
            'Found' in message
        ):
            current_log = self.log_message or ""
            self.log_message = current_log + message + "\n"
    
    def action_import_data(self):
        """Start the import process"""
        self.ensure_one()
        
        try:
            db_path = self._get_db_path()
            self._log(f"Database found at: {db_path}")
            
            # Connect to SQLite database
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get totals
            self.total_perfumes = cursor.execute('SELECT COUNT(*) FROM perfumes').fetchone()[0]
            self.total_notes = cursor.execute('SELECT COUNT(*) FROM notes').fetchone()[0]
            self.total_accords = cursor.execute('SELECT COUNT(*) FROM main_accords').fetchone()[0]
            
            self._log(f"Found {self.total_perfumes} perfumes to import")
            self._log(f"Found {self.total_notes} notes to import")
            self._log(f"Found {self.total_accords} accords to import")
            
            self.state = 'progress'
            
            # Import perfumes
            self._import_perfumes(cursor)
            
            # Import notes
            self._import_notes(cursor)
            
            # Import accords
            self._import_accords(cursor)
            
            # Load images if requested
            if self.import_images:
                self._log("Loading images from static folder...")
                self._load_images()
            
            conn.close()
            
            self.state = 'done'
            self._log("\n=== Import completed successfully! ===")
            
        except Exception as e:
            self._log(f"\n!!! ERROR: {str(e)}")
            raise UserError(f"Import failed: {str(e)}")
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'import.fragrantica.data',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
    
    def _import_perfumes(self, cursor):
        """Import perfumes from SQLite"""
        self._log("\n--- Importing Perfumes ---")
        
        FragranticaPerfume = self.env['fragrantica.perfume']
        
        # Clear existing data (optional - you may want to comment this out)
        # existing_count = FragranticaPerfume.search_count([])
        # if existing_count > 0:
        #     self._log(f"Clearing {existing_count} existing perfumes...")
        #     FragranticaPerfume.search([]).unlink()
        
        cursor.execute("""
            SELECT id, url, name, brand_name, brand_logo_url, image_url,
                   description_title, description_full, arabic_name, year
            FROM perfumes
            ORDER BY id
        """)
        
        batch = []
        count = 0
        
        for row in cursor:
            perfume_data = {
                'fragrantica_id': row['id'],
                'url': row['url'],
                'name': row['name'] or 'Unknown',
                'brand_name': row['brand_name'],
                'brand_logo_url': row['brand_logo_url'],
                'image_url': row['image_url'],
                'description_title': row['description_title'],
                'description_full': row['description_full'],
                'arabic_name': row['arabic_name'],
                'year': row['year'],
            }
            
            batch.append(perfume_data)
            count += 1
            
            # Import in batches
            if len(batch) >= self.batch_size:
                FragranticaPerfume.create(batch)
                self.imported_perfumes = count
                self._log(f"Imported {count}/{self.total_perfumes} perfumes...", save_to_field=False)
                batch = []
        
        # Import remaining
        if batch:
            FragranticaPerfume.create(batch)
            self.imported_perfumes = count
        
        self._log(f"✓ Imported {count} perfumes")
    
    def _import_notes(self, cursor):
        """Import notes from SQLite"""
        self._log("\n--- Importing Notes ---")
        
        FragranticaNote = self.env['fragrantica.note']
        FragranticaPerfume = self.env['fragrantica.perfume']
        
        cursor.execute("""
            SELECT id, perfume_id, note_type, note_name, note_image_url, 
                   note_opacity, note_order
            FROM notes
            ORDER BY perfume_id, note_type, note_order
        """)
        
        batch = []
        count = 0
        
        for row in cursor:
            # Find corresponding perfume in Odoo
            perfume = FragranticaPerfume.search([('fragrantica_id', '=', row['perfume_id'])], limit=1)
            
            if not perfume:
                continue
            
            note_data = {
                'perfume_id': perfume.id,
                'note_type': row['note_type'],
                'note_name': row['note_name'],
                'note_image_url': row['note_image_url'],
                'note_opacity': row['note_opacity'] or 0.0,
                'note_order': row['note_order'] or 0,
            }
            
            batch.append(note_data)
            count += 1
            
            if len(batch) >= self.batch_size:
                FragranticaNote.create(batch)
                self.imported_notes = count
                self._log(f"Imported {count}/{self.total_notes} notes...", save_to_field=False)
                batch = []
        
        if batch:
            FragranticaNote.create(batch)
            self.imported_notes = count
        
        self._log(f"✓ Imported {count} notes")
    
    def _import_accords(self, cursor):
        """Import accords from SQLite"""
        self._log("\n--- Importing Accords ---")
        
        FragranticaAccord = self.env['fragrantica.accord']
        FragranticaPerfume = self.env['fragrantica.perfume']
        
        cursor.execute("""
            SELECT id, perfume_id, accord_name, accord_width, 
                   accord_color, accord_order
            FROM main_accords
            ORDER BY perfume_id, accord_order
        """)
        
        batch = []
        count = 0
        
        for row in cursor:
            # Find corresponding perfume in Odoo
            perfume = FragranticaPerfume.search([('fragrantica_id', '=', row['perfume_id'])], limit=1)
            
            if not perfume:
                continue
            
            accord_data = {
                'perfume_id': perfume.id,
                'accord_name': row['accord_name'],
                'accord_width': row['accord_width'] or 0.0,
                'accord_color': row['accord_color'],
                'accord_order': row['accord_order'] or 0,
            }
            
            batch.append(accord_data)
            count += 1
            
            if len(batch) >= self.batch_size:
                FragranticaAccord.create(batch)
                self.imported_accords = count
                self._log(f"Imported {count}/{self.total_accords} accords...", save_to_field=False)
                batch = []
        
        if batch:
            FragranticaAccord.create(batch)
            self.imported_accords = count
        
        self._log(f"✓ Imported {count} accords")
    
    def _load_images(self):
        """Load images from static folder"""
        self._log("\n--- Loading Images ---")
        
        # Load perfume images
        perfumes = self.env['fragrantica.perfume'].search([('image', '=', False)])
        self._log(f"Loading images for {len(perfumes)} perfumes...")
        
        count = 0
        success = 0
        for perfume in perfumes:
            perfume.load_image_from_static()
            count += 1
            if perfume.image:
                success += 1
            if count % 50 == 0:  # كل 50 بدلاً من 100
                self._log(f"Processed {count}/{len(perfumes)} perfumes ({success} images loaded)...", save_to_field=False)
        
        self._log(f"✓ Loaded {success} perfume images out of {count} perfumes")
        
        # Load note images
        notes = self.env['fragrantica.note'].search([('note_image', '=', False)])
        self._log(f"Loading images for {len(notes)} notes...")
        
        count = 0
        success = 0
        for note in notes:
            note.load_image_from_static()
            count += 1
            if note.note_image:
                success += 1
            if count % 100 == 0:
                self._log(f"Processed {count}/{len(notes)} notes ({success} images loaded)...", save_to_field=False)
        
        self._log(f"✓ Loaded {success} note images out of {count} notes")
    
    def action_close(self):
        """Close wizard"""
        return {'type': 'ir.actions.act_window_close'}

