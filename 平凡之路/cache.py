import cv2, numpy as np
cap = cv2.VideoCapture("video.mp4")
fps = cap.get(cv2.CAP_PROP_FPS)
n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
step = int(fps // 2)
crops = []
i = 0
while True:
    ok = cap.grab()
    if not ok:
        break
    if i % step == 0:
        ok, f = cap.retrieve()
        crops.append(f[672:1080, :])
    i += 1
np.save("crops.npy", np.array(crops))
print(len(crops))
