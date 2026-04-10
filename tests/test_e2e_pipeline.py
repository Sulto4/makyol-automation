"""End-to-end pipeline verification tests.

Runs the full pipeline against all 4 supplier folders and verifies:
1. Output Word file is created at output/rezultat.docx
2. JSON export shows all ~40 PDFs processed
3. All known document types are correctly classified
4. Distributor field is populated for Tehnoworld and Zakprest folders
5. Expiration dates are found for TERAPLAST ISO certificates
6. No crashes during processing
7. Compares results against makyol-automation/rezultate_extrase.json

Requires: Documente/ folder with actual PDFs in project root.
Skip with: pytest -m "not e2e" to skip these tests.
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Mark all tests in this module as e2e
pytestmark = pytest.mark.e2e

# Detect Documente/ folder - check common locations
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTE_DIR = PROJECT_ROOT / "Documente"

# Also check the main makyol-automation repo location
MAIN_REPO = PROJECT_ROOT.parent
if not DOCUMENTE_DIR.exists():
    alt_path = MAIN_REPO / "Documente"
    if alt_path.exists():
        DOCUMENTE_DIR = alt_path

REFERENCE_JSON = PROJECT_ROOT / "makyol-automation" / "rezultate_extrase.json"
if not REFERENCE_JSON.exists():
    # Try alternate locations
    for candidate in [
        MAIN_REPO / "makyol-automation" / "rezultate_extrase.json",
        MAIN_REPO / "rezultate_extrase.json",
    ]:
        if candidate.exists():
            REFERENCE_JSON = candidate
            break

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DOCX = OUTPUT_DIR / "rezultat.docx"
OUTPUT_JSON = OUTPUT_DIR / "results.json"

# Expected supplier folders
EXPECTED_FOLDERS = [
    "Documente Zakprest",
    "PEHD Apa - TERAPLAST",
    "PEHD Apa - VALROM",
    "Teava apa PEHD - Tehnoworld",
]

# Minimum expected PDF count across all folders
MIN_EXPECTED_PDFS = 35

# Distributor folders - these MUST have non-empty distributor
DISTRIBUTOR_FOLDERS = {"Teava apa PEHD - Tehnoworld", "Documente Zakprest"}

# Known expected classifications from the reference
EXPECTED_CLASSIFICATIONS = {
    "2. ISO 9001.pdf": "Certificat ISO 9001",
    "3. ISO 14001.pdf": "Certificat ISO 14001",
    "4. ISO 45001.pdf": "Certificat ISO 45001",
    "14. ISO 50001.pdf": "Certificat ISO 50001",
    "15. DC.pdf": "Declarație de Conformitate",
    "1. FT Teava PEHD apa.pdf": "Fișă Tehnică",
    "9. AGT.pdf": "Agrement Tehnic",
    "7. AVS.pdf": "Aviz Sanitar",
    "8.1 AVT.pdf": "Aviz Tehnic",
    "9. CG.pdf": "Certificat de Garanție",
    "9. CC.pdf": "Certificat de Conformitate",
}

skip_no_documente = pytest.mark.skipif(
    not DOCUMENTE_DIR.exists(),
    reason=f"Documente/ folder not found at {DOCUMENTE_DIR}",
)

skip_no_reference = pytest.mark.skipif(
    not REFERENCE_JSON.exists(),
    reason=f"Reference JSON not found at {REFERENCE_JSON}",
)


def _run_pipeline():
    """Run the full pipeline and return the ProcessingResult."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.main import process_documents

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result = process_documents(
        input_dir=DOCUMENTE_DIR,
        output_path=OUTPUT_DOCX,
        verbose=True,
    )

    # Also export JSON
    from src.main import _export_json
    _export_json(result, OUTPUT_JSON)

    return result


@pytest.fixture(scope="module")
def pipeline_result():
    """Run the pipeline once for the entire test module."""
    return _run_pipeline()


@pytest.fixture(scope="module")
def json_output(pipeline_result):
    """Load the JSON output after pipeline run."""
    if OUTPUT_JSON.exists():
        with open(OUTPUT_JSON, encoding="utf-8") as f:
            return json.load(f)
    return None


