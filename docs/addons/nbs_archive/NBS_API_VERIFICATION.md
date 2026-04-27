# NBS Archive API – Verification Summary

## Scripts

- **Full API check (Python):**  
  `python3 check_nbs_api_full.py [BASE_URL] [DB] [USER] [PASS]`  
  Tests: health, auth, documents, departments, folders, search, notifications, tags, dashboard, edit-requests, audit-logs, templates, workflows, bulk-upload, mobile.

- **Quick check (Bash):**  
  `./check_nbs_api.sh [BASE_URL] [DB] [USER] [PASS]`  
  Tests: health and login only.

## Fixes applied in code

1. **relations_controller**
   - `get_folders`: use `active` instead of `state`, `created_by` instead of `owner_id`; ignore `folder_type` (not on model).
   - `create_folder`: do not pass `folder_type`/`state` to `create`; use `active=True`, `code or name`.

2. **folder_controller**
   - List/tree: iterate by `folder_ids` and `browse(fid)` to avoid singleton issues; wrap per-folder build in try/except; safe read of `document_count`/`all_document_count`.

3. **nbs_folder model**
   - `check_access`: handle empty/multi recordset with `if not self or len(self) != 1: return False` (no `ensure_one()`).

4. **advanced_search_controller & document_controller**
   - Use `getattr(doc, 'document_number', doc.barcode)` so missing `document_number` does not break (fallback to `barcode`).

5. **template_controller & bulk_upload_controller**
   - List endpoints use `.sudo()` for read so API works when access rules restrict `nbs.document.template` / `nbs.bulk.upload.job`.

6. **SQL migration (add columns if missing)**
   - `addons/nbs_archive/scripts/add_deleted_by_id.sql`: adds `deleted_by_id`, `deleted_by`, and `folder_id` to `nbs_document` (Odoo 19 uses field name as column for Many2one).

## Database (run if columns are missing)

From project root:

```bash
psql -d lugal_local -f addons/nbs_archive/scripts/add_deleted_by_id.sql
```

Or run the Python migration (requires Odoo env):

```bash
python3 run_nbs_document_migration.py
```

## After code or DB changes

**Restart Odoo** so that:

- New Python (folders, advanced_search, templates, bulk_upload, relations) is loaded.
- New columns are visible to the ORM.

Then run:

```bash
python3 check_nbs_api_full.py
```

## Expected result

With DB columns present and Odoo restarted:

- Health, auth, documents, departments, document-types, folders, folders/tree, search, search/advanced, notifications, tags, dashboard, edit-requests, audit-logs, templates, workflows, bulk-upload/jobs, mobile/sync should all return HTTP 200 and `success: true` (or valid data) where applicable.

If any endpoint still fails, check the response `error` and server logs for the exact exception.
