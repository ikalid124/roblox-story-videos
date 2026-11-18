# Trend-style captions (1-3 words, pop-in, *highlight* in yellow) + SFX mix -> vertical mp4.
# usage: python3 caption2.py frames_dir out.mp4 fps cues.json
# cues.json: {"captions": [[start, end, "text with *key* word"], ...], "sfx": [[frame, "path.wav", gain], ...]}
import sys, os, glob, json, subprocess
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
YELLOW = (255, 221, 0)

def burn(img, text, age):
    W, H = img.size
    pop = {0: 0.78, 1: 1.12, 2: 1.04}.get(age, 1.0)
    words = text.split()
    size = int(W * 0.115 * pop)
    f = ImageFont.truetype(FONT, size)
    d = ImageDraw.Draw(img)
    plain = [w.strip("*") for w in words]
    space = d.textlength(" ", font=f)
    widths = [d.textlength(w, font=f) for w in plain]
    while sum(widths) + space * (len(words) - 1) > W * 0.9:
        size -= 3; f = ImageFont.truetype(FONT, size); space = d.textlength(" ", font=f); widths = [d.textlength(w, font=f) for w in plain]
    x = (W - (sum(widths) + space * (len(words) - 1))) / 2; y = H * 0.66 - size / 2
    hl = []; on = False
    for w in words:
        start = w.startswith("*"); on = on or start
        hl.append(on)
        if w.endswith("*") and (len(w) > 1 or not start): on = False
    for w, pw, ww, h in zip(words, plain, widths, hl):
        col = YELLOW if h else (255, 255, 255)
        d.text((x, y), pw, font=f, fill=col, stroke_width=max(4, size // 7), stroke_fill=(0, 0, 0))
        x += ww + space
    return img

def main():
    src, out, fps, cues = sys.argv[1], sys.argv[2], float(sys.argv[3]), json.load(open(sys.argv[4]))
    frames = sorted(glob.glob(os.path.join(src, "f_*.png")))
    tmp = os.path.join(src, "_cap"); os.makedirs(tmp, exist_ok=True)
    for i, fp in enumerate(frames, 1):
        img = Image.open(fp).convert("RGB")
        for a, b, t in cues.get("captions", []):
            if a <= i <= b: img = burn(img, t, i - a)
        img.save(os.path.join(tmp, "%04d.png" % i))
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "%04d.png")]
    sfx = cues.get("sfx", [])
    for _, p, _ in sfx: cmd += ["-i", p]
    dur = len(frames) / fps
    if sfx:
        parts = []
        for k, (fr, _, g) in enumerate(sfx, 1):
            ms = int((fr - 1) / fps * 1000)
            parts.append(f"[{k}:a]adelay={ms}|{ms},volume={g}[s{k}]")
        mix = "".join(f"[s{k}]" for k in range(1, len(sfx) + 1))
        parts.append(f"{mix}amix=inputs={len(sfx)}:normalize=0,atrim=0:{dur:.3f},apad=whole_dur={dur:.3f}[a]")
        cmd += ["-filter_complex", ";".join(parts), "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-b:a", "192k", "-ar", "44100"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "veryfast", "-shortest", out]
    subprocess.run(cmd, check=True)
    print("wrote", out, len(frames), "frames")

if __name__ == "__main__":
    main()
