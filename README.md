# BJT DC Bias Web App — Lab 03 + Lab 04 CE Amplifier Simulator

โปรเจกต์นี้รวมสองส่วนแยกชัดเจน:

- **Lab 03** — เครื่องคำนวณ **DC Bias** ของ BJT แบบ Common Emitter สามวงจรไบอัส (Fixed / Emitter / Voltage Divider)
- **Lab 04** — **CE Amplifier Simulator** ที่รัน **ngspice-47 จริง** สำหรับ `.op`, `.ac`, `.tran`

รายวิชา ENG29 2121 Electronics Laboratory  
(ต่อยอดจาก Lab 02 ที่มีเฉพาะวงจรแบ่งแรงดัน)

---

## สารบัญ (Table of Contents)

- [Lab 03 — DC Bias Web App](#lab03)
  - [ลิงก์ส่งงาน Lab 03](#lab03-links)
  - [วิธีรัน Lab 03](#lab03-run)
  - [การทดสอบ Lab 03](#lab03-tests)
  - [ผลตรวจ A1–A5 (Lab 03)](#lab03-browser)
- [Lab 04 — CE Amplifier Simulator](#lab04)
  - [ลิงก์ส่งงาน Lab 04](#lab04-links)
  - [วิธีรันและติดตั้ง ngspice (Lab 04)](#lab04-run)
  - [การทดสอบ Lab 04](#lab04-tests)
  - [ผลตรวจ B1–B8 (Lab 04)](#lab04-browser)
- [โครงสร้างไฟล์](#project-structure)
- [Submission checklist](#submission-checklist)

---

<a id="lab03"></a>

## Lab 03 — DC Bias Web App

หน้า `/` คำนวณ DC Bias ด้วย **Python ฝั่ง server** แล้วส่ง HTML ที่คำนวณเสร็จกลับมา
**ไม่มี JavaScript ฝั่ง client** และไม่มีค่าฮาร์ดโค้ดในหน้าเว็บ

| โหมด | อินพุตตัวต้านทาน | สมการกระแส Base |
|---|---|---|
| **Fixed Bias** | RB, RC | `IB = (VCC − VBE) / RB` |
| **Emitter Bias** (แหล่งจ่ายเดียว) | RB, RC, RE | `IB = (VCC − VBE) / [RB + (β+1)·RE]` |
| **Voltage Divider Bias** | R1, R2, RC, RE | `IB = (VTH − VBE) / [RTH + (β+1)·RE]` |

กดปุ่มโหมดครั้งเดียว — แผนภาพและฟอร์มเปลี่ยนตามทันที ช่องที่โหมดนั้นไม่ใช้จะจางและกดไม่ได้
ผลที่แสดง: `VB, VE, VC, VCE, IC, IB, IE` พร้อมสถานะ **Forward Active / Cutoff / Saturation**

หน้าเว็บแสดงเพิ่มเติม:

- แผนภาพ SVG ที่เปลี่ยนตามโหมด และเติมค่าอุปกรณ์/แรงดัน node จากผลคำนวณจริง
- ข้อความยืนยัน **Active Region Approximation OK**
- คำเตือนเมื่อแบบจำลอง Forward-Active ใช้ไม่ได้
- error ที่ระบุชื่อช่อง (เช่น `RB = 0`) และไม่ค้างผลรอบก่อน
- เลือกหน่วย `Ω`, `kΩ`, `MΩ` (1 MΩ = 1,000 kΩ) และค่าที่เลือกแสดงบน SVG ด้วย

> ⚠️ **ข้อจำกัดของแบบจำลอง Lab 03:** Forward-Active approximation (β คงที่, VBE คงที่,
> ไม่คิด Early effect) **ไม่ใช่ผลจาก SPICE** และไม่ใช่ผลจากการวัดจริง
> เมื่ออยู่นอกช่วงขยาย ค่าที่แสดงเป็นการประมาณเพื่อการสอน — อย่าใช้ตัดสินใจทางวิศวกรรม

<a id="lab03-links"></a>

### ลิงก์ส่งงาน (Lab 03)

| รายการ | ค่า |
|---|---|
| GitHub repository | <https://github.com/siriphailin/BJT-DC-Bias-Web-App> |
| Commit SHA ของ Lab 03 | [`442c05cd329660c48b4ca142e22bedc554d99e99`](https://github.com/siriphailin/BJT-DC-Bias-Web-App/commit/442c05cd329660c48b4ca142e22bedc554d99e99) |
| วิธีตรวจผลจริง | **OpenCode Browser** |
| ไปยัง Lab 04 | [Lab 04 — CE Amplifier Simulator](#lab04) |

<a id="lab03-run"></a>

### วิธีรัน (Lab 03)

```powershell
# 1) ติดตั้ง dependency ของ Flask (ครั้งแรกหรือหลัง clone ใหม่)
python -m pip install -r requirements.txt

# 2) รัน server
python -m flask --app app run --debug
```

เปิด Browser: **<http://127.0.0.1:5000/>**

<a id="lab03-tests"></a>

### การทดสอบ (Lab 03)

```bash
python -m unittest discover -s tests -v
```

ผลรวมทั้งโปรเจกต์: **`Ran 64 tests` … `OK`**  
แยกตามไฟล์: `test_dc_bias.py` 14 + `test_web.py` 7 (Lab 03/route เดิม รวมปุ่มสลับ) = **21**
ล็อกผลรันจริงวันที่ 2026-11-24 (ไม่มี skip) อยู่ใน [`docs/test-log.md`](docs/test-log.md)

<a id="lab03-browser"></a>

### ผลตรวจ A1–A5 (Lab 03)

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
[`docs/validation.md`](docs/validation.md) หัวข้อ 8  
ภาพหน้าจอ: [`docs/screenshots/`](docs/screenshots/) — `lab03-A1-baseline.jpeg`,
`lab03-A2-fixed.jpeg`, `lab03-A3-emitter.jpeg`, `lab03-A5-invalid-input.jpeg`

---

<a id="lab04"></a>

## Lab 04 — CE Amplifier Simulator

หน้า `/simulator` ใช้ **ngspice-47 จริง** กับวงจร voltage-divider bias
(CIN/COUT = 10 µF, RL แก้ได้) และมี **บล็อกเกริ่นนำบนสุด**
`CE Amplifier Lab: DC Bias / AC / Transient` ตามด้วย 4 บล็อก:

1. **Circuit & Parameters** — schematic SVG ของ BJT voltage-divider common-emitter
   (NPN ในวงกลมเล็ก, ตัวต้านทานเป็นกล่องอิมพิแดนซ์, ลูกศร Vin, R1/R2 divider, RC, RE,
   CIN/COUT, RL; rail VCC สั้นจาก R1 ถึง RC) **แสดงเฉพาะชื่ออุปกรณ์ ไม่มีตัวเลขกำกับ**
   + ช่องแก้ `Vcc`, `RC`, `R1`, `R2`, `RE`, `RL`, `Source` พร้อมหน่วย
   (Ω/kΩ/MΩ, mV/V, Hz/kHz/MHz) และปุ่ม Run simulation
2. **Simulation & Plots** — radio `DC` / `AC` / `Transient`, กราฟ
   `Bode response (illustrative)` และ `Input/Output waveforms (illustrative)`
3. **Engineering Results** — `DC Operating Point` (VB · VE · VC · VCE · **IC** จาก `.print op`),
   `AC Frequency Response` (Gain / Phase / Frequency + **low −3 dB frequency**),
   `Transient Response` (Vin / Vout / Time) และกล่อง
   **Analytical reference — NOT a SPICE result** แยกจากผล ngspice
4. **Engine ngspice** — Run status ของ DC/AC/Transient, model, engine version,
   Run timestamp, ตารางหน่วย และ provenance (netlist/log)

กด Run ครั้งเดียวแล้ว Flask รันทั้งสาม analysis (`.op`, `.ac dec 20 1 1Meg`, `.tran`) จริง
ใน temp dir แล้ว render ทุกกราฟ/ตารางพร้อมกัน — radio เป็นตัวเลือก “focus” เท่านั้น
จึงสลับได้โดยไม่ reload หรือล้างผลที่แสดงอยู่ (ตามที่ใบงานกำหนด)

| Analysis | คำสั่งจริงใน netlist | ผลที่ render |
|---|---|---|
| DC | `.op` + `.print op` | VB, VE, VC, VCE, **IC** จากตาราง log จริง |
| AC | `.ac dec 20 1 1Meg` | Bode gain (dB) + phase (°) จาก `.print ac`; −3 dB ใช้ interpolation หรือข้อความ `not determined in sweep range` |
| Transient | `.tran` + `.print tran` | Vin/Vout vs time (ms) จาก `.print tran` |

- หน้าแสดง **Model (`QNPN` teaching), analysis directives, netlist และ engine log excerpt**
  ใน `Netlist & engine log — result provenance` เพื่อยืนยันผลจากการรันจริง ไม่ใช่ค่าฮาร์ดโค้ด
- ค่าอ้างอิงเชิงวิเคราะห์จาก `dc_bias.py` อยู่ในกล่องแยกที่ติดป้าย
  **“Analytical reference — NOT a SPICE result”** ห้ามนำไปปนกับผล ngspice
- กราฟเป็น **SVG ที่ Python สร้างจากจุดข้อมูล SPICE จริง** คำว่า “illustrative” หมายถึง
  รูปแบบสำหรับการสอน ไม่ใช่เส้นที่แต่งขึ้น และไม่มี `<script>` ในหน้า
- Amplitude/Frequency กำหนดแหล่ง sine สำหรับ Transient; DC ไม่ใช้ และ AC ใช้ drive 1 V คงที่
  ในช่วง 1 Hz–1 MHz
- ทั้งสองหน้ามี **ปุ่มสลับ Lab 03 / Lab 04** อยู่เหนือบล็อกแรก (ลิงก์ HTML ล้วน ไม่มี JavaScript;
  หน้าปัจจุบันทำเครื่องหมาย `aria-current="page"`)
- ถ้า `RE=0` หรือ `RL=0` → HTTP 400; ถ้า engine หาย → `ENGINE_NOT_FOUND` + วิธีแก้
  **ไม่แสดงผลเก่าค้าง**

**สมมติฐานของโมเดล (สำคัญ):** `QNPN` คือโมเดลสำหรับการสอน
`BF=100 IS=1E-14 VAF=100 RB=0 CJE=CJC=TF=TR=0` ไม่ใช่ part number ของทรานซิสเตอร์จริง
และกราฟ AC ส่วนใหญ่สะท้อนตัวเก็บประจุคู่จ่าย ไม่ใช่ capacitance ภายในทรานซิสเตอร์

<a id="lab04-links"></a>

### ลิงก์ส่งงาน (Lab 04)

| รายการ | ค่า |
|---|---|
| GitHub repository | <https://github.com/siriphailin/BJT-DC-Bias-Web-App> |
| Commit SHA ของโค้ด Lab 04 (tag `lab04`) | [`e34fcaaedad1d35c4c8e24a0af29155c2121e267`](https://github.com/siriphailin/BJT-DC-Bias-Web-App/commit/e34fcaaedad1d35c4c8e24a0af29155c2121e267) |
| Commit SHA ของหลักฐาน Lab 04 (docs/screenshots/test log) | [`f9868072b744cf2724b9af0f9ee1d62a0738f504`](https://github.com/siriphailin/BJT-DC-Bias-Web-App/commit/f9868072b744cf2724b9af0f9ee1d62a0738f504) |
| วิธีตรวจผลจริง | **OpenCode Browser** + **Impeccable CLI** |
| กลับไป Lab 03 | [Lab 03 — DC Bias Web App](#lab03) |

<a id="lab04-run"></a>

### วิธีรันและติดตั้ง ngspice (Lab 04)

ต้องการ `ngspice_con.exe` (console build) เท่านั้น — `ngspice.exe` แบบ GUI ไม่คืน
output ให้ subprocess วิธีติดตั้งที่ใช้จริงบนเครื่องนี้ (winget ไม่มีแพ็กเกจ):

```powershell
# เปิด PowerShell แบบ "Run as administrator" (กด Yes ตอน UAC แล้วใส่รหัสเครื่องเอง)
$pkg = "$env:TEMP\ngspice.47.0.0.nupkg"
$work = "$env:TEMP\ngspice-setup"
Invoke-WebRequest -Uri https://community.chocolatey.org/api/v2/package/ngspice/47.0.0 -OutFile $pkg
New-Item -ItemType Directory -Force $work | Out-Null
tar -xf $pkg -C $work
tar -xf "$work\tools\ngspice-47_64.7z" -C "$work\tools"

$target = "$env:LOCALAPPDATA\Programs\ngspice-47"
New-Item -ItemType Directory -Force $target | Out-Null
Copy-Item "$work\tools\Spice64" -Destination $target -Recurse -Force
& "$target\Spice64\bin\ngspice_con.exe" -v
```

หรือติดตั้งใน `%LOCALAPPDATA%\Programs\` (ไม่ต้อง UAC) แล้วตั้ง `NGSPICE_ENGINE` ชี้ไปที่
`ngspice_con.exe` เต็ม path ก็ได้ โปรแกรมค้นหาจาก PATH และโฟลเดอร์ติดตั้งที่พบบ่อยเอง
ถ้าตั้ง path ผิดจะแสดง `ENGINE_NOT_FOUND` พร้อมวิธีแก้ แทนการใช้ผลเก่าหรือผลปลอม

รัน server เหมือน Lab 03 แล้วเปิด: **<http://127.0.0.1:5000/simulator>**

```powershell
python -m pip install -r requirements.txt
python -m flask --app app run --debug
```

ถ้าไม่ได้ activate venv ให้ใช้ `.venv\Scripts\python.exe -m flask --app app run --debug`

<a id="lab04-tests"></a>

### การทดสอบ (Lab 04)

```bash
python -m unittest discover -s tests -v
```

ผลรวมทั้งโปรเจกต์: **`Ran 64 tests` … `OK`**  
แยกตามไฟล์: `test_spice_engine.py` 28 + `test_simulator_web.py` 15 = **43**
(รวมกับ Lab 03 21 ตัวเป็น 64)  
ล็อกผลรันจริงวันที่ 2026-11-24 (ไม่มี skip) อยู่ใน [`docs/test-log.md`](docs/test-log.md)

> ถ้าไม่พบ `ngspice_con.exe` ชุดทดสอบ SPICE จะ `skip` อัตโนมัติ; ในเครื่องนี้ติดตั้ง ngspice-47 แล้ว
> รอบล่าสุดจึง **ไม่มี test ใดถูก skip** (รวม end-to-end ที่เรียก engine จริง)

Impeccable v0.1.27 เป็นเครื่องมือพัฒนา UI (ไม่ใช่ runtime dependency) ติดตั้งแบบ project-scope
ใน `.opencode/`; เรียกผ่าน `.opencode\skills\impeccable\scripts\impeccable.cmd`
รายงาน audit หลัง polish ของ layout ก่อนหน้าอยู่ใน
`.impeccable/audit/2026-11-24T08-45-44Z__project.md`; หลัง redesign รัน `detect` บน URL จริงอีกครั้ง
เหลือเฉพาะ advisory/warning (straggler, em-dash, nested-cards) ไม่มี findings เรื่อง overflow
(ถ้าไม่ต้องการเก็บเครื่องมือนี้ใน repo ให้มนุษย์เพิ่ม `.opencode/` และ `.impeccable/` ลง `.gitignore`)

<a id="lab04-browser"></a>

### ผลตรวจ B1–B8 (Lab 04)

ผล **รอบสุดท้ายกับโค้ดที่ push จริง** (`e34fcaa`) อยู่ใน
[`docs/validation.md` หัวข้อ 9.8](docs/validation.md) — B1–B8 ผ่านจริงด้วย
OpenCode Browser + Impeccable CLI (B7 มี HTTP 400 จาก input ผิดตั้งใจ; B8 เหลือ advisory/warning, failure 0)

ภาพหน้าจอจากการรัน ngspice จริง:

- [`lab04-final-desktop-1280x900.png`](docs/screenshots/lab04-final-desktop-1280x900.png) — ภาพ 1280×3568
- [`lab04-final-phone-390x844.png`](docs/screenshots/lab04-final-phone-390x844.png) — ภาพ 406×5513 (includes scrollbar)

> หัวข้อ 9.5–9.7 ใน validation เป็นหลักฐานรอบก่อนหน้า; **§9.8** คือแหล่งที่ใช้อ้าง PASS รอบสุดท้าย

---

<a id="project-structure"></a>

## โครงสร้างไฟล์

```
BJT DC Bias Web App/
├── app.py                  # Lab 03: GET /, POST /calculate | Lab 04: GET /simulator, POST /simulate
├── dc_bias.py              # สมการ DC Bias ทั้งสามโหมด (ไม่ import Flask)
├── spice_engine.py         # validate → netlist → ngspice → parser → SVG (ไม่ import Flask)
├── templates/index.html    # Lab 03 UI (แก้เพียงเพิ่มลิงก์ไป /simulator)
├── templates/simulator.html# Lab 04 UI: intro + 4 blocks, schematic, unit selects, 2 plots, 3 tables
├── static/style.css        # Lab 03 styles + .sim-* styles
├── tests/                  # unittest 64 ตัว (Lab 03 21 + Lab 04 43)
├── docs/                   # design-note, validation, test-log, screenshots, spec/plan
├── requirements.txt
├── AGENTS.md               # conventions สำหรับ AI coding agent
└── .opencode/              # Impeccable แบบ project-scope (มนุษย์ตัดสินใจ commit หรือ ignore)
```

**หลักการสำคัญ:** `app.py` ไม่มีสมการ DC bias แม้บรรทัดเดียว — มันอ่านค่าจากฟอร์ม แปลงหน่วย
เลือกฟังก์ชันตาม `mode` แล้วเรียกฟังก์ชันใน `dc_bias.py`; ส่วน Lab 04 ส่งค่าที่ validate แล้วให้
`spice_engine.py` เป็นคนสร้าง netlist, เรียก ngspice, parse และ render SVG
ห้ามฮาร์ดโค้ดผล SPICE หรือกราฟใน template

<a id="submission-checklist"></a>

## Submission checklist

ดูตารางแยกหัวข้อพร้อมลิงก์หลักฐานได้ใน
[`docs/validation.md` หัวข้อ 10](docs/validation.md) — ครบทั้ง URL/SHA, Flask app,
วิธีติดตั้ง/รันใน README และ B1–B8 พร้อมแหล่งอ้างอิง/ความคลาดเคลื่อน/ข้อจำกัด
