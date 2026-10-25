"""White rabbit variant of rabbit_rigged.glb (Boss 25/10/2026: «chưa thấy thỏ trắng trong world, remove thỏ nâu»).
Only the fur material changes (rig, weights, 4 actions untouched): tan fur (0.659, 0.549, 0.439 linear) → ivory white, matching the
«Lông Trắng Ngà & Kem» look of showcase_rabbits.png. python3 make_white_variant.py → rabbit_white_rigged.glb"""
import json, struct
SRC, DST = "rabbit_rigged.glb", "rabbit_white_rigged.glb"
FUR = [0.86, 0.82, 0.74]          # sRGB ≈ 238, 233, 222 ivory
b = open(SRC, "rb").read()
n = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + n]); rest = b[20 + n:]
hit = [m for m in j["materials"] if m.get("name") == "fur"]
assert hit, "no fur material"
for m in hit: m["pbrMetallicRoughness"]["baseColorFactor"][:3] = FUR
js = json.dumps(j, separators=(",", ":")).encode(); js += b" " * (-len(js) % 4)
out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + len(rest)) + struct.pack("<II", len(js), 0x4E4F534A) + js + rest
open(DST, "wb").write(out); print("ok", DST, len(out))
