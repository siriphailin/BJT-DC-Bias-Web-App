# Design — BJT Common-Emitter Amplifier Simulator v1 (Lab 04)

- **วันที่:** 2026-11-24
- **รายวิชา:** ENG29 2121 Computer Programming for Electrical Engineers (2/2569)
- **ที่มา:** ใบงาน Lab 04 — BJT Amplifier Simulator v1
- **Repo:** `C:\Users\B6837020\Documents\GitHub\BJT-DC-Bias-Web-App` (ต่อยอดจาก Lab 03)
- **สถานะ:** เอกสารออกแบบ v1 (เก็บเป็นหลักฐาน historical) — ภายหลังผู้ขอให้ redesign หน้าเป็น
  3 blocks และตัด analytical/provenance ออกจาก UI; สิ่งที่เปลี่ยนดูได้ใน
  [`../plans/2026-11-24-lab04-bjt-amplifier-simulator.md`](../plans/2026-11-24-lab04-bjt-amplifier-simulator.md)
  หัวข้อ **Update record** และผลทดสอบจริงใน [`../../validation.md`](../../validation.md) §9.5–9.6
  (โค้ด/route/simulation ยังเป็นไปตาม spec นี้; RL แก้ได้และตรวจหา engine ในเครื่องแล้ว)

---

## 1. Intent และเหตุผล

Lab 03 ส่ง Flask Web App ที่คำนวณ DC Bias แบบ Forward-Active ด้วยสมการ Python ล้วน
Lab 04 ต้อง **ต่อยอดอันเดิม** ให้เป็นโปรแกรมจำลอง Common-Emitter Amplifier รุ่นแรกที่
รัน `ngspice` จริง 3 การวิเคราะห์:

1. **DC** `.op` → operating point (VB, VE, VC, VCE, IC)
2. **AC** `.ac` → frequency response (gain magnitude dB และ phase)
3. **Transient** `.tran` → waveform ของ Vin/Vout กับเวลา

เหตุผลที่ไม่สร้างใหม่ทั้งหมด: ใบงานบังคับว่า DC Bias 3 โหมดเดิม (Fixed / Emitter /
Voltage Divider) ต้องยังทำงานอยู่ และห้ามลบเส้นทาง `dc_bias.py` เดิม

เหตุผลที่ต้องใช้ `ngspice` จริง: ใบงานห้ามกราฟ mock/hard-code และให้ความสำคัญกับ
ความถูกต้องมากกว่าความสวยงาม — ถ้า solver ไม่รัน แต่หน้าเว็บยังโชว์ “Success”
ถือว่า **FAIL**

## 2. Goals

1. รักษา `GET /` และ `POST /calculate` ของ Lab 03 ให้ผ่าน A1–A5 เหมือนเดิม (Regression B1)
2. เพิ่มหน้า `GET /simulator` สำหรับ CE Voltage Divider อ้างอิง 1 วงจร
3. `POST /simulate` รัน ngspice จริงผ่าน `spice_engine.py` ด้วย `subprocess.run`
4. แสดงผล DC จาก `.op` พร้อม model/version/run status/netlist log
5. แสดง Bode plot จาก `.ac` (frequency, gain dB, phase) และ waveform จาก `.tran`
   (time, Vin, Vout) โดยกราฟเป็น **SVG ที่ Python สร้างจากข้อมูลจริง**
6. ปรับ amplitude/frequency แล้วผลต้องเปลี่ยน (B3, B6)
7. แยกป้าย "SPICE result" กับ "Analytical reference (`dc_bias.py`)" ให้ชัด
8. error path ต้องชัดเจน: engine ไม่มี / run fail / output ว่าง / timeout / input ผิด
   → ไม่ค้างผลเก่า ไม่แจ้ง Success ปลอม
9. ใช้ Impeccable จริง (critique → polish → audit) และตรวจ B1–B8 ด้วย Browser จริง
10. README + `docs/validation.md` + git diff พร้อม commit โดย **มนุษย์กดเอง**

## 3. Non-goals (ห้ามทำใน Lab 04 นี้)

