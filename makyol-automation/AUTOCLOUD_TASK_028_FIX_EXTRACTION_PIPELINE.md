# Task 028: Fix Data Extraction Pipeline — From Zero to 67%+ Fill Rate

## Priority: CRITICAL (P0)
## Estimated effort: 5-6 hours
## Depends on: Task 025 (env fix), Task 026 (logging)

## Problem

The data extraction pipeline produces near-zero results. Fields like `material`, `companie`, `producator`, `distribuitor`, `adresa_producator` are all null for most documents. The original Python script achieved 67% company extraction, 66% material, and 73% address extraction on the same 309 documents.

## Benchmark (Original Script — 309 documents)

| Field | Extracted | Rate |
|-------|-----------|------|
| companie | 208/309 | 67% |
| material | 206/309 | 66% |
| data_expirare | 135/309 | 43% |
| producator | 181/309 | 58% |
| distribuitor | 7/309 | 2% |
| adresa_producator | 228/309 | 73% |

## Root Causes

### 1. AI extraction fails silently (Task 025 partially fixes this)

When `extract_data_with_ai()` fails, it returns `None`. Then `normalize_extraction_result(None, ...)` returns all-null dict. The user sees empty fields with no explanation.

### 2. No extraction retry on failure

The original script had a retry mechanism: if first AI call returns incomplete data, retry with specific feedback about what's missing. Current pipeline has `MAX_RETRIES = 1` in config but `validate_extraction()` doesn't actually retry — it only retries if a `retry_func` is passed, which it never is.

### 3. Text truncation too aggressive

`extract_data_with_ai()` truncates text to 4000 chars for classification and 6000 chars for extraction. Many construction documents have critical information (company name, address, material description) in headers/footers that appear AFTER the first 6000 chars.

### 4. No extraction fallback without AI

When AI is unavailable, there's zero extraction. The original script had regex-based extraction fallbacks for common fields like company name and dates.

## Requirements

### 1. Implement extraction retry with feedback

In `pipeline/__init__.py`, connect the retry mechanism:

```python
# Step 4: Extraction with retry
extraction = extract_document_data(text, category)

# Check if extraction is all-null
all_null = all(v is None for v in extraction.values())
if all_null and len(text.strip()) >= 50:
    logger.warning("First extraction returned all null for %s, retrying...", filename)
    # Retry with more explicit prompt
    extraction = extract_document_data_with_retry(text, category, attempt=2)
```

### 2. Add regex-based extraction fallback (no AI needed)

Create `pipeline/regex_extraction.py`:

```python
"""Regex-based extraction fallback when AI is unavailable."""

import re
from typing import Optional

def extract_company_regex(text: str) -> Optional[str]:
    """Extract company name using regex patterns."""
    patterns = [
        # Romanian company patterns
        r"(?:S\.?C\.?\s+)([A-Z][A-Z\s&.-]+?)(?:\s+S\.?R\.?L\.?)",
        r"(?:S\.?C\.?\s+)([A-Z][A-Z\s&.-]+?)(?:\s+S\.?A\.?)",
        r"(?:societatea\s+)([A-Z][A-Z\s&.-]+?)(?:\s+S\.?R\.?L\.?)",
        r"([A-Z][A-Z\s&.-]{3,40})\s+(?:S\.?R\.?L\.?|S\.?A\.?|S\.?N\.?C\.?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None

def extract_date_regex(text: str) -> Optional[str]:
    """Extract expiration date using regex patterns."""
    # Direct date patterns
    patterns = [
        r"(?:valabil[aă]?\s+(?:pana\s+la|până\s+la)\s+)(\d{1,2}[./]\d{1,2}[./]\d{4})",
        r"(?:expir[aă]\s+(?:la|in|în)\s+)(\d{1,2}[./]\d{1,2}[./]\d{4})",
        r"(?:data\s+expir[aă]rii?\s*:?\s*)(\d{1,2}[./]\d{1,2}[./]\d{4})",
        r"(?:valid\s+until\s+)(\d{1,2}[./]\d{1,2}[./]\d{4})",
        r"(?:valabilitate\s*:?\s*)(\d{1,2}[./]\d{1,2}[./]\d{4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            # Normalize to DD.MM.YYYY
            return date_str.replace("/", ".")
    return None

def extract_address_regex(text: str) -> Optional[str]:
    """Extract address using regex patterns."""
    patterns = [
        r"(?:sediul?\s*(?:social)?\s*:?\s*)((?:Str|str|Strada|B-dul|Bd|Sos|Calea|Piata)[^,\n]{5,100}(?:,\s*(?:nr|et|ap|bl|sc|sector|jud)[^,\n]{1,50}){0,5})",
        r"(?:adresa\s*:?\s*)((?:Str|str|Strada|B-dul|Bd|Sos|Calea|Piata)[^,\n]{5,100}(?:,\s*[^,\n]{1,50}){0,5})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def regex_extract(text: str, category: str) -> dict:
    """Extract basic fields using regex when AI is unavailable."""
    return {
        "companie": extract_company_regex(text),
        "material": None,  # Hard to extract with regex
        "data_expirare": extract_date_regex(text),
        "producator": None,
        "distribuitor": None,
        "adresa_producator": extract_address_regex(text),
    }
```

