-- Migration: 015_add_page_count_to_documents
-- Description: Track PDF page count alongside file_size on documents.
--              Pipeline already computes it via fitz; this surfaces it in the
--              UI, exports, and detail view.
-- Author: page-count-feature
-- Date: 2026-04-18

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS page_count INTEGER;

COMMENT ON COLUMN documents.page_count IS 'Number of pages in the source PDF, computed by pipeline at processing time.';
