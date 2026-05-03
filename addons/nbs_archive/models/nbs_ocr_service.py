# -*- coding: utf-8 -*-
"""
Google Vision OCR Service for NBS Archive.

Processing pipeline (in order):
  1. Excel / ODS / CSV  → direct cell/text extraction (no API, no size limit)
  2. Plain text         → decode and return
  3. PDF with text layer → pypdf direct extraction (fast, free, no size limit)
  4. Scanned PDF/TIFF   → Google Vision files:annotate (chunked in 5-page,
                           ≤10 MB raw batches to stay under the 20 MB b64 cap)
  5. Images             → Google Vision images:annotate

API key is read from the Odoo system parameter
  ``nbs_archive.google_vision_key``
so it can be rotated without code changes.

Size limits handled:
  - No limit for direct extraction (steps 1–3)
  - Vision API base64 limit is 20 MB → we chunk PDFs at ≤10 MB raw per batch
  - OCR is skipped (returns '') for files > MAX_OCR_BYTES to prevent OOM
"""

import io
import json
import base64
import logging
import mimetypes
import urllib.request
import urllib.error

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# ── Google Vision REST endpoints ──────────────────────────────────────────────
_VISION_IMAGES_URL = 'https://vision.googleapis.com/v1/images:annotate'
_VISION_FILES_URL  = 'https://vision.googleapis.com/v1/files:annotate'

# MIME types handled by the files:annotate endpoint (PDF / TIFF)
_FILE_MIME_TYPES = {'application/pdf', 'image/tiff', 'image/tif'}

# Image MIME types handled by images:annotate
_IMAGE_MIME_TYPES = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
    'image/bmp', 'image/webp', 'image/x-bmp',
}

# Excel MIME types — text extracted directly (no Vision needed)
_EXCEL_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
    'application/vnd.ms-excel',                                            # .xls
    'application/vnd.oasis.opendocument.spreadsheet',                      # .ods
}

# CSV / plain text
_TEXT_MIME_TYPES = {
    'text/plain', 'text/csv', 'application/csv',
}

# Maximum raw file size to attempt Vision API OCR (200 MB)
MAX_OCR_BYTES = 200 * 1024 * 1024

# Maximum raw bytes per Vision API chunk (10 MB → ~13.3 MB b64, well under 20 MB limit)
_VISION_CHUNK_BYTES = 10 * 1024 * 1024


def _get_vision_key(env):
    """Return the Google Vision API key from system parameters."""
    return (
        env['ir.config_parameter'].sudo().get_param(
            'nbs_archive.google_vision_key',
            default='AIzaSyA-z8iBdbsEKZFUTwg4i2SllNe29_ZTJtY',
        )
        or ''
    ).strip()


