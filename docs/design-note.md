# Design Note — BJT DC Bias Web App + Lab 04 CE Amplifier Simulator

เอกสารสรุปการตัดสินใจออกแบบ สำหรับ Lab 02/03/04 (ENG29 2121)
รายละเอียดเต็มอยู่ใน [`superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md`](superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md)
และ [`superpowers/specs/2026-11-24-lab04-bjt-amplifier-simulator-design.md`](superpowers/specs/2026-11-24-lab04-bjt-amplifier-simulator-design.md)

## ปัญหาที่ต้องแก้

ใบงานต้องการเว็บแอปที่ "กรอกค่า → ได้ผล DC Bias" โดยผลลัพธ์ **ต้องคำนวณด้วย Python
ฝั่ง backend** ไม่ใช่คำนวณใน Browser และต้องมี Automated Tests กับ GitHub commit
ข้อจำกัดสำคัญคือเวลา (คาบ 3 ชั่วโมง) และห้ามใช้ JavaScript ฝั่ง client

## ทางเลือกที่พิจารณา

| | วิธี | ข้อดี | ข้อเสีย | สรุป |
|---|---|---|---|---|
| **A** | Server-rendered POST + Jinja | ตรงกับ data flow ในใบงาน, ไม่มี JS, ทดสอบด้วย Flask test client ได้ตรง ๆ | หน้า reload ทุกครั้งที่กดคำนวณ | **เลือก** |
| B | JSON API + `fetch` | ตอบสนองไว ต่อยอดเป็น knob แบบ real-time ได้ | ต้องเขียนโค้ดสองฝั่ง เสี่ยงไม่ทันคาบ | ไม่เลือก (เป็นทางต่อยอดในสัปดาห์ถัดไป) |
| C | HTMX partial swap | ไม่ reload ทั้งหน้า | เพิ่ม dependency นอกหลักสูตร | ไม่เลือก |

**ทำไมเลือก A:** เกณฑ์ประเมิน A1–A7 วัดที่ Flask route และ test client ทั้งหมด
และใบงานระบุชัดว่าให้ Browser ได้ "HTML response rendered" — วิธี A จึงเป็นเส้นทางสั้นที่สุด
ที่ผ่านทุกข้อ และยังทดสอบได้ด้วย `unittest` ล้วนโดยไม่ต้องมี Browser ในเทสต์

## ทำไมแยก `dc_bias.py` ออกจาก `app.py`

นี่คือการตัดสินใจที่สำคัญที่สุดของโปรเจกต์

```
dc_bias.py   ← สมการวิศวกรรมล้วน (pure function) — ไม่รู้จัก Flask, HTML, HTTP
app.py       ← presentation: อ่านฟอร์ม → แปลงหน่วย → เรียก dc_bias → render
index.html   ← แสดงผลเท่านั้น ไม่มีสมการ
```

เหตุผล:

1. **ทดสอบได้โดยไม่ต้องมีเว็บ** — `test_dc_bias.py` เรียกฟังก์ชันตรง ๆ ตรวจค่าตัวเลข
   ได้ในระดับ 1e-9 โดยไม่ต้องสร้าง HTTP request
2. **ตรวจความถูกต้องได้ง่าย** — สมการอยู่ที่เดียว อ่านจบในไฟล์เดียว ไม่ต้องไล่ทั้งโปรเจกต์
3. **เปลี่ยนหน้าเว็บได้โดยไม่เสี่ยงพังสมการ** — ถ้าอนาคตเปลี่ยนไปใช้ JSON API (ทางเลือก B)
   หรือ HTMX (ทางเลือก C) สมการไม่ต้องแก้แม้บรรทัดเดียว
4. **แยก logic กับ presentation ชัดเจน** — template ไม่มีสมการอยู่เลย จึงแก้สมการที่
   `dc_bias.py` ได้โดยไม่ต้องแตะ HTML

## Data flow

```
Browser                    Flask (app.py)                 dc_bias.py
   │                            │                              │
   │  GET /                     │                              │
   │───────────────────────────>│  render index.html (ฟอร์มว่าง)│
   │<───────────────────────────│                              │
   │                            │                              │
   │  POST /calculate           │                              │
   │  vcc=12, r1=100,           │                              │
   │  r1_unit=kohm, ...         │                              │
   │───────────────────────────>│                              │
   │                            │  parse_resistance("100","kohm")│
   │                            │─────────────────────────────>│
   │                            │<───────────── 100000.0 Ω ────│
   │                            │                              │
   │                            │  calculate_dc_bias(...)      │
   │                            │─────────────────────────────>│
   │                            │<── BiasResult(vb, ve, vc,    │
   │                            │     vce, ic, ib, ie, region, │
   │                            │     warnings, ...) ──────────│
   │                            │                              │
   │  HTML ที่มีผลลัพธ์แล้ว      │  render index.html           │
   │<───────────────────────────│  (Jinja เติมตัวเลข + SVG)     │
```

