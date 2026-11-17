"""Web layer (Flask) สำหรับเครื่องคำนวณ DC bias ของ BJT — ENG29 2121

ชั้นนี้ทำหน้าที่ presentation เท่านั้น: อ่านค่าจากฟอร์ม แปลงหน่วยความต้านทาน
เลือกฟังก์ชันตามโหมดที่ผู้ใช้เลือก แล้วส่งต่อให้ :mod:`dc_bias` คำนวณ
สมการทั้งหมดอยู่ใน ``dc_bias.py``
"""

from flask import Flask, render_template, request

from dc_bias import (
    VCE_SAT,
    BiasInputError,
    calculate_dc_bias,
    calculate_emitter_bias,
    calculate_fixed_bias,
    parse_resistance,
)

app = Flask(__name__)

# โหมดไบอัสที่รองรับ: อินพุตตัวต้านทานที่แต่ละโหมดต้องใช้จริง
# (ถ้าเพิ่มโหมดใหม่ ต้องเพิ่มใน dict นี้เท่านั้น — app.py ไม่มีสมการ)
MODES = {
    "divider": {
        "label": "Voltage Divider Bias",
        "thai": "แบ่งแรงดัน",
        "resistors": ("r1", "r2", "rc", "re"),
        "description": (
            "R1 from VCC to Base, R2 from Base to Ground, RC from VCC to Collector "
            "and RE from Emitter to Ground (R1 จาก VCC ไป Base, R2 จาก Base ลงกราวด์, "
            "RC จาก VCC ไป Collector และ RE จาก Emitter ลงกราวด์)"
        ),
    },
    "fixed": {
        "label": "Fixed Bias",
        "thai": "ไบอัสคงที่",
        "resistors": ("rb", "rc"),
        "description": (
            "RB from VCC to Base and RC from VCC to Collector; the Emitter goes "
            "straight to ground, so RE is not used (RB จาก VCC ไป Base, RC จาก VCC "
            "ไป Collector, Emitter ต่อลงกราวด์โดยตรง จึงไม่ใช้ RE)"
        ),
    },
    "emitter": {
        "label": "Emitter Bias (single supply)",
        "thai": "ไบอัสอีมิตเตอร์ แหล่งจ่ายเดียว",
        "resistors": ("rb", "rc", "re"),
        "description": (
            "RB from VCC to Base, RC from VCC to Collector and RE from Emitter to "
            "Ground (RB จาก VCC ไป Base, RC จาก VCC ไป Collector และ RE จาก Emitter "
            "ลงกราวด์)"
        ),
    },
}

DEFAULT_MODE = "divider"


@app.context_processor
def inject_constants() -> dict:
    """ค่าที่ template ต้องใช้ (เกณฑ์ VCE(sat), รายการโหมด และค่าเริ่มต้นของฟอร์ม)"""
    return {
        "vce_sat": VCE_SAT,
        "modes": MODES,
        "default_mode": DEFAULT_MODE,
        "defaults": DEFAULTS,
    }


DEFAULTS = {
    "mode": DEFAULT_MODE,
    "vcc": "12", "rb": "1000", "rb_unit": "kohm",
    "r1": "100", "r1_unit": "kohm", "r2": "22", "r2_unit": "kohm",
    "rc": "2.2", "rc_unit": "kohm", "re": "1", "re_unit": "kohm",
    "beta": "100", "vbe": "0.7",
}

# ชื่อฟิลด์ทั้งหมดในฟอร์ม ใช้ทั้งอ่านค่าและส่งกลับไปคงค่าที่ผู้ใช้กรอก (D9)
FORM_FIELDS = (
    "mode",
    "vcc", "rb", "rb_unit", "r1", "r1_unit", "r2", "r2_unit",
    "rc", "rc_unit", "re", "re_unit", "beta", "vbe",
)

