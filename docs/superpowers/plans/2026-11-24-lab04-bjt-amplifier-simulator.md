# BJT Amplifier Simulator v1 — Implementation Plan (Lab 04)

> **สำหรับ agentic worker:** ทำทีละ task ตาม checkbox ห้ามข้ามหน้า review
> Environment นี้ไม่มี Superpowers skill โหลดอยู่ ให้ยึด checkbox + gate ใน plan นี้เอง
> **ห้ามรัน `git commit` / `git push`** — agent stage/report ได้เท่านั้น มนุษย์กดเอง

**Goal:** ต่อยอด Flask app Lab 03 ให้รัน ngspice จริง `.op/.ac/.tran` สำหรับ CE Voltage Divider
อ้างอิง 1 วงจร โดยไม่ทำให้ DC Bias 3 โหมดเดิมเสีย และไม่ใช้ JavaScript/mock data

**Spec:** `docs/superpowers/specs/2026-11-24-lab04-bjt-amplifier-simulator-design.md`

**Tech stack:** Python 3.14.2, Flask 3.x, `unittest`, stdlib (`subprocess`, `tempfile`, `html`)

**Architecture:** `app.py` เป็น presentation + dispatch; `spice_engine.py` เป็น adapter บริสุทธิ์
(ไม่ import Flask); `dc_bias.py` ไม่ถูกแก้; template render SVG จากข้อมูลจริง

> **Update record (2026-11-24, final state):** plan ด้านล่างเป็นบันทึกการสร้าง v1 ตามลำดับเดิม
> ผู้ขอภายหลังให้ **redesign เป็น 3 blocks** จึงมีสิ่งที่ **supersede** รายละเอียดใน Task 3–5 ดังนี้
> (รายละเอียดและหลักฐานอยู่ใน `docs/validation.md` §9.5–9.6):
> - หน้า `/simulator` มีบล็อกเกริ่นนำบนสุด `CE Amplifier Lab: DC Bias / AC / Transient`
>   ตามด้วย `<h2>` ลำดับ `1 Circuit & Parameters`, `2 Simulation & Plots`,
>   `3 Engineering Results`; **ตัด** analytical reference และ netlist/engine log ออกทั้งหมด
> - radio `DC` / `AC` / `Transient` แทน GET-tab เดิม (`form="sim-form"`); สลับได้ไม่ reload/ล้างผล
> - ปุ่ม `Run simulation` ครั้งเดียวเรียก `run_all_for_request()` รัน `.op/.ac/.tran` จริง
>   แล้ว render 2 plots (`Bode response (illustrative)`, `Input/Output waveforms (illustrative)`)
>   + 3 tables (`DC Operating Point`, `AC Frequency Response`, `Transient Response`)
> - `RL` แก้ได้; resistor Ω/kΩ/MΩ, source mV/V + Hz/kHz/MHz ตามตาราง `UNIT`;
>   ยังรับ `amplitude_mv` / `frequency_khz` แบบเก่าเป็น fallback
> - schematic ใหม่เป็น **BJT voltage-divider common-emitter** (สัญลักษณ์ NPN ในวงกลมเล็ก,
>   ตัวต้านทานเป็นกล่องอิมพิแดนซ์, มีลูกศรที่ Vin, R1/R2 divider, RC, RE, CIN/COUT, RL,
>   rail VCC สั้นจาก R1 ถึง RC) **แสดงเฉพาะชื่ออุปกรณ์ ไม่มีตัวเลข** (อัปเดตทุกครั้งที่พิมพ์
>   ทำไม่ได้เพราะห้ามใช้ JS ฝั่ง client; ค่าในฟอร์มยังมีผลหลังกด Run)
> - `spice_engine.py` มี `find_ngspice_engine()` ค้น path จริงในเครื่อง
>   (`%LOCALAPPDATA%\Programs\ngspice-47\Spice64\bin\ngspice_con.exe`) และหน้าเว็บแสดง path นั้น
>   (`NGSPICE_ENGINE` ยัง override ได้รวมตั้งค่าผิดเพื่อจำลอง `ENGINE_NOT_FOUND`)
> - ชุดทดสอบสุดท้าย **`Ran 62 tests ... OK`** (20 เดิม + 42 ของ Lab 04); B1–B8 ตรวจซ้ำแล้ว
> - ไม่มี `<script>`, ไม่มี dependency ใหม่, Lab 03 `GET /` และ `POST /calculate` ไม่เปลี่ยน,
>   agent ไม่ commit/stage/push

---

## Global Constraints