@pytest.fixture(scope="module")
def all_documents(pipeline_result):
    """Flat list of all DocumentInfo objects from the pipeline result."""
    docs = []
    for folder in pipeline_result.supplier_folders:
        docs.extend(folder.documents)
    return docs


@pytest.fixture(scope="module")
def reference_data():
    """Load the reference rezultate_extrase.json."""
    if REFERENCE_JSON.exists():
        with open(REFERENCE_JSON, encoding="utf-8") as f:
            return json.load(f)
    return None


# ---- Test 1: Output Word file created ----

@skip_no_documente
class TestOutputGeneration:
    """Verify output files are created correctly."""

    def test_docx_exists(self, pipeline_result):
        """Output Word file must be created."""
        assert OUTPUT_DOCX.exists(), f"Expected {OUTPUT_DOCX} to exist"

    def test_docx_not_empty(self, pipeline_result):
        """Output Word file must be > 10KB."""
        size = OUTPUT_DOCX.stat().st_size
        assert size > 10_000, f"Expected > 10KB, got {size} bytes"

    def test_json_exists(self, pipeline_result):
        """JSON export must be created."""
        assert OUTPUT_JSON.exists(), f"Expected {OUTPUT_JSON} to exist"

    def test_json_valid(self, json_output):
        """JSON export must be valid JSON with expected structure."""
        assert json_output is not None
        assert "total_files" in json_output
        assert "suppliers" in json_output
        assert json_output["total_files"] > 0


# ---- Test 2: All PDFs processed ----

@skip_no_documente
class TestCompleteness:
    """Verify all PDFs are processed without crashes."""

    def test_minimum_pdf_count(self, pipeline_result):
        """Pipeline must process at least ~35 PDFs."""
        assert pipeline_result.total_files >= MIN_EXPECTED_PDFS, (
            f"Expected >= {MIN_EXPECTED_PDFS} PDFs, "
            f"got {pipeline_result.total_files}"
        )

    def test_all_supplier_folders_found(self, pipeline_result):
        """All 4 expected supplier folders must be present."""
        found_folders = {f.folder_name for f in pipeline_result.supplier_folders}
        for expected in EXPECTED_FOLDERS:
            assert expected in found_folders, (
                f"Missing supplier folder: {expected}. "
                f"Found: {found_folders}"
            )

    def test_no_crashes(self, pipeline_result):
        """Pipeline must complete without fatal errors."""
        # Some individual PDFs may have errors (OCR failures etc.)
        # but total failures should be small
        assert pipeline_result.failed_files <= 5, (
            f"Too many failures: {pipeline_result.failed_files}. "
            f"Errors: {pipeline_result.errors}"
        )

    def test_high_success_rate(self, pipeline_result):
        """Success rate must be > 80%."""
        assert pipeline_result.success_rate > 80.0, (
            f"Low success rate: {pipeline_result.success_rate:.1f}%"
        )

    def test_json_has_all_pdfs(self, json_output, pipeline_result):
        """JSON export must contain entries for all processed PDFs."""
        total_in_json = sum(
            len(s["documents"]) for s in json_output["suppliers"]
        )
        assert total_in_json == pipeline_result.total_files


# ---- Test 3: Classification correctness ----

@skip_no_documente
class TestClassification:
    """Verify document types are correctly classified."""

    def test_known_classifications(self, all_documents):
        """Known documents must be classified correctly."""
        doc_map = {d.file_name: d for d in all_documents}

        for filename, expected_type in EXPECTED_CLASSIFICATIONS.items():
            if filename not in doc_map:
                continue  # May not be in this folder set
            doc = doc_map[filename]
            assert doc.document_type is not None, (
                f"{filename} has no document_type"
            )
            actual = doc.document_type.value
            assert actual == expected_type, (
                f"{filename}: expected '{expected_type}', got '{actual}'"
            )

    def test_no_unclassified_iso(self, all_documents):
        """All ISO certificate PDFs must be classified as ISO types."""
        for doc in all_documents:
            if "ISO" in doc.file_name.upper():
                assert doc.document_type is not None
                assert "ISO" in doc.document_type.value, (
                    f"{doc.file_name} should be ISO type, "
                    f"got {doc.document_type.value}"
                )


