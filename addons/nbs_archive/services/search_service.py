# -*- coding: utf-8 -*-

import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class NBSSearchService(models.AbstractModel):
    _name = 'nbs.search.service'
    _description = 'Search Service Wrapper'
    
    @api.model
    def search_documents(self, query, user_id=None, filters=None, fuzzy=True, page=1, per_page=20):
        """
        Search documents with user access control
        
        Args:
            query: Search query
            user_id: User ID (default: current user)
            filters: Additional filters
            fuzzy: Enable fuzzy search
            page: Page number
            per_page: Results per page
        
        Returns:
            Dict with results and pagination
        """
        if not user_id:
            user_id = self.env.user.id
        
        user = self.env['res.users'].browse(user_id)
        filters = filters or {}
        
        # Add department filter based on user access
        if not filters.get('department_ids'):
            filters['department_ids'] = user.nbs_department_ids.ids
        
        # Search in OpenSearch
        opensearch = self.env['nbs.opensearch.service']
        search_results = opensearch.search_documents(
            query=query,
            filters=filters,
            fuzzy=fuzzy,
            page=page,
            per_page=per_page
        )
        
        # Filter results by user access (confidentiality level)
        accessible_results = []
        
        for result in search_results.get('results', []):
            document = self.env['nbs.document'].browse(result['document_id'])
            
            if document.exists() and self._can_user_access(user, document):
                accessible_results.append(result)
        
        search_results['results'] = accessible_results
        search_results['total'] = len(accessible_results)
        
        return search_results
    
    @api.model
    def search_by_barcode(self, barcode, user_id=None):
        """
        Search document by barcode
        
        Args:
            barcode: Barcode value
            user_id: User ID
        
        Returns:
            Document info if found and accessible
        """
        if not user_id:
            user_id = self.env.user.id
        
        user = self.env['res.users'].browse(user_id)
        
        # Search in OpenSearch first (faster)
        opensearch = self.env['nbs.opensearch.service']
        result = opensearch.search_by_barcode(barcode)
        
        if result.get('found'):
            document = self.env['nbs.document'].browse(result['document_id'])
            
            if document.exists() and self._can_user_access(user, document):
                return {
                    'found': True,
                    'document': {
                        'id': document.id,
                        'name': document.name,
                        'barcode': document.barcode,
                        'department': document.department_id.name,
                        'document_type': document.document_type_id.name,
                        'upload_date': document.upload_date.isoformat() if document.upload_date else None
                    }
                }
        
        return {'found': False}
    
    def _can_user_access(self, user, document):
        """Check if user can access document"""
        is_admin = user.has_group('nbs_archive.group_nbs_admin')
        is_manager = user in document.department_id.manager_ids
        in_department = user in document.department_id.user_ids
        
        if is_admin:
            return True
        
        level = document.confidentiality_level
        
        if level == 'strict':
            return is_admin
        elif level == 'confidential':
            return is_manager or is_admin
        elif level in ['public', 'internal']:
            return in_department
        
        return False
    
    @api.model
    def get_search_suggestions(self, query, user_id=None, limit=5):
        """
        Get search suggestions based on partial query
        
        Args:
            query: Partial search query
            user_id: User ID
            limit: Max suggestions
        
        Returns:
            List of suggestions
        """
        if not user_id:
            user_id = self.env.user.id
        
        user = self.env['res.users'].browse(user_id)
        
        # Search document titles
        documents = self.env['nbs.document'].search([
            ('name', 'ilike', query),
            ('department_id', 'in', user.nbs_department_ids.ids),
            ('state', '=', 'active')
        ], limit=limit)
        
        suggestions = []
        for doc in documents:
            if self._can_user_access(user, doc):
                suggestions.append({
                    'id': doc.id,
                    'name': doc.name,
                    'barcode': doc.barcode,
                    'type': 'document'
                })
        
        return suggestions


