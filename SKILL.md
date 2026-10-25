---
name: low-poly-origami-character
description: LPM — FACELESS HUMANOID (Boss 22/10/2026). Low-Poly Model — dựng THÂN NGƯỜI TRƠN kiểu origami (mặt phẳng, không mặt cong) bằng code, nam/nữ, có HỢP ĐỒNG GẮN (bộ phận có tên + socket) để lớp đắp (tóc, giày, áo, đồ) gắn/thay. Dùng khi cần base mesh người low-poly cho game/three.js/Blender. Build tự chạy cửa soi đo thật.
version: 2.7.0
author: Antigravity & Hermes (v1) · Claude (v2, 22/10/2026)
license: MIT
repo: https://github.com/HUNGPHAM789/lpm-faceless-humanoid   # self-developed skill (Boss 22/10) — ~/.hermes/skills/creative/low-poly-origami-character is a SYMLINK to the local clone; edit → build → §9 row → commit + push
metadata:
  hermes:
    tags: [faceless-humanoid, 3d-graphics, low-poly, origami, base-mesh, procedural-modeling, threejs, blender, gltf]
    related_skills: [humanoid-replaceable-assets, procedural-low-poly-world]
---

# LPM — FACELESS HUMANOID · thân người trơn low-poly origami

**Nhãn: faceless humanoid** (Boss 22/10: «cả 2 version trên đều ko đc. reverse lại version bạn mới sửa đầu - và tag skill này là faceless humanoid»).
Đầu = khối đá quý + trán, KHÔNG mắt/mũi chi tiết. Bộ có mặt thì ở skill riêng: `low-poly-origami-detailed`, `low-poly-origami-simplified` (chỉ spec).

Bản v1 (≤1.3) ghim cứng toạ độ mặt + râu của một nhân vật «primal settler» — ĐÃ BỎ. Bản lưu: `SKILL_v1.3_old.md.bak`.

## 1. Chạy (một lệnh, có cửa soi tự động)
```bash
python3 lpm.py --out <thư mục>/<tên> --gioi nam|nu [--cao 1.80]     # ⇒ .glb .obj .json, rồi TỰ chạy check_lpm.py
blender -b -P view_lpm.py -- <thư mục>/sheet.png <tên>.glb [khác.glb]   # tấm xem 4 góc: trước · 3/4 · nghiêng · sau
blender -b -P view_closeup.py -- <thư mục>/closeup.png <tên>.glb [khác.glb]   # CẬN vùng T (mặt) + mông, đèn theo phía nhìn
```
`lpm.py` thoát **mã 1 nếu cửa soi trượt** ⇒ người/agent gọi build sẽ thấy lỗi, không cần nhớ chạy soi riêng.
Toạ độ trong code + `.json`: mét, **Z lên**, chân z=0, **mặt nhìn −Y**. File `.glb` đã đổi sang Y-lên theo chuẩn glTF.

## 2. Kiến trúc — vì sao thân phải LIỀN mà tay chân lại RỜI
| phần | cách dựng | lý do |
|---|---|---|
| **thân** (cổ → đáy chậu) | MỘT lưới liền: các **vòng 8 đỉnh** (siêu-elip p≈2,6) theo **bảng mặt cắt**, nối vòng-vòng, bịt 2 đầu bằng quạt | hình LÕM (eo thắt, khe mông, rãnh lưng, rãnh ức) chỉ làm được bằng vòng; ConvexHull lấp phẳng hết |
| tay, chân, khuỷu, gối, cơ delta | khối lồi KÍN rời (`scipy.spatial.ConvexHull`) | khớp lộ ra là nét đẹp của origami; mỗi đoạn tự kín nên tháo đoạn kế bên không thủng |
| **đầu · bàn tay · bàn chân** | khối kín rời **+ socket** | tháo ra thay: tóc/mũ trùm đầu, găng, GIÀY thay bàn chân |

⛔ Bài học v1→v2 (đo 22/10): dựng ngực/bụng/hông thành 3 khối lồi rời ⇒ cắt ngang thấy **bậc 45–190 mm** và nhìn ra 3 hộp chồng. Chỉ đổi sang thân liền mới hết.

