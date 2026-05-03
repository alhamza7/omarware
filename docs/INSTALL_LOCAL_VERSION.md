# تثبيت النسخة المحلية من Lugal NBS ERP
## Local Installation Guide

---

## 📋 المتطلبات الأساسية

### 1. نظام التشغيل:
```
✓ Linux (Ubuntu 20.04+, Debian, Fedora)
✓ macOS (10.15+)
✓ Windows 10/11 (via WSL2)
```

### 2. البرامج المطلوبة:
```
✓ Python 3.10+ (يفضل 3.11 أو 3.12)
✓ PostgreSQL 13+ (يفضل 14 أو 15)
✓ Git
✓ Node.js 16+ (اختياري للتطوير)
```

---

## 🚀 التثبيت السريع (Linux/macOS)

### 1. تثبيت المتطلبات

#### على Ubuntu/Debian:
```bash
# تحديث النظام
sudo apt update && sudo apt upgrade -y

# تثبيت Python و PostgreSQL
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib libpq-dev \
    git build-essential libxml2-dev libxslt1-dev \
    libldap2-dev libsasl2-dev libjpeg-dev zlib1g-dev \
    libfreetype6-dev liblcms2-dev libwebp-dev \
    libopenjp2-7-dev libtiff5-dev tcl8.6-dev tk8.6-dev

# تثبيت wkhtmltopdf (لتحويل HTML إلى PDF)
sudo apt install -y wkhtmltopdf

# تثبيت Node.js (اختياري)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### على macOS:
```bash
# تثبيت Homebrew (إذا لم يكن مثبتاً)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# تثبيت المتطلبات
brew install python@3.11 postgresql@15 git node

# تشغيل PostgreSQL
brew services start postgresql@15
```

#### على Windows (WSL2):
```bash
# في WSL2 Ubuntu terminal:
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv postgresql git
```

---

### 2. إعداد قاعدة البيانات

```bash
# تشغيل PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# إنشاء مستخدم PostgreSQL
sudo -u postgres createuser -s $USER

# إنشاء قاعدة بيانات للتطوير
createdb lugal_dev

# اختبار الاتصال
psql lugal_dev -c "SELECT version();"
```

---

### 3. استنساخ المشروع

```bash
# إنشاء مجلد المشروع
mkdir -p ~/projects
cd ~/projects

# استنساخ المشروع من GitHub
git clone https://github.com/alhamza7/Lugal-ai.git
cd Lugal-ai

# أو إذا كنت تريد نسخ من السيرفر البعيد:
# scp -r lugalai@192.168.116.211:/home/lugalai/Lugal-ai ~/projects/
```

---

### 4. إعداد البيئة الافتراضية

```bash
cd ~/projects/Lugal-ai

# إنشاء البيئة الافتراضية
python3 -m venv venv

# تفعيل البيئة
source venv/bin/activate  # Linux/macOS
# أو
.\venv\Scripts\activate   # Windows

# ترقية pip
pip install --upgrade pip setuptools wheel
```

---

### 5. تثبيت المتطلبات

```bash
# تثبيت جميع المكتبات المطلوبة
pip install -r requirements.txt

# إذا ظهرت أخطاء، قم بتثبيت المكتبات الأساسية أولاً:
pip install psycopg2-binary
pip install -e .
```

---

### 6. إنشاء ملف الإعدادات

```bash
# نسخ ملف الإعدادات
cp odoo.conf odoo_local.conf

# تعديل الإعدادات
nano odoo_local.conf  # أو vi أو code
```

#### محتوى `odoo_local.conf`:

```ini
[options]
# البيانات الأساسية
addons_path = addons,odoo/addons
data_dir = ./filestore
db_host = localhost
db_port = 5432
db_user = YOUR_USERNAME
db_password = False
dbfilter = .*

# المنافذ
http_port = 8069
longpolling_port = 8072

# الأداء
workers = 2
max_cron_threads = 2
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_request = 8192
limit_time_cpu = 600
limit_time_real = 1200

