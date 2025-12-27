# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json
import logging

_logger = logging.getLogger(__name__)


class LugalConversation(models.Model):
    _name = 'lugal.conversation'
    _description = 'Lugal AI Conversation History'
    _rec_name = 'display_name'
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Partner', related='user_id.partner_id', store=True)
    
    # Question
    question = fields.Text(string='Question', required=True)
    question_language = fields.Selection([
        ('ar', 'Arabic'),
        ('en', 'English'),
        ('mixed', 'Mixed'),
    ], string='Question Language', compute='_compute_question_language', store=True)
    
    # Answer
    answer = fields.Text(string='Answer')
    
    # Classification
    category = fields.Selection([
        ('product', 'Product Query'),
        ('sales', 'Sales Query'),
        ('customer', 'Customer Query'),
        ('employee', 'Employee Query'),
        ('analytical', 'Analytical Query'),
        ('operational', 'Operational Query'),
        ('out_of_scope', 'Out of Scope'),
    ], string='Category')
    
    question_index_id = fields.Many2one('lugal.question.index', string='Matched Pattern')
    similarity_score = fields.Float(string='Pattern Similarity %', digits=(5, 2))
    
    # Role & Permissions
    user_role = fields.Selection([
        ('admin', 'Admin'),
        ('employee', 'Employee'),
        ('customer', 'Customer'),
    ], string='User Role', required=True)
    
    # Performance Metrics
    response_time_ms = fields.Float(string='Response Time (ms)')
    input_tokens = fields.Integer(string='Input Tokens')
    output_tokens = fields.Integer(string='Output Tokens')
    total_tokens = fields.Integer(string='Total Tokens', compute='_compute_total_tokens', store=True)
    
    # Context Data
    context_data = fields.Text(string='Context Data (JSON)',
                                help='JSON data that was provided to Gemini')
    data_models_used = fields.Char(string='Models Used',
                                     help='Comma-separated list of Odoo models queried')
    records_count = fields.Integer(string='Records Retrieved')
    
    # Cache
    was_cached = fields.Boolean(string='Was Cached Response', default=False)
    
    # Status
    status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cached', 'From Cache'),
    ], string='Status', default='success')
    
    error_message = fields.Text(string='Error Message')
    
    # Feedback
    user_rating = fields.Selection([
        ('1', '👎 Very Poor'),
        ('2', '😐 Poor'),
        ('3', '🙂 Good'),
        ('4', '😊 Very Good'),
        ('5', '🤩 Excellent'),
    ], string='User Rating')
    
    user_feedback = fields.Text(string='User Feedback')
    
    # Display Name
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    
    @api.depends('question')
    def _compute_display_name(self):
        for record in self:
            if record.question:
                # Truncate to 60 chars
                record.display_name = record.question[:60] + ('...' if len(record.question) > 60 else '')
            else:
                record.display_name = 'Conversation #' + str(record.id)
    
    @api.depends('question')
    def _compute_question_language(self):
        for record in self:
            if not record.question:
                record.question_language = 'en'
                continue
                
            arabic_chars = sum(1 for c in record.question if '\u0600' <= c <= '\u06FF')
            english_chars = sum(1 for c in record.question if c.isalpha() and not ('\u0600' <= c <= '\u06FF'))
            
            total = arabic_chars + english_chars
            if total == 0:
                record.question_language = 'en'
            elif arabic_chars > english_chars * 2:
                record.question_language = 'ar'
            elif english_chars > arabic_chars * 2:
                record.question_language = 'en'
            else:
                record.question_language = 'mixed'
    
    @api.depends('input_tokens', 'output_tokens')
    def _compute_total_tokens(self):
        for record in self:
            record.total_tokens = (record.input_tokens or 0) + (record.output_tokens or 0)
    
    def action_view_context_data(self):
        """View context data in a modal"""
        self.ensure_one()
        try:
            context_json = json.loads(self.context_data) if self.context_data else {}
            formatted_json = json.dumps(context_json, indent=2, ensure_ascii=False)
        except:
            formatted_json = self.context_data or "No context data"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Context Data',
                'message': formatted_json,
                'type': 'info',
                'sticky': True,
            }
        }
    
    @api.model
    def get_conversation_stats(self, user_id=None, days=30):
        """Get conversation statistics for a user"""
        domain = [('create_date', '>=', fields.Datetime.now() - fields.timedelta(days=days))]
        
        if user_id:
            domain.append(('user_id', '=', user_id))
        
        conversations = self.search(domain)
        
        return {
            'total_conversations': len(conversations),
            'avg_response_time': sum(conversations.mapped('response_time_ms')) / len(conversations) if conversations else 0,
            'total_tokens': sum(conversations.mapped('total_tokens')),
            'cached_responses': len(conversations.filtered(lambda c: c.was_cached)),
            'categories': {
                cat: len(conversations.filtered(lambda c: c.category == cat))
                for cat in dict(self._fields['category'].selection).keys()
            },
            'avg_rating': sum(int(c.user_rating) for c in conversations if c.user_rating) / len([c for c in conversations if c.user_rating]) if any(conversations.mapped('user_rating')) else 0,
        }
    
    def ask_question(self, question, context=None):
        """Ask a question and get AI response - for chat interface"""
        from datetime import datetime
        
        config = self.env['lugal.config'].search([], limit=1)
        if not config or not config.gemini_api_key:
            return {
                'success': False,
                'error': 'Gemini API not configured. Please configure it in Settings.'
            }
        
        start_time = datetime.now()
        
        # Get user role
        user = self.env.user
        role = 'admin' if user.has_group('base.group_system') else 'employee'
        
        # Create conversation record
        conversation = self.create({
            'user_id': user.id,
            'user_role': role,
            'question': question,
            'status': 'success'
        })
        
        try:
            # Call Gemini API
            import google.generativeai as genai
            genai.configure(api_key=config.gemini_api_key)
            
            model = genai.GenerativeModel(config.gemini_model or 'gemini-2.0-flash-exp')
            
            # Generate response
            response = model.generate_content(question)
            answer = response.text
            
            # Calculate response time
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Update conversation
            conversation.write({
                'answer': answer,
                'response_time_ms': response_time,
                'category': 'general'
            })
            
            return {
                'success': True,
                'answer': answer,
                'conversation_id': conversation.id,
                'response_time_ms': response_time,
                'was_cached': False,
                'category': 'general'
            }
            
        except Exception as e:
            conversation.write({
                'status': 'failed',
                'error_message': str(e)
            })
            return {
                'success': False,
                'error': f'Failed to get response: {str(e)}'
            }
    
    def get_stats(self, days=30):
        """Get conversation statistics for chat interface"""
        from datetime import datetime, timedelta
        
        domain = [('create_date', '>=', datetime.now() - timedelta(days=days))]
        conversations = self.search(domain)
        
        total = len(conversations)
        if total == 0:
            return {
                'total_questions': 0,
                'avg_response_time': 0,
                'cached_percentage': 0,
                'today_questions': 0
            }
        
        # Today's questions
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_conversations = self.search([('create_date', '>=', today_start)])
        
        # Average response time
        completed = conversations.filtered(lambda c: c.status == 'success' and c.response_time_ms)
        avg_time = sum(c.response_time_ms for c in completed) / len(completed) if completed else 0
        
        # Cached percentage
        cached = conversations.filtered(lambda c: c.was_cached)
        cached_pct = (len(cached) / total * 100) if total > 0 else 0
        
        return {
            'total_questions': total,
            'avg_response_time': int(avg_time),
            'cached_percentage': int(cached_pct),
            'today_questions': len(today_conversations)
        }
    
    def rate_conversation(self, rating):
        """Rate a conversation"""
        self.ensure_one()
        self.write({'user_rating': str(rating)})
        return True


