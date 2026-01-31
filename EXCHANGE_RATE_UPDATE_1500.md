# تحديث سعر الصرف إلى 1500 IQD
## Exchange Rate Update to 1500 IQD

---

## ✅ التحديثات المطبقة

### 1. ملفات POS Perfume
```
✓ addons/pos_perfume_custom/data/default_exchange_rate.xml
  1510.0 → 1500.0

✓ addons/pos_perfume_custom/models/res_config_settings.py
  default=1510.0 → default=1500.0

✓ addons/pos_perfume_custom/static/src/app/pos_perfume_screen.js
  exchangeRate: 1510 → exchangeRate: 1500
  get_param default '1510.0' → '1500.0'
  fallback 1510.0 → 1500.0
  error message 1510 → 1500

✓ addons/pos_perfume_custom/static/src/app/pos_perfume_screen_old.js
  exchangeRate: 1510 → exchangeRate: 1500
```

### 2. قاعدة البيانات
```sql
✓ ir_config_parameter
  pos_perfume.default_exchange_rate_usd_iqd = 1500.0

✓ res_currency_rate (USD)
  rate = 1/1500 = 0.00066667
```

---

## 🚀 تطبيق التحديث على السيرفر

### الطريقة الأوتوماتيكية (موصى بها):

```bash
cd /home/lugalai/Lugal-ai

# سحب التحديثات
git pull origin main

# تشغيل سكريبت التحديث الشامل
bash update_all_rates_to_1500.sh
```

### ماذا يفعل السكريبت؟
```
1. ✓ يحدث سعر Odoo الرئيسي (res_currency_rate)
2. ✓ يحدث سعر POS Perfume (ir_config_parameter)
3. ✓ يعرض التحقق من التحديث
4. ✓ يرقي وحدة pos_perfume_custom
5. ✓ يعيد تشغيل Odoo
```

---

## 📋 الطريقة اليدوية (خطوة بخطوة)

### 1. تحديث سعر Odoo الرئيسي

```bash
cd /home/lugalai/Lugal-ai
venv/bin/python update_exchange_rate.py 1500
```

### 2. تحديث سعر POS Perfume

```bash
sudo -u postgres psql nbs_lugalai
```

```sql
UPDATE ir_config_parameter
SET value = '1500.0'
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';

\q
```

### 3. ترقية الوحدة

```bash
venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai -u pos_perfume_custom --stop-after-init
```

### 4. إعادة تشغيل Odoo

```bash
pkill -9 -f odoo-bin
nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069 > odoo.log 2>&1 &
```

---

## 🌐 في المتصفح (خطوات حاسمة!)

### 1. مسح الكاش بالكامل

```
Ctrl+Shift+Delete
→ Time range: All time
→ Select:
  ✓ Cached images and files
  ✓ Cookies and other site data
  ✓ Hosted app data
→ Clear data
```

### 2. مسح LocalStorage

```
F12 (Developer Tools)
→ Application tab
→ Storage → Local Storage
→ Select: http://192.168.116.211:8069
→ Right click → Clear
→ Close Developer Tools
```

### 3. Hard Refresh

```
Ctrl+Shift+R
أو
Ctrl+F5
```

### 4. تسجيل خروج ودخول

```
1. سجل خروج من Odoo
2. أغلق المتصفح تماماً
3. افتح المتصفح من جديد
4. سجل دخول
5. افتح POS Perfume
```

---

## ✅ التحقق من التحديث

### في POS Perfume:

```
1. افتح POS Perfume
2. ابحث عن أي منتج
3. تحقق من السعر

مثال:
منتج سعره: 100 USD
السعر المتوقع: 150,000 IQD
الحساب: 100 × 1500 = 150,000 ✓
```

### في Console (F12):

```javascript
// يجب أن ترى:
[POS Perfume] Loaded exchange rate: 1500
```

### في قاعدة البيانات:

