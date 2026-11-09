import cv2, numpy as np, sys
src, y0, y1, x0, x1, out = sys.argv[1], *map(int, sys.argv[2:6]), sys.argv[6]
S = 3
im = cv2.imread("seg/" + src)[y0:y1, x0:x1]
im = cv2.resize(im, None, fx=S, fy=S, interpolation=cv2.INTER_LANCZOS4)
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
dark = (g < 150).mean(axis=1)
rows = [y for y in range(1, len(dark) - 1) if dark[y] > 0.55 and dark[y] >= dark[y - 1] and dark[y] >= dark[y + 1]]
lines = []
for y in rows:
    if not lines or y - lines[-1] > 4:
        lines.append(y)
print(lines)
colors = [(0, 0, 255), (0, 160, 0), (255, 0, 0), (0, 140, 255), (200, 0, 200), (120, 120, 0)]
for i, y in enumerate(lines[:6]):
    cv2.line(im, (0, y), (im.shape[1], y), colors[i], 1)
    cv2.putText(im, str(i + 1), (2, y + 5), 0, 0.5, colors[i], 2)
for x in range(0, im.shape[1], 30):
    cv2.putText(im, str(x // S + x0), (x, im.shape[0] - 3), 0, 0.3, (0, 0, 0), 1)
cv2.imwrite(out, im)
