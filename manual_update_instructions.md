# تعليمات التحديث اليدوي من GitHub

إذا كان Git pull لا يعمل، اتبع هذه الخطوات:

## الطريقة 1: استخدام Git Pull

```bash
cd ~/Lugal-ai
git pull origin main
# أو
git pull origin master
```

## الطريقة 2: تحديث يدوي للملفات المهمة

إذا كان Git لا يعمل، قم بنسخ الملفات التالية يدوياً:

### الملفات المهمة:

1. **addons/pos_perfume_custom/models/pos_perfume_order.py**
   - يجب أن يحتوي على: `sync_successful = False`
   - يجب أن يحتوي على: `Manual SAP sync`

2. **addons/sap_integration/models/sale_order_sap.py**
   - يجب أن يحتوي على: `❌ Error sending quotation`
   - يجب أن يحتوي على: `finally:`
   - يجب أن يحتوي على: `FAILED - Check errors above`

3. **addons/pos_perfume_custom/static/src/app/pos_perfume_screen.js**
   - يجب أن يحتوي على: `catch (rpcError)`

## الطريقة 3: استخدام السكريبت الشامل

```bash
chmod +x update_from_github_and_fix.sh
./update_from_github_and_fix.sh
```

## التحقق من التحديث

بعد التحديث، تحقق من:

```bash
# التحقق من pos_perfume_order.py
grep -n "sync_successful = False" addons/pos_perfume_custom/models/pos_perfume_order.py

# التحقق من sale_order_sap.py
grep -n "❌ Error sending quotation" addons/sap_integration/models/sale_order_sap.py

# التحقق من pos_perfume_screen.js
grep -n "catch (rpcError)" addons/pos_perfume_custom/static/src/app/pos_perfume_screen.js
```

إذا كانت النتائج فارغة، الملفات لم يتم تحديثها.

## بعد التحديث

1. تحديث الوحدات:
```bash
venv/bin/python odoo-bin -c odoo.conf -d lugal \
    -u pos_perfume_custom,sap_integration \
    --stop-after-init
```

2. مسح الكاش:
```bash
venv/bin/python clear_cache_from_db.py
```

3. إعادة تشغيل Odoo:
```bash
nohup venv/bin/python odoo-bin -c odoo.conf -d lugal --http-port=8069 > odoo.log 2>&1 &
```