- Drag-and-drop circuit editor หรือต่อวงจรอิสระ
- SPICE ของ Fixed/Emitter Bias หรือ AC ของทุก bias mode
- FET, การเขียน SPICE solver เอง, deploy สู่ภายนอก
- Emitter bypass capacitor `C_E` (เป็นงานต่อยอด)
- Animated overlay / ภาพกระแส-แรงดันเคลื่อนไหวบนวงจร
- การใช้สมการประมาณแทน ngspice เพื่ออ้างว่าเป็นผลจำลอง
- JavaScript ฝั่ง client, dependency ใหม่ของ Python (นอกเหนือ Flask)

## 4. Anti-goals (ถ้าเกิดขึ้นถือว่าล้มเหลว แม้หน้าจะสวย)

- กราฟ/ตัวเลขมาจากค่าที่เขียนค้างใน template หรือจาก mock data
- `app.py` มีสมการวิศวกรรม หรือ `spice_engine.py` import Flask
- ใช้ `shell=True`, ต่อ string จากฟอร์มเข้า command หรือ netlist โดยไม่ validate
- ngspice fail แล้วหน้ายังแสดง status Success/ผลรอบก่อน
- เอาผล analytical และ SPICE ไปรวมตารางเดียวโดยไม่บอกที่มา
- agent รัน `git commit` / `git push` เอง (กติกาเดิมของ repo)

## 5. Constraints และสภาพแวดล้อมจริงที่ตรวจแล้ว

| รายการ | ค่าที่ตรวจได้ | การรับมือ |
|---|---|---|
| Repo | `BJT-DC-Bias-Web-App`, branch `main`, commit `fcdee8d`, working tree สะอาด | แก้บน branch เดิม ไม่ reset |
| Python บน PATH | alias ของ Microsoft Store (ใช้ไม่ได้จริง) | ใช้ `C:\Program Files\Python314\python.exe` หรือ `py -3.14` |
| Python จริง | 3.14.2 (`py -0p` เห็น 3.14 และ 3.7) | ใช้ 3.14 ตาม spec เดิม |
| Flask | ยังไม่ติดตั้งในทุก Python ที่เจอ | `pip install -r requirements.txt` ในขั้น setup |
| git | ไม่มีบน PATH แต่มี `...\AppData\Local\Programs\Git\cmd\git.exe` | ใช้ path เต็ม หรือเพิ่ม PATH ชั่วคราว |
| ngspice | ติดตั้งแล้วจาก Chocolatey nupkg 47.0.0 → `...\AppData\Local\Programs\ngspice-47\Spice64\bin\ngspice_con.exe`, version **ngspice-47** (ตรวจด้วย `-v`) | ใช้ **console binary** `ngspice_con.exe`; ตัว `ngspice.exe` เป็น GUI ไม่ yield output ใน batch |
| node/npx | ติดตั้งแล้ว: node **v26.13.1**, npx **11.20.0** (zip binary ใน `%LOCALAPPDATA%\Programs\node-v26.13.1-win-x64`) | winget ต้อง UAC → ใช้ zip แทน; Impeccable engine v0.1.27 ติดตั้งใน `.opencode` แล้ว |
| dependency | `requirements.txt` มีแค่ `Flask>=3.0,<4.0` | ไม่เพิ่ม chart library; เขียน SVG เอง |
| บรรทัด base | `docs/design-note.md`, spec/plan เดิมอ่านแล้ว | ใช้แนวทางเดียวกัน |

## 6. Decisions ที่ล็อกจาก brainstorming

