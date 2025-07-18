import streamlit as st
from PIL import Image
from io import BytesIO
from utils.image_utils import enhance_image, crop_image_relative, make_canvas_with_image
from utils.pdf_utils import save_image_as_pdf
from utils.word_utils import save_image_as_word

@st.cache_data
def load_and_resize_image(file_bytes, max_width=1000):
    img = Image.open(BytesIO(file_bytes)).convert("RGB")
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)))
    return img

@st.cache_data
def cached_enhance_image(img_bytes, brightness, contrast, sharpness, grayscale):
    img = Image.open(BytesIO(img_bytes))
    return enhance_image(img, brightness, contrast, sharpness, grayscale)

def render(st, config):
    PREVIEW_WIDTH = 600
    page_sizes = config['page_sizes']
    doc_sizes = config['document_sizes']
    page_size_name = st.selectbox('Select page size', list(page_sizes.keys()), index=0, key="page_size_multi_id_center")
    doc_type = st.selectbox('Select document type', list(doc_sizes.keys()), index=0, key="doc_type_multi_id_center")
    page_size = page_sizes[page_size_name]
    doc_size = doc_sizes[doc_type]
    PAGE_WIDTH_INCH = page_size['width_inch']
    PAGE_HEIGHT_INCH = page_size['height_inch']
    DOC_WIDTH_INCH = doc_size['width_inch']
    DOC_HEIGHT_INCH = doc_size['height_inch']
    dpi = config.get('dpi', 300)

    max_images = 4
    uploaded_files = st.file_uploader("Upload up to 4 document images.", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="multi")
    auto_rotate = st.checkbox('Auto-Rotate for Best Fit', value=False, key='auto_rotate_multi_id_center')
    if uploaded_files:
        if len(uploaded_files) > max_images:
            st.warning(f"Maximum {max_images} images allowed.")
            return
        images = []
        positions = []
        doc_w, doc_h = DOC_WIDTH_INCH, DOC_HEIGHT_INCH
        page_px = (int(PAGE_WIDTH_INCH * dpi), int(PAGE_HEIGHT_INCH * dpi))
        doc_px = (int(doc_w * dpi), int(doc_h * dpi))
        n_images = len(uploaded_files)
        spacing = st.slider("Spacing between images (inches)", 0.0, 2.0, 0.25, 0.05, key="spacing_multi")
        # Determine if rotation allows better fit
        use_rotate = False
        if auto_rotate and doc_w > doc_h and n_images * doc_h + (n_images - 1) * spacing <= PAGE_WIDTH_INCH:
            use_rotate = True
            doc_px = (int(doc_h * dpi), int(doc_w * dpi))
        total_height = n_images * doc_px[1] + (n_images - 1) * int(spacing * dpi)
        y_start = (page_px[1] - total_height) // 2
        page = Image.new("RGB", page_px, "white")
        for idx, uploaded_file in enumerate(uploaded_files):
            st.markdown(f"---\n**Image {idx+1}**")
            img_bytes = uploaded_file.read()
            img = load_and_resize_image(img_bytes)
            st.image(img, caption=f"Original Image {idx+1}", width=PREVIEW_WIDTH)
            col1, col2 = st.columns(2)
            with col1:
                rel_left = st.slider(f"Left Crop % (Image {idx+1})", 0, 50, 0, 1, key=f"left_crop_multi_{idx}") / 100.0
                rel_right = st.slider(f"Right Crop % (Image {idx+1})", 0, 50, 0, 1, key=f"right_crop_multi_{idx}") / 100.0
            with col2:
                rel_top = st.slider(f"Top Crop % (Image {idx+1})", 0, 50, 0, 1, key=f"top_crop_multi_{idx}") / 100.0
                rel_bottom = st.slider(f"Bottom Crop % (Image {idx+1})", 0, 50, 0, 1, key=f"bottom_crop_multi_{idx}") / 100.0
            cropped_img = crop_image_relative(img, rel_left, rel_top, rel_right, rel_bottom)
            st.image(cropped_img, caption=f"Cropped Image {idx+1}", width=PREVIEW_WIDTH)
            grayscale = st.toggle(f"Grayscale (Image {idx+1})", key=f"grayscale_multi_{idx}")
            brightness = st.slider(f"Brightness (Image {idx+1})", 0.1, 5.0, 1.0, 0.05, key=f"brightness_multi_{idx}")
            contrast = st.slider(f"Contrast (Image {idx+1})", 0.1, 5.0, 1.0, 0.05, key=f"contrast_multi_{idx}")
            sharpness = st.slider(f"Sharpness (Image {idx+1})", 0.1, 5.0, 1.0, 0.05, key=f"sharpness_multi_{idx}")
            img_bytes2 = BytesIO()
            cropped_img.save(img_bytes2, format='PNG')
            img_bytes2 = img_bytes2.getvalue()
            edited_img = cached_enhance_image(img_bytes2, brightness, contrast, sharpness, grayscale)
            preview_img = edited_img.copy()
            preview_img.thumbnail((PREVIEW_WIDTH, PREVIEW_WIDTH))
            st.image(preview_img, caption=f"Edited Preview {idx+1}", width=PREVIEW_WIDTH)
            # For Word: positions in inches, rotation flag
            x = (page_px[0] - doc_px[0]) // 2
            y = y_start + idx * (doc_px[1] + int(spacing * dpi))
            page.paste(edited_img.rotate(90, expand=True) if use_rotate else edited_img, (x, y))
            positions.append((x / dpi, y / dpi, use_rotate))
            images.append(edited_img)
        st.markdown("---")
        st.subheader("🖼 Layout Options")
        preview_img = page.copy()
        preview_img.thumbnail((PREVIEW_WIDTH, PREVIEW_WIDTH))
        st.image(preview_img, caption="Final Layout Preview", width=PREVIEW_WIDTH)
        pdf_data = save_image_as_pdf(page, PAGE_WIDTH_INCH, PAGE_HEIGHT_INCH)
        word_data = save_image_as_word(images, positions, PAGE_WIDTH_INCH, PAGE_HEIGHT_INCH, DOC_WIDTH_INCH, DOC_HEIGHT_INCH, dpi=dpi, auto_rotate=use_rotate)
        st.download_button("📄 Download PDF", data=pdf_data, file_name="Multi_Documents.pdf", mime="application/pdf")
        st.download_button("📝 Download Word", data=word_data, file_name="Multi_Documents.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        if st.button("🔁 Reset Multi"):
            st.rerun() 