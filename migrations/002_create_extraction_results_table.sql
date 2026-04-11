-- Migration: 002_create_extraction_results_table
-- Description: Create extraction_results table for storing PDF text extraction and metadata
-- Author: auto-claude
-- Date: 2026-04-10

-- Create extraction_results table
CREATE TABLE IF NOT EXISTS extraction_results (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    extracted_text TEXT,
    metadata JSONB DEFAULT '{}',
    confidence_score DECIMAL(3, 2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    extraction_status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (
        extraction_status IN ('pending', 'success', 'partial', 'failed')
    ),
    error_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_document_extraction UNIQUE (document_id)
);

-- Create indexes for common query patterns
CREATE INDEX idx_extraction_results_document_id ON extraction_results(document_id);
CREATE INDEX idx_extraction_results_extraction_status ON extraction_results(extraction_status);
CREATE INDEX idx_extraction_results_created_at ON extraction_results(created_at DESC);

-- Create GIN index for JSONB metadata column to enable efficient querying
CREATE INDEX idx_extraction_results_metadata ON extraction_results USING GIN (metadata);

-- Create trigger to automatically update updated_at on row update
CREATE TRIGGER update_extraction_results_updated_at
    BEFORE UPDATE ON extraction_results
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE extraction_results IS 'Stores extracted text and parsed metadata from PDF documents';
COMMENT ON COLUMN extraction_results.id IS 'Primary key';
COMMENT ON COLUMN extraction_results.document_id IS 'Foreign key reference to documents table';
COMMENT ON COLUMN extraction_results.extracted_text IS 'Raw text content extracted from the PDF';
COMMENT ON COLUMN extraction_results.metadata IS 'JSONB object containing parsed metadata: certificate_number, issuing_organization, issue_date, expiry_date, certified_company, certification_scope';
COMMENT ON COLUMN extraction_results.confidence_score IS 'Confidence score for extraction quality (0.0 to 1.0)';
COMMENT ON COLUMN extraction_results.extraction_status IS 'Extraction status: pending, success, partial (some metadata missing), failed';
COMMENT ON COLUMN extraction_results.error_details IS 'JSONB object containing structured error information if extraction failed';
COMMENT ON COLUMN extraction_results.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN extraction_results.updated_at IS 'Record last update timestamp (auto-updated by trigger)';
