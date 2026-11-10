# BJT DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง Flask Web App ที่รับค่า VCC, R1, R2, RC, RE, β, VBE แล้วคำนวณ DC Operating Point ของวงจร Voltage-Divider Bias ด้วย Python Backend พร้อม validation, region warnings และ automated tests

**Architecture:** Server-rendered POST + Jinja (Approach A). `dc_bias.py` เป็นฟังก์ชันบริสุทธิ์ไม่รู้จัก Flask; `app.py` ทำหน้าที่รับ HTTP, แปลงหน่วย, เรียกสมการ และ render template; `templates/index.html` แสดงผลอย่างเดียว

**Tech Stack:** Python 3.14, Flask 3.x, Jinja2, `unittest`, HTML/CSS (ไม่มี JavaScript)

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md`

## Global Constraints

- Python 3.14 (`python --version` → `Python 3.14.2`), Flask 3.x เท่านั้น — ไม่มี dependency อื่น
- ห้ามใช้ JavaScript ฝั่ง client; ผลลัพธ์ทุกตัวต้องมาจาก Python
- `dc_bias.py` ห้าม `import flask` หรืออ้างถึง HTML/HTTP
- เทสต์ใช้ `unittest` และรันด้วย `python -m unittest discover -s tests -v`
- พอร์ต 5000, เปิดด้วย `python -m flask --app app run --debug`
- ตัวต้านทานรับหน่วย `kohm` หรือ `ohm` จาก dropdown; แปลงเป็น Ω ก่อนคำนวณ
- Warning มี 2 สถานะเท่านั้น: `cutoff` (`VTH <= VBE`) และ `saturation` (`VCE < 0.3`)
- ค่าคงที่: `VCE_SAT = 0.3` V, `VBE_MIN = 0.0`, `VBE_MAX = 1.0`
- แสดงแรงดัน 3 ตำแหน่งทศนิยม, กระแสเป็น mA 3 ตำแหน่ง (IB แสดง µA ด้วย)
- Commit ทำผ่าน **GitHub Desktop** (ผู้ใช้กดเอง) — ไม่ใช้ `git commit` ในเทอร์มินัล
- **ภาษาของ UI: อังกฤษเป็นหลัก มีไทยในวงเล็บ** เช่น `VCE — Collector–Emitter Voltage (แรงดัน Collector–Emitter)`, `R1 must be greater than 0 (R1 ต้องมากกว่า 0)`, `Calculate DC Bias (คำนวณ DC Bias)` — ใช้กับ label, ปุ่ม, หัวข้อ, ข้อความ error และ warning ทั้งหมด
- ห้าม commit `.venv/`, `__pycache__/`, `.env`

## Review Focus

- `RE = 0` หรือ `RC = 0` → ต้องถูกปฏิเสธพร้อมชื่อช่อง (400) ไม่ใช่ 500 และไม่ทำให้เกิด `ZeroDivisionError`
- ช่องว่างหรือข้อความ เช่น `abc` ในช่องตัวเลข → 400 พร้อมชื่อช่องที่ผิด ไม่ใช่ 500
- `VBE <= 0` หรือ `VBE >= 1` → ปฏิเสธ (ถ้าปล่อยผ่านจะได้ผลลัพธ์ไร้ความหมายแต่ดูปกติ)
- `VTH <= VBE` (cutoff) → กระแสเป็น 0, มี warning, สถานะ HTTP ยังเป็น 200
- `β = 1` และ `β = 10000` → ผลลัพธ์เป็นจำนวนจำกัด ไม่ overflow และ region ยังถูกคำนวณ

---

### Task 1: Engineering core (`dc_bias.py`)

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: ไม่มี (task แรก)
- Produces:
  - `class BiasInputError(ValueError)`
  - `@dataclass(frozen=True) class BiasResult` มีฟิลด์ `vth, rth, ib, ic, ie, ve, vb, vc, vce` (float), `region: str`, `warnings: tuple[str, ...]`
  - `parse_resistance(raw: str, unit: str) -> float` — คืนค่าเป็น Ω, `unit` ∈ `{"ohm", "kohm"}`
  - `calculate_dc_bias(vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float) -> BiasResult` — ตัวต้านทานเป็น Ω, กระแสเป็น A

- [ ] **Step 1: สร้างไฟล์ตั้งต้นและ virtual environment**

`.gitignore`:
```
.venv/
__pycache__/
*.pyc
.env
```

`requirements.txt`:
```
Flask>=3.0,<4.0
```

รัน:
```
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
Expected: `Successfully installed Flask-3.x ...`

