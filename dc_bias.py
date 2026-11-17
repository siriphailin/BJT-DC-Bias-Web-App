"""BJT DC bias calculation สำหรับแล็บ ENG29 2121

โมดูลนี้เป็น engineering core แบบ pure Python (standard library เท่านั้น):
- ไม่ผูกกับ web framework หรือชั้น presentation
- ตัวต้านทานรับหน่วยเป็นโอห์ม (ohm) กระแสเป็นแอมป์ (A) แรงดันเป็นโวลต์ (V)

รองรับสามโหมด (Forward-Active approximation):

1. Voltage Divider Bias — ``calculate_dc_bias``

    VTH = VCC * R2 / (R1 + R2)
    RTH = R1 * R2 / (R1 + R2)
    IB  = (VTH - VBE) / (RTH + (beta + 1) * RE)

2. Fixed Bias — ``calculate_fixed_bias`` (RE = 0)

    IB  = (VCC - VBE) / RB

3. Emitter Bias แบบแหล่งจ่ายเดียว — ``calculate_emitter_bias``

    IB  = (VCC - VBE) / (RB + (beta + 1) * RE)

ทุกโหมดใช้ส่วนที่เหลือร่วมกัน:

    IC  = beta * IB
    IE  = (beta + 1) * IB
    VE  = IE * RE
    VB  = VE + VBE
    VC  = VCC - IC * RC
    VCE = VC - VE

Fixed Bias ไม่มี RE จึงได้ VE = 0 V และ VCE = VC

หมายเหตุ: Fixed และ Emitter Bias ไม่มี R1/R2 แต่ Thévenin equivalent ที่ขา Base
ยังเขียนได้คือ VTH = VCC, RTH = RB ทำให้ใช้สมการเดียวกับ Divider ได้
"""

import math
from dataclasses import dataclass

VCE_SAT = 0.2  # เกณฑ์ใบงาน Lab 03: VCE ≤ 0.2 V (Lab 2 เดิม 0.3 V)
VBE_MIN = 0.0
VBE_MAX = 1.0
_UNITS = {"ohm": 1.0, "kohm": 1_000.0, "mohm": 1_000_000.0}
# ชื่อที่แสดงให้ผู้ใช้: (ภาษาอังกฤษ, ภาษาไทย)
_PARAMS = {
    "vcc": ("VCC", "VCC"),
    "rb": ("RB", "RB"),
    "r1": ("R1", "R1"),
    "r2": ("R2", "R2"),
    "rc": ("RC", "RC"),
    "re": ("RE", "RE"),
    "beta": ("beta (β)", "β"),
    "vbe": ("VBE", "VBE"),
}


class BiasInputError(ValueError):
    """ค่าที่ผู้ใช้กรอกไม่ถูกต้อง หรือใช้คำนวณไม่ได้"""


@dataclass(frozen=True)
class BiasResult:
    """ผลลัพธ์การคำนวณ DC bias (SI units) พร้อม region และ warnings"""

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


def _require_number(name: str, value: float) -> float:
    """แปลงเป็น float และกันค่าที่ไม่ใช่จำนวนจริงจำกัด (เช่น inf, nan)"""
    label, thai = _PARAMS[name]
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise BiasInputError(
            f"{label} is not a number (ค่า {thai} ไม่ใช่ตัวเลข)"
        ) from None
    if not math.isfinite(number):
        raise BiasInputError(
            f"{label} must be a finite number (ค่า {thai} ต้องเป็นจำนวนจริงจำกัด)"
        )
    return number


def _require_positive(name: str, value: float) -> float:
    number = _require_number(name, value)
    if number <= 0:
        label, thai = _PARAMS[name]
        raise BiasInputError(
            f"{label} must be greater than 0 ({thai} ต้องมากกว่า 0)"
        )
    return number


def parse_resistance(raw: str, unit: str) -> float:
    """แปลงค่าความต้านทานที่ผู้ใช้กรอกเป็นโอห์ม

    ``raw`` อาจมีช่องว่างหัวท้ายได้ และ ``unit`` ต้องเป็น ``"ohm"``, ``"kohm"`` หรือ ``"mohm"``
    """
    text = str(raw).strip()
    try:
        value = float(text)
    except (TypeError, ValueError):
        raise BiasInputError(
            "Resistance is not a number (ค่าตัวต้านทานไม่ใช่ตัวเลข)"
        ) from None

    if unit not in _UNITS:
        raise BiasInputError("Unknown resistance unit (หน่วยไม่ถูกต้อง)")

    ohms = value * _UNITS[unit]
    if not math.isfinite(ohms) or ohms <= 0:
        raise BiasInputError(
            "Resistance must be greater than 0 Ω (ค่าตัวต้านทานต้องมากกว่า 0 Ω)"
        )
    return ohms


def _require_beta(value: float) -> float:
    return _require_positive("beta", value)


