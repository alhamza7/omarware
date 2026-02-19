# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class CompaniesController(http.Controller):
    """Companies/Brands management controller"""
    
    @http.route('/api/companies', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def list_companies(self, search=None, limit=100, **kwargs):
        """
        Get list of companies/brands
        
        Args:
            search: Optional search term for company name
            limit: Maximum number of results (default: 100)
        
        Returns:
            List of companies with id and name
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            
            domain = [
                ('is_company', '=', True),
                ('active', '=', True)
            ]
            
            if search:
                domain.append(('name', 'ilike', search))
            
            companies = request.env['res.partner'].search(
                domain,
                limit=limit,
                order='name'
            )
            
            return {
                'success': True,
                'data': [{
                    'id': company.id,
                    'name': company.name,
                    'phone': company.phone,
                    'email': company.email,
                    'vat': company.vat,  # Tax ID / رقم ضريبي
                    'street': company.street,
                    'city': company.city,
                    'country_id': company.country_id.id if company.country_id else None,
                    'country_name': company.country_id.name if company.country_id else None,
                } for company in companies],
                'count': len(companies)
            }
        except Exception as e:
            _logger.error(f'List companies error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/companies/<int:company_id>', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_company(self, company_id, **kwargs):
        """Get single company details with statistics"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            
            company = request.env['res.partner'].browse(company_id)
            
            if not company.exists() or not company.is_company:
                return {'success': False, 'error': 'Company not found'}
            
            # Get statistics
            folder_count = request.env['nbs.document.folder'].search_count([
                ('company_id', '=', company_id),
                ('active', '=', True)
            ])
            
            document_count = request.env['nbs.document'].search_count([
                ('company_id', '=', company_id),
                ('is_deleted', '=', False)
            ])
            
            return {
                'success': True,
                'data': {
                    'id': company.id,
                    'name': company.name,
                    'phone': company.phone,
                    'email': company.email,
                    'vat': company.vat,
                    'street': company.street,
                    'city': company.city,
                    'country_id': company.country_id.id if company.country_id else None,
                    'country_name': company.country_id.name if company.country_id else None,
                    'website': company.website,
                    # Statistics
                    'folder_count': folder_count,
                    'document_count': document_count,
                }
            }
        except Exception as e:
            _logger.error(f'Get company error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/companies/create', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def create_company(self, **kwargs):
        """
        Create new company/brand
        
        Request body (JSON):
        {
          "name": "Company Name",  // Required
          "phone": "optional",
          "email": "optional",
          "vat": "optional",
          "street": "optional",
          "city": "optional",
          "country_id": 1,  // Optional: country ID
          "country_name": "United States",  // Optional: country name (alternative to country_id)
          "website": "optional"
        }
        
        Note: Use either country_id OR country_name. If country_name is provided and country 
        doesn't exist, it will be created automatically.
        """
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response({'success': False, 'error': 'Unauthorized'}, status=401)
            
            # Check permission (only managers can create companies)
            if not request.env.user.has_group('nbs_archive.group_nbs_manager'):
                return request.make_json_response({
                    'success': False,
                    'error': 'Only managers can create companies'
                }, status=403)
            
            # Parse JSON body
            try:
                import json
                data = json.loads(request.httprequest.data.decode('utf-8'))
                
                # Handle JSON-RPC format
                if isinstance(data, dict) and 'params' in data:
                    data = data['params']
                    
            except Exception as e:
                return request.make_json_response({
                    'success': False,
                    'error': 'Invalid JSON in request body'
                }, status=400)
            
            if not data.get('name'):
                return request.make_json_response({
                    'success': False,
                    'error': 'Company name is required'
                }, status=400)
            
            # Create company
            vals = {
                'name': data['name'],
                'is_company': True,
                'active': True,
            }
            
            # Optional fields
            if data.get('phone'):
                vals['phone'] = data['phone']
            if data.get('email'):
                vals['email'] = data['email']
            if data.get('vat'):
                vals['vat'] = data['vat']
            if data.get('street'):
                vals['street'] = data['street']
            if data.get('city'):
                vals['city'] = data['city']
            if data.get('website'):
                vals['website'] = data['website']
            
            # Handle country - accept either country_id or country_name
            if data.get('country_id'):
                vals['country_id'] = data['country_id']
            elif data.get('country_name'):
                # Search for country by name
                country = request.env['res.country'].search([
                    ('name', 'ilike', data['country_name'])
                ], limit=1)
                if country:
                    vals['country_id'] = country.id
                else:
                    # Create new country if not found
                    new_country = request.env['res.country'].create({
                        'name': data['country_name'],
                        'code': data['country_name'][:2].upper()  # Default 2-letter code
                    })
                    vals['country_id'] = new_country.id
            
            company = request.env['res.partner'].create(vals)
            
            # Log creation
            request.env['nbs.audit.log'].sudo().create({
                'user_id': request.env.user.id,
                'action': 'company_created',
                'metadata': f'Created company: {company.name} (ID: {company.id})'
            })
            
            return request.make_json_response({
                'success': True,
                'message': 'Company created successfully',
                'data': {
                    'id': company.id,
                    'name': company.name
                }
            })
            
        except Exception as e:
            _logger.error(f'Create company error: {str(e)}', exc_info=True)
            return request.make_json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    @http.route('/api/companies/<int:company_id>/update', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def update_company(self, company_id, **kwargs):
        """
        Update company/brand. Only managers.
        Body (JSON): name, phone, email, vat, street, city, country_id, country_name, website
        
        Note: Use either country_id OR country_name. If country_name is provided and country
        doesn't exist, it will be created automatically.
        """
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response({'success': False, 'error': 'Unauthorized'}, status=401)
            if not request.env.user.has_group('nbs_archive.group_nbs_manager'):
                return request.make_json_response({
                    'success': False,
                    'error': 'Only managers can update companies'
                }, status=403)
            company = request.env['res.partner'].browse(company_id)
            if not company.exists() or not company.is_company:
                return request.make_json_response({'success': False, 'error': 'Company not found'}, status=404)
            try:
                import json
                raw = request.httprequest.get_data(as_text=True)
                data = json.loads(raw) if raw else {}
                if isinstance(data, dict) and 'params' in data:
                    data = data['params']
            except Exception:
                return request.make_json_response({'success': False, 'error': 'Invalid JSON'}, status=400)
            
            allowed = {'name', 'phone', 'email', 'vat', 'street', 'city', 'country_id', 'website'}
            vals = {k: v for k, v in data.items() if k in allowed and v is not None}
            
            # Handle country_name if provided (instead of country_id)
            if data.get('country_name') and not data.get('country_id'):
                country = request.env['res.country'].search([
                    ('name', 'ilike', data['country_name'])
                ], limit=1)
                if country:
                    vals['country_id'] = country.id
                else:
                    # Create new country if not found
                    new_country = request.env['res.country'].create({
                        'name': data['country_name'],
                        'code': data['country_name'][:2].upper()
                    })
                    vals['country_id'] = new_country.id
            
            if not vals:
                return request.make_json_response({
                    'success': True,
                    'message': 'Nothing to update',
                    'data': {'id': company.id, 'name': company.name}
                })
            
            # Track old values for audit log
            old_name = company.name
            old_country = company.country_id.name if company.country_id else None
            
            company.write(vals)
            
            # Build change details for audit log
            changes = []
            if 'name' in vals and old_name != company.name:
                changes.append(f"Name: '{old_name}' → '{company.name}'")
            if 'country_id' in vals:
                new_country = company.country_id.name if company.country_id else 'None'
                if old_country != new_country:
                    changes.append(f"Country: '{old_country or 'None'}' → '{new_country}'")
            if 'phone' in vals:
                changes.append(f"Phone updated")
            if 'email' in vals:
                changes.append(f"Email updated")
            if 'vat' in vals:
                changes.append(f"VAT updated")
            
            # Create audit log
            metadata = f"Updated company: {company.name}"
            if changes:
                metadata += f" | Changes: {', '.join(changes)}"
            
            request.env['nbs.audit.log'].sudo().create({
                'user_id': request.env.user.id,
                'action': 'company_updated',
                'metadata': metadata
            })
            
            return request.make_json_response({
                'success': True,
                'message': 'Company updated successfully',
                'data': {'id': company.id, 'name': company.name}
            })
        except Exception as e:
            _logger.error(f'Update company error: {str(e)}', exc_info=True)
            return request.make_json_response({'success': False, 'error': str(e)}, status=500)
    
    @http.route('/api/companies/<int:company_id>', type='http', auth='none', methods=['DELETE'], csrf=False, cors='*')
    def delete_company(self, company_id, **kwargs):
        """
        Delete (archive) company. Fails if company has any folders.
        Cannot delete a company that has folders linked to it.
        """
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response({'success': False, 'error': 'Unauthorized'}, status=401)
            if not request.env.user.has_group('nbs_archive.group_nbs_manager'):
                return request.make_json_response({
                    'success': False,
                    'error': 'Only managers can delete companies'
                }, status=403)
            company = request.env['res.partner'].browse(company_id)
            if not company.exists() or not company.is_company:
                return request.make_json_response({'success': False, 'error': 'Company not found'}, status=404)
            folder_count = request.env['nbs.document.folder'].search_count([
                ('company_id', '=', company_id),
                ('active', '=', True)
            ])
            if folder_count > 0:
                return request.make_json_response({
                    'success': False,
                    'error': 'Cannot delete company that has folders',
                    'code': 'COMPANY_HAS_FOLDERS',
                    'folder_count': folder_count,
                    'message_ar': 'لا يمكن حذف الشركة لوجود فولدرات مرتبطة بها. قم بإزالة أو نقل الفولدرات أولاً.'
                }, status=400)
            
            # Store name before deletion for audit log
            company_name = company.name
            
            company.write({'active': False})
            
            # Create audit log
            request.env['nbs.audit.log'].sudo().create({
                'user_id': request.env.user.id,
                'action': 'company_deleted',
                'metadata': f'Deleted company: {company_name} (ID: {company_id})'
            })
            
            return request.make_json_response({
                'success': True,
                'message': 'Company deleted successfully',
                'data': {'id': company.id}
            })
        except Exception as e:
            _logger.error(f'Delete company error: {str(e)}', exc_info=True)
            return request.make_json_response({'success': False, 'error': str(e)}, status=500)
    
    @http.route('/api/companies/<int:company_id>/stats', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_company_stats(self, company_id, **kwargs):
        """Get detailed statistics for a company"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            
            # Get company
            company = request.env['res.partner'].browse(company_id)
            
            if not company.exists() or not company.is_company:
                return {'success': False, 'error': 'Company not found'}
            
            # Get folders
            folders = request.env['nbs.document.folder'].search([
                ('company_id', '=', company_id),
                ('active', '=', True)
            ])
            
            # Get documents
            documents = request.env['nbs.document'].search([
                ('company_id', '=', company_id),
                ('is_deleted', '=', False)
            ])
            
            # Count by department
            dept_stats = {}
            for doc in documents:
                dept_name = doc.department_id.name
                if dept_name not in dept_stats:
                    dept_stats[dept_name] = {'count': 0, 'main': 0, 'sub': 0}
                dept_stats[dept_name]['count'] += 1
                if doc.folder_role == 'main':
                    dept_stats[dept_name]['main'] += 1
                elif doc.folder_role == 'sub':
                    dept_stats[dept_name]['sub'] += 1
            
            # Count by document type
            type_stats = {}
            for doc in documents:
                type_name = doc.document_type_id.name
                type_stats[type_name] = type_stats.get(type_name, 0) + 1
            
            return {
                'success': True,
                'data': {
                    'company': {
                        'id': company.id,
                        'name': company.name
                    },
                    'totals': {
                        'folders': len(folders),
                        'documents': len(documents),
                        'main_documents': sum(1 for d in documents if d.folder_role == 'main'),
                        'sub_documents': sum(1 for d in documents if d.folder_role == 'sub'),
                    },
                    'by_department': dept_stats,
                    'by_type': type_stats
                }
            }
        except Exception as e:
            _logger.error(f'Get company stats error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/countries', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def list_countries(self, search=None, limit=100, **kwargs):
        """
        Get list of countries for dropdown/autocomplete
        
        Args:
            search: Optional search term for country name
            limit: Maximum number of results (default: 100)
        
        Returns:
            List of countries with id, name, and code
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            
            domain = []
            
            if search:
                domain.append(('name', 'ilike', search))
            
            countries = request.env['res.country'].search(
                domain,
                limit=limit,
                order='name'
            )
            
            return {
                'success': True,
                'data': [{
                    'id': country.id,
                    'name': country.name,
                    'code': country.code,  # ISO code like 'US', 'GB', 'SA', etc.
                    'phone_code': country.phone_code if country.phone_code else None,  # e.g. 964, 966, 1
                } for country in countries],
                'count': len(countries)
            }
        except Exception as e:
            _logger.error(f'List countries error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