- [ ] **Step 2: เขียน failing tests**

`tests/test_dc_bias.py`:
```python
import unittest

from dc_bias import BiasInputError, calculate_dc_bias, parse_resistance

REF = dict(vcc=12, r1=100_000, r2=22_000, rc=2_200, re=1_000, beta=100, vbe=0.70)


class TestReferenceCase(unittest.TestCase):
    def test_reference_values(self):
        r = calculate_dc_bias(**REF)
        self.assertAlmostEqual(r.vth, 2.1639, places=3)
        self.assertAlmostEqual(r.rth, 18_032.8, delta=0.2)
        self.assertAlmostEqual(r.ib, 12.298e-6, delta=1e-9)
        self.assertAlmostEqual(r.ic, 1.2298e-3, delta=1e-7)
        self.assertAlmostEqual(r.ie, 1.2421e-3, delta=1e-7)
        self.assertAlmostEqual(r.ve, 1.2421, places=3)
        self.assertAlmostEqual(r.vb, 1.9421, places=3)
        self.assertAlmostEqual(r.vc, 9.2944, places=3)
        self.assertAlmostEqual(r.vce, 8.0523, places=3)
        self.assertEqual(r.region, "active")
        self.assertEqual(r.warnings, ())

    def test_beta_increases_ic_monotonically(self):
        low = calculate_dc_bias(vcc=12, r1=100_000, r2=22_000, rc=2_200, re=1_000, beta=50, vbe=0.7)
        high = calculate_dc_bias(vcc=12, r1=100_000, r2=22_000, rc=2_200, re=1_000, beta=200, vbe=0.7)
        self.assertGreater(high.ic, low.ic)
        self.assertLess(high.ic / low.ic, 4.0)  # sublinear: IC ไม่ proportional กับ β


class TestUnits(unittest.TestCase):
    def test_parse_kohm(self):
        self.assertAlmostEqual(parse_resistance("100", "kohm"), 100_000)

    def test_parse_ohm(self):
        self.assertAlmostEqual(parse_resistance("2200", "ohm"), 2_200)

    def test_unit_equivalence(self):
        a = calculate_dc_bias(vcc=12, r1=100_000, r2=22_000, rc=2_200, re=1_000, beta=100, vbe=0.7)
        b = calculate_dc_bias(vcc=12, r1=parse_resistance("100", "kohm"),
                              r2=parse_resistance("22", "kohm"), rc=2_200, re=1_000,
                              beta=100, vbe=0.7)
        self.assertAlmostEqual(a.vce, b.vce, places=9)

    def test_reject_text(self):
        with self.assertRaises(BiasInputError):
            parse_resistance("abc", "ohm")

    def test_reject_unknown_unit(self):
        with self.assertRaises(BiasInputError):
            parse_resistance("1", "Mohm")


class TestValidation(unittest.TestCase):
    def test_zero_resistance_rejected(self):
        with self.assertRaises(BiasInputError):
            calculate_dc_bias(vcc=12, r1=0, r2=22_000, rc=2_200, re=1_000, beta=100, vbe=0.7)

    def test_non_positive_beta_rejected(self):
        with self.assertRaises(BiasInputError):
            calculate_dc_bias(vcc=12, r1=100_000, r2=22_000, rc=2_200, re=1_000, beta=0, vbe=0.7)

    def test_vbe_out_of_range_rejected(self):
        for vbe in (0.0, 1.0, 5.0):
            with self.assertRaises(BiasInputError):
                calculate_dc_bias(vcc=12, r1=100_000, r2=22_000, rc=2_200, re=1_000, beta=100, vbe=vbe)

    def test_zero_re_rejected(self):
        with self.assertRaises(BiasInputError):
            calculate_dc_bias(vcc=12, r1=100_000, r2=22_000, rc=2_200, re=0, beta=100, vbe=0.7)


class TestRegions(unittest.TestCase):
    def test_cutoff(self):
        r = calculate_dc_bias(vcc=12, r1=100_000, r2=2_200, rc=2_200, re=1_000, beta=100, vbe=0.7)
        self.assertEqual(r.region, "cutoff")
        self.assertEqual(r.ib, 0.0)
        self.assertEqual(r.ic, 0.0)
        self.assertEqual(r.vc, 12.0)
        self.assertTrue(any("Cutoff" in w for w in r.warnings))

    def test_saturation(self):
        r = calculate_dc_bias(vcc=12, r1=100_000, r2=22_000, rc=10_000, re=1_000, beta=100, vbe=0.7)
        self.assertEqual(r.region, "saturation")
        self.assertLess(r.vce, 0.3)
        self.assertTrue(any("Saturation" in w for w in r.warnings))

    def test_extreme_beta_is_finite(self):
        for beta in (1, 10_000):
            r = calculate_dc_bias(vcc=12, r1=100_000, r2=22_000, rc=2_200, re=1_000, beta=beta, vbe=0.7)
            self.assertAlmostEqual(r.ic, beta * r.ib, places=9)
            self.assertIn(r.region, {"active", "cutoff", "saturation"})
```