## 3. Bảng mặt cắt thân (người 1,80 m — `THAN` trong lpm.py)
Mỗi mốc: `(tên, z, nửa rộng X, nửa sâu Y, tâm Y, {góc°: hệ số đẩy theo bán kính})`.
Góc đo từ giữa ngực (0°, phía −Y) vòng ra sau (180° = giữa lưng), một góc áp CẢ HAI bên.
Vòng thân dùng `GOC_THAN` = 0 · 30 · 60 · 90 · 120 · 150 · **165** · 180° (14 đỉnh) — mọi vòng PHẢI cùng danh sách góc.
Mốc nam: cổ_đáy 1,505 · vai 1,455 · ngực 1,36 · dưới_ngực 1,27 · eo 1,13 · mào_chậu 1,035 · xương_cùng 0,985 · hông 0,935 · mông 0,88 · mông_dưới 0,835 · lằn_mông 0,80.
- Rãnh ức = 0° ×0,93 · cơ ngực = 30° ×1,03 · rãnh sống lưng = 180° ×0,88–0,92.
- Nữ: vai hẹp 2 cm, eo thắt hơn, hông/mông rộng hơn; ngực = 30° ×1,12 + 60° ×1,04, khe ngực 0° ×0,86.
- **Muốn đổi dáng (béo, gầy, cơ bắp, trẻ con) thì SỬA BẢNG**, đừng chèn khối mới vào thân.

### 3b. MÔNG — nhô NHẸ + đáy hình «W» (Boss 22/10/2026)
- 4 vòng dưới thân (mào_chậu · hông · mông · đáy_chậu). Ở `mong`: 150° ×1,06 · 165° ×1,03 · 180° ×0,88 (nữ 1,08 · 1,04 · 0,86).
- **Vòng `day_chau` CONG** (phần tử thứ 7 = {góc°: lệch z m}): thấp nhất dưới mỗi múi (150–165°: −12/−10 mm), NHÔ LÊN ở khe (180°: +30), hông (90°: +40), háng trước (30–60°: +30/+35).
- **Chóp đáy chậu** nâng +20 mm và dời ra trước 25 mm, giấu giữa hai đùi. Để chóp thấp nhất ở giữa ⇒ đáy thân thành cái bát/gấu váy.
- ⛔ v2.1: thêm `mong_duoi`+`lan_mong`, 150° tới 1,16 ⇒ nhô 68 / khe 31 mm ⇒ XỆ. ⛔ v2.3a: vòng đáy phẳng, rộng bằng hai đùi ⇒ GẤU VÁY ngang.

### 3c. ĐẦU FACELESS — khối đá quý + trán (48 tam giác)
ConvexHull 31 điểm: gốc 38 + 6 điểm trán (+10 tam giác ⇒ trán lùi sau cung mày 57→11 mm). Không mắt, không mũi chi tiết.
⛔ Đã thử và Boss BỎ (22/10): v2.1 loft vùng T (360 tam giác) · v2.4 gờ mày + chọc hốc (56) · v2.5 hốc inset + con ngươi tối + mũi khối riêng (126).
Code các bản đó còn trong `lpm_v2.5_eyes_nose.py.bak` / `lpm_v2.3.py.bak` nếu có ngày cần lại. ⑨ giữ ≤80 tam giác, ≤1,5× thân ⇒ mặt chi tiết sẽ TRƯỢT.

