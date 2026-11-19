"""Render a preview of the tab: data -> MIDI -> FluidSynth with a sampled steel-string guitar (sounding key A, capo 2).

python synth.py
Needs FluidSynth + GeneralUser-GS.sf2 (paths below, override with FLUIDSYNTH / SOUNDFONT env vars).
"""
import os, subprocess
import numpy as np
import mido
import soundfile as sf
import imageio_ffmpeg
from data import X, CHORDS, INTRO, VERSE1, VERSE2, CHORUS, SOLO, OUTRO, TEMPO, CAPO

HOME = os.path.expanduser("~")
FLUIDSYNTH = os.environ.get("FLUIDSYNTH", f"{HOME}/tools/fluidsynth/fluidsynth-v2.6.2-win10-x64-cpp11/bin/fluidsynth.exe")
SOUNDFONT = os.environ.get("SOUNDFONT", f"{HOME}/tools/GeneralUser-GS.sf2")
OPEN = {6: 40, 5: 45, 4: 50, 3: 55, 2: 59, 1: 64}
STEEL_GUITAR = 25            # GM program 26 "Acoustic Guitar (steel)"
KICK, SIDE_STICK = 36, 37     # GM drums: palm-heel hit = kick; thumb slap on strings 5-6 = side stick + soft kick
FINGER_SNAP_VEL = 68          # half the loudness of velocity 96 (SF2 gain ~ velocity^2)
SIXTEENTH = 60 / TEMPO / 4
rng = np.random.default_rng(11)


def resolve(s, txt, chord):
    if txt == X:
        f = CHORDS[chord][0][6 - s]
        return None if f < 0 else f
    return int(txt)


def collect(bars, lead_in=0.5):
    """-> guitar notes [dict(s, t, m, v, end?)], thumb slaps [(t, v)] and drum hits [(t, note, v)] in seconds."""
    notes, slaps, drums = [], [], []
    t, chord = lead_in, None
    for b in bars:
        pos = 0
        for e in b:
            if e["chord"]:
                chord = e["chord"]
            if not e["rest"] and e["n"]:
                on_beat = pos % 4 == 0
                start = t + rng.normal(0, 0.006)
                strs = sorted(e["n"], key=lambda p: -p[0])           # low string first
                if e["strum"] == "down":
                    strs = strs[::-1]
                if e["arp"]:
                    spread = 0.055
                elif e["slap"]:
                    spread = 0.004                       # fingers snap the two strings together
                elif e["strum"]:
                    spread = rng.uniform(0.010, 0.017)
                else:
                    spread = 0.0
                k = 0
                if e["kick"]:
                    drums.append((start, KICK, 92))
                if e["slap"]:
                    slaps.append((start - 0.003, 78))
                    drums += [(start - 0.003, SIDE_STICK, 60), (start - 0.003, KICK, 34)]
                    for s in (6, 5):                     # short muted click of the slapped bass strings
                        fr = resolve(s, X, chord)
                        if fr is not None:
                            notes.append(dict(s=s, t=start - 0.003, m=OPEN[s] + CAPO + fr, v=45, end=start + 0.025))
                for s, txt in strs:
                    fr = resolve(s, txt, chord)
                    if fr is None:
                        continue
                    if e["slap"]:
                        v = FINGER_SNAP_VEL
                    elif e["strum"]:
                        v = (84 if on_beat else 68) if e["strum"] == "up" else 54
                        v -= 4 * k if e["strum"] == "up" else 0
                    else:
                        v = 88 if s >= 5 else (82 if s == 1 else 70)
                    v = int(np.clip(v + rng.normal(0, 5), 30, 120))
                    notes.append(dict(s=s, t=start + k * spread, m=OPEN[s] + CAPO + fr, v=v))
                    k += 1
            pos += e["d"]
            t += e["d"] * SIXTEENTH
    return notes, slaps, drums, t


def note_offs(notes, slaps):
    """A string rings until it is played again or 4 s pass; a thumb slap damps strings 5 and 6."""
    slap_times = sorted(ts for ts, _ in slaps)
    for i, n in enumerate(notes):
        if "end" in n:
            continue
        end = n["t"] + 4.0
        for nx in notes[i + 1:]:
            if nx["s"] == n["s"]:
                end = min(end, nx["t"] - 0.005)
                break
        if n["s"] >= 5:
            later = [ts for ts in slap_times if ts > n["t"] + 0.01]
            if later:
                end = min(end, later[0])
        n["end"] = max(end, n["t"] + 0.04)


def write_midi(notes, drums, path):
    tpq = 480
    sec_per_tick = 60 / TEMPO / tpq
    ev = []
    for n in notes:
        ev.append((n["t"], 1, mido.Message("note_on", channel=0, note=n["m"], velocity=n["v"])))
        ev.append((n["end"], 0, mido.Message("note_off", channel=0, note=n["m"], velocity=0)))
    for ts, drum, v in drums:
        ev.append((ts, 1, mido.Message("note_on", channel=9, note=drum, velocity=v)))
        ev.append((ts + 0.1, 0, mido.Message("note_off", channel=9, note=drum, velocity=0)))
    ev.sort(key=lambda x: (x[0], x[1]))
    mid = mido.MidiFile(ticks_per_beat=tpq)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(TEMPO)))
    tr.append(mido.Message("program_change", channel=0, program=STEEL_GUITAR))
    tr.append(mido.Message("control_change", channel=0, control=91, value=40))   # reverb send
    tr.append(mido.Message("control_change", channel=9, control=7, value=70))
    last = 0
    for ts, _, msg in ev:
        tick = max(int(round(ts / sec_per_tick)), last)
        tr.append(msg.copy(time=tick - last))
        last = tick
    mid.save(path)


def render(name, bars):
    notes, slaps, drums, end = collect(bars)
    note_offs(notes, slaps)
    write_midi(notes, drums, name + ".mid")
    subprocess.run([FLUIDSYNTH, "-ni", "-q", "-g", "0.7", "-r", "44100", "-F", name + ".wav", SOUNDFONT, name + ".mid"],
                   check=True, stdout=subprocess.DEVNULL)
    audio, sr = sf.read(name + ".wav")
    audio = audio[: int((end + 3.5) * sr)]
    fade = int(1.5 * sr)
    audio[-fade:] *= np.linspace(1, 0, fade)[:, None]
    audio = audio / (np.abs(audio).max() + 1e-9) * 0.9
    sf.write(name + ".wav", audio, sr)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", name + ".wav", "-b:a", "192k", name + ".mp3"], check=True)
    os.remove(name + ".mid")
    print(name, f"{len(audio) / sr:.1f}s")


render("平凡之路_试听_全曲", [*INTRO, *VERSE1, *VERSE2, *CHORUS, *SOLO, *OUTRO])
render("平凡之路_试听_主歌二", VERSE2)
render("平凡之路_试听_副歌尾+间奏solo", [*CHORUS[-2:], *SOLO, *OUTRO[:2]])