| # | เรื่อง | ตัดสิน | เหตุผล |
|---|---|---|---|
| D1 | โครงสร้าง | ใช้ repo เดิม ไม่สร้าง scaffold ใหม่ | ใบงานบังคับรักษา Lab 03 |
| D2 | Frontend | **คง no-JS**; กราฟ SVG render จาก Python ฝั่ง server | ตรง `AGENTS.md`, ไม่เพิ่ม dependency, test ง่าย |
| D3 | Route | `GET /` เดิม untouched; เพิ่ม `GET /simulator` + `POST /simulate` | กัน regression B1 ได้ชัดที่สุด |
| D4 | Setup | รวมติดตั้ง Flask/ngspice/Node + fallback engine ไม่พร้อม | สภาพแวดล้อมยังไม่พร้อมจริง |
| D5 | BJT model | `.model QNPN NPN(...)` ที่กำหนดเอง พร้อมระบุสมมติฐาน | ไม่มี Starter Kit; ห้ามเดาแอบอ้างรุ่นจริง |
| D6 | Impeccable | ติดตั้ง Node แล้วใช้ skill จริง | rubric ให้ 2 คะแนน |
| D7 | ภาษา | อังกฤษนำ ไทยในวงเล็บ ตาม `AGENTS.md` | สอดคล้องของเดิม |
| D8 | Commit | agent stage/report ได้ **ห้าม commit/push** | กติกาเดิมของ repo |

## 7. Architecture / Data flow

```
Browser (GET /simulator)
    │  form: analysis, vcc, r1,r2,rc,re, amplitude(mV), frequency(kHz)
    ▼
Flask app.py  → validate (float/finite/range) → spice_engine.build_netlist(params)
    │                                          │
    │                                          ▼
    │                              tempdir/circuit.cir
    │                                          │
    │                              subprocess.run([ngspice, -b, -o, run.log,
    │                                              -r, run.raw, circuit.cir],
    │                                             shell=False, timeout=30, cwd=tempdir)
    │                                          ▼
    │                              parse_op / parse_ac / parse_tran
    │                                          ▼
    │                              SimResult(status, values/series, provenance)
    ▼
templates/simulator.html  ← Jinja เติมตัวเลข + SVG ที่สร้างจาก series จริง
    │
    └── panel แยก: Analytical reference จาก dc_bias.py (ไม่ใช่ SPICE)

dc_bias.py  ไม่ถูกแก้ — เป็น independent reference เฉพาะ DC
Playwright/Browser tools  ตรวจ B1–B8 จาก HTML จริง
Impeccable  critique → polish → audit เฉพาะ template/style
```

## 8. โครงสร้างไฟล์ที่คาดว่าจะเปลี่ยน

```
BJT-DC-Bias-Web-App/
├── app.py                     # EDITOR: เพิ่ม import + 2 route ใหม่; ไม่แตะ /calculate
├── dc_bias.py                 # UNCHANGED (reference เท่านั้น)
├── spice_engine.py            # NEW: netlist + subprocess + parser + SVG helpers
├── templates/
│   ├── index.html             # EDITOR เพิ่มลิงก์ไป /simulator เท่านั้น (ไม่แตะฟอร์มเดิม)
│   └── simulator.html         # NEW: ฟอร์ม + status + ผล + กราฟ + provenance
├── static/style.css           # EDITOR: เพิ่ม class ใหม่ prefix `sim-`
├── tests/
│   ├── test_dc_bias.py        # UNCHANGED (20 tests เดิม)
│   ├── test_web.py            # UNCHANGED (6 tests เดิม)
│   └── test_spice_engine.py   # NEW: netlist/parser/error (fixture คือ parser test เท่านั้น)
├── requirements.txt           # UNCHANGED (Flask เท่านั้น)
├── README.md                  # EDITOR: setup + run + ngspice/Node + version จริง
├── AGENTS.md                  # EDITOR: ขยายขอบเขต Lab 04, ย้ำห้าม commit/hard-code
└── docs/
    ├── design-note.md         # EDITOR: สรุป Lab 04 เพิ่ม
    ├── validation.md          # EDITOR: เพิ่มตาราง B1–B8
    └── superpowers/specs/2026-11-24-lab04-bjt-amplifier-simulator-design.md  # ไฟล์นี้
```

## 9. รายละเอียด `spice_engine.py`

### 9.1 Public interface

