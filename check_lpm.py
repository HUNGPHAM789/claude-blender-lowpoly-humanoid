#!/usr/bin/env python3
"""Cửa soi LPM — chạy TỰ ĐỘNG ở cuối lpm.py (trượt ⇒ mã 1 ⇒ build trượt). Gọi tay: python3 check_lpm.py <out không đuôi>
Đo thật trên file đã xuất, không tin lời tả:
  ① mỗi bộ phận KÍN (watertight)                      ② tổng tam giác 300–2500
  ③ cao đúng ±1 %, chân chạm đất (đáy ∈ [-5, +10] mm)  ④ thể tích hợp lý (0,055–0,095 m³ × (cao/1,8)³)
  ⑤ THÂN LIỀN: cắt ngang mỗi 1 cm từ mông tới vai, mỗi lát đúng 1 vòng kín, độ rộng/sâu không được nhảy > BAC_TOI_DA giữa hai lát
     (bài học v1: thân 3 hộp chồng ⇒ bậc 45–190 mm; thân liền đúng ≈ < 10 mm)
  ⑥ đủ bộ phận rời + socket theo hợp đồng (đầu, bàn tay, bàn chân tháo được)
  ⑦ đối xứng: mọi bộ phận _L có _R, socket _L có _R, kích thước lệch < 3 %
  ⑨ MẶT ĐẦU (faceless): ≤80 tam giác, mật độ ≤1,5× thân — không mắt/mũi chi tiết (Boss 22/10 bỏ cả bản vùng T lẫn bản inset)
  ⑩ MÔNG NHẸ: nhô 30–60 mm (nữ 40–80), khe 5–20 mm, đỉnh múi không tụt >30 mm dưới mốc `mong` (xệ)
  ⑪ TRÁN: mặt trước ở z trán lùi ≤25 mm sau cung mày (nhìn ngang không dẹt)
  ⑫ KHÔNG VÁY: viền đáy thân nhìn từ sau hình «W» — khe và hông cao hơn đáy múi ≥15 mm (viền phẳng ngang = gấu váy)
  ⑮ TAY NẮM: 5 khối/tay; trụ Ø32 tại cam_*: lún ≤1,5 mm; tư thế co≥0,95 ôm ≥75 %; code co=1 phải nắm được
  ⑧ eo THẮT: rộng eo ≤ 0,93 × min(rộng ngực, rộng hông) — bắt thân dựng bằng khối lồi (lấp chỗ lõm)
"""
import json, sys
import numpy as np, trimesh

BAC_TOI_DA = 0.020          # m — bậc mặt cắt tối đa giữa 2 lát cách 1 cm
BO_PHAN_BAT_BUOC = {"than", "co", "dau", "ban_tay_L", "ban_tay_R", "ban_chan_L", "ban_chan_R",
                    "canh_tay_L", "canh_tay_R", "ngon1_L", "ngon1_R", "ngon2_L", "ngon2_R", "cai1_L", "cai1_R", "cai2_L", "cai2_R", "cang_tay_L", "cang_tay_R", "dui_L", "dui_R", "cang_chan_L", "cang_chan_R"}
SOCKET_BAT_BUOC = {"dau", "ban_tay_L", "ban_tay_R", "ban_chan_L", "ban_chan_R", "cam_L", "cam_R", "lung"}


