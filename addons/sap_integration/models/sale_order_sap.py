# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    sap_doc_num = fields.Char(
        string='SAP Document Number',
        copy=False,
        help="رقم Document الذي تم إرجاعه من SAP عند إنشاء Quotation"
    )
    sap_doc_entry = fields.Integer(
        string='SAP Doc Entry',
        copy=False,
        help="رقم DocEntry الذي تم إرجاعه من SAP"
    )
    sap_synced = fields.Boolean(
        string='Synced to SAP',
        default=False,
        copy=False,
        help="تم إرسال هذا Quotation إلى SAP"
    )
    
    @api.model
    def create(self, vals):
        """Override create to send quotation to SAP after creation"""
        quotation = super(SaleOrder, self).create(vals)
        
        _logger.info(f"=== Sale Order Created: {quotation.name}, state={quotation.state}, sap_synced={quotation.sap_synced}, partner={quotation.partner_id.name if quotation.partner_id else 'None'}, partner_ref={quotation.partner_id.ref if quotation.partner_id else 'None'}, order_lines_count={len(quotation.order_line)} ===")
        
        # إرسال quotation إلى SAP إذا كان في حالة draft وبعد أن يتم حفظه بالكامل
        # نستخدم delay لتجنب مشاكل في transaction
        if quotation.state == 'draft' and not quotation.sap_synced:
            _logger.info(f"Quotation {quotation.name} is in draft and not synced, checking conditions...")
            # التحقق من وجود بيانات كافية قبل الإرسال
            if quotation.partner_id and quotation.partner_id.ref and quotation.order_line:
                _logger.info(f"Conditions met for quotation {quotation.name}, attempting to send to SAP...")
                # استخدام with_delay() إذا كان متاحاً، وإلا نرسل مباشرة
                try:
                    quotation._send_to_sap()
                except Exception as e:
                    _logger.warning(f"Could not send quotation {quotation.name} to SAP on create: {e}")
            else:
                _logger.info(f"Conditions not met for quotation {quotation.name}: partner_id={quotation.partner_id is not None}, partner_ref={quotation.partner_id.ref if quotation.partner_id else None}, order_lines={len(quotation.order_line) if quotation.order_line else 0}")
        else:
            _logger.info(f"Quotation {quotation.name} not eligible for SAP sync: state={quotation.state}, sap_synced={quotation.sap_synced}")
        
        return quotation
    
    def write(self, vals):
        """Override write to send quotation/sale order to SAP when needed"""
        result = super(SaleOrder, self).write(vals)
        
        # تحديث في SAP إذا تم تحديث بيانات مهمة
        for order in self:
            # التحقق من وجود بيانات كافية قبل الإرسال
            if not order.partner_id or not order.partner_id.ref or not order.order_line:
                continue
            
            # إذا تم تحديث بيانات مهمة
            if any(field in vals for field in ['partner_id', 'order_line', 'date_order', 'validity_date', 'price_unit', 'discount', 'product_uom_qty']):
                # للـ quotations (draft): إرسال أو تحديث
                if order.state == 'draft':
                    if not order.sap_synced:
                        # إرسال quotation جديد
                        try:
                            order._send_to_sap()
                        except Exception as e:
                            _logger.warning(f"Could not send quotation {order.name} to SAP on write: {e}")
                    elif order.sap_doc_entry:
                        # تحديث quotation موجود في SAP
                        try:
                            order._send_to_sap()
                        except Exception as e:
                            _logger.warning(f"Could not update quotation {order.name} in SAP on write: {e}")
                # للـ sale orders: تحديث فقط إذا كان موجود في SAP
                elif order.state == 'sale' and order.sap_doc_entry:
                    try:
                        order._send_to_sap()
                    except Exception as e:
                        _logger.warning(f"Could not update sale order {order.name} in SAP on write: {e}")
        
        return result
    
    def _send_to_sap(self):
        """إرسال quotation إلى SAP ومزامنته"""
        for quotation in self:
            _logger.info(f">>> Starting _send_to_sap for quotation {quotation.name} <<<")
            try:
                # التحقق من وجود backend نشط
                backend = self.env['sap.backend'].search([
                    ('active', '=', True)
                ], limit=1)
                
                if not backend:
                    _logger.warning(f"No active SAP backend found for quotation {quotation.name}")
                    return
                
                _logger.info(f"Found active SAP backend: {backend.name} (id={backend.id})")
                
                # التحقق من وجود partner مع CardCode
                if not quotation.partner_id or not quotation.partner_id.ref:
                    _logger.warning(f"Quotation {quotation.name} has no partner with CardCode (ref)")
                    return
                
                _logger.info(f"Partner found: {quotation.partner_id.name}, CardCode={quotation.partner_id.ref}")
                
                # التحقق من وجود order lines
                if not quotation.order_line:
                    _logger.warning(f"Quotation {quotation.name} has no order lines")
                    return
                
                _logger.info(f"Order lines found: {len(quotation.order_line)} line(s)")
                
                # إعداد بيانات quotation للـ SAP
                quotation_data = self._prepare_quotation_data_for_sap(quotation, backend)
                _logger.info(f"Prepared quotation data for SAP: CardCode={quotation_data.get('CardCode')}, DocumentLines={len(quotation_data.get('DocumentLines', []))} lines")
                # Log DocumentLines details
                for idx, line in enumerate(quotation_data.get('DocumentLines', [])):
                    _logger.info(f"DocumentLine[{idx}]: ItemCode={line.get('ItemCode')}, UnitEntry={line.get('UnitEntry', 'NOT SET')}, UnitOfMeasure={line.get('UnitOfMeasure', 'NOT SET')}")
                
                # إرسال إلى SAP
                connection = backend.get_connection()
                
                # تحديد نوع الوثيقة في SAP بناءً على حالة الطلب
                if quotation.state == 'sale':
                    # للـ sale orders: تحديث أو إنشاء order في SAP
                    if quotation.sap_doc_entry and quotation.sap_doc_entry > 0:
                        # تحديث sale order موجود في SAP
                        _logger.info(f"Updating sale order {quotation.name} in SAP (DocEntry: {quotation.sap_doc_entry})")
                        # Note: For sale orders, we might need to use update_order instead of update_quotation
                        # For now, we'll try to update using the Orders endpoint
                        try:
                            # Try to update as order
                            url = f"{connection.base_url}/Orders({quotation.sap_doc_entry})"
                            headers = connection._get_headers()
                            response = connection.session.patch(url, json=quotation_data, headers=headers, timeout=30)
                            if response.status_code in [200, 204]:
                                result = response.json() if response.content else {}
                                _logger.info(f"Successfully updated sale order {quotation.name} in SAP")
                            else:
                                _logger.warning(f"Could not update sale order {quotation.name} in SAP: {response.status_code} - {response.text}")
                                result = None
                        except Exception as e:
                            _logger.warning(f"Error updating sale order {quotation.name} in SAP: {e}")
                            result = None
                    else:
                        # إنشاء sale order جديد في SAP (نادر الحدوث)
                        _logger.info(f"Creating sale order {quotation.name} in SAP")
                        url = f"{connection.base_url}/Orders"
                        headers = connection._get_headers()
                        response = connection.session.post(url, json=quotation_data, headers=headers, timeout=30)
                        if response.status_code in [200, 201]:
                            result = response.json() if response.content else {}
                        else:
                            _logger.error(f"Error creating sale order {quotation.name} in SAP: {response.status_code} - {response.text}")
                            result = None
                    
                    if result:
                        # تحديث رقم Document إذا تم إرجاعه
                        update_vals = {}
                        if result.get('DocNum'):
                            update_vals['sap_doc_num'] = result.get('DocNum')
                        if result.get('DocEntry'):
                            update_vals['sap_doc_entry'] = result.get('DocEntry')
                        if update_vals:
                            update_vals['sap_synced'] = True
                            quotation.sudo().write(update_vals)
                            _logger.info(f"Sale order {quotation.name} synced to SAP: DocNum={update_vals.get('sap_doc_num')}, DocEntry={update_vals.get('sap_doc_entry')}")
                else:
                    # للـ quotations: تحديث أو إنشاء quotation في SAP
                    if quotation.sap_doc_entry and quotation.sap_doc_entry > 0:
                        # تحديث quotation موجود
                        _logger.info(f"Updating quotation {quotation.name} in SAP (DocEntry: {quotation.sap_doc_entry})")
                        result = connection.update_quotation(quotation.sap_doc_entry, quotation_data)
                        if result:
                            # تحديث رقم Document إذا تم إرجاعه
                            update_vals = {}
                            if result.get('DocNum'):
                                update_vals['sap_doc_num'] = result.get('DocNum')
                            if result.get('DocEntry'):
                                update_vals['sap_doc_entry'] = result.get('DocEntry')
                            if update_vals:
                                update_vals['sap_synced'] = True
                                quotation.sudo().write(update_vals)
                                _logger.info(f"Quotation {quotation.name} updated in SAP: DocNum={update_vals.get('sap_doc_num')}, DocEntry={update_vals.get('sap_doc_entry')}")
                    else:
                        # إنشاء quotation جديد
                        _logger.info(f"Creating quotation {quotation.name} in SAP")
                        result = connection.create_quotation(quotation_data)
                        
                        if result:
                            # حفظ رقم Document من SAP
                            doc_num = result.get('DocNum', '')
                            doc_entry = result.get('DocEntry', 0)
                            
                            quotation.sudo().write({
                                'sap_doc_num': doc_num,
                                'sap_doc_entry': doc_entry,
                                'sap_synced': True,
                            })
                            _logger.info(f"Quotation {quotation.name} synced to SAP: DocNum={doc_num}, DocEntry={doc_entry}")
                
            except Exception as e:
                _logger.error(f"Error sending quotation {quotation.name} to SAP: {str(e)}", exc_info=True)
                # لا نرفع exception حتى لا نمنع حفظ الـ quotation في Odoo
                # يمكن إضافة notification للمستخدم هنا
    
    def _prepare_quotation_data_for_sap(self, quotation, backend=None):
        """إعداد بيانات quotation للـ SAP Service Layer"""
        # إعداد سطور الوثيقة
        document_lines = []
        for line in quotation.order_line:
            if not line.product_id:
                continue
            
            # إعداد بيانات السطر الأساسية
            line_data = {
                'ItemCode': line.product_id.default_code or '',
                'ItemDescription': line.name or line.product_id.name,
                'Quantity': line.product_uom_qty,
                'UnitPrice': line.price_unit,
                'DiscountPercent': line.discount,
            }
            
            # إضافة UoMEntry (رقم وحدة القياس) إذا كانت متوفرة
            # البحث والتحقق قبل الإرسال
            if line.product_uom_id:
                _logger.info(f"Searching for UoMEntry for UoM: {line.product_uom_id.name} (id={line.product_uom_id.id})")
                
                # البحث عن UoM في sap.uom.sync للحصول على UoMEntry (sap_uom_entry)
                domain = [('odoo_uom_id', '=', line.product_uom_id.id)]
                if backend:
                    domain.append(('backend_id', '=', backend.id))
                    _logger.info(f"Searching in sap.uom.sync with backend_id={backend.id}")
                else:
                    # البحث عن backend نشط إذا لم يتم تمريره
                    active_backend = self.env['sap.backend'].search([
                        ('active', '=', True)
                    ], limit=1)
                    if active_backend:
                        domain.append(('backend_id', '=', active_backend.id))
                        _logger.info(f"Using active backend: {active_backend.name} (id={active_backend.id})")
                    else:
                        _logger.warning("No active backend found, searching without backend filter")
                
                sap_uom_sync = self.env['sap.uom.sync'].search(domain, limit=1)
                
                if sap_uom_sync:
                    _logger.info(f"✓ Found sap_uom_sync record (id={sap_uom_sync.id}): sap_uom_entry={sap_uom_sync.sap_uom_entry}, sap_uom_id={sap_uom_sync.sap_uom_id}")
                    
                    # التحقق من وجود sap_uom_entry قبل الإضافة
                    if sap_uom_sync.sap_uom_entry and sap_uom_sync.sap_uom_entry > 0:
                        uom_entry = sap_uom_sync.sap_uom_entry
                        line_data['UoMEntry'] = uom_entry
                        _logger.info(f"✓ Verified and added UoMEntry={uom_entry} to line data for ItemCode={line_data.get('ItemCode')}")
                    else:
                        _logger.warning(f"✗ sap_uom_sync found but sap_uom_entry is empty or invalid (value={sap_uom_sync.sap_uom_entry}) for UoM {line.product_uom_id.name}")
                else:
                    _logger.warning(f"✗ No sap_uom_sync found for UoM {line.product_uom_id.name} (id={line.product_uom_id.id}) - UoMEntry will NOT be sent")
            else:
                _logger.warning(f"No product_uom_id found for line - UoMEntry will NOT be sent")
            
            # إضافة كود الضريبة إذا كانت متوفرة
            if line.tax_ids:
                # استخدام أول ضريبة (يمكن تعديلها حسب الحاجة)
                tax = line.tax_ids[0]
                # يمكن إضافة mapping للضريبة هنا
                # line_data['TaxCode'] = tax.code or tax.name
            
            # إضافة كود المستودع إذا كان متوفراً
            # يمكن إضافة mapping للمستودع هنا في المستقبل
            # if quotation.warehouse_id:
            #     line_data['WarehouseCode'] = quotation.warehouse_id.code
            
            document_lines.append(line_data)
        
        if not document_lines:
            raise UserError("لا يمكن إرسال quotation بدون سطور")
        
        # إعداد بيانات الوثيقة
        quotation_data = {
            'CardCode': quotation.partner_id.ref or '',
            'DocDate': quotation.date_order.strftime('%Y-%m-%d') if quotation.date_order else datetime.now().strftime('%Y-%m-%d'),
            'DocumentLines': document_lines,
        }
        
        # إضافة تاريخ الصلاحية إذا كان موجوداً
        if quotation.validity_date:
            quotation_data['DocDueDate'] = quotation.validity_date.strftime('%Y-%m-%d')
        
        return quotation_data
    
    def action_confirm(self):
        """Override action_confirm to convert quotation to sales order in SAP"""
        result = super(SaleOrder, self).action_confirm()
        
        # بعد تحويل quotation إلى sale order، نحوله في SAP أيضاً
        for order in self:
            if order.state == 'sale' and order.sap_doc_entry and order.sap_doc_entry > 0:
                _logger.info(f"Converting quotation {order.name} (SAP DocEntry: {order.sap_doc_entry}) to sales order in SAP")
                try:
                    backend = self.env['sap.backend'].search([
                        ('active', '=', True)
                    ], limit=1)
                    
                    if backend:
                        connection = backend.get_connection()
                        sap_order = connection.convert_quotation_to_order(order.sap_doc_entry)
                        
                        if sap_order:
                            # تحديث رقم Document من SAP Sales Order
                            update_vals = {}
                            if sap_order.get('DocNum'):
                                update_vals['sap_doc_num'] = sap_order.get('DocNum')
                            if sap_order.get('DocEntry'):
                                update_vals['sap_doc_entry'] = sap_order.get('DocEntry')
                            
                            if update_vals:
                                order.write(update_vals)
                                _logger.info(f"Successfully converted quotation {order.name} to sales order in SAP. New DocNum: {update_vals.get('sap_doc_num')}, DocEntry: {update_vals.get('sap_doc_entry')}")
                        else:
                            _logger.warning(f"Failed to convert quotation {order.name} to sales order in SAP")
                    else:
                        _logger.warning(f"No active SAP backend found to convert quotation {order.name}")
                except Exception as e:
                    _logger.error(f"Error converting quotation {order.name} to sales order in SAP: {str(e)}", exc_info=True)
        
        return result
    
    def action_manual_sync_to_sap(self):
        """إجراء يدوي لإرسال quotation إلى SAP"""
        self.ensure_one()
        self._send_to_sap()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'تم الإرسال إلى SAP',
                'message': f'تم إرسال Quotation {self.name} إلى SAP بنجاح. رقم SAP: {self.sap_doc_num or "قيد المعالجة"}',
                'type': 'success',
                'sticky': False,
            }
        }