# السجلات
logfile = odoo_local.log
log_level = info

# التطوير
dev_mode = reload
```

---

### 7. إنشاء قاعدة البيانات

```bash
# الطريقة 1: عبر واجهة الويب
# شغل Odoo وافتح المتصفح
./venv/bin/python odoo-bin -c odoo_local.conf

# ثم اذهب إلى: http://localhost:8069
# اختر "Create Database"
# اسم قاعدة البيانات: lugal_dev
# كلمة السر الرئيسية: admin
# اللغة: English/Arabic
# اختر "Demo data" إذا أردت بيانات تجريبية

# الطريقة 2: عبر سطر الأوامر
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_dev \
    -i base,web,sale,purchase,stock,account,hr \
    --stop-after-init
```

---

### 8. تثبيت الوحدات المخصصة

```bash
# تشغيل Odoo في وضع الترقية
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_dev \
    -u nbs_archive,sap_integration,pos_perfume_custom,lugal_fragrantica \
    --stop-after-init

# أو تثبيت كل الوحدات المخصصة:
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_dev \
    -i nbs_archive,sap_integration,pos_perfume_custom,lugal_fragrantica \
    --stop-after-init
```

---

### 9. تشغيل Odoo

```bash
# وضع التطوير (مع إعادة التحميل التلقائي)
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_dev --dev=all

# وضع الإنتاج
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_dev

# تشغيل في الخلفية
nohup ./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_dev > odoo_local.log 2>&1 &
```

---

### 10. الوصول للنظام

افتح المتصفح واذهب إلى:
```
http://localhost:8069

المستخدم: admin
كلمة السر: admin (أو ما اخترته عند إنشاء قاعدة البيانات)
```

---

## 🔧 إعداد سعر الصرف

```bash
# تشغيل سكريبت تحديث السعر
./venv/bin/python update_exchange_rate.py 1500

# تحديث POS Perfume
./venv/bin/python update_pos_perfume_rate.py
```

---

## 📦 استيراد بيانات من السيرفر

### استيراد قاعدة البيانات:

```bash
# على السيرفر البعيد: نسخ احتياطي
ssh lugalai@192.168.116.211
pg_dump nbs_lugalai > ~/nbs_lugalai_backup.sql
exit

# على جهازك: تنزيل النسخة
scp lugalai@192.168.116.211:~/nbs_lugalai_backup.sql ~/

# استيراد
dropdb lugal_dev  # احذف القاعدة القديمة
createdb lugal_dev
psql lugal_dev < ~/nbs_lugalai_backup.sql
```

### استيراد الملفات (filestore):

```bash
# تنزيل المرفقات
rsync -avz lugalai@192.168.116.211:/var/lib/odoo/filestore/nbs_lugalai/ \
    ~/projects/Lugal-ai/filestore/lugal_dev/
```

---

## 🐛 استكشاف الأخطاء

### الخطأ: "Database connection failed"

```bash
# تحقق من PostgreSQL
sudo systemctl status postgresql

# تحقق من المستخدم
psql -l

# تحقق من الإعدادات
cat odoo_local.conf | grep db_
```

### الخطأ: "Module not found"

```bash
# تحقق من المسارات
grep addons_path odoo_local.conf

# تحقق من وجود الوحدات
ls -la addons/

# أعد تثبيت المتطلبات
pip install -r requirements.txt
```

### الخطأ: "Port 8069 already in use"

```bash
# أوقف العملية القديمة
pkill -f odoo-bin

# أو غير المنفذ
# في odoo_local.conf: http_port = 8070
```

---

## 🔄 التحديث والتطوير

### سحب آخر التحديثات:

```bash
cd ~/projects/Lugal-ai
git pull origin main

# ترقية قاعدة البيانات
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_dev \
    -u all --stop-after-init
```

### تطوير وحدة جديدة:

```bash
# إنشاء وحدة جديدة
mkdir -p addons/my_custom_module
cd addons/my_custom_module

