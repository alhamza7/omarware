#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           🚨 إصلاح فوري - تثبيت بدون LDAP                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

PROJECT_DIR="/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai"
cd "$PROJECT_DIR"

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}إيقاف أي عمليات Odoo...${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
pkill -f "odoo-bin" 2>/dev/null || true
sleep 2
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}1️⃣  حذف البيئة الافتراضية الحالية...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

if [ -d "venv" ]; then
    echo "   جاري الحذف..."
    rm -rf venv
    echo -e "${GREEN}✅ تم الحذف${NC}"
else
    echo -e "${GREEN}✅ لا توجد بيئة قديمة${NC}"
fi
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}2️⃣  إنشاء بيئة افتراضية جديدة...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

python3 -m venv venv
echo -e "${GREEN}✅ تم إنشاء البيئة${NC}"
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}3️⃣  تحديث pip...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

./venv/bin/pip install --upgrade pip --quiet
echo -e "${GREEN}✅ تم تحديث pip${NC}"
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}4️⃣  تثبيت psycopg2-binary...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

./venv/bin/pip install psycopg2-binary==2.9.9
echo -e "${GREEN}✅ تم تثبيت psycopg2-binary${NC}"
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}5️⃣  تثبيت المكتبات الأساسية (بدون LDAP)...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

cat > /tmp/odoo_requirements_minimal.txt << 'EOF'
Babel==2.12.1
chardet==5.1.0
cryptography==42.0.8
decorator==5.1.1
docutils==0.20.1
ebaysdk==2.2.0
freezegun==1.2.2
geoip2==4.7.0
gevent==23.9.1
greenlet==3.0.1
idna==3.6
Jinja2==3.1.2
libsass==0.22.0
lxml==5.1.0
lxml_html_clean==0.1.1
MarkupSafe==2.1.3
num2words==0.5.12
ofxparse==0.21
passlib==1.7.4
Pillow==10.1.0
polib==1.2.0
psutil==5.9.6
pydot==1.4.2
pyparsing==3.1.1
PyPDF2==3.0.1
pyserial==3.5
python-dateutil==2.8.2
python-stdnum==1.19
pytz==2023.3
pyusb==1.2.1
qrcode==7.4.2
reportlab==4.0.7
requests==2.32.5
rjsmin==1.2.1
urllib3==2.6.3
vobject==0.9.6.1
Werkzeug==3.0.1
xlrd==2.0.1
XlsxWriter==3.1.9
xlwt==1.3.0
zeep==4.2.1
opensearch-py==3.1.0
PyJWT==2.10.1
EOF

./venv/bin/pip install -r /tmp/odoo_requirements_minimal.txt
rm /tmp/odoo_requirements_minimal.txt
echo -e "${GREEN}✅ تم تثبيت جميع المكتبات${NC}"
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}6️⃣  التحقق من التثبيت...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

./venv/bin/python -c "import babel; print('✅ babel:', babel.__version__)" || echo "❌ babel فشل"
./venv/bin/python -c "import psycopg2; print('✅ psycopg2:', psycopg2.__version__)" || echo "❌ psycopg2 فشل"
./venv/bin/python -c "import lxml; print('✅ lxml:', lxml.__version__)" || echo "❌ lxml فشل"
./venv/bin/python -c "import werkzeug; print('✅ werkzeug:', werkzeug.__version__)" || echo "❌ werkzeug فشل"
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}7️⃣  إعداد قاعدة البيانات...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

DB_NAME="lugal_local"
DB_USER="capo7amzah"

# Check if PostgreSQL is running
if ! systemctl is-active --quiet postgresql; then
    echo -e "${YELLOW}⚠️  PostgreSQL غير نشط${NC}"
    read -p "هل تريد تشغيله؟ (y/N): " START_PG
    if [ "$START_PG" = "y" ] || [ "$START_PG" = "Y" ]; then
        sudo systemctl start postgresql
        echo -e "${GREEN}✅ تم تشغيل PostgreSQL${NC}"
    fi
fi

# Check if database exists
if psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo -e "${YELLOW}⚠️  قاعدة البيانات موجودة${NC}"
    read -p "حذف وإعادة إنشاء؟ (y/N): " DROP_DB
    if [ "$DROP_DB" = "y" ] || [ "$DROP_DB" = "Y" ]; then
        dropdb "$DB_NAME" 2>/dev/null || true
        createdb "$DB_NAME"
        echo -e "${GREEN}✅ تم إعادة إنشاء القاعدة${NC}"
    else
        echo -e "${YELLOW}⚠️  استخدام القاعدة الموجودة${NC}"
    fi
else
    createdb "$DB_NAME" 2>/dev/null || {
        echo -e "${RED}❌ فشل إنشاء القاعدة${NC}"
        echo -e "${YELLOW}قد تحتاج لإنشاء مستخدم PostgreSQL أولاً:${NC}"
        echo "   sudo -u postgres createuser -s capo7amzah"
        exit 1
    }
    echo -e "${GREEN}✅ تم إنشاء قاعدة البيانات${NC}"
fi
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}8️⃣  إنشاء ملف التكوين...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

cat > odoo_local.conf << EOFCONF
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
EOFCONF

echo -e "${GREEN}✅ تم إنشاء odoo_local.conf${NC}"
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}9️⃣  إنشاء مجلد filestore...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

mkdir -p filestore_local
chmod 755 filestore_local
echo -e "${GREEN}✅ تم${NC}"
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}🔟 تهيئة Odoo (قد يستغرق 3-5 دقائق)...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

./venv/bin/python odoo-bin -c odoo_local.conf -i base,web,sale,purchase,stock,account,hr,nbs_archive,pos_perfume_custom --stop-after-init --log-level=warn
echo -e "${GREEN}✅ تم تهيئة Odoo${NC}"
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}1️⃣1️⃣  إعداد كلمة السر...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

cat > /tmp/set_password.py << 'EOFPY'
import sys
import os
sys.path.insert(0, '/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai')
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
        print("✅ كلمة السر: admin")
    else:
        print("❌ المستخدم admin غير موجود")
EOFPY

./venv/bin/python /tmp/set_password.py
rm /tmp/set_password.py
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}1️⃣2️⃣  تحديث سعر الصرف...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""

if [ -f "update_exchange_rate.py" ]; then
    ./venv/bin/python update_exchange_rate.py 1500 2>/dev/null || echo -e "${YELLOW}⚠️  تخطي تحديث السعر${NC}"
fi
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}1️⃣3️⃣  إنشاء سكريبت التشغيل...${NC}"
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
echo -e "${GREEN}✅ تم${NC}"
echo ""

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   🎉 تم بنجاح!                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${GREEN}✅ جميع المكتبات مثبتة (43 مكتبة)${NC}"
echo -e "${GREEN}✅ قاعدة البيانات جاهزة${NC}"
echo -e "${GREEN}✅ Odoo مهيأ بالكامل${NC}"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 لتشغيل النظام:${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "   ./start_local.sh"
echo ""
echo "   ثم افتح المتصفح: ${GREEN}http://localhost:8070${NC}"
echo ""
echo "   👤 المستخدم: ${GREEN}admin${NC}"
echo "   🔑 كلمة السر: ${GREEN}admin${NC}"
echo ""
