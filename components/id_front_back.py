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
    page_size_name = st.selectbox('Select page size', list(page_sizes.keys()), index=0, key="page_size_id_front_back")
    doc_type = st.selectbox('Select document type', list(doc_sizes.keys()), index=0, key="doc_type_id_front_back")
    page_size = page_sizes[page_size_name]
    doc_size = doc_sizes[doc_type]
    PAGE_WIDTH_INCH = page_size['width_inch']
    PAGE_HEIGHT_INCH = page_size['height_inch']
    DOC_WIDTH_INCH = doc_size['width_inch']
    DOC_HEIGHT_INCH = doc_size['height_inch']
    dpi = config.get('dpi', 300)

    st.subheader("Upload Front and Back Images")
    front = st.file_uploader("Upload Front Side", type=["jpg", "jpeg", "png"], key="front")
    back = st.file_uploader("Upload Back Side", type=["jpg", "jpeg", "png"], key="back")
    if front and back:
        st.success("Both images uploaded. You can now crop and edit them below.")
        # --- Front ---
        st.markdown("---\n**Front Side**")
        img_bytes = front.read()
        img_front = load_and_resize_image(img_bytes)
        st.image(img_front, caption="Original Front", width=PREVIEW_WIDTH)
        col1, col2 = st.columns(2)
        with col1:
            rel_left = st.slider("Left Crop % (Front)", 0, 50, 0, 1, key="left_crop_front") / 100.0
            rel_right = st.slider("Right Crop % (Front)", 0, 50, 0, 1, key="right_crop_front") / 100.0
        with col2:
            rel_top = st.slider("Top Crop % (Front)", 0, 50, 0, 1, key="top_crop_front") / 100.0
            rel_bottom = st.slider("Bottom Crop % (Front)", 0, 50, 0, 1, key="bottom_crop_front") / 100.0
        cropped_front = crop_image_relative(img_front, rel_left, rel_top, rel_right, rel_bottom)
        st.image(cropped_front, caption="Cropped Front", width=PREVIEW_WIDTH)
        grayscale_f = st.toggle("Grayscale (Front)", key="grayscale_front")
        brightness_f = st.slider("Brightness (Front)", 0.1, 5.0, 1.0, 0.05, key="brightness_front")
        contrast_f = st.slider("Contrast (Front)", 0.1, 5.0, 1.0, 0.05, key="contrast_front")
        sharpness_f = st.slider("Sharpness (Front)", 0.1, 5.0, 1.0, 0.05, key="sharpness_front")
        img_bytes_f = BytesIO()
        cropped_front.save(img_bytes_f, format='PNG')
        img_bytes_f = img_bytes_f.getvalue()
        edited_front = cached_enhance_image(img_bytes_f, brightness_f, contrast_f, sharpness_f, grayscale_f)
        preview_img_f = edited_front.copy()
        preview_img_f.thumbnail((PREVIEW_WIDTH, PREVIEW_WIDTH))
        st.image(preview_img_f, caption="Edited Front Preview", width=PREVIEW_WIDTH)
        # --- Back ---
        st.markdown("---\n**Back Side**")
        img_bytes = back.read()
        img_back = load_and_resize_image(img_bytes)
        st.image(img_back, caption="Original Back", width=PREVIEW_WIDTH)
        col1, col2 = st.columns(2)
        with col1:
            rel_left = st.slider("Left Crop % (Back)", 0, 50, 0, 1, key="left_crop_back") / 100.0
            rel_right = st.slider("Right Crop % (Back)", 0, 50, 0, 1, key="right_crop_back") / 100.0
        with col2:
            rel_top = st.slider("Top Crop % (Back)", 0, 50, 0, 1, key="top_crop_back") / 100.0
            rel_bottom = st.slider("Bottom Crop % (Back)", 0, 50, 0, 1, key="bottom_crop_back") / 100.0
        cropped_back = crop_image_relative(img_back, rel_left, rel_top, rel_right, rel_bottom)
        st.image(cropped_back, caption="Cropped Back", width=PREVIEW_WIDTH)
        grayscale_b = st.toggle("Grayscale (Back)", key="grayscale_back")
        brightness_b = st.slider("Brightness (Back)", 0.1, 5.0, 1.0, 0.05, key="brightness_back")
        contrast_b = st.slider("Contrast (Back)", 0.1, 5.0, 1.0, 0.05, key="contrast_back")
        sharpness_b = st.slider("Sharpness (Back)", 0.1, 5.0, 1.0, 0.05, key="sharpness_back")
        img_bytes_b = BytesIO()
        cropped_back.save(img_bytes_b, format='PNG')
        img_bytes_b = img_bytes_b.getvalue()
        edited_back = cached_enhance_image(img_bytes_b, brightness_b, contrast_b, sharpness_b, grayscale_b)
        preview_img_b = edited_back.copy()
        preview_img_b.thumbnail((PREVIEW_WIDTH, PREVIEW_WIDTH))
        st.image(preview_img_b, caption="Edited Back Preview", width=PREVIEW_WIDTH)
        # --- Layout ---
        if st.button("🧱 Arrange & Generate PDF/Word"):
            from PIL import Image as PILImage
            page_px = (int(PAGE_WIDTH_INCH * dpi), int(PAGE_HEIGHT_INCH * dpi))
            doc_px = (int(DOC_WIDTH_INCH * dpi), int(DOC_HEIGHT_INCH * dpi))
            page = PILImage.new("RGB", page_px, "white")
            # Place front on upper half, back on lower half, both centered
            x = (page_px[0] - doc_px[0]) // 2
            y_front = int(page_px[1] * 0.15)  # 15% from top
            y_back = int(page_px[1] * 0.6)    # 60% from top
            page.paste(edited_front.resize(doc_px), (x, y_front))
            page.paste(edited_back.resize(doc_px), (x, y_back))
            preview_img = page.copy()
            preview_img.thumbnail((PREVIEW_WIDTH, PREVIEW_WIDTH))
            st.image(preview_img, caption="Final Layout Preview", width=PREVIEW_WIDTH)
            images = [edited_front, edited_back]
            positions = [
                (x / dpi, y_front / dpi, False),
                (x / dpi, y_back / dpi, False)
            ]
            pdf_data = save_image_as_pdf(page, PAGE_WIDTH_INCH, PAGE_HEIGHT_INCH)
            word_data = save_image_as_word(images, positions, PAGE_WIDTH_INCH, PAGE_HEIGHT_INCH, DOC_WIDTH_INCH, DOC_HEIGHT_INCH, dpi=dpi, auto_rotate=False)
            st.download_button("📄 Download PDF", data=pdf_data, file_name="Front_Back.pdf", mime="application/pdf")
            st.download_button("📝 Download Word", data=word_data, file_name="Front_Back.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            if st.button("🔁 Reset Front/Back"):
                st.rerun() 