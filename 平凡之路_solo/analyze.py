import numpy as np, librosa, sys
y, sr = librosa.load("orig.wav", sr=22050)
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
bt = librosa.frames_to_time(beats, sr=sr)
print("tempo", tempo)
names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
ct = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=512)
print("global", dict(zip(names, np.round(chroma.mean(axis=1), 2))))

# simple triad templates
tmpl = {}
for r in range(12):
    for q, iv in (("", (0, 4, 7)), ("m", (0, 3, 7))):
        v = np.zeros(12)
        for i in iv:
            v[(r + i) % 12] = 1
        tmpl[names[r] + q] = v / np.linalg.norm(v)
a, b = float(sys.argv[1]), float(sys.argv[2])
sel = [t for t in bt if a <= t <= b]
print("beats in range", len(sel), "mean beat", np.diff(sel).mean())
for i in range(0, len(sel) - 1, 2):
    t0, t1 = sel[i], sel[min(i + 2, len(sel) - 1)]
    m = (ct >= t0) & (ct < t1)
    v = chroma[:, m].mean(axis=1)
    v = v / (np.linalg.norm(v) + 1e-9)
    best = sorted(tmpl, key=lambda k: -tmpl[k] @ v)[:2]
    print(f"{t0:7.2f}  {best[0]:4s} {best[1]:4s}")
