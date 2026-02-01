#!/bin/bash

# Lugal NBS ERP - Complete Local Setup Script
# Run this script to install everything automatically

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║      Lugal NBS ERP - التثبيت الكامل للنسخة المحلية         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai"
DB_NAME="lugal_local"
HTTP_PORT="8070"
ADMIN_PASS="admin"

cd "$PROJECT_DIR"

echo "📍 مسار المشروع: $PROJECT_DIR"
echo "📊 قاعدة البيانات: $DB_NAME"
echo "🌐 المنفذ: $HTTP_PORT"
echo ""

# Step 1: Install python3-venv
echo "════════════════════════════════════════════════════════════"
echo "1️⃣  تثبيت python3-venv..."
echo "════════════════════════════════════════════════════════════"
echo ""

if ! dpkg -l | grep -q python3.12-venv; then
    echo "📦 تثبيت python3.12-venv (يحتاج sudo)..."
    sudo apt install -y python3.12-venv python3-pip
    echo -e "${GREEN}✅ تم تثبيت python3-venv${NC}"
else
    echo -e "${GREEN}✅ python3-venv مثبت مسبقاً${NC}"
fi
echo ""

# Step 2: Create PostgreSQL user
echo "════════════════════════════════════════════════════════════"
echo "2️⃣  إعداد PostgreSQL..."
echo "════════════════════════════════════════════════════════════"
echo ""

if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='capo7amzah'" | grep -q 1; then
    echo -e "${GREEN}✅ مستخدم PostgreSQL موجود مسبقاً${NC}"
else
    echo "👤 إنشاء مستخدم PostgreSQL (يحتاج sudo)..."
    sudo -u postgres createuser -s capo7amzah
    echo -e "${GREEN}✅ تم إنشاء مستخدم PostgreSQL${NC}"
fi
echo ""

# Step 3: Create virtual environment
echo "════════════════════════════════════════════════════════════"
echo "3️⃣  إنشاء البيئة الافتراضية..."
echo "════════════════════════════════════════════════════════════"
echo ""

if [ -d "venv" ]; then
    echo "⚠️  البيئة الافتراضية موجودة، سيتم حذفها وإعادة إنشائها..."
    rm -rf venv
fi

python3 -m venv venv
echo -e "${GREEN}✅ تم إنشاء البيئة الافتراضية${NC}"
echo ""

# Step 4: Install Python packages
echo "════════════════════════════════════════════════════════════"
echo "4️⃣  تثبيت مكتبات Python..."
echo "════════════════════════════════════════════════════════════"
echo ""

./venv/bin/pip install --upgrade pip setuptools wheel --quiet
echo "   ✅ تم ترقية pip"

./venv/bin/pip install psycopg2-binary --quiet
echo "   ✅ تم تثبيت psycopg2"

echo "   📦 تثبيت جميع المتطلبات (قد يستغرق بضع دقائق)..."
./venv/bin/pip install -r requirements.txt --quiet
echo -e "${GREEN}✅ تم تثبيت جميع المكتبات${NC}"
echo ""

# Step 5: Create database
echo "════════════════════════════════════════════════════════════"
echo "5️⃣  إنشاء قاعدة البيانات..."
echo "════════════════════════════════════════════════════════════"
echo ""

if psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "⚠️  قاعدة البيانات '$DB_NAME' موجودة مسبقاً"
    read -p "   هل تريد حذفها وإعادة إنشائها? (y/N): " DROP_DB
    if [ "$DROP_DB" = "y" ] || [ "$DROP_DB" = "Y" ]; then
        dropdb $DB_NAME
        createdb $DB_NAME
        echo -e "${GREEN}✅ تم إعادة إنشاء قاعدة البيانات${NC}"
    else
        echo "   ℹ️  سيتم استخدام قاعدة البيانات الموجودة"
    fi
else
    createdb $DB_NAME
    echo -e "${GREEN}✅ تم إنشاء قاعدة البيانات${NC}"
fi
echo ""

# Step 6: Create configuration
echo "════════════════════════════════════════════════════════════"
echo "6️⃣  إنشاء ملف الإعدادات..."
echo "════════════════════════════════════════════════════════════"
echo ""

cat > odoo_local.conf << EOF
[options]
# Basic settings
addons_path = addons,odoo/addons
data_dir = ./filestore_local
db_host = localhost
db_port = 5432
db_user = capo7amzah
db_password = False
dbfilter = .*

