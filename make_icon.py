from PIL import Image, ImageDraw

sizes = [16, 32, 48, 64, 128]
imgs = []
for s in sizes:
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = s // 2, s // 2
    r = s // 2 - 1
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(124, 58, 237, 255))
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(168, 85, 247, 255), width=max(1, s // 32))
    th = int(s * 0.3)
    tw = int(s * 0.25)
    x1 = cx - tw // 2 + 2
    draw.polygon([(x1, cy - th), (x1 + tw, cy), (x1, cy + th)], fill=(255, 255, 255, 255))
    imgs.append(img)

imgs[-1].save("logo.ico", format="ICO", sizes=[(s, s) for s in sizes], append_images=imgs[:-1])
imgs[-1].save("logo.png", format="PNG")
print("logo.ico and logo.png created!")