### 3d. BÀN TAY — «găng hở ngón cái», co được để NẮM (`hand.py`, Boss 22/10 «tay với 1 ngón cái? có thể co lại để nắm?»)
5 khối lồi kín rời / tay, mỗi khối quay quanh 1 bản lề (rig cần 4 xương/tay):
| bộ phận | hình | kích thước (nam 1,80 m) | bản lề (trục) |
|---|---|---|---|
| `ban_tay_*` | hộp thon 8 đỉnh + gò mô cái | dài 95 · rộng 64→84 · dày 26→22 mm | cổ tay (socket `ban_tay_*`) |
| `ngon1_*` | khối 4 ngón DÍNH, đốt gần | dài 45 · rộng 80 · dày 20 | KHỚP NGÓN, trục ngang bàn tay |
| `ngon2_*` | khối 4 ngón, đốt xa + mũi vát | dài 35 · rộng 66→53 · dày 16 | GIỮA NGÓN, song song |
| `cai1_*` | lăng trụ 5 cạnh | dài 40 · r 11 | GỐC CÁI, trục dọc bàn tay (lật đối diện) |
| `cai2_*` | lăng trụ 5 cạnh + mũi | dài 30 · r 9 | ĐỐT CÁI |
- Hệ cục bộ: u = dọc (cổ tay → ngón), v = ngang (+v = phía ngón cái), n = pháp tuyến LÒNG. Tư thế chữ A: lòng hướng vào đùi, ngón cái ra trước.
- Một tham số `--co` ∈ [0, 1]: 0 xoè · 1 nắm. Góc ở co = 1 do MÁY DÒ LƯỚI tìm (tối đa độ ôm, lún ≤1,5 mm):
  nam khớp 76° · giữa 90° · cái lật 90° · cái gập 20° (ôm 81 %, lún 0,9 mm) · nữ 80° · 70° · 80° · 30° (ôm 78 %, lún 0,4 mm).
- Vật nắm: trụ Ø32 mm (báng súng/cán kiếm) — KHÔNG co theo người (tay nữ nhỏ 8 % mà dùng góc nam ⇒ lún 7 mm). Tâm trụ = socket `cam_*`, `len` = trục trụ, `r` = 0,016.
- `.json` → `khop_tay[L|R]`: tâm + trục từng bản lề (thế giới) để dựng rig.
- ~74 tam giác/tay. Muốn đổi cỡ: sửa `TAY` trong hand.py rồi CHẠY LẠI máy dò (đoạn mẫu trong §9) — đừng tự chỉnh góc bằng mắt.

## 4. HỢP ĐỒNG GẮN (lớp đắp đọc phần này — đừng đổi tên tuỳ tiện)
Bộ phận (node trong GLB): `than co dau bap_vai_L/R canh_tay_L/R khuyu_L/R cang_tay_L/R ban_tay_L/R ngon1_L/R ngon2_L/R cai1_L/R cai2_L/R dui_L/R goi_L/R cang_chan_L/R ban_chan_L/R`.
Socket (node rỗng `SOCKET_<tên>` trong GLB + toạ độ trong `.json`):
| socket | ở đâu | dùng cho |
|---|---|---|
| `dau` | đỉnh cổ | thay đầu / tóc / mũ (tháo `dau` hoặc trùm lên) |
| `ban_tay_L/R` | cổ tay, `len` = hướng ngón | găng tay, tay khác |
| `cam_L/R` | TÂM trụ nắm Ø32 (khi co = 1), `len` = trục trụ, `r` | súng, kiếm, đồ cầm — đặt cán đồ trùng trụ này rồi build `--co 1` |
| `ban_chan_L/R` | cổ chân, `len` = hướng mũi chân | **giày: tháo `ban_chan_*` rồi đặt giày tại socket** (cẳng chân tự kín nên không hở) |
| `lung` | giữa lưng | ba lô, cánh, bình |
| `hong_L/R` | hai bên hông | bao súng, túi |

## 4b. LỚP ĐẮP: tóc · đồ · công cụ — để ở skill RIÊNG (Boss 22/10: «cập nhật vào bộ skill … chắc để riêng file model-outfit»)
Không nhét vào LPM. Skill `humanoid-replaceable-assets` (~/.hermes/skills/creative/humanoid-replaceable-assets/) giữ:
tóc đặt bằng tia chạm đầu thật · đồ settler = vỏ thân nới 8–11 mm + ống vạt/váy đo theo điểm rải dày · công cụ cầm tay khớp socket `cam_*`
(cán Ø32 mm, gốc ở chỗ cầm) · cửa «không lún vào người» (parity 3 tia bỏ phiếu). LPM chỉ cần giữ ĐÚNG hợp đồng §4.

