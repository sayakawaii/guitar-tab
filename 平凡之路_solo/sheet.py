import cv2, sys, numpy as np
src, step, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
tw = int(sys.argv[4]) if len(sys.argv) > 4 else 320
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS)
dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
print(src, fps, dur, cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
ims, t = [], 0.0
while t < dur:
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, f = cap.read()
    if ok:
        s = cv2.resize(f, (tw, int(tw * f.shape[0] / f.shape[1])))
        cv2.rectangle(s, (0, 0), (70, 18), (0, 255, 255), -1)
        cv2.putText(s, f"{t:.1f}", (2, 14), 0, 0.45, (0, 0, 0), 1)
        ims.append(s)
    t += step
cols = 6
per = cols * 6
for p in range(0, len(ims), per):
    chunk = ims[p:p + per]
    while len(chunk) % cols:
        chunk.append(np.full_like(ims[0], 255))
    rows = [np.hstack(chunk[i:i + cols]) for i in range(0, len(chunk), cols)]
    cv2.imwrite(f"{out}_{p // per}.jpg", np.vstack(rows))
