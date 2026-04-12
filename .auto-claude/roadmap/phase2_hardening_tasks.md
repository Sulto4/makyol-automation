# Phase 2 Hardening Tasks - Makyol Automation System

**Created:** 2026-04-12  
**Status:** Planning  
**Source:** MVP Analysis (mvp_analysis_extracted_from_code.md)

## Executive Summary

This document provides a comprehensive breakdown of Phase 2 hardening tasks for the Makyol automation system. The current MVP is a modular Python-based PDF processing pipeline (1,180 LOC across 7 modules) that uses regex-based extraction with 100% success on test fixtures. Phase 2 focuses on production hardening through 6 key deliverables.

**Current Baseline:**
- 1,180 lines of production code (modular architecture)
- 100% test success on 5 Romanian certificate fixtures
- Regex-based extraction (no AI/LLM integration)
- Real-world performance unknown (no large-scale audit data)

**Phase 2 Goals:**
- Fix critical bugs and edge cases
- Implement company normalization for 20+ suppliers
- Add schema validation with AI retry logic
- Integrate Gemini Vision for scanned PDFs
- Add two-step extraction with AI verification
- Enhance modularization with service layers

---

## Deliverable 1: Bug Fixes (CRITICAL PRIORITY)

**Timeline:** Week 1-2  
**Dependencies:** None (blocking all other work)  
**Priority:** CRITICAL

### 1.1 Date Validation Bug

**Problem:** System extracts dates but doesn't validate they're reasonable. Could extract "99.99.9999" or past dates for future certificates.

**Root Cause:** `metadata_extractor.py` lines 79-88 - Returns "N/A" on failure with no logging or validation.

**Subtasks:**
- [ ] **Task 1.1.1:** Implement date validation function
  - Validate date format is parseable
  - Validate date is not in distant past (> 10 years ago for expiry dates)
  - Validate date is not in distant future (< 20 years for expiry dates)
  - Add unit tests for edge cases
  
- [ ] **Task 1.1.2:** Add date validation to metadata extraction
  - Call validation function after extraction
  - Log warning if date fails validation
  - Return "INVALID_DATE" instead of invalid value
  - Add integration tests

**Verification:**
```bash
# Run metadata extraction tests with invalid date fixtures
python -m pytest tests/test_metadata_extractor.py::test_invalid_date_extraction -v
```

**Files to Modify:**
- `makyol-automation/src/metadata_extractor.py`
- `makyol-automation/tests/test_metadata_extractor.py`

---

### 1.2 Material Extraction Over-Capture Bug

**Problem:** Material pattern captures up to 30 characters, may include noise like newlines or dates: "Tevi PEHD PE100 pentru apa\nData: 2024"

**Root Cause:** `config.py` line 134 - Overly greedy regex pattern.

**Subtasks:**
- [ ] **Task 1.2.1:** Refine material extraction pattern
  - Stop at newline characters
  - Stop at date patterns
  - Trim whitespace and punctuation
  - Test with real-world supplier PDFs
  
- [ ] **Task 1.2.2:** Add material name normalization
  - Create whitelist of known material names
  - Fuzzy match extracted material against whitelist
  - Flag unknown materials for review
  - Add confidence scoring

**Verification:**
```bash
# Test with fixtures containing noisy material names
python -m pytest tests/test_metadata_extractor.py::test_material_extraction_with_noise -v
```

**Files to Modify:**
- `makyol-automation/src/config.py`
- `makyol-automation/src/metadata_extractor.py`
- `makyol-automation/tests/test_metadata_extractor.py`

---

### 1.3 Silent Extraction Failures

**Problem:** Date, producer, and material extraction return "N/A" on failure with no logging or audit trail.

**Root Cause:** `metadata_extractor.py` - Missing error logging throughout extraction functions.

**Subtasks:**
- [ ] **Task 1.3.1:** Add structured logging for all extraction failures
  - Log document name, field name, pattern attempted
  - Log extracted text snippet (first 100 chars)
  - Add log levels: WARNING for soft failures, ERROR for critical
  - Include confidence scores in logs
  
- [ ] **Task 1.3.2:** Create extraction failure registry
  - JSON file logging all failures with timestamps
  - Fields: document_path, field_name, error_reason, text_snippet
  - Append to registry on each failure
  - Add registry analysis tool

