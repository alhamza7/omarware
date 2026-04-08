# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class ProductSearchController(http.Controller):
    
    @http.route('/lugal/api/products/search', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def search_products(self, query='', filters=None, limit=50, **kwargs):
        """
        POS-style product search with AI assistance
        
        Input:
        {
            "query": "search term or natural language question",
            "filters": {
                "category_id": 123,
                "min_price": 10,
                "max_price": 100,
                "available_only": true
            },
            "limit": 50
        }
        
        Output:
        {
            "success": true,
            "products": [...],
            "total_count": 123,
            "ai_suggestion": "Optional AI interpretation"
        }
        """
        try:
            # Check permissions
            permission_model = request.env['lugal.permission']
            if not permission_model.check_permission(request.env.user, 'can_access_products'):
                return {
                    'success': False,
                    'error': 'Access denied to product data',
                }
            
            # Build search domain
            domain = []
            
            # Text search
            if query:
                domain.append('|')
                domain.append(('name', 'ilike', query))
                domain.append(('default_code', 'ilike', query))
            
            # Apply filters
            if filters:
                if filters.get('category_id'):
                    domain.append(('categ_id', '=', filters['category_id']))
                
                if filters.get('min_price'):
                    domain.append(('list_price', '>=', filters['min_price']))
                
                if filters.get('max_price'):
                    domain.append(('list_price', '<=', filters['max_price']))
                
                if filters.get('available_only'):
                    domain.append(('qty_available', '>', 0))
            
            # Search products
            products = request.env['product.product'].search(domain, limit=limit, order='name')
            total_count = request.env['product.product'].search_count(domain)
            
            # Check for SAP integration
            sap_data = self._get_sap_data(products) if self._has_sap_integration() else None
            
            # Format response
            products_data = []
            for product in products:
                products_data.append({
                    'id': product.id,
                    'name': product.name,
                    'default_code': product.default_code,
                    'barcode': product.barcode,
                    'list_price': product.list_price,
                    'standard_price': product.standard_price,
                    'qty_available': product.qty_available,
                    'uom_name': product.uom_id.name,
                    'uom_id': product.uom_id.id,
                    'category': product.categ_id.name if product.categ_id else '',
                    'image_url': f'/web/image/product.product/{product.id}/image_128' if product.image_128 else '',
                    'taxes': [{'id': t.id, 'name': t.name, 'amount': t.amount} for t in product.taxes_id],
                })
            
            # AI suggestion (if query looks like a question)
            ai_suggestion = None
            if query and ('؟' in query or '?' in query or len(query.split()) > 3):
                ai_suggestion = self._get_ai_product_suggestion(query, products_data)
            
            return {
                'success': True,
                'products': products_data,
                'total_count': total_count,
                'ai_suggestion': ai_suggestion,
                'sap_data': sap_data,
            }
            
        except Exception as e:
            _logger.error(f"Error searching products: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
            }
    
    def _get_ai_product_suggestion(self, query, products):
        """Get AI suggestion for product search"""
        try:
            config = request.env['lugal.config'].get_active_config()
            
            import google.generativeai as genai
            genai.configure(api_key=config.gemini_api_key)
            
            model = genai.GenerativeModel(config.gemini_model)
            
            prompt = f"""Based on this product search query: "{query}"

And these available products:
{json.dumps(products[:10], ensure_ascii=False, indent=2)}

Provide a SHORT, helpful suggestion in the same language as the query (Arabic or English).
Maximum 2 sentences. Focus on answering the user's question or recommending the best match.

Response:"""
            
            response = model.generate_content(prompt)
            
            if response and response.text:
                return response.text.strip()
            
        except Exception as e:
            _logger.warning(f"Error getting AI suggestion: {str(e)}")
        
        return None
    
    @http.route('/lugal/api/products/details', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_product_details(self, product_id, **kwargs):
        """Get detailed product information with AI insights"""
        try:
            product = request.env['product.product'].browse(product_id)
            
            if not product.exists():
                return {'success': False, 'error': 'Product not found'}
            
            # Get related data
            variants = product.product_tmpl_id.product_variant_ids
            sales_data = self._get_product_sales_stats(product)
            stock_data = self._get_product_stock_info(product)
            
            return {
                'success': True,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'description': product.description_sale or '',
                    'default_code': product.default_code,
                    'barcode': product.barcode,
                    'list_price': product.list_price,
                    'standard_price': product.standard_price,
                    'currency': request.env.company.currency_id.symbol,
                    'qty_available': product.qty_available,
                    'virtual_available': product.virtual_available,
                    'incoming_qty': product.incoming_qty,
                    'outgoing_qty': product.outgoing_qty,
                    'uom': {
                        'id': product.uom_id.id,
                        'name': product.uom_id.name,
                    },
                    'category': {
                        'id': product.categ_id.id,
                        'name': product.categ_id.name,
                    } if product.categ_id else None,
                    'variants': [{
                        'id': v.id,
                        'name': v.name,
                        'price': v.list_price,
                    } for v in variants],
                    'sales_stats': sales_data,
                    'stock_info': stock_data,
                    'image_urls': {
                        'small': f'/web/image/product.product/{product.id}/image_128',
                        'medium': f'/web/image/product.product/{product.id}/image_256',
                        'large': f'/web/image/product.product/{product.id}/image_512',
                    } if product.image_128 else None,
                },
            }
            
        except Exception as e:
            _logger.error(f"Error getting product details: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _get_product_sales_stats(self, product):
        """Get sales statistics for a product"""
        try:
            permission_model = request.env['lugal.permission']
            if not permission_model.check_permission(request.env.user, 'can_access_sales'):
                return None
            
            # Get sales order lines for this product
            order_lines = request.env['sale.order.line'].search([
                ('product_id', '=', product.id),
                ('order_id.state', 'in', ['sale', 'done']),
            ], limit=100)
            
            if not order_lines:
                return {'total_sold': 0, 'total_revenue': 0}
            
            total_qty = sum(order_lines.mapped('product_uom_qty'))
            total_revenue = sum(order_lines.mapped('price_subtotal'))
            
            return {
                'total_sold': total_qty,
                'total_revenue': total_revenue,
                'avg_price': total_revenue / total_qty if total_qty > 0 else 0,
            }
        except:
            return None
    
    def _get_product_stock_info(self, product):
        """Get stock information for a product"""
        try:
            permission_model = request.env['lugal.permission']
            if not permission_model.check_permission(request.env.user, 'can_access_inventory'):
                return None
            
            # Get stock by location
            quants = request.env['stock.quant'].search([
                ('product_id', '=', product.id),
                ('quantity', '>', 0),
            ])
            
            locations = {}
            for quant in quants:
                loc_name = quant.location_id.complete_name
                locations[loc_name] = locations.get(loc_name, 0) + quant.quantity
            
            return {
                'locations': locations,
                'total_qty': sum(locations.values()),
            }
        except:
            return None
    
    @http.route('/lugal/api/products/categories', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_categories(self, **kwargs):
        """Get product categories"""
        try:
            categories = request.env['product.category'].search([], order='name')
            
            return {
                'success': True,
                'categories': [{
                    'id': c.id,
                    'name': c.complete_name,
                    'parent_id': c.parent_id.id if c.parent_id else None,
                } for c in categories],
            }
            
        except Exception as e:
            _logger.error(f"Error getting categories: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _has_sap_integration(self):
        """Check if SAP integration module is installed"""
        try:
            return 'sap.backend' in request.env
        except:
            return False
    
    def _get_sap_data(self, products):
        """Get SAP-related data for products if SAP integration is available"""
        try:
            if not products:
                return None
            
            sap_data = {}
            for product in products:
                # Check if product has SAP fields
                if hasattr(product, 'sap_material_code'):
                    sap_data[product.id] = {
                        'sap_code': getattr(product, 'sap_material_code', ''),
                        'sap_plant': getattr(product, 'sap_plant', ''),
                        'sap_stock': getattr(product, 'sap_stock_qty', 0),
                        'sap_synced': getattr(product, 'sap_last_sync', False),
                    }
            
            return sap_data if sap_data else None
        except Exception as e:
            _logger.warning(f"Error getting SAP data: {str(e)}")
            return None
    
    @http.route('/lugal/api/products/ask', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def ask_about_products(self, question, **kwargs):
        """Ask AI questions about products"""
        try:
            # Get all products (limited)
            products = request.env['product.product'].search([], limit=200)
            
            products_data = [{
                'name': p.name,
                'code': p.default_code,
                'price': p.list_price,
                'qty': p.qty_available,
                'category': p.categ_id.name if p.categ_id else '',
            } for p in products]
            
            # Call Gemini API via main controller
            gemini_controller = GeminiAPIController()
            
            # Build context
            context = {
                'products': products_data,
                'total_count': len(products),
            }
            
            # Reuse main ask endpoint
            result = request.env['lugal.conversation'].sudo()._ask_gemini_with_context(
                question=question,
                context=json.dumps(context),
                user=request.env.user,
            )
            
            return result
            
        except Exception as e:
            _logger.error(f"Error in ask_about_products: {str(e)}")
            return {'success': False, 'error': str(e)}