- ใช้ `$PY = 'C:\Program Files\Python314\python.exe'` (อย่าใช้ `python` ที่เป็น Store alias)
- ใช้ `$GIT = "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"` เมื่อต้องเช็ก git
- `requirements.txt` **ไม่เพิ่ม** dependency (Flask เท่านั้น)
- ไม่มี `<script>`, `onclick=`, `fetch` ใน template
- ไม่ใช้ `shell=True`; command เป็น list; มี `timeout`; workdir เป็น temp ใหม่ต่อรัน
- ข้อความ UI/error ใช้ **อังกฤษนำ ไทยในวงเล็บ**
- ผล SPICE กับผล analytical ต้องคนละป้ายเสมอ **(เดิม; ภายหลังตัดส่วน analytical ออกจากหน้า ตาม update record)**
- ทุก error ต้องคืน `result=None` / series `None` — ห้ามโชว์ผลเก่าพร้อม Success
- 20 tests เดิม (`tests/test_dc_bias.py` + `tests/test_web.py`) ต้องผ่านทุก task

## Review Focus

- `re=0`, `r1=abc`, `frequency=0`, `amplitude` ติดเครื่องหมาย `;` → ต้อง 400 ก่อนสร้าง netlist
- ngspice ไม่มี / returncode ≠ 0 / log ว่าง / timeout → status ถูกต้อง ไม่หลุดเป็น 500
- เปลี่ยน `re` → DC/AC เปลี่ยน; เปลี่ยน amplitude/frequency → waveform เปลี่ยน
- Bode มีแกน log frequency + gain dB + phase; waveform มี time(ms) + V(Vin/Vout)
- `-3 dB` หาไม่เจอ → ข้อความ "not determined in sweep range" (ห้ามแต่งเลข)
- `/` เดิมยังเปิดได้และให้ค่า A1–A5 เหมือนเดิม

---

## Task 0 — Preflight, setup และขยายขอบเขต AGENTS.md

**Files:**
- EDIT: `AGENTS.md`
- READ-ONLY: `requirements.txt`, `docs/design-note.md`, `docs/validation.md`

**Interfaces:**
- Produces: environment ที่ทดสอบได้จริง + กติกาที่อนุญาต SPICE เฉพาะ Lab 04

- [x] **Step 0.1 — ยืนยัน baseline** ✅ 2026-11-24

Observed: `## main...origin/main`, commit `fcdee8d add unit`, มีไฟล์ spec/plan ใหม่เป็น `??`

- [x] **Step 0.2 — ติดตั้ง Flask ใน Python จริง** ✅ 2026-11-24

Observed: `Python 3.14.2`, Flask `3.1.3` ติดตั้งสำเร็จ (user site),
`Ran 20 tests ... OK`

- [x] **Step 0.3 — หา/ติดตั้ง ngspice และบันทึก version** ✅ 2026-11-24

winget ไม่มีแพ็กเกจ; SourceForge เจอ Cloudflare challenge → ใช้ Chocolatey nupkg
`https://community.chocolatey.org/api/v2/package/ngspice/47.0.0` (13.8 MB) แตกด้วย `tar`
ได้ `Spice64/bin/ngspice_con.exe` + `ngspice.exe`

Observed version: `** ngspice-47 : Circuit level simulation program ... **`
(จาก `ngspice_con.exe -v`; `ngspice.exe --version` ไม่มี output เพราะเป็น GUI binary)

Smoke test `.op/.ac/.tran` ผ่าน พบข้อต้องแก้ 4 อย่าง:

1. `-r` ทำให้ `.print` ถูกข้าม → ตัด `-r` ออกจาก cmd
2. `.print ac freq ...` → `can't parse 'freq'`; ใช้ `.print ac vdb(vout) vp(vout) ...`
3. `.tran 0 tstop 0 tstep` → `TSTEP is invalid`; ใช้ `.tran tstep tstop 0 tstep`
4. `vp()` ออกเป็น **radian** (−3.13926 ที่ 1 kHz) → ต้องแปลงเป็นองศาใน `parse_ac`

record path/version/ผล smoke ลง `docs/validation.md` (Task 4 จะเติมตาราง B1–B8)

**Gate ผ่าน:** มี engine จริงพร้อมรันแล้ว → เดินหน้า Task 1 ได้

- [x] **Step 0.4 — ติดตั้ง Node + Impeccable** ✅ 2026-11-24

Observed: `node v26.13.1`, `npx 11.20.0` (zip binary ใน
`%LOCALAPPDATA%\Programs\node-v26.13.1-win-x64`)
winget **ล้มเหลว** (exit 1602: UAC) → ใช้ zip แทน
`npx impeccable install --yes --providers=opencode --scope=project` สำเร็จ →
`.opencode/` + engine `v0.1.27` (windows-x64) ติดตั้งแล้ว
ใช้ critique จริงใน Task 5 หลังมีหน้า `/simulator`

- [x] **Step 0.5 — อัปเดต `AGENTS.md`** ✅ 2026-11-24 (ข้อความด้านล่างเป็นสิ่งที่เขียนจริง)

เปลี่ยนหัวข้อ 1 จาก “งานนี้เป็น DC Bias … Lab 03” เป็น:

