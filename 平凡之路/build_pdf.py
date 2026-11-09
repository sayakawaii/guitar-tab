import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

CHORDS = ["007_0062.0-0101.0.png", "008_0101.5-0136.5.png"]
TABS = ["009_0137.0-0209.0.png", "010_0209.5-0234.5.png", "011_0235.0-0252.5.png",
        "012_0253.0-0575.0.png", "013_0575.5-0613.0.png", "014_0613.5-0812.5.png",
        "015_0813.0-0824.0.png", "016_0824.5-0848.5.png", "017_0849.0-0863.5.png",
        "018_0864.0-0891.5.png"]

DPI = 200
PW, PH = int(8.27 * DPI), int(11.69 * DPI)
MARGIN = 110
CW = PW - 2 * MARGIN
FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_B = "C:/Windows/Fonts/msyhbd.ttc"


def clean(path):
    im = cv2.imread("lines/" + path)
    im[im.min(axis=2) > 175] = 255
    mask = (im[:30].min(axis=2) < 200).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask)
    for k in range(1, n):
        x, y, w, h, _ = stats[k]
        if y < 15 and h < 8 and w > 3 * h:
            im[:30][lab == k] = 255
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    ys, xs = np.where(g < 200)
    pad = 12
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, im.shape[0])
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, im.shape[1])
    im = im[y0:y1, x0:x1]
    return Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))


def fit(img, max_w=CW, scale=None):
    s = scale or min(1.0, max_w / img.width) if scale is None else scale
    s = min(s, max_w / img.width)
    return img.resize((int(img.width * s), int(img.height * s)), Image.LANCZOS)


tabs = [clean(p) for p in TABS]
tab_scale = min(CW / t.width for t in tabs) * 0.94
tabs = [fit(t, scale=tab_scale) for t in tabs]
chords = [fit(clean(p), scale=tab_scale * 0.8) for p in CHORDS]

pages = []


def new_page():
    p = Image.new("RGB", (PW, PH), "white")
    pages.append(p)
    return p, ImageDraw.Draw(p)


def footer(d, n):
    f = ImageFont.truetype(FONT, 24)
    txt = f"《平凡之路》吉他弹唱谱  ·  曲谱来源：大树音乐屋教学视频  ·  第 {n} 页"
    w = d.textlength(txt, font=f)
    d.text(((PW - w) / 2, PH - 70), txt, fill=(120, 120, 120), font=f)


page, d = new_page()
y = MARGIN
ft = ImageFont.truetype(FONT_B, 72)
fs = ImageFont.truetype(FONT, 30)
title = "平凡之路"
d.text(((PW - d.textlength(title, font=ft)) / 2, y), title, fill="black", font=ft)
y += 110
for line in ["词：朴树、韩寒    曲：朴树",
             "原调：A    选调：G（变调夹夹 2 品变回原调）    拍号：4/4"]:
    d.text(((PW - d.textlength(line, font=fs)) / 2, y), line, fill=(60, 60, 60), font=fs)
    y += 46
y += 20
d.text((MARGIN, y), "和弦图", fill="black", font=ImageFont.truetype(FONT_B, 34))
y += 60
for c in chords:
    page.paste(c, ((PW - c.width) // 2, y))
    y += c.height + 10
y += 30

GAP = 40
for t in tabs:
    if y + t.height > PH - 110:
        footer(d, len(pages))
        page, d = new_page()
        y = MARGIN
    page.paste(t, (MARGIN + (CW - t.width) // 2, y))
    y += t.height + GAP
footer(d, len(pages))

out = "平凡之路_吉他谱_大树音乐屋.pdf"
pages[0].save(out, save_all=True, append_images=pages[1:], resolution=DPI)
for i, p in enumerate(pages):
    p.resize((PW // 2, PH // 2)).save(f"preview_{i}.png")
print(out, len(pages))
