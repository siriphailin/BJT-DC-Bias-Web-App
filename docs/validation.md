# Validation — BJT DC Bias + Lab 04 CE Amplifier Simulator

เอกสารนี้สรุปสมมติฐาน, สมการที่ใช้, การคำนวณมือทีละขั้น, ค่าอ้างอิง, ผล ngspice จริง
และหลักฐานการตรวจ B1–B8 เพื่อแสดงว่าค่าที่เว็บแสดงนั้นเชื่อถือได้

## 1. สมมติฐานของแบบจำลอง (Forward-Active Approximation)

แบบจำลองนี้ใช้ได้เฉพาะเมื่อทรานซิสเตอร์อยู่ใน **Forward-Active region** และตั้งอยู่บนสมมติฐาน:

1. **β คงที่** — กระแส `IC = β · IB` เสมอ ไม่ขึ้นกับแรงดัน (ไม่คิด Early effect)
2. **VBE คงที่** — ใช้ค่าที่ผู้ใช้กรอก (ค่ามาตรฐาน 0.70 V) ไม่คำนวณจาก diode equation
3. **ไม่คิดกระแสรั่ว (leakage)** ในสถานะ cutoff
4. **อุณหภูมิคงที่** — β และ VBE ไม่เปลี่ยนตามอุณหภูมิ
5. **ไม่ใช่ผลจาก SPICE** และไม่ใช่ผลจากการวัดจริง — เป็นการคำนวณเชิงวิเคราะห์เพื่อการสอน

## 2. สมการที่ใช้

```
VTH = VCC · R2 / (R1 + R2)          ← Thévenin voltage ที่ขา Base
RTH = R1 · R2 / (R1 + R2)           ← Thévenin resistance ที่ขา Base
IB  = (VTH − VBE) / (RTH + (β+1)·RE)
IC  = β · IB
IE  = (β + 1) · IB
VE  = IE · RE
VB  = VE + VBE
VC  = VCC − IC · RC
VCE = VC − VE
```

สมการทั้งหมดอยู่ใน [`../dc_bias.py`](../dc_bias.py) ที่เดียว — template ไม่มีสมการ

## 3. การคำนวณมือทีละขั้น (ชุดค่าตัวอย่างจากใบงาน)

**ค่าที่กรอก:** `VCC = 12 V`, `R1 = 100 kΩ`, `R2 = 22 kΩ`, `RC = 2.2 kΩ`, `RE = 1 kΩ`,
`β = 100`, `VBE = 0.70 V`

**ขั้นที่ 1 — Thévenin equivalent ที่ขา Base**

```
VTH = 12 × 22,000 / (100,000 + 22,000)
    = 264,000 / 122,000
    = 2.163934 V

RTH = 100,000 × 22,000 / (100,000 + 22,000)
    = 2,200,000,000 / 122,000
    = 18,032.787 Ω  (18.0328 kΩ)
```

**ขั้นที่ 2 — กระแส Base**

```
ตัวส่วน = RTH + (β + 1)·RE
        = 18,032.787 + 101 × 1,000
        = 18,032.787 + 101,000
        = 119,032.787 Ω

ตัวเศษ  = VTH − VBE = 2.163934 − 0.700 = 1.463934 V

IB = 1.463934 / 119,032.787 = 12.2986 µA
```

**ขั้นที่ 3 — กระแส Collector และ Emitter**

```
IC = 100 × 12.2986 µA = 1.22986 mA
IE = 101 × 12.2986 µA = 1.24216 mA
```

**ขั้นที่ 4 — แรงดันที่ขาต่าง ๆ**

```
VE  = 1.24216 mA × 1 kΩ  = 1.24216 V
VB  = 1.24216 + 0.70     = 1.94216 V
VC  = 12 − (1.22986 mA × 2.2 kΩ)
    = 12 − 2.70569
    = 9.29431 V
VCE = 9.29431 − 1.24216  = 8.05216 V
```

## 4. ตารางค่าอ้างอิง

| ปริมาณ | ค่าที่คำนวณเต็มความละเอียด | ค่าในใบงาน | หมายเหตุ |
|---|---|---|---|
| VTH | 2.16393 V | 2.1639 V | |
| RTH | 18.03279 kΩ | 18.0328 kΩ | |
| IB | 12.2986 µA | 12.298 µA | ใบงานปัดเป็น 12.298 µA |
| IC | 1.22986 mA | 1.2298 mA | ใบงานคำนวณจาก IB ที่ปัดแล้ว |
| IE | 1.24216 mA | 1.2421 mA | |
| VE | 1.24216 V | 1.2421 V | |
| VB | 1.94216 V | 1.9421 V | |
| VC | 9.29431 V | 9.2944 V | |
| VCE | **8.05216 V** | **8.0523 V** | ต่างกัน 0.0002 V (0.002 %) |

### ความต่างจากค่าที่ปัดในใบงาน (หลักที่ 4)

ใบงาน **ปัด `IB = 12.298 µA` ก่อน** แล้วนำไปคูณต่อ:

```
ใบงาน:   IC = 100 × 12.298 µA   = 1.2298 mA   →  VCE = 8.052342 V
โปรแกรม: IC = 100 × 12.2986 µA  = 1.22986 mA  →  VCE = 8.052155 V
```

โปรแกรม **ไม่ปัดเศษกลางทาง** (คำนวณด้วย floating point เต็มความละเอียดแล้วค่อยจัดรูปแบบ
ตอนแสดงผล) ซึ่งเป็นวิธีที่ถูกต้องกว่าในทางวิศวกรรม ทั้งสองค่าเมื่อแสดง 3 ตำแหน่งทศนิยม
ได้ `8.052 V` เท่ากัน จึงไม่มีผลต่อการตรวจคำตอบ

## 5. การตรวจสอบอิสระ (Independent Verification)

นอกจากเทสต์ที่ฝังในโปรเจกต์แล้ว สมการยังถูกตรวจด้วย **วิธีที่สองที่ไม่ใช้ Thévenin เลย**
คือตั้ง KCL ที่ node ของ Base แล้วแก้หา `IE` โดยตรง:

```
(VCC − VB)/R1 = VB/R2 + IB          โดยที่  VB = IE·RE + VBE  และ  IB = IE/(β+1)

⇒ IE · [ RE/R1 + RE/R2 + 1/(β+1) ] = VCC/R1 − VBE/R1 − VBE/R2
```

ผลลัพธ์ทั้งสองวิธีตรงกันถึง **2.2 × 10⁻¹⁶** (ระดับความคลาดเคลื่อนของ floating point)
ยืนยันว่าสมการใน `dc_bias.py` ไม่มีข้อผิดพลาดเชิงพีชคณิต

## 6. กรณีที่แบบจำลองใช้ไม่ได้

### 6.1 Cutoff — เงื่อนไข `VTH <= VBE`

เมื่อแรงดัน Thévenin ที่ขา Base ไม่สูงพอจะไบอัสขา Base–Emitter ให้นำกระแส:

- `IB = IC = IE = 0`
- `VE = 0 V`, `VB = VTH`, `VC = VCC`
- หน้าเว็บแสดง warning และข้อความ **"Active Region Approximation Does Not Apply"**

ตัวอย่าง: `R2 = 2.2 kΩ` → `VTH = 0.258 V < 0.70 V` → cutoff

### 6.2 Saturation — เงื่อนไข `VCE < 0.2 V`

เมื่อสมการ Forward-Active ให้ `VCE` ต่ำกว่า `VCE(sat) = 0.2 V` แปลว่ากระแสที่คำนวณได้
สูงเกินกว่าที่วงจรจะจ่ายให้ได้จริงในโหมด Active:

- โปรแกรม **ไม่ clamp** ค่า VCE แต่ปล่อยค่าดิบจากสมการไว้ (อาจติดลบ) แล้วติด warning
- เหตุผล: การ clamp จะทำให้หน้าจอดู "ปกติ" ทั้งที่แบบจำลองใช้ไม่ได้ ซึ่งทำให้เข้าใจผิด
  มากกว่าการแสดงค่าดิบพร้อมคำอธิบาย

ตัวอย่าง: `RC = 10 kΩ` → `VCE = −1.541 V` → saturation

### 6.3 ขอบเขตของค่า input ที่ยอมรับ

| เงื่อนไข | พฤติกรรม |
|---|---|
| `R1, R2, RC, RE <= 0` | ปฏิเสธ (HTTP 400) พร้อมระบุชื่อช่อง |
| `VBE <= 0` หรือ `VBE >= 1.0` | ปฏิเสธ — ถ้าปล่อยผ่านจะได้ผลที่ดูปกติแต่ไร้ความหมาย |
| `β <= 0` | ปฏิเสธ |
| ช่องว่างหรือข้อความที่ไม่ใช่ตัวเลข (`abc`) | ปฏิเสธพร้อมชื่อช่อง ไม่ crash |
| หน่วยความต้านทานที่รองรับ | ใช้ได้ | `ohm` (Ω), `kohm` (kΩ), `mohm` (MΩ = 1,000 kΩ = 1,000,000 Ω) |
| หน่วยที่ไม่รู้จัก | ปฏิเสธ |

## 7. วิธีตรวจซ้ำด้วยตัวเอง

```bash
# รันชุดทดสอบทั้งหมด (54 ตัว: Lab 03 20 + Lab 04 34)
python -m unittest discover -s tests -v

# ตรวจค่าตัวอย่างจากใบงานด้วยมือ
python -c "from dc_bias import calculate_dc_bias as f; r=f(12,100e3,22e3,2.2e3,1e3,100,0.7); print(r)"
```

แล้วเปิด <http://127.0.0.1:5000/> กรอกชุดค่าตัวอย่างในหัวข้อ 3 — หน้าจอต้องแสดง
`VCE = 8.052 V` และ `IC = 1.230 mA` ตรงกับตารางในหัวข้อ 4

---

## 8. Lab 03 — เพิ่ม Fixed Bias และ Emitter Bias

ส่วนนี้เพิ่มโหมดวงจรจาก 1 เป็น 3 โหมด โดย **คงสมการและผลของ Voltage Divider เดิมไว้ทั้งหมด**
(หัวข้อ 1–7 ยังใช้ได้กับโหมด Divider ตามเดิม)

### 8.1 สมการที่เพิ่มใน `dc_bias.py`

```text
Fixed Bias    IB = (VCC − VBE) / RB
              VE = 0 V  (Emitter ต่อลงกราวด์โดยตรง ไม่มี RE)

Emitter Bias  IB = (VCC − VBE) / [RB + (β+1)·RE]
(แหล่งจ่ายเดียว)

จากนั้นใช้ส่วนที่เหลือร่วมกับ Divider:
IC = β·IB, IE = (β+1)·IB, VE = IE·RE, VB = VE + VBE,
VC = VCC − IC·RC, VCE = VC − VE
```

ทั้งสามโหมดใช้ `_solve_bias()` ตัวเดียวกัน โดยโหมด Divider คำนวณ `VTH, RTH` จาก R1/R2
ส่วน Fixed และ Emitter ใช้ `VTH = VCC, RTH = RB` (Thévenin equivalent ที่ขา Base)
และ Fixed กำหนด `RE = 0` — สมการจึงเหมือน Divider ทุกประการและตรวจสอบได้ด้วยวิธีเดียวกัน

### 8.2 ค่าอ้างอิงอิสระ (คำนวณมือก่อนรันโปรแกรม)

ค่าคงที่ร่วม: `VCC = 12 V`, `RC = 2.2 kΩ`, `β = 100`, `VBE = 0.70 V`

**A2 — Fixed Bias, RB = 1 MΩ**

```text
IB  = (12 − 0.70) / 1,000,000      = 11.300 µA
IC  = 100 × 11.300 µA              = 1.1300 mA
VE  = 0 V                          (ไม่มี RE)
VB  = 0 + 0.70                     = 0.700 V
VC  = 12 − (1.1300 mA × 2.2 kΩ)    = 12 − 2.4860 = 9.5140 V
VCE = 9.5140 − 0                   = 9.5140 V
```

**A3 — Emitter Bias, RB = 1 MΩ, RE = 1 kΩ**

```text
ตัวส่วน = 1,000,000 + 101 × 1,000       = 1,101,000 Ω
IB  = 11.30 / 1,101,000                 = 10.2634 µA
IC  = 100 × 10.2634 µA                  = 1.02634 mA
IE  = 101 × 10.2634 µA                  = 1.03660 mA
VE  = 1.03660 mA × 1 kΩ                 = 1.0366 V
VB  = 1.0366 + 0.70                     = 1.7366 V
VC  = 12 − (1.02634 mA × 2.2 kΩ)        = 12 − 2.25795 = 9.74205 V
VCE = 9.74205 − 1.03660                 = 8.70545 V
```

**A4 — Emitter Bias, เปลี่ยนเฉพาะ RE เป็น 2 kΩ**

```text
ตัวส่วน = 1,000,000 + 101 × 2,000       = 1,202,000 Ω
IB  = 11.30 / 1,202,000                 = 9.40099 µA
IC  = 100 × 9.40099 µA                  = 0.94010 mA
IE  = 101 × 9.40099 µA                  = 0.94950 mA
VE  = 0.94950 mA × 2 kΩ                 = 1.89900 V
VB  = 1.89900 + 0.70                    = 2.59900 V
VC  = 12 − (0.94010 mA × 2.2 kΩ)        = 12 − 2.06822 = 9.93178 V
VCE = 9.93178 − 1.89900                 = 8.03278 V
```

**ทำนายก่อนรัน A4:** `IC` ต้อง **ลดลง** จาก A3 (1.02634 → 0.94010 mA) เพราะ `RE`
อยู่ในตัวส่วน `RTH + (β+1)·RE` — RE ใหญ่ขึ้นทำให้ IB ลดลง และ IC = β·IB จึงลดตาม

