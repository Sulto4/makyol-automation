"""Performance tests for compliance report generation system."""
import pytest
import time
import statistics
from io import BytesIO
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.database import get_db, init_db
from src.models.supplier import Supplier
from src.models.document import Document


@pytest.fixture(scope="module")
def client():
    """Create test client for API testing."""
    # Initialize database
    init_db()

    # Create test client
    client = TestClient(app)

    # Generate sample data before tests
    response = client.post("/api/sample-data/generate")
    assert response.status_code == 200

    yield client


@pytest.fixture(scope="module")
def large_dataset_client():
    """Create test client with a large dataset for stress testing."""
    # Initialize database
    init_db()

    # Create test client
    test_client = TestClient(app)

    # Generate large dataset
    db = next(get_db())
    try:
        # Clear existing data
        db.query(Document).delete()
        db.query(Supplier).delete()
        db.commit()

        # Create 50 suppliers
        suppliers = []
        for i in range(50):
            supplier = Supplier(
                name=f"Test Supplier {i+1}",
                status=["active", "inactive", "pending"][i % 3]
            )
            db.add(supplier)
            suppliers.append(supplier)
        db.commit()

        # Refresh to get IDs
        for supplier in suppliers:
            db.refresh(supplier)

        # Create 10 documents per supplier (500 total)
        today = date.today()
        doc_types = [
            "ISO 9001 Certificate",
            "Tax Certificate",
            "Insurance Policy",
            "Health & Safety Certificate",
            "Environmental Certificate",
            "Quality Assurance Certificate",
            "Business License",
            "Trade Certificate",
            "Export License",
            "Import License",
        ]

        documents = []
        for supplier in suppliers:
            for j, doc_type in enumerate(doc_types):
                # Vary status and dates for realistic data
                status_options = ["valid", "expired", "missing", "pending"]
                status = status_options[j % 4]

                if status == "missing":
                    validity_date = None
                    cert_number = None
                elif status == "expired":
                    validity_date = today - timedelta(days=(j * 10) + 10)
                    cert_number = f"CERT-{supplier.id}-{j:03d}"
                else:
                    validity_date = today + timedelta(days=(j * 30) + 30)
                    cert_number = f"CERT-{supplier.id}-{j:03d}"

                document = Document(
                    supplier_id=supplier.id,
                    type=doc_type,
                    status=status,
                    validity_date=validity_date,
                    certificate_number=cert_number
                )
                documents.append(document)
                db.add(document)

        db.commit()

        yield test_client

    finally:
        db.close()


