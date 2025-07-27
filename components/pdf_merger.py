import streamlit as st
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from io import BytesIO
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2.generic import RectangleObject

# Helper to resize a PDF page to A4 using reportlab
def resize_pdf_to_a4(input_pdf_bytes):
    output = BytesIO()
    reader = PdfReader(BytesIO(input_pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        # Draw the original PDF page as an image (not perfect, but works for most cases)
        # This is a placeholder: ideally, use pdf2image or similar for perfect fidelity
        can.save()
        packet.seek(0)
        new_pdf = PdfReader(packet)
        new_page = new_pdf.pages[0]
        # Overlay the original content
        new_page.merge_page(page)
        writer.add_page(new_page)
    writer.write(output)
    output.seek(0)
    return output

def render(st, config):
    st.header("PDF Tools")
    tab1, tab2 = st.tabs(["Merge PDFs", "Split PDF"])

    with tab1:
        st.subheader("Merge Multiple PDFs")
        pdf_files = st.file_uploader("Upload PDF files to merge", type="pdf", accept_multiple_files=True)
        page_size = st.selectbox("Select output page size", ["A4 (8.27 x 11.69 in)", "Original"], index=0)
        if st.button("Merge PDFs") and pdf_files:
            merger = PdfMerger()
            for pdf in pdf_files:
                pdf_bytes = pdf.read()
                if page_size.startswith("A4"):
                    # Resize each PDF to A4
                    pdf_bytes = resize_pdf_to_a4(pdf_bytes).getvalue()
                merger.append(BytesIO(pdf_bytes))
            merged_pdf = BytesIO()
            merger.write(merged_pdf)
            merger.close()
            merged_pdf.seek(0)
            st.success("PDFs merged successfully!")
            st.download_button("Download Merged PDF", data=merged_pdf, file_name="merged.pdf", mime="application/pdf")

    with tab2:
        st.subheader("Split PDF into Pages")
        pdf_file = st.file_uploader("Upload a PDF to split", type="pdf", key="split_pdf")
        if st.button("Split PDF") and pdf_file:
            reader = PdfReader(BytesIO(pdf_file.read()))
            for i, page in enumerate(reader.pages):
                writer = PdfMerger()
                temp_pdf = BytesIO()
                # Use PdfMerger to write a single page
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_writer = PdfMerger()
                    temp_writer.append(BytesIO(pdf_file.getvalue()), pages=(i, i+1))
                    temp_writer.write(temp_file)
                    temp_writer.close()
                    temp_file.seek(0)
                    temp_pdf.write(temp_file.read())
                temp_pdf.seek(0)
                st.download_button(f"Download Page {i+1}", data=temp_pdf, file_name=f"page_{i+1}.pdf", mime="application/pdf")
