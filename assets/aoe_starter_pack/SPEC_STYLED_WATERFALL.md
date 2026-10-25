# ĐẶC TẢ KỸ THUẬT & NGHIÊN CỨU: THÁC NƯỚC STYLIZED LOW-POLY (WATERFALL SPEC)
*Project: GameDev / AoE Starter Pack / LPM Studio*  
*Chuẩn: Studio Ghibli / The Legend of Zelda: Breath of the Wild / Age of Empires Cozy RTS*  
*Người lập: Antigravity Game Asset Lead*

---

## 1. KHẢO SÁT & VẤN ĐỀ HIỆN TẠI (CRITICAL AUDIT)
- **Hiện trạng:** Thác nước trước đó chỉ là 2 tấm đa giác phẳng ghép lại (`Waterfall_Tier1` và `Tier2`) nối từ đỉnh núi xuống hồ, cạnh thẳng tắp và góc quá cứng, thiếu cảm giác trọng lực và dòng chảy hữu cơ.
- **Yêu cầu của Boss:** «waterfall really need research and spec. everytime your agent finish an asset, need to send me separately not install in the island until i approve.»
- **Mục tiêu:** Xây dựng module Thác Nước hoàn chỉnh, độc lập (modular standalone asset), có đầy đủ 5 tầng cấu trúc, đạt chuẩn thẩm mỹ Ghibli và ngân sách đa giác nhẹ ($\le 450$ tris).

---

## 2. KIẾN TRÚC 5 TẦNG CỦA THÁC NƯỚC STYLIZED (5-LAYER ARCHITECTURE)

```
       [ ĐỈNH NÚI: Thềm Đá Nứt Cố Định - Crest Lip ]
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
    [ TẦNG 1: Dòng Thác Dốc ]    [ VÁCH ĐÁ HẺM NÚI ]
    (Máng nước thu hẹp bề ngang)   (Đá trầm tích bậc thang ôm 2 bên)
             │                           │
             ▼                           ▼
    [ TẦNG 2: Thềm Đá Lắng Giữa Chừng ] (Mid Shelf & Basin)
    (Bể gom nước trung gian làm chậm nhịp rơi)
             │
             ▼
    [ TẦNG 3: Màn Nước Đổ Thẳng Đứng ] (Vertical Plunge)
    (Màn nước xòe rộng hình quạt khi rơi tự do)
             │
             ▼
    [ TẦNG 4: Hồ Chân Thác & Vòng Bọt Sóng ] (Impact Splash Pool & Foam Rings)
    (Hồ nước tròn lượn sóng + 2 vành bọt trắng phát quang)
             │
             ▼
    [ TẦNG 5: Cửa Thoát Nước Ra Suối Con ] (River Outlet)
```

---

## 3. THÔNG SỐ HÌNH HỌC & NGÂN SÁCH ĐA GIÁC (GEOMETRY SPECS)

| Bộ Phận | Dạng Hình Học (Geometry) | Kích Thước (Mét) | Ngân Sách Tris | Màu Sắc / Vật Liệu |
|---|---|---|---|---|
| **Crest Lip** | Thềm đá phiến vát cạnh (Chiseled Rock Slab) | Rộng $2.4\text{m}$, Sâu $1.8\text{m}$ | 36 tris | `M_RegularStone` (`#5A554E`) |
| **Cascade Tier 1** | Dải lưới cong chữ S (Curved Ribbon, 4 đốt) | Rộng $1.4\text{m} \to 1.8\text{m}$, Rơi $3.8\text{m}$ | 48 tris | `M_WaterfallChute` (`#8ED1E0`) |
| **Mid Basin** | Bể đá lắng trung gian + mặt nước gom | Đường kính $2.2\text{m}$, Cao $0.5\text{m}$ | 44 tris | `M_RegularStone` + `M_RiverWater` |
| **Vertical Plunge** | Màn nước hình thang xòe rộng (Fan Curtain) | Rộng $1.8\text{m} \to 2.6\text{m}$, Rơi $3.6\text{m}$ | 32 tris | `M_WaterfallChute` + gân bọt trắng |
| **Splash Pool** | Hồ lắng chân núi hình elip tự nhiên | Trục lớn $4.2\text{m}$, Trục nhỏ $3.6\text{m}$ | 56 tris | `M_RiverWater` (`#327E8C`) |
| **Foam Crests** | 2 vành bọt sóng đồng tâm hình đa giác | Bán kính $3.8\text{m}$ & $4.3\text{m}$ | 48 tris | `M_Foam` (`#E8F6FA`, Emission 1.2) |
| **Gorge Flank Rocks** | 6 khối đá tự nhiên ôm 2 bên hốc thác | Chiều cao bậc $1.2\text{m} - 2.5\text{m}$ | 140 tris | `rock_medium.glb` & `rock_small.glb` LPM |
| **TỔNG CỘNG** | **Module Thác Nước Hoàn Chỉnh** | **Cao 8.5m, Chân 6m x 6m** | **~404 tris** | **Đạt chuẩn Performance Game Mobile / RTS** |

---

## 4. HỢP ĐỒNG VẬT LIỆU & BẢNG MÀU GHIBLI (MATERIAL CONTRACT)

1. **`M_WaterfallChute` (Dòng Thác):**
   - Base Color: `#8ED1E0` (Xanh ngọc bọt khí sRGB `142, 209, 224`).
   - Emission Color: `#E8F6FA` (Trắng băng lam `232, 246, 250`), Emission Strength = `0.85`.
   - Roughness = `0.15`, Metallic = `0.0`.
   - Cơ chế UV: Trục Y trải dài từ 0.0 đến 1.0 hỗ trợ shader UV-scrolling (nước chảy xuống tốc độ $1.8\text{ m/s}$).
2. **`M_Foam` (Bọt Sóng Đập Nước):**
   - Base Color: `#F0F8FA` (`240, 248, 250`).
   - Emission Strength = `1.4` (Tạo hiệu ứng phát sáng nhẹ đặc trưng của phim hoạt hình Ghibli).
3. **`M_RiverWater` (Nước Hồ Chân Thác):**
   - Base Color: `#327E8C` (`50, 126, 140`).
   - Roughness = `0.12`, Transmission / Depth Fade tự nhiên.
4. **`M_RegularStone` (Vách Đá Hẻm Núi):**
   - Base Color: `#5A554E` (`90, 85, 78`).
   - Roughness = `0.88`, Shading phẳng (Flat Shaded) sắc nét.

---

## 5. QUY TRÌNH DUYỆT ASSET RIÊNG BIỆT (MODULAR ASSET APPROVAL GATE)
- Tuân thủ nghiêm ngặt chỉ thị của Boss: **"everytime your agent finish an asset, need to send me separately not install in the island until i approve."**
- Thác nước sau khi dựng xong sẽ:
  1. Render ảnh showcase riêng biệt góc 3D cận cảnh (không gắn vào đảo).
  2. Xuất file `waterfall_pack.glb` riêng biệt.
  3. Gửi trực tiếp lên Telegram để Boss kiểm duyệt và chốt duyệt trước khi tích hợp.
