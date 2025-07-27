import streamlit as st
from PyPDF2 import PdfMerger, PdfReader, PdfWriter, Transformation
from io import BytesIO
import tempfile
from reportlab.lib.pagesizes import A4

# Helper to resize a PDF page to A4 using PyPDF2 transformations
def resize_pdf_to_a4(input_pdf_bytes):
    output = BytesIO()
    reader = PdfReader(BytesIO(input_pdf_bytes))
    writer = PdfWriter()
    a4_width, a4_height = A4  # points
    for page in reader.pages:
        orig_width = float(page.mediabox.width)
        orig_height = float(page.mediabox.height)
        scale_x = a4_width / orig_width
        scale_y = a4_height / orig_height
        scale = min(scale_x, scale_y)
        tx = (a4_width - orig_width * scale) / 2
        ty = (a4_height - orig_height * scale) / 2
        # Create a blank A4 page
        new_page = writer.add_blank_page(width=a4_width, height=a4_height)
        # Transform the original page to fit A4
        page.add_transformation(Transformation().scale(scale, scale).translate(tx, ty))
        new_page.merge_page(page)
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
