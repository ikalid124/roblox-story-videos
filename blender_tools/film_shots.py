# Stage 2 of "The balloons": balloons, shots, cameras, acting, expressions, lip sync, lighting.
import bpy, bmesh, os, sys, math, json, random, importlib, traceback
from mathutils import Vector
from bpy_extras import anim_utils

BASE = os.path.join(os.path.expanduser("~"), "Downloads", "BalloonTest")
TOOLS = os.path.join(BASE, "tools")
if TOOLS not in sys.path: sys.path.insert(0, TOOLS)
import expr2, expr3
importlib.reload(expr2); importlib.reload(expr3)
LOG = open(os.path.join(BASE, "film_log2.txt"), "w")
def log(*a): print(*a, file=LOG, flush=True)
R = math.radians

bpy.ops.wm.open_mainfile(filepath=os.path.join(BASE, "balloon_film.blend"), load_ui=False)
sc = bpy.context.scene; O = bpy.data.objects
TM = json.load(open(os.path.join(BASE, "voice", "timing_s1.json")))
N = TM["frames"]
def F(i): return int(i) + 1                     # timing index -> blender frame
MASK = []
v = 0
for r in TM["mouth_rle"]: MASK += [v] * r; v ^= 1

CAST = ["Maya", "Ezra", "Grandpa", "KidA", "KidB", "Teacher", "Principal", "Photographer", "Dad", "Kid3"]
C = Vector((60, 0, 0)); H = Vector((60, 30, 0)); K = Vector((-60, 0, 0))
OFF = Vector((500, 500, -100))
random.seed(7)

def lin(c): return tuple(pow(x / 255.0, 2.2) for x in c)

# ---------- keyframe helpers ----------
def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    return cb.fcurves if cb else []

def kf(idb, path, f, interp='CONSTANT', index=-1):
    idb.keyframe_insert(path, index=index, frame=f)
    for fc in fcurves(idb):
        if fc.data_path == path and (index == -1 or fc.array_index == index):
            for kp in fc.keyframe_points:
                if abs(kp.co.x - f) < 0.5: kp.interpolation = interp

def rot(obj, f, x=0, y=0, z=0, interp='BEZIER'):
    o = O[obj] if isinstance(obj, str) else obj
    o.rotation_euler = (R(x), R(y), R(z)); kf(o, "rotation_euler", f, interp)

def vis(o, f, show):
    o.hide_render = not show; o.hide_viewport = not show
    kf(o, "hide_render", f); kf(o, "hide_viewport", f)

def root(n): return O[n + "_Root"]

# ---------- balloons ----------
BCOL = [(235, 60, 60), (60, 130, 240), (250, 210, 50), (70, 200, 90), (245, 120, 190), (255, 150, 40), (150, 90, 230), (60, 210, 220)]
PROPS = bpy.data.collections.get("FilmProps") or bpy.data.collections.new("FilmProps")
if PROPS.name not in sc.collection.children: sc.collection.children.link(PROPS)
_lat = {}
def latex(rgb):
    if rgb not in _lat:
        m = bpy.data.materials.new("Latex_%d_%d_%d" % rgb); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*lin(rgb), 1); b.inputs["Roughness"].default_value = 0.18
        try: b.inputs["Coat Weight"].default_value = 0.4
        except Exception: pass
        _lat[rgb] = m
    return _lat[rgb]
SMAT = bpy.data.materials.new("String"); SMAT.use_nodes = True
SMAT.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.85, 0.85, 0.85, 1)


def mesh_obj(name, kind, loc, **kw):
    bm = bmesh.new()
    if kind == "sphere": bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1.0)
    elif kind == "cone": bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=kw["r1"], radius2=kw["r2"], depth=kw["depth"])
    elif kind == "cube": bmesh.ops.create_cube(bm, size=1.0)
    elif kind == "ico": bmesh.ops.create_icosphere(bm, subdivisions=1, radius=kw["radius"])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); PROPS.objects.link(o); o.location = loc
    return o

def link(o):
    for c in o.users_collection: c.objects.unlink(o)
    PROPS.objects.link(o)

def balloon(name, center, grip, rgb, parent, r=0.15):
    s = mesh_obj(name, "sphere", center); s.scale = (r, r, r * 1.18)
    for p in s.data.polygons: p.use_smooth = True
    s.data.materials.append(latex(rgb))
    k = mesh_obj(name + "_knot", "cone", center - Vector((0, 0, r * 1.22)), r1=r * 0.16, r2=r * 0.03, depth=r * 0.25); k.rotation_euler = (math.pi, 0, 0); k.data.materials.append(latex(rgb))
    cu = bpy.data.curves.new(name + "_str", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.003
    sp = cu.splines.new('POLY'); sp.points.add(1)
    a = center - Vector((0, 0, r * 1.3)); sp.points[0].co = (*a, 1); sp.points[1].co = (*grip, 1)
    st = bpy.data.objects.new(name + "_str", cu); sc.collection.objects.link(st); cu.materials.append(SMAT)
    link(st)
    for o in (s, k, st):
        o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    return (s, k, st)

HOLD = {"Ezra": (170, 0, -4)}
BUNDLES = {}
def bundle(n, count, colors=None, spread=0.35, lift=1.0, r=0.14):
    hand = O[n + "_RightHand"]
    ua = O[n + "_RightUpperArm"]; ua.rotation_euler = tuple(R(a) for a in HOLD.get(n, (30, 0, 6)))
    bpy.context.view_layer.update()
    grip = hand.matrix_world @ Vector((0, 0, -0.05))
    e = bpy.data.objects.new(n + "_Sway", None); PROPS.objects.link(e); e.location = grip
    e.parent = hand; e.matrix_parent_inverse = hand.matrix_world.inverted()
    bpy.context.view_layer.update()
    up = Vector((0, 0, lift)) if n != "Ezra" else Vector((0, 0, 0.9))
    items = []
    for i in range(count):
        if count == 1: off = Vector((0.05, 0.05, 0))
        else:
            a = random.uniform(0, 2 * math.pi); rr = spread * math.sqrt(random.random())
            off = Vector((math.cos(a) * rr, math.sin(a) * rr * 0.8, random.uniform(-0.1, 0.25 + count * 0.012)))
        col = colors[i % len(colors)] if colors else BCOL[random.randrange(len(BCOL))]
        items.append(balloon("%s_B%02d" % (n, i), grip + up + off, grip, col, e, r=random.uniform(r * 0.9, r * 1.08)))
    BUNDLES[n] = (e, items)
    return items

def pop(n, idx, f):
    for o in BUNDLES[n][1][idx]:
        vis(o, f - 1, True); vis(o, f, False)

COUNTS = {"Maya": 1, "Ezra": 42, "Grandpa": 11, "KidA": 3, "KidB": 2, "Teacher": 3, "Principal": 9, "Photographer": 2, "Dad": 2, "Kid3": 18}
for n, c in COUNTS.items():
    if n == "Maya": bundle(n, 1, [(150, 150, 158)], r=0.16)
    elif n == "Ezra": bundle(n, 42, spread=0.75, r=0.13)
    else: bundle(n, c, spread=0.25 + c * 0.03)
log("balloons", {n: len(v[1]) for n, v in BUNDLES.items()})

# sway (stronger wind on the cliff)
for n, (e, _) in BUNDLES.items():
    for i, f in enumerate(range(1, N + 40, 22)):
        wind = 3.5 if F(1280) <= f <= F(1454) else 1.0
        a = (3 if i % 2 else -3) * wind
        e.rotation_euler = (R(a * 0.6), R(a), 0); kf(e, "rotation_euler", f, 'BEZIER')

# ---------- props ----------
def boxp(name, size, loc, rgb, parent=None):
    o = mesh_obj(name, "cube", loc)
    o.scale = size; m = bpy.data.materials.new(name); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*lin(rgb), 1); o.data.materials.append(m)
    if parent:
        bpy.context.view_layer.update(); o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o

LAD = C + Vector((0, -1.0, 0))
for sx in (-0.35, 0.35):
    boxp("Ladder_Rail%+.0f" % (sx * 10), (0.07, 0.07, 1.25), LAD + Vector((sx, 0, 0.62)), (190, 150, 60))
for k in range(4):
    boxp("Ladder_Step%d" % k, (0.75, 0.25, 0.05), LAD + Vector((0, 0, 0.3 + k * 0.3)), (190, 150, 60))
bpy.context.view_layer.update()
camprop = boxp("PhotoCam", (0.22, 0.14, 0.14), O["Photographer_LeftHand"].matrix_world.translation + Vector((0, 0.1, 0)), (25, 25, 28), O["Photographer_LeftHand"])
suitcase = boxp("Suitcase", (0.5, 0.18, 0.38), O["Dad_LeftHand"].matrix_world.translation - Vector((0, 0, 0.25)), (120, 70, 40), O["Dad_LeftHand"])
papers = []
for i in range(8):
    p = mesh_obj("Paper%d" % i, "ico", OFF, radius=0.07)
    m = bpy.data.materials.get("PaperMat") or bpy.data.materials.new("PaperMat"); m.use_nodes = True
    p.data.materials.append(m); papers.append(p)
_anc = bpy.data.objects.new("EndAnchor", None); PROPS.objects.link(_anc)
endb = balloon("EndBalloon", Vector((0, 0, 0)), Vector((0, 0, -1.0)), (150, 150, 158), _anc, r=0.17)

def rope(name, a, b):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.012
    sp = cu.splines.new('POLY'); sp.points.add(1); sp.points[0].co = (*a, 1); sp.points[1].co = (*b, 1)
    m = bpy.data.materials.get("RopeMat") or bpy.data.materials.new("RopeMat"); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*lin((200, 170, 120)), 1)
    cu.materials.append(m); o = bpy.data.objects.new(name, cu); PROPS.objects.link(o); vis(o, 1, False); return o

