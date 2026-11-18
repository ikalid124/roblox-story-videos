# Original synthesized meme-style SFX (no samples): boom, whoosh, sad wah, boing, sting, pop, ding.
import numpy as np, wave, os, sys
SR = 44100

def save(name, x, out):
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.9
    y = (x * 32767).astype(np.int16)
    with wave.open(os.path.join(out, name + ".wav"), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())

def t(d): return np.arange(int(SR * d)) / SR
def env(n, a, d): # attack, exponential decay
    tt = np.arange(n) / SR
    return np.minimum(tt / a, 1.0) * np.exp(-tt / d)

def reverb(x, decay=0.35, mix=0.35):
    ir_t = t(1.2); ir = np.random.RandomState(1).randn(len(ir_t)) * np.exp(-ir_t / decay)
    wet = np.convolve(x, ir)[:len(x) + len(ir_t)]
    wet = np.pad(wet, (0, len(x) + len(ir_t) - len(wet)))
    dry = np.concatenate([x, np.zeros(len(ir_t))])
    return dry * (1 - mix) + wet / (np.max(np.abs(wet)) + 1e-9) * np.max(np.abs(x)) * mix

def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR); y = np.zeros_like(x); s = 0.0
    for i in range(len(x)): s = (1 - a) * x[i] + a * s; y[i] = s
    return y

def boom():
    tt = t(1.4); f = 38 + 95 * np.exp(-tt * 9)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.35 * np.sin(2 * ph)
    x = np.tanh(x * 3.0) * env(len(tt), 0.004, 0.45)
    click = np.random.RandomState(2).randn(len(tt)) * env(len(tt), 0.0005, 0.012) * 0.6
    return reverb(x + lowpass(click, 3000), 0.5, 0.3)

def whoosh():
    tt = t(0.55); n = np.random.RandomState(3).randn(len(tt))
    shape = np.sin(np.pi * tt / tt[-1]) ** 2
    lo = lowpass(n, 900); hi = n - lowpass(n, 2500)
    mixw = tt / tt[-1]
    return (lo * (1 - mixw) + hi * 0.5 * mixw) * shape

def sad_wah():
    out = []
    for f0, d in ((392, 0.42), (370, 0.42), (349, 0.42), (330, 1.2)):
        tt = t(d); vib = 1 + (0.012 * np.sin(2 * np.pi * 5.5 * tt) if d > 1 else 0)
        f = f0 * vib * (1 - 0.05 * tt / d if d > 1 else 1)
        ph = 2 * np.pi * np.cumsum(f) / SR
        tone = sum(np.sin(k * ph) / k ** 1.1 for k in range(1, 9))
        wah = 0.55 + 0.45 * np.sin(2 * np.pi * (1.8 if d > 1 else 2.2) * tt - np.pi / 2)
        e = np.minimum(tt / 0.03, 1) * np.minimum((d - tt) / 0.06, 1)
        out.append(lowpass(tone * e, 700 + 2200 * wah.mean()) * (0.6 + 0.4 * wah))
    return reverb(np.concatenate(out), 0.3, 0.2)

def boing():
    tt = t(0.9); f = 180 + 260 * np.exp(-tt * 3) + 60 * np.sin(2 * np.pi * 9 * tt) * np.exp(-tt * 2.5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(len(tt), 0.003, 0.35)

def sting():
    tt = t(1.6); x = np.zeros_like(tt)
    for f in (466, 494, 523, 554):  # clustered strings, tremolo
        x += np.sign(np.sin(2 * np.pi * f * tt)) * 0.3 + np.sin(2 * np.pi * f * tt)
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * 14 * tt)
    e = np.minimum(tt / 0.02, 1) * np.exp(-tt / 0.9)
    return reverb(lowpass(x * trem * e, 3500), 0.6, 0.35)

def pop():
    tt = t(0.12); f = 900 * np.exp(-tt * 30) + 300
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.001, 0.03)

def ding():
    tt = t(1.0)
    return (np.sin(2 * np.pi * 1318 * tt) + 0.4 * np.sin(2 * np.pi * 2637 * tt)) * env(len(tt), 0.002, 0.3)

def laugh_hits():
    out = np.zeros(int(SR * 0.9))
    for i in range(5):
        p = pop() * (0.6 + 0.08 * i); s = int(SR * 0.16 * i); out[s:s + len(p)] += p
    return out

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for name, fn in (("boom", boom), ("whoosh", whoosh), ("sad_wah", sad_wah), ("boing", boing),
                     ("sting", sting), ("pop", pop), ("ding", ding), ("laugh_hits", laugh_hits)):
        save(name, fn(), out)
    print("ok")