```python
@dataclass(frozen=True)
class SimInput:
    vcc: float          # V, >0
    r1: float           # Ω, >0
    r2: float           # Ω, >0
    rc: float           # Ω, >0
    re: float           # Ω, >0
    amplitude_v: float  # V peak, >0 (ฟอร์มรับ mV แล้วแปลง)
    frequency_hz: float # Hz, >0 (ฟอร์มรับ kHz แล้วแปลง)

@dataclass(frozen=True)
class SimResult:
    analysis: str            # "dc" | "ac" | "tran"
    status: str              # SUCCESS | ENGINE_NOT_FOUND | RUN_FAILED | TIMEOUT | EMPTY_OUTPUT | INVALID_INPUT
    message: str             # สองภาษา อังกฤษนำ ไทยในวงเล็บ
    netlist: str
    log_excerpt: str
    values: dict | None      # DC: {vb,ve,vc,vce,ic_mA}
    ac_points: tuple | None  # (freq_hz, gain_db, phase_deg, gain_abs)
    tran_points: tuple | None# (time_s, vin_v, vout_v)
    provenance: dict         # engine_version, model, directive, timestamp, paths
```

Functions:

- `validate_sim_input(raw: dict[str,str]) -> tuple[SimInput|None, list[str]]`
- `build_netlist(params: SimInput, analysis: str) -> str`
- `run_analysis(params: SimInput, analysis: str, workdir: Path, engine: str) -> SimResult`
- `parse_op(log_text: str) -> dict`
- `parse_ac(log_text: str) -> tuple`
- `parse_tran(log_text: str) -> tuple`
- `engine_version(engine: str) -> str`
- `svg_bode(ac_points) -> str`, `svg_waveform(tran_points) -> str`

### 9.2 Netlist อ้างอิง (template)

โหนด: `VCC`, `RCTOP`, `BASE`, `COL`, `EMI`, `VIN`, `VOUT`, `0`

```
* CE voltage-divider reference - ENG29 2121 Lab 04
VCC  VCC 0 {vcc}
VIC  VCC RCTOP 0        ; zero-volt probe for IC measurement
R1   VCC BASE {r1}
R2   BASE 0 {r2}
RC   RCTOP COL {rc}
RE   EMI 0 {re}
Q1   COL BASE EMI QNPN
CIN  VIN BASE 10u
COUT COL VOUT 10u
RL   VOUT 0 10k
VIN  VIN 0 DC 0 AC 1 SIN(0 {amp} {freq})
.MODEL QNPN NPN(BF=100 IS=1E-14 VAF=100 RB=0 CJE=0 CJC=0 TF=0 TR=0)
.op                         ; analysis = dc
.print op v(base) v(col) v(emi) i(vic)
* .ac dec 20 1 1Meg          ; analysis = ac
* .print ac vdb(vout) vp(vout) vdb(vin) vp(vin)
* .tran {tstep} {tstop} 0 {tstep}  ; analysis = tran
* .print tran time v(vin) v(vout)
.END
```

หมายเหตุ netlist (ปรับตามผลทดสอบจริงกับ ngspice-47 แล้ว):

- มี `VIC` เป็น zero-voltage source เพื่ออ่าน `i(vic)` เป็น IC โดยไม่ต้องเดา sign ของ `i(RC)`
- จะเลือกเฉพาะบรรทัด directive/print ของ analysis ที่รัน; ที่เหลือเป็น comment
- **ห้ามส่ง `-r` ให้ ngspice** — เมื่อมี `-r` ngspice จะแจ้ง `print line ignored since rawfile was produced`
  และไม่มีตาราง `.print` ใน log เลย (ตรวจแล้ว) → `-o run.log` อย่างเดียวพอ
- ใช้ title เป็น ASCII อย่างเดียว (อักษร `—` ถูกแปลงเป็น `?` ใน log)
- DC: coupling capacitor เปิดวงจรโดยธรรมชาติ (ngspice `.op`) — ไม่ต้องลบ `CIN/COUT`
- AC: `VIN ... AC 1` ทำให้ `Vin = 1 V` เป็น reference; gain = `vdb(vout) - vdb(vin)`
- **`.print ac` ห้ามใส่ `freq`** — ngspice-47 แจ้ง `can't parse 'freq'`; frequency เป็นคอลัมน์
  อัตโนมัติต่อจาก `Index` ในตารางอยู่แล้ว
- AC sweep `dec 20 1 1Meg` ครอบมุมของ coupling capacitor
- **`.tran` ต้องมี TSTEP > 0** — `.tran 0 ...` ทำให้ `TSTEP is invalid, must be greater than zero`;
  ใช้ `.tran {tstep} {tstop} 0 {tstep}`