จุดสำคัญ: **ไม่มีขั้นตอนใดที่ Browser คำนวณ** — ตัวเลขทุกตัวที่เห็นใน HTML ถูกใส่โดย Jinja
จาก object `BiasResult` ที่ Python สร้างขึ้น

## การจัดการ error

- ค่าที่ผิด (R = 0, ค่าติดลบ, ข้อความที่ไม่ใช่ตัวเลข, VBE นอกช่วง 0–1) ถูกปฏิเสธใน `dc_bias.py`
  ด้วย `BiasInputError` ที่มีข้อความสองภาษาและระบุชื่อช่อง
- `app.py` เก็บ error ทุกข้อไว้ใน list เดียว แล้ว render ฟอร์มใหม่พร้อม **HTTP 400**
  โดยคงค่าที่ผู้ใช้กรอกไว้ทั้งหมด (ไม่ต้องพิมพ์ใหม่) — ไม่มี `500` สำหรับ input ที่ผิด
- เก็บ error ทุกข้อพร้อมกัน ไม่หยุดที่ข้อแรก ผู้ใช้จึงแก้ทีเดียวได้ครบ

## การแบ่ง Region และ Warning

มี 2 สถานะเตือนเท่านั้น ตามที่ใบงานกำหนด:

| สถานะ | เงื่อนไข | ผลลัพธ์ |
|---|---|---|
| Cutoff | `VTH <= VBE` | `IB = IC = IE = 0`, เตือนว่าแบบจำลองใช้ไม่ได้ |
| Saturation | `VCE < 0.2 V` | เตือนว่าแบบจำลอง Forward-Active ใช้ไม่ได้ |
| Active | นอกเหนือจากสองกรณีข้างต้น | แสดง **Active Region Approximation OK** |

ในกรณี Saturation โปรแกรม **ไม่ clamp** ค่า VCE ให้เป็น 0.2 V แต่ปล่อยค่าดิบจากสมการไว้
(อาจติดลบ) แล้วติด warning — เพราะการ clamp จะทำให้ดูเหมือน "คำนวณถูก" ทั้งที่แบบจำลอง
ใช้ไม่ได้จริง การปล่อยค่าดิบพร้อมคำเตือนจึงสื่อข้อจำกัดได้ตรงกว่า

---

## Lab 04 — เพิ่ม CE Amplifier Simulator โดยไม่แตะ Lab 03

### ปัญหาและข้อจำกัด

Lab 04 ต้องการผล `.op/.ac/.tran` จาก ngspice จริง ไม่ใช่กราฟตัวอย่างหรือค่าคงที่ใน template
แต่ต้องคง `GET /` และ `POST /calculate` ของ Lab 03 ไว้ทุกประการ, ห้ามเพิ่ม dependency ใหม่
และห้ามใช้ JavaScript ฝั่ง client ภายหลังผู้ขอให้ redesign เป็น 3 บล็อก, ให้ตัดส่วน analytical
reference และ netlist/engine log ออกจากหน้า และให้แก้ `RL` พร้อมหน่วยของ Source ได้

### การตัดสินใจหลัก

