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
    sap_error_message = fields.Text(
        string='SAP Error Message',
        copy=False,
        help="آخر رسالة خطأ من SAP"
    )
    sap_last_sync_date = fields.Datetime(
        string='Last SAP Sync',
        copy=False,
        help="آخر محاولة مزامنة مع SAP"
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
        
        # لا نُرسل إلى SAP تلقائياً هنا.
        # الـ POS JS يتحكم بالإرسال صراحةً:
        #   - createQuotation   → action_sync_as_quotation  (Quotation)
        #   - confirmSaleOrder  → action_manual_sync_to_sap (Sales Order)
        # هذا يمنع الإرسال المزدوج أو الإرسال بنوع خاطئ.
        _logger.info(f"[SAP] Order {order.name} created — SAP sync deferred to explicit JS call.")
        
        return order
    
    def write(self, vals):
        """Override write to send quotation/sale order to SAP when needed"""
        # Re-entrancy guard: if write contains ONLY SAP internal tracking fields,
        # skip auto-sync to prevent infinite loop (write → _send_to_sap → write → ...)
        sap_internal_fields = {'sap_synced', 'sap_doc_num', 'sap_doc_entry',
                               'sap_error_message', 'sap_last_sync_date'}
        if set(vals.keys()).issubset(sap_internal_fields):
            return super(SaleOrder, self).write(vals)

        # حفظ الحالة القديمة قبل الـ write
        old_states = {order.id: order.state for order in self}
        
        result = super(SaleOrder, self).write(vals)
        
        # تحديث في SAP إذا تم تحديث بيانات مهمة
        for order in self:
            # التحقق من وجود بيانات كافية قبل الإرسال
            if not order.partner_id or not order.partner_id.ref or not order.order_line:
                continue
            
            # Log للتشخيص
            _logger.info(f"🔍 [DIAGNOSIS] Order {order.name}: current_state={order.state}, vals={vals}, old_state={old_states.get(order.id)}, sap_doc_entry={order.sap_doc_entry}")
            
            # التحقق إذا تم تغيير الحالة من draft إلى sale (تأكيد الطلب)
            state_changed_to_sale = (
                'state' in vals and 
                vals['state'] == 'sale' and 
                old_states.get(order.id) == 'draft' and
                order.sap_doc_entry and 
                order.sap_doc_entry > 0
            )
            
            _logger.info(f"🔍 [DIAGNOSIS] state_changed_to_sale={state_changed_to_sale} ('state' in vals={('state' in vals)}, vals.get('state')={vals.get('state')}, old={old_states.get(order.id)}, doc_entry={order.sap_doc_entry})")
            
            if state_changed_to_sale:
                # تغيّرت الحالة إلى 'sale' — لكن الـ POS JS يتحكم بالإرسال إلى SAP صراحةً
                # عبر confirmSaleOrder → action_manual_sync_to_sap
                # لذا لا نُرسل هنا تلقائياً حتى نتجنب إرسال نفس الطلب مرتين أو بنوع خاطئ
                _logger.info(f"🔍 [DIAGNOSIS] state_changed_to_sale for {order.name} — skipping auto-SAP-sync (JS handles this explicitly)")
                continue
            
            # إذا تم تحديث بيانات مهمة (وليس فقط تغيير الحالة)
            # ملاحظة: أضفنا invoice_type و note حتى يتم إرسال نوع الفاتورة والملاحظات
            # أيضاً عند التعديل، وليس فقط عند الإرسال لأول مرة.
            if any(field in vals for field in [
                'partner_id',
                'date_order',
                'validity_date',
                'price_unit',
                'discount',
                'product_uom_qty',
                'invoice_type',
                'note',
                'order_line',  # يشمل تغييرات الأسطر: اسم المنتج، الكمية، السعر، الحذف
            ]):
                # للـ quotations (draft) فقط: إرسال أو تحديث تلقائي
                # السيل اوردر (sale) لا يُرسل تلقائياً — JS يتحكم بهذا صراحةً
                if order.state == 'draft':
                    if not order.sap_synced:
                        try:
                            order._send_to_sap()
                        except Exception as e:
                            _logger.warning(f"Could not send quotation {order.name} to SAP on write: {e}")
                    elif order.sap_doc_entry:
                        try:
                            order._send_to_sap()
                        except Exception as e:
                            _logger.warning(f"Could not update quotation {order.name} in SAP on write: {e}")
                # sale orders: JS handles sync explicitly via action_manual_sync_to_sap
        
        return result
    
    def action_sync_as_quotation(self):
        """
        إرسال/تحديث المستند في SAP كـ Quotation بغض النظر عن حالته في Odoo.
        يُستخدم من زر "Quotation" في POS Perfume.
        """
        self.ensure_one()
        try:
            self._send_to_sap(force_as_quotation=True)
        except Exception as e:
            raise UserError(f'فشل إرسال Quotation إلى SAP:\n{str(e)}')

        # Flush ORM cache so DB query sees latest written values
        self.env.cr.flush()
        self.env.cr.execute(
            "SELECT sap_synced, sap_error_message FROM sale_order WHERE id=%s",
            (self.id,)
        )
        row = self.env.cr.fetchone()
        synced = row[0] if row else False
        error_msg = row[1] if row else ''

        if synced:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'تم الإرسال',
                    'message': f'✅ تم إرسال Quotation {self.name} إلى SAP بنجاح!',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise UserError(
                f'فشل إرسال Quotation {self.name} إلى SAP.\n\n'
                f'السبب:\n{error_msg or "خطأ غير معروف"}'
            )

    def _send_to_sap(self, force_as_quotation=False):
        """إرسال quotation/sale order إلى SAP ومزامنته.
        force_as_quotation=True: يُرسل دائماً كـ Quotation بغض النظر عن state.
        """
        for quotation in self:
            # تحديد نوع المستند — force_as_quotation يُجبر الإرسال كـ Quotation
            if force_as_quotation:
                doc_type = "quotation"
                doc_label = "Quotation"
                send_as_sale = False
            elif quotation.state == 'sale':
                doc_type = "sale order"
                doc_label = "Sale Order"
                send_as_sale = True
            elif quotation.state == 'draft':
                doc_type = "quotation (draft)"
                doc_label = "Quotation"
                send_as_sale = False
            else:
                doc_type = "quotation"
                doc_label = "Quotation"
                send_as_sale = False

            _logger.info(f">>> Starting _send_to_sap for {doc_type} {quotation.name} (send_as_sale={send_as_sale}) <<<")
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
                    quotation.sudo().write({
                        'sap_synced': False,
                        'sap_error_message': 'لا يوجد SAP backend نشط',
                        'sap_last_sync_date': fields.Datetime.now()
                    })
                    return
                
                _logger.info(f"Found active SAP backend: {backend.name} (id={backend.id})")
                
                # التحقق من وجود partner مع CardCode
                if not quotation.partner_id or not quotation.partner_id.ref:
                    error_msg = f"❌ Quotation {quotation.name} has no partner with CardCode (ref). Partner: {quotation.partner_id.name if quotation.partner_id else 'None'}"
                    _logger.error(error_msg)
                    quotation.sudo().write({
                        'sap_synced': False,
                        'sap_error_message': f'العميل ({quotation.partner_id.name if quotation.partner_id else "غير موجود"}) ليس لديه CardCode في SAP',
                        'sap_last_sync_date': fields.Datetime.now()
                    })
                    return
                
                _logger.info(f"Partner found: {quotation.partner_id.name}, CardCode={quotation.partner_id.ref}")
                
                # التحقق من وجود order lines
                if not quotation.order_line:
                    error_msg = f"❌ Quotation {quotation.name} has no order lines"
                    _logger.error(error_msg)
                    quotation.sudo().write({
                        'sap_synced': False,
                        'sap_error_message': 'الفاتورة لا تحتوي على منتجات',
                        'sap_last_sync_date': fields.Datetime.now()
                    })
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

                # تحديد نوع الوثيقة في SAP:
                # send_as_sale=True  → Sales Order (POST /Orders)
                # send_as_sale=False → Quotation  (POST/PATCH /Quotations)
                if send_as_sale:
                    # تأكد من صلاحية الـ session قبل أي طلب
                    connection._ensure_session()
                    headers = connection._get_headers()

                    if quotation.sap_doc_entry and quotation.sap_doc_entry > 0:
                        # sap_doc_entry موجود — نتحقق من SAP هل هو Order أم Quotation
                        _logger.info(f"[SAP] {quotation.name}: sap_doc_entry={quotation.sap_doc_entry} — checking if it is an Order or Quotation in SAP")

                        # أولاً: هل هو Sales Order موجود؟
                        order_check_url = f"{connection.base_url}/Orders({quotation.sap_doc_entry})?$select=DocEntry,DocNum"
                        order_check = connection.session.get(order_check_url, headers=headers, timeout=30)
                        order_doc = order_check.json() if order_check.status_code == 200 and order_check.content else {}
                        order_doc_num = str(order_doc.get('DocNum', '')) if order_doc else ''
                        expected_doc_num = str(quotation.sap_doc_num or '')
                        is_existing_order = (
                            order_check.status_code == 200 and
                            (not expected_doc_num or order_doc_num == expected_doc_num)
                        )
                        _logger.info(
                            f"[SAP] Order check status={order_check.status_code} for DocEntry={quotation.sap_doc_entry}, "
                            f"returned DocNum={order_doc_num or 'N/A'}, expected DocNum={expected_doc_num or 'N/A'}, "
                            f"match={is_existing_order}"
                        )

                        if is_existing_order:
                            # ✅ Sales Order موجود بالفعل في SAP → نُحدِّثه مع معالجة الأسطر المحذوفة
                            _logger.info(f"[SAP] {quotation.name}: Found existing Sales Order (DocEntry={quotation.sap_doc_entry}) — updating via update_order")

                            # بناء قائمة الأسطر الحالية في Odoo لكشف الأسطر المحذوفة
                            # نستخدم نفس الفلتر المستخدم في _prepare_quotation_data_for_sap
                            # (تخطي الأسطر بكمية 0 أو سالبة — تُعامَل كمحذوفة في SAP)
                            odoo_lines_info = [
                                {
                                    'item_code': (line.product_id.default_code or line.product_id.barcode or ''),
                                    'sap_line_num': line.sap_line_num,
                                }
                                for line in quotation.order_line
                                if line.product_id and line.product_uom_qty > 0
                            ]
                            _logger.info(f"[SAP] {quotation.name}: odoo_lines_info={[l['item_code'] for l in odoo_lines_info]}")

                            result = connection.update_order(
                                quotation.sap_doc_entry,
                                quotation_data,
                                existing_odoo_lines=odoo_lines_info,
                            )

                            if result is not None:
                                _logger.info(f"✅ SAP Sales Order updated for {quotation.name}: DocEntry={quotation.sap_doc_entry}")
                                quotation.sudo().write({
                                    'sap_synced': True,
                                    'sap_error_message': False,
                                    'sap_last_sync_date': fields.Datetime.now(),
                                })
                                quotation._sync_sap_fields_to_pos_order(
                                    sap_doc_num=quotation.sap_doc_num,
                                    sap_doc_entry=quotation.sap_doc_entry,
                                )
                                # تحديث LineNums بعد التعديل
                                try:
                                    self._store_sap_line_nums(quotation, connection, doc_type='Orders')
                                except Exception:
                                    pass
                                sync_successful = True
                            else:
                                error_msg = f"❌ Failed to update SAP Sales Order for {quotation.name}: update_order returned None"
                                _logger.error(error_msg)
                                quotation.sudo().write({
                                    'sap_synced': False,
                                    'sap_error_message': error_msg[:500],
                                    'sap_last_sync_date': fields.Datetime.now(),
                                })

                        else:
                            # ثانياً: ليس Order — هل هو Quotation؟
                            quote_check_url = f"{connection.base_url}/Quotations({quotation.sap_doc_entry})?$select=DocEntry,DocNum"
                            quote_check = connection.session.get(quote_check_url, headers=headers, timeout=30)
                            quote_doc = quote_check.json() if quote_check.status_code == 200 and quote_check.content else {}
                            quote_doc_num = str(quote_doc.get('DocNum', '')) if quote_doc else ''
                            expected_doc_num = str(quotation.sap_doc_num or '')
                            is_existing_quotation = (
                                quote_check.status_code == 200 and
                                (not expected_doc_num or quote_doc_num == expected_doc_num)
                            )
                            _logger.info(
                                f"[SAP] Quotation check status={quote_check.status_code} for DocEntry={quotation.sap_doc_entry}, "
                                f"returned DocNum={quote_doc_num or 'N/A'}, expected DocNum={expected_doc_num or 'N/A'}, "
                                f"match={is_existing_quotation}"
                            )

                            if is_existing_quotation:
                                # ✅ Quotation موجود → نُحدِّثه ثم نُحوِّله لـ Sales Order
                                _logger.info(f"Converting quotation {quotation.name} to SAP Sales Order (QuotationDocEntry: {quotation.sap_doc_entry})")
                                try:
                                    # أولاً: نُحدِّث بيانات الـ Quotation
                                    patch_data = quotation_data.copy()
                                    patch_data.pop('CardCode', None)
                                    patch_url = f"{connection.base_url}/Quotations({quotation.sap_doc_entry})"
                                    patch_resp = connection.session.patch(patch_url, json=patch_data, headers=headers, timeout=30)
                                    if patch_resp.status_code not in [200, 204]:
                                        _logger.warning(f"⚠️ PATCH Quotation returned {patch_resp.status_code}: {patch_resp.text[:300]}")
                                    else:
                                        _logger.info(f"✅ Quotation updated successfully before conversion")

                                    # ننشئ Sales Order مرتبطاً بالـ Quotation
                                    order_lines = []
                                    for idx, line in enumerate(quotation_data.get('DocumentLines', [])):
                                        order_line = line.copy()
                                        order_line['BaseType'] = 23
                                        order_line['BaseEntry'] = quotation.sap_doc_entry
                                        order_line['BaseLine'] = idx
                                        order_lines.append(order_line)

                                    order_data = quotation_data.copy()
                                    order_data['DocumentLines'] = order_lines
                                    _logger.info(f"Creating SAP Sales Order linked to Quotation DocEntry={quotation.sap_doc_entry}")

                                    create_url = f"{connection.base_url}/Orders"
                                    create_resp = connection.session.post(create_url, json=order_data, headers=headers, timeout=30)

                                    if create_resp.status_code in [200, 201]:
                                        result = create_resp.json()
                                        update_vals = {
                                            'sap_synced': True,
                                            'sap_error_message': False,
                                            'sap_last_sync_date': fields.Datetime.now(),
                                        }
                                        if result.get('DocNum'):
                                            update_vals['sap_doc_num'] = result.get('DocNum')
                                        if result.get('DocEntry'):
                                            update_vals['sap_doc_entry'] = result.get('DocEntry')
                                        quotation.sudo().write(update_vals)
                                        quotation._sync_sap_fields_to_pos_order(
                                            sap_doc_num=update_vals.get('sap_doc_num'),
                                            sap_doc_entry=update_vals.get('sap_doc_entry'),
                                        )
                                        _logger.info(f"✅ SAP Sales Order created for {quotation.name}: DocNum={update_vals.get('sap_doc_num')}, DocEntry={update_vals.get('sap_doc_entry')}")
                                        sync_successful = True
                                    else:
                                        error_msg = f"❌ Failed to create SAP Sales Order for {quotation.name}: {create_resp.status_code} - {create_resp.text}"
                                        _logger.error(error_msg)
                                        quotation.sudo().write({
                                            'sap_synced': False,
                                            'sap_error_message': error_msg,
                                            'sap_last_sync_date': fields.Datetime.now(),
                                        })
                                except Exception as e:
                                    error_msg = f"❌ Error converting quotation {quotation.name} to SAP Sales Order: {e}"
                                    _logger.error(error_msg, exc_info=True)
                                    quotation.sudo().write({
                                        'sap_synced': False,
                                        'sap_error_message': str(e),
                                        'sap_last_sync_date': fields.Datetime.now(),
                                    })
                            else:
                                # الـ DocEntry لا يوجد في SAP (لا Order ولا Quotation) → ننشئ Order جديد
                                _logger.warning(f"DocEntry {quotation.sap_doc_entry} not found in SAP (neither Order nor Quotation), creating standalone Order")
                                url = f"{connection.base_url}/Orders"
                                response = connection.session.post(url, json=quotation_data, headers=headers, timeout=30)
                                if response.status_code in [200, 201]:
                                    result = response.json() if response.content else {}
                                    update_vals = {}
                                    if result.get('DocNum'):
                                        update_vals['sap_doc_num'] = result.get('DocNum')
                                    if result.get('DocEntry'):
                                        update_vals['sap_doc_entry'] = result.get('DocEntry')
                                    if update_vals:
                                        update_vals['sap_synced'] = True
                                        update_vals['sap_error_message'] = False
                                        update_vals['sap_last_sync_date'] = fields.Datetime.now()
                                        quotation.sudo().write(update_vals)
                                        quotation._sync_sap_fields_to_pos_order(
                                            sap_doc_num=update_vals.get('sap_doc_num'),
                                            sap_doc_entry=update_vals.get('sap_doc_entry'),
                                        )
                                        _logger.info(f"✅ SAP Sales Order created for {quotation.name}: DocNum={update_vals.get('sap_doc_num')}")
                                        sync_successful = True
                                else:
                                    error_msg = f"❌ Error creating SAP Sales Order for {quotation.name}: {response.status_code} - {response.text}"
                                    _logger.error(error_msg)
                                    quotation.sudo().write({
                                        'sap_synced': False,
                                        'sap_error_message': error_msg[:500],
                                        'sap_last_sync_date': fields.Datetime.now(),
                                    })
                    else:
                        # لا يوجد sap_doc_entry → ننشئ Sales Order جديد مباشرة
                        _logger.info(f"Creating new SAP Sales Order for {quotation.name} (no prior SAP document)")
                        url = f"{connection.base_url}/Orders"
                        response = connection.session.post(url, json=quotation_data, headers=headers, timeout=30)
                        if response.status_code in [200, 201]:
                            result = response.json() if response.content else {}
                            update_vals = {}
                            if result.get('DocNum'):
                                update_vals['sap_doc_num'] = result.get('DocNum')
                            if result.get('DocEntry'):
                                update_vals['sap_doc_entry'] = result.get('DocEntry')
                            if update_vals:
                                update_vals['sap_synced'] = True
                                update_vals['sap_error_message'] = False
                                update_vals['sap_last_sync_date'] = fields.Datetime.now()
                                quotation.sudo().write(update_vals)
                                quotation._sync_sap_fields_to_pos_order(
                                    sap_doc_num=update_vals.get('sap_doc_num'),
                                    sap_doc_entry=update_vals.get('sap_doc_entry'),
                                )
                                _logger.info(f"✅ SAP Sales Order created for {quotation.name}: DocNum={update_vals.get('sap_doc_num')}, DocEntry={update_vals.get('sap_doc_entry')}")
                                sync_successful = True
                        else:
                            error_msg = f"❌ Error creating SAP Sales Order for {quotation.name}: {response.status_code} - {response.text}"
                            _logger.error(error_msg)
                            quotation.sudo().write({
                                'sap_synced': False,
                                'sap_error_message': error_msg,
                                'sap_last_sync_date': fields.Datetime.now(),
                            })
                else:
                    # للـ quotations (draft or quotation state): تحديث أو إنشاء quotation في SAP
                    if quotation.sap_doc_entry and quotation.sap_doc_entry > 0:
                        # تحديث quotation موجود في SAP — مع إغلاق الأسطر المحذوفة
                        _logger.info(f"Updating existing quotation {quotation.name} in SAP (DocEntry: {quotation.sap_doc_entry})")

                        # نستخدم نفس الفلتر: تخطي الأسطر بكمية 0 (تُعامَل كمحذوفة)
                        odoo_lines_info = [
                            {
                                'item_code': (line.product_id.default_code or line.product_id.barcode or ''),
                                'sap_line_num': line.sap_line_num,
                            }
                            for line in quotation.order_line
                            if line.product_id and line.product_uom_qty > 0
                        ]

                        result = connection.update_quotation(
                            quotation.sap_doc_entry,
                            quotation_data,
                            existing_odoo_lines=odoo_lines_info,
                        )

                        if result is not None:
                            quotation.sudo().write({
                                'sap_synced': True,
                                'sap_error_message': False,
                                'sap_last_sync_date': fields.Datetime.now(),
                            })
                            quotation._sync_sap_fields_to_pos_order(
                                sap_doc_num=quotation.sap_doc_num,
                                sap_doc_entry=quotation.sap_doc_entry,
                            )
                            _logger.info(f"✅ Quotation {quotation.name} updated in SAP (DocEntry: {quotation.sap_doc_entry})")
                            # Refresh LineNums after update
                            try:
                                self._store_sap_line_nums(quotation, connection)
                            except Exception:
                                pass
                            sync_successful = True
                        else:
                            error_msg = f"❌ Failed to update quotation {quotation.name} in SAP: update_quotation returned None"
                            _logger.error(error_msg)
                            quotation.sudo().write({'sap_synced': False})
                            raise Exception(error_msg)
                    else:
                        # إنشاء quotation جديد في SAP (ليس لديه DocEntry بعد)
                        state_label = "quotation (draft)" if quotation.state == 'draft' else "quotation"
                        _logger.info(f"Creating new {state_label} {quotation.name} in SAP (no existing DocEntry)")
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
                            quotation._sync_sap_fields_to_pos_order(
                                sap_doc_num=doc_num,
                                sap_doc_entry=doc_entry,
                            )
                            
                            # Log success with invoice type info if present
                            inv_type_info = ""
                            if quotation.invoice_type:
                                inv_type_info = f", InvoiceType={quotation.invoice_type} (U_InvType sent to SAP)"
                            _logger.info(f"✅ {state_label.capitalize()} {quotation.name} created in SAP: DocNum={doc_num}, DocEntry={doc_entry}{inv_type_info}")
                            # Store SAP LineNums after first creation
                            try:
                                self._store_sap_line_nums(quotation, connection)
                            except Exception:
                                pass
                            sync_successful = True
                        else:
                            error_msg = f"❌ Failed to create {state_label} {quotation.name} in SAP: create_quotation returned None or empty result. Check SAP logs for details."
                            _logger.error(error_msg)
                            quotation.sudo().write({'sap_synced': False})
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
    
    def _sync_sap_fields_to_pos_order(self, sap_doc_num=None, sap_doc_entry=None):
        """
        Propagates SAP doc fields to the linked pos.perfume.order.
        Called after a successful SAP sync to keep the POS list view in sync,
        since stored related fields are not updated when we write via raw SQL.
        """
        try:
            pos_order = self.env['pos.perfume.order'].sudo().search(
                [('sale_order_id', '=', self.id)], limit=1
            )
            if pos_order:
                update_vals = {}
                if sap_doc_num is not None:
                    update_vals['sap_doc_num'] = sap_doc_num
                if sap_doc_entry is not None:
                    update_vals['sap_doc_entry'] = sap_doc_entry
                if update_vals:
                    pos_order.sudo().write(update_vals)
                    _logger.info(f"[POS Sync] Updated pos.perfume.order {pos_order.name} SAP fields: {update_vals}")
        except Exception as e:
            _logger.warning(f"[POS Sync] Could not update pos.perfume.order for {self.name}: {e}")

    def _prepare_quotation_data_for_sap(self, quotation, backend=None):
        """إعداد بيانات quotation للـ SAP Service Layer"""
        # إعداد سطور الوثيقة — فقط الأسطر الموجودة (المحذوفة تُعالج في update_quotation)
        document_lines = []
        for line in quotation.order_line:
            # تخطي السطور بدون منتج
            if not line.product_id:
                _logger.warning(f"Skipping order line {line.id} - no product_id")
                continue
            
            # تخطي السطور بدون كمية أو بكمية صفر أو سالبة
            if not line.product_uom_qty or line.product_uom_qty <= 0:
                _logger.warning(f"Skipping order line {line.id} for product {line.product_id.name} - quantity is {line.product_uom_qty} (must be > 0)")
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
                _logger.info(f"✅ Using custom product name for ItemDescription: {line.custom_product_name} (Line ID: {line.id}, Product: {line.product_id.name})")
            else:
                _logger.info(f"⚠️ No custom product name found for line ID {line.id}, Product: {line.product_id.name}, hasattr: {hasattr(line, 'custom_product_name')}, value: {getattr(line, 'custom_product_name', 'NOT_SET')}")
            
            _logger.info(f"Preparing DocumentLine: ItemCode={item_code}, Quantity={line.product_uom_qty}")
            
            # إضافة UoMEntry (رقم وحدة القياس) إذا كانت متوفرة
            # البحث والتحقق قبل الإرسال
            if line.product_uom_id:
                _logger.info(f"Searching for UoMEntry for UoM: {line.product_uom_id.name} (id={line.product_uom_id.id})")
                
                # البحث عن UoM في sap.uom.sync للحصول على UoMEntry (sap_uom_entry)
                # أولاً: نحصل على مجموعة UoM الخاصة بالمنتج لتقييد البحث
                product_sap_extended = self.env['sap.product.extended'].search(
                    [('product_id', '=', line.product_id.id)], limit=1
                )
                product_uom_group_id = product_sap_extended.sap_uom_group_id.id if product_sap_extended and product_sap_extended.sap_uom_group_id else None

                domain = [('odoo_uom_id', '=', line.product_uom_id.id)]
                if product_uom_group_id:
                    # البحث أولاً في مجموعة المنتج تحديداً
                    domain_with_group = domain + [('sap_group_id', '=', product_uom_group_id)]
                    if backend:
                        domain_with_group.append(('backend_id', '=', backend.id))
                    sap_uom_sync = self.env['sap.uom.sync'].search(domain_with_group, limit=1)
                    if sap_uom_sync:
                        _logger.info(f"Found sap_uom_sync in product's UoM group (group_id={product_uom_group_id})")
                    else:
                        # fallback: البحث في أي مجموعة
                        if backend:
                            domain.append(('backend_id', '=', backend.id))
                        sap_uom_sync = self.env['sap.uom.sync'].search(domain, limit=1)
                        if sap_uom_sync:
                            _logger.warning(f"⚠️ UoM not found in product's group — using first match from any group (group_id={sap_uom_sync.sap_group_id.id})")
                else:
                    if backend:
                        domain.append(('backend_id', '=', backend.id))
                        _logger.info(f"Searching in sap.uom.sync with backend_id={backend.id}")
                    else:
                        active_backend = self.env['sap.backend'].search([('active', '=', True)], limit=1)
                        if active_backend:
                            domain.append(('backend_id', '=', active_backend.id))
                    sap_uom_sync = self.env['sap.uom.sync'].search(domain, limit=1)

                _logger.info(f"Searching for UoMEntry for UoM: {line.product_uom_id.name} (id={line.product_uom_id.id}), product_group={product_uom_group_id}")
                
                if not sap_uom_sync:
                    # Fallback: UoM غير موجود في مجموعة المنتج — نستخدم أقرب UoM بـ factor=1.0
                    if product_sap_extended and product_sap_extended.sap_uom_group_id:
                        group_syncs = product_sap_extended.sap_uom_group_id.uom_ids.filtered(
                            lambda u: u.odoo_uom_id and u.sap_uom_entry and u.sap_uom_entry > 0
                        )
                        if group_syncs:
                            fallback = min(group_syncs, key=lambda u: (abs(u.odoo_uom_id.factor - 1.0), u.id))
                            sap_uom_sync = fallback
                            _logger.warning(
                                f"⚠️ UoM '{line.product_uom_id.name}' has no SAP mapping in group. "
                                f"Falling back to group base UoM: '{fallback.odoo_uom_id.name}' "
                                f"(sap_uom_entry={fallback.sap_uom_entry}) for {item_code}"
                            )

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
        doc_date = (quotation.date_order or quotation.create_date or self.env.context.get('date')).strftime('%Y-%m-%d') if (quotation.date_order or quotation.create_date) else fields.Date.today().strftime('%Y-%m-%d')
        quotation_data = {
            'CardCode': quotation.partner_id.ref or '',
            'DocumentLines': document_lines,
        }
        # العملة وتاريخ المستند حتى يستخدم SAP سعر الصرف لليوم نفسه (Exchange Rates and Indexes)
        currency = (quotation.currency_id and quotation.currency_id.name) or ''
        if currency:
            quotation_data['DocCurrency'] = currency
        quotation_data['DocDate'] = doc_date
        # عند العملة IQD: إرسال DocRate من SAP حتى يكون سعر الفاتورة في SAP = سعر SAP (بنفس تاريخ اليوم)
        if currency and currency.upper() == 'IQD':
            sap_backend = backend or self.env['sap.backend'].search([('active', '=', True)], limit=1)
            if sap_backend:
                try:
                    conn = sap_backend.get_connection()
                    iqd_rate = conn.get_iqd_exchange_rate()
                    if iqd_rate and 100 <= iqd_rate <= 10000:
                        quotation_data['DocRate'] = iqd_rate
                        _logger.info(f"[SAP] DocRate={iqd_rate} (from SAP for date {doc_date}) for IQD quotation {quotation.name}")
                except Exception as e:
                    _logger.warning(f"[SAP] Could not set DocRate from SAP for IQD: {e}")
        
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

    def _store_sap_line_nums(self, quotation, connection, doc_type=None):
        """
        Fetch the current Quotation/Order from SAP and store LineNum per order line.
        Matches by ItemCode. Called after create or update to keep LineNums in sync.
        doc_type: 'Orders' or 'Quotations' — if None, determined from quotation.state.
        """
        try:
            # تحديد الـ endpoint
            if doc_type == 'Orders':
                endpoint = f"Orders({quotation.sap_doc_entry})"
            elif doc_type == 'Quotations':
                endpoint = f"Quotations({quotation.sap_doc_entry})"
            elif quotation.state == 'sale':
                endpoint = f"Orders({quotation.sap_doc_entry})"
            else:
                endpoint = f"Quotations({quotation.sap_doc_entry})"

            sap_doc = connection.get(endpoint, {'$select': 'DocEntry,DocumentLines'})
            sap_lines = sap_doc.get('DocumentLines', [])

            # Build map: ItemCode → LineNum (take first open line per ItemCode)
            item_line_map = {}
            for sap_line in sap_lines:
                item_code = sap_line.get('ItemCode', '')
                line_num = sap_line.get('LineNum')
                line_status = sap_line.get('LineStatus', '')
                if item_code and line_num is not None and line_status != 'bost_Close':
                    if item_code not in item_line_map:
                        item_line_map[item_code] = line_num

            # Store LineNum on each Odoo order line
            for line in quotation.order_line:
                item_code = line.product_id.default_code or ''
                line_num = item_line_map.get(item_code, -1)
                if line.sap_line_num != line_num:
                    line.sudo().write({'sap_line_num': line_num})

            _logger.info(f"✅ Stored SAP LineNums for {quotation.name}: {item_line_map}")
        except Exception as e:
            _logger.warning(f"⚠️ Could not store SAP LineNums for {quotation.name}: {e}")


        """Override action_confirm to convert quotation to sales order in SAP"""
        result = super(SaleOrder, self).action_confirm()
        # Note: SAP conversion is handled explicitly by confirmSaleOrder JS button
        # which calls action_manual_sync_to_sap after action_confirm.
        # Do NOT auto-convert here to avoid converting Quotation → Sales Order in SAP
        # when action_confirm is triggered implicitly (e.g., from POS workflow).
        return result
    
    def action_manual_sync_to_sap(self):
        """إرسال/تحديث يدوي إلى SAP مع إظهار نتيجة واضحة للمستخدم"""
        self.ensure_one()
        try:
            self._send_to_sap()
        except Exception as e:
            # رفع UserError حتى يرى المستخدم الخطأ
            raise UserError(f'فشل الإرسال إلى SAP:\n{str(e)}')

        # Flush ORM cache so DB query sees latest written values
        self.env.cr.flush()
        # بعد _send_to_sap، تحقق من النتيجة الفعلية
        self.env.cr.execute(
            "SELECT sap_synced, sap_error_message FROM sale_order WHERE id=%s",
            (self.id,)
        )
        row = self.env.cr.fetchone()
        synced = row[0] if row else False
        error_msg = row[1] if row else None

        if synced:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '✅ تم المزامنة مع SAP',
                    'message': f'{self.name} | رقم SAP: {self.sap_doc_num or "—"}',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise UserError(
                f'فشلت المزامنة مع SAP للطلب {self.name}.\n\n'
                f'السبب:\n{error_msg or "خطأ غير معروف — راجع سجل النظام"}'
            )

    def action_update_sap_document(self):
        """
        تحديث مستند موجود في SAP بـ PATCH مباشر (بدون إعادة إنشاء).
        يعمل على Quotations و Sales Orders.
        يُظهر نتيجة واضحة للمستخدم سواء نجح أو فشل.
        """
        self.ensure_one()

        if not self.sap_doc_entry or self.sap_doc_entry <= 0:
            raise UserError(
                f'لا يمكن تحديث الطلب {self.name} في SAP:\n'
                f'لا يوجد رقم مستند SAP (DocEntry) مسجل.\n'
                f'يرجى إرسال الطلب أولاً باستخدام "إرسال إلى SAP".'
            )

        backend = self.env['sap.backend'].search([('active', '=', True)], limit=1)
        if not backend:
            raise UserError('لا يوجد SAP Backend نشط. تحقق من الإعدادات.')

        try:
            connection = backend.get_connection()
            doc_data = self._prepare_quotation_data_for_sap(self, backend)

            # إزالة CardCode لأن PATCH لا يقبله على مستند موجود
            doc_data.pop('CardCode', None)

            # تحديد نوع المستند في SAP (Quotation أو Order)
            if self.state == 'draft':
                endpoint = f"Quotations({self.sap_doc_entry})"
                doc_type_label = 'Quotation (عرض السعر)'
            else:
                endpoint = f"Orders({self.sap_doc_entry})"
                doc_type_label = 'Sales Order (أمر البيع)'

            url = f"{connection.base_url}/{endpoint}"
            headers = connection._get_headers()

            _logger.info(f"[PATCH] Updating SAP {doc_type_label} {self.name} → {url}")
            response = connection.session.patch(url, json=doc_data, headers=headers, timeout=30)

            if response.status_code in (200, 204):
                self.sudo().write({
                    'sap_synced': True,
                    'sap_error_message': False,
                    'sap_last_sync_date': fields.Datetime.now(),
                })
                _logger.info(f"✅ PATCH success for {self.name} (DocEntry: {self.sap_doc_entry})")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '✅ تم التحديث في SAP',
                        'message': (
                            f'{self.name} ({doc_type_label})\n'
                            f'رقم SAP: {self.sap_doc_num or self.sap_doc_entry}'
                        ),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                # محاولة قراءة رسالة الخطأ من SAP
                try:
                    sap_error = response.json()
                    sap_msg = (
                        sap_error.get('error', {}).get('message', {}).get('value')
                        or sap_error.get('error', {}).get('message')
                        or response.text[:500]
                    )
                except Exception:
                    sap_msg = response.text[:500] if response.text else f'HTTP {response.status_code}'

                error_text = (
                    f'فشل تحديث {doc_type_label} {self.name} في SAP.\n\n'
                    f'كود الخطأ: {response.status_code}\n'
                    f'رسالة SAP: {sap_msg}'
                )
                self.sudo().write({
                    'sap_synced': False,
                    'sap_error_message': error_text,
                    'sap_last_sync_date': fields.Datetime.now(),
                })
                _logger.error(f"❌ PATCH failed for {self.name}: {response.status_code} — {sap_msg}")
                raise UserError(error_text)

        except UserError:
            raise
        except Exception as e:
            error_text = f'خطأ غير متوقع عند تحديث {self.name} في SAP:\n{str(e)}'
            self.sudo().write({
                'sap_synced': False,
                'sap_error_message': error_text,
                'sap_last_sync_date': fields.Datetime.now(),
            })
            _logger.error(error_text, exc_info=True)
            raise UserError(error_text)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Custom product name for invoice/report display and SAP ItemDescription
    custom_product_name = fields.Char(
        string='Custom Product Name (Invoice Only)',
        help='Custom product name to display in invoice/report. If set, this name will be used in the report and sent to SAP as ItemDescription. The original product name remains unchanged.'
    )

    # SAP LineNum for this line — stored after first sync so PATCH can reference it
    sap_line_num = fields.Integer(
        string='SAP Line Number',
        default=-1,
        copy=False,
        help='LineNum assigned by SAP for this order line. Used to update/close lines via PATCH.'
    )


