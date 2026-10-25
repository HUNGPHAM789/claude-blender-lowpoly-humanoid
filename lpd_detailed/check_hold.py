"""Cửa NẮM của LPD (CO=1): bàn tay phải ÔM trụ Ø32 mm tại socket cam_* mà không lún vào nó.
Đo trên mặt tay thật (lấy mẫu 6000 điểm trên vùng 'hands'), không đọc góc trong code.
  · lún  = sâu nhất của mặt tay vào trụ (mm)            — đạt ≤ 1,5
  · ôm   = % hướng quanh trục (36 hướng × 3 lát) có mặt tay trong [r, r+14 mm]  — đạt ≥ 65
Chạy: CO=1 GIOI=nam|nu python3 check_hold.py   (exit 1 nếu trượt) — build.sh gọi tự động khi CO>0.
"""
import os, sys, math, importlib
import numpy as np, trimesh

_a = sys.argv; sys.argv = [sys.argv[0]]; G = importlib.import_module("geometry"); sys.argv = _a


def do(G, so_tia=36):
    V = np.array(G.V, float); tri = []
    for f, reg, _ in G.F:
        if reg != 'hands': continue
        tri += [[f[0], f[k], f[k + 1]] for k in range(1, len(f) - 1)]
    m = trimesh.Trimesh(V, np.array(tri), process=False)
    pts, _ = trimesh.sample.sample_surface_even(m, 6000, seed=1) if hasattr(trimesh.sample, 'sample_surface_even') else trimesh.sample.sample_surface(m, 6000)
    kq = {}
    for s, (c, a, r) in G.CAM.items():
        a = a / np.linalg.norm(a); d = pts - c; t = d @ a; rad = np.linalg.norm(d - np.outer(t, a), axis=1)
        gan = np.linalg.norm(d, axis=1) < 0.12                       # chỉ bàn tay bên này
        lun = max(0.0, float((r - rad[gan & (np.abs(t) < 0.045)]).max()) * 1000) if (gan & (np.abs(t) < 0.045)).any() else 0.0
        e1 = np.cross(a, (0, 0, 1.0)); e1 /= np.linalg.norm(e1); e2 = np.cross(a, e1)
        ang = np.arctan2((d - np.outer(t, a)) @ e2, (d - np.outer(t, a)) @ e1)
        om = 0
        for lat in (-0.02, 0.0, 0.02):
            sel = gan & (np.abs(t - lat) < 0.008) & (rad < r + 0.014)
            b = set(((ang[sel] + math.pi) / (2 * math.pi) * so_tia).astype(int) % so_tia)
            om += len(b)
        kq[s] = (100.0 * om / (3 * so_tia), lun)
    return kq


if __name__ == '__main__':
    kq = do(G); ok = True
    for s, (om, lun) in kq.items():
        d = om >= 65 and lun <= 1.5; ok &= d
        print(f"  {'✅' if d else '❌'} tay {'trái' if s > 0 else 'phải'}: ôm {om:.0f} % · lún {lun:.1f} mm")
    if not kq: print("  ❌ không có socket cam_* (CO=0?)"); ok = False
    sys.exit(0 if ok else 1)
