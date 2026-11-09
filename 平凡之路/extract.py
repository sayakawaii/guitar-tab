import cv2, os, numpy as np
os.makedirs("lines", exist_ok=True)
cap = cv2.VideoCapture("video.mp4")
dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
Y0, Y1, X0, X1 = 672, 1080, 0, 1920


def ink(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return (g < 110).astype(np.uint8)


prev = None
segs = []
t = 0.0
while t < dur:
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, f = cap.read()
    if not ok:
        break
    crop = f[Y0:Y1, X0:X1]
    m = ink(crop)
    if prev is None or (np.logical_xor(m, prev).sum() / max(m.sum() + prev.sum(), 1)) > 0.25:
        segs.append([t, t, crop.copy(), m])
        prev = m
    else:
        segs[-1][1] = t
        # keep the frame with the least highlight (most white background)
    t += 1.0

for i, (a, b, crop, m) in enumerate(segs):
    cv2.imwrite(f"lines/{i:03d}_{int(a):04d}-{int(b):04d}.png", crop)
print(len(segs))
