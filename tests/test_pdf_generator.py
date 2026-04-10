"""Tests for PDF generator service."""
import pytest
from io import BytesIO
from datetime import datetime, timedelta

from src.services.pdf_generator import PDFGenerator


def test_supplier_summary_pdf():
    """Test generation of Supplier Summary PDF report."""
    # Initialize generator
    generator = PDFGenerator()

    # Sample supplier summary data
    # Table format: Supplier Name | Status | Document Count | Expiring Soon
    supplier_data = [
        {
            'name': 'ABC Construction Ltd.',
            'status': 'active',
            'document_count': 12,
            'expiring_soon': 2
        },
        {
            'name': 'XYZ Engineering Co.',
            'status': 'active',
            'document_count': 8,
            'expiring_soon': 0
        },
        {
            'name': 'BuildTech Industries',
            'status': 'pending',
            'document_count': 5,
            'expiring_soon': 1
        }
    ]

    # Generate report
    pdf_buffer = generator.generate_supplier_summary_pdf(
        supplier_data=supplier_data,
        preparer="Test User"
    )

    # Verify buffer is created and has content
    assert isinstance(pdf_buffer, BytesIO)
    pdf_content = pdf_buffer.getvalue()
    assert len(pdf_content) > 0

    # Verify it starts with PDF signature
    assert pdf_content.startswith(b'%PDF')


def test_document_inventory_pdf():
    """Test generation of Document Inventory PDF report."""
    # Initialize generator
    generator = PDFGenerator()

    # Sample document inventory data
    # Table format: Supplier | Document Type | Status | Validity Date | Certificate #
    document_data = [
        {
            'supplier_name': 'ABC Construction Ltd.',
            'document_type': 'ISO 9001 Certification',
            'status': 'valid',
            'validity_date': '2025-06-30',
            'certificate_number': 'ISO-9001-2024-001'
        },
        {
            'supplier_name': 'ABC Construction Ltd.',
            'document_type': 'Tax Clearance',
            'status': 'expiring',
            'validity_date': '2026-05-15',
            'certificate_number': 'TAX-2024-456'
        },
        {
            'supplier_name': 'XYZ Engineering Co.',
            'document_type': 'ISO 9001 Certification',
            'status': 'valid',
            'validity_date': '2027-01-20',
            'certificate_number': 'ISO-9001-2024-002'
        },
        {
            'supplier_name': 'BuildTech Industries',
            'document_type': 'Insurance Certificate',
            'status': 'expired',
            'validity_date': '2025-12-31',
            'certificate_number': 'INS-2024-789'
        }
    ]

    # Generate report
    pdf_buffer = generator.generate_document_inventory_pdf(
        document_data=document_data,
        preparer="Test User"
    )

    # Verify buffer is created and has content
    assert isinstance(pdf_buffer, BytesIO)
    pdf_content = pdf_buffer.getvalue()
    assert len(pdf_content) > 0

    # Verify it starts with PDF signature
    assert pdf_content.startswith(b'%PDF')


def test_expiring_certificates_pdf():
    """Test generation of Expiring Certificates PDF report."""
    # Initialize generator
    generator = PDFGenerator()

    # Sample expiring certificates data
    # Table format: Supplier | Document Type | Validity Date | Days Until Expiry | Certificate #
    certificate_data = [
        {
            'supplier_name': 'ABC Construction Ltd.',
            'document_type': 'Tax Clearance',
            'validity_date': '2026-05-15',
            'days_until_expiry': 35,
            'certificate_number': 'TAX-2024-456'
        },
        {
            'supplier_name': 'BuildTech Industries',
            'document_type': 'Insurance Certificate',
            'validity_date': '2026-04-25',
            'days_until_expiry': 15,
            'certificate_number': 'INS-2024-789'
        },
        {
            'supplier_name': 'XYZ Engineering Co.',
            'document_type': 'ISO 9001 Certification',
            'validity_date': '2026-05-01',
            'days_until_expiry': 21,
            'certificate_number': 'ISO-9001-2024-002'
        }
    ]

    # Generate report
    pdf_buffer = generator.generate_expiring_certificates_pdf(
        certificate_data=certificate_data,
        preparer="Test User"
    )

    # Verify buffer is created and has content
    assert isinstance(pdf_buffer, BytesIO)
    pdf_content = pdf_buffer.getvalue()
    assert len(pdf_content) > 0

    # Verify it starts with PDF signature
    assert pdf_content.startswith(b'%PDF')


def test_missing_documents_pdf():
    """Test generation of Missing Documents PDF report."""
    # Initialize generator
    generator = PDFGenerator()

    # Sample missing documents data
    # Table format: Supplier | Document Type | Required | Status
    missing_data = [
        {
            'supplier_name': 'ABC Construction Ltd.',
            'document_type': 'Environmental Compliance Certificate',
            'required': 'Always Required',
            'status': 'Missing'
        },
        {
            'supplier_name': 'BuildTech Industries',
            'document_type': 'Safety Certification',
            'required': 'Always Required',
            'status': 'Missing'
        },
        {
            'supplier_name': 'XYZ Engineering Co.',
            'document_type': 'Quality Assurance Certificate',
            'required': 'Always Required',
            'status': 'Missing'
        },
        {
            'supplier_name': 'BuildTech Industries',
            'document_type': 'Tax Clearance',
            'required': 'Always Required',
            'status': 'Missing'
        }
    ]

    # Generate report
    pdf_buffer = generator.generate_missing_documents_pdf(
        missing_data=missing_data,
        preparer="Test User"
    )

    # Verify buffer is created and has content
    assert isinstance(pdf_buffer, BytesIO)
    pdf_content = pdf_buffer.getvalue()
    assert len(pdf_content) > 0

    # Verify it starts with PDF signature
    assert pdf_content.startswith(b'%PDF')
