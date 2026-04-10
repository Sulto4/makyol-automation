"""FastAPI router for sample data generation endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.sample_data import generate_sample_data

router = APIRouter(
    prefix="/api/sample-data",
    tags=["sample-data"]
)


@router.post("/generate")
async def generate_sample_data_endpoint(db: Session = Depends(get_db)):
    """
    Generate sample suppliers and documents for testing purposes.

    This endpoint clears all existing data and creates a fresh set of
    sample suppliers with various document statuses for testing reports.

    Args:
        db: Database session

    Returns:
        Dictionary with counts of created suppliers and documents
    """
    try:
        result = generate_sample_data(db)
        return {
            "message": "Sample data generated successfully",
            "suppliers_created": result["suppliers_created"],
            "documents_created": result["documents_created"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating sample data: {str(e)}"
        )
