import cv2, os, sys
step = float(sys.argv[1]) if len(sys.argv) > 1 else 10
os.makedirs("samples", exist_ok=True)
cap = cv2.VideoCapture("video.mp4")
fps = cap.get(cv2.CAP_PROP_FPS)
n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(fps, n, cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
t = 0
while t * fps < n:
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, f = cap.read()
    if ok:
        small = cv2.resize(f, (480, int(480 * f.shape[0] / f.shape[1])))
        cv2.imwrite(f"samples/{int(t):04d}.jpg", small)
    t += step