```bash
bash check_pos_perfume_rate.sh
```

يجب أن يعرض:
```
المفتاح: pos_perfume.default_exchange_rate_usd_iqd
السعر: 1500.0 IQD
```

---

## 📊 مقارنة الأسعار

| السعر القديم | السعر الجديد | الفرق | النسبة |
|--------------|--------------|-------|--------|
| 1510 IQD | 1500 IQD | -10 IQD | -0.66% |

### أمثلة:

| المبلغ بـ USD | القديم (1510) | الجديد (1500) | الفرق |
|--------------|---------------|---------------|-------|
| 100 | 151,000 | 150,000 | -1,000 |
| 500 | 755,000 | 750,000 | -5,000 |
| 1,000 | 1,510,000 | 1,500,000 | -10,000 |

---

## 🔍 استكشاف الأخطاء

### المشكلة: ما زال يعرض 1510

**الحل:**
```bash
# 1. تحقق من قاعدة البيانات
sudo -u postgres psql nbs_lugalai -c "
SELECT value FROM ir_config_parameter 
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';
"

# 2. إذا كان 1510، حدّثه يدوياً
sudo -u postgres psql nbs_lugalai -c "
UPDATE ir_config_parameter 
SET value = '1500.0' 
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';
"

# 3. أعد تشغيل Odoo
pkill -9 -f odoo-bin
nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069 > odoo.log 2>&1 &

# 4. امسح كاش المتصفح بالكامل
```

### المشكلة: الكاش لا يُمسح

**الحل:**
```
استخدم متصفح مختلف (Chrome → Firefox أو العكس)
أو
استخدم Incognito Mode: Ctrl+Shift+N
```

### المشكلة: السعر يرجع للقديم

**السبب:** ملفات JavaScript لم تُحدث

**الحل:**
```bash
# تحقق من أن الملفات محدثة
grep "exchangeRate: 15" addons/pos_perfume_custom/static/src/app/pos_perfume_screen.js

# يجب أن يعرض:
# exchangeRate: 1500

# إذا كان 1510، نفذ:
git pull origin main
venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai -u pos_perfume_custom --stop-after-init
```

---

## 📝 ملاحظات مهمة

### للطلبات الجديدة:
```
✓ جميع الطلبات الجديدة ستستخدم 1500 IQD
✓ يُطبق تلقائياً من تاريخ اليوم
✓ لا حاجة لتغيير الطلبات القديمة
```

### للطلبات القديمة:
```
✗ الطلبات المحفوظة سابقاً لن تتأثر
✗ ستبقى بالسعر القديم (1510)
ℹ️  هذا طبيعي ومقصود (حفظ السجل التاريخي)
```

### للمسودات:
```
✓ المسودات (Draft orders) يمكن إعادة حسابها
→ افتح الطلب → عدّل أي حقل → احفظ
→ سيُطبق السعر الجديد
```

---

## 🎯 الملخص

### ما تم تغييره:
```
✓ 5 ملفات في الكود
✓ 2 جداول في قاعدة البيانات
✓ 1 سكريبت تحديث جديد
✓ 1 ملف توثيق (هذا الملف)
```

### السعر الجديد:
```
1 USD = 1500 IQD
```

### المطلوب من المستخدم:
```
1. تشغيل: bash update_all_rates_to_1500.sh
2. مسح كاش المتصفح
3. إعادة فتح POS Perfume
4. اختبار
```

---

## 📞 الدعم

إذا واجهت أي مشكلة:

```bash
# 1. تحقق من اللوغات
tail -50 odoo.log

# 2. تحقق من السعر في قاعدة البيانات
bash check_pos_perfume_rate.sh

# 3. تحقق من حالة Odoo
ps aux | grep odoo-bin
```

---

**تم التحديث:** 29 يناير 2026  
**السعر الجديد:** 1500 IQD  
**الحالة:** ✅ جاهز للتطبيق
