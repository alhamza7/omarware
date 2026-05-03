#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لتجهيز بيانات Fragrantica للتصدير والنقل للسيرفر

هذا السكريبت يقوم بـ:
1. نسخ قاعدة البيانات perfumes.db
2. نسخ الصور (perfumes, brands, notes)
3. إنشاء ملف README للتعليمات
"""

import os
import shutil
import sqlite3
from pathlib import Path

# المسارات
SCRIPT_DIR = Path(__file__).parent
SOURCE_DIR = SCRIPT_DIR.parent / "fregran"
EXPORT_DIR = SCRIPT_DIR

# المجلدات
DB_SOURCE = SOURCE_DIR / "perfumes.db"
IMAGES_SOURCE = SOURCE_DIR / "static" / "images"

DB_DEST = EXPORT_DIR / "perfumes.db"
IMAGES_DEST = EXPORT_DIR / "images"


def get_db_stats(db_path):
    """الحصول على إحصائيات قاعدة البيانات"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    total_perfumes = cursor.execute('SELECT COUNT(*) FROM perfumes').fetchone()[0]
    total_notes = cursor.execute('SELECT COUNT(*) FROM notes').fetchone()[0]
    total_accords = cursor.execute('SELECT COUNT(*) FROM main_accords').fetchone()[0]
    
    conn.close()
    
    return total_perfumes, total_notes, total_accords


def copy_database():
    """نسخ قاعدة البيانات"""
    print("=" * 60)
    print("نسخ قاعدة البيانات...")
    print("=" * 60)
    
    if not DB_SOURCE.exists():
        print(f"❌ خطأ: قاعدة البيانات غير موجودة في: {DB_SOURCE}")
        return False
    
    # نسخ الملف
    shutil.copy2(DB_SOURCE, DB_DEST)
    print(f"✓ تم نسخ قاعدة البيانات إلى: {DB_DEST}")
    
    # عرض الإحصائيات
    total_perfumes, total_notes, total_accords = get_db_stats(DB_DEST)
    print(f"\nإحصائيات قاعدة البيانات:")
    print(f"  - عدد العطور: {total_perfumes:,}")
    print(f"  - عدد النوتات: {total_notes:,}")
    print(f"  - عدد التوافقات: {total_accords:,}")
    
    # حجم الملف
    size_mb = DB_DEST.stat().st_size / (1024 * 1024)
    print(f"  - حجم الملف: {size_mb:.2f} MB")
    
    return True


def copy_images():
    """نسخ الصور"""
    print("\n" + "=" * 60)
    print("نسخ الصور...")
    print("=" * 60)
    
    if not IMAGES_SOURCE.exists():
        print(f"❌ خطأ: مجلد الصور غير موجود في: {IMAGES_SOURCE}")
        return False
    
    # إنشاء مجلد الصور إذا لم يكن موجوداً
    IMAGES_DEST.mkdir(parents=True, exist_ok=True)
    
    # نسخ كل مجلد
    folders = ['perfumes', 'brands', 'notes']
    total_files = 0
    total_size = 0
    
    for folder in folders:
        source_folder = IMAGES_SOURCE / folder
        dest_folder = IMAGES_DEST / folder
        
        if not source_folder.exists():
            print(f"⚠️  تحذير: مجلد {folder} غير موجود، تخطي...")
            continue
        
        print(f"\nنسخ مجلد: {folder}")
        
        # حذف المجلد القديم إن وُجد
        if dest_folder.exists():
            shutil.rmtree(dest_folder)
        
        # نسخ المجلد
        shutil.copytree(source_folder, dest_folder)
        
        # عد الملفات وحساب الحجم
        files = list(dest_folder.glob('*.jpg')) + list(dest_folder.glob('*.png'))
        folder_size = sum(f.stat().st_size for f in files)
        
        print(f"  ✓ تم نسخ {len(files):,} ملف")
        print(f"  ✓ الحجم: {folder_size / (1024 * 1024):.2f} MB")
        
        total_files += len(files)
        total_size += folder_size
    
    print(f"\n{'=' * 60}")
    print(f"إجمالي الصور المنسوخة: {total_files:,} ملف")
    print(f"إجمالي الحجم: {total_size / (1024 * 1024):.2f} MB")
    print(f"{'=' * 60}")
    
    return True