# ---------- shot / acting helpers ----------
JOINTS = ["UpperTorso", "Head", "LeftUpperArm", "LeftUpperLeg", "RightUpperLeg", "LeftLowerArm"]
def shot(i0, cast):
    f = F(i0)
    if f > 1:
        sc.frame_set(f - 1)
        for n in CAST:
            if n in cast and cast[n] is None: continue
            rt = root(n); L, Rr, S = rt.location.copy(), rt.rotation_euler.copy(), rt.scale.copy()
            rt.location = L; rt.rotation_euler = Rr; rt.scale = S
            kf(rt, "location", f - 1); kf(rt, "rotation_euler", f - 1); kf(rt, "scale", f - 1)
    for n in CAST:
        rt = root(n)
        if n in cast and cast[n] is None:
            continue
        if n in cast:
            x, y, z, deg = cast[n][:4]; s = cast[n][4] if len(cast[n]) > 4 else 1.0
            rt.location = (x, y, z); rt.rotation_euler = (0, 0, R(deg)); rt.scale = (s, s, s)
            for j in JOINTS: rot(n + "_" + j, f, interp='CONSTANT')
        else:
            rt.location = OFF; rt.scale = (1, 1, 1)
        kf(rt, "location", f); kf(rt, "rotation_euler", f); kf(rt, "scale", f)

def face(n, f, e): expr3.key(n, F(f) if False else f, e)

def E(n, i, e): expr3.key(n, F(i), e)

def walk(n, i0, i1, p0, p1, cad=8, amp=24):
    rt = root(n); f0, f1 = F(i0), F(i1)
    rt.location = p0; kf(rt, "location", f0, 'LINEAR'); rt.location = p1; kf(rt, "location", f1, 'CONSTANT')
    k = 0
    for f in range(f0, f1 + 1, cad):
        s = amp if k % 2 == 0 else -amp
        rot(n + "_LeftUpperLeg", f, s); rot(n + "_RightUpperLeg", f, -s); rot(n + "_LeftUpperArm", f, -s * 0.6)
        k += 1
    for j in ("LeftUpperLeg", "RightUpperLeg", "LeftUpperArm"): rot(n + "_" + j, f1 + 1, 0, interp='CONSTANT')

def move(n, keys, interp='BEZIER', hold_last=False):
    rt = root(n)
    for k, (i, p) in enumerate(keys):
        rt.location = p; kf(rt, "location", F(i), 'CONSTANT' if (hold_last and k == len(keys) - 1) else interp)

def lipsync(n, i0, i1, base):
    talk = "talk_" + base; state = None; last = -99
    for i in range(i0, min(i1, N)):
        want = talk if MASK[i] else base
        if want == talk and state == talk and i - last >= 5: want = base
        if want != state and i - last >= 2:
            E(n, i, want); state = want; last = i
    E(n, i1, base)

def facing(src, dst):
    d = Vector(dst) - Vector(src); return math.degrees(math.atan2(-d.x, d.y))

# ---------- cameras ----------
CAMS = {}
def cam(name, eye, target, lens, i0, lens_end=None, i1=None, eye_end=None, fstop=2.8, track=None):
    cd = bpy.data.cameras.new(name); co = bpy.data.objects.new(name, cd); sc.collection.objects.link(co)
    cd.lens = lens; cd.sensor_fit = 'VERTICAL'; cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
    co.location = eye
    if eye_end is not None and not track:
        track = bpy.data.objects.new(name + "_Aim", None); PROPS.objects.link(track); track.location = target
    if track:
        c = co.constraints.new('TRACK_TO'); c.target = track; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
        cd.dof.focus_object = track
    else:
        co.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
        cd.dof.focus_distance = (Vector(target) - Vector(eye)).length
    if lens_end is not None or eye_end is not None:
        f0, f1 = F(i0), F(i1)
        kf(cd, "lens", f0, 'BEZIER')
        if eye_end is not None: kf(co, "location", f0, 'BEZIER')
        if lens_end is not None: cd.lens = lens_end
        if eye_end is not None:
            co.location = eye_end
            kf(co, "location", f1)
        kf(cd, "lens", f1)
    m = sc.timeline_markers.new(name, frame=F(i0)); m.camera = co
    CAMS[name] = co
    return co

for _n in CAST:
    _e = bpy.data.objects.new(_n + "_Look", None); PROPS.objects.link(_e); _e.parent = root(_n); _e.location = (0, 0, 1.38)
def head(n): return O[n + "_Look"]
def hpos(n, x, y, z=0.0): return Vector((x, y, z + 1.39))

# ---------- lighting ----------
sun = O["Sun"]; bg = sc.world.node_tree.nodes["Background"]
moon = bpy.data.lights.new("MoonFill", 'SUN'); mo = bpy.data.objects.new("MoonFill", moon); sc.collection.objects.link(mo)
mo.rotation_euler = (R(50), 0, R(-30)); moon.color = (0.55, 0.65, 1.0)
def light(i, sun_e, sun_col, bg_s, moon_e):
    f = F(i); sun.data.energy = sun_e; sun.data.color = sun_col; bg.inputs[1].default_value = bg_s; moon.energy = moon_e
    kf(sun.data, "energy", f); kf(sun.data, "color", f); kf(sc.world.node_tree, 'nodes["Background"].inputs[1].default_value', f); kf(moon, "energy", f)
DAY = (3.2, (1.0, 0.96, 0.9), 0.75, 0.0)

# ================= SHOTS =================
for n in CAST: E(n, 0, "neutral")
light(0, *DAY)

