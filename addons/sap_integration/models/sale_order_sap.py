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
    
    # Invoice Type (SAP User-Defined Field) - قيم ثابتة
    invoice_type = fields.Selection(
        string='نوع الفاتورة / Invoice Type',
        selection=[
            ('1', 'زبون محل'),
            ('2', 'شركات توصيل'),
            ('3', 'نقليات'),
            ('4', 'ديلفري'),
            ('5', 'NBS'),
            ('6', 'شورجة'),
            ('7', 'NA'),
            ('8', 'مكاتب الشورجة'),
        ],
        help="نوع الفاتورة الذي سيتم إرساله إلى SAP (U_InvType)\nالرقم يُرسل إلى SAP، والاسم يظهر في الواجهة"
    )
    
    @api.model
    def create(self, vals):
        """Override create to send quotation/sale order to SAP after creation"""
        order = super(SaleOrder, self).create(vals)
        
        _logger.info(f"=== Sale Order Created: {order.name}, state={order.state}, sap_synced={order.sap_synced}, partner={order.partner_id.name if order.partner_id else 'None'}, partner_ref={order.partner_id.ref if order.partner_id else 'None'}, order_lines_count={len(order.order_line)} ===")
        
        # إرسال إلى SAP بناءً على الحالة
        if not order.sap_synced:
            # التحقق من وجود بيانات كافية قبل الإرسال
            if order.partner_id and order.partner_id.ref and order.order_line:
                # إرسال إلى SAP بناءً على الحالة
                if order.state == 'draft':
                    _logger.info(f"Order {order.name} is draft, will be sent as Quotation to SAP")
                elif order.state == 'sale':
                    _logger.info(f"Order {order.name} is already confirmed (sale), will be sent as Sales Order to SAP")
                else:
                    _logger.info(f"Order {order.name} in state {order.state}, attempting to send to SAP")
                
                try:
                    order._send_to_sap()
                except Exception as e:
                    _logger.warning(f"Could not send order {order.name} to SAP on create: {e}")
            else:
                _logger.info(f"Conditions not met for order {order.name}: partner_id={order.partner_id is not None}, partner_ref={order.partner_id.ref if order.partner_id else None}, order_lines={len(order.order_line) if order.order_line else 0}")
        else:
            _logger.info(f"Order {order.name} already synced to SAP, skipping")
        
        return order
    
    def write(self, vals):
        """Override write to send quotation/sale order to SAP when needed"""
        # حفظ الحالة القديمة قبل الـ write
        old_states = {order.id: order.state for order in self}
        
        result = super(SaleOrder, self).write(vals)
        
        # تحديث في SAP إذا تم تحديث بيانات مهمة
        for order in self:
            # التحقق من وجود بيانات كافية قبل الإرسال
            if not order.partner_id or not order.partner_id.ref or not order.order_line:
                continue
            
            # التحقق إذا تم تغيير الحالة من draft إلى sale (تأكيد الطلب)
            state_changed_to_sale = (
                'state' in vals and 
                vals['state'] == 'sale' and 
                old_states.get(order.id) == 'draft' and
                order.sap_doc_entry and 
                order.sap_doc_entry > 0
            )
            
            if state_changed_to_sale:
                # تحويل Quotation إلى Sales Order في SAP
                _logger.info(f"State changed from draft to sale for {order.name}, converting quotation to sales order in SAP (DocEntry: {order.sap_doc_entry})")
                try:
                    backend = self.env['sap.backend'].search([('active', '=', True)], limit=1)
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
                                # استخدام sudo().write لتجنب إعادة استدعاء write
                                order.sudo().write(update_vals)
                                _logger.info(f"✅ Successfully converted quotation {order.name} to sales order in SAP. New DocNum: {update_vals.get('sap_doc_num')}, DocEntry: {update_vals.get('sap_doc_entry')}")
                        else:
                            _logger.warning(f"Failed to convert quotation {order.name} to sales order in SAP")
                    else:
                        _logger.warning(f"No active SAP backend found to convert quotation {order.name}")
                except Exception as e:
                    _logger.error(f"Error converting quotation {order.name} to sales order in SAP: {str(e)}", exc_info=True)
                
                # بعد التحويل، لا نحتاج لتحديث إضافي
                continue
            
            # إذا تم تحديث بيانات مهمة (وليس فقط تغيير الحالة)
            # ملاحظة: أضفنا invoice_type و note حتى يتم إرسال نوع الفاتورة والملاحظات
            # أيضاً عند التعديل، وليس فقط عند الإرسال لأول مرة.
            if any(field in vals for field in [
                'partner_id',
                'order_line',
                'date_order',
                'validity_date',
                'price_unit',
                'discount',
                'product_uom_qty',
                'invoice_type',
                'note',
            ]):
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
        """إرسال quotation/sale order إلى SAP ومزامنته"""
        for quotation in self:
            # تحديد نوع المستند للّوج فقط (Quotation vs Sale Order)
            if quotation.state == 'sale':
                doc_type = "sale order"
                doc_label = "Sale Order"
            elif quotation.state == 'draft':
                doc_type = "quotation (draft)"
                doc_label = "Quotation"
            else:
                doc_type = "quotation"
                doc_label = "Quotation"

            _logger.info(f">>> Starting _send_to_sap for {doc_type} {quotation.name} <<<")
            sync_successful = False
            
            # Log invoice_type if present
            if quotation.invoice_type:
                _logger.info(f"[SAP Sync] {doc_label} {quotation.name} has invoice_type: {quotation.invoice_type}")
            else:
                _logger.info(f"[SAP Sync] {doc_label} {quotation.name} has NO invoice_type")
            
            try:
                # التحقق من وجود backend نشط
                backend = self.env['sap.backend'].search([
                    ('active', '=', True)
                ], limit=1)
                
                if not backend:
                    error_msg = f"❌ No active SAP backend found for quotation {quotation.name}"
                    _logger.error(error_msg)
                    quotation.sudo().write({'sap_synced': False})
                    return
                
                _logger.info(f"Found active SAP backend: {backend.name} (id={backend.id})")
                
                # التحقق من وجود partner مع CardCode
                if not quotation.partner_id or not quotation.partner_id.ref:
                    error_msg = f"❌ Quotation {quotation.name} has no partner with CardCode (ref). Partner: {quotation.partner_id.name if quotation.partner_id else 'None'}"
                    _logger.error(error_msg)
                    quotation.sudo().write({'sap_synced': False})
                    return
                
                _logger.info(f"Partner found: {quotation.partner_id.name}, CardCode={quotation.partner_id.ref}")
                
                # التحقق من وجود order lines
                if not quotation.order_line:
                    error_msg = f"❌ Quotation {quotation.name} has no order lines"
                    _logger.error(error_msg)
                    quotation.sudo().write({'sap_synced': False})
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
                        # لا نرسل CardCode عند تحديث Sales Order لأنه لا يمكن تعديله في SAP
                        if 'CardCode' in quotation_data:
                            _logger.info(f"Removing CardCode from update payload for sale order {quotation.name} to avoid ODBC -1029")
                            quotation_data.pop('CardCode', None)
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
                                error_msg = f"❌ Could not update sale order {quotation.name} in SAP: {response.status_code} - {response.text}"
                                _logger.error(error_msg)
                                result = None
                                quotation.sudo().write({'sap_synced': False})
                        except Exception as e:
                            error_msg = f"❌ Error updating sale order {quotation.name} in SAP: {e}"
                            _logger.error(error_msg, exc_info=True)
                            result = None
                            quotation.sudo().write({'sap_synced': False})
                    else:
                        # إنشاء sale order جديد في SAP (نادر الحدوث)
                        _logger.info(f"Creating sale order {quotation.name} in SAP")
                        url = f"{connection.base_url}/Orders"
                        headers = connection._get_headers()
                        response = connection.session.post(url, json=quotation_data, headers=headers, timeout=30)
                        if response.status_code in [200, 201]:
                            result = response.json() if response.content else {}
                        else:
                            error_msg = f"❌ Error creating sale order {quotation.name} in SAP: {response.status_code} - {response.text}"
                            _logger.error(error_msg)
                            result = None
                            quotation.sudo().write({'sap_synced': False})
                    
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
                            sync_successful = True
                else:
                    # للـ draft orders: إرسال كـ Quotation في SAP (لأن Quotations يمكن أن تكون Draft)
                    if quotation.state == 'draft':
                        # إنشاء Quotation في SAP (يمكن أن يكون Draft status)
                        _logger.info(f"Creating quotation (draft) {quotation.name} in SAP")
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
                            
                            # Log success with invoice type info if present
                            inv_type_info = ""
                            if quotation.invoice_type:
                                inv_type_info = f", InvoiceType={quotation.invoice_type} (U_InvType sent to SAP)"
                            _logger.info(f"✅ Quotation (draft) {quotation.name} synced to SAP: DocNum={doc_num}, DocEntry={doc_entry}{inv_type_info}")
                            sync_successful = True
                        else:
                            error_msg = f"❌ Failed to create quotation {quotation.name} in SAP: create_quotation returned None or empty result. Check SAP logs for details."
                            _logger.error(error_msg)
                            # تعيين sap_synced = False بشكل صريح عند الفشل
                            quotation.sudo().write({'sap_synced': False})
                            # رفع exception لضمان تسجيل الخطأ بشكل واضح
                            raise Exception(error_msg)
                    else:
                        # للـ quotations الأخرى: تحديث أو إنشاء quotation في SAP
                        if quotation.sap_doc_entry and quotation.sap_doc_entry > 0:
                            # تحديث quotation موجود
                            _logger.info(f"Updating quotation {quotation.name} in SAP (DocEntry: {quotation.sap_doc_entry})")
                            result = connection.update_quotation(quotation.sap_doc_entry, quotation_data)
                            if result and result.get('DocEntry'):
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
                                    sync_successful = True
                            else:
                                error_msg = f"❌ Failed to update quotation {quotation.name} in SAP: update_quotation returned None or invalid result"
                                _logger.error(error_msg)
                                quotation.sudo().write({'sap_synced': False})
                                raise Exception(error_msg)
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
                                
                                # Log success with invoice type info if present
                                inv_type_info = ""
                                if quotation.invoice_type:
                                    inv_type_info = f", InvoiceType={quotation.invoice_type} (U_InvType sent to SAP)"
                                _logger.info(f"✅ Quotation {quotation.name} synced to SAP: DocNum={doc_num}, DocEntry={doc_entry}{inv_type_info}")
                                sync_successful = True
                            else:
                                error_msg = f"❌ Failed to create quotation {quotation.name} in SAP: create_quotation returned None or empty result. Check SAP logs for details."
                                _logger.error(error_msg)
                                # تعيين sap_synced = False بشكل صريح عند الفشل
                                quotation.sudo().write({'sap_synced': False})
                                # رفع exception لضمان تسجيل الخطأ بشكل واضح
                                raise Exception(error_msg)
                
            except Exception as e:
                error_msg = f"❌ Error sending quotation {quotation.name} to SAP: {str(e)}"
                _logger.error(error_msg, exc_info=True)
                sync_successful = False
                # تعيين sap_synced = False بشكل صريح عند الفشل
                try:
                    quotation.sudo().write({'sap_synced': False})
                except Exception as write_error:
                    _logger.error(f"Failed to update sap_synced for quotation {quotation.name}: {str(write_error)}")
                # لا نرفع exception حتى لا نمنع حفظ الـ quotation في Odoo
                # يمكن إضافة notification للمستخدم هنا
            finally:
                # Log final status
                if sync_successful:
                    _logger.info(f"<<< Completed _send_to_sap for {doc_type} {quotation.name}: SUCCESS >>>")
                else:
                    _logger.error(f"<<< Completed _send_to_sap for {doc_type} {quotation.name}: FAILED - Check errors above >>>")
    
    def _prepare_quotation_data_for_sap(self, quotation, backend=None):
        """إعداد بيانات quotation للـ SAP Service Layer"""
        # إعداد سطور الوثيقة
        document_lines = []
        for line in quotation.order_line:
            if not line.product_id:
                continue
            
            # الحصول على ItemCode (كود المنتج) - أولوية: default_code ثم barcode
            item_code = line.product_id.default_code or ''
            if not item_code and line.product_id.barcode:
                item_code = line.product_id.barcode
                _logger.info(f"Using barcode as ItemCode for product {line.product_id.name}: {item_code}")
            
            if not item_code:
                _logger.warning(f"Product {line.product_id.name} (ID: {line.product_id.id}) has no default_code or barcode - ItemCode will be empty!")
            
            # إعداد بيانات السطر الأساسية
            line_data = {
                'ItemCode': item_code,
                'Quantity': line.product_uom_qty,
                'UnitPrice': line.price_unit,
                'DiscountPercent': line.discount,
            }
            
            # إضافة ItemDescription إذا تم تعديل اسم المنتج
            if hasattr(line, 'custom_product_name') and line.custom_product_name:
                line_data['ItemDescription'] = line.custom_product_name
                _logger.info(f"Using custom product name for ItemDescription: {line.custom_product_name}")
            
            _logger.info(f"Preparing DocumentLine: ItemCode={item_code}, Quantity={line.product_uom_qty}")
            
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
            
            # إضافة كود المستودع (WarehouseCode) من Sale Line
            warehouse_code = None
            
            # 1. محاولة الحصول من order line (product_warehouse_id من sale_order_line_multi_warehouse)
            if hasattr(line, 'product_warehouse_id') and line.product_warehouse_id:
                warehouse = line.product_warehouse_id
                _logger.info(f"Found warehouse in order line: {warehouse.name} (ID: {warehouse.id})")
                
                # البحث عن sap_warehouse_code من sap.product.warehouse.info
                if backend:
                    warehouse_info = self.env['sap.product.warehouse.info'].search([
                        ('warehouse_id', '=', warehouse.id),
                        ('backend_id', '=', backend.id)
                    ], limit=1)
                    if warehouse_info and warehouse_info.sap_warehouse_code:
                        warehouse_code = warehouse_info.sap_warehouse_code
                        _logger.info(f"Found WarehouseCode from sap.product.warehouse.info: {warehouse_code}")
                    elif warehouse.code:
                        # استخدام code من warehouse إذا لم يوجد في sap.product.warehouse.info
                        warehouse_code = warehouse.code
                        _logger.info(f"Using warehouse code as WarehouseCode: {warehouse_code}")
                else:
                    # إذا لم يكن backend متوفراً، استخدام warehouse.code مباشرة
                    if warehouse.code:
                        warehouse_code = warehouse.code
                        _logger.info(f"Using warehouse code directly (no backend): {warehouse_code}")
            
            # 2. إذا لم يوجد في order line، استخدام warehouse من quotation
            if not warehouse_code and quotation.warehouse_id:
                warehouse = quotation.warehouse_id
                _logger.info(f"Using warehouse from quotation: {warehouse.name} (ID: {warehouse.id})")
                
                # البحث عن sap_warehouse_code من sap.product.warehouse.info
                if backend:
                    warehouse_info = self.env['sap.product.warehouse.info'].search([
                        ('warehouse_id', '=', warehouse.id),
                        ('backend_id', '=', backend.id)
                    ], limit=1)
                    if warehouse_info and warehouse_info.sap_warehouse_code:
                        warehouse_code = warehouse_info.sap_warehouse_code
                        _logger.info(f"Found WarehouseCode from quotation warehouse: {warehouse_code}")
                    elif warehouse.code:
                        # استخدام code من warehouse إذا لم يوجد في sap.product.warehouse.info
                        warehouse_code = warehouse.code
                        _logger.info(f"Using quotation warehouse code as WarehouseCode: {warehouse_code}")
                else:
                    # إذا لم يكن backend متوفراً، استخدام warehouse.code مباشرة
                    if warehouse.code:
                        warehouse_code = warehouse.code
                        _logger.info(f"Using quotation warehouse code directly (no backend): {warehouse_code}")
            
            # 3. إضافة WarehouseCode إلى line_data إذا كان موجوداً
            if warehouse_code:
                line_data['WarehouseCode'] = warehouse_code
                _logger.info(f"✓ Added WarehouseCode={warehouse_code} to DocumentLine for ItemCode={line_data.get('ItemCode')}")
            else:
                _logger.warning(f"✗ No WarehouseCode found for DocumentLine - ItemCode={line_data.get('ItemCode')}")
            
            document_lines.append(line_data)
        
        if not document_lines:
            raise UserError("لا يمكن إرسال quotation بدون سطور")
        
        # Log all document lines before sending
        _logger.info(f"=== Prepared {len(document_lines)} DocumentLines for SAP ===")
        for idx, line in enumerate(document_lines):
            _logger.info(f"DocumentLine[{idx}]: ItemCode='{line.get('ItemCode')}', Quantity={line.get('Quantity')}, UnitPrice={line.get('UnitPrice')}, UoMEntry={line.get('UoMEntry', 'NOT SET')}, WarehouseCode={line.get('WarehouseCode', 'NOT SET')}")
        _logger.info("=== End of DocumentLines ===")
        
        # إعداد بيانات الوثيقة
        # ملاحظة: لا نرسل DocDate إلى SAP حتى لا نصطدم برسالة
        # "Series period does not match current period" عند تحديث مستندات
        # قديمة ضمن Series مرتبط بفترة مختلفة. SAP سيستخدم التاريخ
        # الافتراضي أو تاريخ المستند الأصلي في النظام.
        quotation_data = {
            'CardCode': quotation.partner_id.ref or '',
            'DocumentLines': document_lines,
        }
        
        # إعداد Comments (الملاحظات) - بدون إضافة نوع الفاتورة
        comments_parts = []
        
        # إضافة ملاحظات Odoo إذا كانت موجودة
        if quotation.note:
            comments_parts.append(quotation.note.strip())
            _logger.info(f"[Invoice Type] Note from sale.order {quotation.name}: {quotation.note[:100]}")
        
        # إضافة نوع الفاتورة (User-Defined Field) إلى U_InvType فقط
        if quotation.invoice_type:
            try:
                # قيمة invoice_type هي رقم SAP (مثلاً "1", "2", "3", ...)
                invoice_type_id = str(quotation.invoice_type).strip()
                
                # قائمة الأسماء العربية الثابتة (للـ logging فقط)
                invoice_type_labels = {
                    '1': 'زبون محل',
                    '2': 'شركات توصيل',
                    '3': 'نقليات',
                    '4': 'ديلفري',
                    '5': 'NBS',
                    '6': 'شورجة',
                    '7': 'NA',
                    '8': 'مكاتب الشورجة',
                }
                invoice_type_label = invoice_type_labels.get(invoice_type_id, invoice_type_id)
                
                # إرسال رقم نوع الفاتورة إلى حقل U_InvType في SAP فقط
                quotation_data['U_InvType'] = invoice_type_id
                _logger.info(f"[Invoice Type] Setting U_InvType={invoice_type_id} ({invoice_type_label}) for sale.order {quotation.name}")
                
            except Exception as e:
                _logger.error(
                    f"[Invoice Type] ERROR adding invoice type to SAP quotation from sale.order {quotation.name}: {str(e)}",
                    exc_info=True
                )
                # لا نرفع exception حتى لا نمنع إرسال الـ quotation
        
        # دمج جميع أجزاء Comments (الملاحظات فقط) في حقل واحد
        if comments_parts:
            quotation_data['Comments'] = "\n".join(comments_parts)
            _logger.info(
                f"[Invoice Type] Final Comments for sale.order {quotation.name}: "
                f"U_InvType={quotation_data.get('U_InvType', 'NOT SET')}, "
                f"Comments length={len(quotation_data['Comments'])}"
            )
        
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


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    # Custom product name for invoice/report display and SAP ItemDescription
    custom_product_name = fields.Char(
        string='Custom Product Name (Invoice Only)',
        help='Custom product name to display in invoice/report. If set, this name will be used in the report and sent to SAP as ItemDescription. The original product name remains unchanged.'
    )