```
งานนี้คือ Flask Web App เดิมของ Lab 03 + Lab 04 Amplifier Simulator v1
- Lab 03: DC Bias 3 โหมด (Fixed/Emitter/Divider) — ห้ามลบ ห้ามแก้สมการ
- Lab 04: SPICE เฉพาะ CE Voltage Divider อ้างอิง 1 วงจร ผ่าน spice_engine.py
```

เพิ่มกติกา:

```
- spice_engine.py ห้าม import Flask; รับเฉพาะค่าที่ validate แล้ว
- ห้าม shell=True / ห้ามต่อข้อความจากฟอร์มเข้า netlist โดยตรง
- ห้ามฮาร์ดโค้ดผล ngspice/กราฟใน template; ต้องมาจาก SimResult
- ผล SPICE กับผล dc_bias.py ต้องมีป้ายแยกกันเสมอ
- agent ห้าม commit/push (คงเดิม)
```

- [ ] **Step 0.6 — Human commit (ถ้าต้องการแยก)**

Summary: `Update project scope for Lab 04 simulator`
→ มนุษย์กดใน GitHub Desktop (agent ห้ามกด)

---

## Task 1 — `spice_engine.py`: validation, netlist, engine probe

**Files:**
- CREATE: `spice_engine.py`
- CREATE: `tests/test_spice_engine.py`

**Interfaces:**
- Consumes: ค่าจากฟอร์มที่ `app.py` จะส่งมา (ยังไม่มี route ตอนนี้)
- Produces: `SimInput`, `SimResult`, `ValidationError`, `validate_sim_input()`,
  `build_netlist()`, `engine_version()`, `_fmt()`

- [x] **Step 1.1 — เขียน failing tests ก่อน** ✅ 2026-11-24 (`tests/test_spice_engine.py`, 12 tests)

`tests/test_spice_engine.py` (เฉพาะส่วนนี้ก่อน):

```python
import math
import unittest
from spice_engine import ValidationError, validate_sim_input, build_netlist, _fmt

BASE = {
    "vcc": "12", "r1": "100", "r1_unit": "kohm", "r2": "22", "r2_unit": "kohm",
    "rc": "2.2", "rc_unit": "kohm", "re": "1", "re_unit": "kohm",
    "amplitude_mv": "10", "frequency_khz": "1",
}

class TestValidate(unittest.TestCase):
    def test_valid(self):
        params, errors = validate_sim_input(BASE)
        self.assertEqual(errors, [])
        self.assertAlmostEqual(params.vcc, 12.0)
        self.assertAlmostEqual(params.r1, 100_000.0)
        self.assertAlmostEqual(params.amplitude_v, 0.010)
        self.assertAlmostEqual(params.frequency_hz, 1_000.0)

    def test_zero_re_rejected(self):
        _, errors = validate_sim_input(dict(BASE, re="0"))
        self.assertTrue(any("RE" in e for e in errors))

    def test_injection_rejected(self):
        for key in ("amplitude_mv", "frequency_khz", "vcc"):
            _, errors = validate_sim_input(dict(BASE, **{key: "10; .op"}))
            self.assertTrue(errors)

    def test_out_of_range(self):
        _, errors = validate_sim_input(dict(BASE, frequency_khz="0"))
        self.assertTrue(errors)

class TestNetlist(unittest.TestCase):
    def setUp(self):
        self.params, _ = validate_sim_input(BASE)

    def test_dc_directives(self):
        net = build_netlist(self.params, "dc")
        self.assertIn(".op", net)
        self.assertIn(".print op v(base) v(col) v(emi) i(vic)", net)
        self.assertIn(".MODEL QNPN", net)
        self.assertNotIn(".control", net)

    def test_ac_directives(self):
        net = build_netlist(self.params, "ac")
        self.assertIn(".ac dec 20 1 1Meg", net)
        self.assertIn(".print ac vdb(vout) vp(vout) vdb(vin) vp(vin)", net)
        self.assertNotIn("freq vdb", net)      # ngspice-47: can't parse 'freq'
        self.assertNotIn(".op", net)

    def test_tran_directives(self):
        net = build_netlist(self.params, "tran")
        # 1 kHz -> tstop = 5 ms (clamped), tstep = 10 us; TSTEP ต้อง > 0
        self.assertIn(".tran 1e-05 0.005 0 1e-05", net)
        self.assertNotIn(".tran 0 ", net)
        self.assertIn(".print tran time v(vin) v(vout)", net)
        self.assertIn("SIN(0 0.01 1000)", net)

    def test_unknown_analysis(self):
        with self.assertRaises(ValidationError):
            build_netlist(self.params, "foobar")

    def test_fmt_is_finite(self):
        self.assertEqual(_fmt(100_000.0), "100000")
        with self.assertRaises(ValidationError):
            _fmt(float("inf"))
```