- `tstop = 5 / frequency_hz`, `tstep = tstop / 500`, จำกัด `tstop ≤ 50 ms`
- `.print` ใช้เพื่อให้ผลเป็นข้อความใน `run.log` ที่ parser อ่านได้โดยไม่พึ่ง raw binary
- **ห้ามใช้ `.control ... .endc`** ร่วมกับ batch mode นี้จนกว่าจะทดสอบจริง

### 9.3 BJT model (สมมติฐานที่ต้องแสดงบนหน้าเว็บ)

`QNPN NPN(BF=100 IS=1E-14 VAF=100 RB=0 CJE=0 CJC=0 TF=0 TR=0)`

- เป็น **model การเรียนการสอนที่กำหนดเอง** ไม่ใช่ transistor รุ่นใดรุ่นหนึ่ง
- `BF=100` ใกล้ β ของ analytical แต่ `IS/VAF` ทำให้ VBE และ Early effect ต่างจาก
  สมการ β/VBE คงที่ของ `dc_bias.py`
- `CJE=CJC=TF=TR=0` → small-signal ไม่มี capacitance ของทรานซิสเตอร์;
  Bode ที่ได้จึงสะท้อน coupling capacitor เป็นหลัก (ต้องเขียนคำเตือนนี้ใน UI)

### 9.4 subprocess และ error handling

```python
cmd = [engine, "-b", "-o", "run.log", "circuit.cir"]   # ไม่มี -r (ดูหมายเหตุ 9.2)
subprocess.run(cmd, cwd=workdir, timeout=30, capture_output=True, text=True,
               shell=False, check=False)
```

- engine resolution ตามลำดับ: `NGSPICE_ENGINE` (env) → `shutil.which("ngspice_con")`
  → `shutil.which("ngspice")` → path install ที่ตรวจแล้ว
  (`%LOCALAPPDATA%\Programs\ngspice-47\Spice64\bin\ngspice_con.exe`);
  ถ้าไม่เจอ → `ENGINE_NOT_FOUND`
- **ใช้ `ngspice_con.exe` ก่อนเสมอ** — `ngspice.exe` เป็น GUI subsystem ทำให้
  `subprocess` ไม่รันจนเสร็จ/ไม่ได้ output
- `returncode != 0` → `RUN_FAILED` + แยก `stderr` มาพร้อม
- `TimeoutExpired` → `TIMEOUT`
- `run.log` ว่างหรือ parser ได้ 0 จุด → `EMPTY_OUTPUT`
- input ผิด → `INVALID_INPUT` (HTTP 400) ก่อนสร้าง netlist
- **ทุก error case ต้องคืน `result=None/series=None`** เพื่อล้างผลเก่าออกจากหน้า
- ใช้ temp directory ใหม่ต่อรัน (`tempfile.TemporaryDirectory`) ไม่เขียนทับของเดิม
- provenance ต้องระบุ path ของ engine ด้วย (ไม่ใช่แค่ version)

### 9.5 Parser (format ที่ตรวจจาก ngspice-47 จริง)

ตารางทุกแบบมีบรรทัดหัว `Index ...` และข้อมูลคั่นด้วย tab; อาจมี form feed (`\f`)
และหัวตารางซ้ำทุก ~60 แถว → parser ต้องข้ามบรรทัดที่แปลง float ไม่ได้ทั้งหมด

- `parse_op`: หาหัวตาราง `Index   v(base) ... vic#branch` แล้วอ่านแถวแรก →
  `vb = v(base)`, `ve = v(emi)`, `vc = v(col)`, `vce = vc - ve`,
  `ic_mA = vic#branch * 1000`
  (ค่าจริงที่ได้: `vb=1.949112`, `ve=1.289454`, `vc=9.189410`, `ic=1.277541 mA`)
