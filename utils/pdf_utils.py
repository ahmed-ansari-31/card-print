from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from PIL import Image

def save_image_as_pdf(page_img, page_width_inch, page_height_inch):
    buffer = BytesIO()
    page_width = page_width_inch * inch
    page_height = page_height_inch * inch
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    c.drawInlineImage(page_img, 0, 0, width=page_width, height=page_height)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer 