"""Dump GP5 measures as text: python gpdump.py first last"""
import sys
import guitarpro as gp

s = gp.parse("平凡之路指弹改编版.gp5")
a, b = int(sys.argv[1]), int(sys.argv[2])
t = 0.0
tempo = s.tempo
for m, h in zip(s.tracks[0].measures, s.measureHeaders):
    num, den = h.timeSignature.numerator, h.timeSignature.denominator.value
    secs = num * (4 / den) * 60 / tempo
    if a <= h.number <= b:
        out = []
        for beat in m.voices[0].beats:
            d = beat.duration
            dur = f"{d.value}{'.' if d.isDotted else ''}{'t' if d.tuplet.enters != 1 else ''}"
            if beat.status == gp.BeatStatus.rest or not beat.notes:
                out.append(f"r/{dur}")
                continue
            ns = []
            for n in beat.notes:
                fx = n.effect
                tag = ""
                if n.type == gp.NoteType.dead:
                    tag = "x"
                if n.type == gp.NoteType.tie:
                    tag = "~"
                if fx.hammer:
                    tag += "h"
                if fx.slides:
                    tag += "s"
                if fx.harmonic:
                    tag += "<>"
                ns.append(f"{n.string}:{n.value}{tag}")
            out.append("+".join(ns) + f"/{dur}")
        print(f"{h.number:3d} {num}/{den} t={t:6.1f}s  " + "  ".join(out))
    t += secs