class TestIndividualReportPerformance:
    """Test performance of individual report generation."""

    def test_supplier_summary_pdf_performance(self, client):
        """Test Supplier Summary PDF generation completes within 5 seconds."""
        start_time = time.time()

        response = client.post(
            "/api/reports/generate",
            json={
                "report_type": "supplier_summary",
                "format": "pdf",
                "preparer": "Performance Test User"
            }
        )

        generation_time = time.time() - start_time

        assert response.status_code == 200
        assert len(response.content) > 0
        assert generation_time < 5.0, f"PDF generation took {generation_time:.3f}s (should be < 5s)"
        print(f"\n  Supplier Summary PDF: {generation_time:.3f}s")

    def test_supplier_summary_excel_performance(self, client):
        """Test Supplier Summary Excel generation completes within 5 seconds."""
        start_time = time.time()

        response = client.post(
            "/api/reports/generate",
            json={
                "report_type": "supplier_summary",
                "format": "excel",
                "preparer": "Performance Test User"
            }
        )

        generation_time = time.time() - start_time

        assert response.status_code == 200
        assert len(response.content) > 0
        assert generation_time < 5.0, f"Excel generation took {generation_time:.3f}s (should be < 5s)"
        print(f"  Supplier Summary Excel: {generation_time:.3f}s")

    def test_document_inventory_pdf_performance(self, client):
        """Test Document Inventory PDF generation completes within 5 seconds."""
        start_time = time.time()

        response = client.post(
            "/api/reports/generate",
            json={
                "report_type": "document_inventory",
                "format": "pdf",
                "preparer": "Performance Test User"
            }
        )

        generation_time = time.time() - start_time

        assert response.status_code == 200
        assert len(response.content) > 0
        assert generation_time < 5.0, f"PDF generation took {generation_time:.3f}s (should be < 5s)"
        print(f"  Document Inventory PDF: {generation_time:.3f}s")

    def test_document_inventory_excel_performance(self, client):
        """Test Document Inventory Excel generation completes within 5 seconds."""
        start_time = time.time()

        response = client.post(
            "/api/reports/generate",
            json={
                "report_type": "document_inventory",
                "format": "excel",
                "preparer": "Performance Test User"
            }
        )

        generation_time = time.time() - start_time

        assert response.status_code == 200
        assert len(response.content) > 0
        assert generation_time < 5.0, f"Excel generation took {generation_time:.3f}s (should be < 5s)"
        print(f"  Document Inventory Excel: {generation_time:.3f}s")

    def test_full_audit_pdf_performance(self, client):
        """Test Full Audit PDF generation completes within 5 seconds."""
        start_time = time.time()

        response = client.post(
            "/api/reports/generate",
            json={
                "report_type": "full_audit",
                "format": "pdf",
                "preparer": "Performance Test User"
            }
        )

        generation_time = time.time() - start_time

        assert response.status_code == 200
        assert len(response.content) > 0
        assert generation_time < 5.0, f"PDF generation took {generation_time:.3f}s (should be < 5s)"
        print(f"  Full Audit PDF: {generation_time:.3f}s")

    def test_full_audit_excel_performance(self, client):
        """Test Full Audit Excel generation completes within 5 seconds."""
        start_time = time.time()

        response = client.post(
            "/api/reports/generate",
            json={
                "report_type": "full_audit",
                "format": "excel",
                "preparer": "Performance Test User"
            }
        )

        generation_time = time.time() - start_time

        assert response.status_code == 200
        assert len(response.content) > 0
        assert generation_time < 5.0, f"Excel generation took {generation_time:.3f}s (should be < 5s)"
        print(f"  Full Audit Excel: {generation_time:.3f}s")


class TestLargeDatasetPerformance:
    """Test performance with large datasets."""

    def test_large_dataset_supplier_summary_pdf(self, large_dataset_client):
        """Test Supplier Summary PDF with 50 suppliers."""
        start_time = time.time()

        response = large_dataset_client.post(
            "/api/reports/generate",
            json={
                "report_type": "supplier_summary",
                "format": "pdf",
                "preparer": "Performance Test User"
            }
        )

        generation_time = time.time() - start_time

        assert response.status_code == 200
        assert len(response.content) > 0
        assert generation_time < 5.0, f"Large dataset PDF took {generation_time:.3f}s (should be < 5s)"
        print(f"\n  Large Dataset (50 suppliers) - Supplier Summary PDF: {generation_time:.3f}s")

    def test_large_dataset_document_inventory_pdf(self, large_dataset_client):
        """Test Document Inventory PDF with 500 documents."""
        start_time = time.time()

        response = large_dataset_client.post(
            "/api/reports/generate",
            json={
                "report_type": "document_inventory",
                "format": "pdf",
                "preparer": "Performance Test User"
            }
        )

        generation_time = time.time() - start_time

        assert response.status_code == 200
        assert len(response.content) > 0
        assert generation_time < 5.0, f"Large dataset PDF took {generation_time:.3f}s (should be < 5s)"
        print(f"  Large Dataset (500 documents) - Document Inventory PDF: {generation_time:.3f}s")

    def test_large_dataset_full_audit_excel(self, large_dataset_client):
        """Test Full Audit Excel with large dataset (most comprehensive report)."""
        start_time = time.time()

        response = large_dataset_client.post(
            "/api/reports/generate",
            json={
                "report_type": "full_audit",
                "format": "excel",
                "preparer": "Performance Test User"
            }
        )

        generation_time = time.time() - start_time

        assert response.status_code == 200
        assert len(response.content) > 0
        assert generation_time < 5.0, f"Large dataset Excel took {generation_time:.3f}s (should be < 5s)"
        print(f"  Large Dataset - Full Audit Excel (multi-sheet): {generation_time:.3f}s")


