-- Migration: 004_create_settings_table
-- Description: Create settings table for storing application configuration as key-value pairs
-- Author: auto-claude
-- Date: 2026-04-13

-- Create settings table
CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index for JSONB value queries (GIN index for efficient JSONB operations)
CREATE INDEX idx_settings_value ON settings USING GIN (value);

-- Create trigger to automatically update updated_at on row update
-- Note: update_updated_at_column() function already exists from migration 001
CREATE TRIGGER update_settings_updated_at
    BEFORE UPDATE ON settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE settings IS 'Stores application configuration as key-value pairs with JSONB values for flexibility';
COMMENT ON COLUMN settings.key IS 'Unique setting identifier (primary key)';
COMMENT ON COLUMN settings.value IS 'JSONB value allowing flexible structured data storage';
COMMENT ON COLUMN settings.created_at IS 'Timestamp when the setting was first created';
COMMENT ON COLUMN settings.updated_at IS 'Timestamp when the setting was last updated (auto-updated by trigger)';
