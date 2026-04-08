-- Add deleted_by (Odoo 19 uses field name as column) and deleted_by_id (legacy) if missing.
-- Run with: psql -d lugal_local -f add_deleted_by_id.sql
-- Or from project root: psql -d lugal_local -f addons/nbs_archive/scripts/add_deleted_by_id.sql

ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS deleted_by_id INTEGER REFERENCES res_users(id);
-- Odoo 19 ORM uses field name "deleted_by" as column name for Many2one
ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES res_users(id);
-- folder_id (Many2one to nbs.document.folder)
ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS folder_id INTEGER REFERENCES nbs_document_folder(id);

-- nbs_document_folder.owner_id NOT NULL: set default so INSERT without owner_id does not fail
ALTER TABLE nbs_document_folder ALTER COLUMN owner_id SET DEFAULT 2;
-- nbs_document_folder.department_id NOT NULL: set default so INSERT without department_id does not fail
ALTER TABLE nbs_document_folder ALTER COLUMN department_id SET DEFAULT 1;
-- nbs_document_folder.name NOT NULL: set default so INSERT without name does not fail
ALTER TABLE nbs_document_folder ALTER COLUMN name SET DEFAULT 'New Folder';