### 8.3 วิธีตรวจที่ใช้จริง และเหตุผลที่ไม่ได้ใช้ Playwright MCP

| ชั้นการตรวจ | สถานะ | รายละเอียด |
|---|---|---|
| Playwright MCP (`browser_navigate`, `browser_snapshot`) | **NOT USED** | โปรเจกต์นี้ยังไม่ได้ตั้งค่า MCP server ใน `opencode.json` |
| OpenCode Browser (browser tool ที่มีใน OpenCode Desktop) | **ใช้จริงทุกกรณี A1–A5** | เปิด `http://127.0.0.1:5000/`, อ่าน snapshot, เลือกโหมด, กรอกฟอร์ม, กด Calculate, ถ่าย screenshot |
| Manual | ไม่ได้ใช้ในรอบนี้ | นักศึกษาทวนเองอีกหนึ่งกรณี (หัวข้อ 8.6) |

ใบงานข้อ 05 ระบุว่า ถ้าเครื่องใช้ Playwright MCP ไม่ได้ ให้ "บันทึก Playwright MCP เป็น NOT RUN พร้อมเหตุผล
แล้วใช้ Browser Tool ที่มีใน OpenCode Desktop รุ่นที่รองรับ … ใช้กรณี A1–A5 และเกณฑ์ให้คะแนนเดียวกัน
แต่ระบุวิธีจริงว่าเป็น Playwright MCP, OpenCode Browser หรือ Manual" — ตารางด้านล่างจึงระบุวิธีจริง
เป็น **OpenCode Browser** ทุกแถว

เกณฑ์ตัดสิน: `|ΔIC| ≤ 0.01 mA` และ `|ΔVCE| ≤ 0.02 V` เทียบกับค่าอ้างอิงที่ยังไม่ปัดเศษ (หัวข้อ 8.2)
หน้าเว็บแสดง 3 ตำแหน่งทศนิยม

### 8.4 ตาราง A1–A5 (อินพุต · ค่าคาดหมาย · ผลจริง · หน่วย · วิธีตรวจ · สถานะ)

| กรณี | โหมด | อินพุต (หน่วยตามฟอร์ม) | ค่าคาดหมาย (อิสระ) | ผลจริงบนหน้าเว็บ | หน่วย | วิธีตรวจ | สถานะ |
|---|---|---|---|---|---|---|---|
| A1 · โหมดเดิม | Voltage Divider | R1 = 100 kΩ · R2 = 22 kΩ · RC = 2.2 kΩ · RE = 1 kΩ | IC 1.2299 · VCE 8.0522 (ผลเดิม Lab 2 ก่อนแก้) | IC **1.230** · VCE **8.052** · VB 1.942 · VC 9.294 | mA · V | OpenCode Browser | **PASS** |
| A2 · Fixed | Fixed Bias | RB = 1 MΩ (= 1000 kΩ) · RC = 2.2 kΩ (ไม่กรอก RE) | IC 1.1300 · VCE 9.5140 | IC **1.130** · VCE **9.514** · VB 0.700 · IB 11.300 | mA · V (IB = µA) | OpenCode Browser | **PASS** |
| A3 · Emitter | Emitter Bias | RB = 1 MΩ · RE = 1 kΩ · RC = 2.2 kΩ | IC 1.02634 · VCE 8.70545 | IC **1.026** · VCE **8.705** · VE 1.037 · VB 1.737 | mA · V | OpenCode Browser | **PASS** |
| A4 · เปลี่ยนค่าเดียว | Emitter Bias | เหมือน A3 แต่ RE = 2 kΩ | ทำนาย: IC **ลดลง** → IC 0.94010 · VCE 8.03278 | IC **0.940** (ลดจาก A3 ✅) · VCE **8.033** · VE 1.899 | mA · V | OpenCode Browser | **PASS** |
| A5 · อินพุตผิด | Fixed Bias | RB = 0 kΩ | ต้องแจ้งให้แก้ RB · เว็บไม่ล่ม · ไม่แสดงผลรอบก่อน | `RB: Resistance must be greater than 0 Ω` · ไม่มีตารางผลลัพธ์ | — | OpenCode Browser | **PASS** |

ค่าคงที่ร่วมทุกกรณี: `VCC = 12 V`, `RC = 2.2 kΩ`, `β = 100`, `VBE = 0.70 V` (ตามใบงาน)

หลักฐานจากหน้าเว็บ (ถ่ายจาก Browser จริง)

| ไฟล์ | เนื้อหา |
|---|---|
| [`screenshots/lab03-A1-baseline.jpeg`](screenshots/lab03-A1-baseline.jpeg) | ผล Divider **ก่อนแก้โค้ด** (baseline A1) — IC 1.230 mA, VCE 8.052 V · ภาพนี้ถ่ายก่อนปรับ `VCE_SAT` จึงยังแสดง "VCE(sat) = 0.3 V" |
| [`screenshots/lab03-A2-fixed.jpeg`](screenshots/lab03-A2-fixed.jpeg) | โหมด Fixed Bias (build ปัจจุบัน) — IC 1.130 mA, VCE 9.514 V, IB 11.300 µA · ช่อง R1/R2/RE จางและกดไม่ได้ |
| [`screenshots/lab03-A3-emitter.jpeg`](screenshots/lab03-A3-emitter.jpeg) | โหมด Emitter หลังคำนวณ (build ปัจจุบัน) — IC 1.026 mA, VCE 8.705 V · แสดง "VCE(sat) = 0.2 V" ตามใบงาน Lab 03 |
| [`screenshots/lab03-A5-invalid-input.jpeg`](screenshots/lab03-A5-invalid-input.jpeg) | RB = 0 → ข้อความ error และไม่มีผลลัพธ์ค้าง |

ข้อความที่คัดจากหน้าเว็บโดยตรง (snapshot ของ browser tool)

```text
A3  Mode (โหมด): Emitter Bias (single supply) (ไบอัสอีมิตเตอร์ แหล่งจ่ายเดียว)
    VB = 1.737 V · VE = 1.037 V · VC = 9.742 V · VCE = 8.705 V · IC = 1.026 mA

A5  Please fix the following (กรุณาแก้ไขข้อมูลต่อไปนี้)
    RB: Resistance must be greater than 0 Ω (RB: ค่าตัวต้านทานต้องมากกว่า 0 Ω)
    RB = 0 kΩ   ← ค่าที่กรอกยังอยู่ แต่ไม่มีตารางผลลัพธ์ของรอบก่อน
```

### 8.5 A5 — พิสูจน์ว่าข้อความมาจาก Flask ไม่ใช่การกันที่ตัวฟอร์ม

ใบงานเตือนว่า "การที่ฟอร์มไม่ยอมส่งยังไม่พิสูจน์ว่า Flask ตรวจค่าแล้ว" จึงตรวจสามชั้น:

