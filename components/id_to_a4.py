import streamlit as st
from PIL import Image
from io import BytesIO
from utils.image_utils import enhance_image, resize_image, crop_image_relative, make_canvas_with_image
from utils.pdf_utils import save_image_as_pdf
from utils.word_utils import save_image_as_word
from datetime import datetime
import math

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

def get_valid_grids(page_w, page_h, doc_w, doc_h, min_space_inch=0.25, allow_rotate=False):
    # Try all grid options up to 8 per page, return only those that fit
    valid = []
    for cols in range(1, 5):
        for rows in range(1, 9):
            n = cols * rows
            if n > 8: continue
            # Try without rotation
            total_w = cols * doc_w + (cols - 1) * min_space_inch
            total_h = rows * doc_h + (rows - 1) * min_space_inch
            if total_w <= page_w and total_h <= page_h:
                valid.append((cols, rows, False))
            # Try with rotation if allowed
            if allow_rotate and (doc_w != doc_h):
                total_w_r = cols * doc_h + (cols - 1) * min_space_inch
                total_h_r = rows * doc_w + (rows - 1) * min_space_inch
                if total_w_r <= page_w and total_h_r <= page_h:
                    valid.append((cols, rows, True))
    return valid

def render(st, config):
    PREVIEW_WIDTH = 600
    page_sizes = config['page_sizes']
    doc_sizes = config['document_sizes']
    page_size_name = st.selectbox('Select page size', list(page_sizes.keys()), index=0, key="page_size_id_to_a4")
    doc_type = st.selectbox('Select document type', list(doc_sizes.keys()), index=0, key="doc_type_id_to_a4")
    page_size = page_sizes[page_size_name]
    doc_size = doc_sizes[doc_type]
    PAGE_WIDTH_INCH = page_size['width_inch']
    PAGE_HEIGHT_INCH = page_size['height_inch']
    DOC_WIDTH_INCH = doc_size['width_inch']
    DOC_HEIGHT_INCH = doc_size['height_inch']
    dpi = config.get('dpi', 300)

    auto_rotate = st.checkbox('Auto-Rotate for Best Fit', value=False, key='auto_rotate_id_to_a4')
    valid_grids = get_valid_grids(PAGE_WIDTH_INCH, PAGE_HEIGHT_INCH, DOC_WIDTH_INCH, DOC_HEIGHT_INCH, allow_rotate=auto_rotate)
    grid_labels = [f"{cols} x {rows} ({cols*rows} per page){' (rotated)' if rot else ''}" for cols, rows, rot in valid_grids]
    if not valid_grids:
        st.warning("No valid grid fits this document and page size. Please select a different combination.")
        return
    grid_idx = st.selectbox("Select grid (columns x rows)", list(range(len(valid_grids))), format_func=lambda i: grid_labels[i], key="grid_id_to_a4")
    columns, rows, use_rotate = valid_grids[grid_idx]

    if 'image_uploaded' not in st.session_state:
        st.session_state.image_uploaded = False
    if 'preview_ready' not in st.session_state:
        st.session_state.preview_ready = False
    if 'cropped_img' not in st.session_state:
        st.session_state.cropped_img = None

    if not st.session_state.image_uploaded:
        uploaded_file1 = st.file_uploader("Upload a document image.", type=["jpg", "jpeg", "png"])
        if uploaded_file1:
            img_bytes = uploaded_file1.read()
            st.session_state.original_image = load_and_resize_image(img_bytes)
            st.session_state.image_uploaded = True
            st.success("✅ Image uploaded. You can now crop and edit it below.")

    if st.session_state.image_uploaded:
        st.subheader("✂️ Crop Image (relative to width/height)")
        img = st.session_state.original_image
        st.image(img, caption="Original Image", width=PREVIEW_WIDTH)
        col1, col2 = st.columns(2)
        with col1:
            rel_left = st.slider("Left Crop (%)", 0, 50, 0, 1, key="left_crop") / 100.0
            rel_right = st.slider("Right Crop (%)", 0, 50, 0, 1, key="right_crop") / 100.0
        with col2:
            rel_top = st.slider("Top Crop (%)", 0, 50, 0, 1, key="top_crop") / 100.0
            rel_bottom = st.slider("Bottom Crop (%)", 0, 50, 0, 1, key="bottom_crop") / 100.0
        cropped_img = crop_image_relative(img, rel_left, rel_top, rel_right, rel_bottom)
        st.session_state.cropped_img = cropped_img
        st.image(cropped_img, caption="Cropped Image", width=PREVIEW_WIDTH)

        st.subheader("🎛 Real-Time Image Editor (Single Document)")
        grayscale = st.toggle("Grayscale")
        brightness = st.slider("Brightness", 0.1, 5.0, 1.0, 0.05)
        contrast = st.slider("Contrast", 0.1, 5.0, 1.0, 0.05)
        sharpness = st.slider("Sharpness", 0.1, 5.0, 1.0, 0.05)

        img_bytes = BytesIO()
        cropped_img.save(img_bytes, format='PNG')
        img_bytes = img_bytes.getvalue()
        edited_preview = cached_enhance_image(img_bytes, brightness, contrast, sharpness, grayscale)
        preview_img = edited_preview.copy()
        preview_img.thumbnail((PREVIEW_WIDTH, PREVIEW_WIDTH))
        st.image(preview_img, caption="🔍 Edited Preview", width=PREVIEW_WIDTH)

        if st.button("🧱 Apply to Layout & Generate PDF/Word"):
            h_spacing = v_spacing = 0.25
            page_px = (int(PAGE_WIDTH_INCH * dpi), int(PAGE_HEIGHT_INCH * dpi))
            if use_rotate:
                img_w, img_h = DOC_HEIGHT_INCH, DOC_WIDTH_INCH
            else:
                img_w, img_h = DOC_WIDTH_INCH, DOC_HEIGHT_INCH
            doc_img = edited_preview.rotate(90, expand=True) if use_rotate else edited_preview
            doc_img = doc_img.resize((int(img_w * dpi), int(img_h * dpi)))
            total_width = columns * int(img_w * dpi) + (columns - 1) * int(h_spacing * dpi)
            total_height = rows * int(img_h * dpi) + (rows - 1) * int(v_spacing * dpi)
            left_margin = (page_px[0] - total_width) // 2
            top_margin = (page_px[1] - total_height) // 2
            page = Image.new("RGB", page_px, "white")
            images = []
            positions = []
            for row in range(rows):
                for col in range(columns):
                    x = left_margin + col * (int(img_w * dpi) + int(h_spacing * dpi))
                    y = top_margin + row * (int(img_h * dpi) + int(v_spacing * dpi))
                    page.paste(doc_img, (x, y))
                    # For Word: positions in inches, rotation flag
                    positions.append((x / dpi, y / dpi, use_rotate))
                    images.append(edited_preview)
            st.session_state.preview_ready = True
            st.session_state.preview_img = page.copy()
            st.session_state.pdf_data = save_image_as_pdf(page, PAGE_WIDTH_INCH, PAGE_HEIGHT_INCH)
            st.session_state.word_data = save_image_as_word(images, positions, PAGE_WIDTH_INCH, PAGE_HEIGHT_INCH, DOC_WIDTH_INCH, DOC_HEIGHT_INCH, dpi=dpi, auto_rotate=use_rotate)

    if st.session_state.get("preview_ready", False):
        st.subheader(f"🖼 Final Layout ({columns*rows} documents on page)")
        preview_img = st.session_state.preview_img.copy()
        preview_img.thumbnail((PREVIEW_WIDTH, PREVIEW_WIDTH))
        st.image(preview_img, use_container_width=True)
        st.download_button("📄 Download PDF", data=st.session_state.pdf_data, file_name="Documents.pdf", mime="application/pdf")
        st.download_button("📝 Download Word", data=st.session_state.word_data, file_name="Documents.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        if st.button("🔁 Reset"):
            st.session_state.clear()
            st.rerun() 