# 1. wide street, neighbours walking with balloons (0-136)
shot(0, {"Grandpa": (-5.5, 0.0, 0, -90), "Teacher": (-7.5, 0.9, 0, -90), "KidA": (0.5, 0.9, 0, -90), "KidB": (-0.5, 0.2, 0, -90), "Principal": (-2.5, 0.2, 0, -90)})
walk("Grandpa", 0, 135, (-5.5, 0.0, 0), (-2.6, 0.0, 0), cad=10)
walk("Teacher", 0, 135, (-7.5, 0.9, 0), (-4.2, 0.9, 0))
walk("KidA", 0, 135, (0.5, 0.9, 0), (3.6, 0.9, 0), cad=7)
walk("KidB", 0, 135, (-0.5, 0.2, 0), (2.6, 0.2, 0), cad=7)
walk("Principal", 0, 135, (-2.5, 0.2, 0), (0.4, 0.2, 0), cad=11)
for n in ("Grandpa", "KidA", "KidB"): E(n, 0, "happy")
cam("Cam01", (-1.5, 10.5, 2.4), (-1.5, 0.5, 1.2), 22, 0, lens_end=24, i1=136, fstop=5.6)

# 2. KidB says sorry to KidA, KidA's balloon pops (136-203)
shot(136, {"KidB": (2.5, 0.75, 0, -90), "KidA": (3.5, 0.75, 0, 90)})
E("KidB", 136, "sad"); E("KidA", 136, "angry")
lipsync("KidB", 139, 165, "sad")
pop("KidA", 0, F(186)); E("KidA", 187, "happy"); E("KidB", 190, "happy")
cam("Cam02", (3.0, 3.3, 1.3), hpos("KidA", 3.0, 0.75) - Vector((0, 0, 0.15)), 40, 136)

# 3a. most people carry two or three (203-258)
shot(203, {"Teacher": (-2.0, 0.75, 0, 0), "KidA": (-0.6, 0.75, 0, 0), "KidB": (0.8, 0.75, 0, 0), "Photographer": (2.2, 0.75, 0, 0)})
for n in ("Teacher", "KidA", "KidB", "Photographer"): E(n, 203, "happy")
cam("Cam03a", (0.1, 4.8, 1.7), (0.1, 0.75, 1.3), 24, 203, lens_end=28, i1=258, fstop=4)

# 3b. night: Grandpa floating, tied to the mailbox (258-397)
mb = O["MailBox"].location
gp = Vector((mb.x + 1.3, mb.y + 0.4, 1.1))
shot(258, {"Grandpa": (gp.x, gp.y, gp.z, 0)})
move("Grandpa", [(258, gp), (330, gp + Vector((0, 0, 0.12))), (397, gp)])
rot("Grandpa_Head", F(258), -14, 0, 10, 'CONSTANT'); E("Grandpa", 258, "happy")
light(258, 0.25, (0.6, 0.7, 1.0), 0.06, 1.2)
r3 = rope("Rope_Mailbox", Vector((mb.x, mb.y, mb.z + 0.1)), gp + Vector((0, 0, 0.95)))
vis(r3, F(258), True); vis(r3, F(397), False)
cam("Cam03b", (mb.x + 3.6, mb.y + 4.2, 1.7), (mb.x + 0.6, mb.y, 1.6), 30, 258, lens_end=36, i1=397, fstop=4)
light(397, *DAY)

# 4. principal in ankle weights, hallway (397-462)
shot(397, {"Principal": (H.x - 0.3, H.y - 8.5, 0, 0)})
walk("Principal", 397, 461, (H.x - 0.3, H.y - 8.5, 0), (H.x - 0.3, H.y - 5.2, 0), cad=14, amp=30)
E("Principal", 397, "smug")
cam("Cam04", (H.x + 1.4, H.y - 2.0, 0.45), (H.x - 0.3, H.y - 5.5, 0.9), 24, 397, fstop=4)

# 5. picture day, photographer on a ladder (462-563)
shot(462, {"KidA": (C.x - 1.6, C.y - 4.9, 0.3, 0), "Maya": (C.x - 0.6, C.y - 5.5, 0.6, 0), "KidB": (C.x + 0.5, C.y - 5.5, 0.6, 0),
           "Kid3": (C.x + 1.6, C.y - 4.9, 0.3, 0), "Photographer": (LAD.x, LAD.y, 1.22, 180)})
move("KidB", [(462, (C.x + 0.5, C.y - 5.5, 0.6)), (505, (C.x + 0.5, C.y - 5.5, 0.75)), (562, (C.x + 0.5, C.y - 5.5, 1.5))])
move("Kid3", [(462, (C.x + 1.6, C.y - 4.9, 0.3)), (515, (C.x + 1.6, C.y - 4.9, 0.4)), (562, (C.x + 1.6, C.y - 4.9, 1.1))])
rot("Photographer_LeftUpperArm", F(462), 85, 0, -25, 'CONSTANT')
for n in ("KidA", "Maya"): E(n, 462, "happy")
E("KidB", 462, "happy"); E("Kid3", 462, "happy"); E("KidB", 505, "shocked"); E("Kid3", 515, "scared"); E("Photographer", 462, "neutral"); E("Photographer", 520, "shocked")
cam("Cam05", (C.x + 3.6, C.y + 1.8, 2.3), (C.x, C.y - 3.6, 1.6), 24, 462, fstop=5.6)