- `parse_ac`: ngspice พิมพ์ **2 ตาราง** (vout แล้ว vin) แต่ละตารางมีคอลัมน์
  `Index frequency vdb(...) vp(...)` (frequency มาอัตโนมัติ) →
  จับคู่ตาม `frequency` → `gain_db = vdb_out - vdb_in`,
  **`phase_deg = degrees(vp_out - vp_in)` เพราะ `vp()` ออกเป็น radian**
  (ตรวจแล้ว: `vp(vout) = -3.13926 rad` ที่ 1 kHz ≈ −179.9°),
  `gain_abs = 10 ** (gain_db / 20)`
- `parse_tran`: อ่าน `time v(vin) v(vout)` → เก็บ tuple `(time_s, vin_v, vout_v)`;
  time step ไม่สม่ำเสมอ (adaptive) ต้องใช้ค่าจาก column ไม่ใช่เดาจาก `tstep`
- `-3 dB`: หา midband = `max(gain_db)` ใน sweep แล้วหาจุดที่ตัด `midband - 3`;
  ถ้าไม่มีจุดตัด → UI แสดง **"not determined in sweep range"** ห้ามแต่งตัวเลข

## 10. หน้า `GET /simulator` และ `POST /simulate`

### 10.1 ฟอร์ม (ไม่มี JavaScript)

| field | ประเภท | ค่าเริ่มต้น | หน่วยที่โชว์ | validation |
|---|---|---|---|---|
| `analysis` | radio/link tab | `dc` | — | dc/ac/tran เท่านั้น |
| `vcc` | number | `12` | V | `0 < vcc ≤ 24` |
| `r1`,`r2`,`rc`,`re` | number + select unit | `100,22,2.2,1` kΩ | Ω/kΩ/MΩ | `0 < R ≤ 10 MΩ` |
| `amplitude_mv` | number | `10` | mV peak | `1 ≤ amp ≤ 100 mV` |
| `frequency_khz` | number | `1` | kHz | `0.1 ≤ f ≤ 100 kHz` |

ปุ่ม/section ทั้งหมดใช้ `<form method="post" action="/simulate">` และ
`<a href="/simulator?analysis=...">` สำหรับเลือกโหมด (GET link ไม่ใช้ JS)

### 10.2 ส่วนแสดงผล

1. **Run status badge**: `SUCCESS` (เขียว) หรือ error status (แดง/เหลือง)
2. **Provenance strip**:
   `Engine: ngspice <version> · Analysis: .op/.ac/.tran · Model: QNPN(simple) ·
   Run: <timestamp> · netlist/log: <path>`
3. **DC panel**: ตาราง VB/VE/VC/VCE/IC พร้อมหน่วย V/mA
4. **AC panel**: SVG Bode — freq axis (log, Hz), gain (dB), phase (°), legend
5. **Transient panel**: SVG waveform — time (ms), voltage (V), Vin เทาเขียว /
   Vout สีส้ม, บอกทิศทางกลับเฟส
6. **Analytical reference panel** (แยกชัดเจน):
   `dc_bias.py · β=100 · VBE=0.70 V · no Early effect · NOT a SPICE result`
7. **Warning panel**: cutoff/saturation จาก analytical หรือ “not determined in sweep range”

### 10.3 HTTP behavior

- `GET /simulator` → 200, ฟอร์มเปล่า/ค่าเริ่มต้น
- `POST /simulate` input ผิด → 400, แจ้งชื่อช่อง, `result=None`
- `POST /simulate` engine/run fail → 200, แจ้ง status, `result=None`
- `POST /simulate` success → 200, แสดงผล + กราฟจาก `SimResult`

## 11. แผนการทดสอบ

### 11.1 Unit (`tests/test_spice_engine.py`)

- `build_netlist` มี directive ตรงตาม analysis, ไม่มี `.control`
- ค่าที่ inject เช่น `"100k; .op"` ถูกปฏิเสธก่อนสร้าง netlist
- `parse_op/parse_ac/parse_tran` อ่าน fixture ที่เป็น **log ตัวอย่างสำหรับเทส parser**
  (ติดป้ายว่าไม่ใช่หลักฐานผล ngspice)
- error path: engine ไม่มี / returncode ≠ 0 / log ว่าง → status ถูกต้อง
- 20 tests เดิมของ Lab 03 ต้องผ่านเหมือนเดิม

### 11.2 Browser acceptance B1–B8

