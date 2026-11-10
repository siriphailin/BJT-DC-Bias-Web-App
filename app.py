"""Web layer (Flask) สำหรับเครื่องคำนวณ DC bias ของ BJT — ENG29 2121

ชั้นนี้ทำหน้าที่ presentation เท่านั้น: อ่านค่าจากฟอร์ม แปลงหน่วยความต้านทาน
แล้วส่งต่อให้ :mod:`dc_bias` คำนวณ สมการทั้งหมดอยู่ใน ``dc_bias.py``
"""

from flask import Flask, render_template, request

from dc_bias import VCE_SAT, BiasInputError, calculate_dc_bias, parse_resistance

app = Flask(__name__)


@app.context_processor
def inject_constants() -> dict[str, float]:
    """ค่าคงที่ที่ template ต้องใช้ (เช่นเกณฑ์ VCE(sat)) — ประกาศที่เดียว ไม่ต้องส่งซ้ำทุก route"""
    return {"vce_sat": VCE_SAT}


DEFAULTS = {
    "vcc": "12", "r1": "100", "r1_unit": "kohm", "r2": "22", "r2_unit": "kohm",
    "rc": "2.2", "rc_unit": "kohm", "re": "1", "re_unit": "kohm",
    "beta": "100", "vbe": "0.7",
}

RESISTOR_FIELDS = (("r1", "R1"), ("r2", "R2"), ("rc", "RC"), ("re", "RE"))

# ชื่อฟิลด์ทั้งหมดในฟอร์ม ใช้ทั้งอ่านค่าและส่งกลับไปคงค่าที่ผู้ใช้กรอก (D9)
FORM_FIELDS = (
    "vcc", "r1", "r1_unit", "r2", "r2_unit", "rc", "rc_unit", "re", "re_unit",
    "beta", "vbe",
)

# (ชื่อฟิลด์, ป้ายอังกฤษ, ป้ายไทย) สำหรับฟิลด์ที่ไม่ใช่ตัวต้านทาน
SCALAR_FIELDS = (
    ("vcc", "VCC", "VCC"),
    ("beta", "beta (β)", "β"),
    ("vbe", "VBE", "VBE"),
)


def _label_error(label: str, thai_label: str, error: Exception) -> str:
    """เติมชื่อช่องลงในข้อความ error ที่ยังไม่มีชื่อช่อง (เช่นของ parse_resistance)"""
    english, separator, thai = str(error).partition(" (")
    if separator:
        return f"{label}: {english} ({thai_label}: {thai}"
    return f"{label}: {error}"


def _read_number(
    submitted: dict[str, str], name: str, label: str, thai_label: str,
    errors: list[str],
) -> float | None:
    """แปลงค่าจากฟอร์มเป็น float โดยเก็บ error แบบสองภาษาไว้ใน ``errors``"""
    try:
        return float(submitted[name])
    except (TypeError, ValueError):
        errors.append(
            f"{label} must be a number (ค่า {thai_label} ต้องเป็นตัวเลข)"
        )
        return None


@app.get("/")
def index():
    return render_template("index.html", form=DEFAULTS, result=None, errors=[])


@app.post("/calculate")
def calculate():
    submitted = {name: request.form.get(name, "") for name in FORM_FIELDS}
    errors: list[str] = []

    scalars = {
        name: _read_number(submitted, name, label, thai, errors)
        for name, label, thai in SCALAR_FIELDS
    }

    resistances: dict[str, float] = {}
    for name, label in RESISTOR_FIELDS:
        try:
            resistances[name] = parse_resistance(
                submitted[name], submitted[f"{name}_unit"]
            )
        except BiasInputError as exc:
            errors.append(_label_error(label, label, exc))

    if errors:
        return (
            render_template("index.html", form=submitted, result=None, errors=errors),
            400,
        )

    try:
        result = calculate_dc_bias(
            vcc=scalars["vcc"],
            r1=resistances["r1"],
            r2=resistances["r2"],
            rc=resistances["rc"],
            re=resistances["re"],
            beta=scalars["beta"],
            vbe=scalars["vbe"],
        )
    except BiasInputError as exc:
        return (
            render_template(
                "index.html", form=submitted, result=None, errors=[str(exc)]
            ),
            400,
        )

    return render_template("index.html", form=submitted, result=result, errors=[])
