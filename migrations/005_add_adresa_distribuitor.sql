-- Migration: 005_add_adresa_distribuitor
-- Description: Add adresa_distribuitor column to extraction_results table
-- Author: auto-claude
-- Date: 2026-04-14

ALTER TABLE extraction_results ADD COLUMN IF NOT EXISTS adresa_distribuitor TEXT;
