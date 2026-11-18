# Build Roblox-style R15 avatars in Blender from real Roblox assets (hair mesh/texture, classic faces)
import bpy, bmesh, math, os
from mathutils import Vector, Matrix
import rbxt as rbx

S = 0.3  # metres per stud
AX = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))  # Roblox (x, y-up, z) -> Blender (x, -z, z-up)

def rb(v):  # Roblox vector (studs) -> Blender vector (m)
    return AX @ Vector(v) * S

def lin(c):
    return tuple(pow(x / 255.0, 2.2) for x in c)

_mat_cache = {}
def flat_mat(name, rgb, rough=0.45, spec=0.35):
    key = (name, tuple(rgb))
    if key in _mat_cache and _mat_cache[key].name in bpy.data.materials:
        return _mat_cache[key]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(rgb), 1)
    b.inputs["Roughness"].default_value = rough
    try: b.inputs["Specular IOR Level"].default_value = spec
    except Exception: pass
    _mat_cache[key] = m
    return m

def image_mat(name, tex_path, base_rgb=None, rough=0.55):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    img = bpy.data.images.load(tex_path, check_existing=True)
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.interpolation = 'Closest' if img.size[0] <= 256 else 'Linear'
    if base_rgb:
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MIX'
        mix.inputs["A"].default_value = (*lin(base_rgb), 1)
        nt.links.new(t.outputs["Color"], mix.inputs["B"]); nt.links.new(t.outputs["Alpha"], mix.inputs["Factor"])
        nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    else:
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    return m

def box_obj(name, size, coll, mat, origin_off, bevel=0.045):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    for v in bm.verts: v.co = AX @ v.co * S - origin_off
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob); me.materials.append(mat)
    if bevel:
        bv = ob.modifiers.new("Bevel", "BEVEL"); bv.width = bevel * S; bv.segments = 3; bv.limit_method = 'NONE'
    for p in me.polygons: p.use_smooth = True
    try: me.shade_smooth_by_angle(angle=math.radians(40))
    except Exception: pass
    return ob

