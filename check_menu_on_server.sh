#!/bin/bash
# سكريبت للتحقق من الملفات على الخادم

echo "=========================================="
echo "التحقق من ملفات menu على الخادم"
echo "=========================================="

cd ~/Lugal-ai || exit 1

echo ""
echo "1. التحقق من menu_sap_integration في sap_dashboard_views.xml:"
grep -n "id=\"menu_sap_integration\"" addons/sap_integration/views/sap_dashboard_views.xml

echo ""
echo "2. التحقق من menu_sap_tools في sap_menu_structure.xml:"
grep -n "id=\"menu_sap_tools\"" addons/sap_integration/views/sap_menu_structure.xml

echo ""
echo "3. التحقق من parent references في wizards:"
grep -n "parent.*menu_sap_tools" addons/sap_integration/wizard/*.xml

echo ""
echo "4. التحقق من ترتيب التحميل في __manifest__.py:"
grep -n "sap_menu_structure\|sap_import_wizard" addons/sap_integration/__manifest__.py

echo ""
echo "5. التحقق من آخر commit:"
git log --oneline -5

echo ""
echo "=========================================="
echo "تم الانتهاء!"
echo "=========================================="

