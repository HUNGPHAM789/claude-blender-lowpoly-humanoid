"""MEAT STORAGE «kho thịt» (Boss 23/10/2026: «Storage stacking display thịt») — open, cozy smoking rack + slatted table.
Back: 4 posts, thatched gable roof on two trusses, hook bar with 8 iron hooks (one haunch each, bone up) over a stone fire ring.
Front: slatted table with 2 brick-stacked piles 4-3-2-1 (10 cuts each). Total 28 cuts = 2×10 + 8.
Slot positions/rotations + fill order come ONLY from settler-storage/scripts/storage.py (o_chua_thit, ma_tran_thit); the layout gate
kho.soi_thit runs inside `lpms render` via META["soi"] (penetration ≤ 5 mm, every cut rests or hangs) ⇒ fail = exit 1.
Stock parts: thit_<NN>_<part>, NN = fill index; storage with Q cuts shows NN < Q (withdraw from the highest NN)."""
import os, sys, math
sys.path[:0] = [os.path.expanduser("~/.hermes/skills/creative/settler-storage/scripts"), os.path.expanduser("~/projects/lpm-faceless-humanoid/lpms/assets")]
import storage as kho, meat_piece
from lpms_helpers import khoi, ong, khoi_meo

META = dict(ten="meat_storage", dat=True, ngan_sach=4400, soi=lambda p: (lambda r: (r[0], f"{r[2]} · " + ("; ".join(r[1][:3]) or "no penetration > 5 mm, every cut rests or hangs")))(kho.soi_thit(p)))
CX = 0.72                      # rack post x
PY = (0.15, 0.51)              # rack post y (hook bar at kho.MOC_Y between them)
THANH_Z = 1.40                 # hook bar height
NOC = 1.86; DOC = 0.7; MAI_DAY = 0.03   # roof ridge top z, slope, thickness


def B(c, sx, sy, sz, mau):
    return khoi([(c[0] + a * sx / 2, c[1] + b * sy / 2, c[2] + d * sz / 2) for a in (-1, 1) for b in (-1, 1) for d in (-1, 1)], mau)


def build():
    Y0, Z = kho.BAN_Y, kho.BAN_Z; my = kho.MOC_Y; p = {}
    # ---- front table (slats along X with gaps, aprons, 4 legs, low stretchers)
    for k, dy in enumerate((-0.1875, -0.0625, 0.0625, 0.1875)): p[f"ban_van_{k}"] = B((0, Y0 + dy, Z - 0.015), 1.30, 0.10, 0.03, "go_sang")
    for k, s in enumerate((-1, 1)):
        p[f"ban_dam_{k}"] = B((0, Y0 + s * 0.20, Z - 0.06), 1.20, 0.04, 0.06, "go")
        for j, sx in enumerate((-1, 1)):
            p[f"ban_chan_{k}{j}"] = ong((sx * 0.58, Y0 + s * 0.20, 0.0), (sx * 0.58, Y0 + s * 0.20, Z - 0.03), 0.035, 0.032, "go")
    for j, sx in enumerate((-1, 1)): p[f"ban_giang_{j}"] = B((sx * 0.58, Y0, 0.15), 0.04, 0.40, 0.04, "go_toi")
    # ---- smoking rack: posts, side rails, low rails, hook bar
    for j, sx in enumerate((-1, 1)):
        for i, y in enumerate(PY): p[f"cot_{j}{i}"] = ong((sx * CX, y, 0.0), (sx * CX, y, 1.56), 0.045, 0.040, "go")
        p[f"ray_tren_{j}"] = ong((sx * CX, PY[0], THANH_Z), (sx * CX, PY[1], THANH_Z), 0.03, 0.03, "go_toi")
        p[f"ray_duoi_{j}"] = ong((sx * CX, PY[0], 0.30), (sx * CX, PY[1], 0.30), 0.028, 0.028, "go_toi")
        # truss flush under the roof
        und = lambda dy: NOC - MAI_DAY - DOC * abs(dy)
        p[f"keo_{j}"] = khoi([(sx * CX + dx, my + dy, z) for dx in (-0.03, 0.03) for dy, z in ((-0.36, 1.50), (0.36, 1.50), (-0.36, und(0.36)), (0.36, und(0.36)), (0, und(0)))], "go_toi")
    p["sao_moc"] = ong((-CX, my, THANH_Z), (CX, my, THANH_Z), 0.028, 0.028, "go_sang")
    for j, hx in enumerate(kho.MOC_X):   # iron hook: rod from the bar down to the tip + small forward curl
        p[f"moc_{j}_can"] = ong((hx, my, THANH_Z), (hx, my, kho.MOC_Z), 0.006, 0.006, "sat", n=5)
        p[f"moc_{j}_mui"] = khoi([(hx + dx, my + dy, kho.MOC_Z + dz) for dx in (-0.005, 0.005) for dy, dz in ((0, 0), (0.028, 0.012), (0.028, 0.034), (0.0, 0.010))], "sat")
    # ---- thatched gable roof + ridge log
    for k, s in enumerate((-1, 1)):
        p[f"mai_{k}"] = khoi([(x, my + s * dy, NOC - DOC * dy - t) for x in (-0.88, 0.88) for dy in (0.0, 0.44) for t in (0.0, MAI_DAY)], "go_sang")   # wood-shingle roof (straw "may" read as a blank sign board in the review)
    p["noc"] = ong((-0.92, my, NOC + 0.005), (0.92, my, NOC + 0.005), 0.032, 0.032, "go_toi")
    # ---- fire ring under the hanging meat (smoke) + two charred logs
    for k in range(7):
        a = 2 * math.pi * k / 7; p[f"bep_da_{k}"] = khoi_meo((0.21 * math.cos(a), my + 0.17 * math.sin(a), 0.03), 0.055, "da", seed=40 + k, det=(1.1, 1.0, 0.75))
    p["bep_cui_0"] = ong((-0.12, my - 0.05, 0.035), (0.12, my + 0.05, 0.035), 0.03, 0.028, "go_toi")
    p["bep_cui_1"] = ong((-0.10, my + 0.07, 0.035), (0.11, my - 0.06, 0.07), 0.026, 0.024, "go_toi")
    # ---- stock
    D = meat_piece.dui()
    for o in kho.o_chua_thit(): p.update(meat_piece.dat(D, kho.ma_tran_thit(o), f"thit_{o['k']:02d}_"))
    return p