# 6a. "and if you ever float?" (563-607)
shot(563, {"Kid3": (4.0, 0.2, 0.0, 0)})
move("Kid3", [(563, (4.0, 0.2, 0.0)), (607, (4.0, 0.2, 1.4))])
E("Kid3", 563, "scared")
rot("Kid3_LeftUpperArm", F(570), 0, -70, 0, 'BEZIER'); rot("Kid3_LeftUpperArm", F(585), 0, -40, 0, 'BEZIER'); rot("Kid3_LeftUpperArm", F(600), 0, -75, 0, 'BEZIER')
cam("Cam06a", (5.6, 3.6, 0.45), (4.0, 0.2, 1.9), 26, 563, fstop=4)

# 6b. crowd judging (607-705)
crowd = {"Grandpa": (2.6, 2.4, 0, 180), "Teacher": (3.6, 2.9, 0, 180), "Principal": (4.6, 2.5, 0, 180), "KidA": (5.5, 3.0, 0, 180)}
shot(607, dict(crowd, Kid3=(4.0, 0.2, 2.2, 0)))
move("Kid3", [(607, (4.0, 0.2, 2.2)), (705, (4.0, 0.2, 3.0))])
for n in crowd:
    E(n, 607, "angry"); rot(n + "_LeftUpperArm", F(612), 150, 0, -10, 'CONSTANT'); rot(n + "_Head", F(607), 22, 0, 0, 'CONSTANT')
E("Kid3", 607, "crying")
cam("Cam06b", (4.0, -0.4, 3.6), (4.0, 2.7, 1.2), 26, 607, fstop=5.6)

# 7a. Maya walking with one gray balloon (705-787)
shot(705, {"Maya": (-4.2, 0.75, 0, -90)})
walk("Maya", 705, 786, (-4.2, 0.75, 0), (-1.6, 0.75, 0), cad=9)
E("Maya", 705, "neutral")
cam("Cam07a", (-2.6, 4.4, 1.5), (-2.6, 0.75, 1.4), 30, 705, fstop=4)

# 7b. close-up, Maya looks up at it, sad (787-912)
shot(787, {"Maya": (-1.6, 0.75, 0, 0)})
rot("Maya_Head", F(787), 0, 0, 0, 'BEZIER'); rot("Maya_Head", F(800), 14, 0, -16, 'BEZIER'); rot("Maya_Head", F(860), 12, 0, -14, 'BEZIER'); rot("Maya_Head", F(880), 0, 0, 0, 'CONSTANT')
E("Maya", 787, "neutral"); E("Maya", 812, "sad")
cam("Cam07b", (-1.3, 3.4, 1.3), hpos("Maya", -1.6, 0.75) - Vector((0, 0, 0.25)), 38, 787, lens_end=50, i1=912)

# 8. Ezra floats to school (912-1035)
shot(912, {"Ezra": (6.0, 0.6, 1.3, 90)})
move("Ezra", [(912, (6.0, 0.6, 1.3)), (1034, (2.2, 0.6, 1.55))], 'LINEAR', hold_last=True)
E("Ezra", 912, "sad")
cam("Cam08", (2.0, 3.6, 0.35), (4.0, 0.6, 2.8), 22, 912, fstop=4)

# 9a. classroom: paper balls (1035-1111)
ez_c = Vector((C.x + 4.2, C.y - 5.0, 0.9))
kids = {"KidA": (C.x + 1.5, C.y - 1.0, 0), "KidB": (C.x + 4.0, C.y - 0.6, 0), "Kid3": (C.x + 2.6, C.y + 1.6, 0), "Maya": (C.x - 3.0, C.y + 1.6, 0)}
cast9 = {n: (*p, facing(p, ez_c)) for n, p in kids.items()}
cast9["Ezra"] = (ez_c.x, ez_c.y, ez_c.z, 0); cast9["Teacher"] = (C.x - 2.5, C.y - 4.7, 0, 0)
shot(1035, cast9)
for n in ("KidA", "KidB", "Kid3"): E(n, 1035, "laughing")
E("Maya", 1035, "smug"); E("Ezra", 1035, "sad"); E("Teacher", 1035, "neutral")
r9 = rope("Rope_Radiator", Vector((C.x + 4.2, C.y - 5.55, 0.95)), ez_c + Vector((0, 0, 0.95)))
vis(r9, F(1035), True); vis(r9, F(1172), False)
throwers = ["KidA", "KidB", "Kid3", "KidA", "KidB", "Kid3", "KidA", "KidB"]
for k, (p, t) in enumerate(zip(papers, throwers)):
    i0 = 1040 + k * 15; i1 = i0 + 10
    src = Vector(kids[t]) + Vector((0, 0, 1.3)); dst = ez_c + Vector((random.uniform(-0.2, 0.2), 0.25, 1.2 + random.uniform(-0.2, 0.3)))
    p.location = OFF; kf(p, "location", F(i0) - 1)
    p.location = src; kf(p, "location", F(i0), 'LINEAR'); p.location = (src + dst) / 2 + Vector((0, 0, 0.5)); kf(p, "location", F(i0) + 5, 'LINEAR')
    p.location = dst; kf(p, "location", F(i1), 'LINEAR'); p.location = dst - Vector((0, 0, 0.9)); kf(p, "location", F(i1) + 8, 'CONSTANT')
    p.location = OFF; kf(p, "location", F(1172))
    rot(t + "_LeftUpperArm", F(i0) - 4, 140, 0, 0); rot(t + "_LeftUpperArm", F(i0) + 2, 40, 0, 0)
