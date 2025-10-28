# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import urllib.parse


class PosWhatsappSend(models.TransientModel):
    _name = 'pos.whatsapp.send'
    _description = 'Send Order via WhatsApp'

    order_id = fields.Many2one(
        'pos.perfume.order',
        string='Order',
        required=True,
        default=lambda self: self.env.context.get('default_order_id')
    )
    
    phone = fields.Char(
        string='Phone Number',
        required=True,
        help='Phone number with country code (e.g., +9647xxxxxxxxx)'
    )
    
    message = fields.Text(
        string='Message',
        required=True
    )
    
    @api.onchange('order_id')
    def _onchange_order_id(self):
        """Prepare default message when order is selected"""
        if self.order_id:
            # Get phone from partner
            if self.order_id.partner_id.phone:
                self.phone = self.order_id.partner_id.phone
            elif self.order_id.partner_id.mobile:
                self.phone = self.order_id.partner_id.mobile
            
            # Prepare message
            self.message = self._prepare_message()
    
    def _prepare_message(self):
        """Prepare WhatsApp message with order details"""
        order = self.order_id
        
        # Header
        message = f"*{_('Order')} {order.name}*\n"
        message += f"{_('Customer')}: {order.partner_id.name}\n"
        message += f"{_('Date')}: {order.date.strftime('%Y-%m-%d %H:%M')}\n"
        message += "\n"
        
        # Order lines
        message += f"*{_('Order Details')}:*\n"
        message += "━━━━━━━━━━━━━━━━━━━━\n"
        
        for line in order.order_line_ids:
            message += f"• {line.product_id.name}\n"
            if line.product_foreign_name:
                message += f"  ({line.product_foreign_name})\n"
            message += f"  {_('Qty')}: {line.quantity:.0f} x ${line.unit_price:.2f}"
            if line.discount_percent > 0:
                message += f" (-{line.discount_percent:.1f}%)"
            message += f"\n  {_('Total')}: ${line.line_total:.2f}\n"
            message += "\n"
        
        # Totals
        message += "━━━━━━━━━━━━━━━━━━━━\n"
        message += f"{_('Subtotal')}: ${order.amount_subtotal:.2f}\n"
        if order.amount_discount > 0:
            message += f"{_('Discount')}: -${order.amount_discount:.2f}\n"
        if order.amount_tax > 0:
            message += f"{_('Tax')}: ${order.amount_tax:.2f}\n"
        message += "\n"
        message += f"*{_('Total (USD)')}: ${order.amount_total:.2f}*\n"
        message += f"*{_('Total (IQD)')}: {order.amount_total_iqd:,.0f} IQD*\n"
        message += "\n"
        message += f"_{_('Exchange Rate')}: 1 USD = {order.exchange_rate:,.0f} IQD_\n"
        message += "\n"
        message += f"{_('Thank you for your business!')} 🌸"
        
        return message
    
    def action_send(self):
        """Send message via WhatsApp"""
        self.ensure_one()
        
        # Clean phone number (remove spaces, dashes, etc.)
        phone = self.phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Make sure phone starts with +
        if not phone.startswith('+'):
            if phone.startswith('00'):
                phone = '+' + phone[2:]
            elif phone.startswith('0'):
                # Assume Iraq (+964)
                phone = '+964' + phone[1:]
            else:
                phone = '+' + phone
        
        # Encode message for URL
        encoded_message = urllib.parse.quote(self.message)
        
        # Create WhatsApp URL
        whatsapp_url = f"https://wa.me/{phone.replace('+', '')}?text={encoded_message}"
        
        # Open WhatsApp in new window
        return {
            'type': 'ir.actions.act_url',
            'url': whatsapp_url,
            'target': 'new',
        }

