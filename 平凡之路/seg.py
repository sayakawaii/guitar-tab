import cv2, numpy as np, os, shutil, sys
crops = np.load("crops.npy", mmap_mode="r")
TH = float(sys.argv[1]) if len(sys.argv) > 1 else 0.1


def ink(img):
    g = cv2.cvtColor(np.ascontiguousarray(img), cv2.COLOR_BGR2GRAY)
    m = (g < 110).astype(np.uint8)
    return cv2.dilate(m, np.ones((3, 3), np.uint8))


masks = [ink(c) for c in crops]
diffs = []
for i in range(1, len(masks)):
    a, b = masks[i - 1], masks[i]
    diffs.append(np.logical_xor(a, b).sum() / max(a.sum() + b.sum(), 1))
diffs = np.array(diffs)
np.save("diffs.npy", diffs)
print(np.percentile(diffs, [50, 80, 90, 95, 98, 99]))

shutil.rmtree("lines", ignore_errors=True)
os.makedirs("lines")
segs = [[0, 0]]
for i, d in enumerate(diffs, start=1):
    if d > TH:
        segs.append([i, i])
    else:
        segs[-1][1] = i
segs = [s for s in segs if s[1] - s[0] >= 2]  # drop transitions (<1.5s)
for k, (a, b) in enumerate(segs):
    # pick the frame with the least highlight colour (most neutral pixels)
    best = min(range(a, b + 1), key=lambda j: (np.abs(crops[j][..., 1].astype(int) - crops[j][..., 2].astype(int)) > 12).sum())
    cv2.imwrite(f"lines/{k:03d}_{a/2:06.1f}-{b/2:06.1f}.png", crops[best])
print(len(segs))
