import os, zipfile
BASE = os.path.join(os.path.expanduser("~"), "Downloads", "BalloonTest")
d = os.path.join(BASE, "frames_film"); bad = []
z = os.path.join(BASE, "frames_film.zip")
with zipfile.ZipFile(z, "w", zipfile.ZIP_STORED) as zf:
    for f in range(1, 3165):
        p = os.path.join(d, "f_%04d.jpg" % f)
        if not os.path.exists(p) or os.path.getsize(p) == 0: bad.append(f); continue
        zf.write(p, os.path.basename(p))
open(os.path.join(BASE, "zip_status.txt"), "w").write("size %d bad %s" % (os.path.getsize(z), bad[:50]))
