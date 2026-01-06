#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
استيراد سريع لبيانات Fragrantica باستخدام SQL مباشر
⚡ أسرع 10x من ORM!
"""

import sqlite3
import psycopg2
import os
from datetime import datetime

# إعدادات Odoo Database
ODOO_DB_NAME = 'lugal'  # أو 'nbs_lugalai' - عدّلها حسب اسم قاعدة بياناتك
ODOO_DB_USER = 'odoo'
ODOO_DB_PASSWORD = ''  # عادة فارغ للاتصال المحلي
ODOO_DB_HOST = 'localhost'

# مسار قاعدة بيانات SQLite
SQLITE_DB_PATH = '/home/lugalai/Lugal-ai/fregran/perfumes.db'

print("=" * 70)
print("⚡ استيراد سريع لبيانات Fragrantica - باستخدام SQL مباشر")
print("=" * 70)
print()

# الاتصال بقواعد البيانات
print("🔗 الاتصال بقواعد البيانات...")
sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

pg_conn = psycopg2.connect(
    dbname=ODOO_DB_NAME,
    user=ODOO_DB_USER,
    password=ODOO_DB_PASSWORD,
    host=ODOO_DB_HOST
)
pg_cursor = pg_conn.cursor()

print("✓ متصل بنجاح!\n")

# الحصول على إحصائيات
print("📊 إحصائيات البيانات:")
total_perfumes = sqlite_cursor.execute('SELECT COUNT(*) FROM perfumes').fetchone()[0]
total_notes = sqlite_cursor.execute('SELECT COUNT(*) FROM notes').fetchone()[0]
total_accords = sqlite_cursor.execute('SELECT COUNT(*) FROM main_accords').fetchone()[0]

print(f"  - العطور: {total_perfumes:,}")
print(f"  - النوتات: {total_notes:,}")
print(f"  - التوافقات: {total_accords:,}\n")

# ===== استيراد العطور =====
print("=" * 70)
print("📦 استيراد العطور...")
print("=" * 70)

start_time = datetime.now()

# حذف البيانات القديمة (إن وُجدت)
pg_cursor.execute("DELETE FROM fragrantica_perfume CASCADE;")
pg_conn.commit()
print("✓ تم حذف البيانات القديمة\n")

# جلب العطور من SQLite
sqlite_cursor.execute("""
    SELECT id, url, name, brand_name, brand_logo_url, image_url,
           description_title, description_full, arabic_name, year
    FROM perfumes
    ORDER BY id
""")

perfumes_data = []
for row in sqlite_cursor:
    perfumes_data.append((
        row['id'],           # fragrantica_id
        row['url'],
        row['name'] or 'Unknown',
        row['brand_name'],
        row['brand_logo_url'],
        row['image_url'],
        row['description_title'],
        row['description_full'],
        row['arabic_name'],
        row['year'],
        datetime.now(),      # created_at
    ))

# إدراج مجمّع (Bulk Insert)
print(f"💾 إدراج {len(perfumes_data):,} عطر...")
pg_cursor.executemany("""
    INSERT INTO fragrantica_perfume 
    (fragrantica_id, url, name, brand_name, brand_logo_url, image_url,
     description_title, description_full, arabic_name, year, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", perfumes_data)
pg_conn.commit()

elapsed = (datetime.now() - start_time).total_seconds()
print(f"✓ تم استيراد {len(perfumes_data):,} عطر في {elapsed:.1f} ثانية!\n")

# ===== استيراد النوتات =====
print("=" * 70)
print("🎵 استيراد النوتات...")
print("=" * 70)

start_time = datetime.now()

# جلب mapping بين fragrantica_id و id في Odoo
pg_cursor.execute("SELECT id, fragrantica_id FROM fragrantica_perfume")
perfume_mapping = {row[1]: row[0] for row in pg_cursor.fetchall()}

# جلب النوتات من SQLite
sqlite_cursor.execute("""
    SELECT perfume_id, note_type, note_name, note_image_url, 
           note_opacity, note_order
    FROM notes
    ORDER BY perfume_id, note_type, note_order
""")

notes_data = []
for row in sqlite_cursor:
    odoo_perfume_id = perfume_mapping.get(row['perfume_id'])
    if not odoo_perfume_id:
        continue
    
    notes_data.append((
        odoo_perfume_id,
        row['note_type'],
        row['note_name'],
        row['note_image_url'],
        row['note_opacity'] or 0.0,
        row['note_order'] or 0,
    ))

# إدراج مجمّع
print(f"💾 إدراج {len(notes_data):,} نوتة...")
pg_cursor.executemany("""
    INSERT INTO fragrantica_note 
    (perfume_id, note_type, note_name, note_image_url, note_opacity, note_order)
    VALUES (%s, %s, %s, %s, %s, %s)
""", notes_data)
pg_conn.commit()

elapsed = (datetime.now() - start_time).total_seconds()
print(f"✓ تم استيراد {len(notes_data):,} نوتة في {elapsed:.1f} ثانية!\n")

# ===== استيراد التوافقات =====
print("=" * 70)
print("🎨 استيراد التوافقات...")
print("=" * 70)

start_time = datetime.now()

# جلب التوافقات من SQLite
sqlite_cursor.execute("""
    SELECT perfume_id, accord_name, accord_width, accord_color, accord_order
    FROM main_accords
    ORDER BY perfume_id, accord_order
""")

accords_data = []
for row in sqlite_cursor:
    odoo_perfume_id = perfume_mapping.get(row['perfume_id'])
    if not odoo_perfume_id:
        continue
    
    accords_data.append((
        odoo_perfume_id,
        row['accord_name'],
        row['accord_width'] or 0.0,
        row['accord_color'],
        row['accord_order'] or 0,
    ))

# إدراج مجمّع
print(f"💾 إدراج {len(accords_data):,} توافق...")
pg_cursor.executemany("""
    INSERT INTO fragrantica_accord 
    (perfume_id, accord_name, accord_width, accord_color, accord_order)
    VALUES (%s, %s, %s, %s, %s)
""", accords_data)
pg_conn.commit()

elapsed = (datetime.now() - start_time).total_seconds()
print(f"✓ تم استيراد {len(accords_data):,} توافق في {elapsed:.1f} ثانية!\n")

# إغلاق الاتصالات
sqlite_conn.close()
pg_conn.close()

print("=" * 70)
print("🎉 اكتمل الاستيراد بنجاح!")
print("=" * 70)
print()
print("📝 ملاحظة: لم يتم تحميل الصور بعد.")
print("   لتحميل الصور، استخدم الكود في Odoo → Settings → Technical → Python Code")
print()
print("✨ الآن يمكنك استخدام المودول! افتح أي منتج → تاب Fragrantica")
print("=" * 70)

