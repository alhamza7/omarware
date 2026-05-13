# حل مشكلة menu_sap_tools

## المشكلة:
```
ValueError: External ID not found in the system: sap_integration.menu_sap_tools
```

## الحل:
تم إصلاح جميع المراجع في الكود. المشكلة الآن هي أن الخادم لم يسحب التحديثات بعد.

## الخطوات المطلوبة على الخادم:

### 1. التأكد من سحب جميع التحديثات:
```bash
cd ~/Lugal-ai
git status
git pull origin main
```

### 2. التحقق من الملفات المُصلحة:
```bash
# التحقق من أن sap_menu_structure.xml يحتوي على menu_sap_tools
grep -n "menu_sap_tools" addons/sap_integration/views/sap_menu_structure.xml

# التحقق من أن wizards تستخدم menu_sap_tools بدون prefix
grep -n "parent.*menu_sap_tools" addons/sap_integration/wizard/*.xml
```

### 3. إذا كان هناك تغييرات محلية، احفظها:
```bash
git stash
git pull origin main
git stash pop  # إذا أردت استعادة التغييرات
```

### 4. إعادة تشغيل Odoo:
```bash
pkill -f odoo-bin
cd ~/Lugal-ai
python3 odoo-bin -c odoo.conf -d lugal --http-port=8069
```

### 5. إذا استمرت المشكلة، قم بتحديث المودول:
- اذهب إلى Apps
- ابحث عن "SAP Integration"
- اضغط على "Upgrade"

## ملاحظات:
- تأكد من أن جميع الملفات تم تحديثها
- تأكد من أن `sap_menu_structure.xml` يتم تحميله قبل الـ wizards في `__manifest__.py`
- تأكد من أن جميع المراجع تستخدم `menu_sap_tools` بدون prefix `sap_integration.`