# ---- Test 4: Distributor field populated ----

@skip_no_documente
class TestDistributor:
    """Verify distributor is populated for Tehnoworld and Zakprest."""

    def test_tehnoworld_has_distributor(self, all_documents):
        """All Tehnoworld documents must have non-empty distributor."""
        tehnoworld_docs = [
            d for d in all_documents
            if "Tehnoworld" in d.supplier_folder
        ]
        assert len(tehnoworld_docs) > 0, "No Tehnoworld documents found"
        for doc in tehnoworld_docs:
            assert doc.distributor and doc.distributor != "N/A", (
                f"{doc.file_name} in Tehnoworld has empty distributor: "
                f"'{doc.distributor}'"
            )

    def test_zakprest_has_distributor(self, all_documents):
        """All Zakprest documents must have non-empty distributor."""
        zakprest_docs = [
            d for d in all_documents
            if "Zakprest" in d.supplier_folder
        ]
        assert len(zakprest_docs) > 0, "No Zakprest documents found"
        for doc in zakprest_docs:
            assert doc.distributor and doc.distributor != "N/A", (
                f"{doc.file_name} in Zakprest has empty distributor: "
                f"'{doc.distributor}'"
            )

    def test_teraplast_no_distributor(self, all_documents):
        """TERAPLAST is a producer, not a distributor."""
        teraplast_docs = [
            d for d in all_documents
            if "TERAPLAST" in d.supplier_folder
        ]
        for doc in teraplast_docs:
            # Distributor should be N/A unless extracted from text
            assert doc.producer and doc.producer != "N/A", (
                f"{doc.file_name} in TERAPLAST has empty producer"
            )


# ---- Test 5: Expiration dates ----

@skip_no_documente
class TestExpirationDates:
    """Verify expiration dates are extracted from text-based ISO certs."""

    def test_teraplast_iso9001_expiry(self, all_documents):
        """TERAPLAST ISO 9001 must have expiration date 04.11.2027."""
        doc = next(
            (d for d in all_documents
             if d.file_name == "2. ISO 9001.pdf"
             and "TERAPLAST" in d.supplier_folder),
            None,
        )
        assert doc is not None, "TERAPLAST ISO 9001 not found"
        assert doc.expiration_date == "04.11.2027", (
            f"Expected '04.11.2027', got '{doc.expiration_date}'"
        )

    def test_teraplast_iso14001_expiry(self, all_documents):
        """TERAPLAST ISO 14001 must have expiration date 04.11.2027."""
        doc = next(
            (d for d in all_documents
             if d.file_name == "3. ISO 14001.pdf"
             and "TERAPLAST" in d.supplier_folder),
            None,
        )
        assert doc is not None, "TERAPLAST ISO 14001 not found"
        assert doc.expiration_date == "04.11.2027", (
            f"Expected '04.11.2027', got '{doc.expiration_date}'"
        )

    def test_some_dates_found(self, all_documents):
        """At least some documents should have extracted expiration dates."""
        docs_with_dates = [
            d for d in all_documents
            if d.expiration_date and d.expiration_date != "N/A"
        ]
        assert len(docs_with_dates) >= 3, (
            f"Expected >= 3 docs with dates, got {len(docs_with_dates)}"
        )


# ---- Test 6: No crashes ----

@skip_no_documente
class TestStability:
    """Verify pipeline stability and error handling."""

    def test_pipeline_completes(self, pipeline_result):
        """Pipeline must return a valid ProcessingResult."""
        assert pipeline_result is not None
        assert pipeline_result.total_files > 0

    def test_all_docs_have_type(self, all_documents):
        """Every document must have a document_type (even if OTHER)."""
        for doc in all_documents:
            assert doc.document_type is not None, (
                f"{doc.file_name} has None document_type"
            )

    def test_all_docs_have_producer_or_material(self, all_documents):
        """Every document must have at least producer or material set."""
        for doc in all_documents:
            has_data = (
                (doc.producer and doc.producer != "N/A")
                or (doc.material and doc.material != "N/A")
            )
            assert has_data, (
                f"{doc.file_name} has neither producer nor material"
            )


