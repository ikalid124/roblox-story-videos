import os
BASE = os.path.join(os.path.expanduser("~"), "Downloads", "BalloonTest")
d = os.path.join(BASE, "frames_film"); n = z = 0
for name in os.listdir(d):
    p = os.path.join(d, name)
    try: f = int(name[2:6])
    except Exception: continue
    if 1281 <= f <= 2795: os.remove(p); n += 1
    elif os.path.getsize(p) == 0: os.remove(p); z += 1
open(os.path.join(BASE, "fixrange.txt"), "w").write("removed %d range, %d empty" % (n, z))
