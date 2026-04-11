-- Migration: 001_create_documents_table
-- Description: Create documents table for storing uploaded PDF files and their processing status
-- Author: auto-claude
-- Date: 2026-04-10

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL CHECK (file_size > 0),
    mime_type VARCHAR(100) NOT NULL DEFAULT 'application/pdf',
    processing_status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (
        processing_status IN ('pending', 'processing', 'completed', 'failed')
    ),
    error_message TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common query patterns
CREATE INDEX idx_documents_processing_status ON documents(processing_status);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at DESC);
CREATE INDEX idx_documents_filename ON documents(filename);

-- Create trigger function for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at on row update
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE documents IS 'Stores metadata for uploaded PDF documents awaiting or having completed text extraction';
COMMENT ON COLUMN documents.id IS 'Primary key';
COMMENT ON COLUMN documents.filename IS 'Sanitized filename stored on disk';
COMMENT ON COLUMN documents.original_filename IS 'Original filename as uploaded by user';
COMMENT ON COLUMN documents.file_path IS 'Full path to the PDF file on disk';
COMMENT ON COLUMN documents.file_size IS 'File size in bytes';
COMMENT ON COLUMN documents.mime_type IS 'MIME type of the uploaded file (should be application/pdf)';
COMMENT ON COLUMN documents.processing_status IS 'Current processing status: pending, processing, completed, failed';
COMMENT ON COLUMN documents.error_message IS 'Error message if processing failed';
COMMENT ON COLUMN documents.uploaded_at IS 'Timestamp when the document was uploaded';
COMMENT ON COLUMN documents.processing_started_at IS 'Timestamp when processing started';
COMMENT ON COLUMN documents.processing_completed_at IS 'Timestamp when processing completed (success or failure)';
COMMENT ON COLUMN documents.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN documents.updated_at IS 'Record last update timestamp (auto-updated by trigger)';
