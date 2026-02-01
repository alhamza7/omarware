#!/bin/bash

# Quick installation script - installs minimal requirements for immediate use

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        تثبيت سريع - Odoo محلي (بدون LDAP)                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

PROJECT_DIR="/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai"
cd "$PROJECT_DIR"

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}1️⃣  تنظيف البيئة السابقة...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

if [ -d "venv" ]; then
    echo "   حذف البيئة الافتراضية القديمة..."
    rm -rf venv
    echo -e "${GREEN}✅ تم${NC}"
fi
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}2️⃣  إنشاء بيئة افتراضية جديدة...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

python3 -m venv venv
echo -e "${GREEN}✅ تم إنشاء البيئة الافتراضية${NC}"
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}3️⃣  تحديث pip...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

./venv/bin/pip install --upgrade pip
echo -e "${GREEN}✅ تم تحديث pip${NC}"
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}4️⃣  تثبيت المكتبات الأساسية (بدون LDAP)...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

./venv/bin/pip install -r requirements_minimal.txt
echo -e "${GREEN}✅ تم تثبيت جميع المكتبات${NC}"
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}5️⃣  التحقق من PostgreSQL...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

if ! systemctl is-active --quiet postgresql; then
    echo -e "${RED}⚠️  PostgreSQL غير نشط. هل تريد تشغيله؟${NC}"
    read -p "نعم للتشغيل (y/N): " START_PG
    if [ "$START_PG" = "y" ] || [ "$START_PG" = "Y" ]; then
        sudo systemctl start postgresql
        echo -e "${GREEN}✅ تم تشغيل PostgreSQL${NC}"
    else
        echo -e "${YELLOW}⚠️  تحذير: يجب تشغيل PostgreSQL لإكمال الإعداد${NC}"
    fi
else
    echo -e "${GREEN}✅ PostgreSQL يعمل${NC}"
fi
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}6️⃣  إنشاء قاعدة البيانات...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

DB_NAME="lugal_local"
DB_USER="capo7amzah"

# Check if database exists
if psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo -e "${YELLOW}⚠️  قاعدة البيانات $DB_NAME موجودة مسبقاً${NC}"
    read -p "هل تريد حذفها وإعادة إنشائها؟ (y/N): " DROP_DB
    if [ "$DROP_DB" = "y" ] || [ "$DROP_DB" = "Y" ]; then
        dropdb "$DB_NAME" 2>/dev/null || true
        echo -e "${GREEN}✅ تم حذف القاعدة القديمة${NC}"
        createdb "$DB_NAME"
        echo -e "${GREEN}✅ تم إنشاء قاعدة بيانات جديدة${NC}"
    else
        echo -e "${YELLOW}⚠️  سيتم استخدام القاعدة الموجودة${NC}"
    fi
else
    createdb "$DB_NAME"
    echo -e "${GREEN}✅ تم إنشاء قاعدة البيانات: $DB_NAME${NC}"
fi
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}7️⃣  إنشاء ملف التكوين...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

cat > odoo_local.conf << EOF
[options]
addons_path = addons,odoo/addons
admin_passwd = admin
db_host = False
db_port = False
db_user = $DB_USER
db_password = False
db_name = $DB_NAME
http_port = 8070
logfile = odoo_local.log
log_level = info
workers = 0
dev_mode = reload
data_dir = ./filestore_local
EOF

echo -e "${GREEN}✅ تم إنشاء odoo_local.conf${NC}"
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}8️⃣  إنشاء مجلد filestore...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

mkdir -p filestore_local
chmod 755 filestore_local
echo -e "${GREEN}✅ تم إنشاء مجلد filestore${NC}"
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}9️⃣  تهيئة Odoo...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

echo "   سيتم تثبيت الوحدات الأساسية..."
./venv/bin/python odoo-bin -c odoo_local.conf -i base,web,sale,purchase,stock,account,hr,nbs_archive,pos_perfume_custom --stop-after-init
echo -e "${GREEN}✅ تم تهيئة Odoo${NC}"
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}🔟 إعداد كلمة سر المستخدم...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

cat > set_admin_password.py << 'EOFPY'
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import odoo
from odoo.api import Environment
from odoo.modules.registry import Registry

dbname = 'lugal_local'
registry = Registry(dbname)

with registry.cursor() as cr:
    env = Environment(cr, odoo.SUPERUSER_ID, {})
    admin = env['res.users'].search([('login', '=', 'admin')], limit=1)
    if admin:
        admin.write({'password': 'admin'})
        cr.commit()
        print("✅ تم تعيين كلمة السر: admin")
    else:
        print("❌ لم يتم العثور على المستخدم admin")
EOFPY

chmod +x set_admin_password.py
./venv/bin/python set_admin_password.py
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}1️⃣1️⃣  تحديث سعر الصرف...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

if [ -f "update_exchange_rate.py" ]; then
    ./venv/bin/python update_exchange_rate.py 1500
    echo -e "${GREEN}✅ تم تحديث سعر الصرف إلى 1500${NC}"
else
    echo -e "${YELLOW}⚠️  ملف update_exchange_rate.py غير موجود${NC}"
fi
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}1️⃣2️⃣  إنشاء سكريبت التشغيل...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

cat > start_local.sh << 'EOFSTART'
#!/bin/bash
echo "============================================================"
echo "Starting Lugal NBS ERP - Local Version"
echo "============================================================"
echo ""
echo "Database: lugal_local"
echo "Port: http://localhost:8070"
echo "User: admin"
echo "Pass: admin"
echo ""
echo "Starting Odoo..."
echo ""

cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
./venv/bin/python odoo-bin -c odoo_local.conf --dev=all

echo ""
echo "Odoo stopped."
EOFSTART

chmod +x start_local.sh
echo -e "${GREEN}✅ تم إنشاء start_local.sh${NC}"
echo ""

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   ✅ اكتمل التثبيت!                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${GREEN}🎉 Odoo جاهز للعمل!${NC}"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📋 معلومات النظام:${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "   🌐 الرابط: http://localhost:8070"
echo "   👤 المستخدم: admin"
echo "   🔑 كلمة السر: admin"
echo "   💾 قاعدة البيانات: lugal_local"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 لتشغيل النظام:${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "   ./start_local.sh"
echo ""
echo -e "${YELLOW}⚠️  ملاحظة: هذا الإصدار بدون دعم LDAP${NC}"
echo -e "${YELLOW}   لتثبيت كامل مع LDAP، نفذ: bash install_dependencies.sh${NC}"
echo ""
