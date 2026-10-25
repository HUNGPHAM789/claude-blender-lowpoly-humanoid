#!/usr/bin/env python3
"""
LPM Stylized Origami Hair Generator (Clump Grammar v2.7)
Solves Boss's feedback (22/10): «làm tóc vẫn chưa ra stylized cần phát triển thêm»
Implements:
  1. Clump Grammar: 12 folded 3D wedges around crown with alternating pointed tips.
  2. Silhouette Gate (check_hair.py): Broken perimeter >= 35% + 0/4000 skull clipping.
"""
import math
import os
import sys
import numpy as np
import trimesh

def build_origami_hair(gioi="nam", cao=1.80, mau_ten="chestnut"):
    s = cao / 1.80
    
    # Hair colors
    MAU_TOC = {
        "black": [24, 22, 24, 255],
        "dark_brown": [58, 40, 28, 255],
        "chestnut": [112, 70, 40, 255]
    }
    color = MAU_TOC.get(mau_ten, MAU_TOC["chestnut"])
    
    # Center of skull (HAIR_SOCKET)
    cx, cy, cz = 0.0, 0.012 * s, 1.70 * s
    # Crown apex elevated to 1.855 to prevent chord clipping into convex dome
    crown_z = 1.855 * s
    
    N_CLUMPS = 12
    verts = []
    faces = []
    
    # Vertex 0: Crown apex center
    verts.append([cx, cy, crown_z])
    
    # Radii along skull: skull has width rx ≈ 0.08, depth ry ≈ 0.095
    rx_skull = 0.082 * s
    ry_skull = 0.098 * s
    
    # Intermediate crown ring to hug skull curve before dropping into clumps
    for i in range(N_CLUMPS):
        theta = i * (2 * math.pi / N_CLUMPS)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        r_base = math.hypot(rx_skull * cos_t, ry_skull * sin_t)
        
        # 1. Crown drop ring
        r_crown = r_base + 0.028 * s
        z_crown = 1.805 * s
        verts.append([cx + r_crown * cos_t, cy + r_crown * sin_t, z_crown])
        
        # 2. Clump Tip (pointed end)
        is_front = (sin_t < -0.35)
        is_back = (sin_t > 0.35)
        
        if is_front:
            # Fringe stops cleanly above brow (z ≈ 1.725)
            z_tip = (1.730 if i % 2 == 0 else 1.710) * s
            r_tip = r_base + 0.024 * s
        elif is_back:
            if gioi == "nu":
                z_tip = (1.535 if i % 2 == 0 else 1.575) * s
                r_tip = r_base + 0.042 * s
            else:
                z_tip = (1.620 if i % 2 == 0 else 1.645) * s
                r_tip = r_base + 0.030 * s
        else:
            # Sides
            if gioi == "nu":
                z_tip = (1.550 if i % 2 == 0 else 1.590) * s
                r_tip = r_base + 0.038 * s
            else:
                z_tip = (1.655 if i % 2 == 0 else 1.680) * s
                r_tip = r_base + 0.028 * s
                
        verts.append([cx + r_tip * cos_t, cy + r_tip * sin_t, z_tip])

    for i in range(N_CLUMPS):
        nxt = (i + 1) % N_CLUMPS
        v_crown_curr = 1 + i * 2
        v_tip_curr   = 1 + i * 2 + 1
        v_crown_nxt  = 1 + nxt * 2
        v_tip_nxt    = 1 + nxt * 2 + 1
        
        # 1. Crown apex to crown ring
        faces.append([0, v_crown_curr, v_crown_nxt])
        # 2. Folded wedge facet 1: crown to tip
        faces.append([v_crown_curr, v_tip_curr, v_crown_nxt])
        # 3. Folded wedge facet 2: tip to next tip (creating jagged triangular valley!)
        faces.append([v_tip_curr, v_tip_nxt, v_crown_nxt])

    verts = np.array(verts, dtype=float)
    faces = np.array(faces, dtype=int)
    
    mat = trimesh.visual.material.PBRMaterial(
        name=f"M_Hair_{mau_ten}",
        baseColorFactor=[c / 255.0 for c in color],
        metallicFactor=0.0,
        roughnessFactor=0.88
    )
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    mesh.visual = trimesh.visual.TextureVisuals(material=mat)
    
    return mesh

if __name__ == "__main__":
    gioi = "nam"
    if len(sys.argv) > 1 and sys.argv[1] in ["nam", "nu"]:
        gioi = sys.argv[1]
    out_path = f"/tmp/hair_origami_{gioi}.glb"
    if len(sys.argv) > 2:
        out_path = sys.argv[2]
        
    m = build_origami_hair(gioi=gioi, cao=1.80, mau_ten="chestnut")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    m.export(out_path)
    print(f"✨ [LPM Hair v2.7] Exported Origami Hair ({len(m.faces)} tris) -> {out_path}")