**Verification:**
```bash
# Process document with missing fields, verify failure logged
python -m makyol-automation.main --input tests/fixtures/incomplete.pdf
grep "Extraction failure" logs/extraction.log
```

**Files to Modify:**
- `makyol-automation/src/metadata_extractor.py`
- `makyol-automation/src/main.py` (initialize failure registry)

**Files to Create:**
- `makyol-automation/logs/extraction_failures.json` (generated)

---

### 1.4 Document Classification Ambiguity

**Problem:** Files like "Aviz-agrement-tehnic-...-DC-Tevi..." match multiple patterns. AGREMENT_TEHNIC takes priority over DECLARATIE_CONFORMITATE, may misclassify some documents.

**Root Cause:** `document_classifier.py` lines 28-36 - First-match wins, no conflict resolution.

**Subtasks:**
- [ ] **Task 1.4.1:** Implement multi-match detection and resolution
  - Track all matching patterns, not just first
  - If multiple matches, use confidence scoring
  - Filename match (1.0) > Text match (0.7)
  - If tie, use longest pattern match
  - Log all ambiguous classifications
  
- [ ] **Task 1.4.2:** Add classification confidence to output
  - Include confidence score in DocumentInfo
  - Flag documents with confidence < 0.5 for manual review
  - Add confidence to Word output and JSON export

**Verification:**
```bash
# Test with ambiguous filename patterns
python -m pytest tests/test_document_classifier.py::test_ambiguous_classification -v
```

**Files to Modify:**
- `makyol-automation/src/document_classifier.py`
- `makyol-automation/src/models.py` (add confidence field)
- `makyol-automation/tests/test_document_classifier.py`

---

### 1.5 Scanned PDF Detection Without Fallback

**Problem:** System detects scanned PDFs (`is_scanned_pdf()` exists) but has no OCR or Vision API fallback. Scanned PDFs counted but not processed correctly.

**Root Cause:** `pdf_extractor.py` - Detection implemented but no action taken.

**Subtasks:**
- [ ] **Task 1.5.1:** Add scanned PDF handling workflow
  - If scanned PDF detected, flag document
  - Log scanned PDF count
  - Add field to ProcessingResult: is_scanned=True
  - Skip metadata extraction for scanned PDFs (for now)
  
- [ ] **Task 1.5.2:** Add scanned PDF report to output
  - List all scanned PDFs in Word document
  - Separate section: "Documents Requiring Manual Review"
  - Include file paths and folder names
  - Add JSON export of scanned PDF list

**Verification:**
```bash
# Test with scanned PDF fixture
python -m pytest tests/test_pdf_extractor.py::test_scanned_pdf_detection -v
```

**Files to Modify:**
- `makyol-automation/src/pdf_extractor.py`
- `makyol-automation/src/models.py` (add is_scanned field)
- `makyol-automation/src/word_generator.py` (add scanned PDF section)

**Acceptance Criteria:**
- All 5 bugs fixed with unit tests
- Integration tests pass
- Extraction failure registry working
- Scanned PDFs flagged for manual review

---

## Deliverable 2: Company Normalization Knowledge Base (HIGH PRIORITY)

**Timeline:** Week 3-4  
**Dependencies:** Bug fixes completed  
**Priority:** HIGH (affects validation and verification work)

### 2.1 Company Knowledge Base Design

**Goal:** Support 20+ company groups with fuzzy matching for variations like "TERAPLAST" vs "SC TERAPLAST SA" vs "Teraplast S.A."

**Current State:** Only 5 hardcoded companies in `config.py` KNOWN_PRODUCERS.

**Subtasks:**
- [ ] **Task 2.1.1:** Design company normalization JSON schema
  - Structure: `{ "canonical_name": str, "aliases": [str], "role": str, "materials": [str] }`
  - Support multiple roles per company (producer + distributor)
  - Include regex patterns for each alias
  - Version field for schema evolution
  
- [ ] **Task 2.1.2:** Create company_normalization.json file
  - Migrate existing 5 companies from config.py
  - Add 15+ new company groups from real-world data
  - Include common variations for each company
  - Document schema in comments

**Files to Create:**
- `makyol-automation/config/company_normalization.json`
- `makyol-automation/docs/company_kb_schema.md`

