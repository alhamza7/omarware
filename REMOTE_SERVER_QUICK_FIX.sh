#!/bin/bash
# -*- coding: utf-8 -*-
# سكريبت سريع لإعداد السيرفر البعيد بعد Pull
# يعمل تلقائياً مع إعدادات السيرفر

echo "=========================================="
echo "إعداد السيرفر البعيد بعد Pull"
echo "=========================================="
echo ""

# تحديد مسار المشروع (محاولة عدة مسارات)
PROJECT_DIR=""
for dir in "/home/lugalai/Lugal-ai" "/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai" "$(dirname "$0")" "$PWD"; do
    if [ -f "$dir/odoo.conf" ] || [ -f "$dir/odoo-bin" ]; then
        PROJECT_DIR="$dir"
        break
    fi
done

if [ -z "$PROJECT_DIR" ]; then
    echo "❌ خطأ: لم يتم العثور على مجلد المشروع"
    exit 1
fi

cd "$PROJECT_DIR" || exit 1

echo "✅ مجلد المشروع: $(pwd)"
echo ""

# قراءة إعدادات قاعدة البيانات
DB_NAME=$(grep "^db_name" odoo.conf 2>/dev/null | sed 's/.*= *\([^ ]*\).*/\1/' | head -1)
if [ -z "$DB_NAME" ]; then
    DB_NAME=$(grep "^dbfilter" odoo.conf 2>/dev/null | sed 's/.*= *\^\([^.*]*\).*/\1/' | head -1)
fi
if [ -z "$DB_NAME" ]; then
    DB_NAME="lugal"
fi

echo "قاعدة البيانات: $DB_NAME"
echo ""

# 1. جعل السكريبتات قابلة للتنفيذ
echo "1. جعل السكريبتات قابلة للتنفيذ..."
chmod +x fix_assets_loading_error.sh 2>/dev/null || true
chmod +x fix_assets_error.py 2>/dev/null || true
chmod +x clear_cache_from_db.py 2>/dev/null || true
echo "   ✅ تم"
echo ""

# 2. التحقق من وجود مشكلة AssetsLoadingError
echo "2. التحقق من وجود مشكلة AssetsLoadingError..."
read -p "هل تواجه مشكلة AssetsLoadingError؟ (y/n): " has_error

if [[ "$has_error" == "y" || "$has_error" == "Y" ]]; then
    echo ""
    echo "تطبيق حل مشكلة AssetsLoadingError..."
    
    if [ -f "fix_assets_loading_error.sh" ]; then
        ./fix_assets_loading_error.sh
    elif [ -f "fix_assets_error.py" ]; then
        python3 fix_assets_error.py || venv/bin/python fix_assets_error.py
    else
        echo "   ⚠️  لم يتم العثور على سكريبتات الحل"
        echo "   جرب: python3 clear_cache_from_db.py"
    fi
else
    echo "   ℹ️  لا توجد مشكلة، تخطي..."
fi

echo ""

# 3. إعادة تشغيل Odoo
echo "3. إعادة تشغيل Odoo..."
read -p "هل تريد إعادة تشغيل Odoo الآن؟ (y/n): " restart_odoo

if [[ "$restart_odoo" == "y" || "$restart_odoo" == "Y" ]]; then
    # إيقاف Odoo
    echo "   إيقاف Odoo..."
    pkill -f "odoo-bin.*$DB_NAME" || pkill -f "odoo-bin" || true
    sleep 3
    echo "   ✅ تم إيقاف Odoo"
    
    # تحديد مسار Python
    if [ -f "venv/bin/python" ]; then
        PYTHON_CMD="venv/bin/python"
    elif [ -f ".venv/bin/python" ]; then
        PYTHON_CMD=".venv/bin/python"
    else
        PYTHON_CMD="python3"
    fi
    
    echo ""
    echo "   إعادة تشغيل Odoo..."
    echo "   استخدم الأمر التالي:"
    echo "   $PYTHON_CMD odoo-bin -c odoo.conf -d $DB_NAME --http-port=8069"
    echo ""
    echo "   أو في الخلفية:"
    echo "   nohup $PYTHON_CMD odoo-bin -c odoo.conf -d $DB_NAME --http-port=8069 > odoo.log 2>&1 &"
    echo ""
    
    read -p "   هل تريد التشغيل في الخلفية الآن؟ (y/n): " run_background
    if [[ "$run_background" == "y" || "$run_background" == "Y" ]]; then
        nohup $PYTHON_CMD odoo-bin -c odoo.conf -d "$DB_NAME" --http-port=8069 > odoo.log 2>&1 &
        echo "   ✅ تم تشغيل Odoo في الخلفية"
        echo "   يمكنك متابعة السجلات: tail -f odoo.log"
    fi
else
    echo "   ℹ️  سيتم تخطي إعادة التشغيل"
fi

echo ""
echo "=========================================="
echo "✅ تم إكمال الإعداد!"
echo "=========================================="
echo ""
echo "الخطوات التالية:"
echo "1. افتح المتصفح ومسح الكاش (Ctrl+Shift+Delete)"
echo "2. أعد تحميل الصفحة (Ctrl+F5)"
echo "3. تحقق من أن Odoo يعمل بشكل صحيح"
echo ""
