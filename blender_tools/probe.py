import bpy, os, math
BASE = os.path.join(os.path.expanduser("~"), "Downloads", "BalloonTest")
bpy.ops.wm.open_mainfile(filepath=os.path.join(BASE, "balloon_film.blend"))
sc = bpy.context.scene; O = bpy.data.objects; out = []
for f in (1300, 1400, 1460, 1690, 2000, 2300, 2600):
    sc.frame_set(f); r = O["Ezra_Root"]
    out.append("%d loc=%s rotz=%.1f look=%s cam=%s" % (f, tuple(round(v, 1) for v in r.location), math.degrees(r.rotation_euler.z),
               tuple(round(v, 1) for v in O["Ezra_Look"].matrix_world.translation), sc.camera.name if sc.camera else None))
fwd = O["Ezra_Root"].matrix_world.to_3x3() @ __import__("mathutils").Vector((0, 1, 0))
out.append("fwd at last frame %s" % (tuple(round(v, 2) for v in fwd),))
c = O["Cam14"]; out.append("cam14 %s" % (tuple(round(v, 1) for v in c.matrix_world.translation),))
open(os.path.join(BASE, "probe.txt"), "w").write("\n".join(out))
