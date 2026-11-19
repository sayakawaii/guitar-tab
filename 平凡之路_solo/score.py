"""Typeset 《平凡之路》: 大树音乐屋编配 + 间奏 solo (vector PDF)."""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from data import X, CHORDS, INTRO, VERSE1, VERSE2, CHORUS, SOLO, OUTRO, TEMPO, CAPO


pdfmetrics.registerFont(TTFont("YH", "C:/Windows/Fonts/msyh.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("YHB", "C:/Windows/Fonts/msyhbd.ttc", subfontIndex=0))

PW, PH = A4
ML, MR, MT, MB = 42, 42, 46, 50
CW = PW - ML - MR
GAP = 6.2
RED = (0.82, 0.25, 0.3)
SOLO_TINT = (0.93, 0.96, 1.0)


def chord_diagram(c, name, x, y, w=22, label=True, fs=7.5):
    frets, base = CHORDS[name]
    cell_w, cell_h, rows = w / 5, w / 5 * 1.15, 4
    gx, gy = x, y - fs - 6
    if label:
        c.setFont("YHB", fs)
        c.drawCentredString(gx + w / 2, y - fs + 1, name)
    c.setLineWidth(0.5)
    for i in range(6):
        c.line(gx + i * cell_w, gy, gx + i * cell_w, gy - rows * cell_h)
    for r in range(rows + 1):
        c.line(gx, gy - r * cell_h, gx + w, gy - r * cell_h)
    if base == 1:
        c.setLineWidth(1.6)
        c.line(gx, gy, gx + w, gy)
        c.setLineWidth(0.5)
    else:
        c.setFont("YH", 5.5)
        c.drawRightString(gx - 1.5, gy - cell_h * 0.8, str(base))
    for i, f in enumerate(frets):
        sx = gx + i * cell_w
        if f == -1:
            c.setFont("YH", 5)
            c.drawCentredString(sx, gy + 1.2, "×")
        elif f == 0:
            c.circle(sx, gy + 2.6, 1.3, stroke=1, fill=0)
        else:
            c.circle(sx, gy - (f - base + 0.5) * cell_h, 1.6, stroke=0, fill=1)


def label_box(c, text, x, y, fs=9, color=RED):
    w = pdfmetrics.stringWidth(text, "YHB", fs) + 8
    c.setFillColorRGB(*color)
    c.roundRect(x, y - 3, w, fs + 6, 2, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("YHB", fs)
    c.drawString(x + 4, y + 0.5, text)
    c.setFillColorRGB(0, 0, 0)
    return w


def arc(c, xa, xb, y, label=""):
    p = c.beginPath()
    p.moveTo(xa + 1, y)
    p.curveTo(xa + 2, y + 4, xb - 2, y + 4, xb - 1, y)
    c.setLineWidth(0.5)
    c.drawPath(p)
    if label:
        c.setFont("YH", 5.5)
        c.drawCentredString((xa + xb) / 2, y + 4.2, label)


def line_height(bars, diagrams=True):
    return (40 if diagrams else 12) + 5 * GAP + 24 + (12 if any(b.ly for b in bars) else 0)


def draw_tab_line(c, bars, x0, ytop, width, diagrams=True, first=False, final=False, time_sig=None,
                  measure_no=None, tint=None):
    diag_h = 40 if diagrams else 12
    y1 = ytop - diag_h
    y6 = y1 - 5 * GAP
    sy = lambda s: y1 - (s - 1) * GAP
    head = 22 if first else 6
    weights = [max(len(b), 5) + 1.5 for b in bars]
    bws = [(width - head) * w / sum(weights) for w in weights]
    if tint:
        c.setFillColorRGB(*tint)
        c.rect(x0, y6 - 2, width, y1 - y6 + 4, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)
    c.setLineWidth(0.5)
    for s in range(1, 7):
        c.line(x0, sy(s), x0 + width, sy(s))
    c.setLineWidth(0.8)
    c.line(x0, y1, x0, y6)
    if first:
        c.setFont("YHB", 8)
        for i, ch in enumerate("TAB"):
            c.drawCentredString(x0 + 6, y1 - 9 - i * 9, ch)
        if time_sig:
            c.setFont("YHB", 10)
            c.drawCentredString(x0 + 16, sy(2) - 4, str(time_sig[0]))
            c.drawCentredString(x0 + 16, sy(5) - 2, str(time_sig[1]))
    stem_top, stem_bot = y6 - 4, y6 - 20
    pending = []
    for bi, bar in enumerate(bars):
        bx = x0 + head + sum(bws[:bi])
        bw = bws[bi]
        if measure_no is not None:
            c.setFont("YH", 5.5)
            c.drawString(bx + 1.5, y1 + 2, str(measure_no + bi))
        n = len(bar)
        pad = 0
        if getattr(bar, "ts", None) and not (first and bi == 0 and time_sig):
            c.setFont("YHB", 9)
            c.drawCentredString(bx + 6, sy(2) - 3.5, str(bar.ts[0]))
            c.drawCentredString(bx + 6, sy(5) - 1.5, str(bar.ts[1]))
            pad = 8
        step = (bw - 12 - pad) / max(n, 1)
        xs = [bx + 8 + pad + step * (i + 0.15) for i in range(n)] if n > 1 else [bx + 10 + pad]
        for e, ex in zip(bar, xs):
            if e["chord"]:
                if diagrams and e["chord"] in CHORDS:
                    chord_diagram(c, e["chord"], ex - 9, ytop, w=18, fs=7 if len(e["chord"]) < 8 else 5.6)
                else:
                    c.setFont("YHB", 8)
                    c.drawString(ex - 3, y1 + 8, e["chord"])
        for e, ex in zip(bar, xs):
            if e["rest"]:
                if e["d"] in (1, 2):
                    yy = sy(3)
                    c.setLineWidth(0.8)
                    for k in range(3 - e["d"]):
                        c.circle(ex - 1.2 - k * 0.8, yy + 2.2 - k * 2.6, 1.0, stroke=0, fill=1)
                        c.line(ex - 1.2 - k * 0.8, yy + 1.4 - k * 2.6, ex + 1.8 - k * 0.8, yy + 2.8 - k * 2.6)
                    c.line(ex + 1.8, yy + 2.8, ex - 0.4 - (2 - e["d"]) * 1.2, yy - 4 - (2 - e["d"]) * 2)
                    c.setLineWidth(0.5)
                else:
                    c.rect(ex - 3, sy(3) - 1.6, 6, 2.6, stroke=0, fill=1)
                continue
            if e["strum"]:
                a, b = e["rng"]
                ya, yb = sy(a) + 1, sy(b) - 1
                c.setLineWidth(0.7)
                c.line(ex - 3.6, ya, ex - 3.6, yb)
                tip = ya if e["strum"] == "up" else yb
                dirn = 1 if e["strum"] == "up" else -1
                p = c.beginPath()
                p.moveTo(ex - 3.6, tip + dirn * 1)
                p.lineTo(ex - 5.4, tip - dirn * 3)
                p.lineTo(ex - 1.8, tip - dirn * 3)
                p.close()
                c.drawPath(p, stroke=0, fill=1)
                c.setLineWidth(0.5)
            if e["slap"]:
                c.setFont("YHB", 8)
                c.drawCentredString(ex, sy(1) + 4.5, "*")
            if e["arp"]:
                strs = [s for s, _ in e["n"]] or [2, 5]
                ya, yb = sy(min(strs)) + 2, sy(max(strs)) - 2
                p = c.beginPath()
                yy = ya
                p.moveTo(ex - 6, yy)
                k = 0
                while yy - 2 > yb:
                    p.lineTo(ex - 6 + (1.5 if k % 2 == 0 else -1.5), yy - 1.5)
                    yy -= 1.5
                    k += 1
                c.setLineWidth(0.6)
                c.drawPath(p)
                p2 = c.beginPath()
                p2.moveTo(ex - 6, ya + 1.5)
                p2.lineTo(ex - 7.8, ya - 1.5)
                p2.lineTo(ex - 4.2, ya - 1.5)
                p2.close()
                c.drawPath(p2, stroke=0, fill=1)
                c.setLineWidth(0.5)
            for s, txt in e["n"]:
                yy = sy(s)
                if txt == X:
                    c.setLineWidth(0.7)
                    c.line(ex - 1.9, yy - 1.9, ex + 1.9, yy + 1.9)
                    c.line(ex - 1.9, yy + 1.9, ex + 1.9, yy - 1.9)
                    c.setLineWidth(0.5)
                else:
                    c.setFont("YH", 6.8)
                    tw = pdfmetrics.stringWidth(txt, "YH", 6.8)
                    c.setFillColorRGB(*(tint or (1, 1, 1)))
                    c.rect(ex - tw / 2 - 0.6, yy - 2.6, tw + 1.2, 5.4, stroke=0, fill=1)
                    c.setFillColorRGB(0, 0, 0)
                    c.drawCentredString(ex, yy - 2.3, txt)
                for (ps, px, kind, lab) in [p for p in pending if p[0] == s]:
                    arc(c, px, ex, yy + 3.2, lab)
                    pending.remove((ps, px, kind, lab))
            for s, _ in e["n"]:
                if e["tech"]:
                    pending.append((s, ex, "tech", e["tech"].upper()))
                if e["tie"] and s == min(s2 for s2, _ in e["n"]):
                    pending.append((s, ex, "tie", ""))
        # stems & beams
        t = 0
        groups = {}
        for e, ex in zip(bar, xs):
            groups.setdefault(int(t // 4), []).append((e, ex))
            t += e["d"]
        for g in groups.values():
            g = [(e, ex) for e, ex in g if not e["rest"]]
            if not g:
                continue
            for e, ex in g:
                bot = stem_bot if e["d"] < 8 else stem_top - 8
                if e["d"] < 16:
                    c.line(ex, stem_top, ex, bot)
                if e["d"] in (3, 6, 12):
                    c.circle(ex + 2.5, bot + 2, 0.7, stroke=0, fill=1)
            short = [(e, ex) for e, ex in g if e["d"] < 4]
            if len(short) >= 2:
                c.setLineWidth(1.6)
                c.line(short[0][1], stem_bot, short[-1][1], stem_bot)
                for i in range(len(short) - 1):
                    if short[i][0]["d"] == 1 and short[i + 1][0]["d"] == 1:
                        c.line(short[i][1], stem_bot + 3, short[i + 1][1], stem_bot + 3)
                    elif short[i][0]["d"] == 1 and (i == 0 or short[i - 1][0]["d"] != 1):
                        c.line(short[i][1], stem_bot + 3, short[i][1] + 4, stem_bot + 3)
                    if i == len(short) - 2 and short[i + 1][0]["d"] == 1 and short[i][0]["d"] != 1:
                        c.line(short[i + 1][1] - 4, stem_bot + 3, short[i + 1][1], stem_bot + 3)
                c.setLineWidth(0.5)
            elif len(short) == 1:
                e, ex = short[0]
                c.setLineWidth(1.2)
                c.line(ex, stem_bot, ex + 4, stem_bot + 4)
                if e["d"] == 1:
                    c.line(ex, stem_bot + 3, ex + 4, stem_bot + 7)
                c.setLineWidth(0.5)
        # lyrics under the measure
        for fi, txt in bar.ly:
            i0 = int(fi)
            frac = fi - i0
            lx = xs[i0] + (frac * ((xs[i0 + 1] if i0 + 1 < n else bx + bw) - xs[i0]))
            c.setFont("YH", 7.6)
            c.drawString(lx - 3, stem_bot - 11, txt)
        xe = bx + bw
        c.setLineWidth(0.8)
        c.line(xe, y1, xe, y6)
        if bar.end == "double":
            c.line(xe - 2.5, y1, xe - 2.5, y6)
        c.setLineWidth(0.5)
    if final:
        c.setLineWidth(2.2)
        c.line(x0 + width - 1, y1, x0 + width - 1, y6)
        c.setLineWidth(0.5)
        c.line(x0 + width - 4, y1, x0 + width - 4, y6)


# ---------------------------------------------------------------- page flow
OUT = "平凡之路_吉他谱_大树+间奏solo.pdf"
c = canvas.Canvas(OUT, pagesize=A4)
c.setTitle("平凡之路 吉他弹唱谱（大树音乐屋编配 + 间奏 solo）")
page = [1]
y = [PH - MT]


def footer():
    c.setFont("YH", 7)
    c.setFillColorRGB(0.45, 0.45, 0.45)
    c.drawCentredString(PW / 2, 26, f"《平凡之路》吉他弹唱谱 · 正歌编配：大树音乐屋（转写） · 间奏 solo：按原曲 rap 段和声新编 · 第 {page[0]} 页")
    c.setFillColorRGB(0, 0, 0)


def need(h):
    if y[0] - h < MB:
        footer()
        c.showPage()
        page[0] += 1
        y[0] = PH - MT


def section(title, note=None, keep=110, color=RED):
    need(keep)
    w = label_box(c, title, ML, y[0] - 10, color=color)
    if note:
        c.setFont("YH", 7.6)
        c.setFillColorRGB(0.55, 0.2, 0.2)
        c.drawString(ML + w + 6, y[0] - 9, note)
        c.setFillColorRGB(0, 0, 0)
    y[0] -= 20


measure = [1]


def tab(bars, layout=None, ts=None, final=False, tint=None, diagrams=True):
    layout = layout or [4] * ((len(bars) + 3) // 4)
    i = 0
    for k in layout:
        chunk = bars[i:i + k]
        h = line_height(chunk, diagrams)
        need(h)
        draw_tab_line(c, chunk, ML, y[0], CW, diagrams=diagrams, first=(i == 0), final=final and i + k >= len(bars),
                      time_sig=(ts or chunk[0].ts) if i == 0 else None, measure_no=measure[0], tint=tint)
        i += k
        measure[0] += len(chunk)
        y[0] -= h


# ---- header
c.setFont("YHB", 24)
c.drawCentredString(PW / 2, y[0] - 20, "平凡之路")
c.setFont("YH", 9)
c.drawCentredString(PW / 2, y[0] - 38,
                    f"词：韩寒 / 朴树    曲 / 原唱：朴树    原调 A  选调 G  变调夹 {CAPO} 品    4/4    速度约 {TEMPO} 拍/分")
c.setFont("YH", 8)
c.setFillColorRGB(0.35, 0.35, 0.35)
c.drawCentredString(PW / 2, y[0] - 52, "前奏 / 主歌 / 副歌 / 尾声：大树音乐屋教学版编配    间奏 solo：替代原曲“向前走 就这么走”rap 段的新编指弹旋律")
c.setFillColorRGB(0, 0, 0)
y[0] -= 70

label_box(c, "和弦", ML, y[0] - 10)
cx = ML + 50
for name in ["Em", "Cadd9", "G6add9", "C", "G", "D/#F", "Em9(no5)/D"]:
    chord_diagram(c, name, cx, y[0], w=22, fs=8 if len(name) < 8 else 6.5)
    cx += 52
y[0] -= 50
c.setFont("YH", 7.2)
c.setFillColorRGB(0.35, 0.35, 0.35)
c.drawString(ML, y[0], "说明：× 表示弹奏当前和弦在该弦上的音；↑ 为下扫（低音弦→高音弦），↓ 为上扫；S 滑音。")
c.drawString(ML, y[0] - 11, "* （主歌二）：大拇指敲击 5、6 弦发出打击声，同时中指、无名指弹击 2、3 弦（或 3、4 弦），两个动作同时完成。")
c.drawString(ML, y[0] - 22, "第 29–36 小节（浅蓝底色）为新增间奏 solo，原曲此处为 rap，和声 D–F#m | A，G 调指法即 C–Em | G；弹完接尾声。")
c.setFillColorRGB(0, 0, 0)
y[0] -= 37

section("前奏")
tab(INTRO, ts=(4, 4))
section("A", "主歌一")
tab(VERSE1)
section("A'", "主歌二 · * 处拇指敲击 5、6 弦 + 中指无名指弹击 2、3 弦（或 3、4 弦）")
tab(VERSE2)
section("B", "副歌 · 扫弦")
tab(CHORUS)
section("间奏 Solo", "新编 · 替代原曲 rap 段（向前走 就这么走…）· 和弦 C–Em | G 循环四次", color=(0.2, 0.4, 0.75))
tab(SOLO, ts=(4, 4), tint=SOLO_TINT)
section("C", "尾声")
tab(OUTRO, layout=[4, 5], final=True)

footer()
c.save()
print("pages", page[0], "measures", measure[0] - 1)
