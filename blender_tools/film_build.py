# Stage 1 of "The balloons": cast + sets. Run inside Blender: exec(open(path).read())
import bpy, os, sys, math, importlib, traceback, bmesh
from mathutils import Vector

BASE = os.path.join(os.path.expanduser("~"), "Downloads", "BalloonTest")
TOOLS = os.path.join(BASE, "tools")
if TOOLS not in sys.path: sys.path.insert(0, TOOLS)
import rbxt, avatar, clothing, expr2, expr3
for m in (rbxt, avatar, clothing, expr2, expr3): importlib.reload(m)

LOG = open(os.path.join(BASE, "film_log.txt"), "w")
def log(*a):
    print(*a, file=LOG, flush=True)

def lin(c): return tuple(pow(x / 255.0, 2.2) for x in c)

bpy.ops.wm.open_mainfile(filepath=os.path.join(BASE, "balloon_v5.blend"))
sc = bpy.context.scene
O = bpy.data.objects

# ---------- clean up test leftovers ----------
for cname in ("Props_v4",):
    c = bpy.data.collections.get(cname)
    if c:
        for o in list(c.objects): bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(c)
for o in list(O):
    if o.type == 'CAMERA' or o.name.startswith("Cap_"):
        bpy.data.objects.remove(o, do_unlink=True)
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for o in O:
    if o.animation_data: o.animation_data_clear()
    if o.type == 'CAMERA' and o.data.animation_data: o.data.animation_data_clear()
for n in ("Maya", "Ezra", "Grandpa", "KidA", "KidB"):
    for o in O:
        if o.name.startswith(n + "_") and o.type in ('MESH', 'EMPTY') and not o.name.endswith("_Root"):
            o.rotation_euler = (0, 0, 0)
log("cleaned")

# ---------- helpers ----------
SETS = bpy.data.collections.get("FilmSets") or bpy.data.collections.new("FilmSets")
if SETS.name not in sc.collection.children: sc.collection.children.link(SETS)
_mats = {}
def mat(rgb, rough=0.6):
    k = (tuple(rgb), rough)
    if k not in _mats:
        m = bpy.data.materials.new("F_%d_%d_%d" % tuple(rgb)); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*lin(rgb), 1); b.inputs["Roughness"].default_value = rough
        _mats[k] = m
    return _mats[k]

def box(name, size, loc, rgb, rough=0.6, bevel=0.03, coll=SETS):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob); ob.location = loc
    me.materials.append(mat(rgb, rough))
    if bevel:
        bv = ob.modifiers.new("Bevel", "BEVEL"); bv.width = bevel; bv.segments = 2; bv.limit_method = 'ANGLE'
    return ob

def cyl(name, r, h, loc, rgb, coll=SETS, rot=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r, radius2=r, depth=h)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob); ob.location = loc; ob.rotation_euler = rot
    me.materials.append(mat(rgb)); [setattr(p, "use_smooth", True) for p in me.polygons]
    return ob

