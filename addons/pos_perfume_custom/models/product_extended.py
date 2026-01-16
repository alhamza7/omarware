# -*- coding: utf-8 -*-
from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class ProductProductExtended(models.Model):
    """Extended Product model - Simplified to match Sale Order behavior"""
    _inherit = 'product.product'
    
    @api.model
    def get_product_info_for_pos(self, product_id, pricelist_id=None, uom_id=None):
        """
        Get complete product info including UoMs, price, and warehouses
        Similar to how Sale Order Line gets product info
        """
        product = self.browse(product_id)
        if not product.exists():
            return {}
        
        # Get pricelist
        if not pricelist_id:
            pricelist = self.env['product.pricelist'].search([('active', '=', True)], limit=1)
            pricelist_id = pricelist.id if pricelist else None
        
        pricelist = self.env['product.pricelist'].browse(pricelist_id) if pricelist_id else None
        
        # Get base UoM if not specified
        if not uom_id:
            uom_id = product.uom_id.id
        uom = self.env['uom.uom'].browse(uom_id)
        
        # Get price from pricelist (same way as sale order line)
        price = 0.0
        if pricelist:
            try:
                price = pricelist._get_product_price(product, 1.0, uom=uom)
            except Exception as e:
                _logger.warning(f"Error getting price from pricelist: {e}")
                price = product.list_price
        else:
            price = product.list_price
        
        # Convert to IQD
        price_iqd = self._convert_to_iqd(price)
        
        # Get all available UoMs from pricelist items
        available_uoms = self._get_available_uoms(product, pricelist_id)
        
        # Get warehouse stock
        warehouses = self._get_product_warehouses_simple(product_id)
        total_qty = sum(wh.get('quantity', 0) for wh in warehouses)
        
        return {
            'id': product.id,
            'name': product.name,
            'default_code': product.default_code or '',
            'list_price': product.list_price,
            'price': price,
            'price_iqd': price_iqd,
            'uom_id': uom.id,
            'uom_name': uom.name,
            'available_uoms': available_uoms,
            'warehouses': warehouses,
            'total_qty': total_qty,
        }
    
    def _get_available_uoms(self, product, pricelist_id):
        """Get all UoMs available for this product from pricelist items"""
        if not pricelist_id:
            return [{
                'id': product.uom_id.id,
                'name': product.uom_id.name,
                'price': product.list_price,
                'price_iqd': self._convert_to_iqd(product.list_price),
                'is_base': True,
            }]
        
        # Get pricelist items with UoM
        items = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist_id),
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('product_uom_id', '!=', False),
            '|',
            ('product_id', '=', False),
            ('product_id', '=', product.id),
        ])
        
        uoms = []
        seen_uom_ids = set()
        pricelist = self.env['product.pricelist'].browse(pricelist_id)
        
        for item in items:
            uom = item.product_uom_id
            if uom.id in seen_uom_ids:
                continue
            
            # Get price using pricelist (same as sale order)
            try:
                price = pricelist._get_product_price(product, 1.0, uom=uom)
            except:
                price = product.list_price
            
            uoms.append({
                'id': uom.id,
                'name': uom.name,
                'price': price,
                'price_iqd': self._convert_to_iqd(price),
                'is_base': uom.id == product.uom_id.id,
            })
            seen_uom_ids.add(uom.id)
        
        # Add base UoM if not in list
        if product.uom_id.id not in seen_uom_ids:
            try:
                price = pricelist._get_product_price(product, 1.0, uom=product.uom_id)
            except:
                price = product.list_price
            
            uoms.insert(0, {
                'id': product.uom_id.id,
                'name': product.uom_id.name,
                'price': price,
                'price_iqd': self._convert_to_iqd(price),
                'is_base': True,
            })
        
        return uoms if uoms else [{
            'id': product.uom_id.id,
            'name': product.uom_id.name,
            'price': product.list_price,
            'price_iqd': self._convert_to_iqd(product.list_price),
            'is_base': True,
        }]
    
    def _convert_to_iqd(self, usd_amount):
        """Convert USD to IQD"""
        try:
            usd_currency = self.env.ref('base.USD')
            iqd_currency = self.env.ref('base.IQD')
            
            if usd_currency and iqd_currency:
                return usd_currency._convert(
                    usd_amount,
                    iqd_currency,
                    self.env.company,
                    fields.Date.today()
                )
        except:
            pass
        
        return usd_amount * 1300
    
    def _get_product_priority_and_color(self, default_code):
        """
        Get priority order and color for products based on code prefix
        Returns: (priority, color_class, badge_text)
        color_class will be just 'r', 'adf', 'g', 'n1' (lowercase)
        R = 1 (red), ADF = 2 (blue), G = 3 (green), N1 = 4 (orange), others = 5 (gray)
        """
        if not default_code:
            return (5, '', '')
        
        code_upper = default_code.upper()
        
        if code_upper.startswith('R'):
            return (1, 'r', 'R')
        elif code_upper.startswith('ADF'):
            return (2, 'adf', 'ADF')
        elif code_upper.startswith('G'):
            return (3, 'g', 'G')
        elif code_upper.startswith('N1'):
            return (4, 'n1', 'N1')
        else:
            return (5, '', '')
    
    @api.model
    def search_products_for_pos(self, search_term, limit=50, pricelist_id=None):
        """
        Search products with full details: prices, warehouses, stock
        Returns data for the right panel search table
        
        Search rules (REBUILT FROM SCRATCH):
        1. "-" → Products with code starting with "S"
        2. Pure number (e.g., "200") → Exact number match in name/code
        3. Number with symbols (e.g., "-200", "200-") → Search in all fields
        4. Text → Search in all fields
        
        Results are ordered by:
        1. Priority (R, ADF, G, N1 first)
        2. Name, Foreign Name, Code
        """
        # Use sudo() to bypass record rules for POS search
        ProductSudo = self.sudo()
        
        # Normalize search term
        search_term = (search_term or '').strip()
        if not search_term:
            return []
        
        # Prepare helpers
        upper_term = search_term.upper()
        tokens = [t for t in upper_term.split() if t]
        
        # RULE 1: "-" → Products with code starting with "S"
        if search_term == '-':
            products = ProductSudo.search([
                ('sale_ok', '=', True),
                ('default_code', '=like', 'S%')
            ], limit=limit)
        
        # RULE 2: Pure number (e.g., "200") - exact numeric match logic
        elif search_term.isdigit():
            products = ProductSudo.search([
                ('sale_ok', '=', True),
                '|', '|',
                ('name', 'ilike', search_term),
                ('default_code', 'ilike', search_term),
                ('barcode', 'ilike', search_term),
            ], limit=limit * 3)
            
            # Filter in Python: number must appear as "مستقل" في الكود أو الاسم
            import re
            filtered_products = []
            for p in products:
                code = (p.default_code or '').upper()
                name = (p.name or '').upper()
                
                code_match = False
                if code:
                    code_parts = re.split(r'[^0-9]+', code)
                    if search_term in code_parts:
                        code_match = True
                
                name_match = False
                if name:
                    if (' ' + search_term + ' ') in name or \
                       name.startswith(search_term + ' ') or \
                       name.endswith(' ' + search_term):
                        name_match = True
                
                if code_match or name_match:
                    filtered_products.append(p)
            
            products = ProductSudo.browse([p.id for p in filtered_products[:limit]])
        
        # RULE 3: "-<number>" → رقم مسبوق بعلامة "-" في الكود أو الاسم (مثل S-200)
        elif search_term.startswith('-') and search_term[1:].isdigit():
            num = search_term[1:]
            like_pattern = f"-%{num}%"
            products = ProductSudo.search([
                ('sale_ok', '=', True),
                '|',
                ('default_code', 'ilike', like_pattern),
                ('name', 'ilike', like_pattern),
            ], limit=limit * 3)
            
            # فلترة إضافية: نضمن وجود "-<num>" فعلياً في النص
            filtered_products = []
            pattern = f"-{num}"
            for p in products:
                hay = f"{p.default_code or ''} {p.name or ''}".upper()
                if pattern.upper() in hay:
                    filtered_products.append(p)
            products = ProductSudo.browse([p.id for p in filtered_products[:limit]])
        
        # RULE 4: Text / complex query – multi-token AND search across fields
        else:
            # أولاً نستخدم ilike عام للحصول على مجموعة مرشّحة أوسع
            products = ProductSudo.search([
                ('sale_ok', '=', True),
                '|', '|', '|',
                ('name', 'ilike', search_term),
                ('default_code', 'ilike', search_term),
                ('barcode', 'ilike', search_term),
                ('foreign_name', 'ilike', search_term) if 'foreign_name' in self._fields else ('name', 'ilike', search_term),
            ], limit=limit * 3)
            
            # ثم نفلتر في Python بحيث يجب أن تظهر كل الكلمات (tokens)
            # في واحد أو أكثر من الحقول: الاسم، الاسم الأجنبي، الكود
            if tokens:
                filtered_products = []
                for p in products:
                    haystack = " ".join([
                        (p.name or ''),
                        getattr(p, 'foreign_name', '') or '',
                        (p.default_code or ''),
                    ]).upper()
                    
                    # كل كلمة من كلمات البحث يجب أن تكون موجودة
                    if all(tok in haystack for tok in tokens):
                        filtered_products.append(p)
                
                products = ProductSudo.browse([p.id for p in filtered_products[:limit]])
        
        # Get pricelist - default to "Price list 1"
        if not pricelist_id:
            # Try to find "Price list 1" - case insensitive search
            pricelist = self.env['product.pricelist'].sudo().search([
                ('name', 'ilike', 'Price list 1'),
                ('active', '=', True)
            ], limit=1)
            
            # If not found, try "list 1"
            if not pricelist:
                pricelist = self.env['product.pricelist'].sudo().search([
                    ('name', 'ilike', 'list 1'),
                    ('active', '=', True)
                ], limit=1)
            
            # If not found, try "Public Pricelist"
            if not pricelist:
                pricelist = self.env['product.pricelist'].sudo().search([
                    ('name', 'ilike', 'Public Pricelist'),
                    ('active', '=', True)
                ], limit=1)
            
            # If still not found, use first active pricelist
            if not pricelist:
                pricelist = self.env['product.pricelist'].sudo().search([('active', '=', True)], limit=1)
            
            pricelist_id = pricelist.id if pricelist else None
        
        result = []
        for product in products:
            try:
                # Get warehouses from SAP
                warehouses = []
                total_stock = 0
                
                if 'sap.product.warehouse.info' in self.env:
                    sap_infos = self.env['sap.product.warehouse.info'].sudo().search([
                        ('product_id', '=', product.id),
                    ])
                    
                    for sap_info in sap_infos:
                        qty = sap_info.current_qty_available or sap_info.last_available or 0
                        if qty > 0 and sap_info.warehouse_id:
                            warehouses.append({
                                'code': sap_info.sap_warehouse_code or sap_info.warehouse_id.code,
                                'name': sap_info.warehouse_id.name,
                                'qty': float(qty),
                            })
                            total_stock += qty
                
                # Get base price for BASE UoM from pricelist
                list_price_usd = 0.0
                if pricelist_id:
                    try:
                        pricelist = self.env['product.pricelist'].sudo().browse(pricelist_id)
                        if pricelist.exists():
                            # Use BASE UoM (product.uom_id) to get price
                            list_price_usd = pricelist._get_product_price(product, 1.0, uom=product.uom_id)
                            # If pricelist returns 0, try with partner context (some pricelists need partner)
                            if list_price_usd == 0.0:
                                # Try with company as partner
                                list_price_usd = pricelist._get_product_price(
                                    product, 1.0, uom=product.uom_id,
                                    partner=self.env.company.partner_id
                                )
                            # If still 0, fallback to product list_price
                            if list_price_usd == 0.0:
                                list_price_usd = product.list_price
                        else:
                            list_price_usd = product.list_price
                    except Exception as e:
                        _logger.warning(f"Error getting pricelist price for product {product.id}: {e}")
                        list_price_usd = product.list_price
                else:
                    # No pricelist - use product list_price
                    list_price_usd = product.list_price
                
                # Convert to IQD
                list_price_iqd = list_price_usd * 1300  # Simple conversion
                
                # Try to use Odoo currency conversion
                try:
                    usd_currency = self.env.ref('base.USD', raise_if_not_found=False)
                    iqd_currency = self.env.ref('base.IQD', raise_if_not_found=False)
                    if usd_currency and iqd_currency:
                        list_price_iqd = usd_currency._convert(
                            list_price_usd,
                            iqd_currency,
                            self.env.company,
                            fields.Date.today()
                        )
                except:
                    pass
                
                foreign_name = ''
                if hasattr(product, 'foreign_name'):
                    foreign_name = product.foreign_name or ''
                
                # Get SAP UoM Group name
                sap_uom_group_name = ''
                if hasattr(product, 'sap_uom_group_id') and product.sap_uom_group_id:
                    sap_uom_group_name = product.sap_uom_group_id.name
                elif hasattr(product.product_tmpl_id, 'sap_uom_group_id') and product.product_tmpl_id.sap_uom_group_id:
                    sap_uom_group_name = product.product_tmpl_id.sap_uom_group_id.name
                # Fallback to UoM name if no UoM Group
                if not sap_uom_group_name:
                    sap_uom_group_name = product.uom_id.name
                
                # Get priority and color info
                priority, color_class, badge_text = self._get_product_priority_and_color(product.default_code)
                
                result.append({
                    'id': product.id,
                    'name': product.name,
                    'default_code': product.default_code or '',
                    'foreign_name': foreign_name,
                    'list_price': list_price_usd,
                    'price_iqd': list_price_iqd,
                    'uom_id': product.uom_id.id,
                    'uom_name': product.uom_id.name,
                    'sap_uom_group_name': sap_uom_group_name,  # SAP UoM Group name
                    'categ_name': product.categ_id.name if product.categ_id else '',
                    'qty_available': total_stock,
                    'warehouses': warehouses,
                    'image_url': f'/web/image/product.product/{product.id}/image_128' if product.image_128 else '',
                    # Priority and color info
                    'priority': priority,
                    'color_class': color_class,
                    'badge_text': badge_text,
                })
            except Exception as e:
                _logger.error(f"Error processing product {product.id}: {str(e)}")
                continue
        
        # Sort results by priority (R, ADF, G, N1 first), then by name
        result.sort(key=lambda x: (x['priority'], x['name'] or '', x['foreign_name'] or '', x['default_code'] or ''))
        
        return result
    
    def _get_product_warehouses_simple(self, product_id):
        """Get warehouse stock - simplified version"""
        try:
            # Use stock.quant to get warehouse info directly
            query = """
                SELECT 
                    sw.id as warehouse_id,
                    sw.name as warehouse_name,
                    sw.code as warehouse_code,
                    SUM(sq.quantity - sq.reserved_quantity) as available_qty
                FROM stock_quant sq
                JOIN stock_location sl ON sq.location_id = sl.id
                JOIN stock_warehouse sw ON sl.warehouse_id = sw.id
                WHERE sq.product_id = %s
                    AND sl.usage = 'internal'
                    AND (sq.quantity - sq.reserved_quantity) > 0
                GROUP BY sw.id, sw.name, sw.code
                ORDER BY sw.name
            """
            
            self.env.cr.execute(query, (product_id,))
            results = self.env.cr.dictfetchall()
            
            warehouses = []
            for row in results:
                warehouses.append({
                    'id': row['warehouse_id'],
                    'name': row['warehouse_name'],
                    'code': row['warehouse_code'] or row['warehouse_name'][:5],
                    'quantity': row['available_qty'],
                })
            
            return warehouses
            
        except Exception as e:
            _logger.error(f"Error getting warehouses: {str(e)}")
            return []
