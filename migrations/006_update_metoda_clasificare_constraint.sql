-- Migration: 006_update_metoda_clasificare_constraint
-- Description: Update metoda_clasificare constraint to include all 8 classification methods returned by pipeline
-- Author: auto-claude
-- Date: 2026-04-14

-- Drop the old constraint that only allowed 5 values
ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_metoda_clasificare_check;

-- Add updated constraint with all 8 values the pipeline can return
ALTER TABLE documents ADD CONSTRAINT documents_metoda_clasificare_check CHECK (
    metoda_clasificare IN (
        'filename_regex',
        'text_rules',
        'ai',
        'text_override',
        'vision',
        'filename+text_agree',
        'filename_wins',
        'fallback'
    )
);

-- Update column comment to reflect all 8 methods
COMMENT ON COLUMN documents.metoda_clasificare IS 'Classification method used: filename_regex, text_rules, ai, text_override, vision, filename+text_agree, filename_wins, fallback';