- [ ] **Step 3: รันเทสต์ให้เห็นว่าล้มเหลว**

```
python -m unittest tests.test_dc_bias -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 4: เขียน `dc_bias.py`**

โครงที่ต้องมี (เติม body เอง):
```python
from dataclasses import dataclass

VCE_SAT = 0.3
VBE_MIN = 0.0
VBE_MAX = 1.0
_UNITS = {"ohm": 1.0, "kohm": 1_000.0}


class BiasInputError(ValueError):
    pass


@dataclass(frozen=True)
class BiasResult:
    vth: float
    rth: float
    ib: float
    ic: float
    ie: float
    ve: float
    vb: float
    vc: float
    vce: float
    region: str
    warnings: tuple[str, ...]


def parse_resistance(raw: str, unit: str) -> float:
    ...


def calculate_dc_bias(vcc, r1, r2, rc, re, beta, vbe) -> BiasResult:
    ...
```

กติกาที่ต้องทำตาม:
- `parse_resistance`: ตัดช่องว่าง, แปลง float ไม่ได้ → `BiasInputError("ค่าตัวต้านทานไม่ใช่ตัวเลข")`; `unit` ไม่อยู่ใน `_UNITS` → `BiasInputError("หน่วยไม่ถูกต้อง")`; ค่าที่ได้ ≤ 0 → `BiasInputError`
- `calculate_dc_bias`: `vcc <= 0`, `r1 <= 0`, `r2 <= 0`, `rc <= 0`, `re <= 0`, `beta <= 0`, `vbe` นอกช่วง `(VBE_MIN, VBE_MAX)` → `BiasInputError` (ข้อความระบุชื่อพารามิเตอร์)
- สมการ: `VTH = vcc*r2/(r1+r2)`, `RTH = r1*r2/(r1+r2)`, `IB = (VTH-vbe)/(RTH+(beta+1)*re)`, `IC = beta*IB`, `IE = (beta+1)*IB`, `VE = IE*re`, `VB = VE+vbe`, `VC = vcc-IC*rc`, `VCE = VC-VE`
- **Cutoff** (`VTH <= vbe`): กำหนด `ib = ic = ie = 0.0`, `ve = 0.0`, `vb = vbe`, `vc = vcc`, `vce = vcc - ve`; region `"cutoff"`; warning มีคำว่า `Cutoff`
- **Saturation** (`VCE < VCE_SAT` และไม่ใช่ cutoff): คงค่าจากสมการ, region `"saturation"`, warning มีคำว่า `Saturation` และระบุว่าแบบจำลองใช้ไม่ได้
- **Active**: region `"active"`, `warnings = ()`

- [ ] **Step 5: รันเทสต์ให้ผ่าน**

```
python -m unittest tests.test_dc_bias -v
```
Expected: `Ran 14 tests ... OK` (0 failures)

- [ ] **Step 6: Commit ผ่าน GitHub Desktop**

เปิด GitHub Desktop → repo *BJT DC Bias Web App* → Changes → Summary:
`Add DC bias engineering core with unit conversion and region warnings`
→ Commit to main (ยังไม่ต้อง Push)

---

### Task 2: Web layer (`app.py` + template + CSS)

**Files:**
- Create: `app.py`
- Create: `templates/index.html`
- Create: `static/style.css`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `BiasInputError`, `calculate_dc_bias`, `parse_resistance` จาก Task 1
- Produces: Flask `app` object ที่ import ได้ (`from app import app`) พร้อม route `GET /` และ `POST /calculate`; ชื่อฟิลด์ฟอร์ม: `vcc, r1, r1_unit, r2, r2_unit, rc, rc_unit, re, re_unit, beta, vbe`

- [ ] **Step 1: เขียน failing tests**

`tests/test_web.py`:
```python
import unittest