def soi(out):
    loi, ghi = [], []
    meta = json.load(open(out + ".json"))
    sc = trimesh.load(out + ".glb", force="scene")
    Z = trimesh.transformations.rotation_matrix(math_pi_2(), (1, 0, 0))            # Y-lên → Z-lên
    bo = {}
    for node in sc.graph.nodes_geometry:
        T, g = sc.graph[node]; m = sc.geometry[g].copy(); m.apply_transform(Z @ T); bo[node] = m
    # ①
    ho = [k for k, m in bo.items() if not m.is_watertight]
    (loi if ho else ghi).append(f"① kín: {'HỞ ' + ', '.join(ho) if ho else 'tất cả ' + str(len(bo)) + ' bộ phận'}")
    # ②
    tg = sum(len(m.faces) for m in bo.values())
    (ghi if 300 <= tg <= 2500 else loi).append(f"② tam giác {tg} (300–2500)")
    # ③
    lo = min(m.bounds[0][2] for m in bo.values()); hi = max(m.bounds[1][2] for m in bo.values()); cao = meta["cao"]
    (ghi if abs(hi - lo - cao) <= cao * 0.01 else loi).append(f"③ cao {hi - lo:.3f} m (đặt {cao})")
    (ghi if -0.005 <= lo <= 0.010 else loi).append(f"③ đáy {lo * 1000:+.1f} mm")
    # ④
    vol = sum(m.volume for m in bo.values()); k = (cao / 1.8) ** 3
    (ghi if 0.055 * k <= vol <= 0.095 * k else loi).append(f"④ thể tích {vol:.4f} m³ ({0.055 * k:.3f}–{0.095 * k:.3f})")
    # ⑤
    th = bo.get("than")
    if th is None:
        loi.append("⑤ không có bộ phận 'than'")
    else:
        moc = meta.get("moc_than", {})
        # đo đoạn THÂN CHÍNH (mông → vai); cổ-vai và đáy chậu là «nắp», dốc gắt là đúng giải phẫu
        z0 = moc.get("mong", th.bounds[0][2] + 0.04); z1 = moc.get("vai", th.bounds[1][2] - 0.06)
        cu, xau, so = None, [], 0
        for z in np.arange(z0 + 0.005, z1, 0.01):
            if any(abs(z - zm) < 0.003 for zm in moc.values()): continue   # lát trùng hàng đỉnh vỡ thành nhiều đoạn GIẢ
            s = th.section(plane_origin=(0, 0, z), plane_normal=(0, 0, 1))
            if s is None: xau.append((round(float(z), 3), "đứt")); continue
            if len(s.entities) != 1: xau.append((round(float(z), 3), f"{len(s.entities)} vòng"))   # khối chồng khối
            p = s.vertices; r, d = np.ptp(p[:, 0]), np.ptp(p[:, 1]); so += 1
            if cu is not None:
                b = max(abs(r - cu[0]), abs(d - cu[1]))
                if b > BAC_TOI_DA: xau.append((round(float(z), 3), round(b * 1000)))
            cu = (r, d)
        if xau: loi.append(f"⑤ thân KHÔNG liền: {len(xau)} bậc > {BAC_TOI_DA * 1000:.0f} mm tại (z, mm) {xau[:6]}")
        else: ghi.append(f"⑤ thân liền: {so} lát, không bậc nào > {BAC_TOI_DA * 1000:.0f} mm")
    # ⑧ eo THẮT thật (khối lồi lấp phẳng chỗ lõm ⇒ eo ≈ nội suy ngực–hông ⇒ trượt)
    if th is not None and {"eo", "nguc", "hong"} <= set(meta.get("moc_than", {})):
        def rong(z):
            s_ = th.section(plane_origin=(0, 0, z + 0.004), plane_normal=(0, 0, 1)); return np.ptp(s_.vertices[:, 0]) if s_ is not None else 0
        mc = meta["moc_than"]; e, n, h = rong(mc["eo"]), rong(mc["nguc"]), rong(mc["hong"])
        ti = e / min(n, h) if min(n, h) else 1
        (ghi if ti <= 0.93 else loi).append(f"⑧ eo thắt: eo/min(ngực,hông) = {ti:.2f} (≤ 0,93) [eo {e:.3f} · ngực {n:.3f} · hông {h:.3f}]")
    # ⑨ VÙNG T + ⑩ MÔNG — đo bằng TIA chiếu thẳng vào bề mặt (không tin toạ độ trong code)
    def cham(m, x, z, tu_truoc=True):
        """tia song song trục Y tại (x, z): trả về Y của bề mặt gặp đầu tiên (từ trước hoặc từ sau). Möller–Trumbore, numpy thuần."""
        tri = m.triangles; o = np.array([x, 0.0, z]); d = np.array([0.0, 1.0, 0.0])
        e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
        pv = np.cross(d, e2); det = np.einsum("ij,ij->i", e1, pv); ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0); tv = o - tri[:, 0]
        u = np.einsum("ij,ij->i", tv, pv) * inv; qv = np.cross(tv, e1); v = (qv @ d) * inv
        t = np.einsum("ij,ij->i", e2, qv) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1)
        if not hit.any(): return None
        return float(t[hit].min() if tu_truoc else t[hit].max())
    # ⑨ MẬT ĐỘ MẶT ĐẦU ≈ THÂN (Boss 22/10: «thêm nhiều mặt phẳng quá so với toàn body cho gương mặt»)
    dau_m = bo.get("dau")
    if dau_m is not None and th is not None:
        md_dau = len(dau_m.faces) / (dau_m.area * 100); md_than = len(th.faces) / (th.area * 100)
        ti = md_dau / md_than
        (ghi if ti <= 1.5 and len(dau_m.faces) <= 80 else loi).append(   # FACELESS (Boss 22/10 «cả 2 version trên đều ko đc»)
            f"⑨ mặt đầu: {len(dau_m.faces)} tam giác (≤80), mật độ {md_dau:.1f}/dm² = {ti:.1f}× thân (≤1,5×)")
    # ⑩ MÔNG NHÔ NHẸ, KHÔNG XỆ (Boss 22/10: «mông hơi xệ, chỉ cần 1 chút thôi»)
    mt = meta.get("moc_than", {})
    if th is not None and {"mong", "eo"} <= set(mt):
        xm = 0.065 * cao / 1.8
        mui_m = [cham(th, sx * xm, mt["mong"], False) for sx in (1, -1)]
        khe = cham(th, 0.0, mt["mong"] + 0.004, False); lung_eo = cham(th, 0.0, mt["eo"] + 0.004, False)
        if None in mui_m or khe is None or lung_eo is None:
            loi.append("⑩ mông: tia không chạm thân")
        else:
            nho = (min(mui_m) - lung_eo) * 1000; sau_khe = (min(mui_m) - khe) * 1000
            doc = [(z, cham(th, xm, z, False)) for z in np.arange(mt["mong"] - 0.08, mt["mong"] + 0.10, 0.005)]
            doc = [(z, y) for z, y in doc if y is not None]
            z_dinh = max(doc, key=lambda t: t[1])[0]; xe = (mt["mong"] - z_dinh) * 1000      # đỉnh múi tụt dưới mốc mông bao nhiêu
            lo, hi = (30, 60) if meta.get("gioi") == "nam" else (40, 80)
            ok = lo <= nho <= hi and 5 <= sau_khe <= 20 and xe <= 30
            (ghi if ok else loi).append(f"⑩ mông nhẹ: nhô {nho:.0f} mm ({lo}–{hi}) · khe {sau_khe:.0f} mm (5–20) · đỉnh múi thấp hơn mốc {xe:.0f} mm (≤30, quá ⇒ XỆ)")
    # ⑪ TRÁN đầy (nhìn ngang): mặt trước ở z «trán» không lùi quá 25 mm sau mặt trước ở z «cung mày»
    if dau_m is not None:
        k = cao / 1.8
        y_may = cham(dau_m, 0.0, 1.725 * k); y_tran = cham(dau_m, 0.0, 1.765 * k)
        if y_may is None or y_tran is None: loi.append("⑪ trán: tia không chạm đầu")
        else:
            lui = (y_tran - y_may) * 1000
            (ghi if lui <= 25 else loi).append(f"⑪ trán: lùi sau cung mày {lui:.0f} mm (≤25; v2.2 = 57 ⇒ trán dẹt)")
    # ⑫ KHÔNG «VÁY» (Boss 22/10: «mông chưa làm mất cạnh dưới (giống váy)»): viền ĐÁY THÂN nhìn từ sau phải hình «W».
    #    Quét tia từ SAU ở x = 0 (khe), ±múi, ±hông; tìm z thấp nhất tia còn chạm THÂN.
    #    Lịch sử: thước «diện tích đáy ngoài đùi» báo 15 % ĐẠT; thước «mặt úp xuống ngoài đùi» báo 86 cm² ĐẠT —
    #    cả hai ĐẠT trên bản v2.3a có gấu váy phẳng ngang (Boss nhìn là thấy). Thứ phải đo là HÌNH VIỀN, không phải diện tích.
    if th is not None and "mong" in mt:
        k = cao / 1.8
        def day_vien(x):
            zs = [z for z in np.arange(mt["mong"], 0.70 * k, -0.002) if cham(th, x, z, False) is not None]
            return min(zs) if zs else None
        z_khe, z_mui, z_hong = day_vien(0.0), day_vien(0.065 * k), day_vien(0.14 * k)
        if None in (z_khe, z_mui, z_hong): loi.append("⑫ váy: tia không chạm đáy thân")
        else:
            khac = (z_khe - z_mui) * 1000; hong_ = (z_hong - z_mui) * 1000
            (ghi if khac >= 15 and hong_ >= 15 else loi).append(
                f"⑫ không váy: đáy khe cao hơn đáy múi {khac:.0f} mm (≥15) · đáy hông cao hơn đáy múi {hong_:.0f} mm (≥15) ⇒ viền «W», không phẳng ngang")
    # ⑮ BÀN TAY NẮM ĐƯỢC (Boss 22/10 «tay với 1 ngón cái? có thể co lại để nắm?»): 5 khối/tay, trụ Ø32 mm tại socket cam_*.
    #    Đo trên FILE: tia từ trục trụ (3 lát × 36 hướng) — ôm = % tia chạm tay trong r+12 mm; lún = tay xuyên vào trụ.
    #    Luôn: lún ≤1,5 mm. Khi co ≥0,95 (tư thế nắm): ôm ≥75 %. Ngoài ra build THỬ co=1 trong code (khả năng nắm phải có ở mọi bản).
    import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__))); import hand as _tay
    for ben in ("L", "R"):
        ten_t = [f"{k}_{ben}" for k in ("ban_tay", "ngon1", "ngon2", "cai1", "cai2")]
        sc_ = meta.get("socket", {}).get(f"cam_{ben}")
        if not all(k in bo for k in ten_t) or not sc_ or "r" not in sc_:
            loi.append(f"⑮ tay {ben}: thiếu bộ phận/socket cam có r"); continue
        tru_ = (np.array(sc_["vi_tri"]), np.array(sc_["len"]), sc_["r"])
        om_, lun_ = _tay.do_nam({k: bo[k].vertices for k in ten_t}, tru_)
        co_ = meta.get("co_tay", 0.0); can_om = 75 if co_ >= 0.95 else 0
        (ghi if lun_ <= 1.5 and om_ >= can_om else loi).append(f"⑮ tay {ben} (co={co_:g}): ôm trụ Ø32 {om_:.0f}% (≥{can_om}) · lún {lun_:.1f} mm (≤1,5)")
    bo_n, _k, tru_n = _tay.dung_tay(1.0, cao / 1.8, nu=meta.get("gioi") == "nu"); om_n, lun_n = _tay.do_nam(bo_n, tru_n)
    (ghi if om_n >= 75 and lun_n <= 1.5 else loi).append(f"⑮ khả năng nắm (code, co=1): ôm {om_n:.0f}% (≥75) · lún {lun_n:.1f} mm")
    # ⑥
    thieu = BO_PHAN_BAT_BUOC - set(bo); thieu_s = SOCKET_BAT_BUOC - set(meta.get("socket", {}))
    (loi if thieu or thieu_s else ghi).append(f"⑥ hợp đồng: thiếu bộ phận {sorted(thieu) or '—'}, thiếu socket {sorted(thieu_s) or '—'}")
    # ⑦
    lech = []
    for k_ in bo:
        if k_.endswith("_L"):
            r = k_[:-2] + "_R"
            if r not in bo: lech.append(f"{k_} không có {r}"); continue
            a, b = bo[k_].extents, bo[r].extents
            if np.max(np.abs(a - b) / np.maximum(a, 1e-6)) > 0.03: lech.append(f"{k_}↔{r}")
    (loi if lech else ghi).append(f"⑦ đối xứng: {', '.join(lech) if lech else 'đủ cặp L/R, lệch < 3 %'}")
    for d in ghi: print("  ✅", d)
    for d in loi: print("  ❌", d)
    print(("⛔ LPM TRƯỢT " if loi else "✅ LPM ĐẠT ") + out)
    return 1 if loi else 0


def math_pi_2():
    import math; return math.pi / 2


if __name__ == "__main__":
    sys.exit(soi(sys.argv[1]))