- [x] **Step 1.2 — รันให้เห็น FAIL** ✅ Observed: `ModuleNotFoundError: No module named 'spice_engine'`

```powershell
& $PY -m unittest tests.test_spice_engine -v
```

Expected: `ModuleNotFoundError: No module named 'spice_engine'`

- [x] **Step 1.3 — เขียน `spice_engine.py` ส่วน validation/netlist** ✅ 2026-11-24 (`spice_engine.py` สร้างแล้ว; `engine_version()` probe ได้ `ngspice-47` จริง)

โครงที่ต้องมี:

```python
from dataclasses import dataclass
import math

UNIT = {"ohm": 1.0, "kohm": 1_000.0, "mohm": 1_000_000.0}

class ValidationError(ValueError): ...

@dataclass(frozen=True)
class SimInput:
    vcc: float; r1: float; r2: float; rc: float; re: float
    amplitude_v: float; frequency_hz: float

@dataclass(frozen=True)
class SimResult:
    analysis: str; status: str; message: str
    netlist: str; log_excerpt: str
    values: dict | None
    ac_points: tuple | None
    tran_points: tuple | None
    provenance: dict

def _fmt(x: float) -> str: ...           # f"{x:.6g}", กัน inf/nan
def _number(raw, label, errors, lo, hi, scale=1.0) -> float | None: ...
def _resistance(raw, unit, label, errors) -> float | None: ...
def validate_sim_input(raw: dict[str,str]) -> tuple[SimInput|None, list[str]]: ...
def build_netlist(params: SimInput, analysis: str) -> str: ...
def engine_version(engine: str) -> str: ...
```

กติกา:
- `_number`: `float(str(raw).strip())`, กัน `inf/nan`, ตรวจ `lo ≤ x ≤ hi`,
  คูณ `scale` ก่อนคืน (amplitude mV→V, frequency kHz→Hz)
- `_resistance`: ใช้ตาราง `UNIT`, กัน unit ผิด และค่า ≤ 0
- ทุก error เป็นสองภาษาและระบุชื่อช่อง เช่น
  `RE must be greater than 0 Ω (RE ต้องมากกว่า 0 Ω)`
- `build_netlist` ใส่เฉพาะ directive ของ analysis ที่เลือก; ที่เหลือเป็น comment
- title เป็น ASCII (`* CE voltage-divider reference - ENG29 2121 Lab 04`) — em dash ถูกแปลงเป็น `?` ใน log
- ห้ามรับสตริงดิบเข้า netlist — ทุกค่าผ่าน `_fmt()` แล้วเท่านั้น
- `tstop = min(5 / frequency_hz, 0.05)`, `tstep = tstop / 500`
- `.tran {tstep} {tstop} 0 {tstep}` (TSTEP ต้อง > 0); `.print ac` ห้ามมี `freq`
- model line ต้องตรงตาม spec ทุกตัวอักษร

- [x] **Step 1.4 — รัน tests ให้ผ่าน** ✅ Observed: `Ran 32 tests ... OK` (12 ใหม่ + 20 เดิม)

```powershell
& $PY -m unittest tests.test_spice_engine tests.test_dc_bias tests.test_web -v
```

Expected: ผ่านทั้งหมด (20 เดิม + ชุดใหม่)

- [ ] **Step 1.5 — Human commit**

Summary: `Add CE netlist builder and input validation for Lab 04`

---

## Task 2 — `spice_engine.py`: subprocess, parser, SVG

**Files:**
- EDIT: `spice_engine.py`
- EDIT: `tests/test_spice_engine.py`
- CREATE (optional): `tests/fixtures/parser_sample.log`

**Interfaces:**
- Consumes: `SimInput`, `build_netlist` จาก Task 1
- Produces: `run_analysis()`, `parse_op()`, `parse_ac()`, `parse_tran()`,
  `svg_bode()`, `svg_waveform()`

- [x] **Step 2.1 — เขียน failing tests สำหรับ parser** ✅ 2026-11-24 (เพิ่ม parser/run/SVG tests รวม 11 ตัว)

