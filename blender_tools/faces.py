# Classic-Roblox-style expression atlases, one consistent style per character.
# Atlas: 4 columns x 3 rows of 512px cells, transparent background.
import math, json, sys
from PIL import Image, ImageDraw, ImageFilter

EXPR = ["neutral", "happy", "sad", "crying", "angry", "shocked",
        "goofy", "smug", "scared", "laughing", "confused", "evil"]
EXPR = EXPR + ["talk_" + e for e in EXPR]
SS = 4            # supersample
C = 512 * SS      # cell size while drawing
BLACK = (22, 22, 26, 255)
WHITE = (255, 255, 255, 255)
MOUTH_IN = (60, 18, 24, 255)
TONGUE = (205, 92, 104, 255)
TEAR = (120, 200, 255, 235)

K = 1.45  # feature scale around the cell centre
def P(x, y): return ((0.5 + (x - 0.5) * K) * C, (0.5 + (y - 0.5) * K) * C)
def W(w): return max(1, int(w * K * C))

def arc_pts(cx, cy, rx, ry, a0, a1, n=48):
    return [P(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
              cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

def thick(d, pts, w, col):
    d.line(pts, fill=col, width=W(w), joint="curve")
    r = W(w) / 2
    for p in (pts[0], pts[-1]):
        d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=col)

class Face:
    def __init__(self, st):
        self.st = st
        self.img = Image.new("RGBA", (C, C), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    # ---------- eyes ----------
    def eye(self, side, kind="normal", look=(0, 0)):
        st = self.st; d = self.d
        cx = 0.5 + side * st["eye_dx"]; cy = st["eye_y"]
        rx, ry = st["eye_rx"], st["eye_ry"]
        if st.get("round"): ry = rx * 1.12
        if kind in ("normal", "half", "narrow", "evil", "big"):
            if kind == "big": rx, ry = rx * 1.25, ry * 1.2
            box = (P(cx - rx, cy - ry)[0], P(cx - rx, cy - ry)[1], P(cx + rx, cy + ry)[0], P(cx + rx, cy + ry)[1])
            layer = Image.new("L", (C, C), 0); ld = ImageDraw.Draw(layer)
            ld.ellipse(box, fill=255)
            if kind == "half":   # flat lid cutting the top 45%
                ld.rectangle((0, 0, C, P(0, cy - ry + 2 * ry * 0.45)[1]), fill=0)
            if kind in ("narrow", "evil"):  # slanted lid, low on the inner side
                inner = cx - side * rx; outer = cx + side * rx
                top_in = cy + ry * (0.15 if kind == "narrow" else 0.0); top_out = cy - ry * 0.35
                ld.polygon([(P(inner, 0)[0], 0), (P(outer, 0)[0], 0), P(outer, top_out), P(inner, top_in)], fill=0)
            self.img.paste(Image.new("RGBA", (C, C), BLACK), (0, 0), layer)
            if kind not in ("narrow", "evil"):
                hx = cx - rx * 0.3 + look[0] * rx * 0.2; hy = cy - ry * (0.35 if kind != "half" else -0.05)
                r = rx * 0.32
                d.ellipse((*P(hx - r, hy - r), *P(hx + r, hy + r)), fill=WHITE)
            if st.get("lashes") and kind in ("normal", "big", "half"):
                ox = cx + side * rx * 0.75; oy = cy - ry * (0.75 if kind != "half" else 0.05)
                thick(d, [P(ox, oy), P(ox + side * rx * 0.55, oy - ry * 0.35)], 0.011, BLACK)
                thick(d, [P(ox - side * rx * 0.2, oy - ry * 0.12), P(ox + side * rx * 0.3, oy - ry * 0.6)], 0.011, BLACK)
        elif kind in ("wide", "tiny"):  # white eyeball with outline, small pupil
            r = rx * (1.45 if kind == "wide" else 1.25)
            d.ellipse((*P(cx - r, cy - r * 1.15), *P(cx + r, cy + r * 1.15)), fill=WHITE, outline=BLACK, width=W(0.012))
            pr = rx * (0.42 if kind == "wide" else 0.28)
            px = cx + look[0] * r * 0.4; py = cy + look[1] * r * 0.4
            d.ellipse((*P(px - pr, py - pr), *P(px + pr, py + pr)), fill=BLACK)
        elif kind == "happy":   # closed ^ arc
            thick(self.d, arc_pts(cx, cy + ry * 0.35, rx * 1.05, ry * 0.75, 200, 340), 0.022, BLACK)
        elif kind == "squeeze":  # >  < laughing
            a = rx * 1.0
            pts = [P(cx + side * a * 0.8, cy - ry * 0.5), P(cx - side * a * 0.6, cy), P(cx + side * a * 0.8, cy + ry * 0.5)]
            thick(self.d, pts, 0.02, BLACK)
        elif kind == "sadclosed":  # crying closed arc (curved down)
            thick(self.d, arc_pts(cx, cy - ry * 0.1, rx * 1.05, ry * 0.6, 20, 160), 0.02, BLACK)

    # ---------- brows ----------
    def brow(self, side, tilt=0.0, raise_=0.0, curve=0.0):
        st = self.st
        cx = 0.5 + side * st["eye_dx"]; cy = st["eye_y"] - st["eye_ry"] - 0.045 - raise_
        L = st["brow_len"]
        inner = (cx - side * L / 2, cy + tilt * 0.06)       # +tilt = inner end down (angry)
        outer = (cx + side * L / 2, cy - tilt * 0.02)
        mid = ((inner[0] + outer[0]) / 2, (inner[1] + outer[1]) / 2 - curve * 0.02)
        pts = [P(*inner), P(*mid), P(*outer)]
        thick(self.d, pts, st["brow_w"], st["brow_col"])

    # ---------- mouths ----------
    def mouth(self, kind):
        st = self.st; d = self.d; lip = st["lip"]
        cx, cy, mw = 0.5, st["mouth_y"], st["mouth_w"]
        if kind == "smile":
            thick(d, arc_pts(cx, cy - 0.03, mw * 0.55, 0.05, 20, 160), 0.018, BLACK)
        elif kind == "frown":
            thick(d, arc_pts(cx, cy + 0.04, mw * 0.45, 0.04, 200, 340), 0.018, BLACK)
        elif kind in ("grin", "laugh", "tongue", "evilgrin"):
            w = mw * (0.62 if kind != "evilgrin" else 0.78)
            h = {"grin": 0.085, "laugh": 0.13, "tongue": 0.1, "evilgrin": 0.1}[kind]
            top = cy - 0.03
            box = (*P(cx - w, top - h), *P(cx + w, top + h))
            mask = Image.new("L", (C, C), 0); md = ImageDraw.Draw(mask)
            md.chord(box, 0, 180, fill=255)
            if kind == "evilgrin":
                md.chord((*P(cx - w, top - h * 0.6), *P(cx + w, top + h * 0.5)), 0, 180, fill=0)
            inside = Image.new("RGBA", (C, C), (0, 0, 0, 0)); idr = ImageDraw.Draw(inside)
            idr.rectangle((0, 0, C, C), fill=MOUTH_IN)
            if kind in ("grin", "laugh", "evilgrin"):
                idr.rectangle((0, 0, C, P(0, top + h * (0.28 if kind != "evilgrin" else 0.6))[1]), fill=WHITE)
            if kind in ("laugh", "tongue"):
                tw = w * 0.55; ty = top + h * (0.95 if kind == "laugh" else 0.75)
                idr.ellipse((*P(cx - tw, ty - h * 0.45), *P(cx + tw, ty + h * 0.55)), fill=TONGUE)
            if kind == "evilgrin":
                for i in range(1, 6):
                    x = cx - w + 2 * w * i / 6
                    idr.line((*P(x, top), *P(x, top + h)), fill=(200, 200, 200, 255), width=W(0.004))
            self.img.paste(inside, (0, 0), mask)
            # lip-coloured outline
            d.chord(box, 0, 180, outline=lip, width=W(0.011))
            if kind == "tongue":  # tongue sticking out below the lip
                tw = w * 0.38
                d.ellipse((*P(cx + w * 0.15 - tw, top + h * 0.7), *P(cx + w * 0.15 + tw, top + h * 1.55)), fill=TONGUE, outline=lip, width=W(0.008))
                d.line((*P(cx + w * 0.15, top + h * 0.95), *P(cx + w * 0.15, top + h * 1.35)), fill=(170, 60, 75, 255), width=W(0.006))
        elif kind == "speak":
            rx, ry, top = 0.06, 0.038, cy + 0.005
            d.chord((*P(cx - rx, top - ry), *P(cx + rx, top + ry)), 0, 360, fill=MOUTH_IN, outline=lip, width=W(0.011))
            d.chord((*P(cx - rx * 0.6, top), *P(cx + rx * 0.6, top + ry * 0.95)), 0, 180, fill=TONGUE)
        elif kind in ("o", "bigo"):
            rx = 0.045 if kind == "o" else 0.06; ry = 0.06 if kind == "o" else 0.085
            d.ellipse((*P(cx - rx, cy - ry), *P(cx + rx, cy + ry)), fill=MOUTH_IN, outline=lip, width=W(0.011))
        elif kind == "wail":  # crying open trapezoid frown
            w = mw * 0.5; h = 0.09; top = cy - 0.02
            pts = [P(cx - w * 0.55, top), P(cx + w * 0.55, top), P(cx + w, top + h), P(cx - w, top + h)]
            d.polygon(pts, fill=MOUTH_IN, outline=lip, width=W(0.011))
            d.ellipse((*P(cx - w * 0.45, top + h * 0.55), *P(cx + w * 0.45, top + h * 1.0)), fill=TONGUE)
            d.line([pts[2], pts[3]], fill=lip, width=W(0.011))
        elif kind == "gritted":
            w = mw * 0.5; h = 0.055; top = cy - 0.02
            d.rounded_rectangle((*P(cx - w, top), *P(cx + w, top + h)), radius=W(0.02), fill=WHITE, outline=lip, width=W(0.011))
            d.line((*P(cx - w, top + h / 2), *P(cx + w, top + h / 2)), fill=(150, 150, 150, 255), width=W(0.005))
            for i in range(1, 5):
                x = cx - w + 2 * w * i / 5
                d.line((*P(x, top), *P(x, top + h)), fill=(150, 150, 150, 255), width=W(0.005))
        elif kind == "smirk":
            p0 = (cx - mw * 0.38, cy + 0.005); p1 = (cx + mw * 0.05, cy + 0.035); p2 = (cx + mw * 0.42, cy - 0.04)
            pts = [P((1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t*t*p2[0], (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t*t*p2[1]) for t in [i/30 for i in range(31)]]
            thick(d, pts, 0.017, BLACK)
        elif kind == "wavy":
            pts = [P(cx - mw * 0.4 + mw * 0.8 * i / 40, cy + 0.012 * math.sin(i / 40 * math.pi * 4)) for i in range(41)]
            thick(d, pts, 0.016, BLACK)
        elif kind == "squiggle":
            pts = [P(cx - mw * 0.3 + mw * 0.6 * i / 40, cy + 0.01 * math.sin(i / 40 * math.pi * 2.5) + 0.02 * i / 40) for i in range(41)]
            thick(d, pts, 0.016, BLACK)

    def tears(self, streams=True):
        st = self.st
        for side in (-1, 1):
            cx = 0.5 + side * st["eye_dx"]; y0 = st["eye_y"] + st["eye_ry"] * 0.6
            if streams:
                self.d.polygon([P(cx - 0.012, y0), P(cx + 0.012, y0), P(cx + 0.024, 0.8), P(cx - 0.024, 0.8)], fill=TEAR); self.d.ellipse((*P(cx - 0.024, 0.78), *P(cx + 0.024, 0.82)), fill=TEAR)
            else:
                self.d.ellipse((*P(cx + side * 0.04 - 0.014, y0), *P(cx + side * 0.04 + 0.014, y0 + 0.04)), fill=TEAR)

    def sweat(self):
        x, y = 0.72, 0.24
        self.d.polygon([P(x, y - 0.05), P(x - 0.025, y + 0.01), P(x + 0.025, y + 0.01)], fill=TEAR)
        self.d.ellipse((*P(x - 0.026, y - 0.015), *P(x + 0.026, y + 0.035)), fill=TEAR)

    def blush(self, a=110):
        col = (*self.st["blush"], a)
        for side in (-1, 1):
            cx = 0.5 + side * (self.st["eye_dx"] + 0.04); cy = self.st["eye_y"] + 0.11
            self.d.ellipse((*P(cx - 0.05, cy - 0.022), *P(cx + 0.05, cy + 0.022)), fill=col)

    def extras(self, e):
        st = self.st; d = self.d
        if st.get("freckles"):
            col = (*st["freckle_col"], 200)
            for side in (-1, 1):
                for dx, dy in ((0.0, 0.0), (0.03, 0.02), (-0.025, 0.025), (0.012, 0.045), (0.045, -0.01)):
                    x = 0.5 + side * (st["eye_dx"] + 0.02 + dx); y = st["eye_y"] + 0.1 + dy
                    d.ellipse((*P(x - 0.0065, y - 0.0065), *P(x + 0.0065, y + 0.0065)), fill=col)
        if st.get("bags") and e not in ("happy", "laughing", "crying"):
            for side in (-1, 1):
                cx = 0.5 + side * st["eye_dx"]; cy = st["eye_y"] + st["eye_ry"] + 0.018
                thick(d, arc_pts(cx, cy - 0.012, st["eye_rx"] * 1.1, 0.014, 25, 155), 0.007, (*st["bag_col"], 255))
        if st.get("mustache"):
            col = (*st["mustache"], 255); my = st["mouth_y"] - 0.045
            for side in (-1, 1):
                pts = [P(0.5, my - 0.005), P(0.5 + side * 0.05, my - 0.018), P(0.5 + side * 0.105, my + 0.012),
                       P(0.5 + side * 0.07, my + 0.022), P(0.5 + side * 0.02, my + 0.012), P(0.5, my + 0.008)]
                d.polygon(pts, fill=col)
        if st.get("gap"):
            pass

    def out(self):
        return self.img.resize((512, 512), Image.LANCZOS)

def draw(st, e):
    M = None
    if e.startswith("talk_"):
        e, M = e[5:], {"neutral": "speak", "happy": "laugh", "sad": "wail", "crying": "wail", "angry": "laugh",
                      "shocked": "o", "goofy": "laugh", "smug": "speak", "scared": "wail", "laughing": "grin",
                      "confused": "speak", "evil": "laugh"}[e[5:]]
    f = Face(st)
    if e == "neutral":
        for s in (-1, 1): f.eye(s); f.brow(s)
        f.mouth(M or "smile")
    elif e == "happy":
        f.blush()
        for s in (-1, 1): f.eye(s, "happy")
        f.mouth(M or "grin")
    elif e == "sad":
        for s in (-1, 1): f.eye(s, "half"); f.brow(s, tilt=-0.9, raise_=0.01)
        f.mouth(M or "frown"); f.tears(streams=False)
    elif e == "crying":
        for s in (-1, 1): f.eye(s, "sadclosed"); f.brow(s, tilt=-1.0, raise_=0.015)
        f.tears(True); f.mouth(M or "wail")
    elif e == "angry":
        for s in (-1, 1): f.eye(s, "narrow"); f.brow(s, tilt=1.1, raise_=-0.01)
        f.mouth(M or "gritted")
    elif e == "shocked":
        for s in (-1, 1): f.eye(s, "wide"); f.brow(s, raise_=0.05, curve=1.2)
        f.mouth(M or "bigo")
    elif e == "goofy":
        f.eye(-1, "wide", look=(0.5, -0.3)); f.eye(1, "tiny", look=(-0.6, 0.4))
        f.brow(-1, raise_=0.05, curve=1); f.brow(1, tilt=0.6)
        f.mouth(M or "tongue")
    elif e == "smug":
        for s in (-1, 1): f.eye(s, "half", look=(1, 0))
        f.brow(-1, raise_=0.03, curve=0.8); f.brow(1, tilt=0.3)
        f.mouth(M or "smirk")
    elif e == "scared":
        for s in (-1, 1): f.eye(s, "tiny"); f.brow(s, tilt=-1.0, raise_=0.04)
        f.mouth(M or "wavy"); f.sweat()
    elif e == "laughing":
        f.blush(140)
        for s in (-1, 1): f.eye(s, "squeeze")
        f.mouth(M or "laugh")
    elif e == "confused":
        f.eye(-1); f.eye(1, "half")
        f.brow(-1, raise_=0.06, curve=1.3); f.brow(1, tilt=0.5)
        f.mouth(M or "squiggle")
    elif e == "evil":
        for s in (-1, 1): f.eye(s, "evil"); f.brow(s, tilt=1.3, raise_=-0.015)
        f.mouth(M or "evilgrin")
    f.extras(e)
    return f.out()

def style(skin, lashes=False, brow_col=(30, 22, 18), big=1.0):
    r, g, b = skin
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    if lum < 150:   # deeper skin: lips are a deeper shade of the skin, not pink
        lip = (int(r * 0.62 + 12), int(g * 0.52), int(b * 0.55), 255)
        blush = (int(r * 0.75 + 30), int(g * 0.45), int(b * 0.45))
    else:
        lip = (int(r * 0.82 + 20), int(g * 0.6), int(b * 0.6), 255)
        blush = (255, 140, 150)
    return dict(eye_dx=0.11, eye_y=0.43, eye_rx=0.038 * big, eye_ry=0.058 * big, brow_len=0.085, brow_w=0.016,
                brow_col=(*brow_col, 255), mouth_y=0.63, mouth_w=0.25, lip=lip, blush=blush, lashes=lashes)

CAST = {
    "Maya":    style((141, 96, 66), lashes=True),
    "Ezra":    style((234, 196, 160), brow_col=(70, 45, 25)),
    "Grandpa": style((220, 180, 145), brow_col=(150, 150, 150)),
    "KidA":    style((200, 150, 110), lashes=True, brow_col=(170, 120, 50), big=1.12),
    "KidB":    style((105, 70, 50), big=1.12),
}
CAST["Ezra"].update(eye_rx=0.034, eye_ry=0.047, brow_w=0.02, round=True)
CAST["Grandpa"].update(brow_w=0.026, brow_len=0.105, eye_rx=0.03, eye_ry=0.04, bags=True, bag_col=(170, 125, 100),
                       mustache=(175, 175, 178), mouth_y=0.66)
CAST["Teacher"] = style((190, 140, 100), lashes=True, brow_col=(60, 40, 30))
CAST["Principal"] = style((120, 85, 60), brow_col=(30, 25, 20))
CAST["Principal"].update(mustache=(35, 30, 28), mouth_y=0.66, brow_w=0.022, eye_rx=0.033, eye_ry=0.045)
CAST["Photographer"] = style((230, 190, 150), brow_col=(110, 70, 40))
CAST["Dad"] = style((141, 96, 66), brow_col=(25, 20, 18))
CAST["Dad"].update(brow_w=0.022, eye_rx=0.034, eye_ry=0.046)
CAST["Kid3"] = style((230, 190, 160), lashes=True, brow_col=(40, 30, 25), big=1.12)
CAST["KidA"].update(freckles=True, freckle_col=(150, 90, 55))
CAST["KidB"].update(round=True, eye_rx=0.044, brow_w=0.018)

if __name__ == "__main__":
    out = sys.argv[1]
    for name, st in CAST.items():
        atlas = Image.new("RGBA", (3072, 2048), (0, 0, 0, 0))
        for i, e in enumerate(EXPR):
            atlas.paste(draw(st, e), ((i % 6) * 512, (i // 6) * 512))
        atlas.save(f"{out}/faces4_{name}.png")
    json.dump(EXPR, open(f"{out}/faces_index.json", "w"))
    print("ok")
