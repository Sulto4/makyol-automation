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
