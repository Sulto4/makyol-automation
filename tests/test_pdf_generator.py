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
