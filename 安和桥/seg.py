import cv2, numpy as np, os, shutil
cap = cv2.VideoCapture("main.mp4")
fps = cap.get(cv2.CAP_PROP_FPS)
Y0 = 280


def ink(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.dilate((g < 110).astype(np.uint8), np.ones((2, 2), np.uint8))


frames, i = [], 0
while True:
    if not cap.grab():
        break
    if i % int(fps // 2) == 0:
        _, f = cap.retrieve()
        frames.append((i / fps, f))
    i += 1

shutil.rmtree("seg", ignore_errors=True)
os.makedirs("seg")
segs, prev = [], None
for t, f in frames:
    # score area: bottom strip + left panel (chord/節奏 boxes); skip the video window
    reg = np.vstack([f[Y0:, :], cv2.resize(f[100:Y0, :190], (f.shape[1], 0 or 1)) * 0 + 255]) if False else f[Y0:, :]
    m = ink(reg)
    left = ink(f[100:Y0, :185])
    sig = (m, left)
    if prev is None:
        changed = True
    else:
        d1 = np.logical_xor(m, prev[0]).sum() / max(m.sum() + prev[0].sum(), 1)
        d2 = np.logical_xor(left, prev[1]).sum() / max(left.sum() + prev[1].sum(), 1)
        changed = d1 > 0.12 or d2 > 0.25
    if changed:
        segs.append([t, t, f])
        prev = sig
    else:
        segs[-1][1] = t
for k, (a, b, f) in enumerate(segs):
    if b - a >= 1.0:
        cv2.imwrite(f"seg/{k:03d}_{a:06.1f}-{b:06.1f}.png", f)
print(len(os.listdir("seg")))
