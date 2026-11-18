import os
BASE = os.path.join(os.path.expanduser("~"), "Downloads", "BalloonTest")
d = os.path.join(BASE, "frames_film"); n = 0
for f in range(1281, 2796):
    p = os.path.join(d, "f_%04d.jpg" % f)
    if os.path.exists(p): os.remove(p); n += 1
open(os.path.join(BASE, "fixrange.txt"), "w").write("removed %d" % n)
