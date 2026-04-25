from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

IN_DIR = Path("comparison")
img1_path = IN_DIR / "comparison_train_loss_only.jpg"
img2_path = IN_DIR / "comparison_train_token_accuracy_only.jpg"

# 直接覆盖之前的 v2 输出
out_jpg = IN_DIR / "comparison_train_loss_token_accuracy_combined_v2.jpg"
out_png = IN_DIR / "comparison_train_loss_token_accuracy_combined_v2.png"

img1 = Image.open(img1_path).convert("RGB")
img2 = Image.open(img2_path).convert("RGB")

def resize_to_height(img, target_h):
    if img.height == target_h:
        return img
    new_w = int(img.width * target_h / img.height)
    return img.resize((new_w, target_h))

def rewrite_title(img, new_title):
    """
    覆盖原图顶部标题区域，并重写标题。
    目标效果：像 0.8B 六合一那种，A/B 直接写进图标题里。
    """
    draw = ImageDraw.Draw(img)
    w, h = img.size

    # 顶部标题带区域高度，按常见 matplotlib 图大致估计
    title_band_h = int(h * 0.12)

    # 用白色覆盖原标题区域
    draw.rectangle([(0, 0), (w, title_band_h)], fill="white")

    # 字体
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 34)
    except Exception:
        font = ImageFont.load_default()

    # 居中写标题
    bbox = draw.textbbox((0, 0), new_title, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = (w - text_w) // 2
    y = max(10, (title_band_h - text_h) // 2)

    draw.text((x, y), new_title, fill="black", font=font)
    return img

# 先改每张图的标题
img1 = rewrite_title(img1, "A. Train loss")
img2 = rewrite_title(img2, "B. Train token accuracy")

# 统一高度
target_h = max(img1.height, img2.height)
img1 = resize_to_height(img1, target_h)
img2 = resize_to_height(img2, target_h)

# 左右拼接，不再额外加顶部总标题
side_pad = 20
gap = 20
top_pad = 10
bottom_pad = 10

canvas_w = side_pad + img1.width + gap + img2.width + side_pad
canvas_h = top_pad + target_h + bottom_pad

canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
canvas.paste(img1, (side_pad, top_pad))
canvas.paste(img2, (side_pad + img1.width + gap, top_pad))

canvas.save(out_jpg, quality=95)
canvas.save(out_png)

print("Saved:")
print(out_jpg)
print(out_png)
