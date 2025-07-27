import streamlit as st
from PyPDF2 import PdfMerger, PdfReader
from io import BytesIO
import tempfile

def render(st, config):
    st.header("PDF Tools")
    tab1, tab2 = st.tabs(["Merge PDFs", "Split PDF"])

    with tab1:
        st.subheader("Merge Multiple PDFs")
        pdf_files = st.file_uploader("Upload PDF files to merge", type="pdf", accept_multiple_files=True)
        if st.button("Merge PDFs") and pdf_files:
            merger = PdfMerger()
            for pdf in pdf_files:
                merger.append(BytesIO(pdf.read()))
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
