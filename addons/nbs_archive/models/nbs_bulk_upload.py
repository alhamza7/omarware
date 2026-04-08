# -*- coding: utf-8 -*-
import uuid
import json
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class NBSBulkUploadJob(models.Model):
    _name = 'nbs.bulk.upload.job'
    _description = 'Bulk Upload Job Tracker'
    _order = 'create_date desc'
    
    job_id = fields.Char(
        string='Job ID',
        required=True,
        index=True,
        default=lambda self: str(uuid.uuid4()),
        readonly=True
    )
    
    name = fields.Char(
        string='Job Name',
        compute='_compute_name',
        store=True
    )
    
    # Status
    status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partially Completed')
    ], string='Status', default='pending', required=True, index=True)
    
    # Counts
    total_files = fields.Integer(string='Total Files', default=0)
    processed_files = fields.Integer(string='Processed Files', default=0)
    successful_files = fields.Integer(string='Successful Files', default=0)
    failed_files = fields.Integer(string='Failed Files', default=0)
    
    # Progress percentage
    progress_percentage = fields.Float(
        string='Progress %',
        compute='_compute_progress',
        store=True
    )
    
    # Relations
    folder_id = fields.Many2one(
        'nbs.document.folder',
        string='Target Folder',
        ondelete='set null'
    )
    
    company_id = fields.Many2one(
        'res.partner',
        string='Company/Brand',
        domain="[('is_company', '=', True)]",
        help='Company for auto-created folders'
    )
    
    department_id = fields.Many2one(
        'nbs.department',
        string='Department',
        required=True
    )
    
    document_type_id = fields.Many2one(
        'nbs.document.type',
        string='Document Type',
        required=True
    )
    
    uploader_id = fields.Many2one(
        'res.users',
        string='Uploader',
        default=lambda self: self.env.user,
        required=True
    )
    
    # Created documents
    created_document_ids = fields.Many2many(
        'nbs.document',
        'bulk_upload_document_rel',
        'job_id',
        'document_id',
        string='Created Documents'
    )
    created_document_count = fields.Integer(
        string='Documents Created',
        compute='_compute_document_count',
        store=True
    )
    
    # Error log
    error_log = fields.Text(string='Error Log')
    
    # Options
    auto_ocr = fields.Boolean(string='Auto OCR', default=False)
    auto_barcode = fields.Boolean(string='Auto Barcode', default=False)
    create_folder_per_file = fields.Boolean(
        string='Create Folder Per File',
        default=False,
        help='If True, creates individual folder for each uploaded file'
    )
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('strict', 'Strict')
    ], string='Confidentiality Level', default='internal')
    
    # Timestamps
    started_at = fields.Datetime(string='Started At')
    completed_at = fields.Datetime(string='Completed At')
    
    @api.depends('job_id', 'create_date')
    def _compute_name(self):
        for job in self:
            if job.create_date:
                job.name = f"Bulk Upload {job.create_date.strftime('%Y-%m-%d %H:%M')}"
            else:
                job.name = f"Bulk Upload Job"
    
    @api.depends('total_files', 'processed_files')
    def _compute_progress(self):
        for job in self:
            if job.total_files > 0:
                job.progress_percentage = (job.processed_files / job.total_files) * 100
            else:
                job.progress_percentage = 0.0
    
    @api.depends('created_document_ids')
    def _compute_document_count(self):
        for job in self:
            job.created_document_count = len(job.created_document_ids)
    
    def process_upload(self, files_data):
        """
        Process bulk file upload
        files_data: list of dicts with keys: file_name, file_data, name, description, create_folder (optional)
        
        If create_folder=True for each file, creates individual folder for each document
        Otherwise, all documents go to job's folder_id (if specified)
        """
        self.ensure_one()
        
        if self.status != 'pending':
            raise ValidationError(_('Job already processing or completed'))
        
        self.write({
            'status': 'processing',
            'started_at': fields.Datetime.now(),
            'total_files': len(files_data)
        })
        
        errors = []
        created_docs = []
        created_folders = []
        
        for idx, file_info in enumerate(files_data):
            try:
                # Determine document name (from file name or provided name)
                doc_name = file_info.get('name') or file_info.get('file_name', '').rsplit('.', 1)[0]
                file_name = file_info.get('file_name')
                
                # Check if should create individual folder for this file
                # Priority: file-level setting > job-level setting
                create_individual_folder = file_info.get('create_folder', self.create_folder_per_file)
                target_folder_id = None
                
                if create_individual_folder:
                    # Create individual folder for this document
                    dept_abbr = self.department_id.code or self.department_id.name[:2].upper()
                    type_abbr = self.document_type_id.code or self.document_type_id.name[:3].upper()
                    folder_code = f"{dept_abbr}-{type_abbr}-{doc_name}"[:64]
                    
                    folder_vals = {
                        'name': doc_name,  # Use document name as folder name
                        'code': folder_code,
                        'department_id': self.department_id.id,
                        'description': f'Auto-created for {doc_name}',
                        'owner_id': self.uploader_id.id,
                        'active': True
                    }
                    # Set company_id if provided in job
                    if self.company_id:
                        folder_vals['company_id'] = self.company_id.id
                    
                    folder = self.env['nbs.document.folder'].create(folder_vals)
                    target_folder_id = folder.id
                    created_folders.append(folder.id)
                    _logger.info(f'Created folder {folder.id} for document: {doc_name}')
                elif self.folder_id:
                    # Use job's folder
                    target_folder_id = self.folder_id.id
                
                # Determine folder_role
                if create_individual_folder:
                    # Each document in its own folder = main document
                    folder_role = 'main'
                elif target_folder_id:
                    # Check if target folder has a main document
                    existing_main = self.env['nbs.document'].search_count([
                        '|',
                        ('folder_id', '=', target_folder_id),
                        ('folder_ids', 'in', [target_folder_id]),
                        ('folder_role', '=', 'main'),
                        ('is_deleted', '=', False)
                    ])
                    folder_role = 'sub' if existing_main > 0 else 'main'
                else:
                    # No folder - standalone
                    folder_role = 'other'
                
                # Create document
                doc_vals = {
                    'name': doc_name,
                    'department_id': self.department_id.id,
                    'document_type_id': self.document_type_id.id,
                    'folder_id': target_folder_id if target_folder_id else False,
                    'folder_role': folder_role,  # SET FOLDER_ROLE!
                    'confidentiality_level': self.confidentiality_level,
                    'state': 'active',
                    'uploader_id': self.uploader_id.id,
                    'is_locked': False,  # Keep unlocked for bulk upload
                }
                
                # Link to folder via Many2many if folder created
                if target_folder_id:
                    doc_vals['folder_ids'] = [(6, 0, [target_folder_id])]
                
                document = self.env['nbs.document'].create(doc_vals)
                
                # Create version instead of attachment for proper file storage
                version_vals = {
                    'document_id': document.id,
                    'version_number': 1,
                    'file_name': file_name,
                    'file_data': file_info.get('file_data'),
                    'uploader_id': self.uploader_id.id,
                    'notes': file_info.get('description') or 'Bulk upload',
                }
                
                version = self.env['nbs.document.version'].create(version_vals)
                
                # Link version to document
                document.write({'current_version_id': version.id})
                
                created_docs.append(document.id)
                
                _logger.info(f'Bulk upload: Created document {document.id} ({doc_name}) with role={folder_role}')
                
                # Update progress
                self.write({
                    'processed_files': idx + 1,
                    'successful_files': len(created_docs)
                })
                
                self.env.cr.commit()  # Commit after each file for progress visibility
                
            except Exception as e:
                error_msg = f"File {idx+1} ({file_info.get('file_name')}): {str(e)}"
                errors.append(error_msg)
                _logger.error(f"Bulk upload error: {error_msg}", exc_info=True)
                
                self.write({
                    'processed_files': idx + 1,
                    'failed_files': self.failed_files + 1
                })
                
                self.env.cr.commit()
        
        # Final status
        if len(created_docs) == len(files_data):
            final_status = 'completed'
        elif len(created_docs) > 0:
            final_status = 'partial'
        else:
            final_status = 'failed'
        
        self.write({
            'status': final_status,
            'completed_at': fields.Datetime.now(),
            'created_document_ids': [(6, 0, created_docs)],
            'error_log': '\n'.join(errors) if errors else False
        })
        
        return {
            'status': final_status,
            'total': len(files_data),
            'successful': len(created_docs),
            'failed': len(errors),
            'errors': errors
        }
    
    def get_progress_info(self):
        """Get current progress information"""
        self.ensure_one()
        
        return {
            'job_id': self.job_id,
            'status': self.status,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'successful_files': self.successful_files,
            'failed_files': self.failed_files,
            'progress_percentage': self.progress_percentage,
            'created_documents': len(self.created_document_ids),
            'error_log': self.error_log,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
