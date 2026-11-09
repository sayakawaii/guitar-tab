import librosa
rows = [l.split() for l in open("notes.txt")]
T0, STEP = 0.10, 0.4925  # eighth note
slots = {}
for s, d, n, p, a in rows:
    s, d, p, a = float(s), float(d), int(p) - 1, float(a)
    k = round((s - T0) / STEP * 2) / 2  # allow 16th
    slots.setdefault(k, []).append((p, d, a))
bar = None
for k in sorted(slots):
    b = int(k // 8)
    if b != bar:
        print(f"--- bar {b + 1}  ({T0 + b * 8 * STEP:.2f}s)")
        bar = b
    ns = sorted(slots[k], reverse=True)
    print(f"  {k % 8:4.1f}: " + "  ".join(f"{librosa.midi_to_note(p, unicode=False)}({d:.1f},{a:.1f})" for p, d, a in ns))
