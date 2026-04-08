#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحميل الصور باستخدام Odoo shell
استخدمه بعد الاستيراد الناجح للبيانات
"""

import odoorpc
import os
import base64

# إعدادات الاتصال
ODOO_HOST = 'localhost'
ODOO_PORT = 8069
ODOO_DB = 'nbs_lugalai'  # عدّلها حسب اسم قاعدة بياناتك
ODOO_USER = 'admin'
ODOO_PASSWORD = 'admin'  # كلمة مرور المدير

# مسار الصور
FREGRAN_PATH = '/home/lugalai/Lugal-ai/fregran'

print("=" * 70)
print("🖼️  تحميل الصور عبر Odoo API")
print("=" * 70)

# الاتصال بـ Odoo
print("\n🔗 الاتصال بـ Odoo...")
odoo = odoorpc.ODOO(ODOO_HOST, port=ODOO_PORT)
odoo.login(ODOO_DB, ODOO_USER, ODOO_PASSWORD)
print("✓ متصل بنجاح!\n")

# تحميل صور العطور
print("=" * 70)
print("📦 تحميل صور العطور...")
print("=" * 70)

Perfume = odoo.env['fragrantica.perfume']
perfumes_without_images = Perfume.search([('image', '=', False)])
total = len(perfumes_without_images)

print(f"وُجد {total:,} عطر بدون صورة\n")

success = 0
for i, perfume_id in enumerate(perfumes_without_images, 1):
    perfume = Perfume.browse(perfume_id)
    perfume.load_image_from_static()
    
    if i % 100 == 0:
        print(f"  💾 معالجة {i:,}/{total:,} ({i*100//total}%)")

print(f"\n✓ تمت معالجة {total:,} عطر!")

# تحميل صور النوتات
print("\n" + "=" * 70)
print("🎵 تحميل صور النوتات...")
print("=" * 70)

Note = odoo.env['fragrantica.note']
notes_without_images = Note.search([('note_image', '=', False)])
total_notes = len(notes_without_images)

print(f"وُجد {total_notes:,} نوتة بدون صورة\n")

for i, note_id in enumerate(notes_without_images, 1):
    note = Note.browse(note_id)
    note.load_image_from_static()
    
    if i % 500 == 0:
        print(f"  💾 معالجة {i:,}/{total_notes:,} ({i*100//total_notes}%)")

print(f"\n✓ تمت معالجة {total_notes:,} نوتة!")

print("\n" + "=" * 70)
print("🎉 اكتمل تحميل الصور!")
print("=" * 70)










