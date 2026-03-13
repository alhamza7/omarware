# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _name    = 'sale.order'
    _inherit = ['sale.order', 'sap.order.mixin']
    
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
        """Send quotation/sale order to SAP after creation if conditions are met."""
        order = super(SaleOrder, self).create(vals)

        error = self._validate_sap_preconditions(order)
        if error:
            _logger.warning("[SAP SO] Conditions not met for %s: %s", order.name, error)
            self._write_sap_status(order, synced=False, error=error)
            return order

        if not order.sap_synced:
            try:
                order._send_to_sap()
            except Exception as e:
                _logger.warning("[SAP SO] Could not send %s to SAP on create: %s", order.name, e)

        return order
    
    def write(self, vals):
        """Re-sync to SAP when state transitions or relevant fields change."""
        old_states = {order.id: order.state for order in self}
        result = super(SaleOrder, self).write(vals)

        for order in self:
            if self._validate_sap_preconditions(order):
                continue

            old_state = old_states.get(order.id)

            # Case A: draft → sale AND already has a Quotation in SAP → convert to Order
            state_changed_to_sale = (
                'state' in vals
                and vals['state'] == 'sale'
                and old_state == 'draft'
                and order.sap_doc_entry
                and order.sap_doc_entry > 0
            )

            # Case B: draft → sale but was never sent to SAP (e.g. SAP was down at creation)
            state_confirmed_without_sap = (
                'state' in vals
                and vals['state'] == 'sale'
                and old_state == 'draft'
                and not (order.sap_doc_entry and order.sap_doc_entry > 0)
                and not order.sap_synced
            )

            if state_changed_to_sale:
                _logger.info("[SAP SO] Converting quotation %s to Sales Order in SAP", order.name)
                try:
                    backend = self._get_active_backend()
                    if not backend:
                        self._write_sap_status(order, synced=False, error='لا يوجد SAP backend نشط')
                        continue
                    connection = backend.get_connection()
                    sap_order  = connection.convert_quotation_to_order(order.sap_doc_entry)
                    if sap_order:
                        self._write_sap_status(
                            order, synced=True,
                            doc_num=sap_order.get('DocNum'),
                            doc_entry=sap_order.get('DocEntry'),
                        )
                        _logger.info("[SAP SO] ✅ Converted %s → DocNum=%s", order.name, sap_order.get('DocNum'))
                    else:
                        self._write_sap_status(order, synced=False, error='فشل تحويل Quotation إلى Sales Order في SAP')
                except Exception as e:
                    _logger.error("[SAP SO] Exception converting %s: %s", order.name, e, exc_info=True)
                    self._write_sap_status(order, synced=False, error=str(e))
                continue

            if state_confirmed_without_sap:
                _logger.info("[SAP SO] Order %s confirmed but never sent to SAP — sending now", order.name)
                try:
                    order._send_to_sap()
                except Exception as e:
                    _logger.warning("[SAP SO] Could not send confirmed order %s to SAP: %s", order.name, e)
                continue

            # Field-level updates trigger re-sync for draft quotations or existing SAP orders
            watched = {
                'partner_id', 'order_line', 'date_order', 'validity_date',
                'price_unit', 'discount', 'product_uom_qty', 'invoice_type', 'note',
            }
            if watched & set(vals):
                if order.state == 'draft' or (order.state == 'sale' and order.sap_doc_entry):
                    try:
                        order._send_to_sap()
                    except Exception as e:
                        _logger.warning("[SAP SO] Could not update %s in SAP on write: %s", order.name, e)

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
        """Send quotation/sale order to SAP.
        force_as_quotation=True: always send as Quotation regardless of state.
        """
        for quotation in self:
            send_as_sale = (not force_as_quotation) and quotation.state == 'sale'
            doc_label    = "Sale Order" if send_as_sale else "Quotation"
            _logger.info("[SAP SO] Starting sync for %s as %s", quotation.name, doc_label)

            if quotation.invoice_type:
                _logger.info("[SAP SO] invoice_type=%s for %s", quotation.invoice_type, quotation.name)

            try:
                backend = self._get_active_backend()
                if not backend:
                    self._write_sap_status(quotation, synced=False, error='لا يوجد SAP backend نشط')
                    return

                error = self._validate_sap_preconditions(quotation)
                if error:
                    self._write_sap_status(quotation, synced=False, error=error)
                    return

                quotation_data = self._prepare_quotation_data_for_sap(quotation, backend)
                connection     = backend.get_connection()
                headers        = connection._get_headers()

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
                    self._sap_create_or_update_quotation(quotation, connection, headers, quotation_data)

            except Exception as e:
                _logger.error("[SAP SO] Exception for %s: %s", quotation.name, e, exc_info=True)
                try:
                    self._write_sap_status(quotation, synced=False, error=str(e))
                except Exception:
                    pass

    def _sap_create_or_convert_order(self, quotation, connection, headers, data):
        """Create SAP Sales Order — linked to prior Quotation if available."""
        if quotation.sap_doc_entry and quotation.sap_doc_entry > 0:
            # Try to update the Quotation first, then create a linked Order
            check_url  = f"{connection.base_url}/Quotations({quotation.sap_doc_entry})?$select=DocEntry,DocStatus"
            check_resp = connection.session.get(check_url, headers=headers, timeout=30)
            quotation_exists = check_resp.status_code == 200

            if quotation_exists:
                patch_data = {k: v for k, v in data.items() if k != 'CardCode'}
                patch_url  = f"{connection.base_url}/Quotations({quotation.sap_doc_entry})"
                patch_resp = connection.session.patch(patch_url, json=patch_data, headers=headers, timeout=30)
                if patch_resp.status_code not in (200, 204):
                    _logger.warning("[SAP SO] Quotation PATCH before conversion returned %s", patch_resp.status_code)

                order_lines = []
                for idx, line in enumerate(data.get('DocumentLines', [])):
                    ol = dict(line)
                    ol.update({'BaseType': 23, 'BaseEntry': quotation.sap_doc_entry, 'BaseLine': idx})
                    order_lines.append(ol)
                order_data = dict(data, DocumentLines=order_lines)
            else:
                _logger.warning("[SAP SO] Quotation %d not found in SAP, creating standalone Order", quotation.sap_doc_entry)
                order_data = data
        else:
            order_data = data

        url      = f"{connection.base_url}/Orders"
        response = connection.session.post(url, json=order_data, headers=headers, timeout=30)

        if response.status_code in (200, 201):
            result = response.json()
            self._write_sap_status(
                quotation, synced=True,
                doc_num=result.get('DocNum'),
                doc_entry=result.get('DocEntry'),
            )
            _logger.info("[SAP SO] ✅ Sales Order created for %s → DocNum=%s", quotation.name, result.get('DocNum'))
        else:
            error = f"POST /Orders → {response.status_code}: {response.text[:300]}"
            _logger.error("[SAP SO] ❌ %s — %s", quotation.name, error)
            self._write_sap_status(quotation, synced=False, error=error)

    def _sap_create_or_update_quotation(self, quotation, connection, headers, data):
        """Create or update a SAP Quotation."""
        if quotation.sap_doc_entry and quotation.sap_doc_entry > 0:
            odoo_lines_info = [
                {
                    'item_code': (line.product_id.default_code or line.product_id.barcode or ''),
                    'sap_line_num': line.sap_line_num,
                }
                for line in quotation.order_line if line.product_id
            ]
            result = connection.update_quotation(
                quotation.sap_doc_entry, data, existing_odoo_lines=odoo_lines_info
            )
            if result is not None:
                self._write_sap_status(quotation, synced=True)
                _logger.info("[SAP SO] ✅ Quotation %s updated (DocEntry=%d)", quotation.name, quotation.sap_doc_entry)
                try:
                    self._store_sap_line_nums(quotation, connection)
                except Exception:
                    pass
            else:
                self._write_sap_status(quotation, synced=False, error='update_quotation returned None')
                raise Exception(f"Failed to update quotation {quotation.name} in SAP")
        else:
            result = connection.create_quotation(data)
            if result:
                self._write_sap_status(
                    quotation, synced=True,
                    doc_num=result.get('DocNum'),
                    doc_entry=result.get('DocEntry'),
                )
                _logger.info(
                    "[SAP SO] ✅ Quotation %s created → DocNum=%s DocEntry=%s",
                    quotation.name, result.get('DocNum'), result.get('DocEntry'),
                )
                try:
                    self._store_sap_line_nums(quotation, connection)
                except Exception:
                    pass
            else:
                self._write_sap_status(quotation, synced=False, error='create_quotation returned None')
                raise Exception(f"Failed to create quotation {quotation.name} in SAP")
    
    def _prepare_quotation_data_for_sap(self, quotation, backend=None):
        """Build the SAP Service Layer payload for a Quotation or Sales Order."""
        backend_id     = backend.id if backend else None
        document_lines = []

        for line in quotation.order_line:
            if not line.product_id:
                _logger.warning("[SAP SO] Skipping line %d — no product", line.id)
                continue
            if not line.product_uom_qty or line.product_uom_qty <= 0:
                _logger.warning("[SAP SO] Skipping line %d — qty=%s", line.id, line.product_uom_qty)
                continue

            item_code = (
                line.product_id.default_code
                or line.product_id.barcode
                or ''
            )
            if not item_code:
                _logger.warning("[SAP SO] Product %s has no ItemCode", line.product_id.name)

            line_data = {
                'ItemCode':        item_code,
                'Quantity':        line.product_uom_qty,
                'UnitPrice':       line.price_unit,
                'DiscountPercent': line.discount,
            }

            if hasattr(line, 'custom_product_name') and line.custom_product_name:
                line_data['ItemDescription'] = line.custom_product_name

            # UoMEntry — same two-step resolution as purchase
            uom_entry = self._resolve_sale_uom_entry(line, backend_id)
            if uom_entry:
                line_data['UoMEntry'] = uom_entry

            # WarehouseCode
            warehouse_code = self._resolve_sale_warehouse_code(line, quotation, backend_id)
            if warehouse_code:
                line_data['WarehouseCode'] = warehouse_code
            else:
                _logger.warning("[SAP SO] No WarehouseCode for ItemCode=%s", item_code)

            document_lines.append(line_data)

        if not document_lines:
            raise UserError("لا يمكن إرسال الطلب بدون سطور صالحة")

        doc_date = (
            (quotation.date_order or quotation.create_date).strftime('%Y-%m-%d')
            if (quotation.date_order or quotation.create_date)
            else fields.Date.today().strftime('%Y-%m-%d')
        )

        payload = {
            'CardCode':      quotation.partner_id.ref or '',
            'DocumentLines': document_lines,
            'DocDate':       doc_date,
        }

        # Currency
        currency = (quotation.currency_id and quotation.currency_id.name) or ''
        if currency:
            payload['DocCurrency'] = currency
            # Fetch today's IQD exchange rate from SAP so amounts match
            if currency.upper() == 'IQD':
                sap_backend = backend or self._get_active_backend()
                if sap_backend:
                    try:
                        iqd_rate = sap_backend.get_connection().get_iqd_exchange_rate()
                        if iqd_rate and 100 <= iqd_rate <= 10000:
                            payload['DocRate'] = iqd_rate
                    except Exception as e:
                        _logger.warning("[SAP SO] Could not get IQD rate: %s", e)

        # Invoice type (SAP UDF)
        if quotation.invoice_type:
            payload['U_InvType'] = str(quotation.invoice_type).strip()

        # Notes / comments
        if quotation.note:
            payload['Comments'] = quotation.note.strip()

        # Validity / due date
        if quotation.validity_date:
            payload['DocDueDate'] = quotation.validity_date.strftime('%Y-%m-%d')

        return payload

    # ── Resolution helpers ─────────────────────────────────────────────────

    def _resolve_sale_uom_entry(self, line, backend_id):
        """
        Resolve SAP UoMEntry for a sale order line.
        Same strategy as purchase: line UoM → product sales_uom_id fallback.
        """
        uom = getattr(line, 'product_uom_id', None) or getattr(line, 'product_uom', None)
        if uom:
            domain = [('odoo_uom_id', '=', uom.id)]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            sync = self.env['sap.uom.sync'].search(domain, limit=1)
            if sync and sync.sap_uom_entry and sync.sap_uom_entry > 0:
                return sync.sap_uom_entry

        if line.product_id and backend_id:
            ext = self.env['sap.product.extended'].search(
                [('product_id', '=', line.product_id.id), ('backend_id', '=', backend_id)],
                limit=1,
            )
            if ext and ext.sales_uom_id:
                sync = self.env['sap.uom.sync'].search(
                    [('odoo_uom_id', '=', ext.sales_uom_id.id), ('backend_id', '=', backend_id)],
                    limit=1,
                )
                if sync and sync.sap_uom_entry and sync.sap_uom_entry > 0:
                    return sync.sap_uom_entry

        if uom:
            _logger.warning("[SAP SO] No UoMEntry for UoM '%s'", uom.name)
        return None

    def _resolve_sale_warehouse_code(self, line, quotation, backend_id):
        """Resolve SAP WarehouseCode for a sale order line."""
        def _lookup(warehouse):
            if not warehouse:
                return None
            if backend_id:
                info = self.env['sap.product.warehouse.info'].search(
                    [('warehouse_id', '=', warehouse.id), ('backend_id', '=', backend_id)],
                    limit=1,
                )
                if info and info.sap_warehouse_code:
                    return info.sap_warehouse_code
            return warehouse.code or None

        wh = getattr(line, 'product_warehouse_id', None)
        code = _lookup(wh)
        if code:
            return code

        wh = getattr(quotation, 'warehouse_id', None)
        return _lookup(wh)

    def _store_sap_line_nums(self, quotation, connection):
        """
        Fetch the current Quotation/Order from SAP and store LineNum per order line.
        Matches by ItemCode. Called after create or update to keep LineNums in sync.
        """
        try:
            # Determine endpoint: Quotations or Orders
            if quotation.state == 'sale':
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

            _logger.info("[SAP SO] ✅ Stored SAP LineNums for %s: %s", quotation.name, item_line_map)
        except Exception as e:
            _logger.warning("[SAP SO] Could not store SAP LineNums for %s: %s", quotation.name, e)

    # action_manual_sync_to_sap is inherited from sap.order.mixin

    def action_update_sap_document(self):
        """
        Direct PATCH to update an existing SAP document (Quotation or Order).
        Shows a clear result notification to the user.
        """
        self.ensure_one()

        if not self.sap_doc_entry or self.sap_doc_entry <= 0:
            raise UserError(
                f'لا يمكن تحديث {self.name}: لا يوجد رقم مستند SAP (DocEntry).\n'
                'يرجى إرسال الطلب أولاً باستخدام "إرسال إلى SAP".'
            )

        backend = self._get_active_backend()
        if not backend:
            raise UserError('لا يوجد SAP Backend نشط. تحقق من الإعدادات.')

        try:
            connection  = backend.get_connection()
            doc_data    = self._prepare_quotation_data_for_sap(self, backend)
            doc_data.pop('CardCode', None)

            endpoint      = f"Quotations({self.sap_doc_entry})" if self.state == 'draft' else f"Orders({self.sap_doc_entry})"
            doc_type_label = 'Quotation' if self.state == 'draft' else 'Sales Order'
            url           = f"{connection.base_url}/{endpoint}"
            headers       = connection._get_headers()

            _logger.info("[SAP SO] PATCH %s → %s", self.name, url)
            response = connection.session.patch(url, json=doc_data, headers=headers, timeout=30)

            if response.status_code in (200, 204):
                self._write_sap_status(self, synced=True)
                _logger.info("[SAP SO] ✅ PATCH success for %s (DocEntry=%d)", self.name, self.sap_doc_entry)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'تم التحديث في SAP',
                        'message': f'{self.name} ({doc_type_label}) | رقم SAP: {self.sap_doc_num or self.sap_doc_entry}',
                        'type': 'success',
                        'sticky': False,
                    },
                }
            else:
                try:
                    sap_err = response.json()
                    sap_msg = (
                        sap_err.get('error', {}).get('message', {}).get('value')
                        or sap_err.get('error', {}).get('message')
                        or response.text[:500]
                    )
                except Exception:
                    sap_msg = response.text[:500] or f'HTTP {response.status_code}'

                error_text = f'فشل تحديث {doc_type_label} {self.name}: {response.status_code} — {sap_msg}'
                self._write_sap_status(self, synced=False, error=error_text)
                _logger.error("[SAP SO] ❌ %s", error_text)
                raise UserError(error_text)

        except UserError:
            raise
        except Exception as e:
            error_text = f'خطأ غير متوقع عند تحديث {self.name}: {e}'
            self._write_sap_status(self, synced=False, error=error_text)
            _logger.error("[SAP SO] ❌ %s", error_text, exc_info=True)
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