cam("Cam09a", (C.x + 6.6, C.y + 3.8, 2.7), (C.x + 2.6, C.y - 3.2, 1.2), 22, 1035, fstop=5.6)

# 9b. Ezra close-up, crying (1111-1172)
shot(1111, cast9)
E("Ezra", 1111, "crying")
cam("Cam09b", (C.x + 3.1, C.y - 2.6, 2.1), ez_c + Vector((0, 0, 1.3)), 38, 1111, lens_end=44, i1=1172)

# 10. Maya calls him a bully (1172-1280)
shot(1172, {"Maya": (C.x - 3.4, C.y + 2.3, 0, -90), "KidA": (C.x - 2.55, C.y + 2.3, 0, 90), "Ezra": (ez_c.x, ez_c.y, ez_c.z, 0)})
E("KidA", 1172, "laughing"); lipsync("Maya", 1175, 1265, "smug")
rot("Maya_Head", F(1172), 0, 0, -10, 'CONSTANT')
cam("Cam10", (C.x - 2.6, C.y + 5.2, 1.4), (C.x - 3.0, C.y + 2.3, 1.3), 32, 1172)

# 11a. cliff field trip, wind (1280-1389)
stake = K + Vector((1.2, 3.6, 0))
cls = {"KidA": (K.x - 3.0, K.y + 1.4, 0, 0), "KidB": (K.x - 1.8, K.y + 2.0, 0, 0), "Kid3": (K.x - 4.2, K.y + 1.9, 0, 0),
       "Maya": (K.x - 1.0, K.y + 2.5, 0, 0), "Teacher": (K.x - 5.4, K.y + 0.8, 0, 0)}
ez_k = stake + Vector((0, 0.3, 1.2))
shot(1280, dict(cls, Ezra=(ez_k.x, ez_k.y, ez_k.z, 180)))
for n in cls: E(n, 1280, "neutral")
E("Ezra", 1280, "sad")
r11 = rope("Rope_Stake", stake + Vector((0, 0, 0.9)), ez_k + Vector((0, 0, 0.95)))
vis(r11, F(1280), True); vis(r11, F(1420), False)
cam("Cam11a", (K.x - 3.0, K.y - 6.0, 2.6), (K.x - 0.5, K.y + 3.5, 1.3), 24, 1280, fstop=5.6)

# 11b. rope snaps (1389-1454)
shot(1389, dict(cls, Ezra=(ez_k.x, ez_k.y, ez_k.z, 180)))
E("Ezra", 1389, "scared"); E("Ezra", 1421, "shocked")
EZPATH = [(1420, ez_k), (1454, ez_k + Vector((0, 2.0, 2.0))), (1538, ez_k + Vector((0, 9.0, 8.0))), (1645, ez_k + Vector((0, 13.0, 10.5))),
          (1745, ez_k + Vector((0, 15.0, 11.5))), (2400, ez_k + Vector((0, 16.0, 12.0))), (2506, ez_k + Vector((0, 15.0, 11.0))),
          (2611, ez_k + Vector((0, 11.0, 8.0))), (2700, ez_k + Vector((0, 5.5, 3.6))), (2788, Vector((K.x - 2.3, K.y + 2.4, 1.15)))]
cam("Cam11b", (K.x + 2.6, K.y + 1.0, 1.6), ez_k + Vector((0, 0, 1.75)), 30, 1389)

# 12. Ezra rises over the ocean (1454-1538)
move("Ezra", EZPATH, 'BEZIER', hold_last=True)
shot(1454, dict(cls, Ezra=None))
for n in cls: E(n, 1454, "shocked")
cam("Cam12", (K.x + 0.2, K.y + 4.4, 1.5), None, 26, 1454, track=head("Ezra"), fstop=8)

# 13. everyone screams "pop them!" (1538-1645)
edge = {"KidA": (K.x - 2.4, K.y + 4.5, 0, 0), "KidB": (K.x - 1.2, K.y + 4.6, 0, 0), "Kid3": (K.x + 0.0, K.y + 4.5, 0, 0),
        "Teacher": (K.x + 1.2, K.y + 4.3, 0, 0), "Maya": (K.x - 3.5, K.y + 4.1, 0, 0)}
shot(1538, dict(edge, Ezra=None))
for n in edge:
    rot(n + "_Head", F(1538), 25, 0, 0, 'CONSTANT'); rot(n + "_LeftUpperArm", F(1545), 160, 0, -15, 'CONSTANT')
    if n != "Maya": lipsync(n, 1541, 1633, "shocked")
E("Maya", 1538, "scared")
cam("Cam13", (K.x - 0.6, K.y + 8.2, 0.7), (K.x - 0.9, K.y + 4.5, 1.6), 26, 1538, fstop=5.6)