def tint_hair(name, rgb):
    ob = O.get(name + "_Hair")
    if not ob or not ob.data.materials: return
    m = ob.data.materials[0]; nt = m.node_tree
    tex = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]; b = nt.nodes["Principled BSDF"]
    bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(tex.outputs["Color"], bw.inputs[0])
    mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs["Factor"].default_value = 1
    nt.links.new(bw.outputs[0], mul.inputs["A"]); mul.inputs["B"].default_value = (*lin(rgb), 1)
    nt.links.new(mul.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.8

# ---------- new cast ----------
AV = bpy.data.collections["Avatars"]
NEW = {
    "Teacher":      dict(skin=(190, 140, 100), shirt=(80, 150, 160), pants=(50, 50, 60), shoes=(40, 30, 30), hair=451220849, face=144080495,
                         cloth=(144076436, 382537569), tint=(90, 60, 40)),
    "Principal":    dict(skin=(120, 85, 60), shirt=(60, 70, 110), pants=(40, 40, 50), shoes=(20, 20, 20), hair=62234425, face=144080495,
                         cloth=(382537702, 382538503), tint=(30, 25, 22)),
    "Photographer": dict(skin=(230, 190, 150), shirt=(230, 180, 60), pants=(70, 80, 100), shoes=(60, 40, 30), hair=376548738, face=144080495,
                         cloth=(4047884939, 382537806), tint=None),
    "Dad":          dict(skin=(141, 96, 66), shirt=(90, 90, 100), pants=(45, 45, 55), shoes=(30, 30, 30), hair=80922374, face=144080495,
                         cloth=(3670737444, 382537569), tint=(25, 20, 18)),
    "Kid3":         dict(skin=(230, 190, 160), shirt=(240, 120, 170), pants=(60, 60, 90), shoes=(250, 250, 250), hair=2956239660, face=144080495,
                         cloth=(4047884939, 382537806), tint=(35, 28, 25)),
}
for i, (n, c) in enumerate(NEW.items()):
    if O.get(n + "_Root"):
        log(n, "exists"); continue
    try:
        avatar.build(n, Vector((200 + i * 3, 0, 0)), c, AV)
        if c["tint"]: tint_hair(n, c["tint"])
        try:
            clothing.apply(n, c["skin"], *c["cloth"])
        except Exception as e:
            log(n, "clothing failed", str(e)[:120])
        expr3.build_head_material(n, c["skin"], "faces4_%s.png" % n)
        log(n, "built")
    except Exception:
        log(n, "ERR", traceback.format_exc()[-600:])

# principal's ankle weights
for side in ("Left", "Right"):
    ll = O.get("Principal_%sLowerLeg" % side)
    if ll and not O.get("Principal_Weight" + side):
        w = cyl("Principal_Weight" + side, 0.2, 0.16, (0, 0, 0), (40, 40, 45))
        w.parent = ll; w.location = (0, 0, -0.22)

# ---------- classroom (C) ----------
C = Vector((60, 0, 0))
if not O.get("Class_Floor"):
    box("Class_Floor", (16, 14, 0.2), C + Vector((0, 0, -0.1)), (200, 165, 120), bevel=0)
    box("Class_BackWall", (16, 0.3, 4.5), C + Vector((0, -6, 2.25)), (235, 225, 200), bevel=0)
    box("Class_LeftWall", (0.3, 14, 4.5), C + Vector((-8, 0, 2.25)), (225, 215, 195), bevel=0)
    box("Class_RightWall", (0.3, 14, 4.5), C + Vector((8, 0, 2.25)), (225, 215, 195), bevel=0)
    for y in (-3, 1, 4):
        box("Class_Window%d" % y, (0.12, 2.0, 1.6), C + Vector((-7.82, y, 2.4)), (170, 215, 240), rough=0.15)
    box("Class_Door", (0.12, 1.2, 2.3), C + Vector((7.82, 3.5, 1.15)), (140, 90, 55))
    box("Class_Board", (5.2, 0.12, 1.9), C + Vector((0, -5.8, 2.2)), (45, 85, 65), rough=0.9)
    box("Class_BoardFrame", (5.5, 0.08, 2.15), C + Vector((0, -5.84, 2.2)), (150, 100, 60))
    box("Class_Radiator", (1.8, 0.3, 0.85), C + Vector((4.2, -5.65, 0.55)), (200, 200, 208), rough=0.3)
    for k in range(9):
        box("Class_RadFin%d" % k, (0.06, 0.34, 0.8), C + Vector((3.45 + k * 0.19, -5.65, 0.55)), (170, 170, 180), bevel=0)
    box("Class_TeacherDesk", (2.2, 0.9, 0.8), C + Vector((-2.5, -4.0, 0.4)), (150, 95, 55))
    for ix, x in enumerate((-4.5, -1.5, 1.5, 4.5)):
        for iy, y in enumerate((-1.5, 1.0, 3.5)):
            box("Class_Desk%d%d" % (ix, iy), (1.1, 0.7, 0.72), C + Vector((x, y, 0.36)), (175, 125, 75))
            box("Class_Chair%d%d" % (ix, iy), (0.5, 0.5, 0.45), C + Vector((x, y + 0.65, 0.225)), (80, 120, 210))
    # picture-day risers + ladder
    box("Class_Riser1", (6, 0.8, 0.3), C + Vector((0, -4.9, 0.15)), (110, 110, 120))
    box("Class_Riser2", (6, 0.8, 0.6), C + Vector((0, -5.5, 0.3)), (110, 110, 120))
log("classroom ok")

# ---------- hallway (H) ----------
H = Vector((60, 30, 0))
if not O.get("Hall_Floor"):
    box("Hall_Floor", (5, 24, 0.2), H + Vector((0, 0, -0.1)), (175, 180, 195), rough=0.3, bevel=0)
    box("Hall_WallR", (0.3, 24, 4), H + Vector((2.5, 0, 2)), (235, 228, 210), bevel=0)
    box("Hall_WallL", (0.3, 24, 4), H + Vector((-2.5, 0, 2)), (235, 228, 210), bevel=0)
    for k in range(28):
        y = -10.5 + k * 0.78
        box("Hall_Locker%d" % k, (0.35, 0.72, 2.0), H + Vector((-2.2, y, 1.0)), (60, 110, 205) if k % 2 else (55, 100, 195), rough=0.35)
        box("Hall_Vent%d" % k, (0.02, 0.4, 0.12), H + Vector((-2.02, y, 1.7)), (30, 50, 100), bevel=0)
log("hallway ok")

# ---------- cliff (K) ----------
K = Vector((-60, 0, 0))
if not O.get("Cliff_Grass"):
    box("Cliff_Grass", (40, 26, 0.3), K + Vector((0, -7, -0.15)), (95, 185, 80), bevel=0.15)
    box("Cliff_Rock", (40, 26, 14), K + Vector((0, -7.1, -7.3)), (135, 112, 90), bevel=0.3)
    box("Ocean", (600, 600, 0.2), K + Vector((0, 200, -12)), (40, 125, 205), rough=0.08, bevel=0)
    for i, (x, y, s) in enumerate(((-6, 5, 1.0), (7, 4.5, 0.8), (3, 5.4, 0.6), (-11, 3, 1.3))):
        box("Cliff_Rock%d" % i, (s, s * 0.8, s * 0.6), K + Vector((x, y, s * 0.25)), (120, 120, 125), bevel=0.15)
    cyl("Cliff_Stake", 0.07, 1.0, K + Vector((1.2, 3.6, 0.45)), (110, 75, 45))
    cyl("Cliff_Sign", 0.05, 1.4, K + Vector((-3, 4.8, 0.6)), (110, 75, 45))
    box("Cliff_SignBoard", (1.2, 0.08, 0.5), K + Vector((-3, 4.8, 1.25)), (200, 60, 50))
log("cliff ok")

sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BASE, "balloon_film.blend"))
log("saved", [o.name for o in O if o.name.endswith("_Root")])
mb = O.get("MailBox"); log("mailbox", tuple(round(v, 2) for v in mb.location) if mb else None)
for n in ("Road", "Grass", "SidewalkFar", "Walls", "Door", "TreeTop", "Path"):
    ob = O.get(n)
    if ob: log(n, tuple(round(v, 2) for v in ob.location), tuple(round(v, 2) for v in ob.dimensions))
LOG.close()
