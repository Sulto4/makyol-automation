# Folder Scanner & Document Importer

A Python-based file system scanner that automatically discovers, classifies, and imports supplier documents from existing folder structures into a SQLite database.

## Overview

This tool bridges the gap between manual folder-based document organization and modern database-driven systems. It reads existing supplier document folders, identifies PDF files, maps them to the correct suppliers, attempts to classify document types from filename patterns, and creates searchable database records.

**Key Features:**
- 🔍 Recursive PDF discovery across multiple supplier folders
- 🏷️ Automatic document classification from filename patterns
- 🔗 Supplier-document relationship mapping
- 🛡️ Idempotent imports (no duplicates via SHA256 file hashing)
- 📊 Detailed import summary reports
- ⚡ Memory-efficient streaming for large folder structures

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or extract the project:**
   ```bash
   cd scanner
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation:**
   ```bash
   python -m src.main --help
   ```

## Folder Structure Requirements

The scanner expects documents organized in a specific folder structure:

```
Documente/
├── Documente Zakprest/
│   ├── 2. ISO 9001.pdf
│   ├── 7. AVS.pdf
│   └── random_document.pdf
├── PEHD Apa - TERAPLAST/
│   ├── 10. Fisa tehnica.pdf
│   └── Certificat ISO 14001 SRAC 2025_2026.pdf
├── PEHD Apa - VALROM/
│   └── 3. ISO 9001.pdf
└── Teava apa PEHD - Tehnoworld/
    └── Certificat ISO 9001.pdf
```

### Supported Suppliers

The scanner is configured to handle the following suppliers (defined in `src/config/settings.py`):

| Supplier Name | Folder Name                    |
|---------------|--------------------------------|
| Zakprest      | Documente Zakprest             |
| TERAPLAST     | PEHD Apa - TERAPLAST           |
| VALROM        | PEHD Apa - VALROM              |
| Tehnoworld    | Teava apa PEHD - Tehnoworld    |

## Usage

### Basic Usage

**Scan the default folder (`Documente/`):**
```bash
python -m src.main
```

**Scan a custom folder location:**
```bash
python -m src.main --base-path /path/to/your/documents
```

### Dry Run Mode

Preview what would be imported without making database changes:
```bash
python -m src.main --dry-run
```

This is useful for:
- Verifying folder structure
- Checking document discovery
- Testing classification patterns

### Verbose Logging

Enable detailed DEBUG-level logging for troubleshooting:
```bash
python -m src.main --verbose
```

### Example Output

```
2026-04-10 18:55:00 - __main__ - INFO - === Document Scanner & Importer ===
2026-04-10 18:55:00 - __main__ - INFO - Base path: Documente
2026-04-10 18:55:00 - __main__ - INFO - Dry run: False
2026-04-10 18:55:00 - __main__ - INFO - Initializing database...
2026-04-10 18:55:00 - src.scanner.folder_scanner - INFO - Scanning supplier folder: Zakprest (Documente/Documente Zakprest)
2026-04-10 18:55:00 - src.importers.document_importer - INFO - Imported new document: 2. ISO 9001.pdf (type: ISO 9001)
...

==================================================

Import Summary:
─────────────────────────────────────────────
Total Documents Found: 7
Total Imported: 7
Total Skipped (duplicates): 0
Total Classified: 6
Total Unclassified (needs review): 1

Per-Supplier Breakdown:
  Zakprest:
    Found: 3 | Imported: 3 | Skipped: 0 | Classified: 2 | Unclassified: 1
  TERAPLAST:
    Found: 2 | Imported: 2 | Skipped: 0 | Classified: 2 | Unclassified: 0
  VALROM:
    Found: 1 | Imported: 1 | Skipped: 0 | Classified: 1 | Unclassified: 0
  Tehnoworld:
    Found: 1 | Imported: 1 | Skipped: 0 | Classified: 1 | Unclassified: 0

==================================================

