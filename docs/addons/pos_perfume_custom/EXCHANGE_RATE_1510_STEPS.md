# إظهار سعر الصرف 1510 لجميع المستخدمين

## على السيرفر (مرة واحدة)

### 1) تحديث الكود
```bash
cd /home/lugalai/Lugal-ai
git pull
```

### 2) تحديث القيمة في قاعدة البيانات
```bash
PGPASSWORD=root psql -h localhost -p 5432 -U odoo_user -d nbs_lugalai -c "
UPDATE ir_config_parameter SET value = '1510.0', write_date = NOW() WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';
INSERT INTO ir_config_parameter (key, value, create_date, write_date, create_uid, write_uid)
SELECT 'pos_perfume.default_exchange_rate_usd_iqd', '1510.0', NOW(), NOW(), 1, 1
WHERE NOT EXISTS (SELECT 1 FROM ir_config_parameter WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd');
"
```

### 3) إعادة تشغيل Odoo
```bash
sudo systemctl restart odoo
```

### 4) ترقية الموديول من واجهة Odoo
- ادخل كأدمن → **التطبيقات**
- ابحث عن **POS Perfume** → **ترقية (Upgrade)**

---

## لكل مستخدم يرى حتى الآن 1500

المتصفح عنده **نسخة قديمة من الصفحة** مخزنة (كاش). يجب تحميل الصفحة من جديد:

1. **طريقة 1 (مفضلة):** فتح POS Perfume في **نافذة خاصة (Incognito/Private)** وتسجيل الدخول — سيظهر 1510.
2. **طريقة 2:** من نفس المتصفح:
   - افتح POS Perfume
   - اضغط **Ctrl+Shift+R** (أو Ctrl+F5) لتحديث قوي بدون كاش
3. **طريقة 3:** مسح كاش الموقع لـ Odoo من إعدادات المتصفح ثم إعادة فتح الصفحة.

---

## التحقق

- سجّل دخولاً بمستخدم عادي (غير الأدمن).
- افتح **أدوات المطوّر** (F12) → تبويب **Console**.
- ادخل إلى **POS Perfume**.
- إذا ظهر في الـ Console: **"سعر الصرف من الخادم (لجميع المستخدمين): 1510"** فالكود الجديد يعمل والسعر صحيح.