# 14. Ezra yells back (1645-1745)
shot(1645, dict(edge, Ezra=None))
lipsync("Ezra", 1648, 1726, "crying")
rot("Ezra_Head", F(1645), -25, 0, 0, 'CONSTANT')
e14 = ez_k + Vector((0, 13.0, 10.5))
cam("Cam14", e14 + Vector((2.0, -2.8, 0.3)), None, 34, 1645, track=head("Ezra"))

# 15. Maya looks at her gray balloon (1745-1953)
shot(1745, dict(cls, Ezra=None))
E("Maya", 1745, "confused"); E("Maya", 1900, "sad")
rot("Maya_Head", F(1745), 0, 0, 0, 'BEZIER'); rot("Maya_Head", F(1790), 15, 0, -16, 'BEZIER'); rot("Maya_Head", F(1930), 14, 0, -14, 'CONSTANT')
for n in cls:
    if n != "Maya": E(n, 1745, "sad")
cam("Cam15", (K.x - 0.8, K.y + 5.0, 1.15), hpos("Maya", K.x - 1.0, K.y + 2.5) - Vector((0, 0, 0.1)), 30, 1745, lens_end=52, i1=1953)

# 16. flashback: dad leaves (1953-2036)
shot(1953, {"Dad": (0.5, 0.6, 0, 90), "Maya": (1.6, 1.1, 0, 90, 0.78)})
walk("Dad", 1953, 2035, (0.5, 0.6, 0), (-3.8, 0.6, 0), cad=10)
E("Dad", 1953, "sad"); E("Maya", 1953, "crying")
rot("Dad_LeftUpperArm", F(1953), 0, 0, 0, 'CONSTANT')
light(1953, 1.6, (1.0, 0.62, 0.38), 0.32, 0.0)
cam("Cam16", (3.6, 4.2, 1.3), (0.2, 0.75, 1.0), 24, 1953, fstop=4)
light(2036, *DAY)

# 17a. realization (2036-2113)
shot(2036, dict(cls, Ezra=None))
E("Maya", 2036, "shocked")
cam("Cam17a", (K.x - 1.0, K.y + 3.75, 1.42), hpos("Maya", K.x - 1.0, K.y + 2.5) - Vector((0, 0, 0.02)), 48, 2036, lens_end=58, i1=2113)

# 17b. the class realizes too (2113-2190)
shot(2113, dict(cls, Ezra=None))
for n in ("KidA", "KidB", "Kid3", "Teacher"): E(n, 2113, "shocked")
cam("Cam17b", (K.x - 3.4, K.y + 4.6, 1.45), (K.x - 3.4, K.y + 1.6, 1.3), 28, 2113, fstop=4)

# 18. Maya turns to the class (2190-2398)
cls18 = {"KidA": (K.x - 2.2, K.y + 0.9, 0, 0), "KidB": (K.x - 0.9, K.y + 0.5, 0, 0), "Kid3": (K.x + 0.3, K.y + 0.9, 0, 0), "Teacher": (K.x - 3.2, K.y + 0.3, 0, 0)}
shot(2190, dict(cls18, Maya=(K.x - 1.0, K.y + 3.0, 0, 0), Ezra=None))
rm = root("Maya"); rm.rotation_euler = (0, 0, 0); kf(rm, "rotation_euler", F(2200), 'BEZIER'); rm.rotation_euler = (0, 0, R(180)); kf(rm, "rotation_euler", F(2215), 'CONSTANT')
E("Maya", 2190, "sad"); E("Maya", 2215, "angry"); lipsync("Maya", 2261, 2381, "angry")
for n in cls18: E(n, 2190, "sad")
cam("Cam18", (K.x - 1.6, K.y - 0.2, 1.55), hpos("Maya", K.x - 1.0, K.y + 3.0) - Vector((0, 0, 0.15)), 34, 2190, lens_end=40, i1=2398)

# 19. Jake whispers "sorry, Ezra" (2398-2496), first pop (2496-2525)
shot(2398, dict(cls18, Maya=(K.x - 1.0, K.y + 3.0, 0, 180), Ezra=None))
E("KidB", 2398, "sad"); lipsync("KidB", 2474, 2494, "sad"); rot("KidB_Head", F(2398), 20, 0, 0, 'CONSTANT')
cam("Cam19", (K.x - 0.9, K.y + 2.6, 1.35), hpos("KidB", K.x - 0.9, K.y + 0.5) - Vector((0, 0, 0.1)), 40, 2398)
shot(2496, dict(cls18, Maya=(K.x - 1.0, K.y + 3.0, 0, 180), Ezra=None))
E("Ezra", 2496, "sad"); E("Ezra", 2507, "shocked")
cam("Cam19b", (K.x + 0.5, K.y + 4.2, 1.2), None, 34, 2496, track=head("Ezra"), fstop=8)

