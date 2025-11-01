# إصلاح خطأ Sale Order Line
## Fix Sale Order Line Error

📅 **التاريخ**: 28 أكتوبر 2025  
🐛 **الخطأ**: `product_uom` not found in model sale.order.line

---

## ❌ الخطأ

```
ValueError: Wrong @depends on '_compute_price_unit' 
(compute method of field sale.order.line.price_unit). 
Dependency field 'product_uom' not found in model sale.order.line.
```

---

## ✅ السبب

في **Odoo 19**، اسم الحقل تغير:
- ❌ القديم: `product_uom` (Odoo 16-18)
- ✅ الجديد: `product_uom_id` (Odoo 19)

---

## 🔧 الإصلاح

### تم إصلاحه في:
```
addons/uom_in_pricelist/models/sale_order_line_smart.py
```

### التغييرات:

#### 1. السطر 25 - @api.depends
```python
# قبل:
@api.depends('product_id', 'product_uom', 'product_uom_qty')

# بعد:
@api.depends('product_id', 'product_uom_id', 'product_uom_qty')
```

#### 2. السطر 44 - استخدام الحقل
```python
# قبل:
uom = line.product_uom or product.uom_id

# بعد:
uom = line.product_uom_id or product.uom_id
```

#### 3. السطر 98 - @api.onchange
```python
# قبل:
@api.onchange('product_uom', 'product_uom_qty')

# بعد:
@api.onchange('product_uom_id', 'product_uom_qty')
```

---

## 🚀 الخطوات التالية

### الخطوة 1: إيقاف Odoo

إذا كان Odoo قيد التشغيل:
```
اضغط Ctrl+C في terminal
```

### الخطوة 2: ترقية الموديول

```bash
python odoo-bin -c odoo.conf -u uom_in_pricelist -d lugal --stop-after-init
```

### الخطوة 3: إعادة تشغيل Odoo

```bash
python odoo-bin -c odoo.conf
```

### الخطوة 4: اختبار

```
1. افتح المتصفح
2. حدّث الصفحة (Ctrl+F5)
3. Sales → Orders → Create
4. اختر منتج
5. ✅ يجب أن يعمل الآن!
```

---

## 🧪 التحقق من الإصلاح

### الطريقة 1: اختبار يدوي

```
1. افتح Sales Order جديد
2. أضف منتج
3. غيّر UoM
4. إذا لم يظهر خطأ → ✅ تم الإصلاح!
```

### الطريقة 2: فحص اللوج

```bash
# شاهد آخر سطر في اللوج
tail -f odoo.log

# يجب أن ترى:
# ✅ لا أخطاء عند فتح Sales Order
```

---

## 📋 ملخص التغييرات

| الموقع | قبل | بعد |
|--------|-----|-----|
| @api.depends | `product_uom` | `product_uom_id` |
| استخدام الحقل | `line.product_uom` | `line.product_uom_id` |
| @api.onchange | `product_uom` | `product_uom_id` |

---

## ✅ النتيجة

```
الخطأ: ❌ product_uom not found
الحل: ✅ تغيير إلى product_uom_id
الحالة: ✅ تم الإصلاح
```

---

**الحالة**: ✅ جاهز للاختبار
**الوقت**: 2 دقيقة



