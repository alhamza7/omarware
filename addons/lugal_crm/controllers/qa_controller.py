# -*- coding: utf-8 -*-
"""
QA Review Controller — QA auditors score calls and messages.
Routes: /api/crm/qa/*
"""

import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id
from ._audit import crm_audit
from ._permissions import is_qa_auditor_or_above, is_qa_supervisor, is_supervisor_or_above, forbidden

_logger = logging.getLogger(__name__)


class QaController(http.Controller):

    @http.route('/api/crm/qa/reviews', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_reviews(self, page=1, limit=20, review_type=None, agent_id=None,
                     reviewer_id=None, status=None, branch_id=None, **kwargs):
        """List QA reviews. Requires QA Auditor role or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_qa_auditor_or_above():
                return forbidden('QA Auditor role required')
            domain = [('active', '=', True)]
            if review_type:
                domain.append(('review_type', '=', review_type))
            if agent_id:
                domain.append(('agent_id', '=', int(agent_id)))
            if reviewer_id:
                domain.append(('reviewer_id', '=', int(reviewer_id)))
            if status:
                domain.append(('status', '=', status))
            if branch_id:
                domain.append(('branch_id', '=', int(branch_id)))
            offset = (int(page) - 1) * int(limit)
            reviews = request.env['lugal.crm.qa.review'].sudo().search(
                domain, limit=int(limit), offset=offset, order='reviewed_at desc'
            )
            total = request.env['lugal.crm.qa.review'].sudo().search_count(domain)
            return {
                'success': True,
                'data': {
                    'total': total,
                    'page': int(page),
                    'limit': int(limit),
                    'items': [self._review_to_dict(r) for r in reviews],
                },
            }
        except Exception as e:
            _logger.exception('qa list_reviews error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/qa/reviews/<int:review_id>', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def get_review(self, review_id, **kwargs):
        """Get single QA review. Requires QA Auditor role or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_qa_auditor_or_above():
                return forbidden('QA Auditor role required')
            review = request.env['lugal.crm.qa.review'].sudo().browse(review_id)
            if not review.exists() or not review.active:
                return {'success': False, 'error': 'Review not found'}
            return {'success': True, 'data': self._review_to_dict(review)}
        except Exception as e:
            _logger.exception('qa get_review error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/qa/reviews/create', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def create_review(self, review_type, call_id=None, conversation_id=None,
                      customer_id=None, agent_id=None, branch_id=None,
                      score=0.0, greeting_score=0.0, product_knowledge_score=0.0,
                      problem_solving_score=0.0, professionalism_score=0.0,
                      compliance_score=0.0, issues_found=None, qa_notes=None,
                      feedback_to_agent=None, listen_duration_seconds=0, **kwargs):
        """Create a new QA review. Requires QA Auditor role or above."""
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            if not is_qa_auditor_or_above():
                return forbidden('QA Auditor role required')
            vals = {
                'review_type': review_type,
                'reviewer_id': uid,
                'score': float(score),
                'greeting_score': float(greeting_score),
                'product_knowledge_score': float(product_knowledge_score),
                'problem_solving_score': float(problem_solving_score),
                'professionalism_score': float(professionalism_score),
                'compliance_score': float(compliance_score),
                'listen_duration_seconds': int(listen_duration_seconds),
                'status': 'draft',
            }
            if call_id:
                vals['call_id'] = int(call_id)
            if conversation_id:
                vals['conversation_id'] = str(conversation_id)
            if customer_id:
                vals['customer_id'] = int(customer_id)
            if agent_id:
                vals['agent_id'] = int(agent_id)
            if branch_id:
                vals['branch_id'] = int(branch_id)
            if issues_found:
                vals['issues_found'] = issues_found
            if qa_notes:
                vals['qa_notes'] = qa_notes
            if feedback_to_agent:
                vals['feedback_to_agent'] = feedback_to_agent
            review = request.env['lugal.crm.qa.review'].sudo().create(vals)
            crm_audit('qa_review_created', customer_id=customer_id,
                      branch_id=branch_id, record_model='lugal.crm.qa.review',
                      record_id=review.id, details={'review_number': review.review_number, 'score': score})
            return {'success': True, 'data': self._review_to_dict(review)}
        except Exception as e:
            _logger.exception('qa create_review error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/qa/reviews/<int:review_id>/update', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def update_review(self, review_id, **kwargs):
        """Update an existing QA review (only if still in draft)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            review = request.env['lugal.crm.qa.review'].sudo().browse(review_id)
            if not review.exists():
                return {'success': False, 'error': 'Review not found'}
            if review.status == 'submitted':
                return {'success': False, 'error': 'Cannot update a submitted review'}
            allowed = [
                'score', 'greeting_score', 'product_knowledge_score', 'problem_solving_score',
                'professionalism_score', 'compliance_score', 'issues_found', 'qa_notes',
                'feedback_to_agent', 'listen_duration_seconds',
            ]
            vals = {k: kwargs[k] for k in allowed if k in kwargs}
            if vals:
                review.write(vals)
            return {'success': True, 'data': self._review_to_dict(review)}
        except Exception as e:
            _logger.exception('qa update_review error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/qa/reviews/<int:review_id>/submit', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def submit_review(self, review_id, **kwargs):
        """Submit a QA review (locks it). Requires QA Auditor role or above."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not is_qa_auditor_or_above():
                return forbidden('QA Auditor role required')
            review = request.env['lugal.crm.qa.review'].sudo().browse(review_id)
            if not review.exists():
                return {'success': False, 'error': 'Review not found'}
            review.write({'status': 'submitted'})
            crm_audit('qa_review_submitted', record_model='lugal.crm.qa.review',
                      record_id=review.id, details={'review_number': review.review_number})
            return {'success': True, 'data': self._review_to_dict(review)}
        except Exception as e:
            _logger.exception('qa submit_review error')
            return {'success': False, 'error': str(e)}

    @http.route('/api/crm/qa/stats', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def qa_stats(self, reviewer_id=None, agent_id=None, branch_id=None,
                 date_from=None, date_to=None, **kwargs):
        """QA stats. Requires QA Supervisor or Supervisor role."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            if not (is_qa_supervisor() or is_supervisor_or_above()):
                return forbidden('QA Supervisor or CRM Supervisor role required')
            domain = [('active', '=', True), ('status', '!=', 'draft')]
            if reviewer_id:
                domain.append(('reviewer_id', '=', int(reviewer_id)))
            if agent_id:
                domain.append(('agent_id', '=', int(agent_id)))
            if branch_id:
                domain.append(('branch_id', '=', int(branch_id)))
            if date_from:
                domain.append(('reviewed_at', '>=', date_from))
            if date_to:
                domain.append(('reviewed_at', '<=', date_to))
            reviews = request.env['lugal.crm.qa.review'].sudo().search(domain)
            total = len(reviews)
            avg_score = sum(reviews.mapped('score')) / total if total else 0
            total_listen_sec = sum(reviews.mapped('listen_duration_seconds'))
            call_reviews = reviews.filtered(lambda r: r.review_type == 'call')
            message_reviews = reviews.filtered(lambda r: r.review_type == 'message')
            return {
                'success': True,
                'data': {
                    'total_reviews': total,
                    'avg_score': round(avg_score, 2),
                    'total_listen_seconds': total_listen_sec,
                    'call_reviews': len(call_reviews),
                    'message_reviews': len(message_reviews),
                },
            }
        except Exception as e:
            _logger.exception('qa stats error')
            return {'success': False, 'error': str(e)}

    def _review_to_dict(self, review):
        """Serialize a QA review record to a JSON-safe dict."""
        return {
            'id': review.id,
            'review_number': review.review_number,
            'review_type': review.review_type,
            'status': review.status,
            'call_id': review.call_id.id if review.call_id else None,
            'conversation_id': review.conversation_id or '',
            'customer_id': review.customer_id.id if review.customer_id else None,
            'customer_name': review.customer_id.name if review.customer_id else '',
            'agent_id': review.agent_id.id if review.agent_id else None,
            'agent_name': review.agent_id.name if review.agent_id else '',
            'reviewer_id': review.reviewer_id.id if review.reviewer_id else None,
            'reviewer_name': review.reviewer_id.name if review.reviewer_id else '',
            'branch_id': review.branch_id.id if review.branch_id else None,
            'reviewed_at': review.reviewed_at.isoformat() if review.reviewed_at else None,
            'listen_duration_seconds': review.listen_duration_seconds,
            'score': review.score,
            'greeting_score': review.greeting_score,
            'product_knowledge_score': review.product_knowledge_score,
            'problem_solving_score': review.problem_solving_score,
            'professionalism_score': review.professionalism_score,
            'compliance_score': review.compliance_score,
            'issues_found': review.issues_found or '',
            'qa_notes': review.qa_notes or '',
            'feedback_to_agent': review.feedback_to_agent or '',
        }