```python
class TestParsers(unittest.TestCase):
    def test_parse_op_real_table_format(self):
        log = ("Index   v(base)         v(col)          v(emi)          vic#branch\n"
               "---------------------------------------------------------------\n"
               "0\t1.949112e+00\t9.189410e+00\t1.289454e+00\t1.277541e-03\n")
        d = parse_op(log)
        self.assertAlmostEqual(d["vb"], 1.949112)
        self.assertAlmostEqual(d["vce"], 9.189410 - 1.289454, places=6)
        self.assertAlmostEqual(d["ic_mA"], 1.277541)

    def test_parse_ac_radians_to_degrees(self):
        # ngspice พิมพ์ 2 ตาราง (vout แล้ว vin); vp() เป็น radian (-pi ~ -180 deg)
        log = ("Index   frequency       vdb(vout)       vp(vout)\n"
               "0\t1.000000e+03\t4.859789e+00\t-3.139260e+00\n"
               "Index   frequency       vdb(vin)        vp(vin)\n"
               "0\t1.000000e+03\t0.000000e+00\t0.000000e+00\n")
        pts = parse_ac(log)
        self.assertAlmostEqual(pts[0][0], 1000.0)
        self.assertAlmostEqual(pts[0][1], 4.859789)
        self.assertAlmostEqual(pts[0][2], -179.9, places=1)   # degrees

    def test_parse_tran(self):
        log = ("Index   time            v(vin)          v(vout)\n"
               "0\t0.000000e+00\t1.0000e-02\t-1.0000e-01\n"
               "1\t1.0000e-04\t1.0000e-02\t-1.0000e-01\n")
        pts = parse_tran(log)
        self.assertEqual(len(pts), 2)
        self.assertAlmostEqual(pts[0][0], 0.0)

    def test_empty_log(self):
        with self.assertRaises(EmptyOutputError):
            parse_op("")
```

> **หมายเหตุสำคัญ:** fixture ในข้อสอบนี้เป็น **parser unit test เท่านั้น**
> ห้ามนำไปแสดงว่าเป็นผล ngspice จริง; หลัง Task 3 ต้องรันจริงแล้วเก็บ log จริงใส่ `docs/validation.md`

- [x] **Step 2.2 — รันให้เห็น FAIL แล้ว implement parser** ✅ Observed: `ImportError: cannot import name 'EmptyOutputError'` → implement แล้วผ่าน

```python
class EmptyOutputError(RuntimeError): ...
class RunFailedError(RuntimeError): ...
class EngineNotFoundError(RuntimeError): ...
class TimeoutError_(RuntimeError): ...
```

parser อ่านเฉพาะบรรทัดที่แปลงเป็น float ได้ (ข้าม header/comment/`Index`/form feed),
คืน tuple ของ float; ถ้าได้ 0 จุด → `EmptyOutputError`
`parse_ac` จับคู่ตาราง vout/vin ตาม frequency, คำนวณ
`gain_db = vdb_out - vdb_in`, `phase_deg = degrees(vp_out - vp_in)` (**vp เป็น radian**),
`gain_abs = 10 ** (gain_db / 20)`
`parse_tran` ใช้ time จาก column เสมอ (adaptive step)

- [x] **Step 2.3 — implement `run_analysis()`** ✅ พร้อม `resolve_engine()`, error status 5 แบบ, provenance ครบ

```python
def run_analysis(params, analysis, workdir, engine):
    net = build_netlist(params, analysis)
    (workdir / "circuit.cir").write_text(net, encoding="utf-8")
    cmd = [engine, "-b", "-o", "run.log", "circuit.cir"]   # ห้ามใส่ -r
    proc = subprocess.run(cmd, cwd=workdir, timeout=30, capture_output=True,
                          text=True, shell=False, check=False)
    ...
    return SimResult(...)
```

status mapping:
| เงื่อนไข | status |
|---|---|
| หา engine ไม่เจอ (env → `ngspice_con` → `ngspice` → known path) | `ENGINE_NOT_FOUND` |
| `TimeoutExpired` | `TIMEOUT` |
| `returncode != 0` | `RUN_FAILED` |
| log ว่าง / parser ได้ 0 จุด | `EMPTY_OUTPUT` |
| success | `SUCCESS` |

`provenance` ต้องมี: `engine_path`, `engine_version`, `model`, `analysis_directive`,
`timestamp`, `netlist_path`, `log_path`

engine ที่ใช้จริงในเครื่องนี้:
`C:\Users\B6837020\AppData\Local\Programs\ngspice-47\Spice64\bin\ngspice_con.exe`
(ห้ามเลือก `ngspice.exe` ก่อน — GUI subsystem ไม่คืน output ให้ subprocess)

- [x] **Step 2.4 — implement SVG helpers (stdlib ล้วน)** ✅ `svg_line_chart/svg_bode/svg_waveform/find_low_cutoff`

```python
def svg_line_chart(series, x_label, y_label, *, log_x=False, height=320, width=760) -> str
def svg_bode(ac_points) -> str      # 2 panels: gain dB + phase, freq log
def svg_waveform(tran_points) -> str# time ms vs Vin/Vout
```

- escape ข้อความด้วย `html.escape` ก่อนใส่ `<text>`
- แกนมีขีด/ตัวเลข/หน่วยครบ; Bode แกน X เป็น log decade; waveform มี legend
- ถ้า series ว่าง → คืนข้อความ “No data” (ไม่คืนกราฟปลอม)
- `-3 dB`: `midband = max(gain_db)`; หา crossing ของ `midband - 3`;
  ถ้าไม่มี → `None` และ UI แสดง "not determined in sweep range"

