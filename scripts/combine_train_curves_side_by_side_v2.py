from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

IN_DIR = Path("comparison")
img1_path = IN_DIR / "comparison_train_loss_only.jpg"
img2_path = IN_DIR / "comparison_train_token_accuracy_only.jpg"

out_jpg = IN_DIR / "comparison_train_loss_token_accuracy_combined_v2.jpg"
out_png = IN_DIR / "comparison_train_loss_token_accuracy_combined_v2.png"

img1 = Image.open(img1_path).convert("RGB")
img2 = Image.open(img2_path).convert("RGB")

def resize_to_height(img, target_h):
    if img.height == target_h:
        return img
    new_w = int(img.width * target_h / img.height)
    return img.resize((new_w, target_h))

# 统一高度
target_h = max(img1.height, img2.height)
img1 = resize_to_height(img1, target_h)
img2 = resize_to_height(img2, target_h)

# 版式参数
top_pad = 90
side_pad = 30
bottom_pad = 20
gap = 30
bg_color = "white"
text_color = "black"

canvas_w = side_pad + img1.width + gap + img2.width + side_pad
canvas_h = top_pad + target_h + bottom_pad

canvas = Image.new("RGB", (canvas_w, canvas_h), bg_color)
draw = ImageDraw.Draw(canvas)

# 尝试更大的字体，失败则回退默认字体
try:
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
except Exception:
    font = ImageFont.load_default()

# 粘贴两张图
x1 = side_pad
y1 = top_pad
x2 = side_pad + img1.width + gap
y2 = top_pad

canvas.paste(img1, (x1, y1))
canvas.paste(img2, (x2, y2))

# 标题
title1 = "A. Train loss"
title2 = "B. Train token accuracy"

draw.text((x1, 25), title1, fill=text_color, font=font)
draw.text((x2, 25), title2, fill=text_color, font=font)

# 保存
canvas.save(out_jpg, quality=95)
canvas.save(out_png)

print("Saved:")
print(out_jpg)
print(out_png)
