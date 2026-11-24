"""Web layer (Flask) สำหรับเครื่องคำนวณ DC bias ของ BJT — ENG29 2121

ชั้นนี้ทำหน้าที่ presentation เท่านั้น: อ่านค่าจากฟอร์ม แปลงหน่วยความต้านทาน
เลือกฟังก์ชันตามโหมดที่ผู้ใช้เลือก แล้วส่งต่อให้ :mod:`dc_bias` คำนวณ
สมการทั้งหมดอยู่ใน ``dc_bias.py``
"""

import math
import tempfile
from pathlib import Path

from flask import Flask, render_template, request

from dc_bias import (
    VCE_SAT,
    BiasInputError,
    calculate_dc_bias,
    calculate_emitter_bias,
    calculate_fixed_bias,
    parse_resistance,
)
from spice_engine import (
    resolve_engine,
    run_analysis,
    svg_bode,
    svg_waveform,
    validate_sim_input,
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


# --- Lab 04: CE amplifier simulator (separate routes; Lab 03 ด้านบนไม่ถูกแตะ) ---

SIM_ANALYSES = {
    "dc": {"label": "DC", "thai": "จุดทำงาน DC", "directive": ".op"},
    "ac": {"label": "AC", "thai": "ตอบสนองความถี่ AC",
           "directive": ".ac dec 20 1 1Meg"},
    "tran": {"label": "Transient", "thai": "รูปคลื่นตามเวลา",
             "directive": ".tran"},
}

SIM_FIELDS = (
    "analysis", "vcc",
    "r1", "r1_unit", "r2", "r2_unit", "rc", "rc_unit", "re", "re_unit",
    "rl", "rl_unit", "amplitude", "amplitude_unit",
    "frequency", "frequency_unit",
)

SIM_DEFAULTS = {
    "analysis": "dc", "vcc": "12",
    "r1": "100", "r1_unit": "kohm", "r2": "22", "r2_unit": "kohm",
    "rc": "2.2", "rc_unit": "kohm", "re": "1", "re_unit": "kohm",
    "rl": "10", "rl_unit": "kohm",
    "amplitude": "10", "amplitude_unit": "mv",
    "frequency": "1", "frequency_unit": "khz",
}

ENGINE_PATH = resolve_engine()


def run_analysis_for_request(params, analysis: str):
    """Run one ngspice analysis in a throwaway directory (kept for callers)."""
    with tempfile.TemporaryDirectory() as directory:
        return run_analysis(params, analysis, Path(directory), ENGINE_PATH)


def run_all_for_request(params):
    """Run DC, AC and transient so both plots and all result tables are real."""
    results = {}
    with tempfile.TemporaryDirectory() as directory:
        for key in SIM_ANALYSES:
            results[key] = run_analysis(
                params, key, Path(directory) / key, ENGINE_PATH
            )
    return results


def _overall_status(results: dict) -> tuple[str, str]:
    """Report one honest status for the three analysis runs."""
    failures = [item for item in results.values() if item.status != "SUCCESS"]
    if not failures:
        return "SUCCESS", "DC, AC and transient analyses complete (รันครบทั้ง 3 การวิเคราะห์)"
    first = failures[0]
    if len(failures) == len(results) and all(
        item.status == first.status for item in failures
    ):
        return first.status, first.message
    return "PARTIAL", (
        f"{first.status}: {first.message} "
        "(บางการวิเคราะห์ยังไม่สำเร็จ — ไม่แสดงผลเก่า)"
    )


def _ac_summary(points) -> dict:
    """One representative AC row: the sweep point nearest to 1 kHz."""
    if not points:
        return {}
    nearest = min(points, key=lambda p: abs(math.log10(p[0] / 1000.0)))
    return {
        "midband_db": max(p[1] for p in points),
        "gain_1k_db": nearest[1],
        "phase_1k_deg": nearest[2],
        "freq_1k_hz": nearest[0],
        "points": len(points),
    }


def _tran_summary(points) -> dict:
    """One representative transient row at the positive Vin peak."""
    if not points:
        return {}
    peak = max(points, key=lambda p: abs(p[1]))
    vin = [p[1] for p in points]
    vout = [p[2] for p in points]
    return {
        "vin": peak[1],
        "vout": peak[2],
        "time_ms": peak[0] * 1000.0,
        "vin_pp": max(vin) - min(vin),
        "vout_pp": max(vout) - min(vout),
        "points": len(points),
    }


def _render_simulator(form, analysis, runs=None, errors=None, status_code=200):
    """Build one template context; every failure clears result/series to None."""
    runs = runs or {}
    successful = {key: item for key, item in runs.items() if item.status == "SUCCESS"}

    dc_result = successful.get("dc")
    dc_values = dc_result.values if dc_result is not None else None
    ac_points = successful["ac"].ac_points if "ac" in successful else ()
    tran_points = successful["tran"].tran_points if "tran" in successful else ()

    status, message = _overall_status(runs) if runs else ("", "")
    first = next(iter(runs.values()), None)
    engine_version = (
        first.provenance.get("engine_version", "unavailable")
        if first is not None else "unavailable"
    )

    return render_template(
        "simulator.html",
        form=form,
        analysis=analysis,
        analyses=SIM_ANALYSES,
        errors=errors or [],
        dc_values=dc_values,
        bode_svg=svg_bode(ac_points),
        wave_svg=svg_waveform(tran_points),
        ac_summary=_ac_summary(ac_points),
        tran_summary=_tran_summary(tran_points),
        status=status,
        message=message,
        engine_version=engine_version,
        engine_path=ENGINE_PATH or "not found",
    ), status_code


@app.get("/simulator")
def simulator():
    """Render the form with the requested analysis focus selected.

    The three tabs are radio inputs associated with the simulation form, so
    switching focus never reloads or clears the rendered results.
    """
    requested = (request.args.get("analysis") or "dc").strip()
    analysis = requested if requested in SIM_ANALYSES else "dc"
    form = {
        name: (request.args.get(name) or SIM_DEFAULTS[name])
        for name in SIM_FIELDS
        if name != "analysis"
    }
    form["analysis"] = analysis
    return _render_simulator(form, analysis)


@app.post("/simulate")
def simulate():
    submitted = {name: request.form.get(name, "") for name in SIM_FIELDS}
    analysis = (submitted.get("analysis") or "dc").strip()
    if analysis not in SIM_ANALYSES:
        return _render_simulator(
            submitted, "dc",
            errors=[
                "Unknown analysis: choose DC, AC or Transient "
                "(การวิเคราะห์ไม่ถูกต้อง: เลือก DC, AC หรือ Transient)"
            ],
            status_code=400,
        )
    submitted["analysis"] = analysis

    params, errors = validate_sim_input(submitted)
    if errors:
        return _render_simulator(submitted, analysis, errors=errors, status_code=400)

    return _render_simulator(submitted, analysis, runs=run_all_for_request(params))
