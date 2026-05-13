# -*- coding: utf-8 -*-
import base64
import hashlib
import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class BulkUploadController(http.Controller):
    """Bulk upload operations controller"""

    # ═══════════════════════════════════════════════════════════════════════════
    # /api/documents/upload/single  — one request per file, no base64 in memory
    #
    # Writes the raw binary body DIRECTLY to the Odoo filestore (same as
    # ir.attachment does internally) so we never hold a base64-encoded copy in
    # RAM.  Peak memory per request = file size (not 1.4× file size).
    # OCR is always deferred to the background.
    # ═══════════════════════════════════════════════════════════════════════════
    @http.route(
        '/api/documents/upload/single',
        type='http', auth='none', methods=['POST'], csrf=False, cors='*',
    )
    def upload_single_fast(self, **kwargs):
        """
        Upload ONE file — returns document_id immediately.  OCR runs in background.

        ── Authentication ──────────────────────────────────────────────────────
        Header:  Authorization: Bearer <jwt_token>

        ── Preferred: RAW BINARY body (fastest, no FormData overhead) ──────────
        Send raw file bytes as the HTTP body.  Pass metadata in headers:

          X-Department-Id        (int, required)
          X-Document-Type-Id     (int, required)
          X-File-Name            (string, required)   e.g. "invoice.pdf"
          X-Doc-Name             (string, optional)   display name (defaults to stem)
          X-Company-Id           (int, optional)
          X-Confidentiality      (string, optional)   public|internal|confidential|strict
          X-Create-Folder        (bool, optional)     true|false  (default: false when X-Folder-Id given)
          X-Auto-Ocr             (bool, optional)     true|false  (default: true)
          X-Folder-Id            (int, optional)      existing folder — skips auto-create
          X-Upload-Kind          (string, optional)   main|sub|other  (default: auto)
          Content-Type:          <mime>               e.g. application/pdf

        ── Alternative: multipart/form-data ────────────────────────────────────
        Field "file"              binary, required
        Field "department_id"     int, required
        Field "document_type_id"  int, required
        Field "file_name"         string, optional
        Field "name"              string, optional
        Field "company_id"        int, optional
        Field "confidentiality_level" string, optional
        Field "create_folder"     bool, optional
        Field "auto_ocr"          bool, optional
        Field "folder_id"         int, optional
        Field "upload_kind"       string, optional   main|sub|other

        ── Response 200 ────────────────────────────────────────────────────────
        {
          "success": true,
          "document_id": 123,
          "document_name": "invoice",
          "barcode": "NBS000123",
          "folder_id": 45,
          "folder_name": "invoice",
          "ocr_queued": true
        }
        """
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response(
                    {'success': False, 'error': 'Unauthorized'}, status=401
                )

            env = request.env
            content_type = (request.httprequest.content_type or '').lower()

            raw_bytes       = None
            file_name       = None
            doc_name        = None
            department_id   = None
            doc_type_id     = None
            company_id      = None
            folder_id       = None
            upload_kind     = None
            confidentiality = 'internal'
            create_folder   = True
            auto_ocr        = True

            # ── PATH A: Raw binary body ────────────────────────────────────────
            if (
                not content_type.startswith('application/json')
                and not content_type.startswith('multipart/')
                and not content_type.startswith('application/x-www-form-urlencoded')
            ):
                raw_bytes = request.httprequest.get_data()
                h = request.httprequest.headers
                file_name       = h.get('X-File-Name') or h.get('X-Filename') or 'file'
                doc_name        = h.get('X-Doc-Name') or h.get('X-Name') or file_name.rsplit('.', 1)[0]
                department_id   = h.get('X-Department-Id')
                doc_type_id     = h.get('X-Document-Type-Id')
                company_id      = h.get('X-Company-Id') or None
                folder_id       = h.get('X-Folder-Id') or None
                upload_kind     = h.get('X-Upload-Kind') or None
                confidentiality = h.get('X-Confidentiality') or 'internal'
                cf = (h.get('X-Create-Folder') or '').lower()
                create_folder = cf not in ('false', '0', 'no') if cf else True
                ao = (h.get('X-Auto-Ocr') or '').lower()
                auto_ocr = ao not in ('false', '0', 'no') if ao else True

            # ── PATH B: multipart/form-data ────────────────────────────────────
            elif content_type.startswith('multipart/'):
                mp_files  = request.httprequest.files
                mp_form   = request.httprequest.form
                mp_upload = None
                for _fname in ('file', 'document', 'upload', 'attachment'):
                    if _fname in mp_files:
                        mp_upload = mp_files[_fname]
                        break
                    if f'{_fname}[]' in mp_files:
                        mp_upload = mp_files[f'{_fname}[]']
                        break
                if mp_upload is None:
                    return request.make_json_response(
                        {'success': False,
                         'error': 'No file found. Use field name "file" in the multipart form.'},
                        status=400,
                    )
                raw_bytes       = mp_upload.read()
                file_name       = mp_form.get('file_name') or mp_upload.filename or 'file'
                doc_name        = mp_form.get('name') or file_name.rsplit('.', 1)[0]
                department_id   = mp_form.get('department_id')
                doc_type_id     = mp_form.get('document_type_id')
                company_id      = mp_form.get('company_id') or None
                folder_id       = mp_form.get('folder_id') or None
                upload_kind     = mp_form.get('upload_kind') or None
                confidentiality = mp_form.get('confidentiality_level', 'internal')
                cf = (mp_form.get('create_folder') or '').lower()
                create_folder = cf not in ('false', '0', 'no') if cf else True
                ao = (mp_form.get('auto_ocr') or '').lower()
                auto_ocr = ao not in ('false', '0', 'no') if ao else True

            else:
                return request.make_json_response({
                    'success': False,
                    'error': (
                        'Unsupported Content-Type. '
                        'Use raw binary body or multipart/form-data.'
                    )
                }, status=400)

            if not raw_bytes:
                return request.make_json_response(
                    {'success': False, 'error': 'Empty file body received.'}, status=400
                )

            # ── Validate required fields ───────────────────────────────────────
            if not department_id:
                return request.make_json_response(
                    {'success': False,
                     'error': 'department_id is required (X-Department-Id header or form field).'},
                    status=400,
                )
            if not doc_type_id:
                return request.make_json_response(
                    {'success': False,
                     'error': 'document_type_id is required (X-Document-Type-Id header or form field).'},
                    status=400,
                )
            try:
                department_id = int(department_id)
                doc_type_id   = int(doc_type_id)
                company_id    = int(company_id) if company_id else False
                folder_id     = int(folder_id)  if folder_id  else False
            except (ValueError, TypeError):
                return request.make_json_response(
                    {'success': False, 'error': 'department_id and document_type_id must be integers.'},
                    status=400,
                )

            # If an existing folder is supplied, never auto-create a new one
            if folder_id:
                create_folder = False

            # ── Write directly to Odoo filestore — NO base64 in memory ─────────
            # Peak RAM = len(raw_bytes) only.  Odoo GC cleans up the file if the
            # transaction is rolled back (same as ir.attachment does internally).
            IrAttachment = env['ir.attachment'].sudo()
            file_size = len(raw_bytes)
            checksum  = IrAttachment._compute_checksum(raw_bytes)
            store_fname = IrAttachment._file_write(raw_bytes, checksum)
            mime_type   = content_type.split(';')[0].strip() or 'application/octet-stream'
            del raw_bytes   # ← free the 52 MB / 80 MB buffer immediately

            # ── Create a lightweight job to track the upload ───────────────────
            job = env['nbs.bulk.upload.job'].create({
                'department_id':          department_id,
                'document_type_id':       doc_type_id,
                'company_id':             company_id or False,
                'folder_id':              folder_id or False,
                'confidentiality_level':  confidentiality or 'internal',
                'create_folder_per_file': create_folder,
                'auto_ocr':               auto_ocr,
                'uploader_id':            env.user.id,
                'status':                 'processing',
                'total_files':            1,
            })

            # ── Process: create folder + document + version (no base64) ────────
            result = job.process_single_file({
                'file_name':   file_name,
                'file_data':   None,         # no base64 needed
                'store_fname': store_fname,  # pre-written to filestore
                'file_size':   file_size,
                'checksum':    checksum,
                'mimetype':    mime_type,
                'name':        doc_name,
                'upload_kind': upload_kind,
                'description': 'Uploaded via /api/documents/upload/single',
            })

            job.finalize_job()

            if not result.get('success'):
                return request.make_json_response(
                    {'success': False, 'error': result.get('error', 'Upload failed')},
                    status=500,
                )

            doc = env['nbs.document'].browse(result['document_id'])
            return request.make_json_response({
                'success':       True,
                'document_id':   result['document_id'],
                'document_name': doc.name if doc.exists() else doc_name,
                'barcode':       doc.barcode if doc.exists() else None,
                'folder_id':     result.get('folder_id'),
                'folder_name':   result.get('folder_name'),
                'ocr_queued':    auto_ocr,
            })

        except Exception as exc:
            _logger.error('upload_single_fast error: %s', exc, exc_info=True)
            return request.make_json_response(
                {'success': False, 'error': str(exc)}, status=500
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # /api/documents/upload/all — send ALL files in one multipart request
    # (the backend processes them one by one, no base64 for any file)
    # ═══════════════════════════════════════════════════════════════════════════
    @http.route(
        '/api/documents/upload/all',
        type='http', auth='none', methods=['POST'], csrf=False, cors='*',
    )
    def upload_all_files(self, **kwargs):
        """
        Upload multiple files in a single multipart/form-data request.
        Each file is written directly to the filestore — no base64 in memory.

        Form fields:
          department_id          int, required
          document_type_id       int, required
          file (repeated)        binary, required (repeat this field for each file)
          folder_id              int, optional
          company_id             int, optional
          confidentiality_level  string, optional
          create_folder_per_file bool, optional  (default: false when folder_id given)
          auto_ocr               bool, optional  (default: true)
        """
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response(
                    {'success': False, 'error': 'Unauthorized'}, status=401
                )

            form = request.httprequest.form
            files_storage = request.httprequest.files

            def _form_bool(key, default=True):
                val = form.get(key, '')
                if val == '':
                    return default
                return str(val).lower() in ('1', 'true', 'yes')

            department_id    = form.get('department_id')
            document_type_id = form.get('document_type_id')
            if not department_id or not document_type_id:
                return request.make_json_response(
                    {'success': False, 'error': 'department_id and document_type_id are required'},
                    status=400,
                )

            company_id      = form.get('company_id') or False
            confidentiality = form.get('confidentiality_level', 'internal')
            folder_id       = form.get('folder_id') or False
            create_folder   = _form_bool('create_folder_per_file', True)
            auto_ocr        = _form_bool('auto_ocr', True)

            # If an existing folder is supplied, never auto-create a new one
            if folder_id:
                create_folder = False

            # Collect all uploaded files
            uploaded = []
            for field_name in ('file', 'files', 'file[]', 'files[]'):
                for f in files_storage.getlist(field_name):
                    if f and f.filename:
                        uploaded.append(f)

            if not uploaded:
                return request.make_json_response(
                    {'success': False,
                     'error': 'No files received. Send files in a multipart field named "file".'},
                    status=400,
                )

            env = request.env
            IrAttachment = env['ir.attachment'].sudo()

            job = env['nbs.bulk.upload.job'].create({
                'department_id':          int(department_id),
                'document_type_id':       int(document_type_id),
                'folder_id':              int(folder_id) if folder_id else False,
                'company_id':             int(company_id) if company_id else False,
                'confidentiality_level':  confidentiality,
                'create_folder_per_file': create_folder,
                'auto_ocr':               auto_ocr,
                'uploader_id':            env.user.id,
                'status':                 'processing',
                'total_files':            len(uploaded),
            })

            results = []
            for upload_file in uploaded:
                raw_bytes = upload_file.read()
                file_name = upload_file.filename or 'file'
                doc_name  = file_name.rsplit('.', 1)[0]
                mime_type = upload_file.content_type or 'application/octet-stream'

                # Write directly to filestore — no base64
                file_size   = len(raw_bytes)
                checksum    = IrAttachment._compute_checksum(raw_bytes)
                store_fname = IrAttachment._file_write(raw_bytes, checksum)
                del raw_bytes   # free immediately

                res = job.process_single_file({
                    'file_name':   file_name,
                    'file_data':   None,
                    'store_fname': store_fname,
                    'file_size':   file_size,
                    'checksum':    checksum,
                    'mimetype':    mime_type,
                    'name':        doc_name,
                    'description': 'Bulk upload',
                })
                results.append({
                    'file_name':        file_name,
                    'success':          res.get('success', False),
                    'document_id':      res.get('document_id'),
                    'folder_id':        res.get('folder_id'),
                    'parent_folder_name': res.get('folder_name'),
                    'error':            res.get('error'),
                })

            final_status = job.finalize_job()

            return request.make_json_response({
                'success':    True,
                'job_id':     job.job_id,
                'status':     final_status,
                'total':      job.total_files,
                'successful': job.successful_files,
                'failed':     job.failed_files,
                'error_log':  job.error_log or None,
                'documents':  results,
            })

        except Exception as exc:
            _logger.error('upload_all_files error: %s', exc, exc_info=True)
            return request.make_json_response(
                {'success': False, 'error': str(exc)}, status=500
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # Legacy endpoints (kept for backward compatibility)
    # ═══════════════════════════════════════════════════════════════════════════
    @http.route('/api/documents/bulk-upload/start',
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def start_bulk_upload(self, department_id, document_type_id, folder_id=None,
                          confidentiality_level='internal', auto_ocr=False,
                          auto_barcode=False, create_folder_per_file=False,
                          company_id=None, **kwargs):
        """Start a new bulk upload job — returns job_id for tracking."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            job = request.env['nbs.bulk.upload.job'].create({
                'department_id':          department_id,
                'document_type_id':       document_type_id,
                'folder_id':              folder_id if folder_id else False,
                'confidentiality_level':  confidentiality_level,
                'auto_ocr':               auto_ocr,
                'auto_barcode':           auto_barcode,
                'create_folder_per_file': create_folder_per_file,
                'company_id':             company_id if company_id else False,
                'uploader_id':            request.env.user.id,
                'status':                 'pending',
            })
            return {
                'success': True,
                'message': 'Bulk upload job created',
                'data': {'job_id': job.job_id, 'id': job.id},
            }
        except Exception as e:
            _logger.error('Start bulk upload error: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/api/documents/bulk-upload/<string:job_id>/progress',
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_upload_progress(self, job_id, **kwargs):
        """Get bulk upload job progress."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            job = request.env['nbs.bulk.upload.job'].search(
                [('job_id', '=', job_id)], limit=1
            )
            if not job:
                return {'success': False, 'error': 'Job not found'}

            return {'success': True, 'data': job.get_progress_info()}
        except Exception as e:
            _logger.error('Get progress error: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/api/documents/bulk-upload/jobs',
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def list_jobs(self, status=None, limit=20, offset=0, **kwargs):
        """List bulk upload jobs for current user."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            domain = [('uploader_id', '=', request.env.user.id)]
            if status:
                domain.append(('status', '=', status))

            try:
                jobs = request.env['nbs.bulk.upload.job'].sudo().search(
                    domain, limit=limit, offset=offset, order='create_date desc'
                )
                result = [{
                    'job_id':              job.job_id,
                    'id':                  job.id,
                    'name':                job.name,
                    'status':              job.status,
                    'total_files':         job.total_files,
                    'successful_files':    job.successful_files,
                    'failed_files':        job.failed_files,
                    'progress_percentage': job.progress_percentage,
                    'department':          job.department_id.name,
                    'document_type':       job.document_type_id.name,
                    'created_at':          job.create_date.isoformat() if job.create_date else None,
                    'completed_at':        job.completed_at.isoformat() if job.completed_at else None,
                } for job in jobs]
                total_count = request.env['nbs.bulk.upload.job'].sudo().search_count(domain)
            except Exception:
                result = []
                total_count = 0

            return {
                'success': True,
                'data':    result,
                'total':   total_count,
                'limit':   limit,
                'offset':  offset,
            }
        except Exception as e:
            _logger.error('List jobs error: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}