class TestConcurrentReportGeneration:
    """Test concurrent report generation performance."""

    def test_concurrent_pdf_generation(self, client):
        """Test generating multiple PDF reports concurrently."""
        def generate_report(report_type):
            """Generate a single report and return timing info."""
            start = time.time()
            response = client.post(
                "/api/reports/generate",
                json={
                    "report_type": report_type,
                    "format": "pdf",
                    "preparer": "Concurrent Test User"
                }
            )
            duration = time.time() - start
            return {
                "report_type": report_type,
                "duration": duration,
                "status_code": response.status_code,
                "size": len(response.content)
            }

        # Test concurrent generation of 5 different report types
        report_types = [
            "supplier_summary",
            "document_inventory",
            "expiring_certificates",
            "missing_documents",
            "full_audit"
        ]

        overall_start = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(generate_report, rt) for rt in report_types]
            results = [future.result() for future in as_completed(futures)]

        overall_duration = time.time() - overall_start

        # Verify all reports succeeded
        for result in results:
            assert result["status_code"] == 200
            assert result["size"] > 0
            assert result["duration"] < 5.0

        print(f"\n  Concurrent generation of 5 PDFs:")
        print(f"    Total time: {overall_duration:.3f}s")
        print(f"    Average per report: {statistics.mean([r['duration'] for r in results]):.3f}s")

    def test_concurrent_mixed_format_generation(self, client):
        """Test generating multiple reports in different formats concurrently."""
        def generate_report(report_type, format_type):
            """Generate a single report and return timing info."""
            start = time.time()
            response = client.post(
                "/api/reports/generate",
                json={
                    "report_type": report_type,
                    "format": format_type,
                    "preparer": "Concurrent Test User"
                }
            )
            duration = time.time() - start
            return {
                "report_type": report_type,
                "format": format_type,
                "duration": duration,
                "status_code": response.status_code,
                "size": len(response.content)
            }

        # Mix of PDF and Excel reports
        report_configs = [
            ("supplier_summary", "pdf"),
            ("supplier_summary", "excel"),
            ("document_inventory", "pdf"),
            ("document_inventory", "excel"),
            ("full_audit", "pdf"),
            ("full_audit", "excel"),
        ]

        overall_start = time.time()

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(generate_report, rt, fmt) for rt, fmt in report_configs]
            results = [future.result() for future in as_completed(futures)]

        overall_duration = time.time() - overall_start

        # Verify all reports succeeded
        for result in results:
            assert result["status_code"] == 200
            assert result["size"] > 0
            assert result["duration"] < 5.0

        print(f"\n  Concurrent generation of 6 mixed reports (3 PDF + 3 Excel):")
        print(f"    Total time: {overall_duration:.3f}s")
        print(f"    Average per report: {statistics.mean([r['duration'] for r in results]):.3f}s")


class TestPerformanceConsistency:
    """Test performance consistency across multiple runs."""

    def test_pdf_generation_consistency(self, client):
        """Test PDF generation time consistency across 10 runs."""
        times = []
        report_type = "supplier_summary"

        for i in range(10):
            start = time.time()
            response = client.post(
                "/api/reports/generate",
                json={
                    "report_type": report_type,
                    "format": "pdf",
                    "preparer": "Consistency Test User"
                }
            )
            duration = time.time() - start
            times.append(duration)

            assert response.status_code == 200
            assert len(response.content) > 0
            assert duration < 5.0

        # Calculate statistics
        mean_time = statistics.mean(times)
        stdev_time = statistics.stdev(times) if len(times) > 1 else 0
        min_time = min(times)
        max_time = max(times)

        print(f"\n  PDF Generation Consistency (10 runs):")
        print(f"    Mean: {mean_time:.3f}s")
        print(f"    Std Dev: {stdev_time:.3f}s")
        print(f"    Min: {min_time:.3f}s")
        print(f"    Max: {max_time:.3f}s")

        # Verify consistency - standard deviation should be reasonable
        # (less than 50% of mean indicates good consistency)
        assert stdev_time < mean_time * 0.5, "Performance variance too high"

    def test_excel_generation_consistency(self, client):
        """Test Excel generation time consistency across 10 runs."""
        times = []
        report_type = "document_inventory"

        for i in range(10):
            start = time.time()
            response = client.post(
                "/api/reports/generate",
                json={
                    "report_type": report_type,
                    "format": "excel",
                    "preparer": "Consistency Test User"
                }
            )
            duration = time.time() - start
            times.append(duration)

            assert response.status_code == 200
            assert len(response.content) > 0
            assert duration < 5.0

        # Calculate statistics
        mean_time = statistics.mean(times)
        stdev_time = statistics.stdev(times) if len(times) > 1 else 0
        min_time = min(times)
        max_time = max(times)

        print(f"\n  Excel Generation Consistency (10 runs):")
        print(f"    Mean: {mean_time:.3f}s")
        print(f"    Std Dev: {stdev_time:.3f}s")
        print(f"    Min: {min_time:.3f}s")
        print(f"    Max: {max_time:.3f}s")

        # Verify consistency
        assert stdev_time < mean_time * 0.5, "Performance variance too high"