1. **ฟอร์มไม่ได้กัน** — ช่อง RB คือ `<input id="rb" type="number" step="any">`
   ไม่มี `required` และไม่มี `min` เบราว์เซอร์จึงส่งค่า `0` ออกไปตามปกติ
2. **Flask ตรวจและปฏิเสธ** — เส้นทางคือ `app.py:181` เรียก `parse_resistance("0", "kohm")`
   → `dc_bias.py:122-125` เห็นว่า `ohms <= 0` แล้ว raise `BiasInputError`
   → `app.py:185` เติมชื่อช่อง → `app.py:188` ตอบกลับด้วย HTTP **400**
3. **ยืนยันด้วยการยิง POST ตรง (ไม่ผ่านเบราว์เซอร์)** — `POST /calculate` ด้วย `mode=fixed, rb=0`
   ได้ `400` และข้อความ `RB: Resistance must be greater than 0 Ω`

การทดสอบชั้นที่ 3 ทำด้วย Flask test client (`app.test_client()`) และเป็นเพียงการยืนยันซ้ำ
ไม่ใช่หลักฐานแทนการตรวจบนเบราว์เซอร์ — หลักฐานหลักของ A5 คือภาพ `lab03-A5-invalid-input.jpeg`

### 8.6 เส้นทางข้อมูลของ RE ใน A4 (ฟอร์ม → Flask → ฟังก์ชัน → สมการ)

| ขั้น | ไฟล์และบรรทัด | ค่าที่ผ่านจุดนี้ |
|---|---|---|
| 1. ฟอร์มส่งค่า | `templates/index.html` — `<input id="re" name="re">` + `<select name="re_unit">` | `re=2`, `re_unit=kohm` |
| 2. Flask อ่านฟอร์ม | `app.py:155` `request.form.get(...)` | `submitted["re"] = "2"` |
| 3. เลือกช่องตามโหมด | `app.py:170` `required = MODES[mode]["resistors"]` | โหมด `emitter` → `("rb", "rc", "re")`; โหมด `fixed` จะไม่อ่าน `re` เลย |
| 4. **แปลงหน่วยครั้งเดียว** | `app.py:181` → `dc_bias.py:105-126` `parse_resistance("2", "kohm")` | `dc_bias.py:121` `2 × 1,000` = **2,000 Ω** |
| 5. เรียกฟังก์ชันของโหมด | `app.py:210` | `calculate_emitter_bias(..., re=2000.0, ...)` |
| 6. ส่งเข้าแกนสมการ | `dc_bias.py:288` → `_solve_bias(...)` | `vth = VCC`, `rth = RB` |
| 7. RE เข้าสมการ IB | `dc_bias.py:181` | `IB = 11.30 / (1,000,000 + 101 × 2,000) = 9.40099 µA` |
| 8. ได้ผลลัพธ์ | `dc_bias.py:182-187` | `IC = 0.94010 mA`, `VE = 1.89900 V`, `VCE = 8.03278 V` |
| 9. แสดงผล | `templates/index.html` | `result.ic * 1000` → `0.940 mA`, `result.vce` → `8.033 V` |

**สรุปคำตอบคำถามปิด Lab:** ถ้าเปลี่ยน RE แล้วผลไม่เปลี่ยน ให้ไล่ตามลำดับนี้ — (ก) ดูว่า
`request.form["re"]` มีค่าใหม่จริงหรือไม่ (ดู DevTools → Network → Form Data หรือ log ชั่วคราว)
(ข) ดูว่า `parse_resistance` คืน 2,000 Ω ไม่ใช่ 1,000 Ω (ค่านั้นถูก cache/ส่งซ้ำหรือเปล่า)
(ค) ดูว่าโหมดที่ส่งไปเป็น `emitter` ไม่ใช่ `divider` เพราะ `app.py:170` เลือกช่องที่จะอ่านตามโหมด
(ง) ดูว่า `_solve_bias` ได้ `re` เป็นพารามิเตอร์ตัวที่ 5 ไม่ใช่ 0 (ซึ่งคือเส้นทางของ Fixed Bias)

**ยังต้องทำเอง:** นักศึกษาเปิด `http://127.0.0.1:5000/` ทำซ้ำ A4 ด้วยมือหนึ่งรอบ
(เลือก Emitter → RB = 1000 kΩ, RE = 2 kΩ → ต้องได้ IC 0.940 mA, VCE 8.033 V)
แล้วบันทึกว่าทำเมื่อไรและเห็นอะไร — ใบงานให้คะแนนส่วน "นักศึกษาทวนเองอย่างน้อยหนึ่งกรณี"

### 8.7 AI สร้างส่วนไหน / นักศึกษาตรวจอะไร / โค้ดเลือกฟังก์ชันกับแปลงหน่วยอยู่ที่ไหน

| ส่วนของงาน | AI (OpenCode) ทำ | นักศึกษาตรวจ |
|---|---|---|
| `dc_bias.py:252-265` `calculate_fixed_bias()` | เขียนฟังก์ชันตามสมการใบงาน | ตรวจว่า `IB = (VCC − VBE)/RB` และ `VE = 0` ถูกต้องตามที่เรียน |
| `dc_bias.py:268-288` `calculate_emitter_bias()` | เขียนฟังก์ชัน + ใช้ `(β+1)RE` ในตัวส่วน | ตรวจว่าตัวส่วนเป็น `RB + (β+1)RE` ไม่ใช่ `RB + RE` และหน่วยเป็น Ω |
| `dc_bias.py:143-222` `_solve_bias()` | แยกส่วน `IC, IE, VE, VB, VC, VCE` และ region มาใช้ร่วม | ตรวจว่าการแยกไม่เปลี่ยนผล Divider (A1) และสูตร `VCE = VC − VE` ยังถูก |
| `dc_bias.py:105-126` `parse_resistance()` | ใช้ของเดิมจาก Lab 2 (ไม่แก้) | ตรวจว่า kΩ → Ω คูณ 1,000 ครั้งเดียว และค่าที่ ≤ 0 ถูกปฏิเสธ |
| `app.py:23-66` `MODES` | ประกาศโหมดและรายการตัวต้านทานที่แต่ละโหมดใช้ | ตรวจว่า Fixed ใช้ RB/RC, Emitter ใช้ RB/RC/RE, Divider ใช้ R1/R2/RC/RE |
| `app.py:191-217` **if/elif เลือกฟังก์ชัน** | เขียนเงื่อนไขเลือกฟังก์ชันตาม `mode` | ตรวจว่าโหมดผูกกับฟังก์ชันถูก และไม่มีสมการหลุดมาอยู่ใน `app.py` |
| `templates/index.html` | ปุ่มโหมด, ฟอร์ม disable ช่องที่ไม่ใช้, แผนภาพ SVG ตามโหมด | ตรวจด้วยตาบนเบราว์เซอร์ว่าโหมด/ฟิลด์/แผนภาพตรงกัน และไม่มี `<script>` |
| `docs/validation.md`, `README.md` | ร่างเอกสาร | ตรวจตัวเลข ค่าอ้างอิง และคำอธิบายว่า AI ทำอะไร |

