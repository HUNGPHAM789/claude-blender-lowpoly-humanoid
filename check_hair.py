#!/usr/bin/env python3
"""
Cửa soi Tóc LPM (Gate ⑯: Silhouette Broken >= 35% & 0/4000 Skull Penetration)
Chạy tự động để nghiệm thu tóc theo chuẩn Origami v2.7.
Thoát mã 1 nếu vi phạm bất kỳ tiêu chí nào!
"""
import sys
import os
import math
import numpy as np
import trimesh
from scipy.spatial import Delaunay

# Import LPM head generator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lpm
import hair_origami

def check_hair(gioi="nam", cao=1.80):
    print(f"🔍 Đang soi tóc Origami ({gioi}, {cao}m)...")
    s = cao / 1.80
    
    # 1. Sinh tóc và đầu
    hair_mesh = hair_origami.build_origami_hair(gioi=gioi, cao=cao)
    head_mesh = lpm.dau(s, gioi)
    
    # Gate 16a: Triangle budget (<= 450 tris)
    n_tris = len(hair_mesh.faces)
    if n_tris > 450:
        print(f"❌ [Gate ⑯a Thất bại] Số tam giác {n_tris} > 450 quy định!")
        return 1
    print(f"  ✅ ⑯a Số tam giác: {n_tris} tris (ngân sách <= 450)")
    
    # Gate 16b: Silhouette Jaggedness (Độ nảy múi răng cưa đường viền)
    tip_indices = [1 + i * 2 + 1 for i in range(12)]
    tip_pts = hair_mesh.vertices[tip_indices]
    
    z_tips = tip_pts[:, 2]
    z_diffs = np.abs(np.diff(np.append(z_tips, z_tips[0])))
    avg_jaggedness_mm = np.mean(z_diffs) * 1000.0
    
    if avg_jaggedness_mm < 15.0:
        print(f"❌ [Gate ⑯b Thất bại] Độ nảy răng cưa {avg_jaggedness_mm:.1f}mm < 15mm (tóc bị phẳng viền, chưa ra múi origami)!")
        return 1
    print(f"  ✅ ⑯b Độ nảy răng cưa múi: {avg_jaggedness_mm:.1f} mm (>= 15mm, đạt chuẩn Clump Grammar)")
    
    # Gate 16c: No-Clipping Gate (0 / 4000 điểm lún vào đầu)
    # Sample 4000 random points on hair surface
    sample_pts, _ = trimesh.sample.sample_surface(hair_mesh, 4000)
    
    # Use Delaunay triangulation of head vertices to test point inclusion
    delaunay = Delaunay(head_mesh.vertices)
    inside_mask = delaunay.find_simplex(sample_pts) >= 0
    n_inside = np.sum(inside_mask)
    
    if n_inside > 0:
        print(f"❌ [Gate ⑯c Thất bại] Có {n_inside} / 4000 điểm tóc lún vào trong hộp sọ!")
        return 1
    print(f"  ✅ ⑯c Độ lún sọ: 0 / 4000 điểm (an toàn 100%, không lộ da đầu)")
    
    print(f"✨ [LPM Gate ⑯] TÓC ORIGAMI ĐẠT CHUẨN!")
    return 0

if __name__ == "__main__":
    gioi = sys.argv[1] if len(sys.argv) > 1 else "nam"
    rc = check_hair(gioi=gioi)
    sys.exit(rc)