class TestMemoryEfficiency:
    """Test memory efficiency during report generation."""

    def test_large_report_file_sizes(self, large_dataset_client):
        """Test that generated files have reasonable sizes."""
        # Generate full audit report with large dataset
        response = large_dataset_client.post(
            "/api/reports/generate",
            json={
                "report_type": "full_audit",
                "format": "pdf",
                "preparer": "Memory Test User"
            }
        )

        assert response.status_code == 200
        pdf_size = len(response.content)

        # PDF should be reasonable size (< 10MB for 500 documents)
        max_size = 10 * 1024 * 1024  # 10MB
        assert pdf_size < max_size, f"PDF size {pdf_size} bytes exceeds {max_size} bytes"
        print(f"\n  Full Audit PDF with 500 documents: {pdf_size / 1024:.1f} KB")

        # Test Excel
        response = large_dataset_client.post(
            "/api/reports/generate",
            json={
                "report_type": "full_audit",
                "format": "excel",
                "preparer": "Memory Test User"
            }
        )

        assert response.status_code == 200
        excel_size = len(response.content)

        # Excel should be reasonable size (< 5MB for 500 documents)
        max_size = 5 * 1024 * 1024  # 5MB
        assert excel_size < max_size, f"Excel size {excel_size} bytes exceeds {max_size} bytes"
        print(f"  Full Audit Excel with 500 documents: {excel_size / 1024:.1f} KB")


class TestPerformanceBenchmark:
    """Comprehensive performance benchmark of all report types."""

    def test_all_reports_performance_benchmark(self, client):
        """
        Benchmark all report types in both formats.
        Generates a comprehensive performance report.
        """
        report_configs = [
            ("supplier_summary", "pdf"),
            ("supplier_summary", "excel"),
            ("document_inventory", "pdf"),
            ("document_inventory", "excel"),
            ("expiring_certificates", "pdf"),
            ("expiring_certificates", "excel"),
            ("missing_documents", "pdf"),
            ("missing_documents", "excel"),
            ("full_audit", "pdf"),
            ("full_audit", "excel"),
        ]

        results = []
        total_start = time.time()

        for report_type, format_type in report_configs:
            start = time.time()

            response = client.post(
                "/api/reports/generate",
                json={
                    "report_type": report_type,
                    "format": format_type,
                    "preparer": "Benchmark Test User"
                }
            )

            duration = time.time() - start

            assert response.status_code == 200
            assert len(response.content) > 0
            assert duration < 5.0

            results.append({
                "report_type": report_type,
                "format": format_type,
                "duration": duration,
                "size_kb": len(response.content) / 1024
            })

        total_duration = time.time() - total_start

        # Print comprehensive benchmark report
        print("\n" + "="*80)
        print("PERFORMANCE BENCHMARK REPORT")
        print("="*80)
        print(f"{'Report Type':<30} {'Format':<8} {'Time (s)':<12} {'Size (KB)':<12}")
        print("-"*80)

        for result in results:
            print(f"{result['report_type']:<30} {result['format']:<8} "
                  f"{result['duration']:<12.3f} {result['size_kb']:<12.1f}")

        print("-"*80)
        print(f"Total time for all 10 reports: {total_duration:.2f}s")
        print(f"Average time per report: {statistics.mean([r['duration'] for r in results]):.3f}s")
        print(f"Fastest report: {min(results, key=lambda x: x['duration'])['report_type']} "
              f"({min(results, key=lambda x: x['duration'])['format']}) - "
              f"{min([r['duration'] for r in results]):.3f}s")
        print(f"Slowest report: {max(results, key=lambda x: x['duration'])['report_type']} "
              f"({max(results, key=lambda x: x['duration'])['format']}) - "
              f"{max([r['duration'] for r in results]):.3f}s")
        print("="*80)

        # All reports should meet the 5-second requirement
        assert all(r["duration"] < 5.0 for r in results), "All reports must complete in < 5 seconds"
