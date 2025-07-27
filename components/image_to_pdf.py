import streamlit as st
from PIL import Image
from io import BytesIO
from utils.image_utils import crop_image_relative, enhance_image

def render(st, config):
    st.header("Image to PDF Converter")
    dpi = config.get('dpi', 300)
    page_sizes = config.get('page_sizes', {'A4': {'width_inch': 8.27, 'height_inch': 11.69}})
    page_size_name = st.selectbox('Select page size', list(page_sizes.keys()), index=0, key="page_size_image_to_pdf")
    page_size = page_sizes[page_size_name]
    PAGE_WIDTH_INCH = page_size['width_inch']
    PAGE_HEIGHT_INCH = page_size['height_inch']
    PREVIEW_WIDTH = 400

    image_files = st.file_uploader("Upload images to convert to PDF", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    processed_images = []
    if image_files:
        for idx, img_file in enumerate(image_files):
            st.markdown(f"---\n**Image {idx+1}**")
            img = Image.open(img_file).convert("RGB")
            st.image(img, caption=f"Original Image {idx+1}", width=PREVIEW_WIDTH)
            col1, col2 = st.columns(2)
            with col1:
                rel_left = st.slider(f"Left Crop % (Image {idx+1})", 0, 50, 0, 1, key=f"left_crop_img2pdf_{idx}") / 100.0
                rel_right = st.slider(f"Right Crop % (Image {idx+1})", 0, 50, 0, 1, key=f"right_crop_img2pdf_{idx}") / 100.0
            with col2:
                rel_top = st.slider(f"Top Crop % (Image {idx+1})", 0, 50, 0, 1, key=f"top_crop_img2pdf_{idx}") / 100.0
                rel_bottom = st.slider(f"Bottom Crop % (Image {idx+1})", 0, 50, 0, 1, key=f"bottom_crop_img2pdf_{idx}") / 100.0
            cropped_img = crop_image_relative(img, rel_left, rel_top, rel_right, rel_bottom)
            st.image(cropped_img, caption=f"Cropped Image {idx+1}", width=PREVIEW_WIDTH)
            grayscale = st.toggle(f"Grayscale (Image {idx+1})", key=f"grayscale_img2pdf_{idx}")
            brightness = st.slider(f"Brightness (Image {idx+1})", 0.1, 5.0, 1.0, 0.05, key=f"brightness_img2pdf_{idx}")
            contrast = st.slider(f"Contrast (Image {idx+1})", 0.1, 5.0, 1.0, 0.05, key=f"contrast_img2pdf_{idx}")
            sharpness = st.slider(f"Sharpness (Image {idx+1})", 0.1, 5.0, 1.0, 0.05, key=f"sharpness_img2pdf_{idx}")
            edited_img = enhance_image(cropped_img, brightness, contrast, sharpness, grayscale)
            preview_img = edited_img.copy()
            preview_img.thumbnail((PREVIEW_WIDTH, PREVIEW_WIDTH))
            st.image(preview_img, caption=f"Edited Preview {idx+1}", width=PREVIEW_WIDTH)
            fit_to_page = st.checkbox(f"Fit to page (Image {idx+1})", value=True, key=f"fit2page_img2pdf_{idx}")
            if fit_to_page:
                # Resize to fit page
                img_w, img_h = PAGE_WIDTH_INCH, PAGE_HEIGHT_INCH
                img_px = (int(img_w * dpi), int(img_h * dpi))
                final_img = edited_img.resize(img_px)
            else:
                final_img = edited_img
            processed_images.append(final_img)
    if st.button("Convert Images to PDF") and processed_images:
        pdf_bytes = BytesIO()
        processed_images[0].save(pdf_bytes, format="PDF", save_all=True, append_images=processed_images[1:])
        pdf_bytes.seek(0)
        st.success("Images converted to PDF!")
        st.download_button("Download PDF", data=pdf_bytes, file_name="images.pdf", mime="application/pdf")
