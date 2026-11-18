# Keyframeable expressions: each head reads a 4x3 face atlas; the head object's "expr" property picks the cell.
import bpy, os
from bpy_extras import anim_utils

EXPR = ["neutral", "happy", "sad", "crying", "angry", "shocked",
        "goofy", "smug", "scared", "laughing", "confused", "evil"]
FACES = os.path.join(os.path.expanduser("~"), "Downloads", "BalloonTest", "faces")

def setup(name):
    head = bpy.data.objects[name + "_Head"]
    m = head.data.materials[0]; nt = m.node_tree
    if m.get("_atlas"): return head
    tex = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]
    comb = [n for n in nt.nodes if n.type == 'COMBXYZ'][0]
    tex.image = bpy.data.images.load(os.path.join(FACES, "faces_%s.png" % name), check_existing=True)
    tex.interpolation = 'Linear'; tex.extension = 'CLIP'
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(comb.outputs[0], sep.inputs[0])
    attr = nt.nodes.new("ShaderNodeAttribute"); attr.attribute_type = 'OBJECT'; attr.attribute_name = "expr"
    def math(op, a, b=None, c=None):
        n = nt.nodes.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: nt.links.new(v, n.inputs[i])
        return n.outputs[0]
    e = math('ROUND', attr.outputs["Fac"])
    row = math('FLOOR', math('DIVIDE', e, 4.0))
    col = math('SUBTRACT', e, math('MULTIPLY', row, 4.0))
    u = sep.outputs["X"]; v = sep.outputs["Y"]
    inside = math('MULTIPLY', math('MULTIPLY', math('GREATER_THAN', u, 0.0), math('LESS_THAN', u, 1.0)),
                  math('MULTIPLY', math('GREATER_THAN', v, 0.0), math('LESS_THAN', v, 1.0)))
    uc = math('MINIMUM', math('MAXIMUM', u, 0.002), 0.998); vc = math('MINIMUM', math('MAXIMUM', v, 0.002), 0.998)
    U = math('DIVIDE', math('ADD', uc, col), 4.0)
    V = math('DIVIDE', math('ADD', vc, math('SUBTRACT', 2.0, row)), 3.0)
    c2 = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(U, c2.inputs[0]); nt.links.new(V, c2.inputs[1])
    nt.links.new(c2.outputs[0], tex.inputs[0])
    # gate the decal alpha to the cell
    mul = [n for n in nt.nodes if n.type == 'MATH' and n.operation == 'MULTIPLY' and n.inputs[0].links and n.inputs[0].links[0].from_node == tex][0]
    gated = math('MULTIPLY', mul.outputs[0], inside)
    mix = [n for n in nt.nodes if n.type == 'MIX'][0]
    nt.links.new(gated, mix.inputs["Factor"])
    m["_atlas"] = 1
    head["expr"] = 0.0
    return head

def key(name, frame, expression):
    head = bpy.data.objects[name + "_Head"]
    head["expr"] = float(EXPR.index(expression))
    head.keyframe_insert('["expr"]', frame=frame)
    ad = head.animation_data
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    for fc in cb.fcurves:
        if fc.data_path == '["expr"]':
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
