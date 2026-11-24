# BJT DC Bias Web App — Lab 03 + Lab 04 CE Amplifier Simulator

เครื่องคำนวณ **DC Bias** ของทรานซิสเตอร์ BJT แบบ Common Emitter **สามวงจรไบอัส**
ป้อนที่ขา Base (Lab 03) และ **เครื่องจำลองขยายสัญญาณ CE ด้วย ngspice จริง** (Lab 04)
รายวิชา ENG29 2121 Electronics Laboratory
(ต่อยอดจาก Lab 02 ที่มีเฉพาะวงจรแบ่งแรงดัน)

| โหมด | อินพุตตัวต้านทาน | สมการกระแส Base |
|---|---|---|
| **Fixed Bias** | RB, RC | `IB = (VCC − VBE) / RB` |
| **Emitter Bias** (แหล่งจ่ายเดียว) | RB, RC, RE | `IB = (VCC − VBE) / [RB + (β+1)·RE]` |
| **Voltage Divider Bias** | R1, R2, RC, RE | `IB = (VTH − VBE) / [RTH + (β+1)·RE]` |

กดปุ่มโหมด (Fixed Bias / Emitter Bias / Voltage Divider Bias) ครั้งเดียว — แผนภาพและฟอร์ม
จะเปลี่ยนตามทันที ฟอร์มแสดงครบทุกช่องแต่ช่องที่โหมดนั้นไม่ใช้จะจางและกดไม่ได้
กรอกค่าแล้วกด **Calculate DC Bias (คำนวณ DC Bias)** หน้าเว็บจะคำนวณ
`VB, VE, VC, VCE, IC, IB, IE` **ด้วย Python ฝั่ง server** แล้วส่ง HTML
ที่คำนวณเสร็จแล้วกลับมาให้ Browser — ไม่มี JavaScript ฝั่ง client และไม่มีค่าที่ฮาร์ดโค้ดไว้ในหน้าเว็บ

หน้าเว็บแสดงเพิ่มเติม:

- แผนภาพวงจร (SVG) ที่เปลี่ยนตามโหมด และเติมค่าอุปกรณ์กับแรงดันที่ node ตามผลคำนวณจริง
- สถานะการทำงานของทรานซิสเตอร์: **Forward Active / Cutoff / Saturation**
- ข้อความยืนยัน **Active Region Approximation OK** เมื่อทรานซิสเตอร์อยู่ในช่วงขยาย
- คำเตือนเมื่อแบบจำลอง Forward-Active ใช้ไม่ได้
- ข้อความ error ที่ระบุชื่อช่องเมื่ออินพุตผิด (เช่น `RB = 0`) และไม่ค้างผลลัพธ์รอบก่อนไว้
- เลือกหน่วยความต้านทานได้ 3 หน่วย: `Ω`, `kΩ`, `MΩ` (1 MΩ = 1,000 kΩ) — ค่าที่เลือกจะแสดงบนแผนภาพ SVG ด้วย

> ⚠️ **ข้อจำกัดของแบบจำลอง:** นี่คือ **Forward-Active approximation** (β คงที่, VBE คงที่,
> ไม่คิด Early effect) **ไม่ใช่ผลจาก SPICE** และไม่ใช่ผลจากการวัดจริง
> เมื่อทรานซิสเตอร์อยู่นอกช่วงขยาย ค่าที่แสดงเป็นเพียงการประมาณเพื่อการสอน — อย่าใช้ตัดสินใจทางวิศวกรรม

---

## ลิงก์ส่งงาน (Lab 03)

| รายการ | ค่า |
|---|---|
| GitHub repository | <https://github.com/siriphailin/BJT-DC-Bias-Web-App> |
| Commit SHA ของ Lab 03 | `442c05cd329660c48b4ca142e22bedc554d99e99` |
| วิธีตรวจผลจริง | **OpenCode Browser** |

---

## การรัน (Run)

```bash
python -m flask --app app run --debug
```

แล้วเปิด Browser:

- Lab 03 DC Bias: **<http://127.0.0.1:5000/>**
- Lab 04 CE Amplifier Simulator: **<http://127.0.0.1:5000/simulator>**

