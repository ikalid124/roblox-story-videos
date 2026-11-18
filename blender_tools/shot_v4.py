# v4 test: two-character exchange with expression changes, balloons, acting and camera punch-ins.
import bpy, math, os, random, importlib
from mathutils import Vector, Matrix
from bpy_extras import anim_utils
import expr; importlib.reload(expr)

sc = bpy.context.scene
base = os.path.join(os.path.expanduser("~"), "Downloads", "BalloonTest")
R = math.radians
O = bpy.data.objects

def lin(c): return tuple(pow(x / 255.0, 2.2) for x in c)

# ---------- reset ----------
for o in list(bpy.data.objects):
    if o.animation_data and (o.name.split("_")[0] in ("Maya", "Ezra", "Grandpa", "KidA", "KidB") or o.name.startswith("Cam_")):
        o.animation_data_clear()
    if o.name.split("_")[0] in ("Maya", "Ezra") and o.type in ('MESH', 'EMPTY'):
        o.rotation_euler = (0, 0, 0) if not o.name.endswith("_Root") else o.rotation_euler
for c in list(bpy.data.collections):
    if c.name == "Props_v4":
        for o in list(c.objects): bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(c)
props = bpy.data.collections.new("Props_v4"); sc.collection.children.link(props)
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for n in ("Maya", "Ezra", "Grandpa", "KidA", "KidB"):
    h = O[n + "_Head"]; tex = [t for t in h.data.materials[0].node_tree.nodes if t.type == 'TEX_IMAGE'][0]
    tex.image = bpy.data.images.load(os.path.join(base, "faces", "faces2_%s.png" % n), check_existing=True)

sc.frame_start, sc.frame_end = 1, 120
sc.render.fps = 30
sc.frame_set(1)

# ---------- staging ----------
maya, ezra = O["Maya_Root"], O["Ezra_Root"]
maya.location = Vector((-3.3, 0.75, 0)); maya.rotation_euler = (0, 0, R(-28))
ezra.location = Vector((-2.05, 0.75, 0)); ezra.rotation_euler = (0, 0, R(28))
O["Maya_RightUpperArm"].rotation_euler = (R(32), 0, R(8))
O["Ezra_RightUpperArm"].rotation_euler = (R(30), 0, R(6))
bpy.context.view_layer.update()

def fwd(root): return (root.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()
def side(root): f = fwd(root); return Vector((f.y, -f.x, 0)).normalized()   # character's right

# ---------- balloons ----------
def latex(rgb):
    m = bpy.data.materials.new("Balloon_%d_%d_%d" % rgb); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(rgb), 1); b.inputs["Roughness"].default_value = 0.18
    try: b.inputs["Coat Weight"].default_value = 0.4
    except Exception: pass
    try: b.inputs["Subsurface Weight"].default_value = 0.15
    except Exception: pass
    return m

def string_mat():
    m = bpy.data.materials.get("BalloonString") or bpy.data.materials.new("BalloonString")
    m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.85, 0.85, 0.85, 1)
    return m

