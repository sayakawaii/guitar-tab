from PIL import Image, ImageDraw
import os, sys
files = sorted(os.listdir("samples"))
cols = 6
w, h = Image.open("samples/" + files[0]).size
for page in range(0, len(files), 30):
    chunk = files[page:page + 30]
    rows = (len(chunk) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * h), "white")
    d = ImageDraw.Draw(sheet)
    for i, fn in enumerate(chunk):
        x, y = (i % cols) * w, (i // cols) * h
        sheet.paste(Image.open("samples/" + fn), (x, y))
        d.rectangle([x, y, x + 60, y + 20], fill="yellow")
        d.text((x + 3, y + 3), fn[:4] + "s", fill="black")
    sheet.save(f"sheet_{page // 30}.jpg", quality=85)
