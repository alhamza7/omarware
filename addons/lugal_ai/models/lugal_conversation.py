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
        ('general', 'General Query'),
        ('product', 'Product Query'),
        ('sales', 'Sales Query'),
        ('customer', 'Customer Query'),
        ('employee', 'Employee Query'),
        ('analytical', 'Analytical Query'),
        ('operational', 'Operational Query'),
        ('out_of_scope', 'Out of Scope'),
    ], string='Category', default='general')
    
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
    
    def _determine_category(self, odoo_data):
        """Determine conversation category based on data used"""
        if not odoo_data['records']:
            return 'general'
        
        models_used = [r['model'] for r in odoo_data['records']]
        
        if 'product.product' in models_used:
            return 'product'
        elif 'sale.order' in models_used:
            return 'sales'
        elif 'res.partner' in models_used:
            return 'customer'
        elif 'account.move' in models_used:
            return 'analytical'
        else:
            return 'operational'
    
    def _collect_odoo_data(self, question, role):
        """Collect relevant data from Odoo based on the question"""
        data = {
            'role': role,
            'source': 'odoo',
            'records': []
        }
        
        question_lower = question.lower()
        
        # Check for product-related questions
        if any(word in question_lower for word in ['منتج', 'منتجات', 'product', 'products', 'مخزون', 'stock', 'كم عدد', 'how many']):
            products = self.env['product.product'].search_read(
                [('active', '=', True)],
                ['name', 'default_code', 'list_price', 'qty_available', 'categ_id'],
                limit=100
            )
            data['records'].append({
                'model': 'product.product',
                'count': len(products),
                'data': products
            })
        
        # Check for sales-related questions
        if any(word in question_lower for word in ['مبيعات', 'بيع', 'sales', 'sale', 'order', 'طلب', 'طلبات']):
            sales = self.env['sale.order'].search_read(
                [('state', '!=', 'cancel')],
                ['name', 'partner_id', 'amount_total', 'state', 'date_order'],
                limit=50
            )
            data['records'].append({
                'model': 'sale.order',
                'count': len(sales),
                'data': sales
            })
        
        # Check for customer-related questions
        if any(word in question_lower for word in ['عميل', 'عملاء', 'customer', 'customers', 'زبون', 'زبائن']):
            if role in ['admin', 'employee']:
                customers = self.env['res.partner'].search_read(
                    [('customer_rank', '>', 0)],
                    ['name', 'email', 'phone', 'city', 'country_id'],
                    limit=50
                )
                data['records'].append({
                    'model': 'res.partner',
                    'count': len(customers),
                    'data': customers
                })
        
        # Check for invoice-related questions
        if any(word in question_lower for word in ['فاتورة', 'فواتير', 'invoice', 'invoices']):
            invoices = self.env['account.move'].search_read(
                [('move_type', 'in', ['out_invoice', 'out_refund'])],
                ['name', 'partner_id', 'amount_total', 'state', 'invoice_date'],
                limit=50
            )
            data['records'].append({
                'model': 'account.move',
                'count': len(invoices),
                'data': invoices
            })
        
        # Check for employee-related questions
        if role == 'admin' and any(word in question_lower for word in ['موظف', 'موظفين', 'employee', 'employees', 'عامل', 'عمال']):
            employees = self.env['hr.employee'].search_read(
                [('active', '=', True)],
                ['name', 'job_title', 'department_id', 'work_email', 'work_phone'],
                limit=50
            )
            data['records'].append({
                'model': 'hr.employee',
                'count': len(employees),
                'data': employees
            })
        
        # Check for warehouse/stock questions
        if any(word in question_lower for word in ['مخزن', 'مستودع', 'warehouse', 'stock', 'inventory']):
            stock_locations = self.env['stock.location'].search_read(
                [('usage', '=', 'internal')],
                ['name', 'complete_name', 'location_id'],
                limit=20
            )
            data['records'].append({
                'model': 'stock.location',
                'count': len(stock_locations),
                'data': stock_locations
            })
        
        # If no specific data found, get basic stats
        if not data['records']:
            stats = {
                'total_products': self.env['product.product'].search_count([('active', '=', True)]),
                'total_customers': self.env['res.partner'].search_count([('customer_rank', '>', 0)]),
                'total_sales': self.env['sale.order'].search_count([('state', '!=', 'cancel')]),
            }
            data['records'].append({
                'model': 'system.stats',
                'count': 1,
                'data': [stats]
            })
        
        return data
    
    def _build_prompt(self, question, role, odoo_data):
        """Build enriched prompt with Odoo data"""
        prompt_parts = []
        
        # Add context header
        prompt_parts.append("=== CONTEXT ===")
        prompt_parts.append(f"User Role: {role.upper()}")
        prompt_parts.append("")
        
        # Add Odoo data if available
        if odoo_data['records']:
            prompt_parts.append("=== AVAILABLE DATA FROM ODOO ===")
            for record_set in odoo_data['records']:
                model_name = record_set['model']
                count = record_set['count']
                data = record_set['data']
                
                prompt_parts.append(f"\nModel: {model_name}")
                prompt_parts.append(f"Total Records: {count}")
                
                # Include actual data (limit to avoid token overflow)
                if data:
                    # Only show first 15 records to save tokens
                    prompt_parts.append("Data Sample:")
                    prompt_parts.append(json.dumps(data[:15], ensure_ascii=False, indent=2))
                    if count > 15:
                        prompt_parts.append(f"... and {count - 15} more records")
        else:
            prompt_parts.append("=== NO SPECIFIC DATA RETRIEVED ===")
            prompt_parts.append("Note: No specific Odoo records matched this query.")
        
        # Add the actual question
        prompt_parts.append("")
        prompt_parts.append("=== USER QUESTION ===")
        prompt_parts.append(question)
        
        # Add instructions
        prompt_parts.append("")
        prompt_parts.append("=== INSTRUCTIONS ===")
        prompt_parts.append("- Provide a clear, direct answer based ONLY on the data provided above")
        prompt_parts.append("- Use numbers and facts from the data")
        prompt_parts.append("- If data is insufficient, clearly state what's missing")
        prompt_parts.append("- Answer in the SAME language as the question (Arabic or English)")
        prompt_parts.append("- Be concise and professional")
        prompt_parts.append("- Do NOT mention 'Odoo', 'database', or 'system' - just answer naturally")
        
        return "\n".join(prompt_parts)
    
    @api.model
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
            # Collect relevant data from Odoo
            odoo_data = self._collect_odoo_data(question, role)
            
            # Call Gemini API
            import google.generativeai as genai
            genai.configure(api_key=config.gemini_api_key)
            
            model = genai.GenerativeModel(
                config.gemini_model or 'gemini-2.0-flash-exp',
                system_instruction=config.system_prompt or "You are Lugal AI, an intelligent assistant for Odoo ERP system."
            )
            
            # Build enriched prompt with data
            enriched_prompt = self._build_prompt(question, role, odoo_data)
            
            # Generate response
            response = model.generate_content(enriched_prompt)
            answer = response.text
            
            # Calculate response time
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Determine category from data used
            category = self._determine_category(odoo_data)
            
            # Update conversation
            conversation.write({
                'answer': answer,
                'response_time_ms': response_time,
                'category': category,
                'context_data': json.dumps(odoo_data, ensure_ascii=False),
                'data_models_used': ', '.join([r['model'] for r in odoo_data['records']]) if odoo_data['records'] else None,
                'records_count': sum([r['count'] for r in odoo_data['records']]) if odoo_data['records'] else 0
            })
            
            # Calculate token usage (estimate)
            input_tokens = len(enriched_prompt.split()) * 1.3  # Rough estimate
            output_tokens = len(answer.split()) * 1.3
            
            return {
                'success': True,
                'answer': answer,
                'conversation_id': conversation.id,
                'response_time_ms': response_time,
                'was_cached': False,
                'category': category,
                'models_used': ', '.join([r['model'] for r in odoo_data['records']]) if odoo_data['records'] else None,
                'records_count': sum([r['count'] for r in odoo_data['records']]) if odoo_data['records'] else 0,
                'input_tokens': int(input_tokens),
                'output_tokens': int(output_tokens)
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
    
    @api.model
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