| ประเด็น | ทางเลือก | เหตุผล |
|---|---|---|
| Route | เพิ่ม `GET /simulator` และ `POST /simulate` ต่อท้าย `app.py` | Lab 03 ไม่ถูกแตะแม้บรรทัดเดียว; แยก footer/link เท่านั้น |
| ชั้น engine | `spice_engine.py` เป็น pure adapter ไม่ `import flask` | ทดสอบ parser/netlist ได้โดยไม่สร้าง HTTP; ทำให้ขอบเขตชัด |
| Engine binary | `ngspice_con.exe` เท่านั้น | `ngspice.exe` เป็น GUI subsystem ไม่คืน stdout ให้ subprocess |
| หา engine | `find_ngspice_engine()` ค้นจาก PATH + `%LOCALAPPDATA%`/Program Files (`ngspice*/Spice64/bin`) แล้วโชว์ path บนหน้าเว็บ | ผู้ใช้ไม่ต้องเดาว่า engine อยู่ที่ไหน; บล็อก Simulation แสดง path ที่ตรวจพบจริง ส่วน `NGSPICE_ENGINE` ยัง override ได้ (รวมตั้งค่าผิดเพื่อทดสอบ error) |
| การรัน | temp dir ต่อหนึ่ง request, ไม่ส่ง `-r` | ป้องกัน stale file และ `-r` ทำให้ ngspice-47 ข้าม `.print` |
| บล็อกเกริ่นนำ + 3 บล็อก | `CE Amplifier Lab: DC Bias / AC / Transient` (บนสุด) → `Circuit & Parameters` → `Simulation & Plots` → `Engineering Results` | ตามโครงที่ผู้ขอระบุ (เพิ่มหัวข้อเกริ่นนำด้านบนแล้วคืนชื่อบล็อกแรกเป็นเดิม); ฟอร์ม/กราฟ/ผลอ่านง่ายบนจอแคบ |
| กราฟ | SVG ที่สร้างจากจุดข้อมูลใน `SimResult` ด้วย stdlib ล้วน | ไม่มี JS, ไม่มี dependency ใหม่, ไม่มี trace ปลอม; ป้าย "illustrative" บอกรูปแบบการสอนไม่ใช่ข้อมูลแต่ง |
| รันครั้งเดียวได้ครบ | `run_all_for_request()` เรียก `.op/.ac/.tran` แล้วรวม `SimResult` | ต้องแสดงกราฟ 2 อัน + ตาราง 3 อันพร้อมกันโดยไม่ต้องกด 3 ครั้ง |
| Mode selector | radio `DC` / `AC` / `Transient` อยู่ในฟอร์มเดียวกัน | ใช้เปลี่ยน focus เท่านั้น จึงสลับได้โดยไม่ reload/ล้างผล |
| หน่วย | ใช้ตาราง `UNIT`, `AMPLITUDE_UNIT`, `FREQUENCY_UNIT` ใน `spice_engine.py` | แปลงเป็น SI ก่อนสร้าง netlist ตามแนว `parse_resistance()` ของ Lab 03 |
| RL | เพิ่ม `rl`/`rl_unit` ตั้งแต่ฟอร์มจนถึง `SimInput` และ netlist | เดิม hard-code `10k`; ตอนนี้แก้ได้และ schematic อ่านค่าจากฟอร์ม |
| Model | `QNPN` แบบ teaching-only (`BF IS VAF`, capacitance=0) | ไม่มี model file จากผู้สอน; ต้องบอกว่าไม่ใช่ part จริง |
| ความผิดพลาด | ทุก error/status ที่ไม่ใช่ `SUCCESS` ล้างผลทั้งหมด | ห้ามโชว์ "SUCCESS" หรือค่ารอบเก่าตอน engine หาย |
| สิ่งที่ตัดออก | ไม่ render analytical table, netlist และ log excerpt อีก | ตามคำขอ redesign; ลด cognitive load และไม่ปะปนแหล่งที่มาของตัวเลข |
| Schematic | SVG ของ **BJT voltage-divider CE** ใน template แสดงชื่อชิ้นส่วนเท่านั้น | วาดสัญลักษณ์ NPN **ในวงกลมเล็ก** (r=34), ตัวต้านทานเป็น **กล่องอิมพิแดนซ์** แทน zigzag, มีลูกศรที่ Vin; R1/R2 divider + RC/RE + CIN/COUT + RL; rail VCC สั้นจาก node บน R1 ถึง node บน RC ตามที่ผู้ขอ; **ไม่ใส่ตัวเลขบนสัญลักษณ์** เพราะห้ามใช้ JS ฝั่ง client จึงอัปเดตทุกครั้งที่พิมพ์ไม่ได้ (ค่าในฟอร์มยังมีผลหลังกด Run) |

### Data flow (Lab 04)

```
Browser ──GET /simulator?analysis=tran&rl=4.7...──> Flask ──render form + focus──> Browser
Browser ──POST /simulate (form ทั้งชุด)───────> Flask
                                      validate_sim_input() → SimInput (SI, รวม RL)
                                      run_all_for_request() → tempdir/dc,ac,tran/*.cir
                                                   → ngspice_con.exe -b -o run.log
                                      parse_op/parse_ac/parse_tran() → SimResult ×3
                                      svg_bode()/svg_waveform() → SVG string
Flask ──render simulator.html (3 blocks, 2 plots, 3 result tables)──> Browser
```

### สิ่งที่ตรวจแล้วว่าทำงาน

- 62 tests ผ่าน (20 เดิม + 42 ของ Lab 04) รวม real ngspice gate
- B1–B7 ตรวจซ้ำหลัง redesign ด้วย OpenCode Browser, B8 ด้วย Impeccable shot
  1280×900/390×844; ไม่มี `<script>`, ไม่มี analytical/netlist section
- detector หลัง redesign เหลือเฉพาะ advisory/warning (straggler, em-dash, nested-cards)
  รายงาน critique/polish/audit ของ layout ก่อนหน้าเก็บไว้ใน `.impeccable/audit/`

### สิ่งที่ยังเป็นข้อจำกัด

- มีวงจรอ้างอิงเดียว ไม่มี circuit editor, ไม่มี emitter bypass, ไม่มี SPICE ของ Fixed/Emitter Bias
- โมเดล QNPN ไม่ใช่ transistor part จริง; อย่าใช้ผลไปออกแบบจ่ายจริง
- ngspice run เป็น synchronous สูงสุด 30 วินาที หน้าเว็บแจ้งไว้แล้วแต่ยังยกเลิกไม่ได้
- ต้องติดตั้ง ngspice console แยกจาก Flask; ไม่ได้ include binary ใน repo

