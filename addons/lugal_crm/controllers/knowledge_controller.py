# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._audit import crm_audit

_logger = logging.getLogger(__name__)


def _article_to_dict(article):
    return {
        'id': article.id,
        'title': article.title,
        'title_ar': article.title_ar or '',
        'category': article.category or '',
        'content': article.content or '',
        'content_ar': article.content_ar or '',
        'author_id': article.author_id.id if article.author_id else None,
        'author_name': article.author_id.name if article.author_id else '',
        'branch_id': article.branch_id.id if article.branch_id else None,
        'is_published': article.is_published,
        'published_at': article.published_at.isoformat() if article.published_at else None,
        'updated_at': article.write_date.isoformat() if article.write_date else None,
    }


def _notification_to_dict(n):
    return {
        'id': n.id,
        'title': n.title or '',
        'body': n.body or '',
        'notification_type': n.notification_type or '',
        'branch_ids': n.branch_ids.ids if n.branch_ids else [],
        'sent_at': n.sent_at.isoformat() if n.sent_at else None,
        'created_at': n.create_date.isoformat() if n.create_date else None,
    }


class KnowledgeController(http.Controller):

    # ─── Articles ─────────────────────────────────────────────────────────

    @http.route('/api/crm/kb/articles/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def article_list(self, page=1, per_page=50, category=None, branch_id=None, published_only=True, **kwargs):
        """List KB articles with optional category and branch filters."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False), ('active', '=', True)]
            if published_only:
                domain.append(('is_published', '=', True))
            if category:
                domain.append(('category', '=', category))
            if branch_id:
                domain += ['|', ('branch_id', '=', branch_id), ('branch_id', '=', False)]
            Article = request.env['lugal.crm.kb.article']
            total = Article.search_count(domain)
            offset = (page - 1) * per_page
            articles = Article.search(domain, limit=per_page, offset=offset, order='write_date desc')
            return {
                'success': True,
                'data': {
                    'items': [_article_to_dict(a) for a in articles],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            _logger.exception('article_list error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/kb/articles/search', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def article_search(self, query, branch_id=None, limit=30, **kwargs):
        """Full-text search articles by title or content."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not query or len(query.strip()) < 2:
                return {'success': True, 'data': {'items': [], 'total': 0}}
            domain = [
                ('is_deleted', '=', False),
                ('active', '=', True),
                '|', '|',
                ('title', 'ilike', query.strip()),
                ('title_ar', 'ilike', query.strip()),
                ('content', 'ilike', query.strip()),
            ]
            if branch_id:
                domain += ['|', ('branch_id', '=', branch_id), ('branch_id', '=', False)]
            articles = request.env['lugal.crm.kb.article'].search(domain, limit=limit, order='write_date desc')
            return {'success': True, 'data': {'items': [_article_to_dict(a) for a in articles], 'total': len(articles)}}
        except Exception as e:
            _logger.exception('article_search error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/kb/articles/<int:article_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def article_get(self, article_id, **kwargs):
        """Get single KB article."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            article = request.env['lugal.crm.kb.article'].browse(article_id)
            if not article.exists() or article.is_deleted:
                return {'success': False, 'error': 'Article not found'}
            return {'success': True, 'data': _article_to_dict(article)}
        except Exception as e:
            _logger.exception('article_get error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/kb/articles/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def article_create(self, title, category='document', content=None, title_ar=None,
                       content_ar=None, branch_id=None, is_published=False, **kwargs):
        """Create KB article."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            vals = {
                'title': title,
                'title_ar': title_ar or '',
                'category': category,
                'content': content or '',
                'content_ar': content_ar or '',
                'branch_id': branch_id,
                'is_published': is_published,
            }
            article = request.env['lugal.crm.kb.article'].create(vals)
            crm_audit('article_created', record_model='lugal.crm.kb.article', record_id=article.id,
                      details={'title': title, 'category': category})
            return {'success': True, 'data': _article_to_dict(article)}
        except Exception as e:
            _logger.exception('article_create error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/kb/articles/<int:article_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def article_update(self, article_id, **kwargs):
        """Update KB article."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            article = request.env['lugal.crm.kb.article'].browse(article_id)
            if not article.exists() or article.is_deleted:
                return {'success': False, 'error': 'Article not found'}
            from odoo.fields import Datetime
            allowed = {'title', 'title_ar', 'category', 'content', 'content_ar', 'branch_id', 'is_published'}
            vals = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
            if vals.get('is_published') and not article.published_at:
                vals['published_at'] = Datetime.now()
            if vals:
                article.write(vals)
            return {'success': True, 'data': _article_to_dict(article)}
        except Exception as e:
            _logger.exception('article_update error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/kb/articles/<int:article_id>/delete', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def article_delete(self, article_id, **kwargs):
        """Soft-delete a KB article."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            article = request.env['lugal.crm.kb.article'].browse(article_id)
            if not article.exists():
                return {'success': False, 'error': 'Article not found'}
            article.write({'is_deleted': True, 'active': False})
            crm_audit('article_deleted', record_model='lugal.crm.kb.article', record_id=article_id,
                      details={'title': article.title})
            return {'success': True}
        except Exception as e:
            _logger.exception('article_delete error')
            return {'success': False, 'error': str(e)}

    # ─── Notifications ────────────────────────────────────────────────────

    @http.route('/api/crm/kb/notifications/list', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def notification_list(self, page=1, per_page=30, branch_id=None, **kwargs):
        """List sent notifications, optionally filtered by branch."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            domain = [('is_deleted', '=', False)]
            if branch_id:
                domain.append(('branch_ids', 'in', [branch_id]))
            Notif = request.env['lugal.crm.kb.notification']
            total = Notif.search_count(domain)
            notifs = Notif.search(domain, limit=per_page, offset=(page - 1) * per_page, order='sent_at desc')
            return {
                'success': True,
                'data': {
                    'items': [_notification_to_dict(n) for n in notifs],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                },
            }
        except Exception as e:
            _logger.exception('notification_list error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/kb/notifications/push', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def notification_push(self, title, body=None, branch_ids=None, notification_type='announcement', **kwargs):
        """Create and push a KB notification to branches."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            vals = {'title': title, 'body': body or '', 'notification_type': notification_type}
            if branch_ids:
                vals['branch_ids'] = [(6, 0, branch_ids)]
            notif = request.env['lugal.crm.kb.notification'].create(vals)
            crm_audit('notification_pushed', record_model='lugal.crm.kb.notification', record_id=notif.id,
                      details={'title': title, 'branch_ids': branch_ids})
            return {'success': True, 'data': _notification_to_dict(notif)}
        except Exception as e:
            _logger.exception('notification_push error')
            return {'success': False, 'error': str(e)}