## 5. Cửa soi `check_lpm.py` (tự chạy trong build; gọi tay: `python3 check_lpm.py <out>`)
① mọi bộ phận kín ② 300–2500 tam giác ③ cao đúng ±1 %, đáy ∈ [−5, +10] mm ④ thể tích 0,055–0,095 m³ × (cao/1,8)³
⑤ **thân liền**: cắt ngang mỗi 1 cm từ `mong` tới `vai`, mỗi lát đúng **1 vòng kín**, bậc rộng/sâu ≤ 20 mm
⑥ đủ bộ phận + socket theo §4 ⑦ đối xứng L/R lệch < 3 % ⑧ **eo thắt**: rộng eo ≤ 0,93 × min(ngực, hông)
⑨ **mặt đầu (faceless)** ≤80 tam giác, mật độ ≤1,5× thân ⑩ **mông nhẹ**: nhô 30–60 mm (nữ 40–80), khe 5–20 mm
⑪ **trán**: mặt trước ở z 1,765 lùi ≤25 mm sau z 1,725 ⑮ **tay nắm**: trụ Ø32 tại `cam_*` — lún ≤1,5 mm; co ≥0,95 ôm ≥75 %; code co=1 luôn phải nắm được ⑫ **không váy**: viền đáy thân nhìn từ sau hình «W» — khe và hông cao hơn đáy múi ≥15 mm.
- Thử ngược 22/10 (đã chạy, có số): thân 3 khối mặt cắt lệch ⇒ ⑤ bắt (bậc 72 mm, rc=1) · thân 1 khối lồi ⇒ ⑧ bắt (eo/min = 1,02, rc=1) · thân liền đúng ⇒ rc=0 (eo/min = 0,82). v2.2 (22/10): chạy cửa mới lên bản v2.1 Boss chê ⇒ ⑨ bắt (360 tam giác, 6×, rc=1) · ⑩ bắt (nhô 68 / khe 31 mm, rc=1). ⚠ phép đo «đỉnh múi tụt» KHÔNG phân biệt được bản xệ (cả hai 0 mm) — bản xệ bị bắt nhờ TRẦN nhô + trần khe, đừng nới hai trần đó.
- Cổ→vai và đáy chậu là «nắp», dốc gắt đúng giải phẫu ⇒ cố ý KHÔNG đo bậc ở đó.
- Lát cắt trùng đúng hàng đỉnh sẽ vỡ thành nhiều đoạn GIẢ ⇒ soi bỏ qua lát cách mốc < 3 mm (đừng gỡ).
- ⛔ Đừng nới `BAC_TOI_DA` để cho qua; sửa bảng mặt cắt.

## 6. Vòng tiến hoá (evolve) — mỗi lượt phải có SỐ ĐO, không chỉ «nhìn đẹp hơn»
1. Build → cửa soi phải ĐẠT (mã 0).
2. `view_lpm.py` ra 4 góc; đặt cạnh ảnh mẫu, ghi từng bộ phận: khác gì, cỡ bao nhiêu (cm/độ).
3. Sửa BẢNG (thân) hoặc tham số `KHOP` (tay chân) — một thay đổi có tên mỗi lượt.
4. Build + xem lại; so tấm trước/sau. Lượt nào không có số đo thay đổi là lượt hỏng.

## 7. Bẫy đã trả giá
- **Chọn trục tham chiếu cho vòng**: v1 lấy sai ⇒ bán kính rộng rơi vào trục Y, khúc bụng xoay 90° (sâu 30 cm, rộng 17 cm). `vong_truc()` đã cố định: rx = ngang (X), ry = sâu.
- **GLB phải Y-lên**: xuất thẳng toạ độ Z-lên thì Blender/three.js thấy người NẰM (cao đo ra 0,30 m).
- **Bắp vai**: dựng quanh trục X thế giới ⇒ chỏm nhô mũi nhọn lên trời. Phải dựng quanh TRỤC CÁNH TAY.
- ConvexHull cho THÂN = mất eo/mông. Đầu thì CỐ Ý dùng ConvexHull (khối đá quý ít mặt — Boss chọn).
- Ảnh render từ phía sau mà đèn chính ở trước ⇒ lưng chìm bóng, tưởng mông phẳng. `view_closeup.py` xoay đèn chính theo phía nhìn.

