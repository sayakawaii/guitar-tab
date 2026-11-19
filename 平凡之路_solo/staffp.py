"""Crop a score line image, overlay numbered string lines and x ruler for reading."""
import cv2, numpy as np, sys, glob
key, half, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
src = glob.glob(f"src_lines/{key}_*.png")[0]
im = cv2.imread(src)
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
d = (g[:, 600:1800] < 200).mean(axis=1)
rows = [y for y in range(5, len(d) - 1) if d[y] > 0.8 and d[y] >= d[y - 1] and d[y] >= d[y + 1]]
lines = []
for y in rows:
    if not lines or y - lines[-1] > 6:
        lines.append(y)
lines = [y for y in lines if y > 100][:6]
print(lines)
x0, x1 = (60, 1000) if half == 0 else (940, 1880)
c = im[120:, x0:x1].copy()
cols = [(0, 0, 255), (0, 170, 0), (255, 0, 0), (0, 140, 255), (200, 0, 200), (0, 160, 160)]
for i, y in enumerate(lines):
    yy = y - 120
    ov = c.copy()
    cv2.line(ov, (0, yy), (c.shape[1], yy), cols[i], 1)
    c = cv2.addWeighted(ov, 0.6, c, 0.4, 0)
    cv2.putText(c, str(i + 1), (2, yy + 5), 0, 0.5, cols[i], 2)
for x in range(0, c.shape[1], 20):
    cv2.line(c, (x, c.shape[0] - 6), (x, c.shape[0]), (0, 0, 255) if x % 100 == 0 else (150, 150, 150), 1)
    if x % 100 == 0:
        cv2.putText(c, str(x + x0), (x + 2, c.shape[0] - 8), 0, 0.4, (0, 0, 255), 1)
cv2.imwrite(out, c)