- [x] **Step 2.5 — ทดสอบกับ ngspice จริง (gate)** ✅ 2026-11-24
  Observed: DC `vb=1.949112, ve=1.289454, vc=9.189410, ic=1.277541 mA`;
  AC 121 points, @1 kHz `gain=4.8598 dB, phase=-179.87°`, `f_c≈1.83 Hz`;
  TRAN 508 points. `Ran 23 tests ... OK` (23 = spice_engine เดี่ยว)

```powershell
& $PY -m unittest tests.test_spice_engine -v
```

จากนั้นรัน netlist ตัวอย่างด้วย ngspice ที่ติดตั้งใน Task 0 และอ่าน `run.log` ด้วยตา
ต้องเห็นค่า VB/VE/VC/IC ที่สมเหตุสมผล (IC ~1 mA, VCE ~8 V ใกล้เคียง analytical)
ถ้า parser ไม่ตรง format → แก้ parser ก่อนไป Task 3

- [ ] **Step 2.6 — Human commit**

Summary: `Add ngspice subprocess adapter, result parsers and SVG charts`

---

## Task 3 — Flask routes + simulator template

**Files:**
- EDIT: `app.py` (เพิ่ม import + 2 route **ท้ายไฟล์** ห้ามแก้ `/` และ `/calculate`)
- CREATE: `templates/simulator.html`
- EDIT: `templates/index.html` (เพิ่มลิงก์ไป `/simulator` เท่านั้น)
- EDIT: `static/style.css` (class ใหม่ขึ้นต้น `sim-`)
- CREATE: `tests/test_simulator_web.py`

**Interfaces:**
- Consumes: `spice_engine.*`
- Produces: `GET /simulator`, `POST /simulate`, หน้าที่แสดงผลจริง

- [x] **Step 3.1 — เขียน failing tests** ✅ 2026-11-24 (`tests/test_simulator_web.py`; เห็น 404/FAIL ก่อน implement)

```python
import unittest
from unittest.mock import patch
from app import app

VALID = {
    "analysis": "dc", "vcc": "12",
    "r1": "100", "r1_unit": "kohm", "r2": "22", "r2_unit": "kohm",
    "rc": "2.2", "rc_unit": "kohm", "re": "1", "re_unit": "kohm",
    "amplitude_mv": "10", "frequency_khz": "1",
}

class TestSimulatorPage(unittest.TestCase):
    def setUp(self): self.client = app.test_client()

    def test_get(self):
        r = self.client.get("/simulator")
        self.assertEqual(r.status_code, 200)
        self.assertIn('name="analysis"', r.get_data(as_text=True))

    def test_invalid_returns_400_and_no_result(self):
        r = self.client.post("/simulate", data=dict(VALID, re="0"))
        self.assertEqual(r.status_code, 400)
        self.assertIn("RE", r.get_data(as_text=True))
        self.assertNotIn("ENGINE", r.get_data(as_text=True))

    @patch("app.run_analysis_for_request")
    def test_success_renders_values_and_svg(self, run):
        run.return_value = FakeSuccessResult()   # กำหนดในเทสต์
        r = self.client.post("/simulate", data=VALID)
        self.assertEqual(r.status_code, 200)
        body = r.get_data(as_text=True)
        self.assertIn("<svg", body)
        self.assertIn("ngspice", body)
        self.assertIn("SUCCESS", body)

    @patch("app.run_analysis_for_request")
    def test_engine_fail_clears_old_result(self, run):
        run.return_value = FakeFailResult()
        r = self.client.post("/simulate", data=VALID)
        body = r.get_data(as_text=True)
        self.assertIn("ENGINE_NOT_FOUND", body)
        self.assertNotIn("SUCCESS", body)
```

- [x] **Step 3.2 — implement route ใน `app.py`** ✅ `/simulator` + `/simulate` ต่อท้าย; `/` และ `/calculate` ไม่ถูกแก้

```python
from spice_engine import validate_sim_input, run_analysis, engine_version, svg_bode, svg_waveform
import tempfile
from pathlib import Path

def run_analysis_for_request(params, analysis):
    with tempfile.TemporaryDirectory() as d:
        return run_analysis(params, analysis, Path(d), ENGINE_PATH)

@app.get("/simulator")
def simulator(): ...        # 200, form กับค่าเริ่มต้น

@app.post("/simulate")
def simulate(): ...
```

- รับฟอร์มด้วย `request.form.get(name, "")` ทุกฟิลด์
- `validate_sim_input` ก่อน → ถ้า error ให้ render พร้อม HTTP 400 และ `result=None`
- success/fail จาก engine → render status + provenance; **fail ต้อง `result=None`**
- แปลง `SimResult` เป็น context: `dc_values`, `bode_svg`, `wave_svg`,
  `analytical` (เรียก `calculate_dc_bias` เฉพาะกรณี DC เพื่อแสดง reference แยก)

