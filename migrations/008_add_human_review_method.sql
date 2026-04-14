-- Migration: 008_add_human_review_method
-- Description: Add 'human_review' to metoda_clasificare constraint for manual corrections
-- Date: 2026-04-15

ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_metoda_clasificare_check;

ALTER TABLE documents ADD CONSTRAINT documents_metoda_clasificare_check CHECK (
    metoda_clasificare IN (
        'filename_regex',
        'text_rules',
        'ai',
        'text_override',
        'vision',
        'filename+text_agree',
        'filename_wins',
        'fallback',
        'human_review'
    )
);
