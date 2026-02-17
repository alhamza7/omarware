# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class PosPerfumeController(http.Controller):

    @http.route('/pos_perfume/get_exchange_rate', type='json', auth='user')
    def get_exchange_rate(self):
        """نفس المصدر المستخدم في الطباعة: قراءة من DB بدون كاش لجميع المستخدمين."""
        return request.env['pos.perfume.order'].sudo().get_exchange_rate_from_db()
    
    @http.route('/pos_perfume/get_product_data', type='json', auth='user')
    def get_product_data(self, product_id, pricelist_id=None, uom_id=None, warehouse_id=None):
        """
        Get product data - EXACTLY like sale.order.line
        """
        try:
            _logger.info(f"[POS] Getting product {product_id}, pricelist {pricelist_id}")
            
            product = request.env['product.product'].browse(product_id)
            if not product.exists():
                return {'success': False, 'error': 'Product not found'}
            
            # Ensure pricelist is a single record
            pricelist = None
            if pricelist_id:
                if isinstance(pricelist_id, list):
                    pricelist_id = pricelist_id[0]  # Take first one
                pricelist = request.env['product.pricelist'].browse(int(pricelist_id))
                if not pricelist.exists():
                    pricelist = None
            
            # Get all UoMs with prices from pricelist items
            available_uoms = self._get_uoms_from_pricelist(product, pricelist)
            
            _logger.info(f"[POS] Found {len(available_uoms)} UoMs")
            
            # Get default price for base UoM
            default_uom = uom_id or product.uom_id.id
            default_price = self._get_price_for_uom(product, pricelist, default_uom)
            
            _logger.info(f"[POS] Default price: {default_price}")
            
            # Get warehouses with stock
            warehouses = self._get_warehouses_simple(product_id)
            
            _logger.info(f"[POS] Found {len(warehouses)} warehouses")
            
            # Get color and badge info based on product code
            priority, color_class, badge_text = product._get_product_priority_and_color(product.default_code)
            
            # Get foreign_name
            foreign_name = ''
            if hasattr(product, 'foreign_name'):
                foreign_name = product.foreign_name or ''
            
            return {
                'success': True,
                'data': {
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_uom_id': product.uom_id.id,
                    'product_uom_name': product.uom_id.name,
                    'price_unit': default_price,
                    'available_qty': product.qty_available,
                    'available_uoms': available_uoms,
                    'warehouses': warehouses,
                    'default_code': product.default_code or '',
                    'foreign_name': foreign_name,
                    'color_class': color_class,
                    'badge_text': badge_text,
                }
            }
            
        except Exception as e:
            _logger.error(f"[POS] Error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _get_uoms_from_pricelist(self, product, pricelist):
        """
        Get all UoMs with prices - Using SAP UoM Group!
        """
        uoms_with_prices = {}  # {uom_id: price}
        
        if not pricelist:
            return [{
                'id': product.uom_id.id,
                'name': product.uom_id.name,
                'price': product.list_price,
            }]
        
        # Step 1: Get available UoMs from SAP UoM Group
        available_uom_ids = []
        
        # Check if product has SAP UoM Group
        extended_info = request.env['sap.product.extended'].search([
            ('product_id', '=', product.id)
        ], limit=1)
        
        if extended_info and extended_info.sap_uom_group_id:
            # Get UoMs from SAP UoM Group
            uom_syncs = extended_info.sap_uom_group_id.uom_ids
            available_uom_ids = uom_syncs.mapped('odoo_uom_id').ids
            _logger.info(f"[POS] Product has UoM Group: {extended_info.sap_uom_group_id.name}, {len(available_uom_ids)} UoMs")
        
        # If no group or no UoMs in group, use all UoMs from pricelist items
        if not available_uom_ids:
            _logger.info(f"[POS] No UoM Group, searching all pricelist items")
        
        # Step 2: Get pricelist items
        items = request.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            '|',
            ('product_id', '=', False),
            ('product_id', '=', product.id),
        ])
        
        _logger.info(f"[POS] Found {len(items)} pricelist items")
        
        # Step 3: Process each item
        for item in items:
            # IMPORTANT: Each pricelist item represents ONE price point
            # - If NO packaging → price applies to product_uom_id
            # - If HAS packaging → price applies to packaging (which IS a UoM in your system)
            
            if not item.product_packaging_id:
                # Case 1: No packaging → this is base UoM price
                uom = item.product_uom_id or product.uom_id
                
                # Filter by UoM Group
                if available_uom_ids and uom.id not in available_uom_ids:
                    _logger.info(f"[POS]   Skipping {uom.name} - not in UoM Group")
                    continue
                
                # Use fixed price
                price = item.fixed_price if item.compute_price == 'fixed' else product.list_price
                
                # Priority: base item (no packaging) always replaces
                uoms_with_prices[uom.id] = {'uom': uom, 'price': price, 'has_packaging': False}
                _logger.info(f"[POS]   UoM {uom.name}: ${price} (BASE - no packaging)")
                
            else:
                # Case 2: Has packaging → packaging IS the UoM in your system
                packaging_uom = item.product_packaging_id
                
                # Filter by UoM Group
                if available_uom_ids and packaging_uom.id not in available_uom_ids:
                    _logger.info(f"[POS]   Skipping {packaging_uom.name} - not in UoM Group")
                    continue
                
                # Use fixed price
                price = item.fixed_price if item.compute_price == 'fixed' else product.list_price
                
                # Only add if not already have base price for this UoM
                if packaging_uom.id not in uoms_with_prices or uoms_with_prices[packaging_uom.id]['has_packaging']:
                    uoms_with_prices[packaging_uom.id] = {'uom': packaging_uom, 'price': price, 'has_packaging': True}
                    _logger.info(f"[POS]   UoM {packaging_uom.name}: ${price} (from packaging)")
                else:
                    _logger.info(f"[POS]   Skipping {packaging_uom.name} packaging - already have base price")
        
        # Step 4: Convert to list
        result = []
        for uom_id, data in uoms_with_prices.items():
            result.append({
                'id': data['uom'].id,
                'name': data['uom'].name,
                'price': data['price'],
            })
        
        # Step 5: Always include base UoM if not present
        if product.uom_id.id not in uoms_with_prices:
            price = self._get_price_for_uom(product, pricelist, product.uom_id.id)
            result.insert(0, {
                'id': product.uom_id.id,
                'name': product.uom_id.name,
                'price': price,
            })
        
        _logger.info(f"[POS] Returning {len(result)} UoMs total")
        
        return result if result else [{
            'id': product.uom_id.id,
            'name': product.uom_id.name,
            'price': product.list_price,
        }]
    
    def _get_price_for_uom(self, product, pricelist, uom_id):
        """Get price for specific UoM using pricelist"""
        if not pricelist:
            return product.list_price
        
        uom = request.env['uom.uom'].browse(uom_id)
        
        try:
            # Use pricelist _get_product_price (same as sale.order.line)
            price = pricelist._get_product_price(
                product=product,
                quantity=1.0,
                uom=uom,
            )
            return price
        except Exception as e:
            _logger.warning(f"[POS] Error getting price: {e}")
            # Fallback: convert base price to target UoM
            base_price = product.list_price
            if uom != product.uom_id:
                try:
                    price = product.uom_id._compute_price(base_price, uom)
                    return price
                except:
                    pass
            return base_price
    
    def _get_warehouses_simple(self, product_id):
        """Get warehouses with available stock from SAP integration or stock.quant"""
        try:
            warehouses = []
            
            # Primary source: sap.product.warehouse.info
            if 'sap.product.warehouse.info' in request.env:
                sap_infos = request.env['sap.product.warehouse.info'].search([
                    ('product_id', '=', product_id),
                ])
                
                _logger.info(f"[POS] Found {len(sap_infos)} SAP warehouse info records")
                
                for sap_info in sap_infos:
                    # Use current_qty_available (computed from Odoo) or last_available (from SAP)
                    qty = sap_info.current_qty_available or sap_info.last_available or 0
                    
                    if qty > 0 and sap_info.warehouse_id:
                        warehouses.append({
                            'id': sap_info.warehouse_id.id,
                            'name': sap_info.warehouse_id.name,
                            'code': sap_info.sap_warehouse_code or sap_info.warehouse_id.code,
                            'quantity': float(qty),
                        })
                
                if warehouses:
                    _logger.info(f"[POS] Returning {len(warehouses)} warehouses from SAP")
                    return warehouses
                else:
                    _logger.info("[POS] No SAP warehouses with stock > 0")
            
            # Fallback: stock.quant (Odoo inventory)
            _logger.info("[POS] Trying stock.quant fallback")
            query = """
                SELECT 
                    sw.id,
                    sw.name,
                    sw.code,
                    COALESCE(SUM(sq.quantity - sq.reserved_quantity), 0) as available_qty
                FROM stock_warehouse sw
                LEFT JOIN stock_location sl ON sl.warehouse_id = sw.id AND sl.usage = 'internal'
                LEFT JOIN stock_quant sq ON sq.location_id = sl.id AND sq.product_id = %s
                WHERE sw.active = true
                GROUP BY sw.id, sw.name, sw.code
                HAVING COALESCE(SUM(sq.quantity - sq.reserved_quantity), 0) > 0
                ORDER BY sw.name
            """
            
            request.env.cr.execute(query, (product_id,))
            results = request.env.cr.dictfetchall()
            
            for row in results:
                warehouses.append({
                    'id': row['id'],
                    'name': row['name'],
                    'code': row['code'] or row['name'][:5],
                    'quantity': float(row['available_qty']),
                })
            
            _logger.info(f"[POS] Returning {len(warehouses)} warehouses from stock.quant")
            return warehouses
            
        except Exception as e:
            _logger.error(f"[POS] Error getting warehouses: {e}", exc_info=True)
            return []
    
    @http.route('/pos_perfume/onchange_uom', type='json', auth='user')
    def onchange_uom(self, product_id, pricelist_id, uom_id):
        """Get price for changed UoM"""
        try:
            product = request.env['product.product'].browse(product_id)
            
            # Ensure pricelist is a single record
            pricelist = None
            if pricelist_id:
                if isinstance(pricelist_id, list):
                    pricelist_id = pricelist_id[0]
                pricelist = request.env['product.pricelist'].browse(int(pricelist_id))
                if not pricelist.exists():
                    pricelist = None
            
            price = self._get_price_for_uom(product, pricelist, uom_id)
            
            return {
                'success': True,
                'price_unit': price,
            }
        except Exception as e:
            _logger.error(f"[POS] Error in onchange_uom: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/pos_perfume/send_whatsapp', type='json', auth='user', methods=['POST'], csrf=False)
    def send_whatsapp(self, order_id):
        """Send invoice details as TEXT via WhatsApp - INSTANT!"""
        try:
            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return {'success': False, 'error': 'Order not found'}
            
            if not order.partner_id or not order.partner_id.phone:
                return {'success': False, 'error': 'Customer phone number is missing'}
            
            _logger.info(f"[WhatsApp Text] Starting for order {order.name}")
            
            # Get ULTRAMSG config
            config = request.env['ultramsg.config'].search([('active', '=', True)], limit=1)
            if not config:
                return {'success': False, 'error': 'ULTRAMSG not configured'}
            
            # Get exchange rate from settings (always use current rate)
            exchange_rate = float(
                request.env['ir.config_parameter'].sudo().get_param(
                    'pos_perfume.default_exchange_rate_usd_iqd', '1510.0'
                )
            )
            iqd_amount = order.amount_total * exchange_rate
            iqd_rounded = round(iqd_amount / 1000) * 1000
            
            # Build detailed message with product list
            product_lines = []
            for idx, line in enumerate(order.order_line_ids, 1):
                product_lines.append(
                    f"{idx}. {line.product_id.name}\n"
                    f"   الكمية: {line.quantity:.2f} {line.product_uom_id.name}\n"
                    f"   السعر: ${line.price_unit:.2f}\n"
                    f"   المجموع: ${line.price_subtotal:.2f}"
                )
            
            products_text = "\n\n".join(product_lines)
            
            message_body = f"""🌟 فاتورة من متجرنا 🌟

👤 العميل: {order.partner_id.name}
📄 رقم الفاتورة: {order.name}
📅 التاريخ: {order.date.strftime('%Y-%m-%d') if order.date else ''}

━━━━━━━━━━━━━━━━━━━━
📦 المنتجات:

{products_text}

━━━━━━━━━━━━━━━━━━━━
💰 المجموع الكلي: ${order.amount_total:.2f}
💵 بالدينار العراقي: {int(iqd_rounded):,} د.ع

شكراً لتعاملك معنا! 💚"""
            
            # Create message log
            message = request.env['ultramsg.message'].create({
                'phone': order.partner_id.phone,
                'message_type': 'text',
                'message_body': message_body,
                'res_model': 'pos.perfume.order',
                'res_id': order.id,
                'state': 'sending',
            })
            
            # Send TEXT via ULTRAMSG (INSTANT!)
            _logger.info("[WhatsApp Text] Sending to ULTRAMSG...")
            
            try:
                result = config.send_message(
                    phone=order.partner_id.phone,
                    message_type='text',
                    message_body=message_body,
                )
                
                if not isinstance(result, dict):
                    _logger.error(f"Unexpected result type: {type(result)}")
                    result = {'success': False, 'error': f'Unexpected response: {type(result)}'}
                
                _logger.info(f"[WhatsApp Text] ULTRAMSG result: {result}")
                
            except Exception as send_error:
                _logger.error(f"Send error: {send_error}", exc_info=True)
                result = {'success': False, 'error': str(send_error)}
            
            # Process result
            if result.get('success'):
                message.write({
                    'state': 'sent',
                    'sent_date': fields.Datetime.now(),
                    'ultramsg_id': result.get('ultramsg_id'),
                    'ultramsg_response': str(result.get('response')),
                })
                _logger.info(f"✅ [WhatsApp Text] Sent to {order.partner_id.phone}")
                return {
                    'success': True,
                    'message': f'✅ تم إرسال الفاتورة إلى {order.partner_id.phone}',
                    'message_id': message.id
                }
            else:
                message.write({
                    'state': 'failed',
                    'error_message': result.get('error'),
                    'ultramsg_response': str(result.get('response')),
                })
                _logger.error(f"❌ [WhatsApp Text] Failed: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error') or 'Failed to send message',
                    'message_id': message.id
                }
                
        except Exception as e:
            _logger.error(f"[WhatsApp Text] Error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
