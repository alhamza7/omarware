#!/bin/bash
# Script to install custom font on Linux server for PDF generation

echo "=========================================="
echo "تثبيت خط MCS-Taybah-S_U على السيرفر"
echo "=========================================="

# Font file name
FONT_FILE="MCS-Taybah-S_U-normal..ttf"
FONT_SOURCE="/home/lugalai/Lugal-ai/addons/product_label_designer/static/src/fonts/$FONT_FILE"

echo ""
echo "Step 1: التحقق من وجود الخط في module..."
if [ -f "$FONT_SOURCE" ]; then
    echo "✓ الخط موجود: $FONT_SOURCE"
else
    echo "✗ الخط غير موجود في: $FONT_SOURCE"
    echo "   الرجاء رفع الخط أولاً!"
    exit 1
fi

echo ""
echo "Step 2: إنشاء مجلد الخطوط للمستخدم..."
mkdir -p ~/.fonts
echo "✓ تم إنشاء: ~/.fonts"

echo ""
echo "Step 3: نسخ الخط إلى مجلد الخطوط..."
cp "$FONT_SOURCE" ~/.fonts/
echo "✓ تم نسخ الخط"

echo ""
echo "Step 4: تحديث cache الخطوط..."
fc-cache -f -v
echo "✓ تم تحديث cache"

echo ""
echo "Step 5: التحقق من تثبيت الخط..."
if fc-list | grep -i "MCS.*Taybah" > /dev/null; then
    echo "✓ الخط مثبت بنجاح!"
    echo ""
    echo "الخطوط المثبتة:"
    fc-list | grep -i "MCS.*Taybah"
else
    echo "⚠ الخط قد يكون مثبت لكن لم يُعثر عليه في القائمة"
    echo "   جرب إعادة تشغيل Odoo"
fi

echo ""
echo "Step 6: (اختياري) تثبيت على مستوى النظام..."
read -p "هل تريد تثبيت الخط على مستوى النظام؟ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "تثبيت على مستوى النظام يتطلب sudo..."
    sudo mkdir -p /usr/share/fonts/truetype/mcs-taybah
    sudo cp "$FONT_SOURCE" /usr/share/fonts/truetype/mcs-taybah/
    sudo fc-cache -f -v
    echo "✓ تم التثبيت على مستوى النظام"
fi

echo ""
echo "=========================================="
echo "✅ انتهى التثبيت!"
echo "=========================================="
echo ""
echo "الخطوات التالية:"
echo "1. أعد تشغيل Odoo"
echo "2. جرب طباعة ملصق"
echo "3. يجب أن يظهر الخط الآن في PDF"
echo ""

