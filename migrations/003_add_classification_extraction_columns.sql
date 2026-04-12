-- Migration: 003_add_classification_extraction_columns
-- Description: Add classification and extended extraction columns to documents and extraction_results tables
-- Author: auto-claude
-- Date: 2026-04-12

-- Add classification columns to documents table
ALTER TABLE documents ADD COLUMN IF NOT EXISTS categorie VARCHAR(100);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS confidence DECIMAL(3, 2) CHECK (confidence >= 0 AND confidence <= 1);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS metoda_clasificare VARCHAR(50) CHECK (
    metoda_clasificare IN ('rule_based', 'vision_ai', 'hybrid', 'manual')
);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS review_status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (
    review_status IN ('pending', 'approved', 'rejected', 'needs_review')
);

-- Add extended extraction columns to extraction_results table
ALTER TABLE extraction_results ADD COLUMN IF NOT EXISTS material TEXT;
ALTER TABLE extraction_results ADD COLUMN IF NOT EXISTS data_expirare DATE;
ALTER TABLE extraction_results ADD COLUMN IF NOT EXISTS companie VARCHAR(255);
ALTER TABLE extraction_results ADD COLUMN IF NOT EXISTS producator VARCHAR(255);
ALTER TABLE extraction_results ADD COLUMN IF NOT EXISTS distribuitor VARCHAR(255);
ALTER TABLE extraction_results ADD COLUMN IF NOT EXISTS adresa_producator TEXT;
ALTER TABLE extraction_results ADD COLUMN IF NOT EXISTS extraction_model VARCHAR(100);

-- Create indexes for new query patterns
CREATE INDEX IF NOT EXISTS idx_documents_categorie ON documents(categorie);
CREATE INDEX IF NOT EXISTS idx_documents_review_status ON documents(review_status);
CREATE INDEX IF NOT EXISTS idx_documents_metoda_clasificare ON documents(metoda_clasificare);
CREATE INDEX IF NOT EXISTS idx_extraction_results_companie ON extraction_results(companie);
CREATE INDEX IF NOT EXISTS idx_extraction_results_data_expirare ON extraction_results(data_expirare);
CREATE INDEX IF NOT EXISTS idx_extraction_results_extraction_model ON extraction_results(extraction_model);

-- Add comments for documentation
COMMENT ON COLUMN documents.categorie IS 'Document category determined by classification pipeline';
COMMENT ON COLUMN documents.confidence IS 'Classification confidence score (0.0 to 1.0)';
COMMENT ON COLUMN documents.metoda_clasificare IS 'Classification method used: rule_based, vision_ai, hybrid, manual';
COMMENT ON COLUMN documents.review_status IS 'Human review status: pending, approved, rejected, needs_review';
COMMENT ON COLUMN extraction_results.material IS 'Material name or description extracted from document';
COMMENT ON COLUMN extraction_results.data_expirare IS 'Expiration date extracted from document';
COMMENT ON COLUMN extraction_results.companie IS 'Company name extracted from document';
COMMENT ON COLUMN extraction_results.producator IS 'Producer/manufacturer name extracted from document';
COMMENT ON COLUMN extraction_results.distribuitor IS 'Distributor name extracted from document';
COMMENT ON COLUMN extraction_results.adresa_producator IS 'Producer address extracted from document';
COMMENT ON COLUMN extraction_results.extraction_model IS 'AI model used for extraction (e.g., gpt-4-vision, gemini-pro-vision)';
