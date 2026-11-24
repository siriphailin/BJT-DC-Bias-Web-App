"""ngspice adapter for the Lab 04 reference CE voltage-divider amplifier.

This module is deliberately free of Flask imports. It validates form values,
builds a netlist from *numbers only*, and (in later tasks) runs the engine and
parses its text output. ``app.py`` owns presentation and HTTP concerns.
"""

from __future__ import annotations

import html
import math
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


UNIT = {"ohm": 1.0, "kohm": 1_000.0, "mohm": 1_000_000.0}
AMPLITUDE_UNIT = {"mv": 1e-3, "v": 1.0}
FREQUENCY_UNIT = {"hz": 1.0, "khz": 1e3, "mhz": 1e6}
ANALYSES = ("dc", "ac", "tran")

TITLE = "* CE voltage-divider reference - ENG29 2121 Lab 04"
MODEL_LINE = (
    ".MODEL QNPN NPN(BF=100 IS=1E-14 VAF=100 RB=0 CJE=0 CJC=0 TF=0 TR=0)"
)


class ValidationError(ValueError):
    """Raised when a value cannot safely be written into a netlist."""


@dataclass(frozen=True)
class SimInput:
    """Validated SI values: volts, ohms, volts peak, hertz."""

    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    rl: float
    amplitude_v: float
    frequency_hz: float


@dataclass(frozen=True)
class SimResult:
    """One engine run. ``None`` series mean 'no result' — never fake data."""

    analysis: str
    status: str
    message: str
    netlist: str
    log_excerpt: str
    values: dict | None
    ac_points: tuple | None
    tran_points: tuple | None
    provenance: dict


def _fmt(value: float) -> str:
    """Format a finite number for a netlist. Injection-safe by construction."""
    if not math.isfinite(value):
        raise ValidationError(
            "Non-finite value cannot be written to the netlist "
            "(ค่าที่ไม่ใช่จำนวนจริงเขียนลง netlist ไม่ได้)"
        )
    return f"{value:.6g}"


def _number(raw, label, errors, lo, hi, *, scale=1.0, unit=""):
    """Parse, bounds-check and scale one numeric form field."""
    try:
        value = float(str(raw).strip())
    except (TypeError, ValueError):
        errors.append(f"{label} must be a number ({label} ต้องเป็นตัวเลข)")
        return None
    if not math.isfinite(value):
        errors.append(
            f"{label} must be finite ({label} ต้องเป็นจำนวนที่ไม่ใช่ infinity หรือ NaN)"
        )
        return None
    if value < lo or value > hi:
        suffix = f" {unit}" if unit else ""
        errors.append(
            f"{label} must be between {_fmt(lo)} and {_fmt(hi)}{suffix} "
            f"({label} ต้องอยู่ระหว่าง {_fmt(lo)} กับ {_fmt(hi)}{suffix})"
        )
        return None
    return value * scale


def _scaled_number(raw, unit_raw, units, label, errors, lo, hi, unit_hint):
    """Parse a value with a selectable unit, clamp it to SI bounds, return SI."""
    unit = str(unit_raw or "").strip().lower()
    if unit not in units:
        errors.append(
            f"{label} unit must be one of {', '.join(units)} "
            f"({label} ต้องเป็นหน่วยที่รองรับ)"
        )
        return None
    try:
        value = float(str(raw).strip())
    except (TypeError, ValueError):
        errors.append(f"{label} must be a number ({label} ต้องเป็นตัวเลข)")
        return None
    if not math.isfinite(value):
        errors.append(
            f"{label} must be finite ({label} ต้องเป็นจำนวนที่ไม่ใช่ infinity หรือ NaN)"
        )
        return None
    scaled = value * units[unit]
    if scaled < lo or scaled > hi:
        errors.append(
            f"{label} must be between {unit_hint} ({label} ต้องอยู่ในช่วง {unit_hint})"
        )
        return None
    return scaled


def _resistance(raw, unit_raw, label, errors):
    """Parse a resistance plus its unit into ohms."""
    unit = str(unit_raw or "").strip().lower()
    if unit not in UNIT:
        errors.append(
            f"{label} unit must be ohm/kohm/mohm "
            f"({label} ต้องเป็นหน่วย Ω/kΩ/MΩ)"
        )
        return None
    try:
        value = float(str(raw).strip())
    except (TypeError, ValueError):
        errors.append(f"{label} must be a number ({label} ต้องเป็นตัวเลข)")
        return None
    if not math.isfinite(value):
        errors.append(
            f"{label} must be finite ({label} ต้องเป็นจำนวนที่ไม่ใช่ infinity หรือ NaN)"
        )
        return None
    if value <= 0:
        errors.append(
            f"{label} must be greater than 0 Ω ({label} ต้องมากกว่า 0 Ω)"
        )
        return None
    ohms = value * UNIT[unit]
    if ohms > 10_000_000.0:
        errors.append(
            f"{label} must be at most 10 MΩ ({label} ต้องไม่เกิน 10 MΩ)"
        )
        return None
    return ohms


