# -*- coding: utf-8 -*-
import base64
import json
import logging
from odoo import http
from odoo.http import request
from .auth_controller import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class BulkUploadController(http.Controller):
    """Bulk upload operations controller"""
    
    @http.route('/api/documents/bulk-upload/start', 
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def start_bulk_upload(self, department_id, document_type_id, folder_id=None, 
                         confidentiality_level='internal', auto_ocr=False, 
                         auto_barcode=False, create_folder_per_file=False, company_id=None, **kwargs):
        """
        Start a new bulk upload job
        
        Args:
            create_folder_per_file: If True, creates individual folder for each uploaded file
                                   File name becomes both document name and folder name
            company_id: Company/Brand ID for auto-created folders
        
        Returns job_id for tracking
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            # Create bulk upload job
            job = request.env['nbs.bulk.upload.job'].create({
                'department_id': department_id,
                'document_type_id': document_type_id,
                'folder_id': folder_id if folder_id else False,
                'confidentiality_level': confidentiality_level,
                'auto_ocr': auto_ocr,
                'auto_barcode': auto_barcode,
                'create_folder_per_file': create_folder_per_file,  # Store setting
                'company_id': company_id if company_id else False,  # For auto-created folders
                'uploader_id': request.env.user.id,
                'status': 'pending'
            })
            
            return {
                'success': True,
                'message': 'Bulk upload job created',
                'data': {
                    'job_id': job.job_id,
                    'id': job.id
                }
            }
        except Exception as e:
            _logger.error(f'Start bulk upload error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/documents/bulk-upload/<string:job_id>/upload', 
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def bulk_upload_files(self, job_id, files, **kwargs):
        """
        Upload files to existing bulk upload job
        files: list of dicts with keys: file_name, file_data, name, description
        
        Example file entry:
        {
            "file_name": "document.pdf",
            "file_data": "base64_encoded_content",
            "name": "My Document",
            "description": "Optional description"
        }
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            # Find job
            job = request.env['nbs.bulk.upload.job'].search([
                ('job_id', '=', job_id)
            ], limit=1)
            
            if not job:
                return {'success': False, 'error': 'Job not found'}
            
            if job.status not in ['pending']:
                return {'success': False, 'error': f'Job already {job.status}'}
            
            # Process files (ensure files is a list of dicts)
            if not isinstance(files, list):
                files = [files] if isinstance(files, dict) else []
            files_data = []
            for file_info in files:
                if not isinstance(file_info, dict):
                    continue
                # Strip DataURL prefix if present
                file_data = file_info.get('file_data', '')
                if isinstance(file_data, str) and 'base64,' in file_data:
                    file_data = file_data.split('base64,', 1)[1]
                
                files_data.append({
                    'file_name': file_info.get('file_name'),
                    'file_data': file_data,
                    'name': file_info.get('name') or file_info.get('file_name'),
                    'description': file_info.get('description', '')
                })
            
            # Process in background (or sync for now)
            result = job.process_upload(files_data)
            
            return {
                'success': True,
                'message': 'Files uploaded successfully',
                'data': result
            }
        except Exception as e:
            _logger.error(f'Bulk upload files error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/documents/bulk-upload/<string:job_id>/progress', 
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_upload_progress(self, job_id, **kwargs):
        """Get bulk upload job progress"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            job = request.env['nbs.bulk.upload.job'].search([
                ('job_id', '=', job_id)
            ], limit=1)
            
            if not job:
                return {'success': False, 'error': 'Job not found'}
            
            progress_info = job.get_progress_info()
            
            return {
                'success': True,
                'data': progress_info
            }
        except Exception as e:
            _logger.error(f'Get progress error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/documents/bulk-upload/<string:job_id>/cancel', 
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def cancel_upload(self, job_id, **kwargs):
        """Cancel bulk upload job (if not completed)"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            job = request.env['nbs.bulk.upload.job'].search([
                ('job_id', '=', job_id)
            ], limit=1)
            
            if not job:
                return {'success': False, 'error': 'Job not found'}
            
            if job.status in ['completed', 'failed']:
                return {'success': False, 'error': 'Cannot cancel completed/failed job'}
            
            job.write({
                'status': 'failed',
                'completed_at': job.env.context.get('tz'),
                'error_log': 'Cancelled by user'
            })
            
            return {
                'success': True,
                'message': 'Job cancelled successfully'
            }
        except Exception as e:
            _logger.error(f'Cancel upload error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/documents/bulk-upload/jobs', 
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def list_jobs(self, status=None, limit=20, offset=0, **kwargs):
        """List bulk upload jobs for current user"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            domain = [('uploader_id', '=', request.env.user.id)]
            
            if status:
                domain.append(('status', '=', status))
            
            try:
                jobs = request.env['nbs.bulk.upload.job'].sudo().search(
                    domain,
                    limit=limit,
                    offset=offset,
                    order='create_date desc'
                )
                result = []
                for job in jobs:
                    result.append({
                        'job_id': job.job_id,
                        'id': job.id,
                        'name': job.name,
                        'status': job.status,
                        'total_files': job.total_files,
                        'successful_files': job.successful_files,
                        'failed_files': job.failed_files,
                        'progress_percentage': job.progress_percentage,
                        'department': job.department_id.name,
                        'document_type': job.document_type_id.name,
                        'created_at': job.create_date.isoformat() if job.create_date else None,
                        'completed_at': job.completed_at.isoformat() if job.completed_at else None
                    })
                total_count = request.env['nbs.bulk.upload.job'].sudo().search_count(domain)
            except Exception:
                result = []
                total_count = 0
            return {
                'success': True,
                'data': result,
                'total': total_count,
                'limit': limit,
                'offset': offset
            }
        except Exception as e:
            _logger.error(f'List jobs error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