from app import app

VALID = {
    "vcc": "12", "r1": "100", "r1_unit": "kohm", "r2": "22", "r2_unit": "kohm",
    "rc": "2.2", "rc_unit": "kohm", "re": "1", "re_unit": "kohm",
    "beta": "100", "vbe": "0.7",
}


class TestIndex(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_index_returns_200_and_form(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', body)


class TestCalculate(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_valid_input_computes_in_backend(self):
        resp = self.client.post("/calculate", data=VALID)
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn("8.052", body)   # VCE จากสมการ ไม่ใช่ค่าคงที่ใน HTML
        self.assertIn("1.230", body)   # IC [mA]

    def test_zero_resistance_returns_400_with_field_name(self):
        data = dict(VALID, r1="0")
        resp = self.client.post("/calculate", data=data)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("R1", resp.get_data(as_text=True))

    def test_non_numeric_returns_400(self):
        data = dict(VALID, vcc="abc")
        resp = self.client.post("/calculate", data=data)
        self.assertEqual(resp.status_code, 400)

    def test_cutoff_shows_warning_and_200(self):
        data = dict(VALID, r2="2.2")
        resp = self.client.post("/calculate", data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Cutoff", resp.get_data(as_text=True))

    def test_diagram_renders_computed_vce(self):
        resp = self.client.post("/calculate", data=VALID)
        body = resp.get_data(as_text=True)
        self.assertIn("<svg", body)
        self.assertRegex(body, r"VCE\s*=\s*8\.052")
```

- [ ] **Step 2: รันเทสต์ให้เห็นว่าล้มเหลว**

```
python -m unittest tests.test_web -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: เขียน `app.py`**

```python
from flask import Flask, render_template, request

from dc_bias import BiasInputError, calculate_dc_bias, parse_resistance

app = Flask(__name__)

DEFAULTS = {
    "vcc": "12", "r1": "100", "r1_unit": "kohm", "r2": "22", "r2_unit": "kohm",
    "rc": "2.2", "rc_unit": "kohm", "re": "1", "re_unit": "kohm",
    "beta": "100", "vbe": "0.7",
}

RESISTOR_FIELDS = (("r1", "R1"), ("r2", "R2"), ("rc", "RC"), ("re", "RE"))


@app.get("/")
def index():
    return render_template("index.html", form=DEFAULTS, result=None, errors=[])


@app.post("/calculate")
def calculate():
    ...
```

กติกาที่ต้องทำตาม:
- อ่านค่าจาก `request.form` โดยใช้ `form.get(name, "")`; ถ้าฟิลด์หายไปให้ถือเป็นค่าว่าง
- แปลง `vcc`, `beta`, `vbe` ด้วย `float()`; แปลงตัวต้านทานด้วย `parse_resistance(raw, unit)`
- เก็บ error ทุกข้อใน list `errors` (ข้อความสองภาษา อังกฤษนำ + ไทยในวงเล็บ ระบุชื่อช่อง เช่น `"R1 must be greater than 0 (R1 ต้องมากกว่า 0)"`) แล้ว `render_template("index.html", form=submitted, result=None, errors=errors)` พร้อม status **400**
- ถ้าผ่าน: `calculate_dc_bias(...)` → `render_template(..., result=result, errors=[])` status 200
- `BiasInputError` ต้องถูกจับ ไม่ให้หลุดเป็น 500; `ValueError` จากการ `float()` ก็จับเช่นกัน
- ส่ง `form` ที่ผู้ใช้กรอกกลับไปเพื่อคงค่า (D9)

- [ ] **Step 3.5: วางแผนภาพวงจร (inline SVG, D11)**

ใน `templates/index.html` เพิ่ม `<svg>` ฝังในหน้า (ไม่ใช่ไฟล์ภาพแยก และไม่มี JavaScript) โดยมี:

- โครงวงจร voltage-divider bias: ราง VCC ด้านบน, R1 จาก VCC ลง base, R2 จาก base ลง ground, RC จาก VCC ลง collector, ทรานซิสเตอร์ NPN, RE จาก emitter ลง ground, สัญลักษณ์ ground ทั้งสองฝั่ง
- **สัญลักษณ์ (ผู้ใช้กำหนด):** ตัวต้านทานทั้งสี่วาดเป็น **เส้นหยัก (ANSI zigzag)** ไม่ใช่สี่เหลี่ยม; ทรานซิสเตอร์วาดเป็น **สัญลักษณ์ BJT ที่มีวงกลมครอบ** (เส้นตั้งของ base อยู่ข้างใน, ขา collector/emitter เฉียงออกจากเส้น base, ลูกศรที่ emitter ชี้ออกจาก base)
- ป้ายค่าอุปกรณ์เติมจาก `form`: `VCC = {{ form.vcc }} V`, `R1 = {{ form.r1 }} {{ 'kΩ' if form.r1_unit == 'kohm' else 'Ω' }}` และเช่นเดียวกันกับ R2, RC, RE, `β = {{ form.beta }}`
- ป้ายแรงดันที่ node เติมจาก `result` (แสดงเฉพาะเมื่อ `result` ไม่ใช่ `None`): `VB = {{ "%.3f"|format(result.vb) }} V`, `VE`, `VC` ในทำนองเดียวกัน
- แผงมุมขวาบนของภาพ: `VCE`, `IC` (mA), `IB` (µA) ด้วยรูปแบบเดียวกับตารางผลลัพธ์
- ถ้า `result is None` ให้ภาพแสดงเฉพาะค่าอุปกรณ์ ไม่มีตัวเลขแรงดันที่ node
- ใช้ `class` ที่ขึ้นต้นด้วย `sc-` สำหรับ style ภายใน SVG เพื่อไม่ชนกับ `static/style.css`
- ต้องมี `<title>` หรือ `aria-label` อธิบายภาพสำหรับ screen reader

เกณฑ์ตรวจ: เปิดหน้าที่มี `result` แล้วเห็นตัวเลขบนภาพตรงกับตัวเลขในตาราง (เช่น VCE 8.052 V ปรากฏทั้งสองที่)

- [ ] **Step 4: เขียน `templates/index.html`**

ต้องมี:
- `<form method="post" action="/calculate">` และ `<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">`
- ช่อง `vcc`, `beta`, `vbe` เป็น `input type="number" step="any" name="..."` พร้อม label
- ช่อง `r1, r2, rc, re` เป็น `input type="number" step="any"` คู่กับ `<select name="<field>_unit">` ที่มี `<option value="kohm">kΩ</option>` และ `<option value="ohm">Ω</option>` (เลือกค่าจาก `form[...]` ด้วย `{% if %}`)
- บล็อก error: `{% if errors %}<ul class="errors">{% for e in errors %}<li>{{ e }}</li>{% endfor %}</ul>{% endif %}`
- บล็อกผลลัพธ์ `{% if result %}` แสดง VB, VE, VC, VCE (V) และ IC (mA), IB (µA), IE (mA) โดยใช้ `{{ "%.3f"|format(result.vce) }}` และ `{{ "%.3f"|format(result.ic * 1000) }}`
- บล็อก warning: `{% for w in result.warnings %}` และถ้า `result.region != 'active'` แสดงข้อความ `Values shown are estimates only — do not use them to make decisions (ค่าที่แสดงเป็นเพียงการประมาณ — อย่าใช้ตัดสินใจ)`
- ป้ายกำกับทุกตัวเป็นสองภาษา (อังกฤษนำ ไทยในวงเล็บ) ตาม Global Constraints; ชื่อปริมาณคงรูปสัญลักษณ์เดิม (`VB`, `VCE`, `IC`, …)

- [ ] **Step 5: เขียน `static/style.css`**

จัด layout 2 คอลัมน์บนจอกว้าง (ฟอร์มซ้าย ผลขวา) และคอลัมน์เดียวต่ำกว่า 700px; `.errors` พื้นแดงอ่อน, warning พื้นเหลืองอ่อน; ใช้ `font-family: Tahoma, "Leelawadee UI", sans-serif`

- [ ] **Step 6: รันเทสต์ทั้งหมดให้ผ่าน**

```
python -m unittest discover -s tests -v
```
Expected: `Ran 20 tests ... OK`

- [ ] **Step 7: ทดสอบด้วยตาบนเบราว์เซอร์**

```
python -m flask --app app run --debug
```
เปิด `http://127.0.0.1:5000/` → กด Calculate → ต้องเห็น VCE 8.052 V และ IC 1.230 mA; ลองกรอก R1 = 0 → เห็น error; หยุด server ด้วย Ctrl+C

- [ ] **Step 8: Commit ผ่าน GitHub Desktop**

Summary: `Add Flask routes, Jinja template and stylesheet for DC bias`
→ Commit to main

---

### Task 3: Documentation และ reproducibility

**Files:**
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `docs/design-note.md`
- Create: `docs/validation.md`
- Create: `docs/reflection.md`

**Interfaces:**
- Consumes: คำสั่งรัน/ทดสอบจาก Task 1–2
- Produces: เอกสารที่ทำให้ clone แล้วรันได้ (A7)

- [ ] **Step 1: เขียน `README.md`**

ต้องมี: ชื่อโปรเจกต์, ภาพรวมสั้น ๆ, วิธีติดตั้ง (`python -m venv .venv`, activate ทั้ง Windows/Linux, `pip install -r requirements.txt`), วิธีรัน (`python -m flask --app app run --debug`, เปิด `http://127.0.0.1:5000/`), วิธีทดสอบ (`python -m unittest discover -s tests -v`), ชุดค่าตัวอย่างจากใบงาน, และหมายเหตุว่าเป็น Forward-Active approximation ไม่ใช่ SPICE

- [ ] **Step 2: เขียน `AGENTS.md`**

ระบุ: `dc_bias.py` ห้าม import Flask; ทุกสมการต้องมี test; ห้ามฮาร์ดโค้ดผลลัพธ์ในเทมเพลต; ใช้ `unittest`; commit ผ่าน GitHub Desktop

- [ ] **Step 3: เขียน `docs/design-note.md`**

สรุป 1 หน้า: ทำไมเลือก Flask, ทำไมแยก `dc_bias.py`, data flow, เหตุผลที่เลือก server-rendered POST

- [ ] **Step 4: เขียน `docs/validation.md`**

ตารางค่าอ้างอิง (ค่าที่คำนวณเต็มความละเอียด: VTH 2.16393 V, RTH 18.03279 kΩ, IB 12.2986 µA, IC 1.22986 mA, IE 1.24216 mA, VE 1.24216 V, VB 1.94216 V, VC 9.29431 V, VCE 8.05216 V — กำกับค่าในใบงาน 8.0523 V ไว้ด้วย), วิธีคำนวณมือทีละขั้น, คำอธิบายว่าใบงานปัด IB เป็น 12.298 µA ก่อนคำนวณต่อจึงต่างกันในหลักที่ 4, สมมติฐาน (β คงที่, VBE คงที่ 0.7 V), และกรณีที่แบบจำลองใช้ไม่ได้ (cutoff / saturation)

- [ ] **Step 5: สร้างโครง `docs/reflection.md` (นักศึกษาเขียนคำตอบเอง)**

สร้างไฟล์ที่มี 4 หัวข้อคำถามจากใบงาน แต่ละข้อมีคำใบ้สั้น ๆ ว่าควรอธิบายประเด็นใด และช่อง `**คำตอบ:**` เปล่าไว้ให้เขียนเอง ห้ามเติมคำตอบแทนนักศึกษา:
1. ทำไมการเปิด `templates/index.html` ตรง ๆ (`file://`) จึงไม่เท่ากับการรัน Flask — ใบ้: ใครเป็นคนคำนวณ, มี HTTP request หรือไม่
2. ฟอร์มส่งข้อมูลไป Python อย่างไร — ใบ้: method, action, `request.form`, ชื่อ route
3. แก้สมการใน `dc_bias.py` แล้วต้องแก้ HTML หรือไม่ — ใบ้: การแยกความรับผิดชอบระหว่าง logic กับ template
4. ทำไมผลใน Region ที่แบบจำลองใช้ไม่ได้จึงต้องมี Warning — ใบ้: Forward-Active approximation ใช้สมมติฐานอะไร

- [ ] **Step 6: ตรวจ reproducibility จาก environment ใหม่**

```
Remove-Item -Recurse -Force .venv-check -ErrorAction SilentlyContinue
python -m venv .venv-check
.venv-check\Scripts\python.exe -m pip install -r requirements.txt
.venv-check\Scripts\python.exe -m unittest discover -s tests -v
```
Expected: `Ran 20 tests ... OK` และติดตั้งได้โดยไม่ต้องแก้อะไร

- [ ] **Step 7: เก็บหลักฐานส่งงาน (ใบงานกำหนดให้ส่งภาพหน้าจอ + Test Log)**

1. รัน `python -m unittest discover -s tests -v` แล้วคัดลอกผลทั้งหมดลง `docs/test-log.md` ในบล็อกโค้ด พร้อมวันที่
2. เปิด `http://127.0.0.1:5000/` กด Calculate ด้วยค่าตัวอย่าง แล้วบันทึกภาพหน้าจอที่เห็นผล DC Bias ครบ ไว้ที่ `docs/screenshots/calculate-success.png`
3. ถ่ายภาพหน้าจอกรณีกรอกค่าผิด (R1 = 0) ไว้ที่ `docs/screenshots/validation-error.png`
4. ตรวจว่า `.gitignore` ไม่ได้กันโฟลเดอร์ `docs/screenshots/`

- [ ] **Step 8: Commit ผ่าน GitHub Desktop**

Summary: `Add README, validation notes and reflection for Lab 02`
→ Commit to main → กด **Push origin**

---

## Self-Review

- Spec coverage: A1 (Task 2 test GET), A2 (Task 2 test valid POST + Task 1 core), A3 (Task 1 reference test + validation.md), A4 (Task 1 validation tests + Task 2 400 tests), A5 (Task 1 region tests + Task 2 cutoff test), A6 (20 tests), A7 (Task 3)
- Type consistency: `BiasResult` ฟิลด์เดียวกันทุก task; `parse_resistance(raw, unit)` ใช้ชื่อเดียวกันใน Task 1 และ Task 2
- Review Focus: แต่ละบรรทัดมี test อยู่ใน Task 1 (RE=0, VBE range, cutoff, β สุดขั้ว) และ Task 2 (non-numeric → 400)
- Proportion: 3 tasks, 20 tests — พอดีกับคาบ 3 ชั่วโมง