## 8. Phong cách
Mặt phẳng, `use_smooth=False`, đất sét ấm `#cbb39a` hoặc giấy washi `#fefcf6`; đèn 3 điểm (key ấm 3,2 · fill lạnh 1,1 · rim 2,0); viền gấp: chỉ vẽ cạnh bóng + nếp gấp > 20°.

## 9. SỔ THEO DÕI NÂNG CẤP (đọc trước khi sửa; thêm dòng sau MỖI lượt Boss góp ý)
| bản | ngày | Boss nói | đổi gì | số đo | cửa chặn |
|---|---|---|---|---|---|
| 1.3 | 21/10 | (Antigravity + Hermes) | mặt/râu primal ghim cứng; thân 3 khối lồi | thân bậc 45–190 mm | — |
| 2.0 | 22/10 | «nâng cấp skill, bỏ primal» | thân LIỀN theo bảng mặt cắt; chi rời; socket; đầu đá quý | 570 tam giác, eo/min 0,82 | ①–⑧ |
| 2.1 | 22/10 | «spec mặt chữ T lõm… mông cũng cần spec» | đầu loft vùng T (360 tam giác); mông 5 vòng | hốc lùi 8–20 mm; mông nhô 68 | (đã thay) |
| 2.2 | 22/10 | «thích bản chưa nâng cấp mắt mũi… nhiều mặt phẳng quá… mông hơi xệ, chỉ cần 1 chút» | đầu về đá quý 38 tam giác; mông 4 vòng nhẹ | đầu 0,7× mật độ thân; nhô 51 / khe 14 | ⑨ mật độ đầu · ⑩ trần mông |
| 2.3 | 22/10 | «thêm ít nhất bao nhiêu mặt… nhìn ngang thiếu trán… mông chưa mất cạnh dưới (giống váy)» | +6 điểm trán (+10 tam giác); vòng đáy cong «W», chóp đáy chậu nâng + dời trước | trán lùi 57→11 mm; khe/hông cao hơn đáy múi 20/38 mm | ⑪ trán · ⑫ viền W |
| 2.4 | 22/10 | «T lõm làm như thế nào với setup mặt hiện có? thay đổi ít nhất?» | +2 điểm gờ mày; `hoc_mat()` chọc 2 hốc (bỏ 3 tam giác/bên, nối viền về đỉnh lùi 12 mm) | 48→56 tam giác (1,0× thân); hốc sau mày 6 / sau mũi 20 mm | ⑬ vùng T nhẹ (v2.3 trượt ⑬, v2.1 trượt ⑨) |
| 2.5 | 22/10 | «hốc mắt mũi vẫn chưa ra - cần sáng tạo hơn tính toán kỹ hơn với code» | mắt inset hạnh nhân (viền nhô 2 mm, thành vách, đáy) + con ngươi tối rời; mũi = khối lồi riêng có mặt dưới; vật liệu glTF Body_Ivory/Eye_Dark | đầu 126 tam giác (2,2× thân); con ngươi 1,6 cm²; mặt dưới mũi 11,7 cm² | ⑭ mắt+mũi (v2.4 trượt: 0/0) · ⑨ nới 140/2,5× (v2.1 vẫn trượt 6×) |
| 2.6 | 22/10 | «cả 2 version trên đều ko đc. reverse lại version bạn mới sửa đầu - tag faceless humanoid. develop spec cho hand (1 ngón cái? co lại để nắm?)» | đầu về v2.3; gỡ ⑬⑭, ⑨ về 80/1,5×; tay 5 khối có bản lề, `--co`; góc nắm do máy dò lưới | tay 74 tam giác; nắm trụ Ø32: nam ôm 81 % lún 0,9 · nữ 78 % lún 0,4 | ⑮ tay nắm (thử ngược: gập 0° → 30 % trượt · gập nửa → 35 % trượt · gập quá → lún 16 mm trượt · găng cũ v2.3 → thiếu bộ phận trượt) |
| 2.7 | 24/10 | «làm tóc vẫn chưa ra stylized cần phát triển thêm» (Boss 22/10) + «do 1 and 2 like you said» (Boss 24/10) | Tóc múi nêm Origami (Clump Grammar) 12 múi vát nhọn so le quanh đầu + Cửa soi đường viền chân tóc (Silhouette Gate `check_hair.py`) | 36 tam giác; độ nảy răng cưa nam 25,8 mm / nữ 50,8 mm (≥15 mm); 0/4000 lún sọ | ⑯ Tóc Origami múi nêm (⑯a ≤450 tris, ⑯b răng cưa ≥15 mm, ⑯c 0/4000 lún sọ) |
| 2.8 | 24/10 | «water pond should not be perfectly round... update LPM skill with trees, mountains, waterfall, deer pack... rule for size in procedural low poly skill» (Boss 24/10) | Chuẩn hóa toàn bộ hệ sinh thái diorama & tỷ lệ thế giới (Rule for Size): Sồi v2 5.8-6.5m, Núi thác Master v11.0 (núi liền khối, thác tràn kín vách, hồ đỉnh liền dòng, hồ organic bất đối xứng, sông S-curve spline 28 điểm), Đàn hươu (Đực/Mẹ/Con), Thỏ sạch | Cây sồi thu gọn 12m→6m; Sông spline 28 điểm; Hồ 20 điểm bán kính 5.1-6.7m; 0 vệt xám; 0 chuỗi đá nhân tạo | ⑰ Chuẩn Tỷ Lệ Thế Giới & Môi Trường Procedural (Cây/Thú/Núi/Nước) |