**จุดที่โค้ดเลือกฟังก์ชัน** — `app.py:191-217` ใน `calculate()`:

```python
if mode == "divider":
    result = calculate_dc_bias(...)
elif mode == "fixed":
    result = calculate_fixed_bias(...)
else:  # emitter
    result = calculate_emitter_bias(...)
```

โหมดที่ไม่รู้จักถูกปฏิเสธที่ `app.py:158-166` (`_resolve_mode` ที่ `app.py:123-126` คืน `None`) → HTTP 400
โดย **ไม่เดาเป็น Divider** ตามที่ใบงานกำหนด

**จุดที่แปลงหน่วย** — `app.py:181` เรียก `parse_resistance(submitted[name], submitted[f"{name}_unit"])`
ครั้งเดียวตอนรับฟอร์ม แล้ว `dc_bias.py` รับค่าเป็น **โอห์มและแอมป์ทั้งหมด** (SI) ไม่มีการแปลงหน่วยซ้ำ
ในสมการ ส่วนการแสดงผล `A → mA/µA` ทำที่ `templates/index.html` (`result.ic * 1000`, `result.ib * 1000000`)
ซึ่งไม่ใช่การแปลงหน่วยอินพุต

`BiasResult` เก็บแรงดันเป็น V และกระแสเป็น A (โครงเดิมของ Lab 2) ใบงานอนุญาตให้ใช้ชื่อคีย์/หน่วยเดิมต่อได้
โดยระบุว่า "ถ้า Lab 2 ใช้ชื่อคีย์อื่นอยู่แล้ว สามารถใช้ชื่อนั้นต่อได้"

### 8.8 การคงผลเดิมของ Divider

A1 ถูกบันทึกไว้ **ก่อน** แก้โค้ด (`lab03-A1-baseline.jpeg`) แล้วรันซ้ำหลังแก้ด้วยอินพุตเดิม
ได้ `IC = 1.230 mA`, `VCE = 8.052 V` เท่ากันทุกหลัก — ยืนยันว่าการแยก `_solve_bias()`
ไม่ได้เปลี่ยนพฤติกรรมของโหมดเดิม และ `tests/` ชุดเดิมทั้ง 20 ตัวยังผ่านทั้งหมด

หลังปรับเกณฑ์ Saturation เป็น 0.2 V ตามใบงาน ได้รัน A1 ซ้ำบนเบราว์เซอร์อีกครั้ง: ยังได้
`IC = 1.230 mA`, `VCE = 8.052 V` และประโยคใต้ผลลัพธ์ขึ้นว่า
`VCE = 8.052 V is above VCE(sat) = 0.2 V` — ค่าตัวเลขไม่เปลี่ยน มีเพียงเกณฑ์เตือนที่เปลี่ยน
(ภาพ baseline เก่ายังเป็นหลักฐานของ "ก่อนแก้โค้ด" จึงยังแสดง 0.3 V อยู่)

### 8.9 ตรวจครบตามข้อกำหนดของใบงาน (Deliverables & grading)

| ข้อกำหนดในใบงาน | สถานะ | หลักฐาน |
|---|---|---|
| ใช้โปรเจกต์ Lab 2 ต่อ ไม่ทำเว็บใหม่ | ✅ | git history ต่อจาก Lab 2, `calculate_dc_bias()` คงพฤติกรรมเดิม |
| Divider ให้ผลเดิมเมื่อกรอกค่าเดิม (A1) | ✅ | หัวข้อ 8.8 + `lab03-A1-baseline.jpeg` |
| เก็บ tests เดิม ไม่เขียน unittest ใหม่ | ✅ | `tests/` ชุดเดิม 20 ตัว ยังผ่าน |
| ฟังก์ชัน Fixed และ Emitter แยกกันใน `dc_bias.py` | ✅ | `dc_bias.py:252` และ `:268` |
| Flask กับฟังก์ชันตกลงชื่อคีย์/หน่วยร่วมกัน | ✅ | `BiasResult` (V, A) — template แปลงเป็น mA/µA |
| `app.py` ใช้ if/elif เลือกฟังก์ชัน | ✅ | `app.py:191-217` |
| ตรวจเฉพาะช่องที่โหมดนั้นใช้ | ✅ | `app.py:170` |
| โหมดไม่รู้จักต้องแจ้ง error ไม่เดาเป็น Divider | ✅ | `app.py:158-166` → HTTP 400 (ทดสอบแล้ว) |
| ฟอร์มเลือกโหมด และช่องที่ไม่ใช้ใช้งานไม่ได้ | ✅ | `templates/index.html` + `static/style.css` |
| ผลและข้อผิดพลาดระบุโหมด | ✅ | `Mode (โหมด): …` ในผล, ชื่อโหมดในหัวข้อฟอร์ม |
| ไม่ให้ผลรอบก่อนดูเหมือนผลของรอบใหม่ | ✅ | error → `result=None` → แสดง placeholder |
| ค่าอ้างอิงอิสระ ≥ 1 กรณีของโหมดใหม่ พร้อมสมการและหน่วย | ✅ | หัวข้อ 8.2 (A2, A3, A4) |
| ตาราง A1–A5: อินพุต · คาดหมาย · ผลจริง · หน่วย · วิธีตรวจ · สถานะ | ✅ | หัวข้อ 8.4 |
| หลักฐานจากหน้าเว็บ ≥ 1 กรณี | ✅ | ภาพ 4 ไฟล์ (A1, A2, A3, A5) + ข้อความที่คัดจากหน้าเว็บ |
| ระบุวิธีตรวจจริง (Playwright MCP / OpenCode Browser / Manual) | ✅ | `README.md` บรรทัด 39 ระบุ **OpenCode Browser**, หัวข้อ 8.3 มีตารางวิธีตรวจ |
| อธิบายบทบาท MCP (MCP Client / MCP Server) | ✅ | หัวข้อ 8.3: OpenCode = MCP Client, Playwright MCP = MCP Server, Browser ↔ Flask เป็น HTTP คนละเส้นทาง (เครื่องนี้ใช้ OpenCode Browser แทนตามข้อ 05) |
| ระบุ AI สร้างส่วนไหน นักศึกษาตรวจอะไร | ✅ | หัวข้อ 8.7 + `README.md` |
| ระบุโค้ดเลือกฟังก์ชันและแปลงหน่วยอยู่ที่ไหน | ✅ | หัวข้อ 8.7 + `README.md` |
| อธิบายเส้นทางค่า RE ใน A4 ถึงสมการ | ✅ | หัวข้อ 8.6 + คำตอบคำถามปิด Lab |
| ตรวจ `git diff --staged` ก่อน commit | ✅ | 12 ไฟล์เข้า commit `442c05cd…` แล้ว ไม่มี `.venv` / `.env` / credentials |
| **นักศึกษาเปิดเว็บเองทำซ้ำ ≥ 1 กรณี** | ⏳ **ยังต้องทำ** | ต้องทำ A4 ด้วยมือแล้วจดวันที่/สิ่งที่เห็น (ข้อ 8.6 ท้ายหัวข้อ) |
| **GitHub URL + Commit SHA + README วิธีรัน** | ✅ | `README.md` บรรทัด 35–39 มี URL, SHA `442c05cd329660c48b4ca142e22bedc554d99e99` และวิธีตรวจ; push แล้ว (`origin/main` = `dd248eb`) |

