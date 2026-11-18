# Roblox asset helpers for Blender (download + rbxm/mesh parsing)
import os, re, struct, urllib.request, json

CACHE = os.path.join(os.path.expanduser("~"), "Downloads", "BalloonTest", "cache")
os.makedirs(CACHE, exist_ok=True)

def fetch(asset_id):
    asset_id = str(asset_id)
    path = os.path.join(CACHE, asset_id)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return open(path, "rb").read()
    req = urllib.request.Request("https://assetdelivery.roblox.com/v1/asset/?id=" + asset_id,
                                 headers={"User-Agent": "Roblox/WinInet"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    open(path, "wb").write(data)
    return data

def fetch_path(asset_id, ext=""):
    fetch(asset_id)
    p = os.path.join(CACHE, str(asset_id))
    if ext and not os.path.exists(p + ext):
        open(p + ext, "wb").write(open(p, "rb").read())
    return p + ext

# ---------- LZ4 block decompression ----------
def lz4_block(src, usize):
    dst = bytearray(); i = 0; n = len(src)
    while i < n:
        tok = src[i]; i += 1
        lit = tok >> 4
        if lit == 15:
            while True:
                b = src[i]; i += 1; lit += b
                if b != 255: break
        dst += src[i:i + lit]; i += lit
        if i >= n: break
        off = src[i] | (src[i + 1] << 8); i += 2
        ml = tok & 15
        if ml == 15:
            while True:
                b = src[i]; i += 1; ml += b
                if b != 255: break
        ml += 4
        start = len(dst) - off
        for k in range(ml):
            dst.append(dst[start + k])
    return bytes(dst)

def rbxm_chunks(data):
    """yield (name, payload) for binary .rbxm"""
    assert data[:8] == b"<roblox!", "not binary rbxm"
    i = 32
    while i < len(data):
        name = data[i:i + 4]; comp, ucomp = struct.unpack_from("<II", data, i + 4)
        i += 16
        if comp == 0:
            payload = data[i:i + ucomp]; i += ucomp
        else:
            raw = data[i:i + comp]; i += comp
            if raw[:4] == b"\x28\xb5\x2f\xfd":
                raise RuntimeError("zstd chunk not supported")
            payload = lz4_block(raw, ucomp)
        yield name, payload
        if name == b"END\x00": break

def rbxm_asset_refs(data):
    """return {propName: [asset ids]} for mesh/texture-ish properties"""
    refs = {}
    if not data.startswith(b"<roblox!"):
        t = data.decode("utf-8", "ignore")
        for pname, val in re.findall(r'name="(MeshId|TextureId|MeshID|TextureID)">\s*(?:<url>)?([^<]*)', t):
            ids = re.findall(r"(\d{4,})", val)
            if ids: refs.setdefault(pname, []).extend(ids)
        for pname in ("Scale", "Offset"):
            m = re.search(r'<Vector3 name="%s">\s*<X>([^<]+)</X>\s*<Y>([^<]+)</Y>\s*<Z>([^<]+)</Z>' % pname, t)
            if m: refs["_" + pname] = [float(m.group(k)) for k in (1, 2, 3)]
        return refs
    for name, p in rbxm_chunks(data):
        if name != b"PROP": continue
        nl = struct.unpack_from("<I", p, 4)[0]
        pname = p[8:8 + nl].decode("latin1")
        body = p[8 + nl:]
        if any(k in pname for k in ("Mesh", "Texture", "ColorMap", "Shirt", "Pants", "Graphic")):
            ids = re.findall(rb"(?:rbxassetid://|id=)(\d+)", body)
            if ids: refs.setdefault(pname, []).extend(x.decode() for x in ids)
        if pname in ("Scale", "Offset", "Size", "MeshSize"):
            refs.setdefault("_raw_" + pname, []).append(body[:1 + 4 * 12])
    return refs

# ---------- .mesh parsing ----------
def parse_mesh(data):
    head = data[:12]
    ver = data[:13].split(b"\n")[0].decode("latin1").strip()
    nl = data.index(b"\n") + 1
    if ver.startswith("version 1"):
        txt = data.decode("latin1").split("\n")
        nf = int(txt[1]); vals = re.findall(r"\[([^\]]*)\]", txt[2])
        verts, uvs, faces = [], [], []
        scale = 0.5 if ver.startswith("version 1.00") else 1.0
        for k in range(nf * 3):
            p = [float(x) for x in vals[k * 3].split(",")]
            t = [float(x) for x in vals[k * 3 + 2].split(",")]
            verts.append((p[0] * scale, p[1] * scale, p[2] * scale)); uvs.append((t[0], 1 - t[1]))
        faces = [(k * 3, k * 3 + 1, k * 3 + 2) for k in range(nf)]
        return ver, verts, uvs, faces
    b = data[nl:]
    if ver.startswith("version 2"):
        hs, vs, fs = struct.unpack_from("<HBB", b, 0)
        nv, nf = struct.unpack_from("<II", b, 4)
        o = hs; lod = None
    elif ver.startswith("version 3"):
        hs, vs, fs, ls, nlod = struct.unpack_from("<HBBHH", b, 0)
        nv, nf = struct.unpack_from("<II", b, 8)
        o = hs
        lodo = hs + nv * vs + nf * 12
        lod = struct.unpack_from("<%dI" % nlod, b, lodo) if nlod >= 2 else None
    elif ver.startswith("version 4") or ver.startswith("version 5"):
        hs, lodtype, nv, nf, nlod, nbones, bnsz, nsub, nhq, _ = struct.unpack_from("<HHIIHHIHBB", b, 0)
        vs = 40; o = hs
        env = nv * 8 if nbones > 0 else 0
        fo = hs + nv * vs + env
        lodo = fo + nf * 12
        lod = struct.unpack_from("<%dI" % nlod, b, lodo) if nlod >= 2 else None
    else:
        raise RuntimeError("unsupported mesh " + ver)
    verts, uvs = [], []
    for k in range(nv):
        px, py, pz, nx, ny, nz, u, v = struct.unpack_from("<8f", b, o + k * vs)
        verts.append((px, py, pz)); uvs.append((u, 1 - v))
    fo = o + nv * vs + (nv * 8 if ver.startswith(("version 4", "version 5")) and nbones > 0 else 0)
    n_use = nf if not lod else (lod[1] - lod[0])
    start = 0 if not lod else lod[0]
    faces = [struct.unpack_from("<3I", b, fo + (start + k) * 12) for k in range(n_use)]
    return ver, verts, uvs, faces
