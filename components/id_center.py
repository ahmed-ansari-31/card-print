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
    page_size_name = st.selectbox('Select page size', list(page_sizes.keys()), index=0, key="page_size_id_center")
    doc_type = st.selectbox('Select document type', list(doc_sizes.keys()), index=0, key="doc_type_id_center")
    page_size = page_sizes[page_size_name]
    doc_size = doc_sizes[doc_type]
    PAGE_WIDTH_INCH = page_size['width_inch']
    PAGE_HEIGHT_INCH = page_size['height_inch']
    DOC_WIDTH_INCH = doc_size['width_inch']
    DOC_HEIGHT_INCH = doc_size['height_inch']
    dpi = config.get('dpi', 300)

    auto_rotate = st.checkbox('Auto-Rotate', value=False, key='auto_rotate_id_center')

    if 'image_uploaded_center' not in st.session_state:
        st.session_state.image_uploaded_center = False
    if 'preview_ready_center' not in st.session_state:
        st.session_state.preview_ready_center = False
    if 'cropped_img_center' not in st.session_state:
        st.session_state.cropped_img_center = None

    if not st.session_state.image_uploaded_center:
        uploaded_file1 = st.file_uploader("Upload a document image.", type=["jpg", "jpeg", "png"], key="center")
        if uploaded_file1:
            img_bytes = uploaded_file1.read()
            st.session_state.original_image_center = load_and_resize_image(img_bytes)
            st.session_state.image_uploaded_center = True
            st.success("✅ Image uploaded. You can now crop and edit it below.")

    if st.session_state.image_uploaded_center:
        st.subheader("✂️ Crop Image (relative to width/height)")
        img = st.session_state.original_image_center
        st.image(img, caption="Original Image", width=PREVIEW_WIDTH)
        col1, col2 = st.columns(2)
        with col1:
            rel_left = st.slider("Left Crop (%)", 0, 50, 0, 1, key="left_crop_center") / 100.0
            rel_right = st.slider("Right Crop (%)", 0, 50, 0, 1, key="right_crop_center") / 100.0
        with col2:
            rel_top = st.slider("Top Crop (%)", 0, 50, 0, 1, key="top_crop_center") / 100.0
            rel_bottom = st.slider("Bottom Crop (%)", 0, 50, 0, 1, key="bottom_crop_center") / 100.0
        cropped_img = crop_image_relative(img, rel_left, rel_top, rel_right, rel_bottom)
        st.session_state.cropped_img_center = cropped_img
        st.image(cropped_img, caption="Cropped Image", width=PREVIEW_WIDTH)

        st.subheader("🎛 Real-Time Image Editor (Single Document)")
        grayscale = st.toggle("Grayscale", key="grayscale_center")
        brightness = st.slider("Brightness", 0.1, 5.0, 1.0, 0.05, key="brightness_center")
        contrast = st.slider("Contrast", 0.1, 5.0, 1.0, 0.05, key="contrast_center")
        sharpness = st.slider("Sharpness", 0.1, 5.0, 1.0, 0.05, key="sharpness_center")

        img_bytes = BytesIO()
        cropped_img.save(img_bytes, format='PNG')
        img_bytes = img_bytes.getvalue()
        edited_preview = cached_enhance_image(img_bytes, brightness, contrast, sharpness, grayscale)
        preview_img = edited_preview.copy()
        preview_img.thumbnail((PREVIEW_WIDTH, PREVIEW_WIDTH))
        st.image(preview_img, caption="🔍 Edited Preview", width=PREVIEW_WIDTH)

        if st.button("🧱 Place on Center & Generate PDF/Word"):
            # Use reusable utility to make canvas and place image at center
            if auto_rotate and DOC_WIDTH_INCH < DOC_HEIGHT_INCH:
                img_w, img_h = DOC_HEIGHT_INCH, DOC_WIDTH_INCH
                rotated = True
            else:
                img_w, img_h = DOC_WIDTH_INCH, DOC_HEIGHT_INCH
                rotated = False
            page_px = (int(PAGE_WIDTH_INCH * dpi), int(PAGE_HEIGHT_INCH * dpi))
            img_px = (int(img_w * dpi), int(img_h * dpi))
            page = Image.new("RGB", page_px, "white")
            img_to_paste = edited_preview.rotate(90, expand=True) if rotated else edited_preview
            x = (page_px[0] - img_px[0]) // 2
            y = (page_px[1] - img_px[1]) // 2
            page.paste(img_to_paste.resize(img_px), (x, y))
            images = [edited_preview]
            positions = [(x / dpi, y / dpi, rotated)]
            st.session_state.preview_ready_center = True
            st.session_state.preview_img_center = page.copy()
            st.session_state.pdf_data_center = save_image_as_pdf(page, PAGE_WIDTH_INCH, PAGE_HEIGHT_INCH)
            st.session_state.word_data_center = save_image_as_word(images, positions, PAGE_WIDTH_INCH, PAGE_HEIGHT_INCH, DOC_WIDTH_INCH, DOC_HEIGHT_INCH, dpi=dpi, auto_rotate=rotated)

    if st.session_state.get("preview_ready_center", False):
        st.subheader("🖼 Final Layout (Document Centered on Page)")
        preview_img = st.session_state.preview_img_center.copy()
        preview_img.thumbnail((PREVIEW_WIDTH, PREVIEW_WIDTH))
        st.image(preview_img, use_container_width=True)
        st.download_button("📄 Download PDF", data=st.session_state.pdf_data_center, file_name="Document_Centered.pdf", mime="application/pdf")
        st.download_button("📝 Download Word", data=st.session_state.word_data_center, file_name="Document_Centered.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        if st.button("🔁 Reset Center"):
            st.session_state.image_uploaded_center = False
            st.session_state.preview_ready_center = False
            st.session_state.cropped_img_center = None
            st.session_state.original_image_center = None
            st.session_state.preview_img_center = None
            st.session_state.pdf_data_center = None
            st.session_state.word_data_center = None
            st.rerun() 