2026-04-10 18:55:01 - __main__ - INFO - Processing complete!
```

## Document Classification Patterns

The classifier uses regex patterns to identify document types from filenames with varying confidence levels:

### High-Confidence Patterns (0.9)

**Numbered Prefix Format:** `<number>. <document_type>.pdf`

Examples:
- `2. ISO 9001.pdf` → `ISO 9001`
- `7. AVS.pdf` → `AVS`
- `10. Fisa tehnica.pdf` → `Fisa tehnica`

### Medium-Confidence Patterns (0.7)

**Keyword Matching:** Case-insensitive keyword detection in any position

Supported document types (in priority order):
1. **Certificat ISO 9001** - matches "Certificat ISO 9001"
2. **Certificat ISO 14001** - matches "Certificat ISO 14001"
3. **Certificat ISO 45001** - matches "Certificat ISO 45001"
4. **ISO 9001** - matches "ISO 9001" (without "Certificat")
5. **ISO 14001** - matches "ISO 14001" (without "Certificat")
6. **ISO 45001** - matches "ISO 45001" (without "Certificat")
7. **AVS** - matches "AVS"
8. **Fisa tehnica** - matches "Fisa tehnica" or "Fișa tehnică" (Romanian diacritics)
9. **Certificat** - generic certificate (fallback)

Examples:
- `Certificat ISO 14001 SRAC 2025_2026.pdf` → `Certificat ISO 14001`
- `ISO 9001 Company Name.pdf` → `ISO 9001`
- `AVS_2024.pdf` → `AVS`

**Note:** Pattern order matters! More specific patterns (e.g., "Certificat ISO 14001") are checked before less specific ones (e.g., "ISO 14001") to ensure accurate classification.

### Unclassifiable Documents (0.0)

Documents that don't match any pattern are marked as unclassifiable with:
- `document_type = None`
- `classification_confidence = 0.0`
- `needs_review = True`

Example: `random_document.pdf` → Needs manual review

## Handling Unclassified Documents

Documents that cannot be automatically classified are flagged for manual review:

### Querying Unclassified Documents

You can query the database to find documents that need manual review:

```python
from src.models.database import SessionLocal
from src.models.document import Document

session = SessionLocal()
unclassified = session.query(Document).filter(Document.needs_review == True).all()

for doc in unclassified:
    print(f"File: {doc.filename}")
    print(f"Supplier: {doc.supplier.name}")
    print(f"Path: {doc.file_path}")
    print("---")

session.close()
```

### Manual Classification Workflow

1. Run the importer and note the "Unclassified (needs review)" count in the summary
2. Query the database for documents with `needs_review = True`
3. Review the actual file or filename
4. Update the database record with the correct document type:

```python
from src.models.database import SessionLocal
from src.models.document import Document

session = SessionLocal()
doc = session.query(Document).filter(Document.filename == "random_document.pdf").first()

if doc:
    doc.document_type = "Contract"  # or appropriate type
    doc.classification_confidence = 1.0  # manual classification
    doc.needs_review = False
    session.commit()

session.close()
```

## Database Schema

### Supplier Model
```
suppliers
├── id (INTEGER, PRIMARY KEY)
├── name (VARCHAR, UNIQUE)
├── folder_path (VARCHAR, UNIQUE)
└── created_at (TIMESTAMP)
```

### Document Model
```
documents
├── id (INTEGER, PRIMARY KEY)
├── supplier_id (INTEGER, FOREIGN KEY → suppliers.id)
├── file_path (VARCHAR)
├── filename (VARCHAR)
├── document_type (VARCHAR, NULLABLE)
├── classification_confidence (FLOAT)
├── file_hash (VARCHAR, UNIQUE) -- SHA256 for deduplication
├── needs_review (BOOLEAN)
└── created_at (TIMESTAMP)
```

### Relationships
- Each Document belongs to one Supplier (many-to-one)
- Each Supplier has many Documents (one-to-many, via `supplier.documents`)

## Idempotency & Deduplication

The importer is **idempotent** - running it multiple times on the same files will not create duplicates:

1. **SHA256 File Hashing:** Each file is hashed using SHA256
2. **Unique Constraint:** The `file_hash` column has a unique constraint
3. **Duplicate Detection:** Before importing, the system checks if a document with the same hash exists
4. **Skip Logic:** Duplicate files are logged and counted as "skipped" in the summary

**Example:**
```bash
# First run: imports 7 documents
python -m src.main --base-path tests/fixtures/sample_docs
# Output: Total Imported: 7, Total Skipped: 0

# Second run: skips all 7 documents (already in database)
python -m src.main --base-path tests/fixtures/sample_docs
# Output: Total Imported: 0, Total Skipped: 7
```

## Configuration

### Database Location

By default, the database is created as `scanner.db` in the current directory. To change this, edit `src/config/settings.py`:

```python
class Settings:
    def __init__(self):
        self.db_path = Path("scanner.db")  # Change to your preferred location
        self.database_url = f"sqlite:///{self.db_path}"
