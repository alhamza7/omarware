#!/usr/bin/env python3
"""
OCR Backfill Script for NBS Archive
Processes each document in its own transaction so failures don't affect others.
"""
import sys, os
sys.path.insert(0, '/home/lugalai/Lugal-ai')

import odoo
from odoo.tools import config
config.parse_config(['-c', '/home/lugalai/Lugal-ai/odoo_simple.conf'])

import odoo.modules.registry
from odoo import api, SUPERUSER_ID

registry = odoo.modules.registry.Registry('nbs_lugalai')

# ── Step 1: collect all document IDs that need OCR ───────────────────────────
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    docs = env['nbs.document'].search([
        ('ocr_status', 'in', ('pending', 'failed')),
        ('current_version_id', '!=', False),
    ], order='id asc')
    doc_ids = docs.ids
    print(f"[backfill] Found {len(doc_ids)} documents to process", flush=True)

# ── Step 2: OCR each document in its own transaction ─────────────────────────
from odoo.addons.nbs_archive.models.nbs_ocr_service import extract_text_via_vision

ok_count   = 0
fail_count = 0
skip_count = 0
total      = len(doc_ids)

for idx, doc_id in enumerate(doc_ids, 1):
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        try:
            doc = env['nbs.document'].browse(doc_id)
            if not doc.exists():
                skip_count += 1
                continue

            version = doc.current_version_id
            if not version or not version.file_data:
                print(f"  [{idx}/{total}] SKIP doc {doc_id} — no file_data")
                skip_count += 1
                continue

            raw           = version.file_data
            file_data_b64 = raw.decode('ascii') if isinstance(raw, bytes) else raw
            file_name     = version.file_name or ''

            print(f"  [{idx}/{total}] doc {doc_id}: {doc.name[:40]} ({file_name}) ...",
                  end=' ', flush=True)

            text = extract_text_via_vision(env, file_data_b64, file_name)

            version.write({
                'extracted_text': text,
                'ocr_completed':  True,
                'ocr_language':   'ara+eng',
            })
            doc.write({
                'ocr_text':   text,
                'ocr_status': 'completed',
            })
            cr.commit()
            print(f"OK ({len(text)} chars)")
            ok_count += 1

        except Exception as exc:
            cr.rollback()
            print(f"FAIL: {exc}")
            # Mark as failed in a fresh sub-transaction
            try:
                with registry.cursor() as cr2:
                    env2 = api.Environment(cr2, SUPERUSER_ID, {})
                    env2['nbs.document'].browse(doc_id).write({'ocr_status': 'failed'})
                    cr2.commit()
            except Exception:
                pass
            fail_count += 1

print(f"\n[backfill] DONE  ✓ ok:{ok_count}  ✗ failed:{fail_count}  - skipped:{skip_count}")
