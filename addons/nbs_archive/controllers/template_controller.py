# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class TemplateController(http.Controller):
    
    @http.route('/api/templates', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def list_templates(self, department_id=None, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            
            domain = [('active', '=', True)]
            if department_id:
                domain.append(('department_id', '=', department_id))
            
            try:
                templates = request.env['nbs.document.template'].sudo().search(domain)
                data = [{
                    'id': t.id,
                    'name': t.name,
                    'department': t.department_id.name,
                    'document_type': t.document_type_id.name
                } for t in templates]
            except Exception:
                data = []
            return {'success': True, 'data': data}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/templates/<int:template_id>/create-document', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def create_from_template(self, template_id, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            
            template = request.env['nbs.document.template'].browse(template_id)
            if not template.exists():
                return {'success': False, 'error': 'Template not found'}
            
            document = template.create_document_from_template()
            
            return {
                'success': True,
                'message': 'Document created from template',
                'data': {'id': document.id, 'name': document.name}
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
