import numpy as np, librosa, sys, soundfile as sf
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

a, b = float(sys.argv[1]), float(sys.argv[2])
y, sr = librosa.load("orig.wav", sr=22050, offset=a, duration=b - a)
# isolate harmonic part, keep mid/high register where a lead line lives
yh = librosa.effects.harmonic(y)
sf.write("seg.wav", yh, sr)
_, midi, notes = predict("seg.wav", ICASSP_2022_MODEL_PATH, onset_threshold=0.55, frame_threshold=0.3,
                         minimum_note_length=100, minimum_frequency=180, maximum_frequency=1500)
notes = sorted(notes, key=lambda n: n[0])
BEAT = 0.714
T0 = float(sys.argv[3]) if len(sys.argv) > 3 else a
# top voice per 8th-note slot, transposed -2 (G shapes)
slots = {}
for s, e, p, amp, _ in notes:
    t = s + a
    k = round((t - T0) / (BEAT / 2))
    if amp < 0.3:
        continue
    if k not in slots or p > slots[k][0]:
        slots[k] = (p, e - s, amp)
bar = None
line = []
for k in sorted(slots):
    bi = k // 8
    if bi != bar:
        if line:
            print(f"bar {bar + 1:2d} ({T0 + bar * 8 * BEAT / 2:6.1f}s): " + " ".join(line))
        bar, line = bi, []
    p, d, amp = slots[k]
    line.append(f"{k % 8}:{librosa.midi_to_note(p - 2, unicode=False)}")
print(f"bar {bar + 1:2d}: " + " ".join(line))
