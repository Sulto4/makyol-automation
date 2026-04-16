-- Migration: 011_add_owner_to_documents
-- Description: Add owner_user_id to documents for per-user data isolation.
-- Column is nullable to preserve existing pre-auth documents; 014 backfills them.
-- Author: auth-phase1
-- Date: 2026-04-16

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS owner_user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_documents_owner_user_id
    ON documents(owner_user_id, uploaded_at DESC);

COMMENT ON COLUMN documents.owner_user_id IS 'User who uploaded the document. NULL for pre-auth legacy rows (backfilled by 014).';
