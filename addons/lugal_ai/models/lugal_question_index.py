# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import difflib

_logger = logging.getLogger(__name__)


class LugalQuestionIndex(models.Model):
    _name = 'lugal.question.index'
    _description = 'Lugal AI Question Index'
    _rec_name = 'question_pattern'
    _order = 'usage_count desc, id desc'

    question_pattern = fields.Char(string='Question Pattern', required=True, 
                                     help='Pattern or template for similar questions')
    category = fields.Selection([
        ('general', 'General Query'),
        ('product', 'Product Query'),
        ('sales', 'Sales Query'),
        ('customer', 'Customer Query'),
        ('employee', 'Employee Query'),
        ('analytical', 'Analytical Query'),
        ('operational', 'Operational Query'),
        ('out_of_scope', 'Out of Scope'),
    ], string='Category', required=True, default='general')
    
    # Answer Template
    answer_template = fields.Text(string='Answer Template',
                                   help='Template for generating consistent answers')
    
    # Required Data
    required_data_models = fields.Char(string='Required Models',
                                        help='Comma-separated list of Odoo models needed (e.g., product.product,sale.order)')
    required_fields = fields.Text(string='Required Fields',
                                   help='Fields needed from each model')
    
    # Multilingual Support
    question_pattern_ar = fields.Char(string='Question Pattern (Arabic)')
    question_pattern_en = fields.Char(string='Question Pattern (English)')
    
    # Usage Statistics
    usage_count = fields.Integer(string='Usage Count', default=0, readonly=True)
    last_used_date = fields.Datetime(string='Last Used', readonly=True)
    avg_response_time = fields.Float(string='Avg Response Time (ms)', readonly=True)
    
    # Permissions
    allowed_roles = fields.Char(string='Allowed Roles',
                                 help='Comma-separated roles (admin,employee,customer)',
                                 default='admin,employee,customer')
    
    # Sample Questions
    sample_questions = fields.Text(string='Sample Questions',
                                    help='Example questions that match this pattern')
    
    # Active
    is_active = fields.Boolean(string='Active', default=True)
    
    @api.model
    def find_matching_pattern(self, question, language='auto'):
        """Find best matching question pattern using fuzzy matching"""
        
        # Auto-detect language if needed
        if language == 'auto':
            language = self._detect_language(question)
        
        # Search in appropriate language field
        if language == 'ar':
            patterns = self.search([('is_active', '=', True), ('question_pattern_ar', '!=', False)])
            pattern_field = 'question_pattern_ar'
        else:
            patterns = self.search([('is_active', '=', True), ('question_pattern_en', '!=', False)])
            pattern_field = 'question_pattern_en'
        
        if not patterns:
            # Fallback to default patterns
            patterns = self.search([('is_active', '=', True)])
            pattern_field = 'question_pattern'
        
        best_match = None
        best_ratio = 0.0
        
        question_lower = question.lower().strip()
        
        for pattern in patterns:
            pattern_text = getattr(pattern, pattern_field) or pattern.question_pattern
            if not pattern_text:
                continue
                
            pattern_lower = pattern_text.lower().strip()
            
            # Calculate similarity ratio
            ratio = difflib.SequenceMatcher(None, question_lower, pattern_lower).ratio()
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = pattern
        
        # Return match if similarity >= 75%
        if best_ratio >= 0.75:
            # Update usage statistics
            best_match.sudo().write({
                'usage_count': best_match.usage_count + 1,
                'last_used_date': fields.Datetime.now(),
            })
            return best_match, best_ratio
        
        return None, 0.0
    
    @api.model
    def _detect_language(self, text):
        """Simple language detection based on Arabic character presence"""
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return 'en'
        
        arabic_ratio = arabic_chars / total_chars
        return 'ar' if arabic_ratio > 0.3 else 'en'
    
    @api.model
    def classify_question(self, question):
        """Classify question into category"""
        question_lower = question.lower()
        
        # Keywords for classification
        product_keywords = ['منتج', 'سعر', 'متوفر', 'كمية', 'product', 'price', 'available', 'stock', 'quantity']
        sales_keywords = ['مبيعات', 'فاتورة', 'طلب', 'sales', 'invoice', 'order', 'revenue']
        customer_keywords = ['عميل', 'زبون', 'customer', 'client', 'partner']
        employee_keywords = ['موظف', 'عامل', 'employee', 'staff', 'worker']
        analytical_keywords = ['تحليل', 'إحصائية', 'تقرير', 'مقارنة', 'analysis', 'report', 'statistics', 'compare']
        
        # Count keyword matches
        scores = {
            'product': sum(1 for kw in product_keywords if kw in question_lower),
            'sales': sum(1 for kw in sales_keywords if kw in question_lower),
            'customer': sum(1 for kw in customer_keywords if kw in question_lower),
            'employee': sum(1 for kw in employee_keywords if kw in question_lower),
            'analytical': sum(1 for kw in analytical_keywords if kw in question_lower),
        }
        
        # Get category with highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return 'operational'  # Default category
    
    def action_view_usage_stats(self):
        """Open usage statistics view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Question Usage Statistics',
            'res_model': 'lugal.question.index',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

