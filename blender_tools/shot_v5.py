# v5: dialogue test with lip sync, per-line expressions and head acting (builds on the v4 scene).
import bpy, math, os, importlib
import expr2; importlib.reload(expr2)
sc = bpy.context.scene; O = bpy.data.objects; R = math.radians
base = expr2.BASE; vd = os.path.join(base, "voice")

# clear acting/expressions/camera keys from v4 (keep balloon sway)
for o in O:
    if o.animation_data and (o.name.split("_")[0] in ("Maya", "Ezra") and "Balloon" not in o.name or o.name in ("Cam_A", "Cam_B")):
        o.animation_data_clear()
for n in ("Cam_A", "Cam_B"):
    O[n].data.animation_data_clear(); O[n].data.lens = 38
for n in ("Maya_Head", "Ezra_Head", "Maya_UpperTorso", "Ezra_UpperTorso", "Maya_LeftUpperArm", "Ezra_LeftUpperArm"):
    O[n].rotation_euler = (0, 0, 0)
O["Maya_RightUpperArm"].rotation_euler = (R(32), 0, R(8)); O["Ezra_RightUpperArm"].rotation_euler = (R(30), 0, R(6))
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)

END = 285
sc.frame_start, sc.frame_end = 1, END
for f, c in ((1, "Cam_A"), (82, "Cam_B"), (182, "Cam_A")):
    m = sc.timeline_markers.new("cut%d" % f, frame=f); m.camera = O[c]

def rk(obj, f, x=0, y=0, z=0):
    o = O[obj]; o.rotation_euler = (R(x), R(y), R(z)); o.keyframe_insert("rotation_euler", frame=f)

def nods(head, start, length, pose, amp=4, every=11):
    """Small talking nods layered on a held head pose (x, y, z degrees)."""
    x, y, z = pose; f = start; i = 0
    while f < start + length:
        rk(head, f, x + (amp if i % 2 else 0), y, z); f += every; i += 1
    rk(head, start + length, x, y, z)

# ---- line 1: Maya, confused, glancing at Ezra's balloons ----
expr2.key("Maya", 1, "neutral")
n1 = expr2.lipsync("Maya", os.path.join(vd, "maya1.wav"), 6, "confused")
rk("Maya_Head", 1, 0, 0, 0); nods("Maya_Head", 6, n1, (6, 8, 10))
# Ezra listening, smug
expr2.key("Ezra", 1, "smug"); rk("Ezra_Head", 1, 6, 0, 10)

# ---- line 2: Ezra, smug, explains ----
n2 = expr2.lipsync("Ezra", os.path.join(vd, "ezra1.wav"), 86, "smug")
nods("Ezra_Head", 86, n2, (8, 0, 6), amp=5, every=10)
for f, x in ((86, 0), (100, -4), (115, 0), (130, -4), (150, 0), (179, 0)):
    rk("Ezra_UpperTorso", f, x)
expr2.key("Ezra", 86 + n2 + 2, "laughing")

# ---- line 3: Maya, sad, looks at her one balloon ----
expr2.key("Maya", 182, "sad")
for f, x, z in ((182, 4, 0), (190, 12, -16), (206, 12, -16), (214, 2, 0)):
    rk("Maya_Head", f, x, 0, z)
n3 = expr2.lipsync("Maya", os.path.join(vd, "maya2.wav"), 214, "sad")
nods("Maya_Head", 214, n3, (2, 0, 0), amp=3, every=12)
expr2.key("Maya", 214 + n3 + 4, "crying")
rk("Maya_Head", 214 + n3 + 4, -6, 0, 0); rk("Maya_Head", END, -8, 0, 0)

# ---- cameras: slow push-ins ----
for c, keys in (("Cam_A", ((1, 36), (81, 40), (182, 38), (END, 50))), ("Cam_B", ((82, 38), (181, 45)))):
    for f, v in keys:
        O[c].data.lens = v; O[c].data.keyframe_insert("lens", frame=f)

# idle bob
for root in (O["Maya_Root"], O["Ezra_Root"]):
    z0 = 0.0
    for i, f in enumerate(range(1, END + 1, 15)):
        root.location.z = z0 + (0.006 if i % 2 else 0); root.keyframe_insert("location", index=2, frame=f)

fr = os.path.join(base, "frames_v5"); os.makedirs(fr, exist_ok=True)
for f in os.listdir(fr): os.remove(os.path.join(fr, f))
sc.render.filepath = os.path.join(fr, "f_####"); sc.render.resolution_percentage = 50
sc.camera = O["Cam_A"]
print("lines", n1, n2, n3, "maya2 starts", 214)