# إنشاء الهيكل
cat > __manifest__.py << 'EOF'
{
    'name': 'My Custom Module',
    'version': '1.0',
    'depends': ['base'],
    'data': [],
    'installable': True,
}
EOF

cat > __init__.py << 'EOF'
from . import models
EOF

mkdir models
touch models/__init__.py
```

---

## 📊 الأوامر المفيدة

### إدارة قاعدة البيانات:

```bash
# قائمة قواعد البيانات
psql -l

# الاتصال بقاعدة بيانات
psql lugal_dev

# حذف قاعدة بيانات
dropdb lugal_dev

# نسخ احتياطي
pg_dump lugal_dev > backup_$(date +%Y%m%d).sql

# استعادة
psql lugal_dev < backup.sql
```

### إدارة Odoo:

```bash
# تشغيل Odoo shell
./venv/bin/python odoo-bin shell -c odoo_local.conf -d lugal_dev

# في الشل:
# >>> env['res.users'].search([])
# >>> env['product.product'].search_count([])

# تحديث وحدة
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_dev \
    -u module_name --stop-after-init

# تثبيت وحدة
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_dev \
    -i module_name --stop-after-init
```

---

## 🎯 نصائح التطوير

### 1. استخدام VS Code:

```bash
# تثبيت ملحقات مفيدة:
code --install-extension ms-python.python
code --install-extension jigar-patel.odoosnippets
code --install-extension ms-python.vscode-pylance
```

### 2. تفعيل وضع التطوير:

```bash
# في odoo_local.conf أضف:
dev_mode = reload,qweb,werkzeug,xml

# أو عند التشغيل:
./venv/bin/python odoo-bin -c odoo_local.conf --dev=all
```

### 3. مراقبة اللوغات:

```bash
# في terminal منفصل
tail -f odoo_local.log

# أو مع تصفية
tail -f odoo_local.log | grep ERROR
```

---

## 🚀 النشر على Docker (اختياري)

### إنشاء Dockerfile:

```dockerfile
FROM python:3.11-slim

# تثبيت المتطلبات
RUN apt-get update && apt-get install -y \
    postgresql-client git build-essential \
    libpq-dev libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# نسخ المشروع
WORKDIR /opt/odoo
COPY . .

# تثبيت المتطلبات Python
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل Odoo
CMD ["python", "odoo-bin", "-c", "odoo.conf"]
```

### docker-compose.yml موجود بالفعل:

```bash
# تشغيل
docker-compose up -d

# الوصول
# http://localhost:8069
```

---

## 📝 ملاحظات مهمة

### الأمان:

```
⚠️  لا تستخدم كلمة سر "admin" في الإنتاج
⚠️  غير db_password في odoo_local.conf
⚠️  لا ترفع ملفات الإعدادات لـ Git
```

### الأداء:

```
💡 استخدم workers > 1 للإنتاج
💡 قلل عدد workers للتطوير
💡 استخدم PostgreSQL 15+ للأداء الأفضل
```

### التطوير:

```
💡 استخدم --dev=all للتطوير
💡 فعّل log_level = debug للتشخيص
💡 استخدم virtual environment دائماً
```

---

## 🎉 النتيجة

بعد اتباع هذه الخطوات، سيكون لديك:

```
✅ نسخة محلية كاملة من Lugal NBS ERP
✅ جميع الوحدات المخصصة مثبتة
✅ بيئة تطوير جاهزة
✅ قاعدة بيانات محلية
✅ إمكانية الاختبار والتطوير
```

---

## 📞 للدعم

إذا واجهت مشاكل:

```bash
# تحقق من اللوغات
tail -50 odoo_local.log

# تحقق من PostgreSQL
sudo systemctl status postgresql

# تحقق من المنفذ
netstat -tuln | grep 8069
```

---

**تم إنشاء الدليل:** 29 يناير 2026  
**النسخة:** 1.0  
**الحالة:** ✅ جاهز للاستخدام
