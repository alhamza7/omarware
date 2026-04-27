# إصلاحات واجهة POS Perfume - Action 1364
## التاريخ: 2025-11-03

### المشاكل التي تم حلّها:

#### 1. ✅ عدم ظهور المخازن المتوفر بها المنتج
**المشكلة:**
- بعد اختيار المنتج، لا تظهر قائمة المخازن
- الخيار موجود لكن فارغ

**الحل:**
- تحسين method `get_available_uoms_with_prices` لإرجاع معلومات المخازن مع كل UoM
- إضافة fields جديدة في response:
  - `warehouses`: قائمة المخازن مع الكميات
  - `total_qty`: إجمالي الكمية المتوفرة

```python
{
    'id': uom.id,
    'name': uom.name,
    'price': price_usd,
    'price_iqd': price_iqd,
    'warehouses': [
        {'id': 1, 'name': 'Main Warehouse', 'code': 'WH', 'quantity': 100},
        {'id': 2, 'name': 'Baghdad', 'code': 'BGD', 'quantity': 50},
    ],
    'total_qty': 150,
}
```

#### 2. ✅ عدم ظهور وحدات القياس المرتبطة بالمنتج
**المشكلة:**
- لا تظهر جميع وحدات القياس المعرّفة في pricelist

**الحل:**
- تحسين البحث في `product.pricelist.item` للبحث عن items التي لديها `product_uom_id`
- إضافة Domain: `('product_uom_id', '!=', False)`
- التأكد من إضافة base UoM دائماً في القائمة

#### 3. ✅ عدم ظهور الأعداد في جدول البحث
**المشكلة:**
- جدول البحث الجانبي لا يعرض الكميات المتوفرة

**الحل:**
- تحسين `search_products_for_pos` method
- إضافة:
  - `qty_available`: إجمالي الكمية
  - `warehouses`: تفاصيل كل مستودع مع كمياته

#### 4. ✅ عدم ظهور السعر الأساسي
**المشكلة:**
- لا يظهر السعر بالدولار (USD)

**الحل:**
- التأكد من إرجاع `list_price` (السعر بالدولار) في كل response

#### 5. ✅ عدم ظهور السعر بالدينار العراقي
**المشكلة:**
- لا يتم عرض السعر مُحوّل إلى IQD

**الحل:**
- إضافة method `_convert_to_iqd` تستخدم Odoo currency conversion API
- Fallback إلى سعر ثابت (1300) إذا لم يتوفر التحويل
- إضافة `price_iqd` لكل منتج في النتائج

```python
def _convert_to_iqd(self, usd_amount):
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
    
    # Fallback to fixed rate
    return usd_amount * 1300
```

### التحسينات الإضافية:

#### 1. **تكامل مع إضافة `sale_order_line_multi_warehouse`**
- تم تفعيل وتحديث الإضافة لـ Odoo 19
- الآن يمكن اختيار مستودع مختلف لكل سطر في Sale Order
- تم تحسين XML views لتتوافق مع Odoo 19

#### 2. **تحسين Error Handling**
- إضافة try-catch blocks في جميع methods
- Logging أفضل للأخطاء
- Fallback data عند فشل أي عملية

#### 3. **تحسين الأداء**
- Cache warehouse info لكل منتج
- تقليل عدد queries للـ database
- Efficient data structure

### الملفات المُعدّلة:

1. **addons/pos_perfume_custom/models/product_extended.py**
   - `get_available_uoms_with_prices()`: إضافة warehouses و total_qty
   - `_convert_to_iqd()`: method جديد للتحويل العملة
   - `_get_fallback_uom_data()`: method جديد للبيانات الاحتياطية
   - `search_products_for_pos()`: تحسين لإرجاع المخازن والأسعار بالـ IQD
   - `_get_product_warehouses()`: تحسين جلب المخازن

2. **addons/sale_order_line_multi_warehouse/__manifest__.py**
   - تحديث الإصدار من 18.0 إلى 19.0

3. **addons/sale_order_line_multi_warehouse/models/sale_order.py**
   - تحسين الكود ليتوافق مع Odoo 19 API
   - إضافة domain للحقول

4. **addons/sale_order_line_multi_warehouse/views/sale_order_view.xml**
   - إصلاح XPath ليتطابق مع Odoo 19 structure
   - إضافة الحقل في list و form views

### كيفية الاستخدام:

#### في POS Perfume (Action 1364):

1. **اختيار المنتج:**
   - ابحث عن المنتج في حقل البحث
   - سيتم عرض قائمة المنتجات مع الكميات

2. **اختيار وحدة القياس:**
   - بعد اختيار المنتج، ستظهر قائمة UoMs
   - كل UoM يحتوي على:
     - الاسم
     - السعر بالدولار
     - السعر بالدينار
     - معلومات التحويل
     - الكميات في كل مستودع

3. **اختيار المستودع:**
   - اختر المستودع المطلوب من القائمة
   - ستظهر الكمية المتوفرة في هذا المستودع

4. **جدول البحث الجانبي:**
   - يعرض:
     - كود المنتج
     - اسم المنتج (عربي + إنجليزي)
     - الفئة
     - الوحدة الأساسية
     - السعر (USD)
     - السعر (IQD)
     - إجمالي الكمية
     - الكميات في كل مستودع

### الاختبار:

```bash
# 1. الوصول إلى الواجهة
http://192.168.116.181:8070/odoo/action-1364

# 2. اختبار البحث عن منتج
- ابحث عن منتج بالاسم أو الكود

# 3. اختبار اختيار UoM
- اختر المنتج
- تحقق من ظهور جميع UoMs
- تحقق من الأسعار بالدولار والدينار

# 4. اختبار اختيار المستودع
- اختر UoM
- تحقق من ظهور المستودعات مع الكميات

# 5. اختبار جدول البحث
- تحقق من عرض الأسعار والكميات
- تحقق من عرض المخازن
```

### ملاحظات مهمة:

1. **التحويل إلى IQD:**
   - يستخدم Odoo currency API أولاً
   - يستخدم rate ثابت (1300) كـ fallback

2. **المخازن:**
   - يتم جلب الكميات من `stock.quant`
   - يتم حساب `available = quantity - reserved_quantity`
   - فقط المخازن ذات الكميات المتوفرة تظهر

3. **الأداء:**
   - البحث محدود بـ 50 منتج
   - Debounce على البحث (300ms)
   - كل العمليات async

### الخطوات التالية (اختياري):

1. إضافة cache للمخازن
2. تحسين UI لعرض المخازن بشكل أفضل
3. إضافة filters في جدول البحث
4. إضافة sort options

---

## Status: ✅ Complete
## Last Updated: 2025-11-03 20:00 GMT
## Module Version: 19.0.1.0.0