**Example Schema:**
```json
{
  "version": "1.0",
  "companies": [
    {
      "canonical_name": "TERAPLAST SA",
      "aliases": [
        "TERAPLAST",
        "SC TERAPLAST SA",
        "Teraplast S.A.",
        "TERAPLAST GROUP"
      ],
      "role": "producer",
      "materials": ["Tevi PEHD PE100 pentru apa"],
      "patterns": [
        "TERAPLAST\\s*(SA|S\\.?A\\.?)?",
        "SC\\s+TERAPLAST"
      ]
    }
  ]
}
```

---

### 2.2 Fuzzy Matching Implementation

**Goal:** Match company name variations with confidence scoring.

**Subtasks:**
- [ ] **Task 2.2.1:** Implement fuzzy matching algorithm
  - Use Levenshtein distance for string similarity
  - Normalize input: lowercase, remove punctuation, trim whitespace
  - Match threshold: 85% similarity
  - Return top 3 matches with confidence scores
  - Exact match = 1.0, fuzzy match = 0.7-0.9, no match = 0.0
  
- [ ] **Task 2.2.2:** Create CompanyNormalizer service
  - Load company_normalization.json at startup
  - Method: `normalize_company(text: str) -> (canonical_name, confidence)`
  - Method: `get_company_role(canonical_name: str) -> str`
  - Method: `get_company_materials(canonical_name: str) -> [str]`
  - Cache normalized results for performance

**Files to Create:**
- `makyol-automation/src/services/company_normalizer.py`
- `makyol-automation/tests/test_company_normalizer.py`

**Dependencies:**
- Add `python-Levenshtein` package to requirements.txt

**Verification:**
```bash
# Test fuzzy matching with variations
python -m pytest tests/test_company_normalizer.py::test_fuzzy_company_matching -v
```

---

### 2.3 Integration with Metadata Extraction

**Goal:** Replace hardcoded company matching with normalization KB.

**Subtasks:**
- [ ] **Task 2.3.1:** Refactor producer extraction
  - Remove KNOWN_PRODUCERS from config.py
  - Use CompanyNormalizer.normalize_company()
  - Store both raw text and canonical name
  - Include confidence score in output
  
- [ ] **Task 2.3.2:** Refactor distributor extraction
  - Use CompanyNormalizer for distributor field
  - Support multiple roles (company can be both producer + distributor)
  - Handle SUPPLIER_ROLES mapping via KB
  - Deprecate hardcoded SUPPLIER_ROLES

**Files to Modify:**
- `makyol-automation/src/metadata_extractor.py`
- `makyol-automation/src/config.py` (remove KNOWN_PRODUCERS, SUPPLIER_ROLES)
- `makyol-automation/src/models.py` (add raw_producer, canonical_producer, producer_confidence)

**Verification:**
```bash
# Test extraction with company variations
python -m pytest tests/test_metadata_extractor.py::test_company_normalization -v
```

---

### 2.4 Company KB Expansion

**Goal:** Expand from 5 to 20+ company groups.

**Subtasks:**
- [ ] **Task 2.4.1:** Research Romanian construction suppliers
  - Identify top 20 producers in Romania
  - Identify top 20 distributors
  - Document common name variations for each
  - Create alias lists
  
- [ ] **Task 2.4.2:** Populate company_normalization.json
  - Add all 20+ company groups
  - Include 3-5 aliases per company
  - Add regex patterns for complex variations
  - Test matching with real-world PDFs

**Files to Modify:**
- `makyol-automation/config/company_normalization.json`

**Acceptance Criteria:**
- Company KB with 20+ groups
- Fuzzy matching with 85%+ accuracy
- Confidence scoring for all matches
- Integration tests pass
- Real-world PDF testing successful

---

## Deliverable 3: Schema Validation + Retry Logic (HIGH PRIORITY)

**Timeline:** Week 5-6  
**Dependencies:** Company normalization KB  
**Priority:** HIGH

### 3.1 Metadata JSON Schema Definition

**Goal:** Define strict JSON schema for all extracted metadata to validate structure and data types.

**Subtasks:**
- [ ] **Task 3.1.1:** Create metadata JSON schema
  - Required fields: document_type, file_path, supplier_folder
  - Optional fields: expiration_date, producer, distributor, material
  - Field types: string, date, float (confidence scores)
  - Enum for document_type (11 valid values)
  - Date format: YYYY-MM-DD or "N/A"
  
- [ ] **Task 3.1.2:** Add schema versioning
  - Schema version field in metadata
  - Support multiple schema versions
  - Migration path for schema updates
  - Backward compatibility testing

**Files to Create:**
- `makyol-automation/schemas/metadata_v1.json`
- `makyol-automation/docs/metadata_schema.md`

**Example Schema:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["document_type", "file_path", "supplier_folder"],
  "properties": {
    "document_type": {
      "type": "string",
      "enum": ["FISA_TEHNICA", "ISO_9001", "ISO_14001", ...]
    },
    "file_path": { "type": "string" },
    "expiration_date": {
      "type": "string",
      "pattern": "^(\\d{4}-\\d{2}-\\d{2}|N/A)$"
    },
    "producer": {
      "type": "object",
      "properties": {
        "raw_text": { "type": "string" },
        "canonical_name": { "type": "string" },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 }
      }
    }
  }
}
```

---

### 3.2 Validation Service Implementation

**Goal:** Validate all extracted metadata against JSON schema before output.

**Subtasks:**
- [ ] **Task 3.2.1:** Create MetadataValidator service
  - Load JSON schema at startup
  - Method: `validate(metadata: dict) -> (is_valid: bool, errors: [str])`
  - Return detailed error messages for each validation failure
  - Support schema version selection
  - Add validation metrics (success rate, failure reasons)
  
- [ ] **Task 3.2.2:** Add validation to extraction pipeline
  - Validate metadata after extraction
  - Log all validation failures
  - Include validation result in ProcessingResult
  - Add validation report to Word output

**Files to Create:**
- `makyol-automation/src/services/metadata_validator.py`
- `makyol-automation/tests/test_metadata_validator.py`

**Dependencies:**
- Add `jsonschema` package to requirements.txt

**Verification:**
```bash
# Test validation with valid and invalid metadata
python -m pytest tests/test_metadata_validator.py -v
```

---

### 3.3 AI Feedback Loop (Future - Requires Gemini Integration)

**Goal:** When validation fails, provide feedback to AI and retry extraction.

**Note:** This subtask depends on Deliverable 4 (Gemini Vision) or separate Gemini API integration. For Phase 2, we implement the framework, actual AI retry comes later.

**Subtasks:**
- [ ] **Task 3.3.1:** Design retry framework
  - Max 3 retry attempts per document
  - Track retry count in ProcessingResult
  - Exponential backoff between retries
  - Different feedback messages per failure type
  
- [ ] **Task 3.3.2:** Create feedback message generator
  - Generate human-readable validation error messages
  - Example: "Expiration date '99.99.9999' is invalid. Please extract date in YYYY-MM-DD format."
  - Provide text snippet for context
  - Include extracted metadata for reference
  
- [ ] **Task 3.3.3:** Implement retry stub (no AI yet)
  - On validation failure, log retry attempt
  - Mark document for manual review
  - Future: Replace stub with actual AI call
  - Test framework with mock AI responses

**Files to Create:**
- `makyol-automation/src/services/retry_service.py`
- `makyol-automation/tests/test_retry_service.py`

**Acceptance Criteria:**
- JSON schema defined for all metadata fields
- Validation service implemented and tested
- Retry framework in place (ready for AI integration)
- Validation report in Word output
- Integration tests pass

---

## Deliverable 4: Gemini Vision API Fallback (MEDIUM PRIORITY)

**Timeline:** Week 7-9  
**Dependencies:** Bug fixes (scanned PDF detection), schema validation  
**Priority:** MEDIUM

### 4.1 Gemini Vision API Integration Setup

**Goal:** Integrate Google Gemini Vision API for processing scanned/image-based PDFs.

**Subtasks:**
- [ ] **Task 4.1.1:** Set up Gemini API credentials
  - Create Google Cloud project
  - Enable Gemini API
  - Generate API key
  - Store API key in environment variables
  - Add credential loading to config.py
  
- [ ] **Task 4.1.2:** Add Gemini SDK to project
  - Add `google-generativeai` to requirements.txt
  - Install and test SDK
  - Create GeminiVisionService wrapper
  - Implement rate limiting and error handling

**Files to Create:**
- `makyol-automation/src/services/gemini_vision_service.py`
- `makyol-automation/.env.example` (with GEMINI_API_KEY placeholder)

**Dependencies:**
- Add `google-generativeai` package to requirements.txt
- Add `python-dotenv` for environment variable loading

---

### 4.2 Vision-Based Text Extraction

**Goal:** Extract text and metadata from scanned PDFs using Gemini Vision.

**Subtasks:**
- [ ] **Task 4.2.1:** Implement PDF to image conversion
  - Convert PDF pages to PNG images
  - Use pdf2image library
  - Handle multi-page PDFs
  - Optimize image size for API limits
  
- [ ] **Task 4.2.2:** Create vision extraction pipeline
  - Method: `extract_from_image(image: bytes) -> str`
  - Send image to Gemini Vision API
  - Request structured text output
  - Handle API errors and retries
  - Add timeout limits (30 seconds per page)
  
- [ ] **Task 4.2.3:** Integrate vision extraction with main pipeline
  - If `is_scanned_pdf == True`, use vision extraction
  - If vision extraction fails, fall back to manual review
  - Store extraction source in metadata (text vs vision)
  - Add confidence scoring for vision extraction

**Files to Create:**
- `makyol-automation/src/services/pdf_to_image.py`
- `makyol-automation/tests/test_gemini_vision_service.py`

**Dependencies:**
- Add `pdf2image` package to requirements.txt
- Add `Pillow` for image processing

**Verification:**
```bash
# Test with scanned PDF fixture
python -m pytest tests/test_gemini_vision_service.py::test_scanned_pdf_extraction -v
```

---

### 4.3 NO_TEXT Document Handling

**Goal:** Detect and process documents with no extractable text.

**Subtasks:**
- [ ] **Task 4.3.1:** Enhance NO_TEXT detection
  - If extracted text < 50 characters, mark as NO_TEXT
  - If text is only whitespace/special chars, mark as NO_TEXT
  - Add heuristic: if is_scanned_pdf == True, likely NO_TEXT
  - Log all NO_TEXT documents
  
- [ ] **Task 4.3.2:** Automatic vision fallback for NO_TEXT
  - If NO_TEXT detected, automatically trigger vision extraction
  - Don't wait for validation failure
  - Log fallback trigger reason
  - Track NO_TEXT count in processing metrics

**Files to Modify:**
- `makyol-automation/src/pdf_extractor.py`
- `makyol-automation/src/main.py` (add vision fallback logic)

---

### 4.4 Vision Extraction Confidence Scoring

**Goal:** Assign confidence scores to vision-based extractions vs text-based.

**Subtasks:**
- [ ] **Task 4.4.1:** Implement confidence scoring algorithm
  - Text-based extraction: 0.9 (high confidence)
  - Vision-based extraction: 0.7 (medium confidence)
  - If vision + validation passes: boost to 0.8
  - If multiple retries needed: reduce to 0.5
  
- [ ] **Task 4.4.2:** Add confidence threshold for acceptance
  - Documents with confidence < 0.5 flagged for manual review
  - Include confidence in Word output
  - Add confidence histogram to processing report

**Files to Modify:**
- `makyol-automation/src/models.py` (add extraction_confidence field)
- `makyol-automation/src/word_generator.py` (show confidence)

**Acceptance Criteria:**
- Gemini Vision API integrated and tested
- Scanned PDFs processed successfully
- NO_TEXT documents handled automatically
- Confidence scoring for all extractions
- E2E tests with scanned PDF fixtures

---

## Deliverable 5: Two-Step Extraction + AI Verification (MEDIUM PRIORITY)

**Timeline:** Week 10-11  
**Dependencies:** Gemini Vision API, schema validation  
**Priority:** MEDIUM

### 5.1 Two-Step Extraction Design

**Goal:** Add AI self-verification pass to boost extraction confidence.

**Current Flow:**
```
PDF → extract text → extract metadata → output
```

**New Flow:**
```
PDF → extract text → extract metadata → AI verification → output
                                              ↓
                                         confidence boost
```

**Subtasks:**
- [ ] **Task 5.1.1:** Design verification prompt
  - Provide AI with original text + extracted metadata
  - Ask: "Does this metadata look correct based on the document text?"
  - Request structured yes/no response with reasons
  - If no, request corrections
  
- [ ] **Task 5.1.2:** Create VerificationService
  - Method: `verify_extraction(text: str, metadata: dict) -> (is_correct: bool, corrections: dict)`
  - Use Gemini Flash API for verification
  - Parse structured verification response
  - Apply corrections if provided

**Files to Create:**
- `makyol-automation/src/services/verification_service.py`
- `makyol-automation/tests/test_verification_service.py`
- `makyol-automation/prompts/verification_prompt.txt`

---

### 5.2 Verification Prompt Engineering

**Goal:** Craft effective verification prompt for AI.

**Subtasks:**
- [ ] **Task 5.2.1:** Create verification prompt template
  - Include document text (first 2000 chars)
  - Include extracted metadata as JSON
  - Specific questions per field type
  - Request confidence score per field
  
- [ ] **Task 5.2.2:** Test and refine prompt
  - Test with 20+ real documents
  - Measure verification accuracy
  - Iterate on prompt wording
  - Handle edge cases (missing fields, ambiguous text)

**Example Verification Prompt:**
```
You are a document metadata verification assistant. I extracted the following metadata from a Romanian construction document. Please verify if the extraction is correct.

DOCUMENT TEXT (excerpt):
{text[:2000]}

EXTRACTED METADATA:
{json.dumps(metadata, indent=2)}

For each field, respond with:
- is_correct: true/false
- confidence: 0.0-1.0
- correction: (if is_correct=false, provide corrected value)
- reason: brief explanation

Respond in JSON format.
```

**Files to Create:**
- `makyol-automation/prompts/verification_prompt_v1.txt`

---

### 5.3 Confidence Boosting Logic

**Goal:** Increase extraction confidence when AI verification passes.

**Subtasks:**
- [ ] **Task 5.3.1:** Implement confidence adjustment
  - If verification passes: boost confidence by 0.1 (max 1.0)
  - If verification fails but provides correction: confidence = 0.6
  - If verification fails with no correction: confidence = 0.3
  - Track verification pass rate
  
- [ ] **Task 5.3.2:** Add verification result to output
  - Field: verification_status (passed/failed/corrected)
  - Field: verification_confidence
  - Include in Word output and JSON export
  - Add verification metrics to processing report

**Files to Modify:**
- `makyol-automation/src/models.py` (add verification fields)
- `makyol-automation/src/main.py` (add verification step)

**Verification:**
```bash
# Test verification with correct and incorrect extractions
python -m pytest tests/test_verification_service.py::test_verification_boost -v
```

---

### 5.4 Integration with Main Pipeline

**Goal:** Add verification as optional step in extraction pipeline.

**Subtasks:**
- [ ] **Task 5.4.1:** Add verification flag to CLI
  - `--verify` flag to enable AI verification
  - Default: disabled (for backward compatibility)
  - Log verification usage
  
- [ ] **Task 5.4.2:** Integrate verification into pipeline
  - After metadata extraction, run verification
  - Apply corrections if provided
  - Re-validate corrected metadata
  - Update confidence scores
  - Track verification metrics (time, cost, success rate)

**Files to Modify:**
- `makyol-automation/src/main.py`
- `makyol-automation/README.md` (document --verify flag)

**Acceptance Criteria:**
- Two-step extraction implemented
- AI verification prompt tested and refined
- Confidence boosting logic working
- Integration tests with real documents
- Verification metrics tracked and reported

---

## Deliverable 6: Modularization Improvements (LOW PRIORITY)

**Timeline:** Week 12-13  
**Dependencies:** All other deliverables  
**Priority:** LOW

**Note:** Current system is already modular (7 files, 1,180 LOC). This deliverable focuses on enhanced service architecture and dependency injection for better testability.

### 6.1 Service Layer Architecture

**Goal:** Introduce service layer to decouple business logic from pipeline orchestration.

**Current Architecture:**
```
main.py → calls functions directly
  ├── pdf_extractor.extract_text_from_pdf()
  ├── document_classifier.classify_document()
  ├── metadata_extractor.extract_metadata()
  └── word_generator.generate_word_document()
```

**Proposed Architecture:**
```
main.py → uses services via dependency injection
  ├── ExtractionService (pdf + vision)
  ├── ClassificationService
  ├── MetadataService (extraction + normalization + validation)
  ├── VerificationService
  └── OutputService (word + json)
