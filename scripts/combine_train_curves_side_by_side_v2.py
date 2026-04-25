from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt

IN_DIR = Path("comparison")
img1_path = IN_DIR / "comparison_train_loss_only.jpg"
img2_path = IN_DIR / "comparison_train_token_accuracy_only.jpg"

# 直接覆盖原来的 v2 输出
out_jpg = IN_DIR / "comparison_train_loss_token_accuracy_combined_v2.jpg"
out_png = IN_DIR / "comparison_train_loss_token_accuracy_combined_v2.png"

img1 = Image.open(img1_path).convert("RGB")
img2 = Image.open(img2_path).convert("RGB")

def crop_top_title(img, frac=0.11):
    w, h = img.size
    crop_h = int(h * frac)
    return img.crop((0, crop_h, w, h))

# 去掉原图顶部标题区域，避免重复标题
img1 = crop_top_title(img1, frac=0.11)
img2 = crop_top_title(img2, frac=0.11)

# 转成 matplotlib 可画对象
img1_arr = img1
img2_arr = img2

fig, axes = plt.subplots(1, 2, figsize=(18, 7))

axes[0].imshow(img1_arr)
axes[0].set_title("A. Train loss", fontsize=14)
axes[0].axis("off")

axes[1].imshow(img2_arr)
axes[1].set_title("B. Train token accuracy", fontsize=14)
axes[1].axis("off")

plt.tight_layout()

fig.savefig(out_jpg, dpi=300, bbox_inches="tight")
fig.savefig(out_png, dpi=300, bbox_inches="tight")
plt.close(fig)

print("Saved:")
print(out_jpg)
print(out_png)