### 3. Use regex fallback when AI fails

In `pipeline/extraction.py`, `extract_document_data()`:

```python
def extract_document_data(text, category):
    """Full extraction: AI → regex fallback → normalization."""
    raw_result = extract_data_with_ai(text, category)
    
    if raw_result is None:
        # AI failed — use regex fallback
        logger.warning("AI extraction failed, using regex fallback for %s", category)
        raw_result = regex_extract(text, category)
    
    normalized = normalize_extraction_result(raw_result, category, text)
    
    # Merge: fill AI nulls with regex results
    regex_result = regex_extract(text, category)
    for field, value in normalized.items():
        if value is None and regex_result.get(field):
            normalized[field] = regex_result[field]
            logger.info("Filled null field '%s' with regex: %s", field, regex_result[field][:50])
    
    return normalized
```

### 4. Smarter text truncation

Instead of simple `text[:6000]`, extract the most informative parts:

```python
def smart_truncate(text: str, max_chars: int = 6000) -> str:
    """Truncate text keeping header, footer, and middle sections."""
    if len(text) <= max_chars:
        return text
    
    # Keep first 2500 chars (usually has company, title, metadata)
    header = text[:2500]
    # Keep last 1500 chars (often has addresses, signatures, dates)
    footer = text[-1500:]
    # Keep 2000 chars from middle (material descriptions, specifics)
    mid_start = len(text) // 2 - 1000
    middle = text[mid_start:mid_start + 2000]
    
    return f"{header}\n\n[...]\n\n{middle}\n\n[...]\n\n{footer}"
```

### 5. Increase timeout for pipeline client

In `src/services/pipelineClient.ts`:

```typescript
this.defaultTimeoutMs = options?.defaultTimeoutMs || 60_000;  // was 30_000
this.largeFileTimeoutMs = options?.largeFileTimeoutMs || 180_000;  // was 120_000
```

### 6. Add `extraction_model` field tracking

Currently `extraction_model` is always null in the database. Set it in `extraction.py`:

```python
def extract_document_data(text, category):
    # ... after successful AI extraction ...
    normalized["extraction_model"] = AI_MODEL  # e.g., "google/gemini-2.0-flash-001"
    return normalized
```

And in `documentController.ts`:

```typescript
extraction_model: extraction.extraction_model ?? AI_MODEL_NAME ?? null,
```

## Verification

1. Upload 10 test PDFs through frontend
2. Check that at least 6/10 have non-null `companie` field
3. Check that at least 5/10 have non-null `material` field
4. When AI is intentionally disabled (wrong key), regex fallback should still extract company and date
5. Check `extraction_model` column is populated in database
6. Full batch of 309 docs should show extraction rates >= 60% for companie and material

## Files to modify

- `pipeline/regex_extraction.py` — create new file
- `pipeline/extraction.py` — add retry, regex fallback, smart truncation, model tracking
- `pipeline/__init__.py` — integrate retry on all-null extraction
- `src/services/pipelineClient.ts` — increase timeouts
- `src/controllers/documentController.ts` — pass extraction_model to DB