```

**Subtasks:**
- [ ] **Task 6.1.1:** Create service interfaces
  - Define abstract base classes for each service
  - Method signatures with type hints
  - Docstrings with expected behavior
  - Error handling contracts
  
- [ ] **Task 6.1.2:** Implement service classes
  - ExtractionService: wraps pdf_extractor + gemini_vision_service
  - ClassificationService: wraps document_classifier
  - MetadataService: wraps metadata_extractor + company_normalizer + metadata_validator
  - VerificationService: wraps verification logic
  - OutputService: wraps word_generator + json export

**Files to Create:**
- `makyol-automation/src/services/__init__.py`
- `makyol-automation/src/services/base_service.py` (abstract base classes)
- `makyol-automation/src/services/extraction_service.py`
- `makyol-automation/src/services/classification_service.py`
- `makyol-automation/src/services/metadata_service.py`
- `makyol-automation/src/services/output_service.py`

---

### 6.2 Dependency Injection Setup

**Goal:** Enable dependency injection for better testing and flexibility.

**Subtasks:**
- [ ] **Task 6.2.1:** Create service container
  - Centralized service registry
  - Lazy initialization of services
  - Singleton pattern for stateless services
  - Factory pattern for stateful services
  
- [ ] **Task 6.2.2:** Refactor main.py to use DI
  - Remove direct function imports
  - Inject services via constructor
  - Support mock services for testing
  - Add service configuration via config file

**Files to Create:**
- `makyol-automation/src/container.py` (service container)
- `makyol-automation/tests/test_container.py`

**Example Usage:**
```python
# Old approach
from pdf_extractor import extract_text_from_pdf
text = extract_text_from_pdf(pdf_path)

# New approach
from container import ServiceContainer
container = ServiceContainer()
extraction_service = container.get(ExtractionService)
text = extraction_service.extract_text(pdf_path)
```

---

### 6.3 Pipeline Orchestration Refactor

**Goal:** Separate pipeline orchestration from service implementation.

**Subtasks:**
- [ ] **Task 6.3.1:** Create Pipeline class
  - Define pipeline stages as methods
  - Each stage calls appropriate service
  - Track stage execution time
  - Handle stage failures gracefully
  
- [ ] **Task 6.3.2:** Implement pipeline configuration
  - YAML config for pipeline stages
  - Enable/disable stages via config
  - Conditional execution (e.g., skip verification if disabled)
  - Support custom pipeline configurations

**Files to Create:**
- `makyol-automation/src/pipeline.py`
- `makyol-automation/config/pipeline_config.yaml`
- `makyol-automation/tests/test_pipeline.py`

**Example Pipeline Config:**
```yaml
pipeline:
  stages:
    - name: extraction
      service: ExtractionService
      enabled: true
    - name: classification
      service: ClassificationService
      enabled: true
    - name: metadata
      service: MetadataService
      enabled: true
    - name: verification
      service: VerificationService
      enabled: false  # Optional
    - name: output
      service: OutputService
      enabled: true
