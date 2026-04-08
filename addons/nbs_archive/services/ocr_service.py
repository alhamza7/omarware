# -*- coding: utf-8 -*-

import os
import logging
import subprocess
import tempfile
import json
from odoo import models, api
from PIL import Image

_logger = logging.getLogger(__name__)

try:
    import pytesseract
    from pdf2image import convert_from_path
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    _logger.warning('pytesseract or pdf2image not installed. OCR will not work.')


class NBSOCRService(models.AbstractModel):
    _name = 'nbs.ocr.service'
    _description = 'OCR Processing Service'
    
    def _get_tesseract_languages(self):
        """Get configured Tesseract languages"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'nbs_archive.tesseract_languages',
            'ara+eng'
        )
    
    def _get_tesseract_dpi(self):
        """Get DPI for PDF to image conversion"""
        return int(self.env['ir.config_parameter'].sudo().get_param(
            'nbs_archive.tesseract_dpi',
            '300'
        ))
    
    def _process_document_async(self, document_id):
        """
        Queue document for OCR processing (async)
        For now, process immediately - will use Celery/RQ later
        """
        try:
            document = self.env['nbs.document'].sudo().browse(document_id)
            if document.exists():
                _logger.info(f'Document {document_id} queued for OCR processing')

                # Mark as processing
                try:
                    document.sudo().write({'ocr_status': 'processing'})
                except Exception:
                    pass

                if not document.current_version_id:
                    _logger.warning(f'Document {document_id} has no current version for OCR')
                    document.sudo().write({'ocr_status': 'failed'})
                    return False

                ok = self.process_document_version(document.current_version_id)
                document.sudo().write({'ocr_status': 'completed' if ok else 'failed'})
                return ok
        except Exception as e:
            _logger.error(f'Failed to queue OCR: {str(e)}')
            try:
                self.env['nbs.document'].sudo().browse(document_id).write({'ocr_status': 'failed'})
            except Exception:
                pass
            return False
    
    @api.model
    def process_document_version(self, version):
        """
        Process OCR for a document version
        
        Args:
            version: nbs.document.version record
        
        Returns:
            Boolean: True if successful, False otherwise
        """
        if not TESSERACT_AVAILABLE:
            _logger.error('Tesseract not available')
            return False
        
        if not version or not version.file_path:
            _logger.error('Version or file path not found')
            return False
        
        file_path = version.file_path
        file_type = version.file_type or ''
        
        try:
            # Determine file type and process accordingly
            if 'pdf' in file_type.lower():
                return self._process_pdf(version, file_path)
            elif any(img in file_type.lower() for img in ['image', 'jpeg', 'jpg', 'png', 'tiff']):
                return self._process_image(version, file_path)
            else:
                _logger.warning(f'Unsupported file type for OCR: {file_type}')
                return False
        
        except Exception as e:
            _logger.error(f'OCR processing failed: {e}', exc_info=True)
            return False
    
    def _process_pdf(self, version, file_path):
        """Process PDF file"""
        _logger.info(f'Processing PDF: {file_path}')
        
        try:
            # Convert PDF to images
            dpi = self._get_tesseract_dpi()
            images = convert_from_path(file_path, dpi=dpi)
            
            if not images:
                _logger.warning('No images extracted from PDF')
                return False
            
            # Process each page
            all_text = []
            per_page_text = []
            languages = self._get_tesseract_languages()
            
            for page_num, image in enumerate(images, start=1):
                _logger.info(f'Processing page {page_num}/{len(images)}')
                
                # Run OCR on page
                text = pytesseract.image_to_string(
                    image,
                    lang=languages,
                    config='--oem 3 --psm 6'  # LSTM OCR Engine, Assume uniform text block
                )
                
                all_text.append(text)
                per_page_text.append({
                    'page': page_num,
                    'text': text.strip()
                })
            
            # Save results
            version.sudo().write({
                'extracted_text': '\n\n'.join(all_text),
                'extracted_text_per_page': json.dumps(per_page_text, ensure_ascii=False),
                'ocr_completed': True,
                'ocr_date': self.env.cr.now()
            })
            
            _logger.info(f'OCR completed for {len(images)} pages')
            return True
        
        except Exception as e:
            _logger.error(f'PDF processing failed: {e}', exc_info=True)
            return False
    
    def _process_image(self, version, file_path):
        """Process image file"""
        _logger.info(f'Processing image: {file_path}')
        
        try:
            # Open image
            image = Image.open(file_path)
            
            # Run OCR
            languages = self._get_tesseract_languages()
            text = pytesseract.image_to_string(
                image,
                lang=languages,
                config='--oem 3 --psm 6'
            )
            
            # Save results
            per_page_text = [{
                'page': 1,
                'text': text.strip()
            }]
            
            version.sudo().write({
                'extracted_text': text,
                'extracted_text_per_page': json.dumps(per_page_text, ensure_ascii=False),
                'ocr_completed': True,
                'ocr_date': self.env.cr.now()
            })
            
            _logger.info('OCR completed for image')
            return True
        
        except Exception as e:
            _logger.error(f'Image processing failed: {e}', exc_info=True)
            return False
    
    @api.model
    def test_tesseract(self):
        """
        Test Tesseract installation
        
        Returns:
            Dict with status and available languages
        """
        if not TESSERACT_AVAILABLE:
            return {
                'available': False,
                'error': 'pytesseract or pdf2image not installed'
            }
        
        try:
            # Check Tesseract version
            version = pytesseract.get_tesseract_version()
            
            # Get available languages
            langs = pytesseract.get_languages(config='')
            
            return {
                'available': True,
                'version': str(version),
                'languages': langs,
                'configured_languages': self._get_tesseract_languages()
            }
        
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }

