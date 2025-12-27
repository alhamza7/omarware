# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import logging
import time

_logger = logging.getLogger(__name__)


class GeminiAPIController(http.Controller):
    
    @http.route('/lugal/api/ask', type='json', auth='user', methods=['POST'], csrf=False)
    def ask_question(self, question, context=None, **kwargs):
        """
        Main API endpoint for asking questions to Lugal AI
        
        Input:
        {
            "question": "User's question",
            "context": "Optional additional context"
        }
        
        Output:
        {
            "success": true/false,
            "answer": "AI response",
            "category": "question category",
            "was_cached": true/false,
            "response_time_ms": 123,
            "conversation_id": 123
        }
        """
        start_time = time.time()
        
        try:
            # Get user and role
            user = request.env.user
            permission_model = request.env['lugal.permission']
            user_role = permission_model.get_user_role(user)
            
            # Get configuration
            config = request.env['lugal.config'].get_active_config()
            
            # Check cache first (if enabled)
            cached_answer = None
            was_cached = False
            
            if config.enable_caching:
                cache_model = request.env['lugal.cache']
                cached_answer = cache_model.get_cached_response(question, user_role, context)
                
                if cached_answer:
                    was_cached = True
                    response_time_ms = (time.time() - start_time) * 1000
                    
                    # Log conversation
                    conversation = request.env['lugal.conversation'].create({
                        'user_id': user.id,
                        'question': question,
                        'answer': cached_answer,
                        'user_role': user_role,
                        'status': 'cached',
                        'was_cached': True,
                        'response_time_ms': response_time_ms,
                    })
                    
                    return {
                        'success': True,
                        'answer': cached_answer,
                        'was_cached': True,
                        'response_time_ms': response_time_ms,
                        'conversation_id': conversation.id,
                    }
            
            # Check question index (if enabled)
            matched_pattern = None
            similarity_score = 0.0
            category = None
            
            if config.enable_question_indexing:
                question_index_model = request.env['lugal.question.index']
                matched_pattern, similarity_score = question_index_model.find_matching_pattern(question)
                
                if matched_pattern:
                    category = matched_pattern.category
                    _logger.info(f"Question matched pattern: {matched_pattern.question_pattern} (similarity: {similarity_score:.2%})")
                else:
                    # Classify question dynamically
                    category = question_index_model.classify_question(question)
            
            # Retrieve relevant data from Odoo
            data = self._retrieve_odoo_data(question, category, user_role, matched_pattern)
            
            # Build request for Gemini
            gemini_request = self._build_gemini_request(question, user_role, category, data, context, config)
            
            # Call Gemini API
            gemini_response = self._call_gemini_api(gemini_request, config)
            
            if not gemini_response.get('success'):
                raise Exception(gemini_response.get('error', 'Unknown error from Gemini API'))
            
            answer = gemini_response.get('answer', '')
            input_tokens = gemini_response.get('input_tokens', 0)
            output_tokens = gemini_response.get('output_tokens', 0)
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Store in cache (if enabled)
            if config.enable_caching and answer:
                request.env['lugal.cache'].set_cached_response(
                    question=question,
                    role=user_role,
                    answer=answer,
                    category=category,
                    context_data=json.dumps(context) if context else None,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cache_duration_hours=config.cache_duration_hours,
                )
            
            # Log conversation
            conversation = request.env['lugal.conversation'].create({
                'user_id': user.id,
                'question': question,
                'answer': answer,
                'category': category,
                'question_index_id': matched_pattern.id if matched_pattern else False,
                'similarity_score': similarity_score * 100 if matched_pattern else 0,
                'user_role': user_role,
                'response_time_ms': response_time_ms,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'context_data': json.dumps(data) if data else None,
                'status': 'success',
                'was_cached': False,
            })
            
            return {
                'success': True,
                'answer': answer,
                'category': category,
                'was_cached': False,
                'response_time_ms': response_time_ms,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'conversation_id': conversation.id,
            }
            
        except Exception as e:
            _logger.error(f"Error in ask_question: {str(e)}", exc_info=True)
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Log failed conversation
            request.env['lugal.conversation'].create({
                'user_id': request.env.user.id,
                'question': question,
                'user_role': user_role if 'user_role' in locals() else 'customer',
                'status': 'failed',
                'error_message': str(e),
                'response_time_ms': response_time_ms,
            })
            
            return {
                'success': False,
                'error': str(e),
                'response_time_ms': response_time_ms,
            }
    
    def _retrieve_odoo_data(self, question, category, user_role, matched_pattern=None):
        """Retrieve relevant data from Odoo based on question category"""
        data = {'records': [], 'source': 'odoo'}
        
        try:
            permission_model = request.env['lugal.permission']
            data_scope = permission_model.get_data_scope(request.env.user)
            max_records = data_scope.get('max_records', 100)
            
            # Product queries
            if category == 'product':
                if not permission_model.check_permission(request.env.user, 'can_access_products'):
                    return {'error': 'Access denied to product data'}
                
                products = request.env['product.product'].search([], limit=max_records)
                data['records'] = [{
                    'name': p.name,
                    'price': p.list_price,
                    'qty_available': p.qty_available,
                    'uom': p.uom_id.name,
                    'default_code': p.default_code,
                } for p in products]
                data['model'] = 'product.product'
            
            # Sales queries
            elif category == 'sales':
                if not permission_model.check_permission(request.env.user, 'can_access_sales'):
                    return {'error': 'Access denied to sales data'}
                
                domain = []
                if data_scope.get('own_data_only'):
                    domain.append(('user_id', '=', request.env.user.id))
                
                orders = request.env['sale.order'].search(domain, limit=max_records, order='date_order desc')
                data['records'] = [{
                    'name': o.name,
                    'partner': o.partner_id.name,
                    'date': o.date_order.strftime('%Y-%m-%d') if o.date_order else '',
                    'amount_total': o.amount_total,
                    'state': o.state,
                } for o in orders]
                data['model'] = 'sale.order'
            
            # Customer queries
            elif category == 'customer':
                if not permission_model.check_permission(request.env.user, 'can_access_customers'):
                    return {'error': 'Access denied to customer data'}
                
                partners = request.env['res.partner'].search([('customer_rank', '>', 0)], limit=max_records)
                data['records'] = [{
                    'name': p.name,
                    'email': p.email,
                    'phone': p.phone,
                    'city': p.city,
                    'country': p.country_id.name if p.country_id else '',
                } for p in partners]
                data['model'] = 'res.partner'
            
            # Employee queries
            elif category == 'employee':
                if not permission_model.check_permission(request.env.user, 'can_access_employees'):
                    return {'error': 'Access denied to employee data'}
                
                employees = request.env['hr.employee'].search([], limit=max_records)
                data['records'] = [{
                    'name': e.name,
                    'job_title': e.job_title,
                    'department': e.department_id.name if e.department_id else '',
                    'work_email': e.work_email,
                } for e in employees]
                data['model'] = 'hr.employee'
            
        except Exception as e:
            _logger.error(f"Error retrieving Odoo data: {str(e)}")
            data['error'] = str(e)
        
        return data
    
    def _build_gemini_request(self, question, user_role, category, data, context, config):
        """Build structured request for Gemini"""
        return {
            'role': user_role,
            'question': question,
            'context': context or '',
            'category': category,
            'data': data,
        }
    
    def _call_gemini_api(self, request_data, config):
        """Call Gemini API with given request"""
        try:
            import google.generativeai as genai
            
            # Configure Gemini
            genai.configure(api_key=config.gemini_api_key)
            
            # Build prompt
            system_prompt = config.system_prompt
            user_prompt = json.dumps(request_data, ensure_ascii=False, indent=2)
            
            # Create model
            model = genai.GenerativeModel(
                model_name=config.gemini_model,
                generation_config={
                    'temperature': config.temperature,
                    'max_output_tokens': config.max_output_tokens,
                }
            )
            
            # Generate response
            full_prompt = f"{system_prompt}\n\nUser Request:\n{user_prompt}"
            response = model.generate_content(full_prompt)
            
            if not response or not response.text:
                raise Exception("Empty response from Gemini")
            
            # Extract token usage (if available)
            input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0) if hasattr(response, 'usage_metadata') else 0
            output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0) if hasattr(response, 'usage_metadata') else 0
            
            return {
                'success': True,
                'answer': response.text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
            }
            
        except Exception as e:
            _logger.error(f"Error calling Gemini API: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
            }
    
    @http.route('/lugal/api/rate', type='json', auth='user', methods=['POST'], csrf=False)
    def rate_conversation(self, conversation_id, rating, feedback=None, **kwargs):
        """Rate a conversation"""
        try:
            conversation = request.env['lugal.conversation'].browse(conversation_id)
            
            if not conversation.exists():
                return {'success': False, 'error': 'Conversation not found'}
            
            if conversation.user_id != request.env.user:
                return {'success': False, 'error': 'Access denied'}
            
            conversation.write({
                'user_rating': str(rating),
                'user_feedback': feedback,
            })
            
            return {'success': True}
            
        except Exception as e:
            _logger.error(f"Error rating conversation: {str(e)}")
            return {'success': False, 'error': str(e)}

