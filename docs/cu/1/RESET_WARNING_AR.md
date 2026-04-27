# ⚠️ تحذير - تصفير البيانات

---

## 🔴 انتبه!

سيتم حذف:
- ✗ جميع المنتجات المستوردة من SAP (12,000+)
- ✗ جميع Extended Info (14,000+)
- ✗ جميع UoM Sync (20+)
- ✗ جميع Warehouse Info
- ✗ جميع Pricelist Sync
- ✗ جميع Stock Quants للمنتجات
- ✗ جميع Migration Wizards

---

## ✅ ما لن يُحذف:

- ✓ المنتجات الافتراضية (بدون default_code)
- ✓ المخزن الرئيسي (My Company)
- ✓ SAP Backend (الاتصال)
- ✓ الإعدادات

---

## 🚀 الخطوات:

### 1. شغّل السكريبت:
```bash
Get-Content reset_sap_data.py | python odoo-bin shell -c odoo.conf -d lugal --no-http
```

### 2. انتظر الحذف (~2 دقيقة)

### 3. شغّل Migration الجديد المحسّن!

---

**هل أنت متأكد؟**




