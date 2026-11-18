#!/usr/bin/env python3
"""Video quality / style metrics for comparing a render to a reference.
usage: analyze.py <video> <out_prefix>
Writes <out_prefix>_metrics.json, <out_prefix>_sheet.jpg (1 frame/2s), <out_prefix>_cuts.jpg (first frame of each shot)
"""
import sys, json, subprocess, cv2, numpy as np

path, out = sys.argv[1], sys.argv[2]
cap = cv2.VideoCapture(path)
fps = cap.get(cv2.CAP_PROP_FPS) or 30
W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=bit_rate,duration:stream=codec_name,bit_rate,codec_type",
                        "-of", "json", path], capture_output=True, text=True).stdout
pj = json.loads(probe) if probe else {}

import os; NW = int(os.environ.get("NW", 540))
sharp, sharp_full, bright, contr, sat, colorful, clipb, clipw, edge, diffs = [], [], [], [], [], [], [], [], [], []
hists, frames_small, idx = [], [], 0
prev = None
while True:
    ok, f = cap.read()
    if not ok: break
    g_full = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    if idx % 3 == 0:
        sharp_full.append(cv2.Laplacian(g_full, cv2.CV_64F).var())
    s = cv2.resize(f, (NW, int(H * NW / W)), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(s, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(s, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256]); cv2.normalize(h, h)
    hists.append(h)
    if prev is not None: diffs.append(float(np.mean(cv2.absdiff(g, prev))))
    prev = g
    if idx % 3 == 0:
        sharp.append(cv2.Laplacian(g, cv2.CV_64F).var())
        bright.append(g.mean()); contr.append(g.std())
        sat.append(hsv[..., 1].mean())
        b, gg, r = [c.astype(float) for c in cv2.split(s)]
        rg, yb = r - gg, 0.5 * (r + gg) - b
        colorful.append(np.sqrt(rg.std()**2 + yb.std()**2) + 0.3 * np.sqrt(rg.mean()**2 + yb.mean()**2))
        clipb.append((g < 8).mean()); clipw.append((g > 247).mean())
        edge.append((cv2.Canny(g, 80, 160) > 0).mean())
    if idx % int(round(fps * 2)) == 0: frames_small.append(cv2.resize(s, (180, int(s.shape[0] * 180 / NW))))
    idx += 1
N = idx
# shot detection: histogram correlation drop OR big luma jump
cuts = [0]
for i in range(1, N):
    c = cv2.compareHist(hists[i - 1], hists[i], cv2.HISTCMP_CORREL)
    if (c < 0.55 or diffs[i - 1] > 40) and i - cuts[-1] > 6: cuts.append(i)
shot_lens = np.diff(cuts + [N]) / fps
# motion within shots (exclude cut frames)
cutset = set(cuts)
inshot = [d for i, d in enumerate(diffs, 1) if i not in cutset]
static = np.mean(np.array(inshot) < 0.6)

def st(a): a = np.array(a, float); return {"mean": round(float(a.mean()), 3), "p10": round(float(np.percentile(a, 10)), 3), "p90": round(float(np.percentile(a, 90)), 3)}
m = {
    "file": path, "resolution": f"{W}x{H}", "fps": round(fps, 2), "frames": N, "duration_s": round(N / fps, 2),
    "bitrate_kbps": round(int(pj.get("format", {}).get("bit_rate", 0)) / 1000),
    "bits_per_pixel": round(int(pj.get("format", {}).get("bit_rate", 0)) / (W * H * fps), 4),
    "sharpness_native": st(sharp_full), "sharpness_at_540w": st(sharp), "brightness": st(bright), "contrast_std": st(contr),
    "saturation": st(sat), "colorfulness": st(colorful), "crushed_black_frac": st(clipb), "blown_white_frac": st(clipw),
    "edge_density": st(edge), "motion_mean_absdiff": st(inshot), "static_frame_frac": round(float(static), 3),
    "shots": len(cuts), "avg_shot_s": round(float(shot_lens.mean()), 2), "median_shot_s": round(float(np.median(shot_lens)), 2),
    "cuts_per_10s": round(len(cuts) / (N / fps) * 10, 2), "cut_times_s": [round(c / fps, 2) for c in cuts],
}
json.dump(m, open(out + "_metrics.json", "w"), indent=1)

def sheet(imgs, cols, name):
    if not imgs: return
    h = max(i.shape[0] for i in imgs); imgs = [cv2.copyMakeBorder(i, 0, h - i.shape[0], 0, 0, cv2.BORDER_CONSTANT) for i in imgs]
    rows = [imgs[k:k + cols] for k in range(0, len(imgs), cols)]
    rows[-1] += [np.zeros_like(imgs[0])] * (cols - len(rows[-1]))
    cv2.imwrite(name, np.vstack([np.hstack(r) for r in rows]), [cv2.IMWRITE_JPEG_QUALITY, 88])
sheet(frames_small, 10, out + "_sheet.jpg")
cap = cv2.VideoCapture(path); cf = []
for c in cuts[:60]:
    cap.set(cv2.CAP_PROP_POS_FRAMES, min(c + 3, N - 1)); ok, f = cap.read()
    if ok: cf.append(cv2.resize(f, (180, int(H * 180 / W))))
sheet(cf, 10, out + "_cuts.jpg")
print(json.dumps({k: v for k, v in m.items() if k != "cut_times_s"}, indent=1))
