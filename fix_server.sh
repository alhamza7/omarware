#!/bin/bash
# سكريبت لإصلاح المشاكل على الخادم

echo "=========================================="
echo "إصلاح مشاكل Odoo على الخادم"
echo "=========================================="

# الانتقال إلى مجلد المشروع
cd ~/Lugal-ai || exit 1

echo ""
echo "1. سحب التحديثات من GitHub..."
git pull origin main

echo ""
echo "2. التحقق من virtual environment..."
if [ -d "venv" ]; then
    echo "✅ تم العثور على virtual environment"
    PIP_CMD="venv/bin/pip"
    PYTHON_CMD="venv/bin/python"
elif [ -d ".venv" ]; then
    echo "✅ تم العثور على virtual environment (.venv)"
    PIP_CMD=".venv/bin/pip"
    PYTHON_CMD=".venv/bin/python"
else
    echo "⚠️  لم يتم العثور على virtual environment"
    echo "   محاولة استخدام pip3 مع --break-system-packages..."
    PIP_CMD="pip3 --break-system-packages"
    PYTHON_CMD="python3"
fi

echo ""
echo "3. تثبيت مكتبة passlib..."
$PIP_CMD install passlib==1.7.4

echo ""
echo "4. تثبيت مكتبة pdfminer.six (اختياري)..."
$PIP_CMD install pdfminer.six

echo ""
echo "5. التحقق من الملف المُصلح..."
if grep -q "<data" addons/sap_integration/views/sap_menu_structure.xml; then
    echo "❌ خطأ: الملف لا يزال يحتوي على <data>"
    echo "يرجى التحقق من أن git pull تم بنجاح"
else
    echo "✅ الملف صحيح - لا يحتوي على <data>"
fi

echo ""
echo "=========================================="
echo "تم الانتهاء!"
echo "=========================================="
echo ""
echo "الخطوات التالية:"
echo "1. إعادة تشغيل Odoo"
echo "2. التحقق من السجل: tail -f ~/Lugal-ai/odoo.log"