def classic_head(name, coll, skin_rgb, face_png, origin_off):
    # classic Roblox head: vertical cylinder with rounded caps (about 1.25 studs wide, 1.2 tall)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=40, radius1=0.62, radius2=0.62, depth=1.2)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
    # cone is built along Blender Z already (vertical)
    for v in me.vertices: v.co = v.co * S - origin_off
    bv = ob.modifiers.new("Bevel", "BEVEL"); bv.width = 0.24 * S; bv.segments = 6; bv.limit_method = 'ANGLE'
    for p in me.polygons: p.use_smooth = True
    # material: skin with the face decal projected from the front (+Y in Blender)
    m = bpy.data.materials.new(name + "_mat"); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.45
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    # object coords are offset by origin_off; recentre on the head centre
    cx, cy, cz = (-origin_off).x, (-origin_off).y, (-origin_off).z
    ux = nt.nodes.new("ShaderNodeMath"); ux.operation = 'MULTIPLY_ADD'
    nt.links.new(sep.outputs["X"], ux.inputs[0]); ux.inputs[1].default_value = 1 / (1.25 * S); ux.inputs[2].default_value = 0.5 - cx / (1.25 * S)
    uy = nt.nodes.new("ShaderNodeMath"); uy.operation = 'MULTIPLY_ADD'
    nt.links.new(sep.outputs["Z"], uy.inputs[0]); uy.inputs[1].default_value = 1 / (1.25 * S); uy.inputs[2].default_value = 0.5 - cz / (1.25 * S)
    comb = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(ux.outputs[0], comb.inputs[0]); nt.links.new(uy.outputs[0], comb.inputs[1])
    img = bpy.data.images.load(face_png, check_existing=True)
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.extension = 'CLIP'
    nt.links.new(comb.outputs[0], t.inputs[0])
    # only on the front half
    front = nt.nodes.new("ShaderNodeMath"); front.operation = 'GREATER_THAN'
    nt.links.new(sep.outputs["Y"], front.inputs[0]); front.inputs[1].default_value = cy
    a = nt.nodes.new("ShaderNodeMath"); a.operation = 'MULTIPLY'
    nt.links.new(t.outputs["Alpha"], a.inputs[0]); nt.links.new(front.outputs[0], a.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
    mix.inputs["A"].default_value = (*lin(skin_rgb), 1)
    nt.links.new(t.outputs["Color"], mix.inputs["B"]); nt.links.new(a.outputs[0], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    me.materials.append(m)
    return ob

def hair_obj(name, coll, hair_asset, head_obj):
    refs = rbx.rbxm_asset_refs(rbx.fetch(hair_asset))
    mid = (refs.get("MeshId") or refs.get("MeshID"))[0]
    tid = (refs.get("TextureId") or refs.get("TextureID") or [None])[0]
    ver, verts, uvs, faces = rbx.parse_mesh(rbx.fetch(mid))
    sc = Vector(refs.get("_Scale") or (1, 1, 1)); off = Vector(refs.get("_Offset") or (0, 0, 0))
    # handle placement: head HairAttachment (0, 0.6, 0) minus the handle's attachment point
    att = refs.get("_att_HairAttachment") or refs.get("_att_HatAttachment") or refs.get("_AttachmentPoint")
    if att is None:
        ys = [v[1] * sc.y for v in verts]
        att = (0, (max(ys) + min(ys)) / 2 - 0.15, 0)  # fit: sit the hair over the crown
    handle = Vector((0, 0.6, 0)) - Vector(att)
    me = bpy.data.meshes.new(name)
    pts = [rb(Vector((v[0] * sc.x, v[1] * sc.y, v[2] * sc.z)) + off + handle) for v in verts]
    me.from_pydata(pts, [], [tuple(f) for f in faces])
    me.validate(); me.update()
    uvl = me.uv_layers.new()
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
    if tid:
        ob.data.materials.append(image_mat(name + "_mat", rbx.fetch_path(tid, ".png"), rough=0.6))
    ob.parent = head_obj
    return ob

def build(name, pos_bl, c, collection_parent):
    """c: dict(skin, shirt, pants, shoes, hair, face). pos_bl: feet position (Blender m). Returns root empty."""
    col = bpy.data.collections.new(name); collection_parent.children.link(col)
    root = bpy.data.objects.new(name + "_Root", None); root.empty_display_size = 0.4; col.objects.link(root)
    root.location = pos_bl
    skin = flat_mat(name + "_skin", c["skin"]); shirt = flat_mat(name + "_shirt", c["shirt"], 0.7, 0.2)
    pants = flat_mat(name + "_pants", c["pants"], 0.7, 0.2); shoes = flat_mat(name + "_shoes", c["shoes"], 0.5)
    def part(pname, size, center, mat, parent, joint, parent_joint):
        off = rb(Vector(joint)) - rb(Vector(center))
        ob = box_obj(name + "_" + pname, size, col, mat, off)
        ob.parent = parent; ob.location = rb(Vector(joint)) - rb(Vector(parent_joint))
        return ob
    O = (0, 0, 0)
    lt = part("LowerTorso", (2, 0.45, 1), (0, 2.2, 0), pants, root, (0, 2.0, 0), O)
    ut = part("UpperTorso", (2, 1.6, 1), (0, 3.2, 0), shirt, lt, (0, 2.4, 0), (0, 2.0, 0))
    def arm(side, sx):
        ua = part(side + "UpperArm", (1, 1.15, 1), (sx, 3.42, 0), shirt, ut, (sx, 3.85, 0), (0, 2.4, 0))
        la = part(side + "LowerArm", (0.98, 0.62, 0.98), (sx, 2.55, 0), skin, ua, (sx, 2.85, 0), (sx, 3.85, 0))
        h = part(side + "Hand", (0.98, 0.32, 0.98), (sx, 2.1, 0), skin, la, (sx, 2.25, 0), (sx, 2.85, 0))
        return ua, la, h
    def leg(side, sx):
        ul = part(side + "UpperLeg", (1, 1.15, 1), (sx, 1.42, 0), pants, lt, (sx, 2.0, 0), (0, 2.0, 0))
        ll = part(side + "LowerLeg", (0.98, 0.6, 0.98), (sx, 0.55, 0), pants, ul, (sx, 0.85, 0), (sx, 2.0, 0))
        f = part(side + "Foot", (1.0, 0.25, 1.08), (sx, 0.125, -0.04), shoes, ll, (sx, 0.25, 0), (sx, 0.85, 0))
        return ul, ll, f
    arm("Left", -1.5); arm("Right", 1.5); leg("Left", -0.5); leg("Right", 0.5)
    face_png = rbx.fetch_path(c["face"], ".png")
    neck = (0, 4.0, 0); head_c = (0, 4.62, 0)
    head = classic_head(name + "_Head", col, c["skin"], face_png, rb(Vector(neck)) - rb(Vector(head_c)))
    head.parent = ut; head.location = rb(Vector(neck)) - rb(Vector((0, 2.4, 0)))
    # hair is positioned relative to the head centre: wrap in an empty at the head centre
    hc = bpy.data.objects.new(name + "_HeadCenter", None); col.objects.link(hc); hc.parent = head
    hc.location = rb(Vector(head_c)) - rb(Vector(neck)); hc.empty_display_size = 0.1
    hair_obj(name + "_Hair", col, c["hair"], hc)
    return root
