# Expressions (4x4 atlas) + amplitude lip sync + Windows SAPI placeholder voice.
import bpy, os, wave, struct, subprocess, math
from bpy_extras import anim_utils

EXPR = ["neutral", "happy", "sad", "crying", "angry", "shocked",
        "goofy", "smug", "scared", "laughing", "confused", "evil",
        "talk_neutral", "talk_happy", "talk_sad", "talk_angry"]
TALKABLE = {"neutral": "talk_neutral", "happy": "talk_happy", "sad": "talk_sad", "angry": "talk_angry",
            "smug": "talk_happy", "confused": "talk_neutral", "scared": "talk_sad", "shocked": "talk_neutral",
            "laughing": "talk_happy", "evil": "talk_angry", "crying": "talk_sad", "goofy": "talk_happy"}
BASE = os.path.join(os.path.expanduser("~"), "Downloads", "BalloonTest")

def use_atlas(name, filename):
    """Point a head (already set up by expr.setup) at a 4x4 atlas."""
    head = bpy.data.objects[name + "_Head"]; nt = head.data.materials[0].node_tree
    tex = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]
    tex.image = bpy.data.images.load(os.path.join(BASE, "faces", filename), check_existing=True)
    for n in nt.nodes:
        if n.type != 'MATH': continue
        if n.operation == 'SUBTRACT' and not n.inputs[0].is_linked and abs(n.inputs[0].default_value - 2.0) < 1e-6:
            n.inputs[0].default_value = 3.0
        if n.operation == 'DIVIDE' and not n.inputs[1].is_linked and abs(n.inputs[1].default_value - 3.0) < 1e-6:
            n.inputs[1].default_value = 4.0
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

def say(text, path, voice="Microsoft Zira Desktop", rate=1):
    """Placeholder TTS with the Windows built-in voices (swap for ElevenLabs later)."""
    t = text.replace("'", "''")
    ps = ("Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
          f"try {{ $s.SelectVoice('{voice}') }} catch {{}}; $s.Rate = {rate}; "
          f"$s.SetOutputToWaveFile('{path}'); $s.Speak('{t}'); $s.Dispose()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, timeout=60,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return path

def envelope(path, fps):
    """Per-frame loudness (0..1) of a mono/stereo 16-bit wav."""
    with wave.open(path) as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        raw = w.readframes(n)
    vals = struct.unpack("<%dh" % (len(raw) // 2), raw)[::ch]
    step = sr / fps; out = []
    i = 0.0
    while int(i) < len(vals):
        seg = vals[int(i):int(i + step)]
        out.append(math.sqrt(sum(v * v for v in seg) / max(1, len(seg))) / 32768.0)
        i += step
    peak = max(out) or 1.0
    return [v / peak for v in out]

def lipsync(name, wav, start, base, fps=30, thresh=0.22, hold=2):
    """Toggle base <-> talking mouth on syllables. Returns the line's length in frames."""
    env = envelope(wav, fps); talk = TALKABLE.get(base, "talk_neutral")
    state = None; last = -99
    for i, v in enumerate(env):
        want = talk if v > thresh else base
        # flap the mouth on long vowels so it does not freeze open
        if want == talk and state == talk and i - last >= 5: want = base
        if want != state and i - last >= hold:
            key(name, start + i, want); state = want; last = i
    key(name, start + len(env), base)
    return len(env)
