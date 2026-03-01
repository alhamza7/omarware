# إصلاحات نظام الأسعار في POS Perfume
**التاريخ:** 2026-02-23  
**الوقت:** ~07:00 – 08:00 UTC

---

## ملخص المشاكل التي تم حلها

| # | المشكلة | الملف |
|---|---------|-------|
| 1 | Pricelist مكررة تُسبب اختيار القائمة الخاطئة (كل أسعارها = 0) | DB + JS + Python |
| 2 | السعر الافتراضي يظهر لوحدة 0.5 كيلو بدلاً من كغم | `pos_perfume_controller.py` |
| 3 | منتجات UoM Group "0.25 كغم" تظهر سعر = 0 | `pos_perfume_controller.py` |
| 4 | سعر كغم خاطئ لـ 1,887 منتج (يظهر سعر الباكيج الصغير) | `pos_perfume_controller.py` |

---

## التفاصيل الكاملة

### 1. إصلاح Pricelist المكررة

**المشكلة:**  
في قاعدة البيانات كانت هناك **4 قوائم أسعار** بدلاً من 2:

```
id=2  SAP Price List 1  →  33,976 سجل، 29,958 سعر صحيح   ✅ الصحيحة
id=4  SAP Price List 1  →   3,845 سجل، جميعها = 0         ❌ مكررة فارغة
id=3  SAP Price List 2  →  10,827 سجل، 10,826 = صفر       (ثانوية)
id=5  SAP Price List 2  →  12,317 سجل، 76 غير صفري        (ثانوية)
```

JavaScript كان يبحث عن القائمة بالاسم (`includes('list 1')`). عند وجود نسختين بنفس الاسم، SQL يُرجعهما بترتيب غير ثابت → أحياناً تُختار id=4 (الأصفار) بدلاً من id=2 (الأسعار الصحيحة).

**الحل:**

**أ) قاعدة البيانات** — تعطيل النسخة المكررة:
```sql
UPDATE product_pricelist SET active = false WHERE id = 4;
```

**ب) `pos_perfume_screen.js` — `loadPricelists()`:**  
بدلاً من `find()` البسيط، يجلب الآن جميع المرشحين ويختار الذي يحتوي أكبر عدد من الأسعار غير الصفرية:
```javascript
// إذا وُجد أكثر من قائمة بنفس الاسم
const itemCounts = await this.orm.readGroup(
    'product.pricelist.item',
    [['pricelist_id', 'in', pl1Candidates.map(p => p.id)], ['fixed_price', '>', 0]],
    ['pricelist_id'], ['pricelist_id']
);
// يختار القائمة ذات أكبر عدد أسعار صحيحة
defaultPricelist = pl1Candidates.reduce((best, p) =>
    (countMap[p.id] || 0) > (countMap[best.id] || 0) ? p : best
, pl1Candidates[0]);
```

**ج) `sap_product_pricelist_sync.py` — `_get_or_create_pricelist()`:**  
بدلاً من `search(..., limit=1)` الذي يعيد نتيجة عشوائية عند وجود نسخ مكررة:
```python
# قبل: كان يُعيد أي نسخة عشوائياً
pricelist = self.env['product.pricelist'].search([...], limit=1)

# بعد: يجلب الكل ويختار الأكثر ثراءً بالأسعار
pricelists = self.env['product.pricelist'].search([...], order='id asc')
# يختار القائمة بأكبر عدد من الأسعار > 0
best = max(pricelists, key=lambda pl: item_count(pl))
```

---

### 2. إصلاح السعر الافتراضي (يظهر 0.5 كيلو بدلاً من كغم)

**المشكلة:**  
بعض المنتجات لها `product.uom_id = "0.5 كيلو"` في SAP وليس كغم. الكود السابق كان يبحث عن التطابق الدقيق مع `product.uom_id`، فيجد سعر 0.5 كيلو (71) بدلاً من عرض أعلى سعر (كغم = 140).

**الحل — دالة جديدة `_get_default_price_from_uoms()`:**

```python
def _get_default_price_from_uoms(self, available_uoms, default_uom_id=None):
    """
    - عند تحميل المنتج أول مرة (بدون uom_id): → أعلى سعر دائماً (= كغم)
    - عند تغيير وحدة القياس (مع uom_id): → السعر الدقيق للوحدة المختارة
    """
    if not available_uoms:
        return 0.0

    non_zero = [u for u in available_uoms if u['price'] > 0]
    if not non_zero:
        return 0.0

    highest_price = max(u['price'] for u in non_zero)

    if default_uom_id:
        for uom in available_uoms:
            if uom['id'] == default_uom_id and uom['price'] > 0:
                return uom['price']
        # لم يُوجد تطابق أو السعر صفر → fall through

    return highest_price  # افتراضي: أعلى سعر = كغم
```

**التطبيق في `get_product_data()`:**
```python
# تحميل أول مرة → أعلى سعر
if uom_id:
    default_price = self._get_default_price_from_uoms(available_uoms, uom_id)
else:
    default_price = self._get_default_price_from_uoms(available_uoms)  # أعلى سعر
```