Lab 04 ต้องการ `ngspice_con.exe` (console build) เท่านั้น — `ngspice.exe` แบบ GUI ไม่คืน
output ให้ subprocess โปรแกรมจะหาเองที่ `%LOCALAPPDATA%\Programs\ngspice-47\Spice64\bin\ngspice_con.exe`
หรือกำหนด path เองด้วยตัวแปรสภาพแวดล้อม `NGSPICE_ENGINE` (ถ้าตั้งค่าผิดจะแสดง
`ENGINE_NOT_FOUND` พร้อมวิธีแก้ แทนการใช้ผลเก่าหรือผลปลอม)

ถ้าไม่ได้ activate venv ให้ใช้:

```powershell
.venv\Scripts\python.exe -m flask --app app run --debug
```

---

## การทดสอบ (Tests)

```bash
python -m unittest discover -s tests -v
```

ผลที่ต้องได้: **`Ran 62 tests` … `OK`** (20 เดิมของ Lab 03 + 42 ของ Lab 04)

ชุดทดสอบแบ่งเป็นสี่ชั้น

| ไฟล์ | จำนวน | ตรวจอะไร |
|---|---|---|
| `tests/test_dc_bias.py` | 14 | สมการ, การแปลงหน่วย, การปฏิเสธค่าผิด, การแบ่ง Region และ warning |
| `tests/test_web.py` | 6 | Flask route เดิม: `GET /` 200, `POST /calculate` 200/400, ค่าที่คำนวณขึ้นหน้าเว็บ |
| `tests/test_spice_engine.py` | 28 | validation (รวม RL และหน่วยของ Source), netlist, parser, error status, ngspice จริง, SVG |
| `tests/test_simulator_web.py` | 14 | `/simulator`, `/simulate`, ไม่มี JS, 3 radio, ชื่อบล็อกใหม่, schematic กล่องอิมพิแดนซ์+วงกลม BJT+ลูกศร Vin+rail สั้น+ไม่มีตัวเลข, success/error render, กราฟ/ตารางครบ, end-to-end จริง |

> ชุดทดสอบ SPICE ที่เรียก engine จริงจะ `skip` อัตโนมัติถ้าไม่พบ `ngspice_con.exe` ตำแหน่งด้านบน

Impeccable v0.1.27 เป็นเครื่องมือพัฒนา UI (ไม่ใช่ runtime dependency) ติดตั้งแบบ project-scope
ใน `.opencode/`; เรียกผ่าน `.opencode\skills\impeccable\scripts\impeccable.cmd`
รายงาน audit หลัง polish ของ layout ก่อนหน้าอยู่ใน
`.impeccable/audit/2026-11-24T08-45-44Z__project.md`; หลัง redesign รัน `detect` บน URL จริงอีกครั้ง
เหลือเฉพาะ advisory/warning (straggler, em-dash, nested-cards) ไม่มี findings เรื่อง overflow
(ถ้าไม่ต้องการเก็บเครื่องมือนี้ใน repo ให้มนุษย์เพิ่ม `.opencode/` และ `.impeccable/` ลง `.gitignore`)

---

## ผลตรวจบน Browser — A1–A5 (Lab 03)

ตรวจด้วย **OpenCode Browser** เปิด `http://127.0.0.1:5000/` จริง: กดปุ่มโหมด กรอกฟอร์ม
กด Calculate แล้วอ่านค่าจากหน้าเว็บ (ไม่ได้อ่านจากโค้ด)
เกณฑ์: `|ΔIC| ≤ 0.01 mA` และ `|ΔVCE| ≤ 0.02 V` เทียบกับค่าอ้างอิงที่ยังไม่ปัด
ค่าคงที่ร่วม: `VCC = 12 V`, `RC = 2.2 kΩ`, `β = 100`, `VBE = 0.70 V`

