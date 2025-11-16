#!/bin/bash
# سكريبت للتحقق من بنية ملفات XML

echo "=========================================="
echo "التحقق من بنية ملفات XML"
echo "=========================================="

cd ~/Lugal-ai || exit 1

echo ""
echo "البحث عن ملفات XML تحتوي على <menuitem> مباشرة بعد <odoo>:"
echo ""

find addons/sap_integration -name "*.xml" -type f | while read file; do
    # التحقق من السطر 3 (بعد <odoo> والسطر الفارغ)
    line3=$(sed -n '3p' "$file")
    line4=$(sed -n '4p' "$file")
    
    # إذا كان السطر 3 فارغاً والسطر 4 يحتوي على <menuitem>
    if [ -z "$line3" ] && echo "$line4" | grep -q "<menuitem"; then
        echo "⚠️  ملف يحتوي على <menuitem> في السطر 4: $file"
        head -8 "$file"
        echo "---"
    # إذا كان السطر 3 يحتوي على <menuitem> مباشرة
    elif echo "$line3" | grep -q "<menuitem"; then
        echo "❌ ملف يحتوي على <menuitem> مباشرة بعد <odoo> (السطر 3): $file"
        head -8 "$file"
        echo "---"
    fi
done

echo ""
echo "=========================================="
echo "التحقق من sap_menu_structure.xml:"
echo "=========================================="
head -8 addons/sap_integration/views/sap_menu_structure.xml

echo ""
echo "=========================================="
echo "التحقق من sap_dashboard_views.xml:"
echo "=========================================="
head -8 addons/sap_integration/views/sap_dashboard_views.xml

echo ""
echo "=========================================="
echo "تم الانتهاء!"
echo "=========================================="