- [x] **Step 3.3 — เขียน `templates/simulator.html`** ✅ no-JS form/status/provenance/DC table/Bode/waveform/analytical/netlist-log

ต้องมี:
- `<form method="post" action="/simulate">` และลิงก์ `?analysis=dc|ac|tran`
- radio/select `analysis` + ช่อง `vcc`, `r1..re` พร้อม unit select,
  `amplitude_mv`, `frequency_khz`
- error list, status badge, provenance strip
- DC table (VB/VE/VC/VCE/IC) เฉพาะเมื่อ `result` มีค่า
- `{{ bode_svg|safe }}` / `{{ wave_svg|safe }}` เฉพาะเมื่อมี serie จริง
- analytical panel ที่มีข้อความ `NOT a SPICE result`
- ไม่มี `<script>` / `onclick` / `fetch`

- [x] **Step 3.4 — ปรับ CSS และลิงก์จากหน้าเดิม** ✅ `.sim-*` responsive + ลิงก์ใน header ของ `index.html` เท่านั้น

- `static/style.css`: `.sim-*` classes, responsive 2 column → 1 column ใต้ 760px
- `templates/index.html`: เพิ่ม `<a href="{{ url_for('simulator') }}">Lab 04 Simulator</a>`
  ใน header **เท่านั้น** (ห้ามแก้ฟอร์ม/สมการ/ชื่อ field)

- [x] **Step 3.5 — รันชุดทดสอบทั้งหมด** ✅ ตอนนี้ `Ran 62 tests ... OK` (20 เดิม + 42 Lab 04; เดิม 52 ตอน v1)

```powershell
& $PY -m unittest discover -s tests -v
```

Expected: 20 เดิมผ่าน + ชุดใหม่ผ่าน; `GET /` ยังให้ค่าเดิม

- [x] **Step 3.6 — ทดสอบด้วยตา** ✅ ดูแลใน Task 4 ด้วย OpenCode Browser แล้ว

```powershell
& $PY -m flask --app app run --debug
```

เปิด `http://127.0.0.1:5000/simulator` → Run DC → ตัวเลขและ netlist/log ปรากฏ

- [ ] **Step 3.7 — Human commit**

Summary: `Add CE simulator route, form and server-rendered result page`

---

## Task 4 — Browser acceptance B1–B8

**Files:**
- EDIT: `docs/validation.md`
- CREATE: `docs/screenshots/lab04-*.png`

- [x] **Step 4.1 — เตรียมตารางเปล่าใน `docs/validation.md`** ✅ filled เป็นหัวข้อ 9.4–9.5 แล้ว

คอลัมน์: `Case | Method | Input | Expected/Reference | Observed | Evidence | Status`
พร้อมบรรทัดระบุ `ngspice version`, `model QNPN`, `path engine`, วันที่ทดสอบ

- [x] **Step 4.2 — ตรวจ B1 (regression)** ✅ OpenCode Browser, Divider/Fixed/Emitter ได้ค่าตามเดิมทุกโหมด

เปิด `/` → Fixed/Emitter/Divider → ใส่ชุด A1–A5 → ต้องได้ค่าเดิม

- [x] **Step 4.3 — ตรวจ B2/B3 (DC + เปลี่ยน RE)** ✅ VB 1.949 → 2.048 V, IC 1.278 → 0.696 mA

Run DC ที่ `/simulator` → บันทึก VB/VE/VC/VCE/IC + version/status
เปลี่ยน `re` เป็น `2 kΩ` → Run ซ้ำ → ต้องต่างจากรอบแรก

- [x] **Step 4.4 — ตรวจ B4/B5/B6 (AC/Transient/source)** ✅ 4.86 dB/−179.9°, 2 series, SIN เปลี่ยน

Run AC → ดูแกน frequency/gain/phase และ log
Run tran @10 mV, 1 kHz → ดู waveform Vin/Vout + บอกทิศทางกลับเฟส
เปลี่ยน amplitude/frequency → Run ซ้ำ → waveform ต้องเปลี่ยน

- [x] **Step 4.5 — ตรวจ B7 (invalid/fail)** ✅ 400 + RE error; ENGINE_NOT_FOUND ไม่มีผลเก่า

ใส่ `re=0` → 400 + ข้อความ RE
จำลอง engine ไม่พร้อม (หรือใช้ path ผิด) → status `ENGINE_NOT_FOUND` + ไม่มีผลเก่า

- [x] **Step 4.6 — ตรวจ B8 + ภาพ** ✅ Impeccable shot 1280×900/390×844, before/after PNG

เปิด desktop ~1280px และ mobile ~390px → ไม่ตัดปุ่ม/กราฟ
เก็บ screenshot อย่างน้อย: DC success, AC, transient, mobile, error

- [ ] **Step 4.7 — Human commit**

Summary: `Add Lab 04 browser acceptance results B1-B8`

---

## Task 5 — Impeccable critique → polish → audit