# 20. more sorrys, more pops
shot(2525, dict(cls18, Maya=(K.x - 1.0, K.y + 3.0, 0, 180), Ezra=None))
lipsync("KidA", 2528, 2540, "sad"); rot("KidA_Head", F(2525), 20, 0, 0, 'CONSTANT')
cam("Cam20a", (K.x - 2.0, K.y + 3.0, 1.4), hpos("KidA", K.x - 2.2, K.y + 0.9) - Vector((0, 0, 0.1)), 40, 2525)
cam("Cam20b", (K.x + 0.5, K.y + 4.2, 1.2), None, 30, 2551, track=head("Ezra"), fstop=8)
lipsync("Teacher", 2572, 2598, "sad")
cam("Cam20c", (K.x - 3.0, K.y + 2.6, 1.5), hpos("Teacher", K.x - 3.2, K.y + 0.3) - Vector((0, 0, 0.1)), 38, 2569)
cam("Cam20d", (K.x + 2.5, K.y + 9.0, 7.2), None, 30, 2608, track=head("Ezra"))
E("Ezra", 2608, "shocked")

# pops: 42 balloons
order = list(range(42)); random.shuffle(order)
pops = [2506, 2554, 2611, 2632, 2653] + [2615 + k * 5 for k in range(11)] + [2680 + k * 4 for k in range(26)]
for idx, i in zip(order, sorted(pops)):
    pop("Ezra", idx, F(i))

# 21. Ezra floats down into their arms (2673-2795)
catch = {"KidA": (K.x - 3.2, K.y + 2.3, 0, 0), "KidB": (K.x - 1.4, K.y + 2.5, 0, 0), "Kid3": (K.x - 2.3, K.y + 1.6, 0, 0),
         "Maya": (K.x - 2.3, K.y + 3.3, 0, 180), "Teacher": (K.x - 4.3, K.y + 1.6, 0, 0)}
shot(2673, dict(catch, Ezra=None))
for n in catch:
    rot(n + "_LeftUpperArm", F(2740), 150, 0, -10, 'CONSTANT'); rot(n + "_Head", F(2673), 20, 0, 0, 'CONSTANT')
    E(n, 2673, "shocked"); E(n, 2770, "happy")
E("Ezra", 2673, "scared"); E("Ezra", 2775, "happy")
cam("Cam21", (K.x - 1.0, K.y - 4.0, 2.3), (K.x - 1.8, K.y + 3.0, 2.6), 22, 2673, fstop=5.6)

# 22. walking to school together (2795-3016)
shot(2795, {"Ezra": (-6.5, 0.75, 0, -90), "Maya": (-7.3, 0.75, 0, -90)})
walk("Ezra", 2795, 3015, (-6.5, 0.75, 0), (-1.0, 0.75, 0), cad=9)
walk("Maya", 2795, 3015, (-7.3, 0.75, 0), (-1.8, 0.75, 0), cad=9)
E("Ezra", 2795, "happy"); E("Maya", 2795, "happy"); E("Maya", 2900, "laughing"); E("Ezra", 2900, "laughing"); E("Maya", 2960, "happy")
aim22 = bpy.data.objects.new("Cam22_Aim", None); PROPS.objects.link(aim22)
aim22.location = (-6.9, 0.75, 1.2); kf(aim22, "location", F(2795), 'LINEAR'); aim22.location = (-1.4, 0.75, 1.2); kf(aim22, "location", F(3015))
c22 = cam("Cam22", (-6.4, 4.4, 1.5), None, 28, 2795, track=aim22, fstop=4)
c22.location = (-6.4, 4.4, 1.5); kf(c22, "location", F(2795), 'LINEAR'); c22.location = (-1.9, 4.4, 1.5); kf(c22, "location", F(3015))

# 23. one more balloon for me (3016-end)
shot(3016, {"Ezra": (-1.0, 0.75, 0, 0), "Maya": (-1.8, 0.75, 0, 0)})
E("Maya", 3016, "laughing"); E("Ezra", 3016, "happy")
anc = O["EndAnchor"]
anc.location = OFF; kf(anc, "location", F(3015))
anc.location = (-0.4, 1.6, 1.2); kf(anc, "location", F(3016), 'BEZIER'); anc.location = (0.2, 1.4, 7.5); kf(anc, "location", F(N) + 20, 'BEZIER')
cam("Cam23", (-1.4, 4.4, 1.3), None, 26, 3016, track=anc, fstop=5.6)

sc.frame_start, sc.frame_end = 1, N + 15
sc.render.fps = 30
log("shots done", len(sc.timeline_markers), "markers")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BASE, "balloon_film.blend"))
log("saved")

# ---------- check stills ----------
CHECK = [60, 170, 230, 320, 430, 520, 590, 660, 750, 850, 980, 1080, 1140, 1230, 1340, 1430, 1500, 1590, 1700, 1850, 1990, 2070, 2150, 2300, 2450, 2510, 2580, 2640, 2740, 2900, 3100]
os.makedirs(os.path.join(BASE, "film_check"), exist_ok=True)
sc.render.resolution_percentage = 20
sc.render.image_settings.media_type = 'IMAGE'; sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 80
try: sc.eevee.taa_render_samples = 8
except Exception: pass
for i in []:
    sc.frame_set(F(i))
    mk = max([m for m in sc.timeline_markers if m.frame <= F(i)], key=lambda m: m.frame)
    sc.camera = mk.camera
    sc.render.filepath = os.path.join(BASE, "film_check", "c_%04d.jpg" % i)
    bpy.ops.render.render(write_still=True)
log("checks rendered")
LOG.close()
