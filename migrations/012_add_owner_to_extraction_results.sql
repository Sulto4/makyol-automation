-- Migration: 012_add_owner_to_extraction_results
-- Description: Denormalized owner_user_id on extraction_results for fast per-user filtering
-- without joining the documents table on every query.
-- Author: auth-phase1
-- Date: 2026-04-16

ALTER TABLE extraction_results
    ADD COLUMN IF NOT EXISTS owner_user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_extraction_results_owner_user_id
    ON extraction_results(owner_user_id);

COMMENT ON COLUMN extraction_results.owner_user_id IS 'Denormalized from parent document for fast filtering';
