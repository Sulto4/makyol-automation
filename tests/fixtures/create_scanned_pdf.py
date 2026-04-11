"""
Utility script to create a sample scanned PDF for testing OCR functionality.

This script creates a PDF that simulates a scanned certificate document
by rendering text as an image (no text layer), which will require OCR processing.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_scanned_certificate_pdf():
    """
    Create a sample scanned certificate PDF for OCR testing.

    The PDF contains certificate text rendered as an image to simulate
    a scanned document without a text layer.
    """
    # Certificate text content
    certificate_text = """
    CERTIFICATE OF COMPLIANCE

    This is to certify that:

    Acme Manufacturing Ltd.
    123 Industrial Drive
    Manufacturing City, MC 12345

    Has been audited and found to be in conformance with the
    requirements of ISO 9001:2015 Quality Management System

    Certificate Number: ISO-9001-2024-001
    Issue Date: January 15, 2024
    Expiry Date: January 14, 2027

    Certification Body:
    Global Standards Institute
    """

    # Create an image with white background
    width, height = 1700, 2200  # Approximately A4 size at 200 DPI
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    # Use default font (PIL's built-in font)
    # For better results in production, use: ImageFont.truetype("path/to/font.ttf", size)
    try:
        # Try to use a TrueType font if available
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Draw the certificate text
    y_position = 150
    for line in certificate_text.strip().split('\n'):
        line = line.strip()
        if line:
            # Center the text horizontally
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_position = (width - text_width) // 2

            draw.text((x_position, y_position), line, fill='black', font=font)
            y_position += 70

    # Add a border to make it look more like a certificate
    draw.rectangle([(50, 50), (width-50, height-50)], outline='black', width=5)
    draw.rectangle([(70, 70), (width-70, height-70)], outline='black', width=2)

    # Save as PDF using PIL
    output_path = os.path.join(os.path.dirname(__file__), 'scanned_certificate.pdf')
    image.save(output_path, 'PDF', resolution=200.0)

    print(f"Created scanned certificate PDF at: {output_path}")
    return output_path

if __name__ == '__main__':
    create_scanned_certificate_pdf()
