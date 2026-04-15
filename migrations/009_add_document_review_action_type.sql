-- Migration: 009_add_document_review_action_type
-- Description: Add 'document_review' to audit_logs action_type constraint
-- Date: 2026-04-15

ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_action_type_check;

ALTER TABLE audit_logs ADD CONSTRAINT audit_logs_action_type_check CHECK (
    action_type IN (
        'document_upload',
        'document_status_change',
        'document_delete',
        'document_review',
        'compliance_check_execution',
        'report_generation',
        'user_login',
        'config_change'
    )
);
