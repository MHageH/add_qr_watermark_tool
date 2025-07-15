import hashlib
import os
import sys
import math
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from pdfrw import PdfReader, PdfWriter, PageMerge

def get_pdf_page_size(pdf_path):
    """Get the page size (width, height) of the PDF"""
    pdf = PdfReader(pdf_path)
    page = pdf.pages[0]
    media_box = page.MediaBox
    if media_box is None:
        media_box = page.CropBox
    if media_box is None:
        return 595, 842  # Default A4 size in points
    llx = float(media_box[0])
    lly = float(media_box[1])
    urx = float(media_box[2])
    ury = float(media_box[3])
    width = urx - llx
    height = ury - lly
    return width, height

def get_pdf_hash(pdf_path):
    """Generate SHA-256 hash of the PDF content"""
    with open(pdf_path, 'rb') as f:
        content = f.read()
    return hashlib.sha256(content).hexdigest()

def generate_repeated_text_watermark(output_path, page_width, page_height, text="text to add", opacity=0.3, angle=45, font_size=20, horizontal_spacing=80, vertical_spacing=80):
    """Generate repeated diagonal watermark on the PDF"""
    c = canvas.Canvas(output_path, pagesize=(page_width, page_height))

    c.setFont("Helvetica-Bold", font_size)
    c.setFillColor(colors.black)
    
    c.setFillAlpha(opacity)

    text_width = c.stringWidth(text, "Helvetica-Bold", font_size)
    text_height = font_size  

    y = 0
    while y < page_height:
        x = 0
        while x < page_width:
            c.saveState()
            c.translate(x, y)
            c.rotate(angle)  
            c.drawString(0, 0, text)  
            c.restoreState()

            x += horizontal_spacing

        y += vertical_spacing

    c.showPage()
    c.save()

def generate_qr_pdf(qr_content, output_path, page_width, page_height, scale=0.6):
    """Generate QR code and save it to a PDF"""
    c = canvas.Canvas(output_path, pagesize=(page_width, page_height))

    qr_code = qr.QrCodeWidget(qr_content)
    bounds = qr_code.getBounds()
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]

    drawing = Drawing(qr_width, qr_height)
    drawing.add(qr_code)

    scaled_qr_width = qr_width * scale
    scaled_qr_height = qr_height * scale

    x = max(0, page_width - scaled_qr_width)
    y = max(0, page_height - scaled_qr_height)

    c.saveState()
    c.translate(x, y)
    c.scale(scale, scale)
    renderPDF.draw(drawing, c, 0, 0)
    c.restoreState()

    c.showPage()
    c.save()

def add_watermark_to_pdf(input_pdf, watermark_pdf, output_pdf):
    """Add watermark to each page of the input PDF"""
    input_reader = PdfReader(input_pdf)
    watermark_reader = PdfReader(watermark_pdf)
    watermark_page = watermark_reader.pages[0]

    for page in input_reader.pages:
        PageMerge(page).add(watermark_page, prepend=False).render()

    PdfWriter(output_pdf, trailer=input_reader).write()

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py input.pdf output_dir")
        return

    input_path = os.path.abspath(sys.argv[1])
    output_dir = os.path.abspath(sys.argv[2])

    if not os.path.isfile(input_path):
        print(f"[✘] File not found: {input_path}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[~] Created output directory: {output_dir}")

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    ext = os.path.splitext(input_path)[1]

    watermark_pdf = os.path.join(output_dir, f"{base_name}_watermark.pdf")
    qr_pdf = os.path.join(output_dir, f"{base_name}_qr.pdf")
    output_pdf = os.path.join(output_dir, f"{base_name}_with_qr_and_watermark{ext}")

    page_width, page_height = get_pdf_page_size(input_path)

    pdf_hash = get_pdf_hash(input_path)
    validity_text=f"Document hash: {pdf_hash}"
    qr_content = f"PDF Hash: {pdf_hash}\n{validity_text}"

    print("[~] Generating repeated text watermark PDF...")
    generate_repeated_text_watermark(watermark_pdf, page_width, page_height, 
                                     validity_text, opacity=0.3, angle=45, font_size=9, horizontal_spacing=300, vertical_spacing=150)

    print("[~] Generating QR code PDF...")
    generate_qr_pdf(qr_content, qr_pdf, page_width, page_height)

    print("[~] Adding watermark and QR to PDF...")
    add_watermark_to_pdf(input_path, watermark_pdf, output_pdf)
    add_watermark_to_pdf(output_pdf, qr_pdf, output_pdf)

    if os.path.exists(watermark_pdf):
        os.remove(watermark_pdf)
    if os.path.exists(qr_pdf):
        os.remove(qr_pdf)

    if os.path.exists(output_pdf):
        print(f"[✔] Output saved at: {output_pdf}")
    else:
        print("[✘] Failed to create output PDF.")

if __name__ == "__main__":
    main()
