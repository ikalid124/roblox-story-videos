# Expressions from a 6x4 atlas (12 expressions + a talking version of each), lip sync, placeholder TTS.
import bpy, os, importlib
import expr2
from expr2 import say, envelope, BASE
from bpy_extras import anim_utils

BASE_EXPR = ["neutral", "happy", "sad", "crying", "angry", "shocked",
             "goofy", "smug", "scared", "laughing", "confused", "evil"]
EXPR = BASE_EXPR + ["talk_" + e for e in BASE_EXPR]
COLS, ROWS = 6, 4

def _lin(c): return tuple(pow(x / 255.0, 2.2) for x in c)

def build_head_material(name, skin_rgb, atlas_file):
    head = bpy.data.objects[name + "_Head"]
    m = bpy.data.materials.new(name + "_HeadFace"); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.45
    L = nt.links.new
    def math(op, a, bb=None):
        n = nt.nodes.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, bb)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L(v, n.inputs[i])
        return n.outputs[0]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L(tc.outputs["Object"], sep.inputs[0])
    S = 0.375          # head width in metres (1.25 studs)
    CZ = 0.186         # head centre above the neck origin
    u = math('ADD', math('DIVIDE', sep.outputs["X"], S), 0.5)
    v = math('ADD', math('DIVIDE', math('SUBTRACT', sep.outputs["Z"], CZ), S), 0.5)
    front = math('GREATER_THAN', sep.outputs["Y"], 0.0)
    inside = math('MULTIPLY', math('MULTIPLY', math('GREATER_THAN', u, 0.0), math('LESS_THAN', u, 1.0)),
                  math('MULTIPLY', math('GREATER_THAN', v, 0.0), math('LESS_THAN', v, 1.0)))
    attr = nt.nodes.new("ShaderNodeAttribute"); attr.attribute_type = 'OBJECT'; attr.attribute_name = "expr"
    e = math('ROUND', attr.outputs["Fac"])
    row = math('FLOOR', math('DIVIDE', e, float(COLS)))
    col = math('SUBTRACT', e, math('MULTIPLY', row, float(COLS)))
    uc = math('MINIMUM', math('MAXIMUM', u, 0.002), 0.998); vc = math('MINIMUM', math('MAXIMUM', v, 0.002), 0.998)
    U = math('DIVIDE', math('ADD', uc, col), float(COLS))
    V = math('DIVIDE', math('ADD', vc, math('SUBTRACT', float(ROWS - 1), row)), float(ROWS))
    cxyz = nt.nodes.new("ShaderNodeCombineXYZ"); L(U, cxyz.inputs[0]); L(V, cxyz.inputs[1])
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.extension = 'CLIP'; tex.interpolation = 'Linear'
    tex.image = bpy.data.images.load(os.path.join(BASE, "faces", atlas_file), check_existing=True)
    L(cxyz.outputs[0], tex.inputs[0])
    a = math('MULTIPLY', math('MULTIPLY', tex.outputs["Alpha"], front), inside)
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
    mix.inputs["A"].default_value = (*_lin(skin_rgb), 1); L(tex.outputs["Color"], mix.inputs["B"]); L(a, mix.inputs["Factor"])
    L(mix.outputs["Result"], b.inputs["Base Color"])
    head.data.materials.clear(); head.data.materials.append(m)
    if "expr" not in head: head["expr"] = 0.0
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

def lipsync(name, wav, start, base, fps=30, thresh=0.22, hold=2):
    env = envelope(wav, fps); talk = "talk_" + base
    state = None; last = -99
    for i, val in enumerate(env):
        want = talk if val > thresh else base
        if want == talk and state == talk and i - last >= 5: want = base
        if want != state and i - last >= hold:
            key(name, start + i, want); state = want; last = i
    key(name, start + len(env), base)
    return len(env)