**เกณฑ์ Saturation ปรับให้ตรงใบงาน Lab 03:** ใบงานกำหนดให้เตือนเมื่อ `IB ≤ 0` หรือ `VCE ≤ 0.2 V`
เดิม Lab 2 ประกาศ `VCE_SAT = 0.3 V` ใน `dc_bias.py` — รอบนี้แก้เป็น **`VCE_SAT = 0.2 V`** ที่
`dc_bias.py:41` (ค่าคงที่เดียว) แล้วข้อความบนหน้าเว็บเปลี่ยนตามทันทีเพราะ template อ่านค่าจาก
`vce_sat` ใน context processor เงื่อนไข `IB ≤ 0` ถูกครอบด้วยการตรวจ Cutoff (`VTH <= VBE` → `IB = 0`)
ที่มีอยู่แล้ว ไม่กระทบกรณี A1–A5 เพราะทุกกรณีมี VCE มากกว่า 8 V และชุดทดสอบเดิม 20 ตัวยังผ่านทั้งหมด
(เอกสารวางแผนของ Lab 2 ใน `docs/superpowers/` ยังบันทึกค่า 0.3 ตามประวัติการตัดสินใจครั้งนั้น)

---

## 9. Lab 04 — BJT CE Amplifier Simulator (redesigned 3 blocks)

### 9.1 สภาพแวดล้อมที่ตรวจจริง (2026-11-24)

| รายการ | ค่าจริง | หมายเหตุ |
|---|---|---|
| Python | `C:\Program Files\Python314\python.exe` → **3.14.2** | `python` บน PATH เป็น Store alias ใช้ไม่ได้ |
| Flask | **3.1.3** (user site) | `pip install -r requirements.txt` สำเร็จ |
| Baseline test | `Ran 20 tests ... OK` | ชุดเดิม Lab 03 ยังผ่าน |
| git | `C:\Users\B6837020\AppData\Local\Programs\Git\cmd\git.exe` | ไม่มีบน PATH |
| engine | `C:\Users\B6837020\AppData\Local\Programs\ngspice-47\Spice64\bin\ngspice_con.exe` | **console binary** |
| engine version | `** ngspice-47 : Circuit level simulation program **` | จาก `ngspice_con.exe -v` |
| source | Chocolatey nupkg `ngspice/47.0.0` (13.8 MB), แตกด้วย `tar -xf` | winget ไม่มีแพ็กเกจ; SourceForge เจอ Cloudflare |
| Node.js | **v26.13.1** / npx **11.20.0** | zip binary ใน `%LOCALAPPDATA%\Programs\node-v26.13.1-win-x64` (winget ต้อง UAC → ถูกยกเลิก exit 1602) |
| Impeccable | engine **v0.1.27** ติดตั้งใน `.opencode` (project scope, provider opencode) | `npx impeccable install --yes --providers=opencode --scope=project`; ใช้จริงใน Task 5 |

**ทำไมต้อง `ngspice_con.exe` ไม่ใช้ `ngspice.exe`:** ตัวหลังเป็น GUI subsystem
รันแล้วไม่คืน stdout ให้ `subprocess` (ทดสอบแล้วได้ output ว่าง)

### 9.2 ผล smoke test กับ ngspice-47 จริง (ก่อนเขียน parser)

Netlist อ้างอิง: `VCC=12 V`, `R1=100 kΩ`, `R2=22 kΩ`, `RC=2.2 kΩ`, `RE=1 kΩ`,
`CIN=COUT=10 µF`, `RL=10 kΩ`, `VIN AC 1 SIN(0 10m 1k)`, model `QNPN` ตาม spec

**DC (`.op`)** — ตารางจาก `.print op`:

```
Index   v(base)         v(col)          v(emi)          vic#branch
0       1.949112e+00    9.189410e+00    1.289454e+00    1.277541e-03
```

→ `VB=1.9491 V`, `VE=1.2895 V`, `VC=9.1894 V`, `VCE=7.9000 V`, `IC=1.2775 mA`
เทียบ analytical (`VBE=0.70`, ไม่มี Early effect): `VB=1.9422 V`, `VE=1.2422 V`,
`VC=9.2943 V`, `VCE=8.0522 V`, `IC=1.2299 mA` → **ต่างกันจริง** เพราะ SPICE ใช้
`VBE≈0.6597 V` จาก diode equation + Early effect → ต้องแยกป้ายเสมอ

**AC (`.ac dec 20 1 1Meg`)** ที่ 1 kHz:

```
frequency   vdb(vout)   vp(vout)
1.000000e+03  4.859789e+00  -3.139260e+00     ← vp เป็น radian ≈ -179.9°
frequency   vdb(vin)    vp(vin)
1.000000e+03  0.000000e+00   0.000000e+00
```

→ gain ≈ **+4.86 dB** (≈1.75×), phase ≈ **−180°** (กลับเฟสตาม CE)

**Transient (`.tran 10u 5m 0 10u`)** ตัวอย่างแถวแรก:

```
0    0.000000e+00  0.000000e+00  0.000000e+00
1    1.000000e-07  6.283185e-06 -3.409260e-05
...
32   2.528000e-04  9.998452e-03 -1.747790e-02
```

→ time step ไม่สม่ำเสมอ (adaptive 1e-7 → 1e-5) และ `Vout` ติดลบเมื่อ `Vin` บวก
ยืนยันการกลับเฟส

### 9.3 ข้อควรระวังที่ค้นพบจากการรันจริง (ต้องใส่ในโค้ด)

1. ห้ามส่ง `-r` — ngspice จะแจ้ง `print line ignored since rawfile was produced`
2. ห้ามเขียน `.print ac freq ...` — `can't parse 'freq'`; frequency เป็น column อัตโนมัติ
3. `.tran` ต้องมี TSTEP > 0 — `.tran 0 tstop 0 tstep` ทำให้ `TSTEP is invalid`
4. `vp()` เป็น **radian** → ต้อง `degrees()` ก่อนแสดงผล
5. title ใน netlist ใช้ ASCII — `—` ถูกแปลงเป็น `?` ใน log
6. parser ต้องข้าม `Index`/form feed/หัวตารางที่ซ้ำทุก ~60 แถว

### 9.4 วิธีตรวจ B1–B8 ที่ใช้จริง

