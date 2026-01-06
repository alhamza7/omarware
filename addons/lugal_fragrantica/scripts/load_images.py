#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحميل سريع للصور من مجلد fregran إلى Odoo
استخدمه بعد fast_import.py
"""

import psycopg2
import os
import base64
from datetime import datetime

# إعدادات
ODOO_DB_NAME = 'lugal'
ODOO_DB_USER = 'odoo'
ODOO_DB_PASSWORD = ''
ODOO_DB_HOST = 'localhost'

# مسارات الصور
FREGRAN_PATH = '/home/lugalai/Lugal-ai/fregran'
PERFUMES_IMAGES = os.path.join(FREGRAN_PATH, 'static', 'images', 'perfumes')
BRANDS_IMAGES = os.path.join(FREGRAN_PATH, 'static', 'images', 'brands')
NOTES_IMAGES = os.path.join(FREGRAN_PATH, 'static', 'images', 'notes')

print("=" * 70)
print("🖼️  تحميل سريع للصور")
print("=" * 70)
print()

# الاتصال بقاعدة البيانات
print("🔗 الاتصال بقاعدة البيانات...")
conn = psycopg2.connect(
    dbname=ODOO_DB_NAME,
    user=ODOO_DB_USER,
    password=ODOO_DB_PASSWORD,
    host=ODOO_DB_HOST
)
cursor = conn.cursor()
print("✓ متصل!\n")

# ===== تحميل صور العطور =====
print("=" * 70)
print("📦 تحميل صور العطور...")
print("=" * 70)

start_time = datetime.now()

# جلب العطور بدون صور
cursor.execute("""
    SELECT id, fragrantica_id, brand_name 
    FROM fragrantica_perfume 
    WHERE image IS NULL
""")

perfumes = cursor.fetchall()
total = len(perfumes)
print(f"وُجد {total:,} عطر بدون صورة\n")

success_count = 0
for i, (perfume_id, fragrantica_id, brand_name) in enumerate(perfumes, 1):
    # صورة العطر
    perfume_image_path = os.path.join(PERFUMES_IMAGES, f"{fragrantica_id}.jpg")
    
    if os.path.exists(perfume_image_path):
        with open(perfume_image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        cursor.execute("""
            UPDATE fragrantica_perfume 
            SET image = %s 
            WHERE id = %s
        """, (image_data, perfume_id))
        success_count += 1
    
    # صورة البراند (إن وُجدت)
    if brand_name:
        brand_filename = brand_name.lower().replace(' ', '-').replace('.', '') + '.jpg'
        brand_image_path = os.path.join(BRANDS_IMAGES, brand_filename)
        
        if os.path.exists(brand_image_path):
            with open(brand_image_path, 'rb') as f:
                brand_data = base64.b64encode(f.read()).decode('utf-8')
            
            cursor.execute("""
                UPDATE fragrantica_perfume 
                SET brand_logo = %s 
                WHERE id = %s
            """, (brand_data, perfume_id))
    
    # حفظ كل 100 عطر
    if i % 100 == 0:
        conn.commit()
        print(f"  💾 حُفظ {i:,}/{total:,} ({i*100//total}%)")

conn.commit()
elapsed = (datetime.now() - start_time).total_seconds()
print(f"\n✓ تم تحميل {success_count:,} صورة عطر في {elapsed:.1f} ثانية!\n")

# ===== تحميل صور النوتات =====
print("=" * 70)
print("🎵 تحميل صور النوتات...")
print("=" * 70)

start_time = datetime.now()

# جلب النوتات بدون صور
cursor.execute("""
    SELECT id, note_name 
    FROM fragrantica_note 
    WHERE note_image IS NULL
""")

notes = cursor.fetchall()
total_notes = len(notes)
print(f"وُجد {total_notes:,} نوتة بدون صورة\n")

# جلب أسماء النوتات الفريدة
unique_notes = {}
for note_id, note_name in notes:
    if note_name not in unique_notes:
        note_filename = note_name.lower().replace(' ', '-').replace('.', '') + '.jpg'
        note_image_path = os.path.join(NOTES_IMAGES, note_filename)
        
        if os.path.exists(note_image_path):
            with open(note_image_path, 'rb') as f:
                unique_notes[note_name] = base64.b64encode(f.read()).decode('utf-8')

print(f"وُجد {len(unique_notes):,} صورة نوتة فريدة")

# تحديث النوتات
success_notes = 0
for i, (note_id, note_name) in enumerate(notes, 1):
    if note_name in unique_notes:
        cursor.execute("""
            UPDATE fragrantica_note 
            SET note_image = %s 
            WHERE id = %s
        """, (unique_notes[note_name], note_id))
        success_notes += 1
    
    if i % 500 == 0:
        conn.commit()
        print(f"  💾 حُفظ {i:,}/{total_notes:,} ({i*100//total_notes}%)")

conn.commit()
elapsed = (datetime.now() - start_time).total_seconds()
print(f"\n✓ تم تحميل {success_notes:,} صورة نوتة في {elapsed:.1f} ثانية!\n")

# الإغلاق
cursor.close()
conn.close()
sqlite_conn.close()

print("=" * 70)
print("🎉 اكتمل تحميل الصور بنجاح!")
print("=" * 70)
print(f"\n✅ صور العطور: {success_count:,}")
print(f"✅ صور النوتات: {success_notes:,}")
print(f"\n🚀 الآن افتح Odoo وجرّب ربط منتج بعطر من Fragrantica!")
print("=" * 70)

