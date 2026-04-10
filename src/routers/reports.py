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
            data = suppliers
        elif request.report_type == "document_inventory":
            documents = get_documents_data(
                db,
                request.supplier_id,
                request.date_from,
                request.date_to,
                request.status
            )
            data = documents
        elif request.report_type == "expiring_certificates":
            documents = get_expiring_documents(
                db,
                request.days_threshold,
                request.supplier_id
            )
            data = documents
        elif request.report_type == "missing_documents":
            documents = get_missing_documents(db, request.supplier_id)
            data = documents
        elif request.report_type == "full_audit":
            suppliers = get_suppliers_data(db, request.supplier_id)
            data = suppliers
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


def generate_pdf_report(report_type: str, data, preparer: str, days_threshold: int = 30):
    """Generate PDF report based on type."""
    pdf_gen = PDFGenerator()

    if report_type == "supplier_summary":
        return pdf_gen.generate_supplier_summary_pdf(data, preparer)
    elif report_type == "document_inventory":
        return pdf_gen.generate_document_inventory_pdf(data, preparer)
    elif report_type == "expiring_certificates":
        return pdf_gen.generate_expiring_certificates_pdf(data, preparer, days_threshold)
    elif report_type == "missing_documents":
        return pdf_gen.generate_missing_documents_pdf(data, preparer)
    elif report_type == "full_audit":
        return pdf_gen.generate_full_audit_pdf(data, preparer)
    else:
        raise ValueError(f"Unknown report type: {report_type}")


def generate_excel_report(report_type: str, data, preparer: str, days_threshold: int = 30):
    """Generate Excel report based on type."""
    excel_gen = ExcelGenerator()

    if report_type == "supplier_summary":
        return excel_gen.generate_supplier_summary_excel(data, preparer)
    elif report_type == "document_inventory":
        return excel_gen.generate_document_inventory_excel(data, preparer)
    elif report_type == "expiring_certificates":
        return excel_gen.generate_expiring_certificates_excel(data, preparer, days_threshold)
    elif report_type == "missing_documents":
        return excel_gen.generate_missing_documents_excel(data, preparer)
    elif report_type == "full_audit":
        return excel_gen.generate_full_audit_excel(data, preparer)
    else:
        raise ValueError(f"Unknown report type: {report_type}")