| Case | สิ่งที่ต้องเห็น |
|---|---|
| B1 | เปิด `/` แล้ว Fixed/Emitter/Divider ยังให้ค่าเดิม (A1–A5) |
| B2 | `/simulator` → Run DC → มี VB/VE/VC/VCE/IC + version/model/status |
| B3 | เปลี่ยน `re` เดียว → operating point และ/หรือ gain เปลี่ยน |
| B4 | Run AC → แกน frequency/gain/phase มีหน่วย และข้อมูลมาจาก log จริง |
| B5 | Run tran @10 mV, 1 kHz → Vin/Vout ตามเวลา + บอกกลับเฟส |
| B6 | เปลี่ยน amplitude/frequency → waveform เปลี่ยน (ไม่ hard-code) |
| B7 | `re=0` หรือ engine หาย → error ชัด ไม่ค้างผล Success |
| B8 | desktop ~1280px + mobile ~390px ไม่ตัดปุ่ม/กราฟ |

บันทึกใน `docs/validation.md` แบบตาราง: Method / Input / Expected / Observed /
Evidence / PASS·FAIL·NOT RUN พร้อมระบุ ngspice version + model ที่ใช้จริง

## 12. การตรวจ Impeccable

1. ติดตั้ง Node.js → `npx impeccable install` (เลือก OpenCode + Project scope)
2. โหลด skill และรัน critique บน **URL ที่รันจริง** ไม่ใช่แค่ source
3. prompt ต้องย้ำ: preserve การคำนวณ/mode/plot data/หน่วย; แตะเฉพาะ UI
4. ตรวจ desktop/mobile ด้วย Browser tool; เก็บ before/after screenshot
5. ถ้าติดตั้งไม่สำเร็จ → บันทึก NOT Run ตรงไปตรงมา อย่าเคลมว่ใช้ skill แล้ว

## 13. ความเสี่ยงและการรับมือ

| ความเสี่ยง | การรับมือ |
|---|---|
| ngspice ไม่มีจริง | setup step + `ENGINE_NOT_FOUND`; ถ้าติดไม่ได้ บันทึก B2–B6 เป็น NOT RUN |
| ผล `.print` ต่างตาม version ngspice | ตรวจ version จริงก่อนเขียน parser; เก็บ log ตัวอย่างจากรันจริง |
| Python314 + Flask ติดตั้งไม่ได้เพราะ network | ใช้ path Python จริง (`py -3.14`) และ 기록 error |
| Node ไม่มี → Impeccable ใช้ไม่ได้ | ติดตั้ง Node ใน setup; ไม่งั้น NOT Run ตามข้อ 12 |
| ค่า SPICE ไม่ตรง analytical | คาดอยู่แล้ว; แยกป้าย + อธิบายสมมติฐาน ห้ามปรับให้เท่ากันเอง |
| agent เผลอ commit | `AGENTS.md` ย้ำ; stage ได้อย่างเดียว แล้วรายงานให้มนุษย์กด |

## 14. Acceptance mapping ตามใบงาน

| ใบงาน | ครอบด้วย |
|---|---|
| ความต่อเนื่อง Lab 3 (1) | B1 + 20 tests เดิม |
| การเชื่อม ngspice (3) | `spice_engine.py` + B2/B3/B7 + provenance |
| AC + Transient (2) | B4/B5/B6 + SVG จริง |
| UI + Impeccable (2) | ข้อ 12 + before/after |
| Browser Acceptance (1) | ตาราง B1–B8 ใน `docs/validation.md` |
| GitHub + Reproducibility (1) | README + commit โดยมนุษย์ |

## 15. สิ่งที่ต้องอนุมัติก่อนเขียนโค้ด

1. โครง `.model QNPN` และ `.print` directives ในข้อ 9.2–9.3
2. แยก route `/simulator` ออกจาก `/` (D3)
3. ขอบเขต no-JS / ไม่เพิ่ม dependency (D2)
4. ขั้น setup ติดตั้ง Flask + ngspice + Node (D4, D6)
5. หลังอนุมัติจะเขียน **implementation plan** แยกอีกไฟล์ก่อนแตะโค้ดจริง
