"""Sample data generation service for testing purposes."""
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Dict

from src.models.supplier import Supplier
from src.models.document import Document


def generate_sample_data(db: Session) -> Dict[str, int]:
    """
    Generate sample suppliers and documents for testing.

    Args:
        db: Database session

    Returns:
        Dictionary with counts of created suppliers and documents
    """
    # Clear existing data
    db.query(Document).delete()
    db.query(Supplier).delete()
    db.commit()

    # Create sample suppliers
    suppliers = [
        Supplier(name="Acme Steel Corp", status="active"),
        Supplier(name="Global Cement Ltd", status="active"),
        Supplier(name="TechParts Manufacturing", status="active"),
        Supplier(name="SafeEquip Industries", status="inactive"),
        Supplier(name="QuickSupply Co", status="pending"),
    ]

    for supplier in suppliers:
        db.add(supplier)
    db.commit()

    # Refresh to get IDs
    for supplier in suppliers:
        db.refresh(supplier)

    # Document types
    doc_types = [
        "ISO 9001 Certificate",
        "Tax Certificate",
        "Insurance Policy",
        "Health & Safety Certificate",
        "Environmental Certificate",
        "Quality Assurance Certificate",
    ]

    # Create sample documents
    documents = []
    today = date.today()

    # Supplier 1 - Acme Steel Corp (mostly valid)
    documents.extend([
        Document(
            supplier_id=suppliers[0].id,
            type="ISO 9001 Certificate",
            status="valid",
            validity_date=today + timedelta(days=180),
            certificate_number="ISO-2024-001"
        ),
        Document(
            supplier_id=suppliers[0].id,
            type="Tax Certificate",
            status="valid",
            validity_date=today + timedelta(days=120),
            certificate_number="TAX-2024-100"
        ),
        Document(
            supplier_id=suppliers[0].id,
            type="Insurance Policy",
            status="valid",
            validity_date=today + timedelta(days=90),
            certificate_number="INS-2024-500"
        ),
    ])

    # Supplier 2 - Global Cement Ltd (some expiring soon)
    documents.extend([
        Document(
            supplier_id=suppliers[1].id,
            type="ISO 9001 Certificate",
            status="valid",
            validity_date=today + timedelta(days=15),  # Expiring soon
            certificate_number="ISO-2024-002"
        ),
        Document(
            supplier_id=suppliers[1].id,
            type="Tax Certificate",
            status="valid",
            validity_date=today + timedelta(days=25),  # Expiring soon
            certificate_number="TAX-2024-101"
        ),
        Document(
            supplier_id=suppliers[1].id,
            type="Health & Safety Certificate",
            status="expired",
            validity_date=today - timedelta(days=30),
            certificate_number="HSE-2023-200"
        ),
    ])

    # Supplier 3 - TechParts Manufacturing (mixed status)
    documents.extend([
        Document(
            supplier_id=suppliers[2].id,
            type="ISO 9001 Certificate",
            status="valid",
            validity_date=today + timedelta(days=200),
            certificate_number="ISO-2024-003"
        ),
        Document(
            supplier_id=suppliers[2].id,
            type="Environmental Certificate",
            status="missing",
            validity_date=None,
            certificate_number=None
        ),
        Document(
            supplier_id=suppliers[2].id,
            type="Quality Assurance Certificate",
            status="pending",
            validity_date=today + timedelta(days=60),
            certificate_number="QA-2024-300"
        ),
    ])

    # Supplier 4 - SafeEquip Industries (inactive, some expired)
    documents.extend([
        Document(
            supplier_id=suppliers[3].id,
            type="ISO 9001 Certificate",
            status="expired",
            validity_date=today - timedelta(days=60),
            certificate_number="ISO-2023-004"
        ),
        Document(
            supplier_id=suppliers[3].id,
            type="Tax Certificate",
            status="expired",
            validity_date=today - timedelta(days=15),
            certificate_number="TAX-2023-102"
        ),
    ])

    # Supplier 5 - QuickSupply Co (pending, missing documents)
    documents.extend([
        Document(
            supplier_id=suppliers[4].id,
            type="ISO 9001 Certificate",
            status="missing",
            validity_date=None,
            certificate_number=None
        ),
        Document(
            supplier_id=suppliers[4].id,
            type="Insurance Policy",
            status="missing",
            validity_date=None,
            certificate_number=None
        ),
    ])

    for document in documents:
        db.add(document)
    db.commit()

    return {
        "suppliers_created": len(suppliers),
        "documents_created": len(documents)
    }
