-- Migration: Add missing columns to nbs_document (soft delete, folder role, etc.)
-- Run this if you get: column "is_deleted" of relation "nbs_document" does not exist
-- Usage: psql -U your_user -d your_database -f addons/nbs_archive/data/migrate_nbs_document_columns.sql

-- Soft delete fields
ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS deleted_by_id INTEGER REFERENCES res_users(id);
ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS deletion_reason TEXT;
ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS restore_deadline TIMESTAMP;
ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS state_before_trash VARCHAR;

-- Folder / hierarchy
ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS folder_role VARCHAR;
ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS is_attachment BOOLEAN DEFAULT FALSE;
ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS parent_document_id INTEGER REFERENCES nbs_document(id);

-- Search
ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS indexed_in_search BOOLEAN DEFAULT FALSE;
ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS last_indexed_date TIMESTAMP;

-- Indexes for common filters
CREATE INDEX IF NOT EXISTS idx_nbs_document_is_deleted ON nbs_document(is_deleted);
CREATE INDEX IF NOT EXISTS idx_nbs_document_folder_role ON nbs_document(folder_role);