### Bài học về CỬA SOI (đừng lặp)
- v2.3 có HAI thước «váy» báo ĐẠT trên bản vẫn còn gấu váy: ① % diện tích đáy thân ngoài đùi (15 %) ② diện tích mặt úp xuống ngoài đùi (86 cm²). Thứ Boss nhìn là **HÌNH VIỀN** (đường đáy phẳng ngang) — đo diện tích là đổi điều cần chứng minh lấy thứ dễ đo. Cửa ⑫ hiện đo hình viền bằng tia quét.
- Mỗi cửa mới: chạy lên bản Boss ĐÃ CHÊ phải ra rc=1, VÀ render nhìn lại bản đạt — cửa đạt mà mắt thấy sai thì cửa sai.
- ⑩ phép «đỉnh múi tụt» không phân biệt được bản xệ (đều 0 mm) — bản xệ bị bắt nhờ trần nhô/khe.
- ⑬ (độ sâu hốc) cho bản v2.4 ĐẠT mà Boss vẫn thấy «chưa ra» — độ sâu hình học không bằng thứ mắt đọc (bóng + màu tối). Cửa phải đo cái người xem nhìn thấy.

### Máy dò góc nắm (chạy lại khi đổi cỡ tay)
```python
import itertools, tay
G, T = tay.GOC_NAM, tay.TRU_NAM          # nữ: GOC_NAM_NU, TRU_NAM_NU, dung_tay(1.0, nu=True)
best = None
for khop, giua, u, n, cd, cg in itertools.product(range(64, 101, 4), range(70, 131, 8), (0.064, 0.068, 0.072, 0.076, 0.080),
                                                  (0.026, 0.028, 0.030, 0.032), range(70, 101, 10), range(0, 41, 10)):
    G.update(khop=khop, giua=giua, cai_doi=cd, cai_gap=cg); T.update(u=u, n=n)
    bo, _, tru = tay.dung_tay(1.0); om, lun = tay.do_nam(bo, tru)
    if lun <= 1.5 and (best is None or om > best[0]): best = (om, lun, khop, giua, u, n, cd, cg)
print(best)   # ghi vào GOC_NAM / TRU_NAM
```


## Animating LPM / settler bodies (23/10/2026)
Animation is NOT done in this skill. Use `humanoid-rig-animation` and read its §PREVENTION RULES + the manifest
`~/projects/GameDev/anim_settler/MANIFEST_ADJUSTMENTS_2026-10-23.md` first (why Boss had to correct bow/spear/crouch clips and how it is blocked).