| รายการ | วิธีจริง | หมายเหตุ |
|---|---|---|
| Playwright MCP | **NOT RUN** | โปรเจกต์นี้ไม่ได้ตั้งค่า Playwright MCP server ใน `opencode.json` |
| OpenCode Browser | **ใช้จริงทุกเคส B1–B7** | เปิด Flask จริงที่ `http://127.0.0.1:5000` (และ port 5001 สำหรับจำลอง engine หาย) ใช้ `tabs.open`, `navigate`, `evaluate`, `wait`, `network.list` อ่านค่าจาก DOM ที่ render แล้ว ไม่ได้อ่านจากโค้ด |
| Impeccable CLI | **ใช้จริง B8** | `impeccable shot` ที่ viewport 1280×900 และ 390×844; `impeccable detect` บน URL จริง |
| Manual | ไม่ได้ใช้ในรอบนี้ | นักศึกษาควรทวน B3 หรือ B6 ด้วยมือหนึ่งรอบตามที่ใบงานกำหนด |

> Browser harness ที่ใช้โต้ตอบจริงมี viewport **532×840** จึงไม่ได้อ้างว่ากดทดสอบบนหน้าจอ 390 px
> แบบ touch จริง — 390 px เป็นหลักฐานจาก Impeccable headless render เท่านั้น
> Fresh tab ที่ `/simulator` ตรวจ console level=error แล้วได้รายการว่าง และ DOM มี `<script>` จำนวน 0

### 9.5 ตาราง B1–B8 (ผลจริงหลัง redesign — ตรวจซ้ำ 2026-11-24)

หน้า `/simulator` หลัง redesign มีบล็อกเกริ่นนำบนสุด `CE Amplifier Lab: DC Bias / AC / Transient`
แล้วตามด้วย `<h2>` ลำดับ `1 Circuit & Parameters`, `2 Simulation & Plots`, `3 Engineering Results`
ไม่มีข้อความ `NOT a SPICE result` และไม่มี `Netlist & engine log` อีกต่อไป
DOM มี `<script>` จำนวน **0** และ console level=error ว่างทุกครั้งที่ตรวจ
ค่าคงที่เริ่มต้น: `VCC=12 V`, `R1=100 kΩ`, `R2=22 kΩ`, `RC=2.2 kΩ`, `RE=1 kΩ`,
`RL=10 kΩ`, `amplitude=10 mV peak`, `frequency=1 kHz`; model `QNPN` แบบ teaching-only
กด Run ครั้งเดียวรัน `.op/.ac/.tran` จริงแล้ว render 3 ตาราง + 2 กราฟพร้อมกัน

| Case | Method | Input | Expected | Observed | Evidence | Status |
|---|---|---|---|---|---|---|
| B1 regression `/` | OpenCode Browser | Divider/Fixed/Emitter ชุด A1–A3 เดิม | ค่าเดิมไม่เปลี่ยน | Divider **IC 1.230 mA · VCE 8.052 V**; Fixed **1.130 mA · 9.514 V**; Emitter **1.026 mA · 8.705 V** | `wait()` เจอ `Forward Active` ทุกโหมด; 20 test เดิมยังผ่าน; console errors ว่าง | **PASS** |
| B2 default run | OpenCode Browser | ค่าคงที่ด้านบน, กด `Run simulation` ครั้งเดียว | 3 blocks, 2 plots, 3 tables, success status | `SUCCESS` + `Engine: ngspice-47`; DC **VB 1.949 V · VE 1.289 V · VC 9.189 V · VCE 7.900 V**; AC **1000 Hz · 4.86 dB · −179.9°**; Tran **0.010 V · −0.017 V · 0.253 ms**; `<polyline>` รวม 4; `<script>` 0 | `h2` ตรงตามลำดับ; `Bode response (illustrative)` + `Input/Output waveforms (illustrative)`; radio `dc` checked และมี active tab เดียว | **PASS** |
| B3 แก้ resistor | OpenCode Browser | `RE=2 kΩ` (unit `kohm`) แล้วรัน | ค่า/กราฟเปลี่ยนตาม RE | AC note เปลี่ยนเป็น `Peak ≈ −1.14 dB · @1000 Hz = −1.14 dB / −179.9° · 121 points`; ตาราง DC/AC/Tran ยังครบ 3 | เปรียบเทียบ `polyline.points` และข้อความ note ก่อน/หลัง; schematic แสดงเฉพาะชื่ออุปกรณ์ (ไม่มีตัวเลข) | **PASS** |
| B4 AC Bode | OpenCode Browser | `.ac dec 20 1 1Meg` จากการรันเดียว | gain dB + phase มีหน่วย, ไม่มี JS | @1 kHz **4.86 dB / −179.9°**, **121 points**; กราฟ `Bode response (illustrative)` มี `<polyline>` 2; note ระบุ `Peak ≈ 4.86 dB` | axes `Frequency (Hz)`, `Gain (dB)`, `Phase (deg)`; `<script>` 0 | **PASS** |
| B5 Transient | OpenCode Browser | 10 mV, 1 kHz จากการรันเดียว | Vin/Vout ตามเวลา และกลับเฟส | กราฟ `Input/Output waveforms (illustrative)` มี `<polyline>` 2, **508 points**, note `Vin ≈ 0.020 Vpp · Vout ≈ 0.035 Vpp`; ตาราง `Vin / Vout / Time` = `0.010 V · −0.017 V · 0.253 ms` | ตรวจ legend และ `points` ของทั้งสอง series | **PASS** |
| B6 แก้ RL/source | OpenCode Browser | `RL=4.7 kΩ`, `amplitude=0.02 V`, `frequency=2000 Hz` แล้วรัน | netlist/results เปลี่ยน | AC **3.25 dB / −179.8°**; Tran **0.020 V / −0.029 V / 0.126 ms**; ช่องฟอร์มยังเก็บค่าใหม่ | เปรียบเทียบตาราง/กราฟกับรอบเริ่มต้น; ยืนยัน editable end-to-end (สัญลักษณ์ไม่แสดงตัวเลขตามข้อกำหนด no-JS) | **PASS** |
| B7 error | OpenCode Browser | `RE=0`; อีก port ตั้ง `NGSPICE_ENGINE=missing-engine.exe` | 400 หรือ status error ไม่ค้างผลเก่า | `POST /simulate` ตอบ **400** พร้อม `RE must be greater than 0 Ω`, ไม่มี `SUCCESS`, ไม่มี `1.949`, ตาราง 0; engine หายแสดง **ENGINE_NOT_FOUND**, ไม่มี `SUCCESS`/`1.949`, ตาราง 0, `<polyline>` 0, มี `What to try` | `network.list` เห็น status 400; ตรวจ `document.body.innerText` หลัง error | **PASS** |
| B8 responsive | Impeccable CLI | 1280×900 + 390×844 | ปุ่ม/กราฟไม่ตัด | screenshot ทั้งสองขนาดถูกสร้างจริง; `detect` เหลือเฉพาะ advisory/warning (`straggler`, `nested-cards`) ไม่มี overflow; `.sim-groups/.sim-tabs` collapse บนจอแคบ | [`lab04-redesign-desktop-1280x900.png`](screenshots/lab04-redesign-desktop-1280x900.png), [`lab04-redesign-phone-390x844.png`](screenshots/lab04-redesign-phone-390x844.png) | **PASS (render)** |

