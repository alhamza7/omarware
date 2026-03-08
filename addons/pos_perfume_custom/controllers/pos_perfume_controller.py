# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import logging
import io
import base64

_logger = logging.getLogger(__name__)

class PosPerfumeController(http.Controller):

    @http.route('/pos_perfume/get_exchange_rate', type='json', auth='user')
    def get_exchange_rate(self):
        """
        Return IQD/USD rate for POS Perfume. Same key as SAP Exchange Rate Sync
        (pos_perfume.default_exchange_rate_usd_iqd). So POS IQD prices follow SAP when sync runs.
        """
        return request.env['pos.perfume.order'].sudo().get_exchange_rate_from_db()
    
    @http.route('/pos_perfume/get_product_data', type='json', auth='user')
    def get_product_data(self, product_id, pricelist_id=None, uom_id=None, warehouse_id=None):
        """
        Get product data - prices come directly from pricelist items (via product_packaging_id mapping)
        to avoid Odoo's standard price logic which ignores the custom UoM-packaging mapping.
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
                    pricelist_id = pricelist_id[0]
                pricelist = request.env['product.pricelist'].browse(int(pricelist_id))
                if not pricelist.exists():
                    pricelist = None
            
            # Get all UoMs with prices from pricelist items (uses product_packaging_id mapping)
            available_uoms = self._get_uoms_from_pricelist(product, pricelist)
            
            _logger.info(f"[POS] Found {len(available_uoms)} UoMs")
            
            # Default price on initial load = highest price (= كغم, the most expensive pack).
            # When uom_id is explicitly passed, use exact match for that UoM instead.
            if uom_id:
                default_price = self._get_default_price_from_uoms(available_uoms, uom_id)
            else:
                default_price = self._get_default_price_from_uoms(available_uoms)
            
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
        Get all UoMs with prices for a product using its SAP UoM Group + pricelist items.

        Special handling for items where product_uom_id = Units (id=1):
        SAP sometimes exports prices with UoM = Units regardless of the actual unit.
        These items are treated as generic prices and mapped to the product's actual UoM group.
        
        Fallback strategy: if UoM group filtering produces no results, retry without the filter
        to avoid showing price = 0 when the pricelist item's UoM doesn't match the group.
        """
        if not pricelist:
            return [{'id': product.uom_id.id, 'name': product.uom_id.name, 'price': product.list_price}]

        # Step 1: Get available UoMs from SAP UoM Group
        available_uom_ids = []
        extended_info = request.env['sap.product.extended'].search(
            [('product_id', '=', product.id)], limit=1
        )
        if extended_info and extended_info.sap_uom_group_id:
            uom_syncs = extended_info.sap_uom_group_id.uom_ids
            available_uom_ids = uom_syncs.mapped('odoo_uom_id').ids
            _logger.info(f"[POS] UoM Group: {extended_info.sap_uom_group_id.name}, UoMs: {available_uom_ids}")

        # Step 2: Get pricelist items for this product
        items = request.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            '|', ('product_id', '=', False), ('product_id', '=', product.id),
        ])
        _logger.info(f"[POS] Found {len(items)} pricelist items")

        # Step 3: Process items with group filter
        uoms_with_prices = self._process_pricelist_items(items, product, available_uom_ids)

        # Step 4: Fallback - if group filter produced nothing, retry without filter
        # This handles products where SAP uses 'Units' as UoM code even though actual
        # unit is '0.25 كغم' or similar - the UoM id doesn't match the group
        if not uoms_with_prices and items:
            _logger.info(f"[POS] Group filter yielded no results - retrying without UoM filter")
            uoms_with_prices = self._process_pricelist_items(items, product, [])

        # Step 5: Build result list
        result = [
            {'id': data['uom'].id, 'name': data['uom'].name, 'price': data['price']}
            for data in uoms_with_prices.values()
        ]

        # Step 6: Ensure product base UoM is always visible
        if product.uom_id.id not in uoms_with_prices:
            best_price = max((v['price'] for v in uoms_with_prices.values()), default=product.list_price)
            result.insert(0, {'id': product.uom_id.id, 'name': product.uom_id.name, 'price': best_price})

        _logger.info(f"[POS] Returning {len(result)} UoMs")
        return result or [{'id': product.uom_id.id, 'name': product.uom_id.name, 'price': product.list_price}]

    # SAP exports the base-unit price with product_uom_id = Units (id=1) regardless
    # of the product's actual UoM. We must remap it to the product's real base UoM.
    SAP_GENERIC_UOM_ID = 1  # "Units" - SAP's catch-all UoM code

    def _process_pricelist_items(self, items, product, available_uom_ids):
        """
        Process pricelist items and return {uom_id: {uom, price, has_packaging}} dict.
        When available_uom_ids is empty, no UoM group filtering is applied.

        Key behaviour:
        - Items with product_uom_id = Units (SAP_GENERIC_UOM_ID) and no packaging are
          treated as the product's actual base UoM price (product.uom_id), since SAP
          uses 'Units' as a placeholder regardless of the real unit.
        """
        uoms_with_prices = {}

        for item in items:
            price = item.fixed_price if item.compute_price == 'fixed' else product.list_price

            if not item.product_packaging_id:
                # No packaging: resolve target UoM
                raw_uom = item.product_uom_id or product.uom_id

                # SAP stores the base-unit price with UoM = Units (id=1).
                # Remap it to the product's actual base UoM so it passes the group filter.
                if raw_uom.id == self.SAP_GENERIC_UOM_ID:
                    if product.uom_id.id != self.SAP_GENERIC_UOM_ID:
                        # Normal case: product has a real base UoM (e.g. كغم)
                        uom = product.uom_id
                    elif available_uom_ids:
                        # Edge case: product.uom_id is ALSO Units (SAP never updated it).
                        # Find the "base" UoM of the group: the one NOT used as packaging
                        # in any other item, with factor closest to 1.0. Tiebreak: lowest id.
                        used_as_packaging = {
                            it.product_packaging_id.id
                            for it in items
                            if it.product_packaging_id
                        }
                        group_uoms = request.env['uom.uom'].browse(available_uom_ids)
                        not_packaging = [u for u in group_uoms if u.id not in used_as_packaging]
                        pool = not_packaging if not_packaging else list(group_uoms)
                        uom = min(pool, key=lambda u: (abs(u.factor - 1.0), u.id))
                    else:
                        uom = product.uom_id
                    _logger.info(f"[POS]   Remapping Units→{uom.name} (SAP generic uom)")
                else:
                    uom = raw_uom

                # Skip if UoM not in group (unless no group filter active)
                if available_uom_ids and uom.id not in available_uom_ids:
                    _logger.info(f"[POS]   Skip (no pkg) {uom.name} - not in group")
                    continue

                # Base item (no packaging) always takes priority over packaging items
                uoms_with_prices[uom.id] = {'uom': uom, 'price': price, 'has_packaging': False}
                _logger.info(f"[POS]   UoM {uom.name}: {price} (base)")

            else:
                # Has packaging: the packaging field IS the target UoM
                packaging_uom = item.product_packaging_id

                if available_uom_ids and packaging_uom.id not in available_uom_ids:
                    _logger.info(f"[POS]   Skip (pkg) {packaging_uom.name} - not in group")
                    continue

                # Packaging item only added when no base item already claims this UoM
                if packaging_uom.id not in uoms_with_prices or uoms_with_prices[packaging_uom.id]['has_packaging']:
                    uoms_with_prices[packaging_uom.id] = {'uom': packaging_uom, 'price': price, 'has_packaging': True}
                    _logger.info(f"[POS]   UoM {packaging_uom.name}: {price} (packaging)")

        return uoms_with_prices

    def _get_default_price_from_uoms(self, available_uoms, default_uom_id=None):
        """
        Resolve the price from available_uoms list.
        - When default_uom_id is given (UoM change): return exact match for that UoM.
        - When default_uom_id is None (initial product load): return highest price (= كغم / largest pack).
        Always returns highest price as ultimate fallback to avoid showing 0.
        """
        if not available_uoms:
            return 0.0

        # Filter out zero-priced entries for comparisons
        non_zero = [u for u in available_uoms if u['price'] > 0]
        if not non_zero:
            return 0.0

        highest_price = max(u['price'] for u in non_zero)

        # Exact UoM match requested (e.g. from onchange_uom)
        if default_uom_id:
            for uom in available_uoms:
                if uom['id'] == default_uom_id and uom['price'] > 0:
                    return uom['price']
            # UoM found but price is 0 or not in list → fall through to highest

        # Default: always show highest price (كغم = most expensive pack)
        return highest_price

    def _get_price_for_uom(self, product, pricelist, uom_id):
        """
        Legacy helper - kept for backward compatibility with onchange_uom endpoint.
        New code should use _get_default_price_from_uoms instead.
        """
        if not pricelist:
            return product.list_price

        uom = request.env['uom.uom'].browse(uom_id)
        try:
            price = pricelist._get_product_price(product=product, quantity=1.0, uom=uom)
            return price
        except Exception as e:
            _logger.warning(f"[POS] Error getting price: {e}")
            return product.list_price
    
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
        """
        Get price when user changes UoM. Uses pricelist item mapping (product_packaging_id)
        directly instead of Odoo's standard price logic to ensure correct price is returned.
        """
        try:
            product = request.env['product.product'].browse(product_id)

            pricelist = None
            if pricelist_id:
                if isinstance(pricelist_id, list):
                    pricelist_id = pricelist_id[0]
                pricelist = request.env['product.pricelist'].browse(int(pricelist_id))
                if not pricelist.exists():
                    pricelist = None

            # Use pricelist items mapping for reliable price lookup
            available_uoms = self._get_uoms_from_pricelist(product, pricelist)
            price = self._get_default_price_from_uoms(available_uoms, uom_id)

            return {'success': True, 'price_unit': price}
        except Exception as e:
            _logger.error(f"[POS] Error in onchange_uom: {e}")
            return {'success': False, 'error': str(e)}
    
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
                    'pos_perfume.default_exchange_rate_usd_iqd', '1550.0'
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

    @http.route('/pos_perfume/export_excel/<int:order_id>', type='http', auth='user', methods=['GET'])
    def export_excel(self, order_id, **kwargs):
        """
        Generate and return an Excel file with all invoice details for the given order_id.
        """
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter
        except ImportError:
            return request.make_response(
                'openpyxl library is not installed. Run: pip install openpyxl',
                headers=[('Content-Type', 'text/plain')]
            )

        order = request.env['pos.perfume.order'].browse(order_id)
        if not order.exists():
            return request.make_response('Order not found', headers=[('Content-Type', 'text/plain')])

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Invoice"

        # ─── Styles ────────────────────────────────────────────────────────────
        header_fill   = PatternFill("solid", fgColor="2563EB")
        section_fill  = PatternFill("solid", fgColor="EFF6FF")
        title_fill    = PatternFill("solid", fgColor="1E3A5F")
        white_font    = Font(color="FFFFFF", bold=True, size=12)
        bold_font     = Font(bold=True, size=11)
        title_font    = Font(color="FFFFFF", bold=True, size=14)
        normal_font   = Font(size=11)
        center        = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left          = Alignment(horizontal="left",   vertical="center", wrap_text=True)
        right         = Alignment(horizontal="right",  vertical="center")
        thin          = Side(style="thin", color="BFDBFE")
        thin_border   = Border(left=thin, right=thin, top=thin, bottom=thin)

        def style_cell(cell, font=None, fill=None, alignment=None, border=None, number_format=None):
            if font:        cell.font        = font
            if fill:        cell.fill        = fill
            if alignment:   cell.alignment   = alignment
            if border:      cell.border      = border
            if number_format: cell.number_format = number_format

        # ─── Column widths ─────────────────────────────────────────────────────
        # Col: #, Internal Ref, Product, UoM, Warehouse, Qty, Unit Price, Disc%, Total
        col_widths = [5, 18, 35, 14, 16, 12, 14, 10, 14]
        for i, w in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

        row = 1

        # ─── Title row ─────────────────────────────────────────────────────────
        ws.merge_cells(f"A{row}:I{row}")
        title_cell = ws.cell(row=row, column=1, value="INVOICE / فاتورة")
        style_cell(title_cell, font=title_font, fill=title_fill, alignment=center)
        ws.row_dimensions[row].height = 32
        row += 1

        # ─── Invoice header info ───────────────────────────────────────────────
        exchange_rate = float(
            request.env['ir.config_parameter'].sudo().get_param(
                'pos_perfume.default_exchange_rate_usd_iqd', '1550.0'
            )
        )
        partner_name = order.partner_id.name if order.partner_id else ''
        partner_phone = order.partner_id.phone or order.partner_id.mobile or ''
        order_date = order.date.strftime('%Y-%m-%d %H:%M') if order.date else ''
        salesperson = order.user_id.name if order.user_id else ''
        pricelist = order.pricelist_id.name if order.pricelist_id else ''
        state_label = dict(order._fields['state'].selection).get(order.state, order.state)
        sale_order_name = order.sale_order_id.name if order.sale_order_id else ''
        sap_doc = order.sap_doc_num or ''
        note = order.note or ''

        header_pairs = [
            ("Invoice No. / رقم الفاتورة", order.name,       "Date / التاريخ",       order_date),
            ("Customer / العميل",           partner_name,      "Phone / الهاتف",       partner_phone),
            ("Status / الحالة",             state_label,       "Pricelist / قائمة الأسعار", pricelist),
            ("Salesperson / المندوب",       salesperson,       "Sale Order / أمر البيع",     sale_order_name),
            ("SAP Doc / مستند SAP",         sap_doc,           "Exchange Rate / سعر الصرف",  f"{exchange_rate:,.0f} IQD/USD"),
        ]
        if note:
            header_pairs.append(("Note / ملاحظة", note, "", ""))

        for label1, val1, label2, val2 in header_pairs:
            ws.merge_cells(f"A{row}:B{row}")
            ws.merge_cells(f"C{row}:E{row}")
            ws.merge_cells(f"F{row}:G{row}")
            ws.merge_cells(f"H{row}:I{row}")

            c1 = ws.cell(row=row, column=1, value=label1)
            c2 = ws.cell(row=row, column=3, value=val1)
            c3 = ws.cell(row=row, column=6, value=label2)
            c4 = ws.cell(row=row, column=8, value=val2)

            style_cell(c1, font=bold_font, fill=section_fill, alignment=left, border=thin_border)
            style_cell(c2, font=normal_font, alignment=left, border=thin_border)
            style_cell(c3, font=bold_font, fill=section_fill, alignment=left, border=thin_border)
            style_cell(c4, font=normal_font, alignment=left, border=thin_border)
            ws.row_dimensions[row].height = 18
            row += 1

        row += 1  # blank row

        # ─── Order lines header ────────────────────────────────────────────────
        line_headers = [
            "#",
            "Internal Ref / الكود",
            "Product / المنتج",
            "UoM / الوحدة",
            "Warehouse / المستودع",
            "Qty / الكمية",
            "Unit Price $",
            "Disc %",
            "Total $",
        ]
        for col_idx, header in enumerate(line_headers, 1):
            cell = ws.cell(row=row, column=col_idx, value=header)
            style_cell(cell, font=white_font, fill=header_fill, alignment=center, border=thin_border)
        ws.row_dimensions[row].height = 22
        row += 1

        # ─── Order lines data ──────────────────────────────────────────────────
        alt_fill = PatternFill("solid", fgColor="F0F7FF")
        total_usd = 0.0
        for idx, line in enumerate(order.order_line_ids, 1):
            line_fill    = alt_fill if idx % 2 == 0 else None
            internal_ref = line.product_id.default_code or ''
            product_name = line.product_id.name or ''
            uom_name     = line.product_uom_id.name if line.product_uom_id else ''
            warehouse    = line.warehouse_id.name if hasattr(line, 'warehouse_id') and line.warehouse_id else ''
            qty          = line.quantity
            unit_price   = line.price_unit
            disc         = line.discount if hasattr(line, 'discount') else 0.0
            subtotal     = line.price_subtotal
            total_usd   += subtotal

            # Col indices: 1=#, 2=ref, 3=product, 4=uom, 5=warehouse, 6=qty, 7=price, 8=disc, 9=total
            row_data = [idx, internal_ref, product_name, uom_name, warehouse, qty, unit_price, disc, subtotal]
            for col_idx, val in enumerate(row_data, 1):
                cell = ws.cell(row=row, column=col_idx, value=val)
                num_fmt = None
                if col_idx in (6, 7, 8, 9):
                    num_fmt = '#,##0.00'
                style_cell(cell,
                           font=normal_font,
                           fill=line_fill,
                           alignment=center if col_idx not in (2, 3) else left,
                           border=thin_border,
                           number_format=num_fmt)
            ws.row_dimensions[row].height = 18
            row += 1

        row += 1  # blank row

        # ─── Totals section ────────────────────────────────────────────────────
        total_iqd          = total_usd * exchange_rate
        total_iqd_rounded  = round(total_iqd / 1000) * 1000
        amount_subtotal    = order.amount_subtotal or total_usd
        amount_discount    = order.amount_discount or 0.0
        amount_tax         = order.amount_tax or 0.0

        totals = [
            ("Subtotal / المجموع الجزئي",              f"${amount_subtotal:,.2f}"),
            ("Discount / الخصم",                       f"-${amount_discount:,.2f}"),
            ("Tax / الضريبة",                          f"${amount_tax:,.2f}"),
            ("TOTAL (USD) / المجموع بالدولار",         f"${order.amount_total:,.2f}"),
            ("TOTAL (IQD) / المجموع بالدينار",         f"{int(total_iqd_rounded):,} IQD"),
        ]

        for label, value in totals:
            ws.merge_cells(f"A{row}:G{row}")
            ws.merge_cells(f"H{row}:I{row}")
            lc = ws.cell(row=row, column=1, value=label)
            vc = ws.cell(row=row, column=8, value=value)
            is_total = "TOTAL" in label
            lbl_font = Font(bold=True, size=12 if is_total else 11,
                            color="FFFFFF" if is_total else "1E3A5F")
            val_font = Font(bold=True, size=12 if is_total else 11,
                            color="FFFFFF" if is_total else "1E3A5F")
            lbl_fill = header_fill if is_total else section_fill
            val_fill = header_fill if is_total else section_fill
            style_cell(lc, font=lbl_font, fill=lbl_fill, alignment=left,   border=thin_border)
            style_cell(vc, font=val_font, fill=val_fill, alignment=center,  border=thin_border)
            ws.row_dimensions[row].height = 20 if is_total else 18
            row += 1

        # ─── Footer ────────────────────────────────────────────────────────────
        row += 1
        ws.merge_cells(f"A{row}:I{row}")
        footer = ws.cell(row=row, column=1,
                         value="Generated by POS Perfume System | نظام نقاط البيع")
        style_cell(footer, font=Font(size=9, italic=True, color="6B7280"), alignment=center)

        # ─── Save & stream ─────────────────────────────────────────────────────
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        excel_data = output.read()

        safe_name = (order.name or f'order_{order_id}').replace('/', '-')
        filename = f"Invoice_{safe_name}.xlsx"

        return request.make_response(
            excel_data,
            headers=[
                ('Content-Type',        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename="{filename}"'),
                ('Content-Length',      str(len(excel_data))),
            ]
        )
