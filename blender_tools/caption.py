# Burn trend-style captions onto rendered frames and encode a vertical mp4.
# usage: python3 caption.py frames_dir out.mp4 fps "start:end:text" ...
import sys, os, glob, subprocess
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"

def burn(img, text):
    W, H = img.size
    d = ImageDraw.Draw(img)
    size = int(W * 0.085)
    f = ImageFont.truetype(FONT, size)
    tw = d.textlength(text, font=f)
    while tw > W * 0.86:
        size -= 2; f = ImageFont.truetype(FONT, size); tw = d.textlength(text, font=f)
    x = (W - tw) / 2; y = H * 0.70
    d.text((x, y), text, font=f, fill=(255, 255, 255), stroke_width=max(3, size // 9), stroke_fill=(0, 0, 0))
    return img

def main():
    src, out, fps = sys.argv[1], sys.argv[2], float(sys.argv[3])
    cues = []
    for c in sys.argv[4:]:
        a, b, t = c.split(":", 2); cues.append((int(a), int(b), t))
    frames = sorted(glob.glob(os.path.join(src, "*.png")))
    tmp = os.path.join(src, "_cap"); os.makedirs(tmp, exist_ok=True)
    for i, fp in enumerate(frames, 1):
        img = Image.open(fp).convert("RGB")
        for a, b, t in cues:
            if a <= i <= b: img = burn(img, t)
        img.save(os.path.join(tmp, "%04d.png" % i))
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "veryfast", out], check=True)
    print("wrote", out, len(frames), "frames")

if __name__ == "__main__":
    main()