def create_readme():
    """إنشاء ملف README"""
    print("\n" + "=" * 60)
    print("إنشاء ملف README...")
    print("=" * 60)
    
    readme_content = """# Fragrantica Data Export

## 📦 محتويات هذا المجلد

هذا المجلد يحتوي على البيانات اللازمة لمودول Fragrantica في Odoo:

### الملفات:
- `perfumes.db` - قاعدة بيانات SQLite تحتوي على معلومات العطور
- `images/` - مجلد الصور
  - `perfumes/` - صور العطور (37,600+ صورة)
  - `brands/` - شعارات البراندات (4,500+ صورة)
  - `notes/` - صور النوتات العطرية (1,600+ صورة)

---

## 📋 خطوات النقل للسيرفر

### الخطوة 1: رفع المجلد للسيرفر

استخدم SCP أو SFTP أو أي طريقة لنقل الملفات:

```bash
# مثال باستخدام SCP
scp -r fragrantica_data_export/ user@server:/tmp/
```

### الخطوة 2: نقل الملفات للموقع الصحيح

على السيرفر، قم بتنفيذ:

```bash
# الانتقال لمجلد المودول
cd /opt/odoo/addons/lugal_fragrantica/

# إنشاء مجلد البيانات
sudo mkdir -p static/fragrantica_data

# نسخ قاعدة البيانات
sudo cp /tmp/fragrantica_data_export/perfumes.db static/fragrantica_data/

# نسخ الصور
sudo cp -r /tmp/fragrantica_data_export/images static/fragrantica_data/

# تعيين الصلاحيات
sudo chown -R odoo:odoo static/fragrantica_data
sudo chmod -R 755 static/fragrantica_data
```

### الخطوة 3: إعادة تشغيل Odoo

```bash
sudo systemctl restart odoo
```

---

## 🚀 استيراد البيانات في Odoo

بعد تثبيت المودول:

1. اذهب إلى: **Fragrantica → Configuration → Import Data**
2. اترك حقل Database Path فارغاً (سيستخدم المسار الافتراضي)
3. فعّل خيار "Import Images" لاستيراد الصور
4. اضغط "Start Import"
5. انتظر حتى اكتمال الاستيراد (قد يستغرق 10-20 دقيقة)

---

## 📊 معلومات إضافية

### حجم البيانات:
- قاعدة البيانات: ~50 MB
- الصور: ~2-3 GB
- **إجمالي**: ~2.5-3 GB

### عدد السجلات:
- العطور: ~49,000
- النوتات: ~150,000
- التوافقات: ~100,000

### المتطلبات:
- مساحة القرص: 5 GB على الأقل
- RAM: 2 GB على الأقل للاستيراد
- Odoo 14.0 أو أحدث

---

## ⚠️ ملاحظات مهمة

1. **النسخ الاحتياطي**: قم بعمل backup لقاعدة بيانات Odoo قبل الاستيراد
2. **الوقت**: الاستيراد قد يستغرق 10-20 دقيقة حسب سرعة السيرفر
3. **الاستيراد مرة واحدة**: لا تقم بتشغيل الاستيراد أكثر من مرة لنفس البيانات
4. **التحديث**: لتحديث البيانات، استبدل الملفات وأعد تشغيل الاستيراد

---

## 🔧 حل المشاكل

### المشكلة: "Database file not found"
**الحل**: تأكد من نسخ perfumes.db إلى:
```
/opt/odoo/addons/lugal_fragrantica/static/fragrantica_data/perfumes.db
```

### المشكلة: "Permission denied"
**الحل**: تأكد من الصلاحيات:
```bash
sudo chown -R odoo:odoo /opt/odoo/addons/lugal_fragrantica/static/
```

### المشكلة: الاستيراد بطيء جداً
**الحل**: قلل Batch Size إلى 100 في نافذة الاستيراد

---

## 📞 الدعم

للمزيد من المساعدة، راجع الملف:
`addons/lugal_fragrantica/README.md`

"""
    
    readme_path = EXPORT_DIR / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✓ تم إنشاء ملف README في: {readme_path}")


def main():
    """الدالة الرئيسية"""
    print("\n")
    print("=" * 60)
    print("       تجهيز بيانات Fragrantica للتصدير")
    print("=" * 60)
    print()
    
    # التحقق من وجود المصدر
    if not SOURCE_DIR.exists():
        print(f"❌ خطأ: مجلد fregran غير موجود في: {SOURCE_DIR}")
        return
    
    # نسخ قاعدة البيانات
    if not copy_database():
        print("\n❌ فشل نسخ قاعدة البيانات!")
        return
    
    # نسخ الصور
    if not copy_images():
        print("\n❌ فشل نسخ الصور!")
        return
    
    # إنشاء README
    create_readme()
    
    # خلاصة
    print("\n" + "=" * 60)
    print("✅ تم تجهيز البيانات بنجاح!")
    print("=" * 60)
    print(f"\nمجلد التصدير: {EXPORT_DIR}")
    print("\nالملفات الجاهزة للنقل:")
    print("  ✓ perfumes.db")
    print("  ✓ images/perfumes/")
    print("  ✓ images/brands/")
    print("  ✓ images/notes/")
    print("  ✓ README.md")
    print("\nاقرأ ملف README.md للحصول على تعليمات النقل للسيرفر.")
    print("=" * 60)


if __name__ == '__main__':
    main()










