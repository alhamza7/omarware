#!/bin/bash
# تحميل الصور باستخدام Odoo shell

cd /home/lugalai/Lugal-ai

# تفعيل venv
source venv/bin/activate

# تشغيل Python code عبر Odoo shell
python odoo-bin shell -c odoo.conf -d nbs_lugalai << 'PYTHON_CODE'

print("=" * 70)
print("🖼️ بدء تحميل الصور...")
print("=" * 70)

# تحميل صور العطور
print("\n📦 تحميل صور العطور...")
perfumes = env['fragrantica.perfume'].search([])
total = len(perfumes)
success = 0

for i, perfume in enumerate(perfumes, 1):
    if not perfume.image:
        perfume.load_image_from_static()
        if perfume.image:
            success += 1
    
    if i % 100 == 0:
        print(f"  معالجة: {i}/{total} ({i*100//total}%) - نجح: {success}")
        env.cr.commit()

env.cr.commit()
print(f"\n✓ تم تحميل {success} صورة عطر\n")

# تحميل صور النوتات
print("🎵 تحميل صور النوتات...")
notes = env['fragrantica.note'].search([])
total_notes = len(notes)
success_notes = 0

for i, note in enumerate(notes, 1):
    if not note.note_image:
        note.load_image_from_static()
        if note.note_image:
            success_notes += 1
    
    if i % 500 == 0:
        print(f"  معالجة: {i}/{total_notes} ({i*100//total_notes}%) - نجح: {success_notes}")
        env.cr.commit()

env.cr.commit()
print(f"\n✓ تم تحميل {success_notes} صورة نوتة")

print("\n" + "=" * 70)
print("🎉 اكتمل!")
print("=" * 70)
print(f"✅ صور العطور: {success}")
print(f"✅ صور النوتات: {success_notes}")

PYTHON_CODE










