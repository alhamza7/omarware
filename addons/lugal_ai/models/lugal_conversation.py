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
                'اعرض', 'display', 'list', 'قائمة', 'ابحث', 'search'
            ]
            
            # Check if question is too short or generic (1-2 words only with no context)
            question_words = question_lower.split()
            is_too_generic = len(question_words) <= 2 and not any(keyword in question_lower for keyword in specific_product_keywords)
            
            # Extract potential product names (3+ chars that aren't common words)
            common_words = [
                'منتج', 'منتجات', 'product', 'products',
                'في', 'كل', 'the', 'in', 'على', 'عن', 'من', 'إلى', 
                'هل', 'ما', 'ماذا', 'كيف', 'أين', 'لماذا',
                'تعرف', 'لدينا', 'لدينا؟', 'عندنا', 'عندك',
                'موجود', 'موجودة', 'have', 'has', 'know',
                'كم', 'how', 'many', 'much', 'عدد', 'number',
                'ممكن', 'اريد', 'want', 'need', 'يرجى', 'please'
            ]
            potential_product_names = []
            for word in question_words:
                if len(word) > 2 and word not in common_words:
                    potential_product_names.append(word)
            
            # Only trigger if we have specific product keywords OR a product name
            is_product_question = any(word in question_lower for word in product_keywords)
            has_specific_intent = any(word in question_lower for word in specific_product_keywords)
            
            # Filter out if too generic AND no specific intent
            if is_too_generic and not has_specific_intent and len(potential_product_names) <= 1:
                is_product_question = False
                _logger.info(f"⚠️ Question too generic, treating as general conversation")
            
            # Only search if it's clearly a product question
            if is_product_question:
                is_product_question = has_specific_intent or len(potential_product_names) > 0
            
            _logger.info(f"🛍️ Is product question: {is_product_question}, has_intent: {has_specific_intent}, potential_products: {potential_product_names}")
            
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
                    
                    # Only search for specific products if we have actual product names
                    if specific_product_names:
                        # Specific product search
                        product_domain = ['|', '|',
                            ('name', 'ilike', ' '.join(specific_product_names)),
                            ('default_code', 'ilike', ' '.join(specific_product_names)),
                            ('active', '=', True)
                        ]
                        _logger.info(f"🔎 Searching for specific products: {' '.join(specific_product_names)}")
                    else:
                        # General product question - get sample of products
                        _logger.info(f"🔎 General product question - getting product sample")
                    
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
                    
                    data['records'].append({
                        'model': 'product.product',
                        'count': len(products),
                        'data': products
                    })
                    _logger.info(f"📦 Collected {len(products)} products with stock details for AI")
            
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
                        # Check if we have detailed data or just basic
                        has_detailed_data = any('stock_by_location' in p or 'recent_movements' in p for p in data[:5])
                        
                        # If just asking for count, show minimal info
                        if asking_for_count:
                            prompt_parts.append(f"\n📦 إجمالي عدد المنتجات: {count}")
                            prompt_parts.append("\nعينة من المنتجات (أول 10):")
                            for idx, product in enumerate(data[:10], 1):
                                prompt_parts.append(f"{idx}. {product.get('name', 'N/A')} (كود: {product.get('default_code', 'N/A')})")
                            if count > 10:
                                prompt_parts.append(f"\n... و {count - 10} منتجات أخرى")
                        elif has_detailed_data:
                            prompt_parts.append("\n📦 تفاصيل المنتجات الكاملة:")
                            for idx, product in enumerate(data[:50], 1):  # Show up to 50 products
                                prompt_parts.append(f"\n{'='*60}")
                                prompt_parts.append(f"المنتج #{idx}: {product.get('name', 'N/A')}")
                                prompt_parts.append(f"{'='*60}")
                        else:
                            # Simplified view for basic data
                            prompt_parts.append("\n📦 معلومات المنتجات:")
                            for idx, product in enumerate(data[:50], 1):  # Show up to 50 products
                                prompt_parts.append(f"\n{idx}. {product.get('name', 'N/A')}")
                            # Skip all details if just asking for count
                            if asking_for_count:
                                continue
                            
                            # Basic Info - only if detailed view
                            if has_detailed_data:
                                prompt_parts.append("\n🏷️ معلومات أساسية:")
                                prompt_parts.append(f"  • الكود: {product.get('default_code', 'غير محدد')}")
                                prompt_parts.append(f"  • الباركود: {product.get('barcode', 'غير محدد')}")
                                prompt_parts.append(f"  • النوع: {product.get('type', 'N/A')}")
                                prompt_parts.append(f"  • الحالة: {'نشط' if product.get('active') else 'غير نشط'}")
                            else:
                                # Simplified info
                                if product.get('default_code'):
                                    prompt_parts.append(f"   الكود: {product['default_code']}")
                                if product.get('barcode'):
                                    prompt_parts.append(f"   الباركود: {product['barcode']}")
                            
                            # Category - show in both views
                            if product.get('categ_id'):
                                cat_name = product['categ_id'][1] if isinstance(product['categ_id'], (list, tuple)) else str(product['categ_id'])
                                if has_detailed_data:
                                    prompt_parts.append(f"  • الفئة: {cat_name}")
                                else:
                                    prompt_parts.append(f"   الفئة: {cat_name}")
                            
                            # Pricing
                            if has_detailed_data:
                                prompt_parts.append("\n💰 الأسعار:")
                                prompt_parts.append(f"  • سعر البيع: {product.get('list_price', 0)}")
                                prompt_parts.append(f"  • التكلفة: {product.get('standard_price', 0)}")
                                if product.get('currency_id'):
                                    curr = product['currency_id'][1] if isinstance(product['currency_id'], (list, tuple)) else ''
                                    prompt_parts.append(f"  • العملة: {curr}")
                            else:
                                # Simplified pricing
                                prompt_parts.append(f"   السعر: {product.get('list_price', 0)}")
                            
                            # Stock Quantities
                            if has_detailed_data:
                                prompt_parts.append("\n📊 الكميات:")
                                prompt_parts.append(f"  • المتوفر حالياً: {product.get('qty_available', 0)}")
                                if product.get('virtual_available') is not None:
                                    prompt_parts.append(f"  • المتوقع (مع الطلبات): {product.get('virtual_available', 0)}")
                                if product.get('incoming_qty'):
                                    prompt_parts.append(f"  • الوارد: {product.get('incoming_qty', 0)}")
                                if product.get('outgoing_qty'):
                                    prompt_parts.append(f"  • الصادر: {product.get('outgoing_qty', 0)}")
                            else:
                                # Simplified stock
                                prompt_parts.append(f"   الكمية المتوفرة: {product.get('qty_available', 0)}")
                            
                            # Units
                            if product.get('uom_id'):
                                uom_name = product['uom_id'][1] if isinstance(product['uom_id'], (list, tuple)) else ''
                                if has_detailed_data:
                                    prompt_parts.append(f"  • وحدة القياس: {uom_name}")
                                else:
                                    prompt_parts.append(f"   الوحدة: {uom_name}")
                            
                            # Stock by Location (detailed) - only in detailed view
                            if has_detailed_data and 'stock_by_location' in product and product['stock_by_location']:
                                prompt_parts.append(f"\n🏭 توزيع الكميات في المخازن ({product.get('total_locations', 0)} مخزن):")
                                for quant in product['stock_by_location']:
                                    loc_name = quant.get('location_id', ['', 'موقع غير معروف'])[1] if isinstance(quant.get('location_id'), (list, tuple)) else 'موقع غير معروف'
                                    qty = quant.get('quantity', 0)
                                    reserved = quant.get('reserved_quantity', 0)
                                    available = quant.get('available_quantity', 0)
                                    lot = quant.get('lot_id', ['', ''])[1] if quant.get('lot_id') else 'بدون رقم تسلسلي'
                                    
                                    prompt_parts.append(f"  • {loc_name}:")
                                    prompt_parts.append(f"    - الكمية الكلية: {qty}")
                                    prompt_parts.append(f"    - محجوز: {reserved}")
                                    prompt_parts.append(f"    - متاح: {available}")
                                    if lot != 'بدون رقم تسلسلي':
                                        prompt_parts.append(f"    - الرقم التسلسلي: {lot}")
                            
                            # Suppliers - only in detailed view
                            if has_detailed_data and 'suppliers' in product and product['suppliers']:
                                prompt_parts.append(f"\n🏪 الموردين ({len(product['suppliers'])} مورد):")
                                for supplier in product['suppliers'][:5]:  # Show top 5
                                    supp_name = supplier.get('partner_id', ['', 'غير معروف'])[1] if isinstance(supplier.get('partner_id'), (list, tuple)) else 'غير معروف'
                                    price = supplier.get('price', 0)
                                    min_qty = supplier.get('min_qty', 1)
                                    delay = supplier.get('delay', 0)
                                    prompt_parts.append(f"  • {supp_name}:")
                                    prompt_parts.append(f"    - السعر: {price}")
                                    prompt_parts.append(f"    - الحد الأدنى للطلب: {min_qty}")
                                    prompt_parts.append(f"    - مدة التوصيل: {delay} يوم")
                            
                            # Recent Movements - only in detailed view
                            if has_detailed_data and 'recent_movements' in product and product['recent_movements']:
                                prompt_parts.append(f"\n📦 آخر الحركات ({len(product['recent_movements'])} حركة):")
                                for move in product['recent_movements'][:5]:  # Show last 5
                                    date = move.get('date', '')[:10] if move.get('date') else ''
                                    qty = move.get('product_uom_qty', 0)
                                    origin = move.get('origin', '') or move.get('reference', 'غير محدد')
                                    from_loc = move.get('location_id', ['', ''])[1] if isinstance(move.get('location_id'), (list, tuple)) else ''
                                    to_loc = move.get('location_dest_id', ['', ''])[1] if isinstance(move.get('location_dest_id'), (list, tuple)) else ''
                                    
                                    prompt_parts.append(f"  • {date}: {qty} من {from_loc} → {to_loc}")
                                    if origin and origin != 'غير محدد':
                                        prompt_parts.append(f"    المرجع: {origin}")
                            
                            # Recent Sales - only in detailed view
                            if has_detailed_data and 'recent_sales' in product and product['recent_sales']:
                                total_qty = product.get('total_sales_qty', 0)
                                total_amount = product.get('total_sales_amount', 0)
                                prompt_parts.append(f"\n💰 المبيعات الأخيرة ({len(product['recent_sales'])} عملية):")
                                prompt_parts.append(f"  • الكمية المباعة: {total_qty}")
                                prompt_parts.append(f"  • قيمة المبيعات: {total_amount}")
                                
                                for sale in product['recent_sales'][:5]:  # Show last 5
                                    customer = sale.get('order_partner_id', ['', 'غير معروف'])[1] if isinstance(sale.get('order_partner_id'), (list, tuple)) else 'غير معروف'
                                    qty = sale.get('product_uom_qty', 0)
                                    price = sale.get('price_unit', 0)
                                    subtotal = sale.get('price_subtotal', 0)
                                    prompt_parts.append(f"  • {customer}: {qty} × {price} = {subtotal}")
                            
                            # Description - only in detailed view
                            if has_detailed_data:
                                if product.get('description_sale'):
                                    prompt_parts.append(f"\n📝 الوصف: {product['description_sale'][:200]}")
                                
                                # Tracking
                                if product.get('tracking') and product['tracking'] != 'none':
                                    prompt_parts.append(f"\n🔍 التتبع: {product['tracking']}")
                                
                                # Weight & Volume
                                if product.get('weight') or product.get('volume'):
                                    prompt_parts.append("\n📏 الأبعاد:")
                                    if product.get('weight'):
                                        prompt_parts.append(f"  • الوزن: {product['weight']}")
                                    if product.get('volume'):
                                        prompt_parts.append(f"  • الحجم: {product['volume']}")
                        
                        _logger.info(f"📍 Product {product['name']}: {len(product.get('stock_by_location', []))} locations, {len(product.get('recent_movements', []))} movements, {len(product.get('suppliers', []))} suppliers, {len(product.get('recent_sales', []))} sales")
                    
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
        prompt_parts.append("1. إذا كانت البيانات متوفرة، أجب بناءً عليها فقط")
        prompt_parts.append("2. إذا لم تكن البيانات متوفرة:")
        prompt_parts.append("   - إذا كان السؤال تحية أو محادثة عامة، رد بشكل ودي ومهذب")
        prompt_parts.append("   - إذا كان السؤال يطلب معلومات محددة، اذكر أنك بحاجة لمزيد من التفاصيل")
        prompt_parts.append("   - إذا كان السؤال عن دعم أو مساعدة، قدم المساعدة المناسبة")
        prompt_parts.append("3. أجب بنفس لغة السؤال (عربي/إنجليزي)")
        prompt_parts.append("4. كن ودوداً ومحترفاً ومفيداً")
        prompt_parts.append("5. أنت مساعد ذكي لنظام Odoo - يمكنك المساعدة في:")
        prompt_parts.append("   - معلومات عن المنتجات والمخزون")
        prompt_parts.append("   - معلومات عن المبيعات والعملاء")
        prompt_parts.append("   - معلومات عن الفواتير والطلبات")
        prompt_parts.append("   - الرد على الاستفسارات العامة والتحيات")
        
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


