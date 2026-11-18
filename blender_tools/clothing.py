# Classic Roblox shirt/pants templates mapped onto the R15 box rig built by avatar.py
import bpy, re
from mathutils import Vector
import rbxt as rbx

TW, TH = 585.0, 559.0
# template rects (x, y, w, h) in pixels
TORSO = {"up": (231, 8, 128, 64), "+x": (165, 74, 64, 128), "front": (231, 74, 128, 128),
         "-x": (361, 74, 64, 128), "back": (427, 74, 128, 128), "down": (231, 204, 128, 64)}
RARM = {"up": (217, 289, 64, 64), "-x": (19, 355, 64, 128), "back": (85, 355, 64, 128),
        "+x": (151, 355, 64, 128), "front": (217, 355, 64, 128), "down": (217, 485, 64, 64)}
LARM = {"up": (308, 289, 64, 64), "front": (308, 355, 64, 128), "-x": (374, 355, 64, 128),
        "back": (440, 355, 64, 128), "+x": (506, 355, 64, 128), "down": (308, 485, 64, 64)}

def template_id(asset_id):
    data = rbx.fetch(asset_id)
    t = data.decode("utf-8", "ignore")
    m = re.search(r'(?:Shirt|Pants)Template">\s*(?:<url>)?[^<\d]*(\d{4,})', t)
    if m: return m.group(1)
    m = re.findall(r'(?:rbxassetid://|id=)(\d{4,})', t)
    return m[0] if m else None

def _lin(c): return tuple(pow(x / 255.0, 2.2) for x in c)

def _uv(ob, rects, a, b, top, bottom):
    """Assign UVs on a box object. a..b = vertical fraction of the limb this part covers (0 = top)."""
    me = ob.data
    uvl = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    co = [v.co.copy() for v in me.vertices]
    xs = [c.x for c in co]; ys = [c.y for c in co]; zs = [c.z for c in co]
    mn = Vector((min(xs), min(ys), min(zs))); mx = Vector((max(xs), max(ys), max(zs)))
    sz = mx - mn
    def nx(c): return (c.x - mn.x) / sz.x
    def ny(c): return (c.y - mn.y) / sz.y
    def nz(c): return (c.z - mn.z) / sz.z
    for p in me.polygons:
        n = p.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        if ax == 2:
            key = "up" if n.z > 0 else "down"
        elif ax == 1:
            key = "front" if n.y > 0 else "back"
        else:
            key = "+x" if n.x > 0 else "-x"
        x0, y0, w, h = rects[key]
        for li in p.loop_indices:
            c = co[me.loops[li].vertex_index]
            if key == "front":   u, t = 1 - nx(c), nz(c)          # viewer right = -X
            elif key == "back":  u, t = nx(c), nz(c)              # viewer right = +X
            elif key == "+x":    u, t = ny(c), nz(c)              # viewer right = +Y
            elif key == "-x":    u, t = 1 - ny(c), nz(c)          # viewer right = -Y
            elif key == "up":    u, t = 1 - nx(c), 1 - ny(c)      # front edge at bottom of rect
            else:                u, t = 1 - nx(c), ny(c)          # down: front edge at top of rect
            if key in ("up", "down"):
                if (key == "up" and not top) or (key == "down" and not bottom):
                    # hidden joint cap: sample a thin strip of the front face
                    fx0, fy0, fw, fh = rects["front"]; px = fx0 + fw * u; py = fy0 + fh * (a if key == "up" else b)
                else:
                    px = x0 + w * u; py = y0 + h * (1 - t)
            else:
                px = x0 + w * u; py = y0 + h * (a + (1 - t) * (b - a))
            uvl.data[li].uv = (px / TW, 1 - py / TH)

def _mat(name, base_rgb, layers):
    """layers: list of image paths, composited in order over the base colour using their alpha."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.6
    try: b.inputs["Specular IOR Level"].default_value = 0.25
    except Exception: pass
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "UVMap"
    prev = None
    col = nt.nodes.new("ShaderNodeRGB"); col.outputs[0].default_value = (*_lin(base_rgb), 1); prev = col.outputs[0]
    for path in layers:
        img = bpy.data.images.load(path, check_existing=True)
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.interpolation = 'Linear'; t.extension = 'CLIP'
        nt.links.new(uvn.outputs[0], t.inputs[0])
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
        nt.links.new(prev, mix.inputs["A"]); nt.links.new(t.outputs["Color"], mix.inputs["B"])
        nt.links.new(t.outputs["Alpha"], mix.inputs["Factor"])
        prev = mix.outputs["Result"]
    nt.links.new(prev, b.inputs["Base Color"])
    return m

def apply(name, skin_rgb, shirt_asset=None, pants_asset=None):
    shirt = rbx.fetch_path(template_id(shirt_asset), ".png") if shirt_asset else None
    pants = rbx.fetch_path(template_id(pants_asset), ".png") if pants_asset else None
    O = lambda p: bpy.data.objects[name + "_" + p]
    torso_layers = [x for x in (pants, shirt) if x]
    # torso: Upper covers top 78%, Lower the rest
    for part, a, b, top, bot in (("UpperTorso", 0, 0.78, True, False), ("LowerTorso", 0.78, 1, False, True)):
        ob = O(part); _uv(ob, TORSO, a, b, top, bot)
        ob.data.materials.clear(); ob.data.materials.append(_mat(ob.name + "_cloth", skin_rgb, torso_layers))
    limb = (("Upper", 0, 0.55, True, False), ("Lower", 0.55, 0.85, False, False), ("Hand", 0.85, 1, False, True))
    leg = (("UpperLeg", 0, 0.55, True, False), ("LowerLeg", 0.55, 0.88, False, False), ("Foot", 0.88, 1, False, True))
    for side, rects in (("Right", RARM), ("Left", LARM)):
        for suf, a, b, top, bot in limb:
            pn = side + (suf + "Arm" if suf != "Hand" else "Hand")
            ob = O(pn); _uv(ob, rects, a, b, top, bot)
            ob.data.materials.clear(); ob.data.materials.append(_mat(ob.name + "_cloth", skin_rgb, [shirt] if shirt else []))
        for suf, a, b, top, bot in leg:
            ob = O(side + suf); _uv(ob, rects, a, b, top, bot)
            ob.data.materials.clear(); ob.data.materials.append(_mat(ob.name + "_cloth", skin_rgb, [pants] if pants else []))
    return shirt, pants