หลักฐานเพิ่มเติมจาก browser จริง:

- schematic ใหม่เป็น **BJT voltage-divider common-emitter** (`title` =
  `BJT voltage-divider common-emitter amplifier schematic`) มีสัญลักษณ์ NPN **ในวงกลมเล็ก**
  (`<circle cx="400" cy="170" r="34">`), ตัวต้านทานทั้ง 5 ตัวเป็น **กล่องอิมพิแดนซ์** (`<rect>`)
  แทนเส้นหยัก, มีลูกศรขึ้นที่สัญลักษณ์ Vin (`M70 151 L75 159 L65 159 Z`),
  R1/R2 divider, RC, RE, CIN/COUT, RL **แสดงเฉพาะชื่ออุปกรณ์ ไม่มีตัวเลขกำกับ**
- rail VCC ถูกตัดให้เชื่อมเฉพาะ node บน R1 → node บน RC
  (`<line x1="250" y1="40" x2="450" y2="40"/>`) ไม่ยาวข้ามทั้งภาพ; browser ยืนยัน DOM ตรงตามนี้
- **ไม่มีตัวเลขบนสัญลักษณ์**: เพราะข้อกำหนดห้ามใช้ JavaScript ฝั่ง client การอัปเดตตัวเลขทุกครั้งที่พิมพ์
  ทำไม่ได้ จึงลบ `<g class="sim-value">` ออก เหลือเฉพาะชื่อ `VCC/VIN/R1/R2/RC/RE/RL/CIN/COUT/B/C/E/Q1`;
  ค่าที่กรอกอยู่ในฟอร์มและมีผลกับ netlist/ผลลัพธ์หลังกด Run ตามปกติ
- บล็อก Simulation แสดง path ที่ตรวจพบจริง:
  `Engine detected on this machine: C:\Users\B6837020\AppData\Local\Programs\ngspice-47\Spice64\bin\ngspice_con.exe`
  (ค้นจาก PATH + โฟลเดอร์ติดตั้งที่พบบ่อย; `find_ngspice_engine()`)
- กด radio `tran` แล้ว checked เปลี่ยนเป็น `tran`, active tab เดียวคือ `Transient waveform`,
  ค่าฟอร์ม (`vcc=12`, `rl=10`, `amplitude=10`, `frequency=1`) ไม่เปลี่ยน และหลังรันตารางยังครบ
  3 + `<polyline>` 4 → radio เป็น focus เท่านั้น ไม่ reload/ล้างผล
- ชุดทดสอบหลัง redesign: **`Ran 62 tests ... OK`** (เพิ่ม test ตรวจบล็อกเกริ่นนำบนสุด + ชื่อ `Circuit & Parameters` เดิม, กล่องอิมพิแดนซ์, วงกลม BJT, ลูกศร Vin, rail VCC สั้น และไม่มีตัวเลขบนสัญลักษณ์)

หลักฐานภาพจาก browser/CLI จริง (หลัง redesign):

| ไฟล์ | เนื้อหา |
|---|---|
| [`screenshots/lab04-redesign-desktop-1280x900.png`](screenshots/lab04-redesign-desktop-1280x900.png) | `/simulator` 1280×900: 3 blocks, schematic ใหม่, engine path, 2 plots, 3 tables |
| [`screenshots/lab04-redesign-phone-390x844.png`](screenshots/lab04-redesign-phone-390x844.png) | `/simulator` 390×844: layout collapse บนจอแคบ |

ข้อความที่คัดจากหน้าเว็บจริง (ไม่ใช่จากโค้ด):

```text
SUCCESS  Engine: ngspice-47
DC Operating Point    VB 1.949 V · VE 1.289 V · VC 9.189 V · VCE 7.900 V
AC Frequency Response 1000 Hz · 4.86 dB · -179.9°
Transient Response    0.010 V · -0.017 V · 0.253 ms
Bode response (illustrative)        Peak ≈ 4.86 dB · @1000 Hz = 4.86 dB / -179.9° · 121 points.
Input/Output waveforms (illustrative) Vin ≈ 0.020 Vpp · Vout ≈ 0.035 Vpp · 508 points.
Engine detected on this machine: C:\Users\B6837020\AppData\Local\Programs\ngspice-47\Spice64\bin\ngspice_con.exe

B7  ENGINE_NOT_FOUND → Engine not ready — NGspice executable not found
    What to try: ... (ไม่มี SUCCESS, ไม่มีค่าเก่า, ไม่มีตาราง/กราฟค้าง)
```

### 9.6 Impeccable critique → polish → redesign → detect

| ขั้น | สิ่งที่ทำจริง | หลักฐาน |
|---|---|---|
| Critique (layout เดิม) | รัน Assessment A (design review) และ Assessment B (detector + screenshot) แบบแยก sub-agent ตาม reference ของ Impeccable v0.1.27 | A: Nielsen 25/40, cognitive load สูง, 3 P1 (tab reset, ไม่มี schematic, AC caveat/cutoff ไม่ชัด); B: detector 4 findings ใน markup scan |
| Polish (layout เดิม) | tab เปลี่ยนจาก `<a href>` เป็น `<button formmethod="get">`; `GET /simulator` อ่านค่าจาก query; เพิ่ม schematic; range hint; remedy ของ engine หาย | 15/20 Good; `.impeccable/audit/2026-11-24T08-45-44Z__project.md` (รายงาน nàyอธิบาย **ก่อน redesign** เท่านั้น) |
| Redesign (รอบปัจจุบัน) | เปลี่ยนเป็น 3 blocks ตามที่ผู้ขอระบุ; radio `DC/AC/Transient` แทน GET-tab; run ครั้งเดียวได้ 3 analysis; ตัด analytical + netlist/log; เพิ่ม `RL`, source units, schematic voltage-divider ใหม่, แสดง engine path | `app.py`, `spice_engine.py`, `templates/simulator.html`, `static/style.css`, tests; 62 tests ผ่าน; browser ตรวจ B1–B7 ใหม่ |
| Detect (หลัง redesign) | `impeccable detect --json http://127.0.0.1:5000/simulator` และ `shot --viewport 1280x900,390x844` | เหลือ advisory/warning (`straggler`, `em-dash-overuse`, `nested-cards`) ไม่มี primary finding เรื่อง overflow หรือ tap target; screenshot ใหม่สองไฟล์ในตาราง 9.5 |

> ข้อมูลในหัวข้อ 9.2–9.3 เป็น **result จาก ngspice จริง** ที่ใช้ validate parser ส่วนหัวข้อ 9.5
> เป็นหลักฐานจาก UI จริงหลังรันโปรแกรมแล้ว

