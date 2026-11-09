"""Typeset 《安和桥》: 大树音乐屋 verse/chorus arrangement + Mr.伊森 interlude."""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import math, re

pdfmetrics.registerFont(TTFont("YH", "C:/Windows/Fonts/msyh.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("YHB", "C:/Windows/Fonts/msyhbd.ttc", subfontIndex=0))

PW, PH = A4
ML, MR, MT, MB = 42, 42, 46, 50
CW = PW - ML - MR
GAP = 6.2          # distance between tab strings
X = "×"
RED = (0.82, 0.25, 0.3)

# ---------------------------------------------------------------- chords
# frets from string 6 to string 1; -1 = muted, 0 = open; base = first fret shown
CHORDS = {
    "G": ([3, 2, 0, 0, 0, 3], 1),
    "D/#F": ([2, -1, 0, 2, 3, 2], 1),
    "D9sus4": ([-1, 5, 4, 0, 3, 0], 3),
    "D": ([-1, -1, 0, 2, 3, 2], 1),
    "Em": ([0, 2, 2, 0, 0, 0], 1),
    "C": ([-1, 3, 2, 0, 1, 0], 1),
    "C9": ([-1, 3, 2, 0, 3, 0], 1),
    "Cadd9": ([-1, 3, 2, 0, 3, 0], 1),
    "Dadd9": ([-1, 5, 4, -1, 5, -1], 4),
    "Gadd9": ([3, 0, 0, 2, 0, 0], 1),
    "D/A": ([-1, 0, 0, 2, 3, -1], 1),
}


def chord_diagram(c, name, x, y, w=22, label=True, fs=7.5):
    """Draw diagram with top-left at (x, y) (y = top of the name)."""
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
            r = f - base
            c.circle(sx, gy - (r + 0.5) * cell_h, 1.6, stroke=0, fill=1)
    return fs + 6 + rows * cell_h + 2


# ---------------------------------------------------------------- tab model
def E(d, notes=(), chord=None, tech=None, tie=False, strum=None, arp=False, rest=False, harm=False, rng=(1, 6)):
    return dict(d=d, n=list(notes), chord=chord, tech=tech, tie=tie, strum=strum, arp=arp, rest=rest, harm=harm, rng=rng)


def label_box(c, text, x, y, fs=9):
    w = pdfmetrics.stringWidth(text, "YHB", fs) + 8
    c.setFillColorRGB(*RED)
    c.roundRect(x, y - 3, w, fs + 6, 2, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("YHB", fs)
    c.drawString(x + 4, y + 0.5, text)
    c.setFillColorRGB(0, 0, 0)
    return w


def draw_tab_line(c, bars, x0, ytop, width, diagrams=True, first=False, final=False, time_sig=None,
                  measure_no=None, repeat_end=False):
    """ytop = top of the whole system. Returns height used."""
    diag_h = 40 if diagrams else 12
    y1 = ytop - diag_h                     # string 1
    y6 = y1 - 5 * GAP                      # string 6
    sy = lambda s: y1 - (s - 1) * GAP
    head = 22 if first else 6
    weights = [max(len(b), 5) + 1.5 for b in bars]
    bws = [(width - head) * w / sum(weights) for w in weights]
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
    prev_pos = {}  # string -> (x, event) of previous note for techniques / ties
    pending = []   # (string, x_from, kind, label)
    for bi, bar in enumerate(bars):
        bx = x0 + head + sum(bws[:bi])
        bw = bws[bi]
        if measure_no is not None:
            c.setFont("YH", 5.5)
            c.drawString(bx + 1.5, y1 + 2, str(measure_no + bi))
        n = len(bar)
        step = (bw - 12) / max(n, 1)
        xs = [bx + 8 + step * (i + 0.15) for i in range(n)] if n > 1 else [bx + 10]
        # chord diagrams / names
        for e, ex in zip(bar, xs):
            if e["chord"]:
                if diagrams and e["chord"] in CHORDS:
                    chord_diagram(c, e["chord"], ex - 9, ytop, w=18, fs=7)
                else:
                    c.setFont("YHB", 8)
                    c.drawString(ex - 3, y1 + 8, e["chord"])
        # notes
        for e, ex in zip(bar, xs):
            if e["rest"]:
                c.rect(ex - 3, sy(3) - 1.6, 6, 2.6, stroke=0, fill=1)
                continue
            if e["strum"]:
                a, b = e["rng"]
                ya, yb = sy(a) + 1, sy(b) - 1
                c.setLineWidth(0.7)
                c.line(ex, ya, ex, yb)
                tip = ya if e["strum"] == "up" else yb
                dirn = 1 if e["strum"] == "up" else -1
                p = c.beginPath()
                p.moveTo(ex, tip + dirn * 1)
                p.lineTo(ex - 2, tip - dirn * 3.5)
                p.lineTo(ex + 2, tip - dirn * 3.5)
                p.close()
                c.drawPath(p, stroke=0, fill=1)
                c.setLineWidth(0.5)
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
                p2.moveTo(ex - 6, yb + 1)
                p2.lineTo(ex - 7.8, yb + 4)
                p2.lineTo(ex - 4.2, yb + 4)
                p2.close()
                c.drawPath(p2, stroke=0, fill=1)
                c.setLineWidth(0.5)
            for s, txt in e["n"]:
                yy = sy(s)
                if txt == X:
                    c.setLineWidth(0.7)
                    c.line(ex - 2.2, yy - 2.2, ex + 2.2, yy + 2.2)
                    c.line(ex - 2.2, yy + 2.2, ex + 2.2, yy - 2.2)
                    c.setLineWidth(0.5)
                else:
                    label = f"<{txt}>" if e["harm"] else txt
                    c.setFont("YH", 6.8)
                    tw = pdfmetrics.stringWidth(label, "YH", 6.8)
                    c.setFillColorRGB(1, 1, 1)
                    c.rect(ex - tw / 2 - 0.6, yy - 2.6, tw + 1.2, 5.4, stroke=0, fill=1)
                    c.setFillColorRGB(0, 0, 0)
                    c.drawCentredString(ex, yy - 2.3, label)
                # connect technique / tie from previous
                for (ps, px, kind, lab) in [p for p in pending if p[0] == s]:
                    arc(c, px, ex, yy + 3.2, lab)
                    pending.remove((ps, px, kind, lab))
            if e["harm"]:
                c.setFont("YH", 6)
                c.drawString(ex + 10, sy(1) + 3, "Harm. 12品泛音（延音）")
            for s, _ in e["n"]:
                if e["tech"]:
                    pending.append((s, ex, "tech", e["tech"].upper()))
                if e["tie"] and s == min(s2 for s2, _ in e["n"]):
                    pending.append((s, ex, "tie", ""))
        # stems & beams
        t = 0
        groups = {}
        for e, ex in zip(bar, xs):
            groups.setdefault(t // 4, []).append((e, ex))
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
        # bar line
        xe = bx + bw
        c.setLineWidth(0.8)
        c.line(xe, y1, xe, y6)
        c.setLineWidth(0.5)
    if final:
        c.setLineWidth(2.2)
        c.line(x0 + width - 1, y1, x0 + width - 1, y6)
        c.setLineWidth(0.5)
        c.line(x0 + width - 4, y1, x0 + width - 4, y6)
    return diag_h + 5 * GAP + 26


def arc(c, xa, xb, y, label=""):
    p = c.beginPath()
    p.moveTo(xa + 1, y)
    p.curveTo(xa + 2, y + 4, xb - 2, y + 4, xb - 1, y)
    c.setLineWidth(0.5)
    c.drawPath(p)
    if label:
        c.setFont("YH", 5.5)
        c.drawCentredString((xa + xb) / 2, y + 4.2, label)


# ---------------------------------------------------------------- chord-over-lyrics
def chord_lyric_line(c, text, x, y, fs=10.5):
    """text like '[G]让我再看你一[D/#F]遍' ; chord sits above the following char."""
    parts = re.split(r"(\[[^\]]+\])", text)
    cx = x
    chord = None
    last_chord_end = -1e9
    for p in parts:
        if not p:
            continue
        if p.startswith("["):
            chord = p[1:-1]
            continue
        for ch in p:
            w = pdfmetrics.stringWidth(ch, "YH", fs)
            if chord:
                cxx = max(cx, last_chord_end + 3)
                c.setFont("YHB", 9)
                c.setFillColorRGB(0.1, 0.2, 0.55)
                c.drawString(cxx, y + fs + 2, chord)
                c.setFillColorRGB(0, 0, 0)
                last_chord_end = cxx + pdfmetrics.stringWidth(chord, "YHB", 9)
                chord = None
            c.setFont("YH", fs)
            c.drawString(cx, y, ch)
            cx += w + (2 if ch != " " else 4)
    if chord:
        c.setFont("YHB", 9)
        c.setFillColorRGB(0.1, 0.2, 0.55)
        c.drawString(max(cx + 4, last_chord_end + 3), y + fs + 2, chord)
        c.setFillColorRGB(0, 0, 0)
    return fs + 16


# ---------------------------------------------------------------- music data
def two(a, b):
    return a + b


# Prelude (大树音乐屋)
P1 = [E(2, [(6, X)], "G"), E(2, [(4, X)]), E(2, [(2, X)]), E(2, [(4, X)]),
      E(2, [(3, X), (6, X)], "D/#F"), E(2, [(4, X)]), E(2, [(2, "0")]), E(2, [(4, X)])]
P2 = [E(2, [(6, X), (3, X)], "Em"), E(2, [(4, "2")], tech="s"), E(2, [(4, "4")]), E(2, [(3, X)]),
      E(2, [(4, "4")], tech="s"), E(2, [(4, "2")]), E(4, [(4, "0")])]
P3 = [E(2, [(5, X)], "Cadd9"), E(2, [(4, X)]), E(2, [(2, X)]), E(2, [(4, X)]),
      E(2, [(5, X)], "Dadd9"), E(2, [(4, X)]), E(2, [(2, X)]), E(2, [(3, "0")])]
P4 = [E(2, [(6, X)], "Gadd9"), E(2, [(4, X)]), E(2, [(3, X)]), E(2, [(2, X)], tie=True),
      E(2, [(2, X)]), E(2, [(4, X)]), E(2, [(3, X)]), E(2, [(4, X)])]
P8 = [E(2, [(6, X)], "Gadd9"), E(2, [(4, X)]), E(2, [(3, X)]), E(2, [(2, X)], tie=True),
      E(4, [(2, X)]), E(4, rest=True)]

# A-section ending lick on Em (大树音乐屋)
EM_END = [E(2, [(6, X)], "Em"), E(2, [(4, X)]), E(2, [(3, X)]), E(2, [(2, X)]),
          E(4, [(2, X), (3, X), (4, X), (5, X)], arp=True, tie=True), E(4, [(2, X), (3, X), (4, X), (5, X)], arp=True)]

# Rhythm pattern ①  (bass – 3 – 1+2 – 3), shown on G like the video
R1 = [E(2, [(6, X)], "G"), E(2, [(3, X)]), E(2, [(1, X), (2, X)]), E(2, [(3, X)]),
      E(2, [(6, X)]), E(2, [(3, X)]), E(2, [(1, X), (2, X)]), E(2, [(3, X)])]
# Rhythm pattern ②  (strum)
R2 = [E(4, strum="up"), E(2, strum="up"), E(1, strum="up", rng=(1, 4)), E(1, strum="down", rng=(1, 4)),
      E(1, strum="up"), E(1, strum="down", rng=(1, 4)), E(2, strum="up"),
      E(2, strum="up"), E(1, strum="up", rng=(1, 4)), E(1, strum="down", rng=(1, 4))]

# Interlude (transcribed from Mr.伊森 short, G shapes; original video capo 1)
I1 = [E(2, [(6, "0")], "Em"), E(1, [(3, "2")], tech="h"), E(1, [(3, "4")]), E(2, [(1, "0")]), E(2, [(1, "0")]),
      E(2, [(5, "3"), (4, "2")], "C"), E(2, [(3, "0")]), E(2, [(1, "3"), (2, "0")]), E(1, [(3, "0")]), E(1, [(3, "2")])]
I2 = [E(1, [(5, "0"), (3, "2")], "D/A"), E(1, [(4, "0")]), E(2, [(5, "0")]), E(1, [(4, "0")]), E(1, [(3, "4"), (2, "3")]), E(2, [(4, "0")]),
      E(2, [(6, "3")], "G"), E(2, [(4, "0"), (2, "0")]), E(2, [(3, "0")]), E(2, [(4, "0")])]
I3 = [E(2, [(6, "0")], "Em"), E(1, [(3, "2")], tech="h"), E(1, [(3, "4")]), E(2, [(1, "0")]), E(1, [(1, "0")]), E(1, [(2, "3")]),
      E(2, [(5, "3"), (4, "2")], "C"), E(2, [(3, "0"), (1, "0")]), E(2, [(2, "0")]), E(1, [(3, "0")]), E(1, [(3, "2")])]
I4 = I2
I5 = [E(2, [(6, "0"), (4, "0")], "Em"), E(2, [(3, "0")]), E(1, [(1, "5")], tech="h"), E(1, [(1, "7")]), E(1, [(1, "5")], tech="p"), E(1, [(1, "3")]),
      E(2, [(5, "3")], "C"), E(2, [(3, "0")]), E(2, [(1, "3"), (2, "0")]), E(1, [(1, "3")], tech="h"), E(1, [(1, "5")])]
I6 = [E(2, [(4, "0"), (1, "5")], "D"), E(2, [(3, "0")]), E(1, [(1, "7")], tech="s"), E(1, [(1, "10")]), E(1, [(2, "0")]), E(1, [(3, "0")]),
      E(2, [(6, "0"), (1, "7")], "Em"), E(2, [(4, "2"), (3, "0")]), E(2, [(2, "0")]), E(1, [(3, "0")]), E(1, [(2, "0")])]
I7 = [E(2, [(6, "0")], "Em"), E(1, [(1, "10")], tech="h"), E(1, [(1, "12")]), E(2, [(1, "12")]), E(2, [(1, "12")]),
      E(2, [(5, "3"), (1, "5")], "C"), E(2, [(3, "0")]), E(1, [(1, "3"), (2, "0")]), E(1, [(2, "0")]), E(2, [(1, "3"), (3, "0")])]
I8 = [E(2, [(4, "0"), (1, "5")], "D"), E(2, [(1, "3"), (3, "0")]), E(2, [(1, "5")]), E(1, [(1, "5")], tech="h"), E(1, [(1, "7")]),
      E(2, [(6, "0"), (1, "7")], "Em"), E(2, [(1, "0")]), E(2, [(2, "0")]), E(1, [(3, "0")]), E(1, [(2, "0")])]
I9 = [E(16, [(1, "12"), (2, "12"), (3, "12")], "Em", harm=True)]

# ---------------------------------------------------------------- page flow
c = canvas.Canvas("安和桥_吉他弹唱谱_大树编配+伊森间奏.pdf", pagesize=A4)
c.setTitle("安和桥 吉他弹唱谱")
page = [1]
y = [PH - MT]


def footer():
    c.setFont("YH", 7)
    c.setFillColorRGB(0.45, 0.45, 0.45)
    c.drawCentredString(PW / 2, 26, f"《安和桥》吉他弹唱谱 · 正歌编配：大树音乐屋 · 间奏：Mr.伊森（转写） · 第 {page[0]} 页")
    c.setFillColorRGB(0, 0, 0)


def need(h):
    if y[0] - h < MB:
        footer()
        c.showPage()
        page[0] += 1
        y[0] = PH - MT


def section(title, note=None, keep=60):
    need(keep)
    w = label_box(c, title, ML, y[0] - 10)
    if note:
        c.setFont("YH", 8)
        c.setFillColorRGB(0.55, 0.2, 0.2)
        c.drawString(ML + w + 6, y[0] - 9, note)
        c.setFillColorRGB(0, 0, 0)
    y[0] -= 22


def tab(bars, per_line=4, measure_start=1, final=False, ts=None, diagrams=True, width=None):
    for i in range(0, len(bars), per_line):
        chunk = bars[i:i + per_line]
        w = (width or CW) * len(chunk) / per_line if len(chunk) < per_line and width is None else (width or CW)
        h = 40 + 5 * GAP + 30 if diagrams else 12 + 5 * GAP + 30
        need(h)
        draw_tab_line(c, chunk, ML, y[0], w, diagrams=diagrams, first=(i == 0), final=final and i + per_line >= len(bars),
                      time_sig=ts if i == 0 else None, measure_no=measure_start + i)
        y[0] -= h


def lyrics(lines):
    for ln in lines:
        need(30)
        y[0] -= chord_lyric_line(c, ln, ML + 14, y[0] - 22)
    y[0] -= 6


# ---- header
c.setFont("YHB", 24)
c.drawCentredString(PW / 2, y[0] - 20, "安和桥")
c.setFont("YH", 9)
c.drawCentredString(PW / 2, y[0] - 38, "词 / 曲 / 原唱：宋冬野    G 调指法    4/4    速度约 60 拍/分")
c.setFont("YH", 8)
c.setFillColorRGB(0.35, 0.35, 0.35)
c.drawCentredString(PW / 2, y[0] - 52, "前奏 / 主歌 / 副歌 / 尾奏：大树音乐屋教学版编配    间奏：Mr.伊森 演奏版（按视频转写）")
c.setFillColorRGB(0, 0, 0)
y[0] -= 70

# ---- chord chart
label_box(c, "和弦", ML, y[0] - 10)
cx = ML + 50
for name in ["G", "D/#F", "Em", "C", "C9", "D9sus4", "D", "Cadd9", "Dadd9", "Gadd9", "D/A"]:
    chord_diagram(c, name, cx, y[0], w=22, fs=8)
    cx += 44
y[0] -= 50
c.setFont("YH", 7.2)
c.setFillColorRGB(0.35, 0.35, 0.35)
c.drawString(ML, y[0], "说明：谱中 × 表示弹奏当前和弦在该弦上的音；↑ 为下扫（低音弦→高音弦），↓ 为上扫；S 滑音，H 击弦，P 勾弦。")
c.drawString(ML, y[0] - 11, "大树视频的和弦表中 D 给的是 D9sus4 指法，弹唱时用普通 D 和弦也可以；D/A 仅用于间奏。")
c.setFillColorRGB(0, 0, 0)
y[0] -= 28

# ---- prelude
section("前奏", "（A 段伴奏弹法与前奏相同）")
tab([P1, P2, P3, P4, P1, P2, P3, P8], ts=(4, 4))

# ---- A
section("A段", "主歌 · 节奏型同前奏（G–D/#F | Em | C9–D | G）")
lyrics([
    "[G]让我再看你一[D/#F]遍  从南[Em]到北  像是被[C9]五环[D]路  蒙住的  [G]双眼",
    "[G]请你再讲[D/#F]一遍  关[Em]于那天  抱着[C9]盒子的姑[D]娘  和擦汗的[Em]男人",
])
need(80)
c.setFont("YH", 8)
c.drawString(ML, y[0] - 4, "A 段结尾（“男人”处 Em 过门）：")
y[0] -= 14
draw_tab_line(c, [EM_END], ML, y[0], CW * 0.3, diagrams=False, first=True)
y[0] -= 12 + 5 * GAP + 34

# ---- B (pattern 1)
section("B段", "副歌 · 节奏型①（低音 – 3弦 – 1、2弦 – 3弦，低音弹和弦根音）")
need(70)
draw_tab_line(c, [R1], ML, y[0], CW * 0.32, diagrams=False, first=True)
c.setFont("YH", 7.5)
c.drawString(ML + CW * 0.34, y[0] - 30, "节奏型①：每个和弦弹半小节（4 个八分音符）")
y[0] -= 12 + 5 * GAP + 34
lyrics([
    "我知[C]道  那[D]些夏天  就[Em]像青春一[D]样回不来  [C]代替梦想[D]的也只能是勉为  [G]其难",
    "我知[C]道  吹过[D]的牛逼  也会[Em]随青春[D]一笑了之  让我[C]困在城[D]市里  纪[Em]念你",
])

# ---- A2
section("A段", "主歌 · 节奏型同前奏")
lyrics([
    "[G]让我再尝一[D/#F]口  秋[Em]天的酒  一直[C9]往南方[D]开  不会[G]太久",
    "[G]让我再听一[D/#F]遍  最美[Em]的那一句  你回家了  [C9]我在等你[D]呢  [Em]",
])
c.setFont("YH", 7.5)
c.drawString(ML + 14, y[0] + 2, "（结尾同样接 Em 过门）")
y[0] -= 10

# ---- interlude
section("间奏", "Mr.伊森 版（替换大树版的“重复前奏”）· 原视频夹 1 品，此处与全曲统一为 G 调指法")
tab([I1, I2, I3, I4, I5, I6, I7, I8, I9], per_line=5, ts=(4, 4))
need(20)
c.setFont("YH", 7.2)
c.setFillColorRGB(0.35, 0.35, 0.35)
c.drawString(ML, y[0] - 4, "第 9 小节：左手食指轻放 12 品品丝正上方，右手扫 1、2、3 弦弹出自然泛音，延音收尾，随后进入 B 段。")
c.setFillColorRGB(0, 0, 0)
y[0] -= 14

# ---- B (pattern 2) ×2
section("B段", "副歌 · 节奏型②（扫弦）")
need(70)
draw_tab_line(c, [R2], ML, y[0], CW * 0.42, diagrams=False, first=True)
y[0] -= 12 + 5 * GAP + 34
lyrics([
    "我知[C]道  那[D]些夏天  就[Em]像青春一[D]样回不来  [C]代替梦想[D]的也只能是勉为  [G]其难",
    "我知[C]道  吹过[D]的牛逼  也会[Em]随青春[D]一笑了之  让我[C]困在城[D]市里  纪[Em]念你",
    "我知[C]道  那[D]些夏天  就像[Em]你一样[D]回不来  我也[C]不会再对[D]谁  满怀  [G]期待",
    "我知[C]道  这[D]个世界  每天[Em]都有太多[D]遗憾  所以[C]你好[D]  再[Em]见",
])

# ---- outro
section("尾奏", keep=140)
tab([P1, P2, P3, P4], final=True, ts=(4, 4))

footer()
c.save()
print("pages", page[0])
