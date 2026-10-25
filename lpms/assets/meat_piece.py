"""MEAT CUT (Boss 23/10/2026: «Storage stacking display thịt») — one storage unit after hunt → butcher → carry home.
Stylized smoked HAUNCH tied with jute twine: faceted body (flat bottom, top plateau at the big end so cuts stack brick-wise),
lighter cut face on the big end, bone stub + knob on the narrow end. ~0.33 m long, ~100 tris.
Local frame = the one settler-storage/scripts/storage.py places (o_chua_thit): length +X (big end +X, bone −X), bottom z=0, top z=kho.THIT_CAO.
Small variant `lat()` = flat slab with fat strip + twine (asset meat_piece_small.py). Storage asset meat_storage.py imports dui()/dat()."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.expanduser("~/.hermes/skills/creative/settler-storage/scripts"))
import storage as kho
from lpms_helpers import khoi, ong, cau

META = dict(ten="meat_piece", dat=True, ngan_sach=120)


def _vong(x, ws, sc=1.0, cz=None, dw=0.0, dz=0.0):
    """ring of 6 points at station x; ws = [(half_width, z) bottom, mid, top]; optional scale about cz, widen dw, raise top dz."""
    out = []
    for j, (w, z) in enumerate(ws):
        if cz is not None: w, z = w * sc, cz + (z - cz) * sc
        w += dw; z += dz if j == 2 else 0.0
        out += [(x, w, z), (x, -w, z)]
    return out


def _mat_cat(x, R):
    """cross-section at x by linear interpolation of station table R = [(x, ws)]."""
    R = sorted(R, key=lambda r: r[0])
    for (x0, a), (x1, b) in zip(R, R[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0); return [(wa + t * (wb - wa), za + t * (zb - za)) for (wa, za), (wb, zb) in zip(a, b)]
    raise ValueError(x)


def dui():
    """HAUNCH parts (local frame). Big end +X, bone −X, flat bottom z=0, plateau z=THIT_CAO at x=0.07."""
    H = kho.THIT_CAO
    R = [(0.12, [(0.034, 0.0), (0.042, 0.033), (0.026, 0.058)]),
         (0.07, [(0.055, 0.0), (0.065, 0.035), (0.045, H)]),
         (-0.02, [(0.050, 0.0), (0.056, 0.033), (0.036, 0.066)]),
         (-0.10, [(0.024, 0.0), (0.030, 0.035), (0.020, 0.056)])]
    p = {"than": khoi(sum((_vong(x, ws) for x, ws in R), []), "thit")}
    p["mat_cat"] = khoi(_vong(0.118, R[0][1]) + _vong(0.128, R[0][1], sc=0.78, cz=0.03), "thit_tuoi")      # lighter cut face
    p["day"] = khoi(_vong(0.0, _mat_cat(0.0, R), dw=0.004, dz=0.004) + _vong(0.022, _mat_cat(0.022, R), dw=0.004, dz=0.004), "may")  # twine band
    p["xuong"] = ong((-0.09, 0, 0.035), (-0.172, 0, 0.035), 0.014, 0.012, "xuong", n=5)
    p["dau_xuong"] = cau((-0.185, 0, 0.035), 0.020, "xuong")          # knob: its −X tip = kho.THIT_MOC (tie point when hung)
    return p


def lat():
    """SMALL variant: flat slab 0.24 × 0.11 × 0.045 with a fat strip along one edge and a twine band (~60 tris)."""
    ws = [(0.050, 0.0), (0.056, 0.022), (0.044, 0.045)]
    p = {"than": khoi(_vong(-0.12, ws, sc=0.8, cz=0.022) + _vong(-0.10, ws) + _vong(0.10, ws) + _vong(0.12, ws, sc=0.8, cz=0.022), "thit")}
    p["mo"] = khoi([(x, y, z) for x in (-0.095, 0.095) for y in (0.030, 0.058) for z in (0.012, 0.047)], "mo")
    p["day"] = khoi(_vong(-0.02, ws, dw=0.004, dz=0.004) + _vong(0.0, ws, dw=0.004, dz=0.004), "may")
    return p


def dat(parts, M, tien_to):
    """copy parts through 4×4 M (kho.ma_tran_thit) and prefix names."""
    out = {}
    for k, m in parts.items():
        g = m.copy(); g.apply_transform(M); out[f"{tien_to}{k}"] = g
    return out


def build():
    return dui()
