# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class POSPerfumeWhatsAppImage(http.Controller):
    """Send invoice as IMAGE via WhatsApp - Direct HTML to Image"""
    
    @http.route('/pos_perfume/send_whatsapp_image', type='json', auth='user', methods=['POST'], csrf=False)
    def send_whatsapp_image(self, order_id):
        """Send invoice as PNG IMAGE via WhatsApp (Direct HTML → Image)"""
        try:
            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return {'success': False, 'error': 'Order not found'}
            
            if not order.partner_id or not order.partner_id.phone:
                return {'success': False, 'error': 'Customer phone number is missing'}
            
            _logger.info(f"[WhatsApp Image] Starting DIRECT HTML→Image for order {order.name}")
            
            try:
                import subprocess
                import tempfile
                import os
                import base64
                from io import BytesIO
                
                # Step 1: Generate HTML
                _logger.info("[WhatsApp Image] Step 1: Generating HTML...")
                
                # Get the QWeb template and render it directly
                template_name = 'pos_perfume_custom.report_pos_perfume_order'
                html_content = request.env['ir.qweb']._render(template_name, {'docs': order, 'o': order})
                
                # Convert bytes to string if needed
                if isinstance(html_content, bytes):
                    html_content = html_content.decode('utf-8')
                
                # Add base tag for relative URLs
                base_url = request.httprequest.host_url
                if '<head>' in html_content:
                    html_content = html_content.replace('<head>', f'<head><base href="{base_url}"/>')
                elif '<!DOCTYPE' in html_content or '<html' in html_content:
                    # Add head if missing
                    html_content = html_content.replace('<html', f'<html><head><base href="{base_url}"/></head', 1)
                
                if not html_content or len(html_content) < 100:
                    raise Exception("HTML generation returned empty content")
                
                _logger.info(f"[WhatsApp Image] HTML generated ({len(html_content)} chars)")
                
                # Step 2: Convert HTML → PNG using wkhtmltoimage (via stdin)
                _logger.info("[WhatsApp Image] Step 2: Converting HTML to PNG...")
                
                # Create temp output file
                png_path = tempfile.mktemp(suffix='.png')
                
                # wkhtmltoimage command - read from stdin
                cmd = [
                    'wkhtmltoimage',
                    '--quality', '85',
                    '--width', '800',
                    '--height', '0',  # Auto height
                    '--load-error-handling', 'ignore',
                    '--load-media-error-handling', 'ignore',
                    '--disable-javascript',
                    '--no-stop-slow-scripts',
                    '--encoding', 'utf-8',
                    '-',  # Read from stdin
                    png_path
                ]
                
                # Set environment variables
                env = os.environ.copy()
                env['XDG_RUNTIME_DIR'] = '/tmp/runtime-odoo'
                
                # Run conversion with HTML as stdin
                result = subprocess.run(
                    cmd,
                    input=html_content.encode('utf-8'),
                    capture_output=True,
                    timeout=30,
                    env=env
                )
                
                if result.returncode != 0:
                    _logger.error(f"wkhtmltoimage stderr: {result.stderr.decode('utf-8')}")
                    raise Exception(f"wkhtmltoimage failed with code {result.returncode}")
                
                # Step 3: Read image
                with open(png_path, 'rb') as img_file:
                    img_content = img_file.read()
                
                img_base64 = base64.b64encode(img_content).decode('utf-8')
                
                _logger.info(f"[WhatsApp Image] Image generated ({len(img_content)} bytes)")
                
                # Cleanup temp file
                try:
                    os.unlink(png_path)
                except:
                    pass
                
                # Step 5: Create attachment
                attachment = request.env['ir.attachment'].create({
                    'name': f'Invoice_{order.name}.png',
                    'type': 'binary',
                    'datas': base64.b64encode(img_content),
                    'res_model': 'pos.perfume.order',
                    'res_id': order.id,
                    'public': True,
                    'mimetype': 'image/png'
                })
                _logger.info(f"[WhatsApp Image] Attachment created (ID: {attachment.id})")
                
            except FileNotFoundError:
                _logger.error("wkhtmltoimage not found!")
                return {
                    'success': False,
                    'error': 'wkhtmltoimage not installed. Run: sudo apt-get install wkhtmltopdf'
                }
            except subprocess.TimeoutExpired:
                _logger.error("wkhtmltoimage timeout!")
                return {'success': False, 'error': 'Image generation timeout'}
            except Exception as img_error:
                _logger.error(f"Image generation error: {img_error}", exc_info=True)
                return {'success': False, 'error': f'Failed to generate image: {str(img_error)}'}
            
            # Step 6: Get ULTRAMSG config
            config = request.env['ultramsg.config'].search([('active', '=', True)], limit=1)
            if not config:
                return {'success': False, 'error': 'ULTRAMSG not configured'}
            
            # Step 7: Prepare message
            exchange_rate = float(
                request.env['ir.config_parameter'].sudo().get_param(
                    'pos_perfume.default_exchange_rate_usd_iqd', '1530.0'
                )
            )
            iqd_amount = order.amount_total * exchange_rate
            iqd_rounded = round(iqd_amount / 1000) * 1000
            
            message_body = f"""مرحباً {order.partner_id.name}،

📄 فاتورة رقم: {order.name}
💰 المجموع: ${order.amount_total:.2f}
💵 بالدينار: {int(iqd_rounded):,} د.ع

شكراً لتعاملك معنا! 🌟"""
            
            # Step 8: Create message log
            message = request.env['ultramsg.message'].create({
                'phone': order.partner_id.phone,
                'message_type': 'image',
                'message_body': message_body,
                'res_model': 'pos.perfume.order',
                'res_id': order.id,
                'state': 'sending',
            })
            
            # Step 9: Send IMAGE via ULTRAMSG
            _logger.info("[WhatsApp Image] Sending to ULTRAMSG...")
            
            try:
                result = config.send_message(
                    phone=order.partner_id.phone,
                    message_type='image',
                    message_body=message_body,
                    document_url=img_base64,
                    document_name=f'Invoice_{order.name}.png',
                )
                
                # Ensure result is a dict
                if not isinstance(result, dict):
                    _logger.error(f"Unexpected result type: {type(result)}, value: {result}")
                    result = {'success': False, 'error': f'Unexpected response type: {type(result)}'}
                
                _logger.info(f"[WhatsApp Image] ULTRAMSG result: {result}")
                
            except Exception as send_error:
                _logger.error(f"Error sending to ULTRAMSG: {send_error}", exc_info=True)
                result = {'success': False, 'error': str(send_error)}
            
            # Process result
            if result.get('success'):
                message.write({
                    'state': 'sent',
                    'sent_date': fields.Datetime.now(),
                    'ultramsg_id': result.get('ultramsg_id'),
                    'ultramsg_response': str(result.get('response')),
                })
                _logger.info(f"✅ [WhatsApp Image] Sent to {order.partner_id.phone}")
                return {
                    'success': True,
                    'message': f'✅ تم إرسال الفاتورة كصورة إلى {order.partner_id.phone}',
                    'message_id': message.id
                }
            else:
                message.write({
                    'state': 'failed',
                    'error_message': result.get('error'),
                    'ultramsg_response': str(result.get('response')),
                })
                _logger.error(f"❌ [WhatsApp Image] Failed: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error') or 'Failed to send image',
                    'message_id': message.id
                }
                
        except Exception as e:
            _logger.error(f"[WhatsApp Image] Error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