def balloon(name, center, grip, rgb, parent, r=0.15):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=center)
    s = bpy.context.active_object; s.name = name; s.scale = (r, r, r * 1.18)
    for p in s.data.polygons: p.use_smooth = True
    s.data.materials.append(latex(rgb))
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=r * 0.16, radius2=r * 0.03, depth=r * 0.25,
                                    location=center - Vector((0, 0, r * 1.22)))
    k = bpy.context.active_object; k.name = name + "_knot"; k.rotation_euler = (math.pi, 0, 0); k.data.materials.append(latex(rgb))
    cu = bpy.data.curves.new(name + "_str", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0025
    sp = cu.splines.new('POLY'); sp.points.add(1)
    a = center - Vector((0, 0, r * 1.3)); sp.points[0].co = (*a, 1); sp.points[1].co = (*grip, 1)
    st = bpy.data.objects.new(name + "_str", cu); bpy.context.scene.collection.objects.link(st)
    cu.materials.append(string_mat())
    for o in (s, k, st):
        for c in o.users_collection: c.objects.unlink(o)
        props.objects.link(o)
        o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()

def holder(char):
    hand = O[char + "_RightHand"]
    grip = hand.matrix_world @ Vector((0, 0, -0.05))
    e = bpy.data.objects.new(char + "_BalloonSway", None); props.objects.link(e)
    e.location = grip; e.empty_display_size = 0.05
    e.parent = hand; e.matrix_parent_inverse = hand.matrix_world.inverted()
    for f, a in ((1, -3), (25, 3), (50, -3), (75, 3), (100, -3), (120, 2)):
        e.rotation_euler = (R(a * 0.5), R(a), 0); e.keyframe_insert("rotation_euler", frame=f)
    bpy.context.view_layer.update()
    return e, grip

e, grip = holder("Maya")
c = grip + side(maya) * 0.02 + fwd(maya) * 0.05 + Vector((0, 0, 1.0))
balloon("Maya_Balloon", c, grip, (150, 150, 158), e, r=0.16)

e, grip = holder("Ezra")
random.seed(42)
cols = [(235, 60, 60), (60, 130, 240), (250, 210, 50), (70, 200, 90), (245, 120, 190), (255, 150, 40),
        (150, 90, 230), (60, 210, 220), (235, 60, 60), (250, 210, 50), (60, 130, 240), (245, 120, 190), (70, 200, 90), (255, 150, 40)]
base_c = grip + side(ezra) * 0.05 - fwd(ezra) * 0.15 + Vector((0, 0, 1.05))
for i, col in enumerate(cols):
    a = random.uniform(0, 2 * math.pi); rr = random.uniform(0.05, 0.36)
    off = side(ezra) * math.cos(a) * rr + fwd(ezra) * math.sin(a) * rr * 0.6 + Vector((0, 0, random.uniform(-0.12, 0.3)))
    balloon("Ezra_Balloon%02d" % i, base_c + off, grip, col, e, r=random.uniform(0.12, 0.15))

# ---------- cameras ----------
def cam(name, char, shift, lens=38):
    root = O[char + "_Root"]; head = O[char + "_HeadCenter"].matrix_world.translation
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    co = O.get(name) or bpy.data.objects.new(name, cd)
    if co.name not in sc.collection.objects: sc.collection.objects.link(co)
    cd.lens = lens; cd.sensor_fit = 'VERTICAL'; cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.0
    cd.dof.focus_object = O[char + "_HeadCenter"]
    tgt = head + Vector((0, 0, -0.12))
    co.location = tgt + fwd(root) * 2.6 + side(root) * shift + Vector((0, 0, 0.05))
    co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()
    return co

camA = cam("Cam_A", "Maya", 0.55); camB = cam("Cam_B", "Ezra", -0.55)
for f, c in ((1, camA), (31, camB), (61, camA), (91, camB)):
    m = sc.timeline_markers.new("cut%d" % f, frame=f); m.camera = c
def lens_keys(c, keys):
    for f, v in keys:
        c.data.lens = v; c.data.keyframe_insert("lens", frame=f)
lens_keys(camA, ((1, 38), (60, 38), (61, 55), (70, 46), (77, 46), (78, 52), (90, 50)))
lens_keys(camB, ((31, 38), (47, 38), (48, 42), (90, 42), (91, 38), (103, 38), (104, 54), (112, 48)))
sc.camera = camA

# ---------- acting ----------
def rk(obj, f, x=0, y=0, z=0):
    o = O[obj]; o.rotation_euler = (R(x), R(y), R(z)); o.keyframe_insert("rotation_euler", frame=f)

# Maya: neutral -> sad looking up at her one balloon -> shocked -> angry
for f, x, z in ((1, 0, 0), (10, 0, 0), (16, 12, -16), (30, 10, -14), (60, 2, 0), (61, 14, 0), (64, 8, 0), (77, 6, 0), (78, -6, 8), (90, -5, 6)):
    rk("Maya_Head", f, x, 0, z)
for f, x in ((1, 0), (60, 0), (61, 6), (65, 3), (77, 3), (78, -7), (82, -9), (90, -8)):
    rk("Maya_UpperTorso", f, x)
for f, x, zz in ((1, 0, 0), (77, 0, 0), (79, 25, -15), (90, 28, -18)):   # angry: left fist up
    rk("Maya_LeftUpperArm", f, x, 0, zz)
# Ezra: smug -> laughing bounce -> goofy -> scared
for f, x, y, z in ((1, 6, 0, 10), (47, 6, 0, 10), (48, 14, 0, 0), (60, 12, 0, 0), (90, 10, 0, 0), (91, 0, 14, 0), (103, 0, 14, 0), (104, 4, 0, -6), (120, 4, 0, -8)):
    rk("Ezra_Head", f, x, y, z)
for i, f in enumerate(range(48, 62, 3)):
    rk("Ezra_UpperTorso", f, 6 if i % 2 == 0 else -2)
for f, x in ((1, 0), (47, 0), (62, 0), (103, 0), (104, 7), (120, 8)):
    rk("Ezra_UpperTorso", f, x)
for f, x, zz in ((1, 0, 0), (103, 0, 0), (105, 70, -30), (120, 75, -32)):   # scared: hands up
    rk("Ezra_LeftUpperArm", f, x, 0, zz)
# idle bob
for root in (maya, ezra):
    z0 = root.location.z
    for i, f in enumerate(range(1, 121, 15)):
        root.location.z = z0 + (0.006 if i % 2 else 0); root.keyframe_insert("location", index=2, frame=f)

# ---------- expressions ----------
for f, e in ((1, "neutral"), (14, "sad"), (61, "shocked"), (78, "angry")): expr.key("Maya", f, e)
for f, e in ((1, "smug"), (48, "laughing"), (91, "goofy"), (104, "scared")): expr.key("Ezra", f, e)

# ---------- render ----------
fr = os.path.join(base, "frames_v4"); os.makedirs(fr, exist_ok=True)
for f in os.listdir(fr): os.remove(os.path.join(fr, f))
sc.render.image_settings.media_type = 'IMAGE'; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
sc.render.filepath = os.path.join(fr, "f_####"); sc.render.resolution_percentage = 50
print("built")
