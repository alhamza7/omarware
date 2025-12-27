# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json
import logging
from datetime import datetime, date

_logger = logging.getLogger(__name__)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


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
            formatted_json = json.dumps(context_json, indent=2, ensure_ascii=False, default=json_serial)
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
        
        if 'product.product' in models_used or 'product.count' in models_used:
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
        _logger.info(f"🔎 Analyzing question (lowercase): {question_lower}")
        
        # Check if asking about stock quantities in warehouses
        asking_about_warehouse_quantities = any(word in question_lower for word in ['كميات', 'كل مخزن', 'في المخازن', 'by location', 'per warehouse', 'في كل'])
        _logger.info(f"📍 Asking about warehouse quantities: {asking_about_warehouse_quantities}")
        
        try:
            # Check for product-related questions - must be specific
            product_keywords = ['منتج', 'منتجات', 'product', 'products', 'مخزون', 'stock', 'كميات']
            # More specific keywords that indicate product questions
            specific_product_keywords = [
                'كم عدد', 'how many', 'عن منتج', 'about product', 'معلومات عن', 'info about',
                'معلومات منتج', 'product info', 'تفاصيل', 'details', 'أرني', 'show me',
                'اعرض', 'display', 'list', 'قائمة', 'ابحث', 'search', 'كود', 'code',
                'ما معلومات', 'what info', 'what is', 'ما هو', 'ما هي'
            ]
            
            # Check if question is too short or generic (1-2 words only with no context)
            question_words = question_lower.split()
            is_too_generic = len(question_words) <= 2 and not any(keyword in question_lower for keyword in specific_product_keywords)
            
            # Extract potential product names - be smarter about it
            common_words = [
                'منتج', 'منتجات', 'product', 'products',
                'في', 'كل', 'the', 'in', 'على', 'عن', 'من', 'إلى', 
                'هل', 'ما', 'ماذا', 'كيف', 'أين', 'لماذا',
                'تعرف', 'لدينا', 'لدينا؟', 'عندنا', 'عندك',
                'موجود', 'موجودة', 'have', 'has', 'know',
                'كم', 'how', 'many', 'much', 'عدد', 'number',
                'ممكن', 'اريد', 'want', 'need', 'يرجى', 'please',
                'معلومات', 'information', 'info', 'تفاصيل', 'details',
                'كود', 'code', 'اسم', 'name', 'سعر', 'price'
            ]
            
            # Extract product name more intelligently
            potential_product_names = []
            
            # Pattern 0: Direct product name - "منتج X" or "product X"
            if question_lower.strip().startswith('منتج '):
                product_name = question_lower.replace('منتج', '').strip()
                if product_name:
                    potential_product_names = [product_name]
                    _logger.info(f"🎯 Direct product: {product_name}")
            
            elif question_lower.strip().startswith('product '):
                product_name = question_lower.replace('product', '').strip()
                if product_name:
                    potential_product_names = [product_name]
                    _logger.info(f"🎯 Direct product: {product_name}")
            
            # Pattern 1: "معلومات عن X" or "info about X"
            elif 'معلومات عن' in question_lower:
                product_part = question_lower.split('معلومات عن')[-1].strip()
                # Clean up the extracted part
                product_part = product_part.replace('منتج', '').replace('?', '').replace('؟', '').strip()
                if product_part:
                    potential_product_names = [product_part]
                    _logger.info(f"🎯 Extracted from 'معلومات عن': {product_part}")
            
            elif 'info about' in question_lower:
                product_part = question_lower.split('info about')[-1].strip()
                product_part = product_part.replace('product', '').replace('?', '').strip()
                if product_part:
                    potential_product_names = [product_part]
                    _logger.info(f"🎯 Extracted from 'info about': {product_part}")
            
            # Pattern 2: "كود X" or "code Y"
            elif 'كود ' in question_lower or 'code ' in question_lower:
                for word in question_words:
                    # Look for codes (alphanumeric)
                    if any(c.isdigit() for c in word) and len(word) >= 4:
                        potential_product_names.append(word.upper())  # Codes usually uppercase
                        _logger.info(f"🔢 Found potential code: {word.upper()}")
            
            # Pattern 3: Direct product name mention (first check for codes in the question)
            if not potential_product_names:
                # First, look for product codes (ADF00016 format)
                for word in question_words:
                    if (any(c.isdigit() for c in word) and any(c.isalpha() for c in word) and len(word) >= 5):
                        potential_product_names.append(word)
                        _logger.info(f"🔢 Found product code in question: {word}")
                
                # If no codes found, extract ALL meaningful words (even if just one word like "لاكوست")
                if not potential_product_names:
                    # Join all non-common words together
                    meaningful_words = [word for word in question_words if len(word) > 2 and word not in common_words]
                    if meaningful_words:
                        # Use the whole phrase if multiple words, or single word if alone
                        potential_product_names = meaningful_words
                        _logger.info(f"📝 Extracted potential product name(s): {meaningful_words}")
            
            # Determine if this is a product question
            is_product_question = any(word in question_lower for word in product_keywords)
            has_specific_intent = any(word in question_lower for word in specific_product_keywords)
            
            # Special case: If question is short (1-4 words) with potential product names, assume it's a direct product search
            # But exclude greetings and common questions
            greeting_words = ['السلام', 'عليكم', 'hello', 'hi', 'مرحبا', 'كيف', 'how', 'شكرا', 'thanks', 'وداعا', 'bye', 'صباح', 'مساء', 'good', 'morning']
            common_questions = ['نعم', 'لا', 'yes', 'no', 'ok', 'حسنا', 'تمام', 'طيب']
            is_likely_greeting = any(word in question_lower for word in greeting_words)
            is_common_reply = any(word == question_lower.strip() for word in common_questions)
            
            is_direct_product_search = (
                len(question_words) <= 4 and 
                len(potential_product_names) > 0 and
                not is_likely_greeting and
                not is_common_reply
            )
            
            # Also check if the ENTIRE question is just a product code (like "ADF00016")
            is_just_a_code = (
                len(question_words) == 1 and
                len(question_words[0]) >= 5 and
                any(c.isdigit() for c in question_words[0]) and
                any(c.isalpha() for c in question_words[0])
            )
            
            # Check if it's just a product name (1-2 words, not greeting, looks like a product name)
            is_just_product_name = (
                len(question_words) <= 2 and
                len(question_words[0]) >= 3 and  # At least 3 characters
                not is_likely_greeting and
                not is_common_reply and
                len(potential_product_names) > 0
            )
            
            # Special case: Question starts with "منتج" = direct product search
            starts_with_product = question_lower.strip().startswith('منتج ') or question_lower.strip().startswith('product ')
            
            # If direct search, just a code, just a name, or starts with "منتج", force it to be a product question
            if is_direct_product_search or starts_with_product or is_just_a_code or is_just_product_name:
                is_product_question = True
                has_specific_intent = True
                if is_just_a_code:
                    _logger.info(f"🔢 Product code search detected: {question_words[0]}")
                    # Make sure the code is in potential_product_names
                    if not potential_product_names:
                        potential_product_names = [question_words[0].upper()]
                elif is_just_product_name:
                    _logger.info(f"🏷️ Direct product name search: {' '.join(potential_product_names)}")
                else:
                    _logger.info(f"🎯 Direct product search detected!")
            
            # REMOVE the generic filter - if we have potential product names, search for them!
            # The old logic was too restrictive
            
            # If we have potential product names but no explicit product keywords, still search
            if len(potential_product_names) > 0 and not is_product_question:
                # Check if it's likely a product search (not a greeting)
                if not is_likely_greeting and not is_common_reply:
                    is_product_question = True
                    has_specific_intent = True
                    _logger.info(f"🔄 No explicit product keywords, but have potential names - treating as product search")
            
            _logger.info(f"🛍️ Is product question: {is_product_question}, has_intent: {has_specific_intent}, direct_search: {is_direct_product_search}, potential_products: {potential_product_names}")
            
            if is_product_question:
                _logger.info(f"📦 Starting product data collection...")
                
                # Check if asking about count/number - highest priority
                asking_about_count = any(word in question_lower for word in ['كم عدد', 'how many', 'عدد المنتجات', 'number of', 'كم منتج', 'how many products'])
                
                # If asking about count, just get count (minimal data)
                if asking_about_count:
                    _logger.info(f"🔢 Asking about product COUNT - getting total count only")
                    # Get count only
                    total_count = self.env['product.product'].search_count([('active', '=', True)])
                    _logger.info(f"✅ Total products: {total_count}")
                    
                    # Add count to data directly
                    data['records'].append({
                        'model': 'product.count',
                        'count': total_count,
                        'data': [{'total_products': total_count, 'message': f'لديكم إجمالي {total_count} منتج نشط'}]
                    })
                    _logger.info(f"📦 Product count collected successfully")
                
                # Otherwise, get detailed product data
                if not asking_about_count:
                    # Search for specific product if mentioned
                    product_domain = [('active', '=', True)]
                    
                    # Filter out generic words from potential product names
                    generic_words = ['المنتجات', 'منتجات', 'منتج', 'products', 'product', 'عدد', 'كمية', 'how', 'many', 'what', 'where']
                    specific_product_names = [word for word in potential_product_names if word not in generic_words]
                    
                    _logger.info(f"🔍 After filtering: potential_product_names={potential_product_names}, specific_product_names={specific_product_names}")
                    
                    # Search for products based on extracted names  
                    if specific_product_names:
                        # Build search for name OR code
                        search_term = ' '.join(specific_product_names)
                        
                        # Clean up the search term
                        search_term_clean = search_term.strip().replace('؟', '').replace('?', '')
                        
                        # Check if it looks like a product code (contains numbers/letters mix)
                        looks_like_code = any(c.isdigit() for c in search_term_clean) and any(c.isalpha() for c in search_term_clean)
                        
                        if looks_like_code:
                            # Prioritize code search
                            product_domain = ['|', '|', '|',
                                ('default_code', '=ilike', search_term_clean),  # Exact match first
                                ('default_code', 'ilike', search_term_clean),
                                ('name', 'ilike', search_term_clean),
                                ('active', '=', True)
                            ]
                            _logger.info(f"🔢 Searching for product CODE: {search_term_clean}")
                        else:
                            # Name search
                            if len(specific_product_names) == 1:
                                # Single word search - very flexible
                                product_domain = ['|',
                                    ('name', 'ilike', search_term_clean),
                                    ('default_code', 'ilike', search_term_clean),
                                    ('active', '=', True)
                                ]
                                _logger.info(f"🔎 Searching for product NAME (single word): '{search_term_clean}'")
                            else:
                                # Multiple words - search for phrase first, then individual words
                                product_domain = ['|', '|',
                                    ('name', 'ilike', search_term_clean),  # Try full phrase first
                                    ('default_code', 'ilike', search_term_clean),
                                    ('active', '=', True)
                                ]
                                _logger.info(f"🔎 Searching for product NAME (phrase): '{search_term_clean}'")
                    
                    elif potential_product_names:
                        # Fall back to using potential names if specific names are empty
                        search_term = ' '.join(potential_product_names).strip()
                        product_domain = ['|',
                            ('name', 'ilike', search_term),
                            ('default_code', 'ilike', search_term),
                            ('active', '=', True)
                        ]
                        _logger.info(f"🔎 Fallback search using potential names: '{search_term}'")
                    
                    else:
                        # No names at all - get sample
                        _logger.info(f"🔎 No product names - getting product sample")
                    
                    _logger.info(f"🔍 Searching products with domain: {product_domain}")
                    
                    # Try to get full product data, fallback to basic if error
                    try:
                        products = self.env['product.product'].search_read(
                        product_domain,
                        [
                            # Basic Info
                            'name', 'default_code', 'barcode', 'type', 'active',
                            # Pricing
                            'list_price', 'standard_price', 'currency_id',
                            # Stock
                            'qty_available', 'virtual_available', 'incoming_qty', 'outgoing_qty',
                            # Categories & Classification
                            'categ_id', 'pos_categ_ids',
                            # Units
                            'uom_id',
                            # Supplier & Purchase
                            'seller_ids',
                            # Sales
                            'sale_ok', 'purchase_ok',
                            # Taxes
                            'taxes_id', 'supplier_taxes_id',
                            # Description
                            'description', 'description_sale', 'description_purchase',
                            # Tracking
                            'tracking',
                            # Weight & Volume
                            'weight', 'volume',
                            # Images
                            'image_128',
                            # Variants
                            'product_tmpl_id', 'attribute_line_ids',
                            # Additional
                            'company_id', 'create_date', 'write_date'
                        ],
                            limit=100
                        )
                        _logger.info(f"✅ Found {len(products)} products with full data")
                    except Exception as field_error:
                        _logger.warning(f"⚠️ Full field search failed: {str(field_error)}, trying basic fields...")
                        # Fallback to basic fields only
                        products = self.env['product.product'].search_read(
                            product_domain,
                            ['name', 'default_code', 'list_price', 'qty_available', 'categ_id', 'uom_id', 'barcode'],
                            limit=100
                        )
                        _logger.info(f"✅ Found {len(products)} products with basic data")
                    
                    # If no products found and we have a specific search term, try fuzzy search
                    if not products and specific_product_names:
                        _logger.warning(f"⚠️ No exact match, trying fuzzy search...")
                        search_term = ' '.join(specific_product_names)
                        # Try searching each word separately
                        fuzzy_domain = ['|'] * (len(specific_product_names) - 1) if len(specific_product_names) > 1 else []
                        for word in specific_product_names:
                            fuzzy_domain.extend([
                                '|',
                                ('name', 'ilike', word),
                                ('default_code', 'ilike', word)
                            ])
                        if fuzzy_domain:
                            fuzzy_domain.append(('active', '=', True))
                            try:
                                products = self.env['product.product'].search_read(
                                    fuzzy_domain,
                                    ['name', 'default_code', 'list_price', 'qty_available', 'categ_id', 'uom_id', 'barcode'],
                                    limit=10
                                )
                                if products:
                                    _logger.info(f"✅ Fuzzy search found {len(products)} products")
                            except:
                                pass
                    
                    # Get detailed stock and related info for products
                    if products:
                        product_ids = [p['id'] for p in products]
                        
                        # 1. Get stock quantities by location
                        stock_quants = self.env['stock.quant'].search_read(
                            [
                                ('product_id', 'in', product_ids),
                                ('location_id.usage', '=', 'internal')
                            ],
                            ['product_id', 'location_id', 'quantity', 'reserved_quantity', 'available_quantity', 'lot_id'],
                            limit=500
                        )
                        
                        # 2. Get recent stock moves (last movements)
                        recent_moves = self.env['stock.move'].search_read(
                            [
                                ('product_id', 'in', product_ids),
                                ('state', '=', 'done')
                            ],
                            ['product_id', 'location_id', 'location_dest_id', 'product_uom_qty', 'date', 'reference', 'origin'],
                            order='date desc',
                            limit=50
                        )
                        
                        # 3. Get supplier info
                        supplier_info = self.env['product.supplierinfo'].search_read(
                            [('product_id', 'in', product_ids)],
                            ['product_id', 'partner_id', 'price', 'min_qty', 'delay', 'currency_id'],
                            limit=100
                        )
                        
                        # 4. Get recent sales
                        sale_lines = self.env['sale.order.line'].search_read(
                            [
                                ('product_id', 'in', product_ids),
                                ('state', 'in', ['sale', 'done'])
                            ],
                            ['product_id', 'order_id', 'product_uom_qty', 'price_unit', 'price_subtotal', 'order_partner_id'],
                            order='create_date desc',
                            limit=30
                        )
                        
                        # 5. Get product variants info
                        product_templates = list(set([p['product_tmpl_id'][0] if p.get('product_tmpl_id') else None for p in products if p.get('product_tmpl_id')]))
                        variants_info = []
                        if product_templates:
                            variants_info = self.env['product.template'].search_read(
                                [('id', 'in', product_templates)],
                                ['name', 'product_variant_count', 'attribute_line_ids'],
                                limit=50
                            )
                        
                        # Organize all data by product
                        for product in products:
                            pid = product['id']
                            
                            # Stock by location
                            product_quants = [q for q in stock_quants if q.get('product_id') and q['product_id'][0] == pid]
                            product_quants = [q for q in product_quants if q.get('quantity', 0) > 0]
                            product['stock_by_location'] = product_quants
                            product['total_locations'] = len(product_quants)
                            
                            # Recent movements
                            product_moves = [m for m in recent_moves if m.get('product_id') and m['product_id'][0] == pid]
                            product['recent_movements'] = product_moves[:10]  # Last 10 movements
                            
                            # Suppliers
                            product_suppliers = [s for s in supplier_info if s.get('product_id') and s['product_id'][0] == pid]
                            product['suppliers'] = product_suppliers
                            
                            # Recent sales
                            product_sales = [s for s in sale_lines if s.get('product_id') and s['product_id'][0] == pid]
                            product['recent_sales'] = product_sales[:10]  # Last 10 sales
                            product['total_sales_qty'] = sum([s.get('product_uom_qty', 0) for s in product_sales])
                            product['total_sales_amount'] = sum([s.get('price_subtotal', 0) for s in product_sales])
                            
                            _logger.info(f"📍 Product {product['name']}: {len(product_quants)} locations, {len(product_moves)} movements, {len(product_suppliers)} suppliers, {len(product_sales)} sales")
                    
                    if products:
                        data['records'].append({
                            'model': 'product.product',
                            'count': len(products),
                            'data': products
                        })
                        _logger.info(f"📦 Collected {len(products)} products with stock details for AI")
                        _logger.info(f"📋 First product: {products[0].get('name', 'N/A')} (Code: {products[0].get('default_code', 'N/A')})")
                    else:
                        # No products found - add empty result to show we searched
                        data['records'].append({
                            'model': 'product.product',
                            'count': 0,
                            'data': []
                        })
                        _logger.warning(f"⚠️ No products found matching the search criteria")
            
            # Check for sales-related questions
            if any(word in question_lower for word in ['مبيعات', 'بيع', 'sales', 'sale', 'order', 'طلب', 'طلبات']):
                sales = self.env['sale.order'].search_read(
                    [('state', '!=', 'cancel')],
                    [
                        'name', 'partner_id', 'user_id', 'team_id',
                        'amount_untaxed', 'amount_tax', 'amount_total',
                        'state', 'date_order', 'validity_date',
                        'payment_term_id', 'pricelist_id',
                        'order_line', 'invoice_status', 'delivery_status'
                    ],
                    limit=100
                )
                
                # Get order lines for these sales
                if sales:
                    sale_ids = [s['id'] for s in sales]
                    sale_lines = self.env['sale.order.line'].search_read(
                        [('order_id', 'in', sale_ids)],
                        ['order_id', 'product_id', 'product_uom_qty', 'price_unit', 'price_subtotal', 'qty_delivered', 'qty_invoiced'],
                        limit=500
                    )
                    
                    # Attach lines to orders
                    for sale in sales:
                        sale_order_lines = [l for l in sale_lines if l.get('order_id') and l['order_id'][0] == sale['id']]
                        sale['line_items'] = sale_order_lines
                        sale['total_items'] = len(sale_order_lines)
                        sale['total_qty'] = sum([l.get('product_uom_qty', 0) for l in sale_order_lines])
                
                data['records'].append({
                    'model': 'sale.order',
                    'count': len(sales),
                    'data': sales
                })
                _logger.info(f"💰 Collected {len(sales)} sales orders with {len(sale_lines)} line items for AI")
            
            # Check for customer-related questions
            if any(word in question_lower for word in ['عميل', 'عملاء', 'customer', 'customers', 'زبون', 'زبائن']):
                if role in ['admin', 'employee']:
                    customers = self.env['res.partner'].search_read(
                        [('customer_rank', '>', 0)],
                        [
                            'name', 'email', 'phone', 'mobile', 'street', 'street2',
                            'city', 'state_id', 'country_id', 'zip',
                            'customer_rank', 'supplier_rank',
                            'user_id', 'team_id',
                            'property_payment_term_id', 'property_product_pricelist',
                            'credit_limit', 'total_due', 'total_overdue',
                            'sale_order_count', 'sale_order_ids',
                            'invoice_ids', 'payment_token_count'
                        ],
                        limit=100
                    )
                    
                    # Get sales statistics for each customer
                    if customers:
                        customer_ids = [c['id'] for c in customers]
                        customer_sales = self.env['sale.order'].read_group(
                            [('partner_id', 'in', customer_ids), ('state', '!=', 'cancel')],
                            ['partner_id', 'amount_total:sum', 'id:count'],
                            ['partner_id']
                        )
                        
                        # Attach sales stats to customers
                        for customer in customers:
                            cust_stats = next((s for s in customer_sales if s.get('partner_id') and s['partner_id'][0] == customer['id']), None)
                            if cust_stats:
                                customer['total_sales_amount'] = cust_stats.get('amount_total', 0)
                                customer['total_orders'] = cust_stats.get('partner_id_count', 0)
                    
                    data['records'].append({
                        'model': 'res.partner',
                        'count': len(customers),
                        'data': customers
                    })
                    _logger.info(f"👥 Collected {len(customers)} customers with sales statistics for AI")
            
            # Check for invoice-related questions
            if any(word in question_lower for word in ['فاتورة', 'فواتير', 'invoice', 'invoices', 'مدفوع', 'paid', 'مستحق', 'due']):
                invoices = self.env['account.move'].search_read(
                    [('move_type', 'in', ['out_invoice', 'out_refund'])],
                    [
                        'name', 'partner_id', 'move_type',
                        'amount_untaxed', 'amount_tax', 'amount_total', 'amount_residual',
                        'state', 'payment_state', 'invoice_date', 'invoice_date_due',
                        'invoice_origin', 'ref', 'currency_id',
                        'invoice_line_ids', 'payment_id'
                    ],
                    limit=100
                )
                
                # Get invoice lines
                if invoices:
                    invoice_ids = [inv['id'] for inv in invoices]
                    invoice_lines = self.env['account.move.line'].search_read(
                        [
                            ('move_id', 'in', invoice_ids),
                            ('display_type', '=', False)  # Exclude section/note lines
                        ],
                        ['move_id', 'product_id', 'quantity', 'price_unit', 'price_subtotal', 'tax_ids'],
                        limit=500
                    )
                    
                    # Attach lines to invoices
                    for invoice in invoices:
                        inv_lines = [l for l in invoice_lines if l.get('move_id') and l['move_id'][0] == invoice['id']]
                        invoice['line_items'] = inv_lines
                        invoice['total_items'] = len(inv_lines)
                
                data['records'].append({
                    'model': 'account.move',
                    'count': len(invoices),
                    'data': invoices
                })
                _logger.info(f"📄 Collected {len(invoices)} invoices with {len(invoice_lines)} line items for AI")
            
            # Check for employee-related questions
            if role == 'admin' and any(word in question_lower for word in ['موظف', 'موظفين', 'employee', 'employees', 'عامل', 'عمال']):
                try:
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
                    _logger.info(f"👔 Collected {len(employees)} employees for AI")
                except:
                    _logger.warning("HR module not available")
            
            # Check for warehouse/stock questions
            if any(word in question_lower for word in ['مخزن', 'مستودع', 'warehouse', 'stock', 'inventory', 'كميات', 'quantities']):
                try:
                    # Get internal locations (warehouses)
                    stock_locations = self.env['stock.location'].search_read(
                        [('usage', '=', 'internal')],
                        ['name', 'complete_name', 'location_id', 'company_id'],
                        limit=50
                    )
                    
                    # Get stock quantities summary
                    if stock_locations:
                        location_ids = [loc['id'] for loc in stock_locations]
                        quants = self.env['stock.quant'].search_read(
                            [('location_id', 'in', location_ids), ('quantity', '>', 0)],
                            ['product_id', 'location_id', 'quantity', 'available_quantity'],
                            limit=200
                        )
                        
                        # Add quants to locations
                        for location in stock_locations:
                            location_quants = [q for q in quants if q['location_id'][0] == location['id']]
                            location['products_count'] = len(set([q['product_id'][0] for q in location_quants]))
                            location['total_quantity'] = sum([q['quantity'] for q in location_quants])
                    
                    data['records'].append({
                        'model': 'stock.location',
                        'count': len(stock_locations),
                        'data': stock_locations
                    })
                    _logger.info(f"🏭 Collected {len(stock_locations)} stock locations with quantities for AI")
                except Exception as e:
                    _logger.warning(f"Stock module error: {str(e)}")
            
            # If no specific data found, get comprehensive stats
            if not data['records']:
                stats = {
                    'total_products': self.env['product.product'].search_count([('active', '=', True)]),
                    'total_customers': self.env['res.partner'].search_count([('customer_rank', '>', 0)]),
                    'total_sales': self.env['sale.order'].search_count([('state', '!=', 'cancel')]),
                    'total_invoices': self.env['account.move'].search_count([('move_type', 'in', ['out_invoice', 'out_refund'])]),
                }
                
                # Add warehouse count if available
                try:
                    stats['total_warehouses'] = self.env['stock.warehouse'].search_count([])
                    stats['total_locations'] = self.env['stock.location'].search_count([('usage', '=', 'internal')])
                except:
                    pass
                
                data['records'].append({
                    'model': 'system.stats',
                    'count': 1,
                    'data': [stats]
                })
                _logger.info(f"📊 Providing comprehensive stats: {stats}")
        
        except Exception as e:
            _logger.error(f"❌ Error collecting Odoo data: {str(e)}")
            # Return empty data but don't fail
            pass
        
        return data
    
    def _build_prompt(self, question, role, odoo_data):
        """Build enriched prompt with Odoo data"""
        prompt_parts = []
        
        # Check if asking for simple count
        question_lower = question.lower()
        asking_for_count = any(word in question_lower for word in ['كم عدد', 'how many', 'عدد المنتجات', 'number of'])
        
        # Add Odoo data directly
        if odoo_data['records']:
            prompt_parts.append("📊 البيانات المتوفرة من النظام:")
            prompt_parts.append("")
            
            for record_set in odoo_data['records']:
                model_name = record_set['model']
                count = record_set['count']
                data = record_set['data']
                
                prompt_parts.append(f"النموذج: {model_name} | العدد الكلي: {count}")
                
                # Include ALL data (not limited) - formatted clearly
                if data:
                    if model_name == 'product.count':
                        # Simple count response
                        count_data = data[0] if data else {}
                        total = count_data.get('total_products', 0)
                        prompt_parts.append(f"\n📦 إجمالي عدد المنتجات: {total}")
                        prompt_parts.append(f"\n{count_data.get('message', '')}")
                    
                    elif model_name == 'product.product':
                        # Check if we have detailed data
                        has_detailed_data = any('stock_by_location' in p or 'recent_movements' in p for p in data[:5] if p)
                        
                        # Check if this is a search for a specific product
                        is_specific_search = count <= 5
                        
                        # Handle empty results
                        if count == 0:
                            prompt_parts.append("\n⚠️ لم يتم العثور على أي منتج بهذا الاسم أو الكود.")
                            prompt_parts.append("يرجى التحقق من الاسم أو الكود والمحاولة مرة أخرى.")
                        
                        # If just asking for count
                        elif asking_for_count:
                            prompt_parts.append(f"\n📦 إجمالي عدد المنتجات المطابقة: {count}")
                            prompt_parts.append("\nعينة من المنتجات:")
                            for idx, product in enumerate(data[:10], 1):
                                prompt_parts.append(f"{idx}. {product.get('name', 'N/A')} (كود: {product.get('default_code', 'N/A')})")
                            if count > 10:
                                prompt_parts.append(f"\n... و {count - 10} منتجات أخرى")
                        
                        # If specific search (1-5 products), show FULL details
                        elif is_specific_search:
                            prompt_parts.append(f"\n📦 {'وجدت منتج واحد' if count == 1 else f'وجدت {count} منتجات'}:")
                            prompt_parts.append("")
                            
                            for idx, product in enumerate(data, 1):
                                # Product header
                                if count > 1:
                                    prompt_parts.append(f"\n{'='*70}")
                                    prompt_parts.append(f"المنتج #{idx}: {product.get('name', 'غير محدد')}")
                                    prompt_parts.append(f"{'='*70}")
                                else:
                                    prompt_parts.append(f"المنتج: {product.get('name', 'غير محدد')}")
                                    prompt_parts.append(f"{'='*70}")
                                
                                # الكود والباركود
                                prompt_parts.append("")
                                prompt_parts.append("🏷️ التعريف:")
                                if product.get('default_code'):
                                    prompt_parts.append(f"  • كود المنتج: {product['default_code']}")
                                else:
                                    prompt_parts.append(f"  • كود المنتج: غير محدد")
                                
                                if product.get('barcode'):
                                    prompt_parts.append(f"  • الباركود: {product['barcode']}")
                                
                                # الفئة
                                if product.get('categ_id'):
                                    cat_name = product['categ_id'][1] if isinstance(product['categ_id'], (list, tuple)) else str(product['categ_id'])
                                    prompt_parts.append(f"  • الفئة: {cat_name}")
                                
                                # الأسعار
                                prompt_parts.append("")
                                prompt_parts.append("💰 الأسعار:")
                                prompt_parts.append(f"  • سعر البيع: {product.get('list_price', 0)}")
                                if product.get('standard_price'):
                                    prompt_parts.append(f"  • التكلفة: {product.get('standard_price', 0)}")
                                
                                # وحدة القياس
                                if product.get('uom_id'):
                                    uom = product['uom_id'][1] if isinstance(product['uom_id'], (list, tuple)) else str(product['uom_id'])
                                    prompt_parts.append(f"  • وحدة القياس: {uom}")
                                    prompt_parts.append(f"  • السعر لكل {uom}: {product.get('list_price', 0)}")
                                
                                # الكميات
                                prompt_parts.append("")
                                prompt_parts.append("📊 المخزون:")
                                prompt_parts.append(f"  • الكمية المتوفرة: {product.get('qty_available', 0)}")
                                
                                if product.get('virtual_available') is not None:
                                    prompt_parts.append(f"  • الكمية المتوقعة: {product.get('virtual_available', 0)}")
                                
                                # توزيع الكميات في المخازن
                                if 'stock_by_location' in product and product['stock_by_location']:
                                    prompt_parts.append("")
                                    prompt_parts.append(f"🏭 توزيع الكميات في المخازن ({product.get('total_locations', 0)} مخزن):")
                                    for quant in product['stock_by_location']:
                                        loc_name = quant.get('location_id', ['', 'مخزن'])[1] if isinstance(quant.get('location_id'), (list, tuple)) else 'مخزن'
                                        qty = quant.get('quantity', 0)
                                        available = quant.get('available_quantity', 0)
                                        prompt_parts.append(f"  • {loc_name}:")
                                        prompt_parts.append(f"    - الكمية: {qty}")
                                        prompt_parts.append(f"    - المتاح: {available}")
                        
                        # Many products - show list
                        else:
                            prompt_parts.append(f"\n📦 وجدت {count} منتج:")
                            prompt_parts.append("")
                            for idx, product in enumerate(data[:20], 1):
                                name = product.get('name', 'غير محدد')
                                code = product.get('default_code', 'N/A')
                                price = product.get('list_price', 0)
                                qty = product.get('qty_available', 0)
                                uom = product.get('uom_id', ['', 'وحدة'])[1] if isinstance(product.get('uom_id'), (list, tuple)) else 'وحدة'
                                
                                prompt_parts.append(f"{idx}. {name}")
                                prompt_parts.append(f"   كود: {code} | سعر: {price} | كمية: {qty} {uom}")
                                prompt_parts.append("")
                            
                            if count > 20:
                                prompt_parts.append(f"... و {count - 20} منتج آخر")
                    
                    elif model_name == 'sale.order':
                        prompt_parts.append("\n💼 تفاصيل طلبات المبيعات:")
                        for idx, sale in enumerate(data[:30], 1):
                            prompt_parts.append(f"\n{idx}. طلب رقم: {sale.get('name', 'N/A')}")
                            
                            # Customer
                            customer = sale.get('partner_id', ['', 'غير معروف'])[1] if isinstance(sale.get('partner_id'), (list, tuple)) else 'غير معروف'
                            prompt_parts.append(f"  • العميل: {customer}")
                            
                            # Amounts
                            prompt_parts.append(f"  • المبلغ (قبل الضريبة): {sale.get('amount_untaxed', 0)}")
                            prompt_parts.append(f"  • الضريبة: {sale.get('amount_tax', 0)}")
                            prompt_parts.append(f"  • الإجمالي: {sale.get('amount_total', 0)}")
                            
                            # Status
                            prompt_parts.append(f"  • الحالة: {sale.get('state', 'N/A')}")
                            prompt_parts.append(f"  • حالة الفاتورة: {sale.get('invoice_status', 'N/A')}")
                            
                            # Date
                            if sale.get('date_order'):
                                prompt_parts.append(f"  • التاريخ: {sale['date_order'][:10]}")
                            
                            # Items
                            if 'line_items' in sale and sale['line_items']:
                                prompt_parts.append(f"  • عدد الأصناف: {sale.get('total_items', 0)}")
                                prompt_parts.append(f"  • الكمية الكلية: {sale.get('total_qty', 0)}")
                                prompt_parts.append("  • الأصناف:")
                                for line in sale['line_items'][:5]:  # Show first 5 items
                                    prod_name = line.get('product_id', ['', 'غير معروف'])[1] if isinstance(line.get('product_id'), (list, tuple)) else 'غير معروف'
                                    qty = line.get('product_uom_qty', 0)
                                    price = line.get('price_unit', 0)
                                    prompt_parts.append(f"    - {prod_name}: {qty} × {price}")
                    
                    elif model_name == 'res.partner':
                        prompt_parts.append("\n👥 تفاصيل العملاء:")
                        for idx, customer in enumerate(data[:30], 1):
                            prompt_parts.append(f"\n{idx}. {customer.get('name', 'N/A')}")
                            
                            # Contact Info
                            if customer.get('email'):
                                prompt_parts.append(f"  • البريد: {customer['email']}")
                            if customer.get('phone'):
                                prompt_parts.append(f"  • الهاتف: {customer['phone']}")
                            if customer.get('mobile'):
                                prompt_parts.append(f"  • الجوال: {customer['mobile']}")
                            
                            # Address
                            address_parts = []
                            if customer.get('street'):
                                address_parts.append(customer['street'])
                            if customer.get('city'):
                                address_parts.append(customer['city'])
                            if address_parts:
                                prompt_parts.append(f"  • العنوان: {', '.join(address_parts)}")
                            
                            # Sales Statistics
                            if 'total_sales_amount' in customer:
                                prompt_parts.append(f"  • إجمالي المبيعات: {customer['total_sales_amount']}")
                                prompt_parts.append(f"  • عدد الطلبات: {customer.get('total_orders', 0)}")
                            
                            # Credit
                            if customer.get('credit_limit'):
                                prompt_parts.append(f"  • حد الائتمان: {customer['credit_limit']}")
                    
                    elif model_name == 'stock.location':
                        prompt_parts.append("\n🏭 تفاصيل المخازن:")
                        for idx, location in enumerate(data[:30], 1):
                            prompt_parts.append(f"\n{idx}. {location.get('complete_name', location.get('name', 'N/A'))}")
                            if 'products_count' in location:
                                prompt_parts.append(f"   - عدد المنتجات: {location['products_count']}")
                                prompt_parts.append(f"   - الكمية الإجمالية: {location['total_quantity']}")
                    
                    elif model_name == 'account.move':
                        prompt_parts.append("\n📄 تفاصيل الفواتير:")
                        for idx, invoice in enumerate(data[:30], 1):
                            inv_type = 'فاتورة' if invoice.get('move_type') == 'out_invoice' else 'إشعار دائن'
                            prompt_parts.append(f"\n{idx}. {inv_type}: {invoice.get('name', 'N/A')}")
                            
                            customer = invoice.get('partner_id', ['', 'غير معروف'])[1] if isinstance(invoice.get('partner_id'), (list, tuple)) else 'غير معروف'
                            prompt_parts.append(f"  • العميل: {customer}")
                            
                            # Amounts
                            prompt_parts.append(f"  • المبلغ (قبل الضريبة): {invoice.get('amount_untaxed', 0)}")
                            prompt_parts.append(f"  • الضريبة: {invoice.get('amount_tax', 0)}")
                            prompt_parts.append(f"  • الإجمالي: {invoice.get('amount_total', 0)}")
                            prompt_parts.append(f"  • المتبقي (غير مدفوع): {invoice.get('amount_residual', 0)}")
                            
                            # Status
                            prompt_parts.append(f"  • حالة الفاتورة: {invoice.get('state', 'N/A')}")
                            prompt_parts.append(f"  • حالة الدفع: {invoice.get('payment_state', 'N/A')}")
                            
                            # Dates
                            if invoice.get('invoice_date'):
                                prompt_parts.append(f"  • تاريخ الإصدار: {invoice['invoice_date']}")
                            if invoice.get('invoice_date_due'):
                                prompt_parts.append(f"  • تاريخ الاستحقاق: {invoice['invoice_date_due']}")
                            
                            # Items
                            if 'line_items' in invoice and invoice['line_items']:
                                prompt_parts.append(f"  • عدد الأصناف: {invoice.get('total_items', 0)}")
                                prompt_parts.append("  • الأصناف:")
                                for line in invoice['line_items'][:5]:
                                    prod_name = line.get('product_id', ['', 'صنف'])[1] if isinstance(line.get('product_id'), (list, tuple)) else 'صنف'
                                    qty = line.get('quantity', 0)
                                    price = line.get('price_unit', 0)
                                    subtotal = line.get('price_subtotal', 0)
                                    prompt_parts.append(f"    - {prod_name}: {qty} × {price} = {subtotal}")
                    
                    elif model_name == 'stock.location':
                        prompt_parts.append("\n🏭 تفاصيل المخازن:")
                        for idx, location in enumerate(data[:30], 1):
                            prompt_parts.append(f"\n{idx}. {location.get('complete_name', location.get('name', 'N/A'))}")
                            if 'products_count' in location:
                                prompt_parts.append(f"   - عدد المنتجات: {location['products_count']}")
                                prompt_parts.append(f"   - الكمية الإجمالية: {location['total_quantity']}")
                    
                    else:
                        # For other models, show formatted data
                        prompt_parts.append(json.dumps(data[:20], ensure_ascii=False, indent=2, default=json_serial))
        else:
            # No specific data found - this is a general conversation
            prompt_parts.append("📊 البيانات المتوفرة من النظام:")
            prompt_parts.append("")
            prompt_parts.append("النموذج: system.stats | العدد الكلي: إحصائيات عامة")
            prompt_parts.append("")
            prompt_parts.append("⚠️ ملاحظة: لم يتم العثور على بيانات محددة لهذا السؤال.")
            prompt_parts.append("يبدو أن هذا سؤال عام أو محادثة عادية.")
        
        # Add the actual question
        prompt_parts.append("")
        prompt_parts.append("=" * 50)
        prompt_parts.append(f"❓ السؤال: {question}")
        prompt_parts.append("=" * 50)
        prompt_parts.append("")
        prompt_parts.append("✅ تعليمات الإجابة:")
        prompt_parts.append("")
        
        # Check if this looks like specific product search
        has_product_data = any(r.get('model') in ['product.product', 'product.count'] for r in odoo_data.get('records', []))
        product_count = next((r.get('count', 0) for r in odoo_data.get('records', []) if r.get('model') == 'product.product'), 0)
        
        if has_product_data and product_count <= 5 and product_count > 0:
            # Specific product search - give detailed instructions
            prompt_parts.append("⚠️ هذا سؤال محدد عن منتج أو منتجات معينة:")
            prompt_parts.append("1. اعرض جميع التفاصيل المتوفرة عن المنتج/المنتجات")
            prompt_parts.append("2. اذكر: الاسم، الكود، السعر، الكمية، والمخازن (إن وجدت)")
            prompt_parts.append("3. إذا كان المنتج واحد فقط، اعرض كل تفاصيله بشكل مفصل")
            prompt_parts.append("4. رتب المعلومات بشكل واضح ومنظم")
        elif has_product_data and product_count == 0:
            prompt_parts.append("⚠️ لم يتم العثور على المنتج المطلوب:")
            prompt_parts.append("1. أخبر المستخدم أنه لم يتم العثور على منتج بهذا الاسم أو الكود")
            prompt_parts.append("2. اقترح التحقق من الاسم أو الكود")
            prompt_parts.append("3. يمكنك اقتراح طلب قائمة بالمنتجات المتوفرة")
        else:
            # General instructions
            prompt_parts.append("1. إذا كانت البيانات متوفرة، أجب بناءً عليها فقط")
            prompt_parts.append("2. إذا لم تكن البيانات متوفرة:")
            prompt_parts.append("   - إذا كان السؤال تحية أو محادثة عامة، رد بشكل ودي ومهذب")
            prompt_parts.append("   - إذا كان السؤال يطلب معلومات محددة، قدم ما لديك أو اطلب توضيح")
            prompt_parts.append("   - إذا كان السؤال عن دعم أو مساعدة، قدم المساعدة المناسبة")
        
        prompt_parts.append("")
        prompt_parts.append("📌 قواعد عامة:")
        prompt_parts.append("- أجب بنفس لغة السؤال (عربي/إنجليزي)")
        prompt_parts.append("- كن واضحاً ومحدداً ومفيداً")
        prompt_parts.append("- لا تذكر 'قاعدة البيانات' أو 'Odoo' - تحدث بشكل طبيعي")
        
        final_prompt = "\n".join(prompt_parts)
        _logger.info(f"📝 Built prompt with {len(final_prompt)} characters, {len(final_prompt.split())} words")
        _logger.info(f"📋 Prompt preview (first 500 chars): {final_prompt[:500]}")
        
        return final_prompt
    
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
            _logger.info(f"🔍 Collecting data for question: {question[:100]}")
            odoo_data = self._collect_odoo_data(question, role)
            _logger.info(f"📊 Data collected: {len(odoo_data.get('records', []))} record sets")
            
            # Call Gemini API
            import google.generativeai as genai
            genai.configure(api_key=config.gemini_api_key)
            
            # Build system instruction
            system_instruction = config.system_prompt if config.system_prompt else """
أنت Lugal AI - مساعد ذكي متخصص في نظام Odoo.

🎯 دورك الأساسي:
- مساعدة المستخدمين في الحصول على معلومات من نظام Odoo
- الرد على الأسئلة عن المنتجات، المبيعات، العملاء، والفواتير
- التفاعل بشكل ودي ومهني مع المستخدمين

✅ قواعد الإجابة:
- رد على التحيات بشكل ودي (مثل: "وعليكم السلام! كيف يمكنني مساعدتك؟")
- إذا كانت البيانات متوفرة، استخدمها في الإجابة
- إذا لم تكن البيانات متوفرة، قدم مساعدة عامة
- كن محترفاً ومفيداً دائماً
- أجب بنفس لغة السؤال (عربي أو إنجليزي)

🚫 ممنوع:
- ذكر "قاعدة البيانات" أو "النظام" أو "Odoo"
- اختراع أرقام أو بيانات غير موجودة
- الرد بطريقة غير ودية أو جافة
"""
            
            model = genai.GenerativeModel(
                config.gemini_model or 'gemini-2.0-flash-exp',
                system_instruction=system_instruction
            )
            
            # Build enriched prompt with data
            enriched_prompt = self._build_prompt(question, role, odoo_data)
            
            # Generate response
            _logger.info(f"🤖 Sending to Gemini API...")
            response = model.generate_content(enriched_prompt)
            answer = response.text
            _logger.info(f"✅ Got response from Gemini: {len(answer)} characters")
            
            # Calculate response time
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Determine category from data used
            category = self._determine_category(odoo_data)
            
            # Update conversation
            models_used = ', '.join([r['model'] for r in odoo_data['records']]) if odoo_data['records'] else None
            records_count = sum([r['count'] for r in odoo_data['records']]) if odoo_data['records'] else 0
            
            _logger.info(f"💾 Saving conversation: category={category}, models={models_used}, records={records_count}")
            
            conversation.write({
                'answer': answer,
                'response_time_ms': response_time,
                'category': category,
                'context_data': json.dumps(odoo_data, ensure_ascii=False, default=json_serial),
                'data_models_used': models_used,
                'records_count': records_count
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