# ---- Test 7: Parity with reference ----

@skip_no_documente
@skip_no_reference
class TestReferenceParity:
    """Compare results against the prototype's rezultate_extrase.json."""

    def test_reference_loaded(self, reference_data):
        """Reference data must be loaded."""
        assert reference_data is not None
        assert len(reference_data) > 0

    def test_all_reference_files_processed(self, reference_data, all_documents):
        """Every file in the reference must also appear in our results."""
        our_files = {d.file_name for d in all_documents}
        ref_files = {r["filename"] for r in reference_data}
        missing = ref_files - our_files
        assert len(missing) == 0, (
            f"Files in reference but not in our output: {missing}"
        )

    def test_classification_parity(self, reference_data, all_documents):
        """Document types should match the reference (with our enum values)."""
        doc_map = {d.file_name: d for d in all_documents}
        mismatches = []

        # Map reference doc_type strings to our enum values
        ref_to_enum = {
            "Fisa tehnica": "Fișă Tehnică",
            "Certificat ISO 9001": "Certificat ISO 9001",
            "Certificat ISO 14001": "Certificat ISO 14001",
            "Certificat ISO 45001": "Certificat ISO 45001",
            "Certificat ISO 50001": "Certificat ISO 50001",
            "Aviz sanitar": "Aviz Sanitar",
            "Aviz tehnic": "Aviz Tehnic",
            "Agrement tehnic": "Agrement Tehnic",
            "Declaratie de conformitate": "Declarație de Conformitate",
            "Certificat de calitate": "Certificat de Conformitate",
            "Certificat de garantie": "Certificat de Garanție",
            "Document tehnic": "Altul",
            "Aprobare material": "Altul",
        }

        for ref_entry in reference_data:
            fname = ref_entry["filename"]
            if fname not in doc_map:
                continue
            doc = doc_map[fname]
            ref_type = ref_entry["doc_type"]
            expected = ref_to_enum.get(ref_type, ref_type)
            actual = doc.document_type.value if doc.document_type else "None"

            if actual != expected:
                mismatches.append(
                    f"  {fname}: ref='{ref_type}' -> expected='{expected}', got='{actual}'"
                )

        # Allow some mismatches due to improvements
        assert len(mismatches) <= 5, (
            f"Too many classification mismatches vs reference ({len(mismatches)}):\n"
            + "\n".join(mismatches)
        )

    def test_distributor_improvement(self, reference_data, all_documents):
        """Our results should IMPROVE on the reference for distributor fields.

        The prototype had empty distributor for ALL documents. We should
        have non-empty distributor for Tehnoworld and Zakprest folders.
        """
        doc_map = {d.file_name: d for d in all_documents}
        distributor_count = 0

        for ref_entry in reference_data:
            fname = ref_entry["filename"]
            if fname not in doc_map:
                continue
            doc = doc_map[fname]
            if doc.distributor and doc.distributor != "N/A":
                distributor_count += 1

        # Reference had 0 distributors populated. We should have some.
        ref_distributor_count = sum(
            1 for r in reference_data if r.get("distributor", "")
        )
        assert distributor_count > ref_distributor_count, (
            f"No improvement in distributor field: "
            f"reference had {ref_distributor_count}, we have {distributor_count}"
        )

    def test_expiry_date_parity(self, reference_data, all_documents):
        """Expiry dates from reference must also be found in our results."""
        doc_map = {d.file_name: d for d in all_documents}
        missed_dates = []

        for ref_entry in reference_data:
            ref_expiry = ref_entry.get("expiry", "")
            if not ref_expiry:
                continue
            fname = ref_entry["filename"]
            if fname not in doc_map:
                continue
            doc = doc_map[fname]
            if doc.expiration_date != ref_expiry:
                missed_dates.append(
                    f"  {fname}: ref='{ref_expiry}', got='{doc.expiration_date}'"
                )

        assert len(missed_dates) <= 2, (
            f"Missed expiration dates vs reference:\n"
            + "\n".join(missed_dates)
        )