**Files:**
- EDIT เฉพาะ UI: `templates/simulator.html`, `static/style.css`
- CREATE: `docs/screenshots/lab04-ui-before.png`, `lab04-ui-after.png`

- [x] **Step 5.1 — เก็บ before screenshot** ✅ `lab04-simulator-desktop-1280x900.png`, `lab04-simulator-phone-390x844.png`

ก่อนแตะ CSS ให้ถ่ายหน้า `/simulator` desktop + mobile

- [x] **Step 5.2 — รัน critique บน URL จริง** ✅ Assessment A/B แยก sub-agent; Nielsen 25/40; detector 4 findings

```
Load the Impeccable skill.
Critique the running BJT CE simulator at http://127.0.0.1:5000/simulator.
This is an engineering tool for EE students, not a marketing page.
Preserve calculations, mode choices, plot data and units.
Prioritize input groups, graph legends, error states, responsive layout,
engine status and result provenance. Show the smallest useful plan; wait.
```

- [x] **Step 5.3 — อนุมัติแล้ว polish เฉพาะ UI** ✅ tab คงค่า, schematic, AC caveat/cutoff, error remedy, range hint

ห้ามแก้ `spice_engine.py`, `dc_bias.py`, หรือแทนที่กราฟด้วยภาพนิ่ง; อนุญาตแก้ `GET /simulator`
เฉพาะเพื่อส่งค่าฟอร์มกลับเมื่อสลับ tab (ไม่แตะ Lab 03 หรือสมการ/parser)

- [x] **Step 5.4 — audit + เก็บ after screenshot + rerun B1–B8 ย่อส่วนที่กระทบ** ✅ 15/20 Good; B1–B7 rerun ผ่าน

- [ ] **Step 5.5 — Human commit**

Summary: `Polish simulator UI after Impeccable review`

---

## Task 6 — Documentation และ publish

**Files:**
- EDIT: `README.md`, `docs/design-note.md`, `docs/validation.md`, `AGENTS.md` (ถ้าจำเป็น)
- READ: git diff ทั้งหมด

- [x] **Step 6.1 — อัปเดต `README.md`** ✅ path Python จริง, ngspice, `/simulator`, QNPN caveat, 62 tests, 3 blocks, engine path, schematic ใหม่

เพิ่ม: ใช้ `$PY` จริง, วิธีติดตั้ง ngspice, Node+Impeccable, วิธีรัน `/simulator`,
คำอธิบาย model QNPN ว่าเป็น model สำหรับการเรียนการสอน, และลิงก์ `docs/validation.md`

- [x] **Step 6.2 — อัปเดต `docs/design-note.md`** ✅ สรุป Lab 04 architecture/data flow/ข้อจำกัด

สรุป 1 หน้า: ทำไมแยก route ใหม่, ทำไม no-JS, ทำไม `.print` แทน raw binary,
ทำไมแยก SPICE กับ analytical

- [x] **Step 6.3 — ตรวจความสะอาด** ✅ ตรวจ `git status --short` / `diff --stat`; ไม่มี `.venv`, `.env`, credential

```powershell
& $GIT status --short
& $GIT diff --stat
```

ต้องไม่มี `.venv/`, `.env`, `__pycache__/`, token, หรือ log ขนาดใหญ่เกินจำเป็น
ถ้าจะเก็บ sample log ให้เก็บเฉพาะตัวอย่างสั้น + บอกวิธีสร้างซ้ำ

- [x] **Step 6.4 — รัน reproduction สั้น** ✅ `Ran 62 tests ... OK` (หลัง redesign)

```powershell
& $PY -m unittest discover -s tests -v
```

- [x] **Step 6.5 — รายงานให้มนุษย์กด commit/push** ✅ รายงานไฟล์/commit message ให้มนุษย์แล้ว; agent ไม่ commit/push ตาม AGENTS.md

agent ส่ง: รายการไฟล์, commit message ที่แนะนำ 3–5 ข้อความ, ผล test, และหมายเหตุ
"ยังไม่ได้ commit ตาม AGENTS.md"

---

## Self-Review

- **Spec coverage:** D1–D8 ครบ; `.op/.ac/.tran` มีทั้ง netlist/parser/UI; B1–B8 มี task รองรับ
- **Type consistency:** `SimInput`/`SimResult` ใช้ชื่อเดียวกันทุก task; หน่วย V/Ω/Hz สอดคล้อง
- **Regression:** `/` และ `/calculate` ไม่ถูกแก้; 20 tests เดิมรันทุก task
- **Provenance:** ทุก route success คืน version/model/status/log path; error ล้างผลเก่า
- **Safety:** ไม่มี shell=True, ไม่มี JS, ไม่เพิ่ม dependency, ไม่มี commit โดย agent
- **Honesty:** ถ้า ngspice/Impeccable ไม่พร้อม → NOT RUN ตรงไปตรงมา ไม่เคลม PASS