```

---

### 6.4 Enhanced Error Handling

**Goal:** Centralized error handling and recovery strategies.

**Subtasks:**
- [ ] **Task 6.4.1:** Create custom exception hierarchy
  - ExtractionException
  - ClassificationException
  - ValidationException
  - VerificationException
  - OutputException
  
- [ ] **Task 6.4.2:** Add exception handling to pipeline
  - Catch stage-specific exceptions
  - Log errors with full context
  - Continue processing other documents on error
  - Generate error report at end of run

**Files to Create:**
- `makyol-automation/src/exceptions.py`
- `makyol-automation/tests/test_exceptions.py`

---

### 6.5 Testing Improvements

**Goal:** Enhanced test coverage with mocked services.

**Subtasks:**
- [ ] **Task 6.5.1:** Create service mocks
  - MockExtractionService (return predefined text)
  - MockClassificationService (return predefined types)
  - MockMetadataService (return predefined metadata)
  - Easy to use in tests
  
- [ ] **Task 6.5.2:** Add integration tests with mocks
  - Test full pipeline with mocked services
  - Test error scenarios
  - Test pipeline configuration
  - Measure test performance (should be fast with mocks)

**Files to Create:**
- `makyol-automation/tests/mocks/__init__.py`
- `makyol-automation/tests/mocks/mock_services.py`
- `makyol-automation/tests/test_pipeline_integration.py`

**Acceptance Criteria:**
- Service layer architecture implemented
- Dependency injection working
- Pipeline orchestration refactored
- Enhanced error handling in place
- Test coverage > 90% with mocks
- All existing tests still pass

---

## Cross-Cutting Concerns

### Logging & Monitoring

**Subtasks:**
- [ ] Add structured logging throughout all services
- [ ] Create processing metrics dashboard (JSON export)
- [ ] Track success rates, confidence scores, retry counts
- [ ] Add performance metrics (time per document, API call counts)

**Files to Create:**
- `makyol-automation/src/monitoring.py`
- `makyol-automation/logs/metrics.json` (generated)

---

### Configuration Management

**Subtasks:**
- [ ] Move all hardcoded values to config files
- [ ] Support YAML/JSON configuration
- [ ] Add environment variable overrides
- [ ] Add hot reload of configuration (optional)

**Files to Create:**
- `makyol-automation/config/extraction_config.yaml`
- `makyol-automation/config/validation_config.yaml`

---

### Documentation

**Subtasks:**
- [ ] Create PROMPT_CONTEXT.md (AI prompts and extraction rules)
- [ ] Create DOCUMENTATIE_SISTEM.md (architecture documentation)
- [ ] Create API_INTEGRATION.md (Gemini API usage guide)
- [ ] Update README.md with Phase 2 features

**Files to Create:**
- `makyol-automation/docs/PROMPT_CONTEXT.md`
- `makyol-automation/docs/DOCUMENTATIE_SISTEM.md`
- `makyol-automation/docs/API_INTEGRATION.md`

---

## Success Metrics

### Phase 2 Completion Criteria

- [ ] All 5 critical bugs fixed
- [ ] 20+ companies in normalization KB
- [ ] Schema validation with 95%+ success rate
- [ ] Gemini Vision processing scanned PDFs
- [ ] AI verification boosting confidence scores
- [ ] Service layer architecture implemented
- [ ] Test coverage > 85%
- [ ] Documentation complete

### Performance Targets

- **Extraction Accuracy:** 95%+ (up from current unknown)
- **Company Normalization:** 90%+ fuzzy match success
- **Validation Success:** 95%+ on first pass
- **Vision API Success:** 85%+ on scanned PDFs
- **Verification Pass Rate:** 80%+ on first verification

### Quality Targets

- **Test Coverage:** > 85%
- **Code Quality:** Pass all linters (flake8, mypy)
- **Documentation:** 100% of public APIs documented
- **Error Handling:** All exceptions caught and logged

---

## Risk Assessment

### High Risk Items

1. **Gemini API Costs**
   - Vision API calls can be expensive at scale
   - Mitigation: Cache results, optimize image size, set daily limits

2. **Scanned PDF Quality**
   - Low-quality scans may not extract well even with Vision API
   - Mitigation: Confidence scoring, manual review for low confidence

3. **Company KB Completeness**
   - May not cover all real-world company variations
   - Mitigation: Continuous expansion, fallback to fuzzy matching

### Medium Risk Items

1. **Schema Evolution**
   - Schema changes may break existing data
   - Mitigation: Versioning, migration scripts

2. **AI Verification Accuracy**
   - AI may introduce errors in verification step
   - Mitigation: Human-in-the-loop for low confidence

3. **Performance Degradation**
   - Multiple AI calls per document may slow processing
   - Mitigation: Parallel processing, caching, optional verification

---

## Timeline Summary

| Week | Deliverable | Tasks |
|------|-------------|-------|
| 1-2 | Bug Fixes | 5 critical bugs + tests |
| 3-4 | Company Normalization | KB design + fuzzy matching + integration |
| 5-6 | Schema Validation | JSON schema + validation service + retry framework |
| 7-9 | Gemini Vision | API setup + vision extraction + NO_TEXT handling |
| 10-11 | AI Verification | Two-step extraction + prompt engineering + confidence boosting |
| 12-13 | Modularization | Service layer + DI + pipeline refactor |

**Total Duration:** 13 weeks (~3 months)

---

## Next Steps

1. **Review this task breakdown** with stakeholders
2. **Prioritize deliverables** (may adjust order based on business needs)
3. **Create Kanban board** from this breakdown (see kanban_update.md)
4. **Assign tasks** to team members
5. **Set up development environment** (API keys, dependencies)
6. **Start with Deliverable 1** (bug fixes - blocking everything else)

---

## Notes

- This breakdown is based on MVP analysis from actual codebase (1,180 LOC across 7 modules)
- Real-world audit data (309 documents) not available - success rates are estimates
- Timeline assumes 1 developer working full-time
- Adjust timeline if multiple developers or part-time work
- Some subtasks can be parallelized (e.g., bug fixes + KB design)