| กรณี | โหมด | อินพุต | ค่าคาดหมาย (คำนวณมือ) | ผลจริง | หน่วย | วิธีตรวจ | สถานะ |
|---|---|---|---|---|---|---|---|
| A1 | Divider | R1=100 kΩ, R2=22 kΩ, RE=1 kΩ | IC 1.2299 · VCE 8.0522 | IC **1.230** · VCE **8.052** | mA · V | OpenCode Browser | **PASS** |
| A2 | Fixed | RB=1 MΩ | IC 1.1300 · VCE 9.5140 | IC **1.130** · VCE **9.514** | mA · V | OpenCode Browser | **PASS** |
| A3 | Emitter | RB=1 MΩ, RE=1 kΩ | IC 1.02634 · VCE 8.70545 | IC **1.026** · VCE **8.705** | mA · V | OpenCode Browser | **PASS** |
| A4 | Emitter | RB=1 MΩ, RE=2 kΩ (เปลี่ยนค่าเดียว) | IC **ลดลง** → 0.94010 · VCE 8.03278 | IC **0.940** · VCE **8.033** | mA · V | OpenCode Browser | **PASS** |
| A5 | Fixed | RB=0 | ต้องแจ้งให้แก้ RB และไม่ค้างผลเดิม | `RB: Resistance must be greater than 0 Ω` | — | OpenCode Browser | **PASS** |

สมการ ค่าอ้างอิง ชุดค่าตัวอย่างจากใบงาน คำตอบ A5 และเส้นทางข้อมูล RE อยู่ใน
[`docs/validation.md`](docs/validation.md) (หัวข้อ 8)
ภาพหน้าจอ 4 ไฟล์: [`docs/screenshots/`](docs/screenshots/) — `lab03-A1-baseline.jpeg`,
`lab03-A2-fixed.jpeg`, `lab03-A3-emitter.jpeg`, `lab03-A5-invalid-input.jpeg`

---

## Lab 04 — CE Amplifier Simulator

หน้า `/simulator` ใช้ **ngspice-47 จริง** กับวงจร voltage-divider bias วงจรเดียว
(CIN/COUT = 10 µF, RL แก้ได้) และมี **บล็อกเกริ่นนำอยู่บนสุด**
`CE Amplifier Lab: DC Bias / AC / Transient` ตามด้วย 3 บล็อกตามลำดับ:

1. **Circuit & Parameters** — schematic SVG ของ
   **BJT voltage-divider common-emitter** (สัญลักษณ์ NPN ในวงกลมเล็ก, ตัวต้านทานเป็น
   **กล่องอิมพิแดนซ์**, มีลูกศรที่ Vin, R1/R2 divider, RC, RE, CIN/COUT, RL;
   rail VCC สั้นจาก R1 ถึง RC) **แสดงเฉพาะชื่ออุปกรณ์ ไม่มีตัวเลขกำกับ**
   (ทำ live update ทุกครั้งที่พิมพ์ไม่ได้เพราะห้ามใช้ JS ฝั่ง client) + ช่องแก้ `Vcc`, `RC`,
   `R1`, `R2`, `RE`, `RL`, `Source` พร้อมตัวเลือกหน่วย (Ω/kΩ/MΩ, mV/V, Hz/kHz/MHz)
   และปุ่ม Run simulation
2. **Simulation & Plots** — radio `DC` / `AC` / `Transient`, กราฟ
   `Bode response (illustrative)` และ `Input/Output waveforms (illustrative)`
3. **Engineering Results** — `DC Operating Point` (VB · VE · VC · VCE),
   `AC Frequency Response` (Gain / Phase / Frequency), `Transient Response` (Vin / Vout / Time)

กด Run ครั้งเดียวแล้ว Flask รันทั้งสอง analysis จริงใน temp dir แล้ว render ทุกกราฟ/ตารางพร้อมกัน
radio เป็นตัวเลือก "focus" เท่านั้น จึงสลับได้โดยไม่ reload หรือล้างผลที่แสดงอยู่

| Analysis | คำสั่งจริงใน netlist | ผลที่ render |
|---|---|---|
| DC | `.op` + `.print op` | VB, VE, VC, VCE จากตาราง log จริง |
| AC | `.ac dec 20 1 1Meg` | Bode gain (dB) + phase (°) จาก `.print ac` |
| Transient | `.tran` + `.print tran` | Vin/Vout vs time (ms) จาก `.print tran` |

