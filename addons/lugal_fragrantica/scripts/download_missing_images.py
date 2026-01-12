#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحميل الصور المفقودة من الروابط الخارجية
يستخدم بعد الاستيراد لتحميل الصور التي لم توجد محلياً
"""

print("""
="*70
🌐 تحميل الصور من الروابط الخارجية
="*70

استخدم هذا السكريبت في Odoo Shell:
python odoo-bin shell -c odoo.conf -d nbs_lugalai

ثم الصق الكود التالي:
="*70
""")

CODE = '''
import requests
import base64
import time

# 1. تحميل صور العطور من URLs
print("📦 تحميل صور العطور من الروابط الخارجية...")
perfumes = env['fragrantica.perfume'].search([
    ('image', '=', False),
    ('image_url', '!=', False)
])

total = len(perfumes)
success = 0
print(f"وُجد {total} عطر بدون صورة محلية لكن لديه رابط خارجي\\n")

for i, p in enumerate(perfumes, 1):
    try:
        response = requests.get(p.image_url, timeout=10)
        if response.status_code == 200:
            p.image = base64.b64encode(response.content)
            success += 1
    except Exception as e:
        pass
    
    if i % 50 == 0:
        print(f"  {i}/{total} - نجح: {success}")
        env.cr.commit()
        time.sleep(0.5)  # تأخير بسيط

env.cr.commit()
print(f"✓ تم تحميل {success} صورة عطر\\n")

# 2. تحميل شعارات البراندات
print("🏷️ تحميل شعارات البراندات...")
perfumes_no_logo = env['fragrantica.perfume'].search([
    ('brand_logo', '=', False),
    ('brand_logo_url', '!=', False)
])

total_brands = len(perfumes_no_logo)
success_brands = 0

for i, p in enumerate(perfumes_no_logo, 1):
    try:
        response = requests.get(p.brand_logo_url, timeout=10)
        if response.status_code == 200:
            p.brand_logo = base64.b64encode(response.content)
            success_brands += 1
    except:
        pass
    
    if i % 50 == 0:
        print(f"  {i}/{total_brands} - نجح: {success_brands}")
        env.cr.commit()
        time.sleep(0.5)

env.cr.commit()
print(f"✓ تم تحميل {success_brands} شعار براند\\n")

# 3. تحميل صور النوتات
print("🎵 تحميل صور النوتات...")
notes = env['fragrantica.note'].search([
    ('note_image', '=', False),
    ('note_image_url', '!=', False)
])

total_notes = len(notes)
success_notes = 0

for i, n in enumerate(notes, 1):
    try:
        response = requests.get(n.note_image_url, timeout=10)
        if response.status_code == 200:
            n.note_image = base64.b64encode(response.content)
            success_notes += 1
    except:
        pass
    
    if i % 100 == 0:
        print(f"  {i}/{total_notes} - نجح: {success_notes}")
        env.cr.commit()
        time.sleep(0.5)

env.cr.commit()
print(f"✓ تم تحميل {success_notes} صورة نوتة")

print("\\n" + "="*70)
print("🎉 اكتمل التحميل!")
print("="*70)
print(f"✅ صور العطور: {success}")
print(f"✅ شعارات البراندات: {success_brands}")
print(f"✅ صور النوتات: {success_notes}")
print(f"\\n🌐 تم تحميل كل الصور من الإنترنت!")
'''

print(CODE)
print("\n" + "="*70)
print("📋 انسخ الكود أعلاه والصقه في Odoo shell")
print("="*70)




