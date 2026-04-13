# Task 027: Improve Document Classification Accuracy

## Priority: HIGH (P1)
## Estimated effort: 4-5 hours
## Depends on: Task 025 (env fix), Task 026 (logging)

## Problem

The current 3-level classification cascade (filename regex → text rules → AI) is weaker than the original Python script. The original script achieved 80% classification accuracy with additional hybrid methods. The current pipeline is missing these hybrid methods and has weaker text-based rules.

## Benchmark (Original Script — 309 documents)

| Method | Count | Percentage |
|--------|-------|-----------|
| filename_regex | 220 | 71% |
| text_rules | 39 | 13% |
| ai | 38 | 12% |
| filename+text_agree | 9 | 3% |
| text_override | 3 | 1% |

Classification accuracy: **80% OK** (250/309), 6% REVIEW (18/309)

## Missing Features in Current Pipeline

### 1. Hybrid classification method: `filename+text_agree`

The original script had a validation step: when filename regex gives one category and text rules ALSO give the same category, confidence is boosted to 0.98. This caught 9/309 documents (3%) where neither method alone was confident enough.

**Implementation in `pipeline/classification.py`:**

```python
def classify_document(filename, text):
    # Level 1: Filename regex
    filename_result = classify_by_filename(filename)
    
    # Level 2: Text content rules (always run, even if filename matched)
    text_result = classify_by_text(text)
    
    # Hybrid: both agree → boosted confidence
    if filename_result and text_result:
        if filename_result[0] == text_result[0]:
            logger.info("Classified '%s' by filename+text agreement: %s (0.98)", 
                       filename, filename_result[0])
            return (filename_result[0], 0.98, "filename+text_agree")
        # If they disagree, filename wins but lower confidence
        logger.info("Filename says %s, text says %s for '%s' — using filename", 
                    filename_result[0], text_result[0], filename)
        return (filename_result[0], 0.85, "filename_regex")
    
    if filename_result:
        return filename_result
    
    if text_result:
        return text_result
    
    # Level 3: AI classification
    result = classify_by_ai(text)
    if result:
        return result
    
    return ("ALTELE", 0.3, "fallback")
```

### 2. Text override method: `text_override`

When filename says category X but text content STRONGLY indicates category Y (text score >= 5 vs filename score), the text category wins. This caught 3/309 mislabeled files.

**Add to hybrid logic:**

```python
if filename_result and text_result:
    if filename_result[0] != text_result[0]:
        # Check if text evidence is overwhelming
        text_score = _get_text_score(text, text_result[0])
        if text_score >= 5:
            logger.info("Text override: filename=%s but text strongly says %s (score=%d)", 
                       filename_result[0], text_result[0], text_score)
            return (text_result[0], 0.90, "text_override")
```

### 3. Additional filename regex patterns (from original script analysis)

The original script had patterns that may be missing. Review and add:

```python
# Additional patterns found in original script
(r"(?i)certificat\s*de\s*inregistrare\s*fiscala", "CUI"),
(r"(?i)\bONRC\b", "CUI"),
(r"(?i)registrul\s*comertului", "CUI"),
(r"(?i)buletin\s*de\s*analiza", "CERTIFICAT_CALITATE"),
(r"(?i)raport\s*de\s*incercare", "CERTIFICAT_CALITATE"),
(r"(?i)test\s*report", "CERTIFICAT_CALITATE"),
```

### 4. Improve text markers with additional patterns

Add text markers for patterns commonly found in construction documents:

```python
# Additional text markers
(r"(?i)ASRO", "ISO", 1),  # Romanian standards body
(r"(?i)SR\s*EN\s*\d+", "ISO", 1),  # Romanian standard reference
(r"(?i)IQNet", "ISO", 2),  # IQNet certification network
(r"(?i)CERTIND", "ISO", 2),  # Romanian certification body
(r"(?i)organism.*notificat", "CE", 1),  # Notified body reference
(r"(?i)regulament.*UE", "CE", 1),  # EU regulation reference
(r"(?i)ETA-\d+", "AGREMENT", 2),  # European Technical Assessment
(r"(?i)EOTA", "AGREMENT", 1),  # European Organisation for Technical Assessment
(r"(?i)ministerul.*dezvoltarii", "AGREMENT", 1),  # Ministry of Development
(r"(?i)INCERC", "AGREMENT", 2),  # Romanian building research institute
(r"(?i)punct\s*de\s*lucru", "CUI", 1),  # Work point (company registration)
(r"(?i)capital\s*social", "CUI", 1),  # Share capital
(r"(?i)administrator", "CUI", 1),  # Administrator (company docs)
```

### 5. Category-specific validation boost

After classification, if extracted data STRONGLY matches expected category (e.g., document classified as ISO and text contains "ISO 9001:2015"), boost confidence:

```python
def validate_classification(category, confidence, text):
    """Post-classification validation — boost or flag confidence."""
    validators = {
        "ISO": [r"ISO\s*\d{4,5}", r"management\s*system"],
        "CE": [r"CE\s*mark", r"directive\s*\d+/\d+"],
        "FISA_TEHNICA": [r"caracteristici\s*tehnice", r"proprietati"],
        # ... etc for each category
    }
    patterns = validators.get(category, [])
    matches = sum(1 for p in patterns if re.search(p, text, re.I))
    if matches >= 2:
        return min(confidence + 0.05, 0.99)
    return confidence
```

## Verification

1. Run the same 309 document batch through the updated pipeline
2. Compare classification accuracy: target >= 80% OK (matching original script)
3. Verify hybrid methods (`filename+text_agree`, `text_override`) are triggered
4. Check that no previously-correct classifications are broken (regression test)

## Files to modify

- `pipeline/classification.py` — add hybrid methods, new patterns, validation boost
- `pipeline/__init__.py` — update to use new classify_document signature (if changed)
