-- Migration: 014_backfill_existing_documents
-- Description: Attach pre-auth documents/extractions to the first admin user.
-- Safe to run repeatedly (idempotent via IS NULL check).
-- Author: auth-phase1
-- Date: 2026-04-16
--
-- NOTE: This migration is a no-op until at least one admin user exists.
-- The main migration runner will apply it; it simply skips all rows
-- if there is no admin yet.

DO $$
DECLARE
    admin_user_id UUID;
BEGIN
    SELECT id INTO admin_user_id
    FROM users
    WHERE is_admin = true AND is_active = true
    ORDER BY created_at ASC
    LIMIT 1;

    IF admin_user_id IS NULL THEN
        RAISE NOTICE '[014] No admin user found yet; skipping backfill (will be re-run on next startup)';
        RETURN;
    END IF;

    UPDATE documents
    SET owner_user_id = admin_user_id
    WHERE owner_user_id IS NULL;

    UPDATE extraction_results er
    SET owner_user_id = admin_user_id
    WHERE owner_user_id IS NULL;

    RAISE NOTICE '[014] Backfilled pre-auth documents/extractions to admin %', admin_user_id;
END $$;