# (ชื่อฟิลด์, ป้ายอังกฤษ, ป้ายไทย) สำหรับฟิลด์ที่ไม่ใช่ตัวต้านทาน
SCALAR_FIELDS = (
    ("vcc", "VCC", "VCC"),
    ("beta", "beta (β)", "β"),
    ("vbe", "VBE", "VBE"),
)

RESISTOR_LABELS = {
    "rb": ("RB", "RB"),
    "r1": ("R1", "R1"),
    "r2": ("R2", "R2"),
    "rc": ("RC", "RC"),
    "re": ("RE", "RE"),
}


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


def _resolve_mode(raw: str | None) -> str | None:
    """คืนชื่อโหมดที่รู้จัก หรือ ``None`` ถ้าโหมดไม่ถูกต้อง (ไม่เดาเป็น divider)"""
    mode = (raw or "").strip() or DEFAULT_MODE
    return mode if mode in MODES else None


def _error_response(submitted: dict[str, str], errors: list[str]):
    # template ต้องมี form.mode ที่รู้จักเสมอ ไม่งั้นไม่มีปุ่มโหมดไหนถูก mark ว่า active
    mode = _resolve_mode(submitted.get("mode")) or DEFAULT_MODE
    form = dict(submitted, mode=mode)
    return (
        render_template(
            "index.html", form=form, result=None, errors=errors,
            mode=mode, mode_info=MODES.get(mode),
        ),
        400,
    )


@app.get("/")
def index():
    mode = _resolve_mode(request.args.get("mode"))
    if mode is None:
        return _error_response(
            dict(DEFAULTS), [f"Unknown bias mode (โหมดไบอัสไม่ถูกต้อง)"]
        )
    form = dict(DEFAULTS, mode=mode)
    return render_template("index.html", form=form, result=None, errors=[], mode=mode)


@app.post("/calculate")
def calculate():
    submitted = {name: request.form.get(name, "") for name in FORM_FIELDS}
    errors: list[str] = []

    mode = _resolve_mode(submitted["mode"])
    if mode is None:
        return _error_response(
            submitted,
            [
                "Unknown bias mode: choose Fixed, Emitter or Voltage Divider "
                "(โหมดไบอัสไม่ถูกต้อง: เลือก Fixed, Emitter หรือ Voltage Divider)"
            ],
        )
    submitted["mode"] = mode

    # ตรวจเฉพาะช่องที่โหมดนั้นใช้จริง — ช่องของโหมดอื่นไม่ถูกอ่านเลย
    required = MODES[mode]["resistors"]

    scalars = {
        name: _read_number(submitted, name, label, thai, errors)
        for name, label, thai in SCALAR_FIELDS
    }

    resistances: dict[str, float] = {}
    for name in required:
        label, thai = RESISTOR_LABELS[name]
        try:
            resistances[name] = parse_resistance(
                submitted[name], submitted[f"{name}_unit"]
            )
        except BiasInputError as exc:
            errors.append(_label_error(label, thai, exc))

    if errors:
        return _error_response(submitted, errors)

    try:
        if mode == "divider":
            result = calculate_dc_bias(
                vcc=scalars["vcc"],
                r1=resistances["r1"],
                r2=resistances["r2"],
                rc=resistances["rc"],
                re=resistances["re"],
                beta=scalars["beta"],
                vbe=scalars["vbe"],
            )
        elif mode == "fixed":
            result = calculate_fixed_bias(
                vcc=scalars["vcc"],
                rb=resistances["rb"],
                rc=resistances["rc"],
                beta=scalars["beta"],
                vbe=scalars["vbe"],
            )
        else:  # emitter
            result = calculate_emitter_bias(
                vcc=scalars["vcc"],
                rb=resistances["rb"],
                rc=resistances["rc"],
                re=resistances["re"],
                beta=scalars["beta"],
                vbe=scalars["vbe"],
            )
    except BiasInputError as exc:
        return _error_response(submitted, [str(exc)])

    return render_template(
        "index.html",
        form=submitted,
        result=result,
        errors=[],
        mode=mode,
        mode_info=MODES[mode],
    )
