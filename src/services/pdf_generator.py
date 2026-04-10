"""PDF report generator service using ReportLab."""
from io import BytesIO
from typing import Optional
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents

from src.templates.pdf_template import MakyolPDFTemplate


class PDFGenerator:
    """Service for generating PDF reports with Makyol branding."""

    def __init__(self):
        """Initialize PDF generator with Makyol template."""
        self.template = MakyolPDFTemplate()

    def _add_page_number(self, canvas, doc):
        """
        Add page numbers to the footer.

        Args:
            canvas: ReportLab canvas object
            doc: Document object
        """
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.setFont('Helvetica', 8)
        canvas.drawRightString(
            doc.pagesize[0] - self.template.RIGHT_MARGIN,
            0.5 * inch,
            text
        )

    def create_document(
        self,
        report_title: str,
        preparer: Optional[str] = None,
        report_info: Optional[dict] = None
    ) -> tuple[BytesIO, SimpleDocTemplate, list]:
        """
        Create a new PDF document with Makyol branding.

        Args:
            report_title: Title of the report
            preparer: Name of the person generating the report
            report_info: Optional dictionary with report metadata

        Returns:
            Tuple of (BytesIO buffer, SimpleDocTemplate, story elements list)
        """
        # Create buffer
        buffer = BytesIO()

        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.template.PAGE_SIZE,
            leftMargin=self.template.LEFT_MARGIN,
            rightMargin=self.template.RIGHT_MARGIN,
            topMargin=self.template.TOP_MARGIN,
            bottomMargin=self.template.BOTTOM_MARGIN,
            title=report_title
        )

        # Initialize story with header
        story = []

        # Add header
        story.extend(self.template.create_header(report_title))

        # Add report info section if provided
        if report_info:
            story.extend(self.template.create_info_section(report_info))

        return buffer, doc, story

    def add_table(
        self,
        story: list,
        data: list[list],
        col_widths: Optional[list] = None,
        title: Optional[str] = None
    ) -> None:
        """
        Add a formatted table to the story.

        Args:
            story: List of story elements
            data: Table data (including header row)
            col_widths: Optional list of column widths
            title: Optional section title for the table
        """
        if title:
            section_title = Paragraph(
                f"<b>{title}</b>",
                self.template.styles['MakyolSectionHeading']
            )
            story.append(section_title)
            story.append(Spacer(1, 0.1 * inch))

        # Create table
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(self.template.get_table_style())

        story.append(table)
        story.append(Spacer(1, 0.3 * inch))

    def add_section(
        self,
        story: list,
        title: str,
        content: Optional[str] = None
    ) -> None:
        """
        Add a titled section to the story.

        Args:
            story: List of story elements
            title: Section title
            content: Optional section content text
        """
        section_title = Paragraph(
            f"<b>{title}</b>",
            self.template.styles['MakyolSectionHeading']
        )
        story.append(section_title)

        if content:
            section_content = Paragraph(
                content,
                self.template.styles['Normal']
            )
            story.append(section_content)

        story.append(Spacer(1, 0.2 * inch))

    def finalize_document(
        self,
        doc: SimpleDocTemplate,
        story: list,
        preparer: Optional[str] = None
    ) -> None:
        """
        Finalize and build the PDF document.

        Args:
            doc: SimpleDocTemplate instance
            story: List of story elements
            preparer: Name of the person generating the report
        """
        # Add footer
        footer = self.template.create_footer(preparer)
        story.append(Spacer(1, 0.5 * inch))
        story.append(footer)

        # Build PDF
        doc.build(
            story,
            onFirstPage=self._add_page_number,
            onLaterPages=self._add_page_number
        )

    def generate_basic_report(
        self,
        report_title: str,
        preparer: Optional[str] = None,
        report_info: Optional[dict] = None,
        sections: Optional[list[dict]] = None
    ) -> BytesIO:
        """
        Generate a basic PDF report with sections and tables.

        Args:
            report_title: Title of the report
            preparer: Name of the person generating the report
            report_info: Dictionary with report metadata
            sections: List of section dictionaries with 'title', 'content', and optional 'table' data

        Returns:
            BytesIO buffer containing the PDF

        Example:
            sections = [
                {
                    'title': 'Summary',
                    'content': 'This is the summary section.',
                    'table': {
                        'data': [['Header1', 'Header2'], ['Row1Col1', 'Row1Col2']],
                        'col_widths': [3*inch, 3*inch]
                    }
                }
            ]
        """
        # Create document
        buffer, doc, story = self.create_document(
            report_title=report_title,
            preparer=preparer,
            report_info=report_info
        )

        # Add sections
        if sections:
            for section in sections:
                # Add section title and content
                self.add_section(
                    story,
                    title=section.get('title', 'Section'),
                    content=section.get('content')
                )

                # Add table if present
                if 'table' in section and section['table']:
                    table_data = section['table'].get('data', [])
                    col_widths = section['table'].get('col_widths')

                    if table_data:
                        self.add_table(
                            story,
                            data=table_data,
                            col_widths=col_widths
                        )

        # Finalize document
        self.finalize_document(doc, story, preparer)

        # Reset buffer position
        buffer.seek(0)
        return buffer

    def generate_supplier_summary_pdf(
        self,
        supplier_data: list[dict],
        preparer: Optional[str] = None
    ) -> BytesIO:
        """
        Generate Supplier Summary PDF report.

        Args:
            supplier_data: List of supplier dictionaries with keys:
                - name: Supplier name
                - status: Supplier status (active, inactive, pending)
                - document_count: Total number of documents
                - expiring_soon: Number of documents expiring soon
            preparer: Name of the person generating the report

        Returns:
            BytesIO buffer containing the PDF

        Example:
            supplier_data = [
                {
                    'name': 'ABC Construction Ltd.',
                    'status': 'active',
                    'document_count': 12,
                    'expiring_soon': 2
                }
            ]
        """
        # Create report info
        report_info = {
            'Report Type': 'Supplier Compliance Summary',
            'Total Suppliers': str(len(supplier_data)),
            'Generated On': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Create document
        buffer, doc, story = self.create_document(
            report_title="Supplier Compliance Summary",
            preparer=preparer,
            report_info=report_info
        )

        # Prepare table data
        # Header row
        table_data = [
            ['Supplier Name', 'Status', 'Document Count', 'Expiring Soon']
        ]

        # Data rows
        for supplier in supplier_data:
            table_data.append([
                supplier.get('name', 'N/A'),
                supplier.get('status', 'N/A').title(),
                str(supplier.get('document_count', 0)),
                str(supplier.get('expiring_soon', 0))
            ])

        # Add table to story
        col_widths = [3.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch]
        self.add_table(
            story,
            data=table_data,
            col_widths=col_widths,
            title="Supplier Overview"
        )

        # Finalize document
        self.finalize_document(doc, story, preparer)

        # Reset buffer position
        buffer.seek(0)
        return buffer

    def generate_document_inventory_pdf(
        self,
        document_data: list[dict],
        preparer: Optional[str] = None
    ) -> BytesIO:
        """
        Generate Document Inventory PDF report.

        Args:
            document_data: List of document dictionaries with keys:
                - supplier_name: Name of the supplier
                - document_type: Type of document
                - status: Document status (valid, expiring, expired, missing)
                - validity_date: Validity date (YYYY-MM-DD format or date string)
                - certificate_number: Certificate/document number
            preparer: Name of the person generating the report

        Returns:
            BytesIO buffer containing the PDF

        Example:
            document_data = [
                {
                    'supplier_name': 'ABC Construction Ltd.',
                    'document_type': 'ISO 9001 Certification',
                    'status': 'valid',
                    'validity_date': '2025-06-30',
                    'certificate_number': 'ISO-9001-2024-001'
                }
            ]
        """
        # Create report info
        report_info = {
            'Report Type': 'Document Inventory',
            'Total Documents': str(len(document_data)),
            'Generated On': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Create document
        buffer, doc, story = self.create_document(
            report_title="Document Inventory Report",
            preparer=preparer,
            report_info=report_info
        )

        # Prepare table data
        # Header row
        table_data = [
            ['Supplier', 'Document Type', 'Status', 'Validity Date', 'Certificate #']
        ]

        # Data rows
        for document in document_data:
            table_data.append([
                document.get('supplier_name', 'N/A'),
                document.get('document_type', 'N/A'),
                document.get('status', 'N/A').title(),
                document.get('validity_date', 'N/A'),
                document.get('certificate_number', 'N/A')
            ])

        # Add table to story
        col_widths = [1.8 * inch, 2.0 * inch, 1.0 * inch, 1.3 * inch, 1.9 * inch]
        self.add_table(
            story,
            data=table_data,
            col_widths=col_widths,
            title="Document Details"
        )

        # Finalize document
        self.finalize_document(doc, story, preparer)

        # Reset buffer position
        buffer.seek(0)
        return buffer

    def generate_expiring_certificates_pdf(
        self,
        certificate_data: list[dict],
        preparer: Optional[str] = None
    ) -> BytesIO:
        """
        Generate Expiring Certificates PDF report.

        Args:
            certificate_data: List of certificate dictionaries with keys:
                - supplier_name: Name of the supplier
                - document_type: Type of document/certificate
                - validity_date: Validity/expiry date (YYYY-MM-DD format or date string)
                - days_until_expiry: Number of days until expiration
                - certificate_number: Certificate/document number
            preparer: Name of the person generating the report

        Returns:
            BytesIO buffer containing the PDF

        Example:
            certificate_data = [
                {
                    'supplier_name': 'ABC Construction Ltd.',
                    'document_type': 'Tax Clearance',
                    'validity_date': '2026-05-15',
                    'days_until_expiry': 35,
                    'certificate_number': 'TAX-2024-456'
                }
            ]
        """
        # Create report info
        report_info = {
            'Report Type': 'Expiring Certificates',
            'Total Expiring': str(len(certificate_data)),
            'Generated On': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Create document
        buffer, doc, story = self.create_document(
            report_title="Expiring Certificates Report",
            preparer=preparer,
            report_info=report_info
        )

        # Prepare table data
        # Header row
        table_data = [
            ['Supplier', 'Document Type', 'Validity Date', 'Days Until Expiry', 'Certificate #']
        ]

        # Data rows
        for certificate in certificate_data:
            table_data.append([
                certificate.get('supplier_name', 'N/A'),
                certificate.get('document_type', 'N/A'),
                certificate.get('validity_date', 'N/A'),
                str(certificate.get('days_until_expiry', 'N/A')),
                certificate.get('certificate_number', 'N/A')
            ])

        # Add table to story
        col_widths = [1.8 * inch, 2.0 * inch, 1.2 * inch, 1.3 * inch, 1.7 * inch]
        self.add_table(
            story,
            data=table_data,
            col_widths=col_widths,
            title="Certificates Expiring Soon"
        )

        # Finalize document
        self.finalize_document(doc, story, preparer)

        # Reset buffer position
        buffer.seek(0)
        return buffer

    def generate_missing_documents_pdf(
        self,
        missing_data: list[dict],
        preparer: Optional[str] = None
    ) -> BytesIO:
        """
        Generate Missing Documents PDF report.

        Args:
            missing_data: List of missing document dictionaries with keys:
                - supplier_name: Name of the supplier
                - document_type: Type of document that is missing
                - required: When the document is required (e.g., 'Always Required', date)
                - status: Status of the document (typically 'Missing')
            preparer: Name of the person generating the report

        Returns:
            BytesIO buffer containing the PDF

        Example:
            missing_data = [
                {
                    'supplier_name': 'ABC Construction Ltd.',
                    'document_type': 'Environmental Compliance Certificate',
                    'required': 'Always Required',
                    'status': 'Missing'
                }
            ]
        """
        # Create report info
        report_info = {
            'Report Type': 'Missing Documents',
            'Total Missing': str(len(missing_data)),
            'Generated On': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Create document
        buffer, doc, story = self.create_document(
            report_title="Missing Documents Report",
            preparer=preparer,
            report_info=report_info
        )

        # Prepare table data
        # Header row
        table_data = [
            ['Supplier', 'Document Type', 'Required', 'Status']
        ]

        # Data rows
        for missing in missing_data:
            table_data.append([
                missing.get('supplier_name', 'N/A'),
                missing.get('document_type', 'N/A'),
                missing.get('required', 'N/A'),
                missing.get('status', 'Missing')
            ])

        # Add table to story
        col_widths = [2.5 * inch, 2.5 * inch, 1.5 * inch, 1.5 * inch]
        self.add_table(
            story,
            data=table_data,
            col_widths=col_widths,
            title="Document Compliance Gaps"
        )

        # Finalize document
        self.finalize_document(doc, story, preparer)

        # Reset buffer position
        buffer.seek(0)
        return buffer

    def generate_full_audit_pdf(
        self,
        supplier_data: list[dict],
        document_data: list[dict],
        certificate_data: list[dict],
        missing_data: list[dict],
        preparer: Optional[str] = None
    ) -> BytesIO:
        """
        Generate Full Audit PDF report combining all compliance data.

        This comprehensive report includes an executive summary and detailed sections
        for supplier compliance, document inventory, expiring certificates, and
        missing documents. Suitable for regulatory submission and audit preparation.

        Args:
            supplier_data: List of supplier dictionaries with keys:
                - name: Supplier name
                - status: Supplier status (active, inactive, pending)
                - document_count: Total number of documents
                - expiring_soon: Number of documents expiring soon
            document_data: List of document dictionaries with keys:
                - supplier_name: Name of the supplier
                - document_type: Type of document
                - status: Document status (valid, expiring, expired, missing)
                - validity_date: Validity date (YYYY-MM-DD format or date string)
                - certificate_number: Certificate/document number
            certificate_data: List of certificate dictionaries with keys:
                - supplier_name: Name of the supplier
                - document_type: Type of document/certificate
                - validity_date: Validity/expiry date (YYYY-MM-DD format or date string)
                - days_until_expiry: Number of days until expiration
                - certificate_number: Certificate/document number
            missing_data: List of missing document dictionaries with keys:
                - supplier_name: Name of the supplier
                - document_type: Type of document that is missing
                - required: When the document is required (e.g., 'Always Required', date)
                - status: Status of the document (typically 'Missing')
            preparer: Name of the person generating the report

        Returns:
            BytesIO buffer containing the PDF

        Example:
            pdf = generator.generate_full_audit_pdf(
                supplier_data=[{...}],
                document_data=[{...}],
                certificate_data=[{...}],
                missing_data=[{...}],
                preparer="Compliance Engineer"
            )
        """
        # Calculate summary statistics
        total_suppliers = len(supplier_data)
        total_documents = len(document_data)
        total_expiring = len(certificate_data)
        total_missing = len(missing_data)

        # Calculate active suppliers
        active_suppliers = sum(1 for s in supplier_data if s.get('status', '').lower() == 'active')

        # Create report info
        report_info = {
            'Report Type': 'Full Compliance Audit',
            'Total Suppliers': str(total_suppliers),
            'Active Suppliers': str(active_suppliers),
            'Total Documents': str(total_documents),
            'Documents Expiring Soon': str(total_expiring),
            'Missing Documents': str(total_missing),
            'Generated On': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Create document
        buffer, doc, story = self.create_document(
            report_title="Full Compliance Audit Report",
            preparer=preparer,
            report_info=report_info
        )

        # Executive Summary Section
        self.add_section(
            story,
            title="Executive Summary",
            content=(
                f"This comprehensive audit report covers {total_suppliers} suppliers with "
                f"{total_documents} total documents tracked. {total_expiring} certificates are "
                f"expiring soon and require renewal action. {total_missing} required documents "
                f"are currently missing and need immediate attention. This report is suitable "
                f"for regulatory submission and compliance verification."
            )
        )

        # Add page break before first major section
        story.append(PageBreak())

        # Section 1: Supplier Compliance Summary
        self.add_section(
            story,
            title="1. Supplier Compliance Summary"
        )

        # Prepare supplier summary table
        supplier_table_data = [
            ['Supplier Name', 'Status', 'Document Count', 'Expiring Soon']
        ]
        for supplier in supplier_data:
            supplier_table_data.append([
                supplier.get('name', 'N/A'),
                supplier.get('status', 'N/A').title(),
                str(supplier.get('document_count', 0)),
                str(supplier.get('expiring_soon', 0))
            ])

        col_widths = [3.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch]
        self.add_table(
            story,
            data=supplier_table_data,
            col_widths=col_widths,
            title="Supplier Overview"
        )

        # Add page break before next section
        story.append(PageBreak())

        # Section 2: Document Inventory
        self.add_section(
            story,
            title="2. Document Inventory"
        )

        # Prepare document inventory table
        document_table_data = [
            ['Supplier', 'Document Type', 'Status', 'Validity Date', 'Certificate #']
        ]
        for document in document_data:
            document_table_data.append([
                document.get('supplier_name', 'N/A'),
                document.get('document_type', 'N/A'),
                document.get('status', 'N/A').title(),
                document.get('validity_date', 'N/A'),
                document.get('certificate_number', 'N/A')
            ])

        col_widths = [1.8 * inch, 2.0 * inch, 1.0 * inch, 1.3 * inch, 1.9 * inch]
        self.add_table(
            story,
            data=document_table_data,
            col_widths=col_widths,
            title="Complete Document Listing"
        )

        # Add page break before next section
        story.append(PageBreak())

        # Section 3: Expiring Certificates
        self.add_section(
            story,
            title="3. Expiring Certificates"
        )

        # Prepare expiring certificates table
        certificate_table_data = [
            ['Supplier', 'Document Type', 'Validity Date', 'Days Until Expiry', 'Certificate #']
        ]
        for certificate in certificate_data:
            certificate_table_data.append([
                certificate.get('supplier_name', 'N/A'),
                certificate.get('document_type', 'N/A'),
                certificate.get('validity_date', 'N/A'),
                str(certificate.get('days_until_expiry', 'N/A')),
                certificate.get('certificate_number', 'N/A')
            ])

        col_widths = [1.8 * inch, 2.0 * inch, 1.2 * inch, 1.3 * inch, 1.7 * inch]
        self.add_table(
            story,
            data=certificate_table_data,
            col_widths=col_widths,
            title="Action Required: Renewals Needed"
        )

        # Add page break before final section
        story.append(PageBreak())

        # Section 4: Missing Documents
        self.add_section(
            story,
            title="4. Missing Documents"
        )

        # Prepare missing documents table
        missing_table_data = [
            ['Supplier', 'Document Type', 'Required', 'Status']
        ]
        for missing in missing_data:
            missing_table_data.append([
                missing.get('supplier_name', 'N/A'),
                missing.get('document_type', 'N/A'),
                missing.get('required', 'N/A'),
                missing.get('status', 'Missing')
            ])

        col_widths = [2.5 * inch, 2.5 * inch, 1.5 * inch, 1.5 * inch]
        self.add_table(
            story,
            data=missing_table_data,
            col_widths=col_widths,
            title="Compliance Gaps Requiring Immediate Action"
        )

        # Finalize document
        self.finalize_document(doc, story, preparer)

        # Reset buffer position
        buffer.seek(0)
        return buffer