def validate_sim_input(raw: dict) -> tuple[SimInput | None, list[str]]:
    """Validate simulator form data; return ``(params, errors)``.

    Every value is converted to SI here, so downstream code never needs to
    know about Ω/kΩ/MΩ, mV/V or Hz/kHz/MHz. Raw strings never reach the
    netlist builder. Old ``amplitude_mv`` / ``frequency_khz`` field names are
    accepted as a fallback so existing links and tests keep working.
    """
    raw = raw or {}
    errors: list[str] = []

    vcc = _number(raw.get("vcc", ""), "VCC", errors, 0.0, 24.0, unit="V")
    r1 = _resistance(raw.get("r1", ""), raw.get("r1_unit", ""), "R1", errors)
    r2 = _resistance(raw.get("r2", ""), raw.get("r2_unit", ""), "R2", errors)
    rc = _resistance(raw.get("rc", ""), raw.get("rc_unit", ""), "RC", errors)
    re = _resistance(raw.get("re", ""), raw.get("re_unit", ""), "RE", errors)
    rl = _resistance(raw.get("rl", "10"), raw.get("rl_unit", "kohm"), "RL", errors)

    amplitude_raw = raw.get("amplitude", raw.get("amplitude_mv", ""))
    amplitude_unit = raw.get("amplitude_unit", "mv")
    amplitude_v = _scaled_number(
        amplitude_raw, amplitude_unit, AMPLITUDE_UNIT, "Amplitude", errors,
        1e-3, 100.0, "1 mV–100 V",
    )
    frequency_raw = raw.get("frequency", raw.get("frequency_khz", ""))
    frequency_unit = raw.get("frequency_unit", "khz")
    frequency_hz = _scaled_number(
        frequency_raw, frequency_unit, FREQUENCY_UNIT, "Frequency", errors,
        100.0, 100e6, "100 Hz–100 MHz",
    )

    if errors:
        return None, errors
    return (
        SimInput(
            vcc=vcc, r1=r1, r2=r2, rc=rc, re=re, rl=rl,
            amplitude_v=amplitude_v, frequency_hz=frequency_hz,
        ),
        [],
    )


def build_netlist(params: SimInput, analysis: str) -> str:
    """Return a complete ngspice deck for exactly one analysis.

    Notes from real ngspice-47 runs (see docs/validation.md §9.3):
      * no ``-r`` may be passed by the caller, otherwise ``.print`` is ignored;
      * ``.print ac`` must not contain ``freq`` — it is column 1 automatically;
      * ``.tran`` needs a strictly positive TSTEP.
    """
    if analysis not in ANALYSES:
        raise ValidationError(
            f"Unknown analysis: {analysis} (การวิเคราะห์ไม่รู้จัก)"
        )

    vcc = _fmt(params.vcc)
    r1 = _fmt(params.r1)
    r2 = _fmt(params.r2)
    rc = _fmt(params.rc)
    re = _fmt(params.re)
    rl = _fmt(params.rl)
    amp = _fmt(params.amplitude_v)
    freq = _fmt(params.frequency_hz)

    if analysis == "tran":
        tstop = min(5.0 / params.frequency_hz, 0.05)
        tstep = tstop / 500.0
        tran_line = f".tran {_fmt(tstep)} {_fmt(tstop)} 0 {_fmt(tstep)}"
        tran_print = ".print tran time v(vin) v(vout)"
    else:
        # Comment text must not accidentally contain '.tran 0 ' for other modes.
        tran_line = "* Transient analysis (not selected)"
        tran_print = "* Transient print (not selected)"

    lines = [
        TITLE,
        f"VCC  VCC 0 {vcc}",
        "VIC  VCC RCTOP 0",
        f"R1   VCC BASE {r1}",
        f"R2   BASE 0 {r2}",
        f"RC   RCTOP COL {rc}",
        f"RE   EMI 0 {re}",
        "Q1   COL BASE EMI QNPN",
        "CIN  VIN BASE 10u",
        "COUT COL VOUT 10u",
        f"RL   VOUT 0 {rl}",
        f"VIN  VIN 0 DC 0 AC 1 SIN(0 {amp} {freq})",
        MODEL_LINE,
        ".op" if analysis == "dc" else "* DC operating point (not selected)",
        (
            ".print op v(base) v(col) v(emi) i(vic)"
            if analysis == "dc" else "* DC print (not selected)"
        ),
        ".ac dec 20 1 1Meg" if analysis == "ac" else "* AC sweep (not selected)",
        (
            ".print ac vdb(vout) vp(vout) vdb(vin) vp(vin)"
            if analysis == "ac" else "* AC print (not selected)"
        ),
        tran_line,
        tran_print,
        ".END",
    ]
    return "\n".join(lines) + "\n"