```

### Adding New Suppliers

To add support for additional suppliers, edit `src/config/settings.py`:

```python
self.supplier_folders = {
    "Zakprest": "Documente Zakprest",
    "TERAPLAST": "PEHD Apa - TERAPLAST",
    "VALROM": "PEHD Apa - VALROM",
    "Tehnoworld": "Teava apa PEHD - Tehnoworld",
    "NewSupplier": "Path/To/Supplier/Folder"  # Add new supplier here
}
```

### Adding Classification Patterns

To add new document type patterns, edit `src/importers/document_classifier.py`:

```python
self.keyword_patterns = [
    # Add your pattern here (most specific first)
    (re.compile(r'your_pattern', re.IGNORECASE), "Document Type Name"),
    # Existing patterns...
]
```

**Important:** Add more specific patterns at the beginning of the list to ensure correct classification priority.

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run with Coverage

```bash
pytest tests/ -v --cov=src --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`.

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared pytest fixtures
├── test_scanner.py          # FolderScanner tests
├── test_classifier.py       # DocumentClassifier tests
├── test_importer.py         # DocumentImporter tests
└── fixtures/
    └── sample_docs/         # Test PDF files
```

### Running Integration Tests

Test the full import flow with sample documents:

```bash
# Dry run test (no database changes)
python -m src.main --base-path tests/fixtures/sample_docs --dry-run

# Full import test
python -m src.main --base-path tests/fixtures/sample_docs

# Idempotency test (run twice, second run should skip all)
python -m src.main --base-path tests/fixtures/sample_docs
python -m src.main --base-path tests/fixtures/sample_docs
```

## Development

### Project Structure

```
scanner/
├── src/
│   ├── __init__.py
│   ├── main.py                      # CLI entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py              # Application settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py              # Database configuration
│   │   ├── supplier.py              # Supplier model
│   │   └── document.py              # Document model
│   ├── scanner/
│   │   ├── __init__.py
│   │   └── folder_scanner.py        # Folder scanning logic
│   └── importers/
│       ├── __init__.py
│       ├── document_classifier.py   # Classification logic
│       └── document_importer.py     # Import logic
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_scanner.py
│   ├── test_classifier.py
│   ├── test_importer.py
│   └── fixtures/
│       └── sample_docs/
├── requirements.txt
└── README.md
```

### Architecture

The system follows a layered architecture:

1. **Data Layer** (`src/models/`): SQLAlchemy models and database configuration
2. **Business Logic Layer**:
   - `src/scanner/`: File system scanning and discovery
   - `src/importers/`: Document classification and import logic
3. **Integration Layer** (`src/main.py`): CLI interface and orchestration

### Key Design Decisions

- **Generator Pattern:** `FolderScanner` uses generators (`yield`) for memory efficiency when scanning large folder structures
- **Context Manager:** `DocumentImporter` supports context manager protocol for automatic resource cleanup
- **Idempotency:** SHA256 file hashing prevents duplicate imports
- **Transaction Safety:** Database operations use SQLAlchemy sessions with proper commit/rollback
- **Error Handling:** Graceful error handling - individual file failures don't stop the entire import process
- **Confidence Scoring:** Classification confidence helps identify documents needing manual review

## Troubleshooting

### Database is Locked

If you see "database is locked" errors:
1. Close any open database connections or SQLite browsers
2. Run the import again
3. Consider using PostgreSQL for concurrent access in production

### No Documents Found

If the summary shows "No documents found":
1. Verify the `--base-path` points to the correct directory
2. Check that supplier folders exist and match `settings.supplier_folders`
3. Ensure PDF files exist in the supplier folders
4. Run with `--verbose` to see detailed scanning logs

### Classification Issues

If documents are incorrectly classified or not classified:
1. Check the filename patterns in `src/importers/document_classifier.py`
2. Add new patterns or adjust existing ones
3. Remember pattern order matters (most specific first)
4. Use `--verbose` to see which patterns are matching

### Duplicate Detection Not Working

If the same file is imported multiple times:
1. Check that the file content hasn't changed (hash is based on content)
2. Verify the `file_hash` unique constraint exists in the database
3. Drop the database and recreate: `rm scanner.db && python -m src.main`

## License

Copyright © 2026 Makyol. All rights reserved.

## Support

For issues or questions, please contact the development team.
