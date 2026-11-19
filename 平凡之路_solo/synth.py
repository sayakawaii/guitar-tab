"""Render a plucked-string preview of the tab in data.py (Karplus-Strong, sounding key A = capo 2)."""
import subprocess, sys
import numpy as np
import soundfile as sf
from scipy.signal import lfilter, resample_poly
import imageio_ffmpeg
from data import X, CHORDS, INTRO, VERSE1, VERSE2, CHORUS, SOLO, OUTRO, TEMPO, CAPO

SR = 88200                     # synthesize at 2x, downsample to 44.1k for better tuning of short delay lines
OPEN = {6: 40, 5: 45, 4: 50, 3: 55, 2: 59, 1: 64}
SIXTEENTH = 60 / TEMPO / 4
rng = np.random.default_rng(7)


def pluck(midi, dur, vel=0.8, bright=0.5, decay=0.996):
    f = 440 * 2 ** ((midi - 69) / 12)
    n = int(dur * SR)
    N = SR / f
    D = int(N - 0.6)
    frac = N - 0.5 - D                                   # remaining delay for the allpass, in [0.1, 1.1)
    ca = (1 - frac) / (1 + frac)
    exc = rng.uniform(-1, 1, D)
    exc = lfilter([bright, 1 - bright], [1], exc)        # soften attack
    x = np.zeros(n)
    x[:D] = exc[:min(D, n)]
    a = np.zeros(D + 3)
    a[0], a[1] = 1, ca
    a[D] -= decay * 0.5 * ca
    a[D + 1] -= decay * 0.5 * (1 + ca)
    a[D + 2] -= decay * 0.5
    y = lfilter([1, ca], a, x)
    rel = min(int(0.03 * SR), n)
    y[-rel:] *= np.linspace(1, 0, rel)
    return vel * y


def resolve(s, txt, chord):
    if txt == X:
        f = CHORDS[chord][0][6 - s]
        return None if f < 0 else f
    return int(txt)


def render(sections, lead_in=0.4, tail=3.0):
    bars = [b for sec in sections for b in sec]
    total = lead_in + sum(e["d"] for b in bars for e in b) * SIXTEENTH + tail
    out = np.zeros(int(total * SR) + SR)
    voices = {}                    # string -> (start sample, array) currently ringing
    notes = []                     # (string, start_t, midi, vel, stop_t_or_None, dur_hint)
    t = lead_in
    chord = None
    for b in bars:
        for e in b:
            if e["chord"]:
                chord = e["chord"]
            if not e["rest"] and e["n"]:
                strs = sorted(e["n"], key=lambda p: -p[0])          # low string first
                if e["strum"] == "down":
                    strs = strs[::-1]
                gap = 0.045 if e["arp"] else (0.012 if e["strum"] else 0.0)
                for k, (s, txt) in enumerate(strs):
                    fr = resolve(s, txt, chord)
                    if fr is None:
                        continue
                    vel = 0.55 if e["strum"] else 0.75
                    if e["strum"] == "down":
                        vel *= 0.8
                    notes.append(dict(s=s, t=t + k * gap, m=OPEN[s] + CAPO + fr, v=vel, acc=e["acc"]))
                if e["acc"]:
                    notes.append(dict(s=0, t=t + 0.05, m=None, v=0.5, acc=True))
            t += e["d"] * SIXTEENTH
    # each note rings until the same string is played again (or a muting slap)
    for i, nt in enumerate(notes):
        if nt["m"] is None:
            continue
        end = nt["t"] + 4.0
        for nx in notes[i + 1:]:
            if nx["s"] == nt["s"] or (nx["m"] is None and nx["t"] > nt["t"]):
                end = nx["t"] if nx["m"] is not None else min(end, nx["t"] + 0.02)
                break
        if nt["acc"]:
            end = min(end, nt["t"] + 0.06)
        dur = max(end - nt["t"], 0.05)
        y = pluck(nt["m"], dur + 0.03, nt["v"], bright=0.45 if nt["s"] >= 4 else 0.6)
        a = int(nt["t"] * SR)
        out[a:a + len(y)] += y[:len(out) - a]
    for nt in notes:
        if nt["m"] is None:                       # palm slap: short filtered noise burst
            n = int(0.04 * SR)
            burst = lfilter([0.3], [1, -0.7], rng.uniform(-1, 1, n)) * np.exp(-np.linspace(0, 6, n)) * 0.35
            a = int(nt["t"] * SR)
            out[a:a + n] += burst
    out = lfilter([1, 0.6, 0.2], [1], out)          # tiny body coloration
    out = resample_poly(out, 1, 2)
    out = out / (np.abs(out).max() + 1e-9) * 0.89
    return out[: int(total * 44100)]


def save(name, audio):
    sf.write(name + ".wav", audio, 44100)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", name + ".wav", "-b:a", "192k", name + ".mp3"], check=True)
    print(name, f"{len(audio) / 44100:.1f}s")


save("平凡之路_试听_全曲", render([INTRO, VERSE1, VERSE2, CHORUS, SOLO, OUTRO]))
save("平凡之路_试听_副歌尾+间奏solo", render([CHORUS[-2:], SOLO, OUTRO[:2]]))