- หน้า redesigned **ไม่มี** ส่วน analytical reference หรือ netlist/engine log อีกต่อไป
  (ตามคำขอ) — ค่าที่เหลือมาจาก ngspice เท่านั้น
- กราฟเป็น **SVG ที่ Python สร้างจากจุดข้อมูล SPICE จริง** คำว่า "illustrative" หมายถึง
  รูปแบบสำหรับการสอน ไม่ใช่เส้นที่แต่งขึ้น และไม่มี `<script>` ในหน้า
- Amplitude/Frequency กำหนดแหล่ง sine สำหรับ Transient; DC ไม่ใช้ และ AC ใช้ drive 1 V คงที่
  ในช่วง 1 Hz–1 MHz
- หน้าแสดง **path ของ `ngspice_con.exe` ที่ตรวจพบในเครื่อง** (ค้นหาจาก PATH และโฟลเดอร์
  ติดตั้งที่พบบ่อย เช่น `%LOCALAPPDATA%\Programs\ngspice-*\Spice64\bin`) ที่บล็อก Simulation
  → ไม่ต้องเดาว่า engine อยู่ที่ไหน; override ได้ด้วย `NGSPICE_ENGINE` (รวมตั้งค่าผิดเพื่อทดสอบ
  `ENGINE_NOT_FOUND`)
- ถ้า `RE=0` หรือ `RL=0` → HTTP 400; ถ้า engine หาย → `ENGINE_NOT_FOUND` + วิธีแก้
  **ไม่แสดงผลเก่าค้าง**

**สมมติฐานของโมเดล (สำคัญ):** `QNPN` คือโมเดลสำหรับการสอน
`BF=100 IS=1E-14 VAF=100 RB=0 CJE=CJC=TF=TR=0` ไม่ใช่ part number ของทรานซิสเตอร์จริง
และกราฟ AC ส่วนใหญ่สะท้อนตัวเก็บประจุคู่จ่าย ไม่ใช่ capacitance ภายในทรานซิสเตอร์

ผลตรวจ B1–B8 หลัง redesign ด้วย OpenCode Browser และ Impeccable CLI อยู่ใน
[`docs/validation.md`](docs/validation.md) (หัวข้อ 9) ภาพหน้าจอใหม่คือ
`docs/screenshots/lab04-redesign-desktop-1280x900.png` และ
`lab04-redesign-phone-390x844.png`

## โครงสร้างไฟล์

```
BJT DC Bias Web App/
├── app.py                  # Lab 03: GET /, POST /calculate | Lab 04: GET /simulator, POST /simulate
├── dc_bias.py              # สมการ DC Bias ทั้งสามโหมด (ไม่ import Flask)
├── spice_engine.py         # validate → netlist → ngspice → parser → SVG (ไม่ import Flask)
├── templates/index.html    # Lab 03 UI (แก้เพียงเพิ่มลิงก์ไป /simulator)
├── templates/simulator.html# Lab 04 UI: 3 blocks, schematic, unit selects, 2 plots, 3 tables
├── static/style.css        # Lab 03 styles + .sim-* styles
├── tests/                  # unittest 62 ตัว (20 เดิม + 42 ของ Lab 04)
├── docs/                   # design-note, validation, screenshots, spec/plan
├── requirements.txt
├── AGENTS.md               # conventions สำหรับ AI coding agent
└── .opencode/              # Impeccable แบบ project-scope (มนุษย์ตัดสินใจ commit หรือ ignore)
```

**หลักการสำคัญ:** `app.py` ไม่มีสมการ DC bias แม้บรรทัดเดียว — มันอ่านค่าจากฟอร์ม แปลงหน่วย
เลือกฟังก์ชันตาม `mode` แล้วเรียกฟังก์ชันใน `dc_bias.py`; ส่วน Lab 04 ส่งค่าที่ validate แล้วให้
`spice_engine.py` เป็นคนสร้าง netlist, เรียก ngspice, parse และ render SVG
ห้ามฮาร์ดโค้ดผล SPICE หรือกราฟใน template


