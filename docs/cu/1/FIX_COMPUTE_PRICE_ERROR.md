# إصلاح نهائي - خطأ _compute_price
## Final Fix - _compute_price Error

🐛 **الخطأ**: `TypeError: _compute_price() got an unexpected keyword argument 'uom'`

---

## ✅ السبب

في **Odoo 19**، signature الـ `_compute_price` تغير:

### Odoo 16-18:
```python
def _compute_price(self, product, quantity, uom, date=False, currency=False):
```

### Odoo 19:
```python
def _compute_price(self, product, quantity, date=False, currency=False):
    # لا يوجد uom parameter!
```

---

## 🔧 الإصلاح

تم تعديل 3 ملفات:

### 1. `product_pricelist_item.py`
```python
# قبل:
def _compute_price(self, product, quantity, target_uom, date=False, currency=False):

# بعد:
def _compute_price(self, product, quantity, date=False, currency=False):
```

### 2. `product_pricelist_smart.py` - موقعين
```python
# قبل:
price = rule._compute_price(product, quantity, uom, date=date, currency=...)

# بعد:
if rule.compute_price == 'fixed':
    price = rule.fixed_price
else:
    price = rule._compute_price(product, quantity, date=date, currency=...)
```

---

## 🚀 تطبيق الإصلاح

تم الإصلاح في الملفات، الآن:

```bash
# أوقف Odoo (Ctrl+C)

# ترقية
python odoo-bin -c odoo.conf -u uom_in_pricelist -d lugal --stop-after-init

# أعد التشغيل
python odoo-bin -c odoo.conf
```

---

## ✅ التحقق

بعد التطبيق:
```
1. افتح Sales Order
2. أضف منتج
3. ✅ لا خطأ!
4. غيّر UoM
5. ✅ السعر يتغير!
```

---

**الحالة**: ✅ تم الإصلاح

