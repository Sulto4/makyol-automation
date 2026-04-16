-- Migration: 013_alter_audit_logs_user_id
-- Description: Convert audit_logs.user_id from VARCHAR(255) to UUID and add FK to users.
-- Safe to re-run: only modifies column if it is still VARCHAR. Existing rows have
-- user_id = NULL (audit logs pre-auth), so conversion loses no data.
-- Author: auth-phase1
-- Date: 2026-04-16

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'audit_logs'
          AND column_name = 'user_id'
          AND data_type = 'character varying'
    ) THEN
        DROP INDEX IF EXISTS idx_audit_logs_user_id;
        DROP INDEX IF EXISTS idx_audit_logs_user_action;

        ALTER TABLE audit_logs
            ALTER COLUMN user_id TYPE UUID USING NULL;

        RAISE NOTICE '[013] audit_logs.user_id converted to UUID';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'audit_logs' AND constraint_name = 'audit_logs_user_id_fkey'
    ) THEN
        ALTER TABLE audit_logs
            ADD CONSTRAINT audit_logs_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
        RAISE NOTICE '[013] audit_logs_user_id_fkey added';
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action ON audit_logs(user_id, action_type);

COMMENT ON COLUMN audit_logs.user_id IS 'FK to users.id — who performed the action. NULL for system events.';
