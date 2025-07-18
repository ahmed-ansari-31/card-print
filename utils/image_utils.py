from PIL import Image, ImageEnhance, ImageOps

def enhance_image(img, brightness=1.0, contrast=1.0, sharpness=1.0, grayscale=False, rotate_angle=0, crop_values=(0,0,0,0)):
    img = img.convert("RGB")
    if grayscale:
        img = ImageOps.grayscale(img).convert("RGB")
    img = img.rotate(rotate_angle, expand=True)
    width, height = img.size
    left_crop, top_crop, right_crop, bottom_crop = crop_values
    img = img.crop((left_crop, top_crop, width - right_crop, height - bottom_crop))
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Sharpness(img).enhance(sharpness)
    return img

def resize_image(img, width_inch, height_inch, dpi=300):
    return img.resize((int(width_inch * dpi), int(height_inch * dpi)))

def crop_image_relative(img, rel_left, rel_top, rel_right, rel_bottom):
    """Crop image using relative coordinates (0-1 floats)."""
    width, height = img.size
    left = int(rel_left * width)
    top = int(rel_top * height)
    right = int(width - rel_right * width)
    bottom = int(height - rel_bottom * height)
    return img.crop((left, top, right, bottom))

def make_canvas_with_image(page_width_inch, page_height_inch, img, img_width_inch, img_height_inch, position="center", dpi=300):
    page_px = (int(page_width_inch * dpi), int(page_height_inch * dpi))
    img_px = (int(img_width_inch * dpi), int(img_height_inch * dpi))
    canvas = Image.new("RGB", page_px, "white")
    img_resized = img.resize(img_px)
    if position == "center":
        x = (page_px[0] - img_px[0]) // 2
        y = (page_px[1] - img_px[1]) // 2
    else:
        x, y = 0, 0  # Top-left by default
    canvas.paste(img_resized, (x, y))
    return canvas 