**التطبيق في `onchange_uom()`:**
```python
# المستخدم اختار UoM محدد → استخدم available_uoms مباشرة (موثوق)
# بدلاً من pricelist._get_product_price (منطق أودو القياسي غير الموثوق)
available_uoms = self._get_uoms_from_pricelist(product, pricelist)
price = self._get_default_price_from_uoms(available_uoms, uom_id)
```

---

### 3. إصلاح منتجات UoM Group "0.25 كغم" (سعر = 0)

**المشكلة:**  
منتجات مثل `FL00146, R01447, ADF01254` لها UoM Group = "0.25 كغم" يحتوي فقط على `[id=33, id=39]`. لكن سعرها في الـ pricelist مخزن بـ `product_uom_id = Units (1)`:

```
product_packaging_id = NULL
product_uom_id       = Units (id=1)   ← ليس في المجموعة [33, 39]
fixed_price          = 38.25
```

فيلتر المجموعة يحذف هذا السعر (`1 not in [33, 39]`) → `uoms_with_prices = {}` → سعر = 0.

**الحل — Fallback بدون فلتر:**

```python
# Step 3: Process items WITH group filter
uoms_with_prices = self._process_pricelist_items(items, product, available_uom_ids)

# Step 4: إذا لم تُعطِ المجموعة أي نتيجة → أعد المحاولة بدون فلتر
if not uoms_with_prices and items:
    _logger.info("[POS] Group filter yielded no results - retrying without UoM filter")
    uoms_with_prices = self._process_pricelist_items(items, product, [])
```

---

### 4. إصلاح سعر كغم الخاطئ (1,887 منتج)

**المشكلة:**  
SAP يُخزّن سعر الوحدة الأساسية (كغم) بـ `product_uom_id = Units (id=1)` كرمز افتراضي. عند وجود UoM Group (مثل "لك" = [كغم, 50غم, 100غم...])، فيلتر المجموعة يحذف السعر لأن `Units (1) ∉ [34, 35, 36...]`:

```
# ALC00032 (مثبت ايزو سوبر) مثال:
Pricelist items:
  product_uom_id=Units(1), NO packaging, price=65.00  ← سعر كغم الحقيقي (يُحذف!)
  product_uom_id=Units(1), packaging=100غم,  price=7.50
  product_uom_id=Units(1), packaging=50غم,   price=4.00

النتيجة: كغم يظهر بسعر 7.50 (أعلى ما تبقى) بدلاً من 65.00
```

**الحل — Remapping تلقائي لـ Units → product.uom_id:**

```python
SAP_GENERIC_UOM_ID = 1  # "Units" - رمز SAP الافتراضي

def _process_pricelist_items(self, items, product, available_uom_ids):
    for item in items:
        if not item.product_packaging_id:
            raw_uom = item.product_uom_id or product.uom_id

            # SAP يستخدم Units(1) كرمز عام لوحدة القياس الأساسية
            # نُحوّله إلى product.uom_id الفعلية (كغم=34) ليمر فلتر المجموعة
            if raw_uom.id == self.SAP_GENERIC_UOM_ID:
                uom = product.uom_id  # كغم(34) → موجود في المجموعة ✓
            else:
                uom = raw_uom
            ...
```

**النتائج:**

| المنتج | قبل | بعد |
|--------|-----|-----|
| ALC00032 (مثبت ايزو سوبر) كغم | ~~7.50~~ ❌ | **65.00** ✅ |
| G01250 (كاليفورنيا دريم) | ~~0~~ ❌ | **600.00** ✅ |
| G01092 (اماجينيشن سوبر) | ~~0~~ ❌ | **450.00** ✅ |
| FL00146 | ~~0~~ ❌ | **8.50** ✅ |
| R01447 | ~~0~~ ❌ | **9.50** ✅ |

**عدد المنتجات المُصلحة: 1,887 منتج**

---

## الملفات المُعدَّلة

| الملف | التعديلات |
|-------|-----------|
| `addons/pos_perfume_custom/controllers/pos_perfume_controller.py` | دالة جديدة `_get_default_price_from_uoms`، إعادة هيكلة `_get_uoms_from_pricelist`، دالة جديدة `_process_pricelist_items`، Remapping لـ Units→product.uom_id، Fallback بدون فلتر، إصلاح `onchange_uom` |
| `addons/pos_perfume_custom/static/src/app/pos_perfume_screen.js` | إصلاح `loadPricelists` لاختيار القائمة الأكثر ثراءً عند وجود نسخ مكررة |
| `addons/sap_integration/models/sap_product_pricelist_sync.py` | إصلاح `_get_or_create_pricelist` لمنع إنشاء نسخ مكررة |
| **قاعدة البيانات** | `UPDATE product_pricelist SET active=false WHERE id=4` |

---

## منطق اختيار السعر (بعد الإصلاح)

```
عند اختيار منتج:
  1. جلب items من pricelist id=2 (SAP Price List 1)
  2. لكل item:
     a. إذا product_uom_id = Units(1) وبدون packaging
        → remap إلى product.uom_id الفعلية
     b. تطبيق فلتر UoM Group
  3. إذا الفلتر أعطى 0 نتائج → أعد بدون فلتر
  4. السعر المعروض = أعلى سعر (= كغم دائماً)

عند تغيير وحدة القياس:
  → البحث المباشر في available_uoms بالتطابق الدقيق
```
