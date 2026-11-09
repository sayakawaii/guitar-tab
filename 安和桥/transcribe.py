import numpy as np, librosa, pretty_midi
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

_, midi, notes = predict("short.wav", ICASSP_2022_MODEL_PATH,
                         onset_threshold=0.5, frame_threshold=0.3, minimum_note_length=80)
midi.write("short.mid")
notes = sorted(notes, key=lambda n: (n[0], -n[2]))
names = lambda p: librosa.midi_to_note(p, unicode=False)
with open("notes.txt", "w") as f:
    for s, e, p, a, _ in notes:
        f.write(f"{s:6.2f} {e - s:5.2f} {names(p):>4} {p:3d} {a:.2f}\n")
print(len(notes))

y, sr = librosa.load("short.wav")
chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
print("chroma", dict(zip(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"], np.round(chroma, 2))))
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
print("tempo", tempo, "beats", np.round(librosa.frames_to_time(beats, sr=sr), 2))
