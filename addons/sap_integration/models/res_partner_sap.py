# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    sap_synced = fields.Boolean(
        string='Synced to SAP',
        default=False,
        copy=False,
        help="تم إرسال هذا العميل إلى SAP"
    )
    
    def web_save(self, vals, specification: dict[str, dict], next_id=None) -> list[dict]:
        """Override web_save to handle SAP sync for new partners"""
        was_empty = not self
        _logger.info(f"=== res_partner_sap.web_save() CALLED with self={self}, was_empty={was_empty}, vals keys={list(vals.keys()) if vals else 'None'} ===")
        
        # استدعاء web_save الأصلي
        result = super(ResPartner, self).web_save(vals, specification, next_id)
        
        _logger.info(f"=== After super().web_save(): result type={type(result)}, result length={len(result) if result else 0}, result={result[:1] if result else 'None'} ===")
        
        # إذا كان record جديد (self كان فارغ)، نحاول إرساله إلى SAP
        if was_empty and result and len(result) > 0:
            partner_id_raw = result[0].get('id')
            _logger.info(f"=== Found partner_id_raw in result: {partner_id_raw}, type: {type(partner_id_raw)}, bool(partner_id_raw): {bool(partner_id_raw)} ===")
            
            # التعامل مع NewId إذا كان موجوداً
            from odoo.api import NewId
            if isinstance(partner_id_raw, NewId):
                partner_id = partner_id_raw.origin
                _logger.info(f"=== partner_id_raw is NewId, using origin: {partner_id} ===")
            else:
                partner_id = partner_id_raw
            
            _logger.info(f"=== Final partner_id: {partner_id}, type: {type(partner_id)}, bool(partner_id): {bool(partner_id)} ===")
            
            if partner_id:
                _logger.info(f"=== partner_id is truthy, proceeding to browse ===")
                try:
                    partner = self.env['res.partner'].browse(partner_id)
                    _logger.info(f"=== After browse: partner={partner}, exists={partner.exists()}, len={len(partner)} ===")
                    if not partner.exists():
                        _logger.error(f"=== Partner {partner_id} does not exist after browse ===")
                        return result
                    _logger.info(f"=== Partner Created via web_save: {partner.name} (ID: {partner.id}), customer_rank={partner.customer_rank}, ref={partner.ref}, is_company={partner.is_company} ===")
                    
                    # إرسال partner إلى SAP إذا لم يكن له ref (CardCode) بعد
                    # نرسل جميع الـ partners الجدد إلى SAP بغض النظر عن customer_rank
                    if not partner.ref:
                        _logger.info(f"New partner created via web_save: {partner.name} (ID: {partner.id}), attempting to sync to SAP...")
                        try:
                            partner._send_to_sap()
                        except Exception as e:
                            _logger.warning(f"Could not send partner {partner.name} to SAP on web_save: {e}", exc_info=True)
                    else:
                        _logger.info(f"Partner {partner.name} (ID: {partner.id}) already has ref (CardCode): {partner.ref}, skipping SAP sync")
                except Exception as e:
                    _logger.error(f"Error accessing partner {partner_id}: {e}", exc_info=True)
            else:
                _logger.warning(f"=== partner_id is None or False in result[0] ===")
        else:
            _logger.info(f"=== Condition not met: was_empty={was_empty}, result={result is not None}, len(result)={len(result) if result else 0} ===")
        
        return result
    
    @api.model
    def create(self, vals):
        """Override create to send partner to SAP after creation"""
        _logger.info(f"=== res_partner_sap.create() CALLED with vals: {vals} ===")
        partner = super(ResPartner, self).create(vals)
        
        _logger.info(f"=== Partner Created: {partner.name} (ID: {partner.id}), customer_rank={partner.customer_rank}, ref={partner.ref}, is_company={partner.is_company} ===")
        
        # إرسال partner إلى SAP إذا لم يكن له ref (CardCode) بعد
        # نرسل جميع الـ partners الجدد إلى SAP بغض النظر عن customer_rank
        if not partner.ref:
            _logger.info(f"New partner created: {partner.name} (ID: {partner.id}), attempting to sync to SAP...")
            try:
                partner._send_to_sap()
            except Exception as e:
                _logger.warning(f"Could not send partner {partner.name} to SAP on create: {e}", exc_info=True)
                # لا نرفع exception حتى لا نمنع حفظ الـ partner في Odoo
        else:
            _logger.info(f"Partner {partner.name} (ID: {partner.id}) already has ref (CardCode): {partner.ref}, skipping SAP sync")
        
        return partner
    
    def write(self, vals):
        """Override write to update partner in SAP when needed"""
        result = super(ResPartner, self).write(vals)
        
        # تحديث في SAP إذا تم تحديث بيانات مهمة وكان partner موجود في SAP
        for partner in self:
            if partner.ref and partner.sap_synced:
                # إذا تم تحديث بيانات مهمة
                if any(field in vals for field in ['name', 'email', 'phone', 'street', 'city', 'zip', 'country_id']):
                    try:
                        partner._send_to_sap()
                    except Exception as e:
                        _logger.warning(f"Could not update partner {partner.name} in SAP on write: {e}")
        
        return result
    
    def _send_to_sap(self):
        """إرسال partner إلى SAP ومزامنته"""
        for partner in self:
            _logger.info(f">>> Starting _send_to_sap for partner {partner.name} <<<")
            try:
                # التحقق من وجود backend نشط
                backend = self.env['sap.backend'].search([
                    ('active', '=', True)
                ], limit=1)
                
                if not backend:
                    _logger.warning(f"No active SAP backend found for partner {partner.name}")
                    return
                
                _logger.info(f"Found active SAP backend: {backend.name} (id={backend.id})")
                
                # الحصول على connection
                connection = backend.get_connection()
                
                # إعداد بيانات partner للـ SAP (بدون CardCode - سيولدها SAP تلقائياً)
                partner_data = self._prepare_partner_data_for_sap(partner, connection)
                card_code = partner_data.get('CardCode', '')
                if card_code:
                    _logger.info(f"Prepared partner data for SAP: CardName={partner_data.get('CardName')}, CardCode={card_code}")
                else:
                    _logger.info(f"Prepared partner data for SAP: CardName={partner_data.get('CardName')}, CardCode will be generated by SAP from Numbering Series")
                
                # طباعة البيانات المرسلة بالكامل للتحقق
                import json
                _logger.info(f"Full partner data being sent to SAP: {json.dumps(partner_data, indent=2, default=str)}")
                
                if partner.ref and partner.sap_synced:
                    # تحديث partner موجود
                    _logger.info(f"Updating partner {partner.name} in SAP (CardCode: {partner.ref})")
                    result = connection.update_business_partner(partner.ref, partner_data)
                    if result:
                        _logger.info(f"Partner {partner.name} updated in SAP: CardCode={result.get('CardCode', partner.ref)}")
                else:
                    # إنشاء partner جديد
                    if card_code:
                        _logger.info(f"Creating partner {partner.name} in SAP with CardCode: {card_code}")
                    else:
                        _logger.info(f"Creating partner {partner.name} in SAP (SAP will generate CardCode from Numbering Series)")
                    result = connection.create_business_partner(partner_data)
                    
                    if result:
                        # حفظ CardCode من SAP في حقل ref
                        returned_card_code = result.get('CardCode', '')
                        
                        if returned_card_code:
                            partner.sudo().write({
                                'ref': returned_card_code,
                                'sap_synced': True,
                            })
                            _logger.info(f"Partner {partner.name} synced to SAP: CardCode={returned_card_code}")
                        else:
                            _logger.warning(f"Partner {partner.name} created in SAP but no CardCode returned")
                
            except Exception as e:
                _logger.error(f"Error sending partner {partner.name} to SAP: {str(e)}", exc_info=True)
                # لا نرفع exception حتى لا نمنع حفظ الـ partner في Odoo
    
    def _prepare_partner_data_for_sap(self, partner, connection=None):
        """إعداد بيانات partner للـ SAP Service Layer (الطريقة الموصى بها: SAP ينشئ CardCode، Notes+Address إلزاميان)"""
        partner_data = {
            'CardName': partner.name or '',
            'CardType': 'cCustomer',
        }
        
        # عند التحديث فقط: إرسال CardCode لأن الطلب PATCH يستهدف سجلاً موجوداً
        if partner.ref and partner.sap_synced:
            partner_data['CardCode'] = partner.ref
            _logger.info(f"Using existing CardCode for update: {partner.ref}")
        else:
            # إنشاء جديد: لا نرسل CardCode - SAP ينشئه تلقائياً من السلسلة (Series)
            if connection:
                try:
                    series_number = connection.get_ibg_series_number()
                    partner_data['Series'] = series_number
                    _logger.info(f"Creating new partner in SAP (Series: {series_number}), CardCode will be generated by SAP")
                except Exception as e:
                    _logger.warning(f"Error getting Series number: {e}, using default 72")
                    partner_data['Series'] = 72
            else:
                partner_data['Series'] = 72
            partner_data['GroupCode'] = 100
        
        # Notes و Address إلزاميان معاً (حل validation في SAP) - قيم غير فارغة
        _notes = (partner.city or partner.street or partner.name or "—").strip() or "—"
        _address = (partner.street or partner.city or partner.name or "—").strip() or "—"
        partner_data['Notes'] = _notes
        partner_data['Address'] = _address
        
        # إضافة البريد الإلكتروني
        if partner.email:
            partner_data['EmailAddress'] = partner.email
        
        # إضافة الهاتف
        if partner.phone:
            partner_data['Phone1'] = partner.phone
        
        if partner.street2:
            partner_data['Block'] = partner.street2
        
        if partner.city:
            partner_data['City'] = partner.city
        
        if partner.zip:
            partner_data['ZipCode'] = partner.zip
        
        partner_data['Country'] = (partner.country_id and partner.country_id.code) or 'IQ'
        
        # إضافة الموقع الإلكتروني
        if partner.website:
            partner_data['Website'] = partner.website
        
        # إضافة VAT (Tax ID)
        if partner.vat:
            partner_data['VatLiable'] = 'Y'
            partner_data['FederalTaxID'] = partner.vat
        
        # إضافة BPAddresses (مطلوب في بعض إصدارات SAP)
        address_data = {}
        if partner.street:
            address_data['Street'] = partner.street
        if partner.street2:
            address_data['Block'] = partner.street2
        if partner.city:
            address_data['City'] = partner.city
        if partner.zip:
            address_data['ZipCode'] = partner.zip
        if partner.country_id:
            address_data['Country'] = partner.country_id.code or ''
        
        if address_data:
            partner_data['BPAddresses'] = [
                {
                    'AddressName': 'BillTo',
                    'AddressType': 'bo_BillTo',
                    **address_data
                },
                {
                    'AddressName': 'ShipTo',
                    'AddressType': 'bo_ShipTo',
                    **address_data
                }
            ]
        
        return partner_data
    
    def _generate_card_code(self, partner):
        """إنشاء CardCode تلقائياً من اسم الـ partner"""
        import re
        
        # محاولة الحصول على Default Series من Odoo (مثل IBG للعملاء)
        prefix = 'IBG'  # Default Series للعملاء في Odoo
        try:
            # البحث عن sequence للعملاء
            sequence = self.env['ir.sequence'].search([
                ('code', '=', 'res.partner'),
                ('company_id', '=', partner.company_id.id if partner.company_id else False)
            ], limit=1)
            if sequence and sequence.prefix:
                prefix = sequence.prefix.strip().upper()
                # إزالة الأحرف الخاصة من prefix
                prefix = re.sub(r'[^A-Za-z0-9]', '', prefix)
        except Exception as e:
            _logger.debug(f"Could not get sequence prefix, using default: {e}")
        
        # استخدام ID كرقم بعد البادئة (حد أقصى 5 أرقام)
        # Format: PREFIX + ID (max 5 digits after prefix)
        partner_id_str = str(partner.id)
        
        # إذا كان ID أكثر من 5 أرقام، نأخذ آخر 5 أرقام
        if len(partner_id_str) > 5:
            partner_id_str = partner_id_str[-5:]
        
        # إنشاء CardCode: PREFIX + ID (5 digits max)
        card_code = f"{prefix}{partner_id_str.zfill(5)}"
        
        # التأكد من أن CardCode لا يتجاوز 15 حرف (حد SAP)
        if len(card_code) > 15:
            # إذا كان prefix طويلاً، نأخذ أول 10 أحرف من prefix + 5 أرقام
            max_prefix_length = 15 - 5
            prefix = prefix[:max_prefix_length]
            card_code = f"{prefix}{partner_id_str.zfill(5)}"
        
        return card_code