# Ports
http_port = $HTTP_PORT
longpolling_port = 8073

# Performance
workers = 2
max_cron_threads = 1
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648

# Logging
logfile = odoo_local.log
log_level = info

# Development
dev_mode = reload,qweb,xml
EOF

echo -e "${GREEN}✅ تم إنشاء odoo_local.conf${NC}"
echo ""

# Step 7: Create filestore directory
mkdir -p filestore_local
echo -e "${GREEN}✅ تم إنشاء مجلد filestore_local${NC}"
echo ""

# Step 8: Initialize Odoo
echo "════════════════════════════════════════════════════════════"
echo "7️⃣  تهيئة Odoo (قد يستغرق عدة دقائق)..."
echo "════════════════════════════════════════════════════════════"
echo ""

echo "   📦 تثبيت الوحدات الأساسية..."
./venv/bin/python odoo-bin -c odoo_local.conf -d $DB_NAME \
    -i base,web --stop-after-init --without-demo=all 2>&1 | grep -E "INFO|ERROR|WARNING" | tail -10
echo -e "${GREEN}   ✅ تم تثبيت base و web${NC}"

echo "   📦 تثبيت وحدات الأعمال..."
./venv/bin/python odoo-bin -c odoo_local.conf -d $DB_NAME \
    -i sale,purchase,stock,account,hr --stop-after-init --without-demo=all 2>&1 | grep -E "INFO|ERROR|WARNING" | tail -10
echo -e "${GREEN}   ✅ تم تثبيت وحدات الأعمال${NC}"

echo "   📦 تثبيت الوحدات المخصصة..."
./venv/bin/python odoo-bin -c odoo_local.conf -d $DB_NAME \
    -i nbs_archive,pos_perfume_custom --stop-after-init 2>&1 | grep -E "INFO|ERROR|WARNING" | tail -10
echo -e "${GREEN}   ✅ تم تثبيت الوحدات المخصصة${NC}"
echo ""

# Step 9: Set admin password
echo "════════════════════════════════════════════════════════════"
echo "8️⃣  إعداد المستخدم الرئيسي..."
echo "════════════════════════════════════════════════════════════"
echo ""

psql $DB_NAME -c "UPDATE res_users SET password = '$ADMIN_PASS' WHERE login = 'admin';" > /dev/null
echo -e "${GREEN}✅ تم تعيين كلمة سر admin${NC}"
echo ""

# Step 10: Set exchange rate
echo "════════════════════════════════════════════════════════════"
echo "9️⃣  إعداد سعر الصرف..."
echo "════════════════════════════════════════════════════════════"
echo ""

if [ -f "update_exchange_rate.py" ]; then
    ./venv/bin/python update_exchange_rate.py 1500 2>&1 | tail -5
    echo -e "${GREEN}✅ تم تعيين سعر الصرف: 1500 IQD${NC}"
else
    echo "   ℹ️  ملف update_exchange_rate.py غير موجود (اختياري)"
fi
echo ""

# Create start script
cat > start_local.sh << 'EOFSTART'
#!/bin/bash
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
echo "════════════════════════════════════════════════════════════"
echo "🚀 Starting Lugal NBS ERP - Local Version"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📊 Database: lugal_local"
echo "🌐 URL: http://localhost:8070"
echo "👤 User: admin"
echo "🔑 Pass: admin"
echo ""
echo "🛑 لإيقاف النظام: اضغط Ctrl+C"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_local --dev=all
EOFSTART

chmod +x start_local.sh

# Final summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   ✅ اكتمل التثبيت!                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}🎉 نسختك المحلية من Lugal NBS ERP جاهزة للاستخدام!${NC}"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "📊 ملخص التثبيت:"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  📁 المسار: $PROJECT_DIR"
echo "  🗄️  قاعدة البيانات: $DB_NAME"
echo "  🌐 المنفذ: http://localhost:$HTTP_PORT"
echo "  👤 المستخدم: admin"
echo "  🔑 كلمة السر: $ADMIN_PASS"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "🚀 لتشغيل النظام:"
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}  ./start_local.sh${NC}"
echo ""
echo "أو:"
echo ""
echo -e "${BLUE}  ./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_local${NC}"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "🌐 ثم افتح المتصفح:"
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}  http://localhost:8070${NC}"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📝 للمزيد من المعلومات:"
echo "   - LOCAL_INSTALLATION_COMPLETE.md"
echo "   - INSTALL_LOCAL_VERSION.md"
echo ""