## 10. Sub-Skills & Hệ Sinh Thái Companion (GameDev)
### Sub-skills tích hợp sẵn trong repo (`skills/`)
1. **`skills/humanoid-replaceable-assets`**:
   - Quản lý các lớp đắp gắn qua socket: Tóc múi nêm Origami (`hair_origami.py`), quần áo settler (`hair_outfit.py`), công cụ cầm tay (`tools.py`).
2. **`skills/procedural-low-poly-world`**:
   - Dựng thế giới đảo nổi, môi trường diorama low-poly procedurally (Three.js & Godot 4).

### Con trỏ 2 chiều sang Không gian GameDev (`projects/GameDev`)
- **Đường dẫn**: `~/projects/GameDev` (Local Companion Workspace).
- **Phân công & Quan hệ**:
  - `lpm-faceless-humanoid` là **Authority** cung cấp mesh người base faceless, hợp đồng socket, tóc origami và 16 cửa soi.
  - `GameDev` là **Engine & Xưởng Game Asset**:
    - **Engine dựng hình**: `lpms/lpms_helpers.py` (`khoi()`, `khoi_meo()`, `quet()`, `dun()`, `la_gap()`).
    - **Bảng màu sRGB**: `theme_colors.py`.
    - **Kho 34 Game Assets**: `lpms_store/` (bàn ghế, công cụ, vũ khí, rương hòm...).
    - **Starter Packs**: `assets/aoe_starter_pack/` (Mountain Waterfall Pack Master v6.0, Starter 4-Square Storage, Stylized Oak Tree).
    - **Testbed chuyển động**: `anim_settler/`.

## 11. Bảng Tỷ Lệ Thế Giới & Ngân Sách Kích Thước (Rule for Size)
Mọi tài sản môi trường, cây cối, động vật trong hệ sinh thái BẮT BUỘC phải quy chiếu chuẩn theo nhân vật Người Khai Hoang LPM ($H = 1,80\text{m}$):

| Thực Thể | Chiều Cao / Kích Thước | Tỷ Lệ So Với Người | Quy Cách Tạo Hình & Silhouette |
|---|---|---|---|
| **Người LPM (Humanoid Base)** | **$1,80\text{m}$** | **$1,00\times$ (Mốc Gốc)** | Thân người origami trơn faceless, ngón cái co được, 16 cửa soi. |
| **Cây Sồi Stylized Oak v2** | $5,80\text{m} - 6,50\text{m}$ | $3,2\times - 3,6\times$ người | Thân cây có 2 nhánh lộ rõ nâng các cụm tán rời; đã thu nhỏ từ 12m xuống 6m để cân đối với muông thú. |
| **Cây Thông (Pine Tree)** | $6,50\text{m} - 7,50\text{m}$ | $3,6\times - 4,2\times$ người | Tán lá hình nón 3 tầng giật cấp vuốt nhọn. |
| **Bụi Cây Berry (Bush)** | $0,90\text{m} - 1,10\text{m}$ | $0,50\times - 0,60\times$ người | Ngang thắt lưng người, thấp hơn vai hươu; điểm thu hoạch quả. |
| **Hươu Đực (Stag)** | Vai $1,50\text{m}$ / Gạc $2,10\text{m}$ | Vai $0,83\times$ / Chóp gạc $1,17\times$ | Gạc chia nhánh procedural màu trắng xương (`#ede4d3`), ngực vạm vỡ. |
| **Hươu Mẹ (Hind)** | Vai $1,30\text{m}$ | $0,72\times$ người | Cổ thon dài, không gạc, bụng màu kem mềm mại. |
| **Hươu Con (Fawn)** | Vai $0,85\text{m}$ | $0,47\times$ người | Tỷ lệ đầu to tai to chân ngắn đáng yêu, chấm đốm lưng nhẹ. |
| **Thỏ (Rabbit)** | Cao $0,45\text{m}$ | $0,25\times$ người | Động vật nhỏ, ngang đầu gối người; ngực sạch không tem dán. |
| **Kho 4 Ô (Starter Storage)** | $4,00\text{m} \times 4,00\text{m} \times 0,25\text{m}$ | $2,22\times$ bề ngang người | Nền gỗ 4 ô $2\text{m} \times 2\text{m}$, 4 cọc gỗ góc vát nhọn. |
| **Rặng Núi Vách Đứng** | Đỉnh cao nguyên $8,50\text{m} - 9,00\text{m}$ | $4,7\times - 5,0\times$ người | Dãy núi liền khối 2 tầng (thềm thấp $4,8\text{m}$, cao nguyên $8,5\text{m}$). |

