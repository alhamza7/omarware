# Lugal Supply — موردين وحاويات

موديول منفصل عن الـ CRM: **موردين** (res.partner) و **حاويات** (lugal.supply.container).

- **أوامر الشراء (مشتريات)** و **سطور أمر الشراء** تبقى في **lugal_crm** وترتبط بالحاوية هنا عبر `container_id`.
- الدخول من **نفس واجهة الـ CRM**: كل الـ API تحت `/api/crm/supply/*` (الكونترولر في lugal_crm يستدعي موديل الحاوية من هذا الموديول).

## التبعيات
- **lugal_crm** يعتمد على **lugal_supply** لربط أمر الشراء بالحاوية.

## الموديلات
- `lugal.supply.container` — الحاويات (B/L, شركة التخليص, تتبع Searates، قسم أوروبا/الصين، إلخ).

## الموردين
- الموردون = `res.partner` حيث `supplier_rank > 0`.
- قائمة الموردين: من واجهة الـ CRM عبر `/api/crm/supply/vendors/list`.