def engine_version(engine: str) -> str:
    """Probe the engine banner; return ``'unknown'`` when unavailable."""
    try:
        proc = subprocess.run(
            [engine, "-v"], capture_output=True, text=True,
            timeout=10, shell=False, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    match = re.search(r"ngspice-[A-Za-z0-9_.]+", proc.stdout + proc.stderr)
    return match.group(0) if match else "unknown"


class EmptyOutputError(RuntimeError):
    """The engine ran but its log contained no usable table."""


class RunFailedError(RuntimeError):
    """The engine returned a non-zero exit code."""


class EngineNotFoundError(RuntimeError):
    """No usable console engine is available."""


class EngineTimeoutError(RuntimeError):
    """The engine exceeded the time limit."""


MODEL_LABEL = (
    "QNPN(BF=100 IS=1E-14 VAF=100, CJE=CJC=TF=TR=0; teaching model)"
)
_NO_DATA = '<p class="sim-no-data">No data (ไม่มีข้อมูลจากการรัน SPICE)</p>'


def _excerpt(text: str, limit: int = 4000) -> str:
    text = text or ""
    return text[-limit:] if len(text) > limit else text


def _tables(text: str, header_re: str) -> list[tuple[list[str], list[list[float]]]]:
    """Extract `.print` tables: (header tokens, numeric rows without Index).

    The regex matches the whole header so wrapped lines and repeated headers
    (ngspice reprints one every ~60 rows after a form feed) both work.
    """
    text = text.replace("\f", "\n")
    matches = list(re.finditer(header_re, text))
    tables = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        rows = []
        for line in text[match.end():end].splitlines():
            parts = line.split()
            if len(parts) < 2 or not parts[0].isdigit():
                continue
            try:
                rows.append([float(p) for p in parts[1:]])
            except ValueError:
                continue
        tables.append((match.group(0).split(), rows))
    return tables


def parse_op(log_text: str) -> dict:
    tables = _tables(
        log_text, r"Index\s+v\(base\)\s+v\(col\)\s+v\(emi\)\s+vic#branch"
    )
    if not tables or not tables[0][1]:
        raise EmptyOutputError(
            "No operating-point table in log (ไม่พบตาราง operating point ใน log)"
        )
    vb, vc, ve, ic_a = tables[0][1][0][:4]
    return {
        "vb": vb,
        "ve": ve,
        "vc": vc,
        "vce": vc - ve,
        "ic_mA": ic_a * 1000.0,
    }


def parse_ac(log_text: str) -> tuple:
    """Join the vout/vin tables by frequency; convert vp() radians to degrees."""
    tables = _tables(
        log_text, r"Index\s+frequency\s+vdb\([^)]+\)\s+vp\([^)]+\)"
    )
    out_rows: list[list[float]] = []
    in_rows: list[list[float]] = []
    for headers, rows in tables:
        if "vdb(vout)" in headers:
            out_rows.extend(rows)
        elif "vdb(vin)" in headers:
            in_rows.extend(rows)
    if not out_rows or not in_rows:
        raise EmptyOutputError(
            "No AC tables in log (ไม่พบตาราง AC ใน log)"
        )
    vin_by_freq = {round(row[0], 6): row for row in in_rows}
    points = []
    for row in out_rows:
        freq, vdb_out, vp_out = row[:3]
        reference = vin_by_freq.get(round(freq, 6))
        if reference is None:
            continue
        gain_db = vdb_out - reference[1]
        phase_deg = math.degrees(vp_out - reference[2])
        points.append((freq, gain_db, phase_deg, 10 ** (gain_db / 20.0)))
    if not points:
        raise EmptyOutputError(
            "AC tables could not be paired (จับคู่ตาราง AC ไม่ได้)"
        )
    return tuple(sorted(points))


def parse_tran(log_text: str) -> tuple:
    tables = _tables(log_text, r"Index\s+time\s+v\(vin\)\s+v\(vout\)")
    points = []
    for _, rows in tables:
        points.extend((row[0], row[1], row[2]) for row in rows if len(row) >= 3)
    if not points:
        raise EmptyOutputError(
            "No transient table in log (ไม่พบตาราง transient ใน log)"
        )
    return tuple(points)


def _engine_roots() -> list[Path]:
    """Common install locations searched for the ngspice console binary."""
    keys = ("LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)")
    roots = [Path(os.environ[key]) for key in keys if os.environ.get(key)]
    roots.extend((
        Path.home() / "AppData" / "Local" / "Programs",
        Path(os.environ.get("ProgramData", "C:/ProgramData")) / "chocolatey" / "lib",
    ))
    return roots


def find_ngspice_engine() -> str | None:
    """Find `ngspice_con.exe` on PATH or in common install folders.

    Only bounded, ngspice-named folders are walked so startup stays fast;
    on this machine it finds
    `%LOCALAPPDATA%\\Programs\\ngspice-47\\Spice64\\bin\\ngspice_con.exe`.
    """
    found = shutil.which("ngspice_con")
    if found:
        return found
    patterns = (
        "ngspice*/Spice64/bin/ngspice_con.exe",
        "ngspice*/bin/ngspice_con.exe",
        "ngspice*/tools/Spice64/bin/ngspice_con.exe",
        "ngspice*/tools/ngspice-*/Spice64/bin/ngspice_con.exe",
    )
    for root in _engine_roots():
        if not root.is_dir():
            continue
        for pattern in patterns:
            for candidate in root.glob(pattern):
                if candidate.is_file():
                    return str(candidate)
    return shutil.which("ngspice")


def resolve_engine() -> str | None:
    """Prefer the console binary; the GUI `ngspice.exe` yields no output."""
    env_path = os.environ.get("NGSPICE_ENGINE", "").strip()
    if env_path:
        # Explicit override is honoured even when it is wrong: that lets an
        # operator simulate "Engine not ready" instead of silently falling
        # back to a stale working engine.
        return env_path
    return find_ngspice_engine()


def run_analysis(params: SimInput, analysis: str, workdir, engine: str) -> SimResult:
    """Run one ngspice analysis in a fresh workdir and return a SimResult.

    ``-r`` is intentionally absent: with a rawfile requested, ngspice-47 skips
    every ``.print`` line and the log has no parseable table.
    """
    net = build_netlist(params, analysis)
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    netlist_path = workdir / "circuit.cir"
    log_path = workdir / "run.log"
    netlist_path.write_text(net, encoding="utf-8")

    directives = {
        "dc": ".op",
        "ac": ".ac dec 20 1 1Meg",
        "tran": "transient (tstop from frequency)",
    }
    provenance = {
        "engine_path": str(engine),
        "engine_version": "unavailable",
        "model": MODEL_LABEL,
        "analysis_directive": directives[analysis],
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "netlist_path": str(netlist_path),
        "log_path": str(log_path),
    }

    def make(status, message, *, values=None, ac=None, tran=None, log_text=""):
        return SimResult(
            analysis=analysis, status=status, message=message, netlist=net,
            log_excerpt=_excerpt(log_text), values=values, ac_points=ac,
            tran_points=tran, provenance=provenance,
        )

    if not engine or not (Path(engine).is_file() or shutil.which(engine)):
        return make(
            "ENGINE_NOT_FOUND",
            "Engine not ready — NGspice executable not found "
            "(Engine ยังไม่พร้อม — ไม่พบโปรแกรม ngspice ในเครื่อง)",
        )
    try:
        proc = subprocess.run(
            [str(engine), "-b", "-o", "run.log", "circuit.cir"],
            cwd=str(workdir), capture_output=True, text=True,
            timeout=30, shell=False, check=False,
        )
    except subprocess.TimeoutExpired:
        return make(
            "TIMEOUT",
            "NGspice run timed out after 30 s (การรัน ngspice หมดเวลา 30 วินาที)",
        )
    except OSError as exc:
        return make(
            "RUN_FAILED",
            f"Could not start engine: {exc} (เริ่มโปรแกรม ngspice ไม่ได้)",
        )

    log_text = (
        log_path.read_text(encoding="utf-8", errors="replace")
        if log_path.is_file() else ""
    )
    provenance["engine_version"] = engine_version(str(engine))
    if proc.returncode != 0:
        return make(
            "RUN_FAILED",
            f"NGspice exited with code {proc.returncode} "
            f"(ngspice จบด้วยโค้ด {proc.returncode})",
            log_text=log_text + "\n" + (proc.stderr or ""),
        )
    try:
        if analysis == "dc":
            values = parse_op(log_text)
            return make("SUCCESS", "DC operating point complete", values=values,
                        log_text=log_text)
        if analysis == "ac":
            points = parse_ac(log_text)
            return make("SUCCESS", "AC sweep complete", ac=points,
                        log_text=log_text)
        points = parse_tran(log_text)
        return make("SUCCESS", "Transient run complete", tran=points,
                    log_text=log_text)
    except EmptyOutputError as exc:
        return make(
            "EMPTY_OUTPUT",
            f"{exc} (engine รันแต่ไม่มีข้อมูลให้แสดง — ไม่แสดงผลเก่า)",
            log_text=log_text,
        )


def find_low_cutoff(ac_points: tuple) -> float | None:
    """Low −3 dB frequency (Hz), or ``None`` when not inside the sweep."""
    if not ac_points:
        return None
    ordered = sorted(ac_points)
    target = max(p[1] for p in ordered) - 3.0
    for (f1, g1, _, _), (f2, g2, _, _) in zip(ordered, ordered[1:]):
        if g1 <= target <= g2 and g2 > g1:
            ratio = (target - g1) / (g2 - g1)
            return math.exp(math.log(f1) + ratio * (math.log(f2) - math.log(f1)))
    return None


def _axis_number(value: float) -> str:
    if value == 0:
        return "0"
    if abs(value) >= 1000 or abs(value) < 0.01:
        return f"{value:.2e}"
    return f"{value:.3g}"


def _map_x(value, x_min, x_max, log_x, x0, width):
    if log_x:
        lo, hi = math.log10(x_min), math.log10(x_max)
        ratio = (math.log10(value) - lo) / (hi - lo) if hi > lo else 0.5
    else:
        ratio = (value - x_min) / (x_max - x_min) if x_max > x_min else 0.5
    return x0 + ratio * width


def _map_y(value, y_min, y_max, y0, height):
    ratio = (value - y_min) / (y_max - y_min) if y_max > y_min else 0.5
    return y0 + height - ratio * height


def svg_line_chart(series, x_label, y_label, *, log_x=False, height=320,
                   width=760, x_min=None, x_max=None, reference_lines=()):
    """Render one small, dependency-free SVG line chart from real points.

    ``series`` is an iterable of ``(label, colour, points)`` where each point is
    ``(x, y)`` in the units printed on the axes.
    """
    charts = [(label, colour, tuple(points)) for label, colour, points in series]
    charts = [chart for chart in charts if chart[2]]
    if not charts:
        return _NO_DATA

    all_x = [x for _, _, pts in charts for x, _ in pts]
    all_y = [y for _, _, pts in charts for _, y in pts]
    if x_min is None:
        x_min = min(all_x)
    if x_max is None:
        x_max = max(all_x)
    if log_x and (x_min <= 0 or x_max <= 0):
        return _NO_DATA
    y_min, y_max = min(all_y), max(all_y)
    if y_min == y_max:
        y_min -= 1.0
        y_max += 1.0
    else:
        pad = (y_max - y_min) * 0.08
        y_min -= pad
        y_max += pad

    left, right, top, bottom = 78, 26, 38, 58
    plot_x, plot_y = left, top
    plot_w, plot_h = width - left - right, height - top - bottom
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{html.escape(x_label)} versus {html.escape(y_label)}">',
        '<rect x="0" y="0" width="' + str(width) + '" height="' + str(height) +
        '" fill="#ffffff"/>',
    ]

    for i in range(5):
        value = y_min + (y_max - y_min) * i / 4
        py = _map_y(value, y_min, y_max, plot_y, plot_h)
        parts.append(
            f'<line x1="{plot_x}" y1="{py:.1f}" x2="{plot_x + plot_w}" y2="{py:.1f}" '
            f'stroke="#e2e8f0" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{plot_x - 8}" y="{py + 4:.1f}" text-anchor="end" '
            f'font-size="11" fill="#475569">{html.escape(_axis_number(value))}</text>'
        )

    if log_x:
        x_ticks = [10 ** decade for decade in
                   range(math.floor(math.log10(x_min)),
                         math.ceil(math.log10(x_max)) + 1)
                   if x_min <= 10 ** decade <= x_max]
    else:
        x_ticks = [x_min + (x_max - x_min) * i / 4 for i in range(5)]
    for value in x_ticks:
        px = _map_x(value, x_min, x_max, log_x, plot_x, plot_w)
        parts.append(
            f'<line x1="{px:.1f}" y1="{plot_y}" x2="{px:.1f}" '
            f'y2="{plot_y + plot_h}" stroke="#e2e8f0" stroke-width="1"/>'
        )
        label = f"10^{int(round(math.log10(value)))}" if log_x else _axis_number(value)
        parts.append(
            f'<text x="{px:.1f}" y="{plot_y + plot_h + 18}" text-anchor="middle" '
            f'font-size="11" fill="#475569">{html.escape(label)}</text>'
        )

    for value, label, colour in reference_lines:
        if not y_min <= value <= y_max:
            continue
        py = _map_y(value, y_min, y_max, plot_y, plot_h)
        parts.append(
            f'<line x1="{plot_x}" y1="{py:.1f}" x2="{plot_x + plot_w}" y2="{py:.1f}" '
            f'stroke="{html.escape(colour)}" stroke-width="1" stroke-dasharray="5 4"/>'
        )
        parts.append(
            f'<text x="{plot_x + 6}" y="{py - 5:.1f}" font-size="11" '
            f'fill="{html.escape(colour)}">{html.escape(label)}</text>'
        )

    parts.append(
        f'<line x1="{plot_x}" y1="{plot_y + plot_h}" x2="{plot_x + plot_w}" '
        f'y2="{plot_y + plot_h}" stroke="#94a3b8"/>'
        f'<line x1="{plot_x}" y1="{plot_y}" x2="{plot_x}" '
        f'y2="{plot_y + plot_h}" stroke="#94a3b8"/>'
    )
    for label, colour, pts in charts:
        coords = " ".join(
            f"{_map_x(x, x_min, x_max, log_x, plot_x, plot_w):.1f},"
            f"{_map_y(y, y_min, y_max, plot_y, plot_h):.1f}" for x, y in pts
        )
        parts.append(
            f'<polyline fill="none" stroke="{html.escape(colour)}" '
            f'stroke-width="2" points="{coords}"/>'
        )

    for i, (label, colour, _) in enumerate(charts):
        lx = plot_x + i * 150
        parts.append(
            f'<line x1="{lx}" y1="16" x2="{lx + 22}" y2="16" '
            f'stroke="{html.escape(colour)}" stroke-width="3"/>'
            f'<text x="{lx + 28}" y="20" font-size="12" fill="#334155">'
            f'{html.escape(label)}</text>'
        )
    parts.append(
        f'<text x="{plot_x + plot_w / 2:.1f}" y="{height - 12}" '
        f'text-anchor="middle" font-size="12" fill="#334155">'
        f'{html.escape(x_label)}</text>'
        f'<text transform="rotate(-90 18 {plot_y + plot_h / 2:.1f})" x="18" '
        f'y="{plot_y + plot_h / 2:.1f}" text-anchor="middle" font-size="12" '
        f'fill="#334155">{html.escape(y_label)}</text>'
        '</svg>'
    )
    return "".join(parts)


