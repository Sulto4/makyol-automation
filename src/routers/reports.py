"""FastAPI router for report generation endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date, timedelta

from src.database import get_db
from src.schemas.report_request import ReportRequest
from src.services.pdf_generator import PDFGenerator
from src.services.excel_generator import ExcelGenerator
from src.models.supplier import Supplier
from src.models.document import Document

router = APIRouter(
    prefix="/api/reports",
    tags=["reports"]
)


def apply_filters(
    query,
    supplier_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status: Optional[str] = None
):
    """
    Apply common filters to a query.

    Args:
        query: SQLAlchemy query object
        supplier_id: Filter by supplier ID
        date_from: Filter documents from this date
        date_to: Filter documents up to this date
        status: Filter by document status

    Returns:
        Filtered query object
    """
    if supplier_id is not None:
        query = query.filter(Document.supplier_id == supplier_id)
    if date_from is not None:
        query = query.filter(Document.validity_date >= date_from)
    if date_to is not None:
        query = query.filter(Document.validity_date <= date_to)
    if status is not None:
        query = query.filter(Document.status == status)
    return query


def get_suppliers_data(db: Session, supplier_id: Optional[int] = None):
    """Get suppliers with their documents."""
    query = db.query(Supplier)
    if supplier_id is not None:
        query = query.filter(Supplier.id == supplier_id)
    return query.all()


def get_documents_data(
    db: Session,
    supplier_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status: Optional[str] = None
):
    """Get documents with filters applied."""
    query = db.query(Document)
    query = apply_filters(query, supplier_id, date_from, date_to, status)
    return query.all()


def get_expiring_documents(
    db: Session,
    days_threshold: int = 30,
    supplier_id: Optional[int] = None
):
    """Get documents expiring within specified days."""
    threshold_date = date.today() + timedelta(days=days_threshold)
    query = db.query(Document).filter(
        Document.validity_date.isnot(None),
        Document.validity_date <= threshold_date,
        Document.validity_date >= date.today(),
        Document.status != "expired"
    )
    if supplier_id is not None:
        query = query.filter(Document.supplier_id == supplier_id)
    return query.all()


def get_missing_documents(db: Session, supplier_id: Optional[int] = None):
    """Get missing or expired documents."""
    query = db.query(Document).filter(
        (Document.status == "missing") | (Document.status == "expired")
    )
    if supplier_id is not None:
        query = query.filter(Document.supplier_id == supplier_id)
    return query.all()


@router.post("/")
@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a compliance report based on the request parameters.

    Args:
        request: Report request with type, format, and filters
        db: Database session

    Returns:
        StreamingResponse with the generated report file
    """
    try:
        # Fetch data based on report type
        if request.report_type == "supplier_summary":
            suppliers = get_suppliers_data(db, request.supplier_id)
            data = {"suppliers": suppliers}
        elif request.report_type == "document_inventory":
            documents = get_documents_data(
                db,
                request.supplier_id,
                request.date_from,
                request.date_to,
                request.status
            )
            data = {"documents": documents}
        elif request.report_type == "expiring_certificates":
            documents = get_expiring_documents(
                db,
                request.days_threshold,
                request.supplier_id
            )
            data = {"documents": documents}
        elif request.report_type == "missing_documents":
            documents = get_missing_documents(db, request.supplier_id)
            data = {"documents": documents}
        elif request.report_type == "full_audit":
            suppliers = get_suppliers_data(db, request.supplier_id)
            documents = get_documents_data(db, request.supplier_id, request.date_from, request.date_to, request.status)
            expiring = get_expiring_documents(db, request.days_threshold, request.supplier_id)
            missing = get_missing_documents(db, request.supplier_id)
            data = {
                "suppliers": suppliers,
                "documents": documents,
                "expiring": expiring,
                "missing": missing
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid report type: {request.report_type}"
            )

        # Generate report based on format
        if request.format == "pdf":
            buffer = generate_pdf_report(request.report_type, data, request.preparer, request.days_threshold)
            media_type = "application/pdf"
            file_extension = "pdf"
        elif request.format == "excel":
            buffer = generate_excel_report(request.report_type, data, request.preparer, request.days_threshold)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            file_extension = "xlsx"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format: {request.format}"
            )

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{request.report_type}_{timestamp}.{file_extension}"

        # Return streaming response
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )


def transform_suppliers_to_dict(suppliers: list) -> list:
    """Transform supplier models to dictionaries for report generation."""
    result = []
    for supplier in suppliers:
        # Count documents and expiring soon
        doc_count = len(supplier.documents)
        expiring_soon = sum(
            1 for doc in supplier.documents
            if doc.validity_date and
            date.today() <= doc.validity_date <= (date.today() + timedelta(days=30)) and
            doc.status != "expired"
        )

        result.append({
            'name': supplier.name,
            'status': supplier.status,
            'document_count': doc_count,
            'expiring_soon': expiring_soon
        })
    return result


def transform_documents_to_dict(documents: list) -> list:
    """Transform document models to dictionaries for report generation."""
    return [
        {
            'supplier_name': doc.supplier.name,
            'document_type': doc.type,
            'status': doc.status,
            'validity_date': doc.validity_date.isoformat() if doc.validity_date else 'N/A',
            'certificate_number': doc.certificate_number or 'N/A'
        }
        for doc in documents
    ]


def transform_expiring_documents_to_dict(documents: list) -> list:
    """Transform expiring document models to dictionaries for report generation."""
    result = []
    today = date.today()
    for doc in documents:
        if doc.validity_date:
            days_until_expiry = (doc.validity_date - today).days
            result.append({
                'supplier_name': doc.supplier.name,
                'document_type': doc.type,
                'validity_date': doc.validity_date.isoformat(),
                'days_until_expiry': days_until_expiry,
                'certificate_number': doc.certificate_number or 'N/A'
            })
    return result


def transform_missing_documents_to_dict(documents: list) -> list:
    """Transform missing/expired document models to dictionaries for report generation."""
    return [
        {
            'supplier_name': doc.supplier.name,
            'document_type': doc.type,
            'required': 'Always Required',
            'status': doc.status.title()
        }
        for doc in documents
    ]


def generate_pdf_report(report_type: str, data: dict, preparer: str, days_threshold: int = 30):
    """Generate PDF report based on type."""
    pdf_gen = PDFGenerator()

    if report_type == "supplier_summary":
        transformed_data = transform_suppliers_to_dict(data["suppliers"])
        return pdf_gen.generate_supplier_summary_pdf(transformed_data, preparer)
    elif report_type == "document_inventory":
        transformed_data = transform_documents_to_dict(data["documents"])
        return pdf_gen.generate_document_inventory_pdf(transformed_data, preparer)
    elif report_type == "expiring_certificates":
        transformed_data = transform_expiring_documents_to_dict(data["documents"])
        return pdf_gen.generate_expiring_certificates_pdf(transformed_data, preparer)
    elif report_type == "missing_documents":
        transformed_data = transform_missing_documents_to_dict(data["documents"])
        return pdf_gen.generate_missing_documents_pdf(transformed_data, preparer)
    elif report_type == "full_audit":
        supplier_data = transform_suppliers_to_dict(data["suppliers"])
        document_data = transform_documents_to_dict(data["documents"])
        expiring_data = transform_expiring_documents_to_dict(data["expiring"])
        missing_data = transform_missing_documents_to_dict(data["missing"])
        return pdf_gen.generate_full_audit_pdf(
            supplier_data, document_data, expiring_data, missing_data, preparer
        )
    else:
        raise ValueError(f"Unknown report type: {report_type}")


def generate_excel_report(report_type: str, data: dict, preparer: str, days_threshold: int = 30):
    """Generate Excel report based on type."""
    excel_gen = ExcelGenerator()

    if report_type == "supplier_summary":
        transformed_data = transform_suppliers_to_dict(data["suppliers"])
        return excel_gen.generate_supplier_summary_excel(transformed_data, preparer)
    elif report_type == "document_inventory":
        transformed_data = transform_documents_to_dict(data["documents"])
        return excel_gen.generate_document_inventory_excel(transformed_data, preparer)
    elif report_type == "expiring_certificates":
        transformed_data = transform_expiring_documents_to_dict(data["documents"])
        return excel_gen.generate_expiring_certificates_excel(transformed_data, preparer)
    elif report_type == "missing_documents":
        transformed_data = transform_missing_documents_to_dict(data["documents"])
        return excel_gen.generate_missing_documents_excel(transformed_data, preparer)
    elif report_type == "full_audit":
        supplier_data = transform_suppliers_to_dict(data["suppliers"])
        document_data = transform_documents_to_dict(data["documents"])
        expiring_data = transform_expiring_documents_to_dict(data["expiring"])
        missing_data = transform_missing_documents_to_dict(data["missing"])
        return excel_gen.generate_full_audit_excel(
            supplier_data, document_data, expiring_data, missing_data, preparer
        )
    else:
        raise ValueError(f"Unknown report type: {report_type}")
