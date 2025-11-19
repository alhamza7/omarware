# معلومات قاعدة البيانات - سطح المكتب البعيد

## معلومات قاعدة البيانات الجديدة:

```ini
db_host = localhost
db_port = 5432
db_user = odoo_user1
db_password = rooto
dbfilter = ^lugal_nbs.*$
قاعدة البيانات: lugal_nbs
```

## السكريبتات المتاحة:

### 1. تحديث إعدادات odoo.conf
```bash
chmod +x update_remote_config.sh
./update_remote_config.sh
```

### 2. إنشاء قاعدة بيانات lugal_nbs
```bash
chmod +x create_lugal_nbs_database.sh
./create_lugal_nbs_database.sh
```

### 3. إعداد شامل (تحديث + إنشاء + تثبيت)
```bash
chmod +x setup_lugal_nbs.sh
./setup_lugal_nbs.sh
```

### 4. تحديث الوحدات ومسح الكاش
```bash
chmod +x update_and_clear_cache.sh
./update_and_clear_cache.sh
```

## الأوامر اليدوية:

### إنشاء قاعدة البيانات:
```bash
PGPASSWORD=rooto psql -h localhost -U odoo_user1 -d postgres -c "CREATE DATABASE lugal_nbs OWNER odoo_user1;"
```

### تهيئة قاعدة البيانات:
```bash
venv/bin/python odoo-bin -c odoo.conf -d lugal_nbs --init=base --stop-after-init
```

### تثبيت الوحدات:
```bash
venv/bin/python odoo-bin -c odoo.conf -d lugal_nbs -i pos_perfume_custom,sap_integration --stop-after-init
```

### تشغيل Odoo:
```bash
venv/bin/python odoo-bin -c odoo.conf -d lugal_nbs --http-port=8069
```

## ملاحظات:

- قاعدة البيانات الجديدة: `lugal_nbs`
- المستخدم: `odoo_user1`
- كلمة المرور: `rooto`
- جميع السكريبتات تقرأ اسم قاعدة البيانات تلقائياً من `odoo.conf`