def svg_bode(ac_points: tuple) -> str:
    if not ac_points:
        return _NO_DATA
    freqs = [p[0] for p in ac_points]
    midband = max(p[1] for p in ac_points)
    gain_panel = svg_line_chart(
        (("Vout/Vin", "#2563eb", [(p[0], p[1]) for p in ac_points]),),
        "Frequency (Hz)", "Gain (dB)", log_x=True, height=300,
        x_min=min(freqs), x_max=max(freqs),
        reference_lines=((midband - 3.0, "-3 dB", "#94a3b8"),),
    )
    phase_panel = svg_line_chart(
        (("Phase", "#dc2626", [(p[0], p[2]) for p in ac_points]),),
        "Frequency (Hz)", "Phase (deg)", log_x=True, height=300,
        x_min=min(freqs), x_max=max(freqs),
    )
    return gain_panel + phase_panel


def svg_waveform(tran_points: tuple) -> str:
    if not tran_points:
        return _NO_DATA
    return svg_line_chart(
        (
            ("Vin", "#64748b", [(p[0] * 1000.0, p[1]) for p in tran_points]),
            ("Vout", "#ea580c", [(p[0] * 1000.0, p[2]) for p in tran_points]),
        ),
        "Time (ms)", "Voltage (V)", height=340,
    )
