#!/bin/bash

# ============================================
# تحديث مودل SAP Integration
# Update SAP Integration Module
# ============================================

echo "================================"
echo "تحديث مودل SAP Integration"
echo "SAP Integration Module Update"
echo "================================"
echo ""

# المسارات
PROJECT_PATH="/home/lugalai/Lugal-ai"
PYTHON_PATH="$PROJECT_PATH/venv/bin/python3"
ODOO_BIN="$PROJECT_PATH/odoo-bin"
CONFIG_FILE="$PROJECT_PATH/odoo_simple.conf"
DATABASE="lugal"

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# التحقق من وجود الملفات
echo -e "${YELLOW}التحقق من الملفات...${NC}"
if [ ! -f "$PYTHON_PATH" ]; then
    echo -e "${RED}❌ خطأ: Python غير موجود في: $PYTHON_PATH${NC}"
    exit 1
fi
if [ ! -f "$ODOO_BIN" ]; then
    echo -e "${RED}❌ خطأ: odoo-bin غير موجود في: $ODOO_BIN${NC}"
    exit 1
fi
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ خطأ: ملف الإعدادات غير موجود في: $CONFIG_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ جميع الملفات موجودة${NC}"
echo ""

# الانتقال إلى مجلد المشروع
echo -e "${YELLOW}الانتقال إلى مجلد المشروع...${NC}"
cd "$PROJECT_PATH" || exit 1

# تحديث المودل
echo ""
echo -e "${CYAN}================================${NC}"
echo -e "${YELLOW}بدء التحديث...${NC}"
echo -e "${YELLOW}Updating module...${NC}"
echo -e "${CYAN}================================${NC}"
echo ""
echo -e "${YELLOW}⏳ قد يستغرق هذا بضع دقائق...${NC}"
echo ""

# تنفيذ التحديث
"$PYTHON_PATH" "$ODOO_BIN" -c "$CONFIG_FILE" -d "$DATABASE" -u sap_integration --stop-after-init

# التحقق من نجاح التحديث
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}✅ تم التحديث بنجاح!${NC}"
    echo -e "${GREEN}✅ Update completed successfully!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo -e "${CYAN}الخطوات التالية:${NC}"
    echo -e "${NC}1. شغّل Odoo: $PYTHON_PATH $ODOO_BIN -c $CONFIG_FILE -d $DATABASE${NC}"
    echo -e "${NC}2. افتح المتصفح: http://192.168.116.211:8069${NC}"
    echo -e "${NC}3. اذهب إلى: SAP Integration → Management Tools → حذف التكرارات${NC}"
    echo ""
    
    # سؤال المستخدم إذا كان يريد تشغيل Odoo
    read -p "هل تريد تشغيل Odoo الآن؟ (y/n): " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo ""
        echo -e "${GREEN}🚀 تشغيل Odoo...${NC}"
        echo -e "${YELLOW}اضغط Ctrl+C لإيقاف Odoo${NC}"
        echo ""
        "$PYTHON_PATH" "$ODOO_BIN" -c "$CONFIG_FILE" -d "$DATABASE"
    else
        echo -e "${CYAN}يمكنك تشغيل Odoo يدوياً باستخدام:${NC}"
        echo -e "${NC}$PYTHON_PATH $ODOO_BIN -c $CONFIG_FILE -d $DATABASE${NC}"
    fi
else
    echo ""
    echo -e "${RED}================================${NC}"
    echo -e "${RED}❌ فشل التحديث!${NC}"
    echo -e "${RED}❌ Update failed!${NC}"
    echo -e "${RED}================================${NC}"
    echo ""
    echo -e "${YELLOW}راجع الأخطاء أعلاه للمزيد من التفاصيل${NC}"
    echo -e "${YELLOW}Check the errors above for details${NC}"
    exit 1
fi

