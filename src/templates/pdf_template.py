"""PDF template configuration for Makyol branding."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from datetime import datetime


class MakyolPDFTemplate:
    """Template configuration for Makyol-branded PDF reports."""

    # Page settings
    PAGE_SIZE = A4
    PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE

    # Margins
    LEFT_MARGIN = 0.75 * inch
    RIGHT_MARGIN = 0.75 * inch
    TOP_MARGIN = 1.0 * inch
    BOTTOM_MARGIN = 1.0 * inch

    # Brand colors
    MAKYOL_PRIMARY = colors.HexColor("#1B4F72")  # Dark blue
    MAKYOL_SECONDARY = colors.HexColor("#2E86C1")  # Light blue
    MAKYOL_ACCENT = colors.HexColor("#5DADE2")  # Accent blue
    HEADER_BG = colors.HexColor("#F8F9F9")  # Light grey for table headers

    def __init__(self):
        """Initialize template styles."""
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create custom paragraph styles for Makyol branding."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='MakyolTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.MAKYOL_PRIMARY,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='MakyolSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.MAKYOL_SECONDARY,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))

        # Header style
        self.styles.add(ParagraphStyle(
            name='MakyolHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))

        # Footer style
        self.styles.add(ParagraphStyle(
            name='MakyolFooter',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))

        # Section heading style
        self.styles.add(ParagraphStyle(
            name='MakyolSectionHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=self.MAKYOL_PRIMARY,
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

    def create_header(self, report_title: str) -> list:
        """
        Create report header with Makyol branding.

        Args:
            report_title: Title of the report

        Returns:
            List of reportlab flowables for the header
        """
        elements = []

        # Company name (placeholder for logo)
        company_name = Paragraph(
            "<b>MAKYOL</b>",
            self.styles['MakyolTitle']
        )
        elements.append(company_name)

        # Subtitle
        subtitle = Paragraph(
            "Compliance Management System",
            self.styles['MakyolSubtitle']
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 0.2 * inch))

        # Report title
        title = Paragraph(
            f"<b>{report_title}</b>",
            self.styles['MakyolSectionHeading']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.1 * inch))

        # Horizontal line
        line_table = Table(
            [['']],
            colWidths=[self.PAGE_WIDTH - self.LEFT_MARGIN - self.RIGHT_MARGIN]
        )
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 2, self.MAKYOL_PRIMARY),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 0.2 * inch))

        return elements

    def create_footer(self, preparer: str = None) -> Paragraph:
        """
        Create report footer with generation info.

        Args:
            preparer: Name of the person who generated the report

        Returns:
            Paragraph flowable for the footer
        """
        generation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        footer_text = f"Generated on {generation_date}"
        if preparer:
            footer_text += f" | Prepared by: {preparer}"
        footer_text += " | Makyol Compliance Management System"

        return Paragraph(footer_text, self.styles['MakyolFooter'])

    def create_info_section(self, info_data: dict) -> list:
        """
        Create an information section with key-value pairs.

        Args:
            info_data: Dictionary of key-value pairs to display

        Returns:
            List of reportlab flowables
        """
        elements = []

        data = [[key + ":", str(value)] for key, value in info_data.items()]

        info_table = Table(data, colWidths=[2 * inch, 4 * inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), self.MAKYOL_SECONDARY),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def get_table_style(self) -> TableStyle:
        """
        Get standard table style for report tables.

        Returns:
            TableStyle for data tables
        """
        return TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), self.HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.MAKYOL_PRIMARY),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Data rows styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),

            # All cells
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 2, self.MAKYOL_PRIMARY),

            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9F9")]),
        ])
