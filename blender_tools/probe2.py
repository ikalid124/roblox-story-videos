import bpy, os, math
from bpy_extras import anim_utils
BASE = os.path.join(os.path.expanduser("~"), "Downloads", "BalloonTest")
bpy.ops.wm.open_mainfile(filepath=os.path.join(BASE, "balloon_film.blend"))
O = bpy.data.objects; out = []
r = O["Ezra_Root"]; ad = r.animation_data
cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
for fc in cb.fcurves:
    if fc.data_path == "rotation_euler" and fc.array_index == 2:
        out.append("rotz keys: " + " ".join("%d:%.0f" % (k.co.x, math.degrees(k.co.y)) for k in fc.keyframe_points))
    if fc.data_path == "location" and fc.array_index == 1:
        out.append("locy keys: " + " ".join("%d:%.1f" % (k.co.x, k.co.y) for k in fc.keyframe_points))
src = open(os.path.join(BASE, "tools", "film_shots5.py")).read()
out.append("file has 180: %s" % ("ez_k.z, 180" in src))
open(os.path.join(BASE, "probe.txt"), "w").write("\n".join(out))