def _require_vbe(value: float) -> float:
    vbe = _require_number("vbe", value)
    if not VBE_MIN < vbe < VBE_MAX:
        raise BiasInputError(
            f"VBE must be between {VBE_MIN:g} and {VBE_MAX:g} V "
            f"(VBE ต้องอยู่ระหว่าง {VBE_MIN:g} ถึง {VBE_MAX:g} V)"
        )
    return vbe


def _solve_bias(
    vcc: float,
    vth: float,
    rth: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> BiasResult:
    """แก้สมการ DC bias จาก Thévenin equivalent ที่ขา Base

    ใช้ร่วมทั้งสามโหมด: Divider ส่ง VTH/RTH จาก R1,R2 ส่วน Fixed และ Emitter
    ส่ง VTH = VCC, RTH = RB และ Fixed ส่ง RE = 0

    ``vcc`` เป็นแรงดันไฟเลี้ยงจริง (ใช้คิด VC) ซึ่งต่างจาก ``vth`` ในโหมด Divider
    ผู้เรียกต้องตรวจค่า input มาแล้ว (ฟังก์ชันนี้ไม่ตรวจซ้ำ)
    """
    # Cutoff: ไบแอสที่ฐานไม่พอจะทำให้เบส-อีมิตเตอร์ forward bias
    if vth <= vbe:
        ve = 0.0
        return BiasResult(
            vth=vth,
            rth=rth,
            ib=0.0,
            ic=0.0,
            ie=0.0,
            ve=ve,
            vb=vbe,
            vc=vcc,
            vce=vcc - ve,
            region="cutoff",
            warnings=(
                "Cutoff: VTH <= VBE so IB = IC = 0; the Forward-Active model "
                "does not apply (VTH <= VBE ทำให้ IB = IC = 0 "
                "แบบจำลอง Forward-Active ใช้ไม่ได้)",
            ),
        )

    ib = (vth - vbe) / (rth + (beta + 1) * re)
    ic = beta * ib
    ie = (beta + 1) * ib
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    if vce < VCE_SAT:
        return BiasResult(
            vth=vth,
            rth=rth,
            ib=ib,
            ic=ic,
            ie=ie,
            ve=ve,
            vb=vb,
            vc=vc,
            vce=vce,
            region="saturation",
            warnings=(
                f"Saturation: VCE < {VCE_SAT:g} V so the transistor is saturated; "
                "the Forward-Active model does not apply "
                f"(VCE < {VCE_SAT:g} V ทรานซิสเตอร์อิ่มตัว "
                "แบบจำลอง Forward-Active ใช้ไม่ได้)",
            ),
        )

    return BiasResult(
        vth=vth,
        rth=rth,
        ib=ib,
        ic=ic,
        ie=ie,
        ve=ve,
        vb=vb,
        vc=vc,
        vce=vce,
        region="active",
        warnings=(),
    )


def calculate_dc_bias(
    vcc: float,
    r1: float,
    r2: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> BiasResult:
    """คำนวณ DC bias ของวงจร voltage-divider bias

    พารามิเตอร์ตัวต้านทานเป็นโอห์ม (แปลงหน่วยมาก่อนด้วย :func:`parse_resistance`)
    คืนค่า :class:`BiasResult` โดย ``region`` เป็น ``"active"``, ``"cutoff"``
    หรือ ``"saturation"``
    """
    vcc = _require_positive("vcc", vcc)
    r1 = _require_positive("r1", r1)
    r2 = _require_positive("r2", r2)
    rc = _require_positive("rc", rc)
    re = _require_positive("re", re)
    beta = _require_beta(beta)
    vbe = _require_vbe(vbe)

    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)
    return _solve_bias(vcc, vth, rth, rc, re, beta, vbe)


def calculate_fixed_bias(
    vcc: float, rb: float, rc: float, beta: float, vbe: float
) -> BiasResult:
    """คำนวณ DC bias ของวงจร fixed bias (RB จาก VCC ไป Base, ไม่มี RE)

    IB = (VCC - VBE) / RB และ VE = 0 V เพราะ Emitter ต่อลงกราวด์โดยตรง
    """
    vcc = _require_positive("vcc", vcc)
    rb = _require_positive("rb", rb)
    rc = _require_positive("rc", rc)
    beta = _require_beta(beta)
    vbe = _require_vbe(vbe)

    return _solve_bias(vcc, vcc, rb, rc, 0.0, beta, vbe)


def calculate_emitter_bias(
    vcc: float,
    rb: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> BiasResult:
    """คำนวณ DC bias ของวงจร emitter bias แบบแหล่งจ่ายเดียว

    RB ต่อจาก VCC ไป Base และ RE ต่อจาก Emitter ลงกราวด์:
    IB = (VCC - VBE) / (RB + (beta + 1) * RE)
    """
    vcc = _require_positive("vcc", vcc)
    rb = _require_positive("rb", rb)
    rc = _require_positive("rc", rc)
    re = _require_positive("re", re)
    beta = _require_beta(beta)
    vbe = _require_vbe(vbe)

    return _solve_bias(vcc, vcc, rb, rc, re, beta, vbe)