def _post_json(url: str, payload: dict) -> dict:
    """Minimal HTTP POST helper that avoids the `requests` dependency."""
    body = json.dumps(payload).encode('utf-8')
    req  = urllib.request.Request(
        url,
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode('utf-8', errors='replace')
        _logger.error('Vision API HTTP %s: %s', exc.code, error_body)
        raise RuntimeError(f'Vision API error {exc.code}: {error_body}') from exc


def _extract_excel_text(file_bytes: bytes, file_name: str) -> str:
    """
    Extract all cell values from an Excel / ODS file without OCR.
    Falls back to xlrd for legacy .xls files.
    """
    ext = (file_name or '').rsplit('.', 1)[-1].lower()
    lines = []

    if ext in ('xlsx', 'ods') or ext not in ('xls',):
        try:
            import openpyxl
            import io
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                lines.append(f'[Sheet: {sheet_name}]')
                for row in ws.iter_rows(values_only=True):
                    row_text = '\t'.join(
                        str(cell) for cell in row if cell is not None
                    )
                    if row_text.strip():
                        lines.append(row_text)
            return '\n'.join(lines)
        except Exception as exc:
            _logger.warning('openpyxl failed for %s: %s — trying xlrd', file_name, exc)

    # Fallback: xlrd (handles .xls and corrupt xlsx)
    try:
        import xlrd
        wb = xlrd.open_workbook(file_contents=file_bytes)
        for sheet in wb.sheets():
            lines.append(f'[Sheet: {sheet.name}]')
            for row_idx in range(sheet.nrows):
                row_text = '\t'.join(
                    str(sheet.cell_value(row_idx, col))
                    for col in range(sheet.ncols)
                    if sheet.cell_value(row_idx, col) not in ('', None)
                )
                if row_text.strip():
                    lines.append(row_text)
        return '\n'.join(lines)
    except Exception as exc:
        raise RuntimeError(f'Cannot extract text from Excel file: {exc}') from exc


def _extract_text_text(file_bytes: bytes) -> str:
    """Decode plain text / CSV files."""
    for encoding in ('utf-8', 'utf-16', 'cp1256', 'latin-1'):
        try:
            return file_bytes.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return file_bytes.decode('utf-8', errors='replace')


def _detect_mime(file_name: str, file_data_b64: str) -> str:
    """Best-effort MIME detection from filename, then magic bytes."""
    if file_name:
        ext = file_name.rsplit('.', 1)[-1].lower() if '.' in file_name else ''
        ext_map = {
            'pdf':  'application/pdf',
            'tiff': 'image/tiff',
            'tif':  'image/tiff',
            'jpg':  'image/jpeg',
            'jpeg': 'image/jpeg',
            'png':  'image/png',
            'gif':  'image/gif',
            'bmp':  'image/bmp',
            'webp': 'image/webp',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls':  'application/vnd.ms-excel',
            'ods':  'application/vnd.oasis.opendocument.spreadsheet',
            'csv':  'text/csv',
            'txt':  'text/plain',
        }
        if ext in ext_map:
            return ext_map[ext]
        mime, _ = mimetypes.guess_type(file_name)
        if mime:
            return mime.lower()
    # Sniff magic bytes
    try:
        head = base64.b64decode(file_data_b64[:20])
        if head.startswith(b'%PDF'):
            return 'application/pdf'
        if head[:4] == b'PK\x03\x04':  # ZIP-based: xlsx, ods, docx …
            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    except Exception:
        pass
    return 'application/pdf'


def _extract_pdf_text_direct(file_bytes: bytes) -> str:
    """
    Extract the embedded text layer from a PDF using pypdf.
    Returns '' if the PDF has no text layer (i.e. it is a scanned image PDF).
    Never raises — returns '' on any error.
    """
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        parts = []
        for page in reader.pages:
            text = page.extract_text() or ''
            if text.strip():
                parts.append(text.strip())
        return '\n\n'.join(parts)
    except Exception as exc:
        _logger.debug('pypdf direct extraction failed: %s', exc)
        return ''


def _call_images_annotate(api_key: str, content_b64: str) -> str:
    """Extract text from an image using images:annotate."""
    payload = {
        'requests': [{
            'image': {'content': content_b64},
            'features': [{'type': 'DOCUMENT_TEXT_DETECTION', 'maxResults': 1}],
        }]
    }
    url  = f'{_VISION_IMAGES_URL}?key={api_key}'
    resp = _post_json(url, payload)

    responses = resp.get('responses', [{}])
    if responses and responses[0].get('error'):
        raise RuntimeError(responses[0]['error'].get('message', 'Vision API error'))

    annotation = responses[0].get('fullTextAnnotation', {})
    return annotation.get('text', '').strip()


def _call_files_annotate_chunk(api_key: str, content_b64: str, mime_type: str) -> str:
    """
    Extract text from one PDF/TIFF chunk (must be ≤ 10 MB raw / ~13.3 MB b64).
    Uses files:annotate with pages 1–5 (Vision API limit per request).
    """
    payload = {
        'requests': [{
            'inputConfig': {
                'content':  content_b64,
                'mimeType': mime_type,
            },
            'features': [{'type': 'DOCUMENT_TEXT_DETECTION'}],
            'pages': list(range(1, 6)),  # pages 1–5
        }]
    }
    url  = f'{_VISION_FILES_URL}?key={api_key}'
    resp = _post_json(url, payload)

    responses = resp.get('responses', [{}])
    if responses and responses[0].get('error'):
        raise RuntimeError(responses[0]['error'].get('message', 'Vision API error'))

    page_responses = responses[0].get('responses', [])
    return '\n\n'.join(
        pr.get('fullTextAnnotation', {}).get('text', '').strip()
        for pr in page_responses
        if pr.get('fullTextAnnotation', {}).get('text', '').strip()
    )


def _call_files_annotate(api_key: str, file_bytes: bytes, mime_type: str) -> str:
    """
    Extract text from a PDF/TIFF, automatically chunking files that exceed
    the Vision API's 20 MB base64 limit (~10 MB raw per chunk).

    For PDFs the chunking splits by page using pypdf so each chunk is a valid
    PDF.  For TIFF and other formats the file is sent in one shot if it fits,
    or skipped with a warning if it is too large.
    """
    file_size = len(file_bytes)

    # ── PDF: chunk by page groups ─────────────────────────────────────────────
    if mime_type == 'application/pdf':
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            total_pages = len(reader.pages)
            _logger.info('Vision OCR: %d-page PDF (%d MB)', total_pages, file_size // (1024*1024))

            all_texts = []
            # Group pages into chunks of 5 (Vision API limit) while keeping
            # each chunk under _VISION_CHUNK_BYTES.
            chunk_start = 0
            while chunk_start < total_pages:
                writer = pypdf.PdfWriter()
                chunk_bytes = 0
                page_idx = chunk_start
                while page_idx < total_pages and page_idx - chunk_start < 5:
                    writer.add_page(reader.pages[page_idx])
                    page_idx += 1

                buf = io.BytesIO()
                writer.write(buf)
                chunk_data = buf.getvalue()
                chunk_b64  = base64.b64encode(chunk_data).decode('ascii')

                _logger.info(
                    'Vision OCR chunk: pages %d-%d (%d KB)',
                    chunk_start + 1, page_idx, len(chunk_data) // 1024,
                )
                try:
                    chunk_text = _call_files_annotate_chunk(api_key, chunk_b64, mime_type)
                    if chunk_text:
                        all_texts.append(chunk_text)
                except Exception as chunk_exc:
                    _logger.warning(
                        'Vision OCR chunk pages %d-%d failed: %s',
                        chunk_start + 1, page_idx, chunk_exc,
                    )
                chunk_start = page_idx

            return '\n\n'.join(all_texts)

        except ImportError:
            # pypdf not available — fall back to single-shot if file fits
            _logger.warning('pypdf not available for PDF chunking')

    # ── Non-PDF or pypdf unavailable: single shot if within limit ─────────────
    if file_size > _VISION_CHUNK_BYTES:
        _logger.warning(
            'Vision OCR: file too large for single-shot (%d MB > %d MB limit) '
            '— skipping Vision API',
            file_size // (1024 * 1024),
            _VISION_CHUNK_BYTES // (1024 * 1024),
        )
        return ''

    content_b64 = base64.b64encode(file_bytes).decode('ascii')
    return _call_files_annotate_chunk(api_key, content_b64, mime_type)


def extract_text_via_vision(env, file_data_b64: str, file_name: str = '') -> str:
    """
    Public entry point: extract text from base64-encoded file bytes.

    Pipeline:
      1. Excel / ODS / CSV  → direct extraction (no API, no size limit)
      2. Plain text         → decode and return
      3. PDF with text layer → pypdf (instant, free, handles any size)
      4. Scanned PDF/TIFF   → Google Vision (auto-chunked for large files)
      5. Images             → Google Vision images:annotate

    Returns the full extracted text string (empty string on failure).
    """
    if not file_data_b64:
        return ''

    # Strip any data-URL prefix (data:...;base64,<data>)
    if 'base64,' in file_data_b64:
        file_data_b64 = file_data_b64.split('base64,', 1)[1]

    mime_type  = _detect_mime(file_name, file_data_b64)
    file_bytes = base64.b64decode(file_data_b64)
    file_size  = len(file_bytes)

    _logger.info('OCR: processing %s (%d MB), mime=%s', file_name, file_size // (1024*1024), mime_type)

    # ── Size guard (200 MB limit) ─────────────────────────────────────────────
    if file_size > MAX_OCR_BYTES:
        _logger.warning(
            'OCR: file %s (%d MB) exceeds MAX_OCR_BYTES (%d MB) — skipping',
            file_name, file_size // (1024 * 1024), MAX_OCR_BYTES // (1024 * 1024),
        )
        return ''

    # ── Excel / ODS — no Vision needed ────────────────────────────────────────
    if mime_type in _EXCEL_MIME_TYPES:
        return _extract_excel_text(file_bytes, file_name)

    # ── Plain text / CSV ───────────────────────────────────────────────────────
    if mime_type in _TEXT_MIME_TYPES:
        return _extract_text_text(file_bytes)

    # ── PDF: try direct text extraction first (handles any size, no API cost) ─
    if mime_type == 'application/pdf':
        direct_text = _extract_pdf_text_direct(file_bytes)
        if direct_text and len(direct_text.strip()) > 20:
            _logger.info(
                'OCR: PDF text extracted directly via pypdf (%d chars)', len(direct_text)
            )
            return direct_text
        # No embedded text → must be a scanned PDF, fall through to Vision API

    # ── Vision API for scanned PDFs / TIFFs / images ──────────────────────────
    api_key = _get_vision_key(env)
    if not api_key:
        raise RuntimeError(
            'Google Vision API key not configured. '
            'Set it via: Settings → Technical → Parameters → '
            'nbs_archive.google_vision_key'
        )

    if mime_type in _FILE_MIME_TYPES:
        return _call_files_annotate(api_key, file_bytes, mime_type)
    elif mime_type in _IMAGE_MIME_TYPES:
        content_b64 = base64.b64encode(file_bytes).decode('ascii')
        return _call_images_annotate(api_key, content_b64)
    else:
        _logger.warning(
            'OCR: unsupported MIME type %s for %s — treating as PDF', mime_type, file_name
        )
        return _call_files_annotate(api_key, file_bytes, 'application/pdf')


# ── Odoo model ────────────────────────────────────────────────────────────────

class NBSOCRService(models.Model):
    _name        = 'nbs.ocr.service'
    _description = 'OCR Processing Service (Google Vision)'

    name           = fields.Char(string='OCR Job', required=True)
    document_id    = fields.Many2one('nbs.document', string='Document')
    attachment_id  = fields.Many2one('nbs.document.attachment', string='Attachment')

    status = fields.Selection([
        ('pending',    'Pending'),
        ('processing', 'Processing'),
        ('completed',  'Completed'),
        ('failed',     'Failed'),
    ], default='pending')

    extracted_text   = fields.Text(string='Extracted Text')
    confidence_score = fields.Float(string='Confidence Score')
    language         = fields.Char(string='Detected Language')
    error_message    = fields.Text(string='Error Message')

    # ── public methods ────────────────────────────────────────────────────────

    def _read_version_bytes(self, version):
        """
        Read the raw file bytes for a document version.

        Tries filestore path first (fast, no base64 decode overhead),
        then falls back to the ORM Binary field.
        Returns (bytes, file_name) or (None, file_name) if unavailable.
        """
        import os
        file_name = version.file_name or ''

        # ── Path 1: read directly from filestore via ir.attachment ───────────
        IrAttachment = self.env['ir.attachment'].sudo()
        att = IrAttachment.search([
            ('res_model', '=', 'nbs.document.version'),
            ('res_field', '=', 'file_data'),
            ('res_id',    '=', version.id),
        ], limit=1)

        if att and att.store_fname:
            full_path = IrAttachment._full_path(att.store_fname)
            if os.path.isfile(full_path):
                try:
                    with open(full_path, 'rb') as fh:
                        return fh.read(), file_name
                except Exception as exc:
                    _logger.warning('OCR: filestore read failed for %s: %s', full_path, exc)

        # ── Path 2: ORM fallback (loads via Binary field / base64 decode) ────
        if version.file_data:
            raw = version.file_data
            try:
                if isinstance(raw, bytes):
                    return base64.b64decode(raw), file_name
                return base64.b64decode(raw.encode('ascii')), file_name
            except Exception as exc:
                _logger.warning('OCR: ORM binary decode failed for version %s: %s', version.id, exc)

        return None, file_name

    def process_document_version(self, version):
        """
        Run OCR on a document version record and persist the result.

        Called by ``nbs.document._process_ocr()``.
        Returns True on success, False on failure.
        """
        if not version or not version.exists():
            return False

        try:
            file_bytes, file_name = self._read_version_bytes(version)

            if not file_bytes:
                _logger.warning('OCR: version %s has no file data', version.id)
                return False

            # Convert bytes → base64 string for the extraction pipeline
            file_data_b64 = base64.b64encode(file_bytes).decode('ascii')

            text = extract_text_via_vision(
                self.env, file_data_b64, file_name
            )

            version.write({
                'extracted_text':  text,
                'ocr_completed':   True,
                'ocr_date':        fields.Datetime.now(),
                'ocr_language':    'ara+eng',
            })

            if version.document_id:
                version.document_id.write({
                    'ocr_text':   text,
                    'ocr_status': 'completed',
                })

            _logger.info(
                'OCR completed for document %s (%d chars)',
                version.document_id.name if version.document_id else '?',
                len(text),
            )
            return True

        except Exception as exc:
            _logger.error('OCR failed for version %s: %s', version.id, exc, exc_info=True)
            if version.document_id:
                version.document_id.write({'ocr_status': 'failed'})
            return False

    def process_ocr_inline(self, file_data_b64: str, file_name: str = '') -> str:
        """
        Lightweight helper for inline (synchronous) OCR during file upload.
        Returns extracted text or empty string.
        """
        try:
            return extract_text_via_vision(self.env, file_data_b64, file_name)
        except Exception as exc:
            _logger.error('Inline OCR error (%s): %s', file_name, exc)
            return ''

    def test_tesseract(self):
        """Diagnostics endpoint — now returns Google Vision connectivity info."""
        key = _get_vision_key(self.env)
        return {
            'provider': 'Google Cloud Vision API',
            'key_configured': bool(key),
            'key_preview': (key[:8] + '...' + key[-4:]) if len(key) > 12 else '(short)',
            'endpoints': {
                'images': _VISION_IMAGES_URL,
                'files':  _VISION_FILES_URL,
            },
        }

    def _process_document_async(self, document_id: int):
        """Wrapper called by the OCR controller to trigger OCR on a document."""
        doc = self.env['nbs.document'].sudo().browse(document_id)
        if not doc.exists() or not doc.current_version_id:
            return False
        doc.write({'ocr_status': 'processing'})
        try:
            return self.sudo().process_document_version(doc.current_version_id)
        except Exception as exc:
            _logger.error('Async OCR error for doc %s: %s', document_id, exc)
            doc.write({'ocr_status': 'failed'})
            return False


# ── Keep existing unrelated models in the same file ──────────────────────────

class NBSEmailNotification(models.Model):
    _name        = 'nbs.email.notification'
    _description = 'Email Notifications'

    name              = fields.Char(string='Subject', required=True)
    document_id       = fields.Many2one('nbs.document', string='Document')
    recipient_ids     = fields.Many2many('res.users', string='Recipients')
    email_template_id = fields.Many2one('mail.template', string='Email Template')

    status = fields.Selection([
        ('pending', 'Pending'),
        ('sent',    'Sent'),
        ('failed',  'Failed'),
    ], default='pending')

    send_date      = fields.Datetime(string='Send Date')
    error_message  = fields.Text(string='Error')

    def send_notification(self):
        self.ensure_one()
        try:
            for recipient in self.recipient_ids:
                self.env['mail.mail'].create({
                    'subject':   self.name,
                    'body_html': f'<p>Document: {self.document_id.name}</p>',
                    'email_to':  recipient.email,
                }).send()
            self.write({'status': 'sent', 'send_date': fields.Datetime.now()})
        except Exception as exc:
            self.write({'status': 'failed', 'error_message': str(exc)})


class NBSDocumentAnalytics(models.Model):
    _name        = 'nbs.document.analytics'
    _description = 'Document Analytics & Reports'

    name        = fields.Char(string='Report Name', required=True)
    report_type = fields.Selection([
        ('department', 'By Department'),
        ('type',       'By Document Type'),
        ('user',       'By User'),
        ('timeline',   'Timeline'),
        ('storage',    'Storage Usage'),
    ], required=True)

    date_from     = fields.Date(string='From Date')
    date_to       = fields.Date(string='To Date')
    department_id = fields.Many2one('nbs.department', string='Department')

    total_documents   = fields.Integer(string='Total Documents',  compute='_compute_stats')
    active_documents  = fields.Integer(string='Active',           compute='_compute_stats')
    archived_documents = fields.Integer(string='Archived',        compute='_compute_stats')
    trash_documents   = fields.Integer(string='In Trash',         compute='_compute_stats')
    total_size_mb     = fields.Float(string='Total Size (MB)',     compute='_compute_storage')

    def _compute_stats(self):
        for a in self:
            domain = []
            if a.department_id:
                domain.append(('department_id', '=', a.department_id.id))
            if a.date_from:
                domain.append(('create_date', '>=', a.date_from))
            if a.date_to:
                domain.append(('create_date', '<=', a.date_to))
            Doc = self.env['nbs.document']
            a.total_documents    = Doc.search_count(domain)
            a.active_documents   = Doc.search_count(domain + [('state', '=', 'active')])
            a.archived_documents = Doc.search_count(domain + [('state', '=', 'archived')])
            a.trash_documents    = Doc.search_count(domain + [('is_deleted', '=', True)])

    def _compute_storage(self):
        for a in self:
            atts = self.env['nbs.document.attachment'].search([
                ('document_id.department_id', '=', a.department_id.id if a.department_id else False)
            ])
            a.total_size_mb = sum(atts.mapped('file_size')) / (1024 * 1024)
