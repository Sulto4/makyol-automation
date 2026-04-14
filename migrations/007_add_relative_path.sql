-- Migration: 007_add_relative_path
-- Description: Add relative_path column to documents table for preserving folder structure
-- Date: 2026-04-14

ALTER TABLE documents ADD COLUMN IF NOT EXISTS relative_path TEXT;

COMMENT ON COLUMN documents.relative_path IS 'Original relative path from folder upload (e.g., SubFolder/file.pdf). Used to recreate folder structure in archive exports.';
