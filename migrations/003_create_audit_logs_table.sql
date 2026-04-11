-- Migration: 003_create_audit_logs_table
-- Description: Create audit_logs table for immutable activity logging and audit trail
-- Author: auto-claude
-- Date: 2026-04-11

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255),
    action_type VARCHAR(100) NOT NULL CHECK (
        action_type IN (
            'document_upload',
            'document_status_change',
            'document_delete',
            'compliance_check_execution',
            'report_generation',
            'user_login',
            'config_change'
        )
    ),
    entity_type VARCHAR(100) NOT NULL CHECK (
        entity_type IN (
            'document',
            'extraction_result',
            'compliance_check',
            'report',
            'user',
            'config'
        )
    ),
    entity_id INTEGER,
    before_value JSONB,
    after_value JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common query patterns
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX idx_audit_logs_entity_type ON audit_logs(entity_type);
CREATE INDEX idx_audit_logs_entity_id ON audit_logs(entity_id);

-- Create composite index for common filtering combinations
CREATE INDEX idx_audit_logs_user_action ON audit_logs(user_id, action_type);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);

-- Create GIN indexes for JSONB columns to enable efficient querying
CREATE INDEX idx_audit_logs_before_value ON audit_logs USING GIN (before_value);
CREATE INDEX idx_audit_logs_after_value ON audit_logs USING GIN (after_value);
CREATE INDEX idx_audit_logs_metadata ON audit_logs USING GIN (metadata);

-- Add comments for documentation
COMMENT ON TABLE audit_logs IS 'Immutable audit trail storing all significant system activities';
COMMENT ON COLUMN audit_logs.id IS 'Primary key';
COMMENT ON COLUMN audit_logs.timestamp IS 'Timestamp when the action occurred';
COMMENT ON COLUMN audit_logs.user_id IS 'User who performed the action (nullable for system-initiated events)';
COMMENT ON COLUMN audit_logs.action_type IS 'Type of action: document_upload, document_status_change, document_delete, compliance_check_execution, report_generation, user_login, config_change';
COMMENT ON COLUMN audit_logs.entity_type IS 'Type of entity affected by the action: document, extraction_result, compliance_check, report, user, config';
COMMENT ON COLUMN audit_logs.entity_id IS 'ID of the affected entity';
COMMENT ON COLUMN audit_logs.before_value IS 'JSONB object containing entity state before the action';
COMMENT ON COLUMN audit_logs.after_value IS 'JSONB object containing entity state after the action';
COMMENT ON COLUMN audit_logs.metadata IS 'JSONB object containing additional context and metadata about the action';
COMMENT ON COLUMN audit_logs.created_at IS 'Record creation timestamp';

-- Create rule to prevent UPDATE operations (immutability constraint)
CREATE RULE audit_logs_no_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;

-- Create rule to prevent DELETE operations (immutability constraint)
CREATE RULE audit_logs_no_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING;