## 12. Đặc Tả Chuẩn Bộ Núi Thác Nước Master v11.0
- **Dãy núi liền khối (Unified Massif):** Dãy núi là một khối đá duy nhất trải dài toàn bộ chiều ngang ($X \in [-13.5, +13.5]$). Tuyệt đối không tạo khối chèn giữa (`Center_Connecting_Ridge`) hay bậc hạ thấp gây lộ đường nối.
- **Máng thác bám sát thành vách (Flush Stepped Bedrock):** Khối đá bệ đỡ sau thác giật cấp bậc thang khớp $100\%$ từng góc cạnh của máng nước (rơi ở $Y = 20.5, 18.8, 16.8$). Không có khoảng hở không khí phía sau.
- **Nước tràn kín 2 vách hẻm núi (Wall-to-Wall Water):** Máng nước rộng $4.84\text{m}$ phủ kín hẻm núi rộng $4.80\text{m}$, lẹm $2\text{cm}$ vào vách đá hai bên. Không có gờ đá khô lộ ra hai bên máng nước.
- **Hồ nước đỉnh núi hàn liền máng thác:** Hồ nước đỉnh cao nguyên ($Z = 8.52\text{m}$) hàn chung một lưới với máng thác tại mép tràn $Y = 20.5$, nước đổ tràn qua gờ núi liên tục.
- **Hồ hạ thổ bất đối xứng tự nhiên (Organic Non-Circular Pond):** Đáy hồ hạ thổ âm đất ($Z = 0.18\text{m}$, mặt đất $0.40\text{m}$). Đường biên là đa giác hữu cơ 20 điểm lượn sóng tự nhiên ($r \in [5.1\text{m}, 6.7\text{m}]$), không được dùng hình tròn hoàn hảo.
- **Dòng sông S-curve uốn lượn mượt mà (Sinusoidal Spline):** Dòng sông uốn lượn 28 điểm spline với bờ kè vát $45^\circ$, lấn sâu vào lòng hồ tận $Y = 11.5\text{m}$ để xóa sạch vệt viền xám ngăn cách.
- **Bờ hồ tự nhiên:** Mặt cỏ tiếp giáp trực tiếp mặt nước; gỡ bỏ hoàn toàn chuỗi đá xếp đều quanh hồ.



---

## Curated character profile reference — `primal-detailed-settler` (2026-10-24)

**Do not merge this into the canonical faceless base.** The 8 screenshots of a muscular bearded primal man are a **separate, opt-in study** with detailed face, hair, clothes, skeleton and skin weights. Full observations, individual body-part meter targets and pixel annotations:
- [Primal Human 8-view spec](skills/humanoid-replaceable-assets/PRIMAL_HUMAN_REFERENCE_SPEC_2026-10-24.md)
- [Calibrated pixel/rig data](skills/humanoid-replaceable-assets/SKELETON_LANDMARKS_8VIEW.json)
- [Original images and their provenance](skills/humanoid-replaceable-assets/references/README.md)
- [Executable Primal Stone/Bone Axe generator](skills/humanoid-replaceable-assets/scripts/build_primal_axe.py), plus GLB under `assets/`.

The external reference contains a full facial/brow/eye/beard rig and separate finger silhouettes, which violates the strict **faceless head budget** if indiscriminately merged. Preserve LPM v2.7's 16 base gates, **separate** `primal-detailed-settler` geometry/LOD/skinning gates, and keep all socket names.

## English names (Boss 23–25/10/2026, ledger #111)
Every file/folder name in this repo and in GameDev is English. Gate: `.git/hooks/pre-commit` → `python3 ~/bin/rename_to_english.py scan-staged` (refuses Vietnamese-named paths); full scan `rename_to_english.py scan <repo>`; reverse proof `~/bin/test_english_names_precommit.sh vn` (must exit 1).
