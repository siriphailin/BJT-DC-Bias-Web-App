import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from spice_engine import (
    EmptyOutputError, ValidationError, build_netlist, engine_version,
    parse_ac, parse_op, parse_tran, resolve_engine, run_analysis,
    svg_bode, svg_waveform, validate_sim_input, _fmt,
)

REAL_ENGINE = (
    Path.home() / "AppData" / "Local" / "Programs" / "ngspice-47"
    / "Spice64" / "bin" / "ngspice_con.exe"
)


BASE = {
    "vcc": "12", "r1": "100", "r1_unit": "kohm", "r2": "22", "r2_unit": "kohm",
    "rc": "2.2", "rc_unit": "kohm", "re": "1", "re_unit": "kohm",
    "rl": "10", "rl_unit": "kohm",
    "amplitude": "10", "amplitude_unit": "mv",
    "frequency": "1", "frequency_unit": "khz",
}


class TestValidate(unittest.TestCase):
    def test_valid(self):
        params, errors = validate_sim_input(BASE)
        self.assertEqual(errors, [])
        self.assertAlmostEqual(params.vcc, 12.0)
        self.assertAlmostEqual(params.r1, 100_000.0)
        self.assertAlmostEqual(params.r2, 22_000.0)
        self.assertAlmostEqual(params.rc, 2_200.0)
        self.assertAlmostEqual(params.re, 1_000.0)
        self.assertAlmostEqual(params.rl, 10_000.0)
        self.assertAlmostEqual(params.amplitude_v, 0.010)
        self.assertAlmostEqual(params.frequency_hz, 1_000.0)

    def test_zero_re_rejected(self):
        _, errors = validate_sim_input(dict(BASE, re="0"))
        self.assertTrue(any("RE" in e for e in errors))

    def test_zero_rl_rejected(self):
        _, errors = validate_sim_input(dict(BASE, rl="0"))
        self.assertTrue(any("RL" in e for e in errors))

    def test_selectable_source_units(self):
        params, errors = validate_sim_input(dict(
            BASE, amplitude="1", amplitude_unit="v",
            frequency="2", frequency_unit="mhz",
        ))
        self.assertEqual(errors, [])
        self.assertAlmostEqual(params.amplitude_v, 1.0)
        self.assertAlmostEqual(params.frequency_hz, 2_000_000.0)

    def test_legacy_source_fields_still_work(self):
        params, errors = validate_sim_input({
            "vcc": "12", "r1": "100", "r1_unit": "kohm",
            "r2": "22", "r2_unit": "kohm", "rc": "2.2", "rc_unit": "kohm",
            "re": "1", "re_unit": "kohm", "rl": "10", "rl_unit": "kohm",
            "amplitude_mv": "30", "frequency_khz": "2",
        })
        self.assertEqual(errors, [])
        self.assertAlmostEqual(params.amplitude_v, 0.030)
        self.assertAlmostEqual(params.frequency_hz, 2_000.0)

    def test_injection_rejected(self):
        for key in ("amplitude", "frequency", "vcc", "rl"):
            _, errors = validate_sim_input(dict(BASE, **{key: "10; .op"}))
            self.assertTrue(errors)

    def test_out_of_range(self):
        _, errors = validate_sim_input(dict(BASE, frequency="0"))
        self.assertTrue(errors)

    def test_bad_unit_rejected(self):
        _, errors = validate_sim_input(dict(BASE, re_unit="farad"))
        self.assertTrue(any("RE" in e for e in errors))
        _, errors = validate_sim_input(dict(BASE, amplitude_unit="farad"))
        self.assertTrue(any("Amplitude" in e for e in errors))
        _, errors = validate_sim_input(dict(BASE, frequency_unit="farad"))
        self.assertTrue(any("Frequency" in e for e in errors))

    def test_missing_field_rejected(self):
        raw = dict(BASE)
        del raw["vcc"]
        params, errors = validate_sim_input(raw)
        self.assertIsNone(params)
        self.assertTrue(any("VCC" in e for e in errors))


class TestNetlist(unittest.TestCase):
    def setUp(self):
        self.params, errors = validate_sim_input(BASE)
        self.assertEqual(errors, [])

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

    def test_values_are_formatted_not_raw(self):
        net = build_netlist(self.params, "dc")
        self.assertIn("VCC  VCC 0 12", net)
        self.assertIn("R1   VCC BASE 100000", net)
        self.assertIn("RC   RCTOP COL 2200", net)
        self.assertIn("RL   VOUT 0 10000", net)

    def test_custom_rl_in_netlist(self):
        params, errors = validate_sim_input(dict(BASE, rl="4.7", rl_unit="kohm"))
        self.assertEqual(errors, [])
        self.assertIn("RL   VOUT 0 4700", build_netlist(params, "dc"))

    def test_fmt_is_finite(self):
        self.assertEqual(_fmt(100_000.0), "100000")
        with self.assertRaises(ValidationError):
            _fmt(float("inf"))
        with self.assertRaises(ValidationError):
            _fmt(float("nan"))


class TestParsers(unittest.TestCase):
    def test_parse_op_real_table_format(self):
        log = ("Index   v(base)         v(col)          v(emi)          vic#branch\n"
               "---------------------------------------------------------------\n"
               "0\t1.949112e+00\t9.189410e+00\t1.289454e+00\t1.277541e-03\n")
        d = parse_op(log)
        self.assertAlmostEqual(d["vb"], 1.949112)
        self.assertAlmostEqual(d["ve"], 1.289454)
        self.assertAlmostEqual(d["vc"], 9.189410)
        self.assertAlmostEqual(d["vce"], 9.189410 - 1.289454, places=6)
        self.assertAlmostEqual(d["ic_mA"], 1.277541)

    def test_parse_ac_radians_to_degrees(self):
        # ngspice prints 2 tables (vout then vin); vp() is in radians.
        log = ("Index   frequency       vdb(vout)       vp(vout)\n"
               "0\t1.000000e+03\t4.859789e+00\t-3.139260e+00\n"
               "1\t1.122018e+03\t4.850000e+00\t-3.130000e+00\n"
               "Index   frequency       vdb(vin)        vp(vin)\n"
               "0\t1.000000e+03\t0.000000e+00\t0.000000e+00\n"
               "1\t1.122018e+03\t0.000000e+00\t0.000000e+00\n")
        pts = parse_ac(log)
        self.assertEqual(len(pts), 2)
        self.assertAlmostEqual(pts[0][0], 1000.0)
        self.assertAlmostEqual(pts[0][1], 4.859789)
        self.assertAlmostEqual(pts[0][2], -179.9, places=1)
        self.assertAlmostEqual(pts[0][3], 10 ** (4.859789 / 20), places=6)

    def test_parse_tran(self):
        log = ("Index   time            v(vin)          v(vout)\n"
               "0\t0.000000e+00\t1.0000e-02\t-1.0000e-01\n"
               "1\t1.0000e-04\t1.0000e-02\t-1.0000e-01\n")
        pts = parse_tran(log)
        self.assertEqual(len(pts), 2)
        self.assertAlmostEqual(pts[0][0], 0.0)
        self.assertAlmostEqual(pts[1][0], 1e-4)
        self.assertAlmostEqual(pts[1][2], -0.1)

    def test_empty_log(self):
        with self.assertRaises(EmptyOutputError):
            parse_op("")
        with self.assertRaises(EmptyOutputError):
            parse_ac("no tables here")
        with self.assertRaises(EmptyOutputError):
            parse_tran("Index   time            v(vin)          v(vout)\n")


class TestRunAnalysis(unittest.TestCase):
    def setUp(self):
        self.params, errors = validate_sim_input(BASE)
        self.assertEqual(errors, [])

    def test_missing_engine_status(self):
        with tempfile.TemporaryDirectory() as d:
            result = run_analysis(
                self.params, "dc", Path(d),
                str(Path(d) / "does-not-exist.exe"),
            )
        self.assertEqual(result.status, "ENGINE_NOT_FOUND")
        self.assertIsNone(result.values)
        self.assertEqual(result.provenance["model"].startswith("QNPN"), True)

    def test_env_override_can_simulate_engine_not_ready(self):
        with patch.dict("os.environ", {"NGSPICE_ENGINE": "missing-engine.exe"}):
            engine = resolve_engine()
            with tempfile.TemporaryDirectory() as d:
                result = run_analysis(self.params, "dc", Path(d), engine)
        self.assertEqual(engine, "missing-engine.exe")
        self.assertEqual(result.status, "ENGINE_NOT_FOUND")
        self.assertIsNone(result.values)

    def test_engine_version_from_real_engine(self):
        if not REAL_ENGINE.is_file():
            self.skipTest("ngspice not installed")
        self.assertTrue(engine_version(str(REAL_ENGINE)).startswith("ngspice-"))

    def test_real_ngspice_dc(self):
        if not REAL_ENGINE.is_file():
            self.skipTest("ngspice not installed")
        with tempfile.TemporaryDirectory() as d:
            result = run_analysis(self.params, "dc", Path(d), str(REAL_ENGINE))
        self.assertEqual(result.status, "SUCCESS", result.message)
        self.assertAlmostEqual(result.values["vb"], 1.949112, places=3)
        self.assertAlmostEqual(result.values["ic_mA"], 1.277541, places=3)
        self.assertEqual(result.provenance["engine_version"], "ngspice-47")

    def test_real_ngspice_ac_and_tran(self):
        if not REAL_ENGINE.is_file():
            self.skipTest("ngspice not installed")
        for analysis, attr in (("ac", "ac_points"), ("tran", "tran_points")):
            with self.subTest(analysis=analysis), tempfile.TemporaryDirectory() as d:
                result = run_analysis(
                    self.params, analysis, Path(d), str(REAL_ENGINE)
                )
                self.assertEqual(result.status, "SUCCESS", result.message)
                self.assertGreater(len(getattr(result, attr)), 100)


class TestSvg(unittest.TestCase):
    def test_no_data(self):
        self.assertIn("No data", svg_bode(()))
        self.assertIn("No data", svg_waveform(()))

    def test_bode_has_axes_and_units(self):
        points = ((100.0, 3.0, -170.0, 1.41), (1000.0, 6.0, -179.0, 2.0))
        svg = svg_bode(points)
        self.assertIn("<svg", svg)
        self.assertIn("Frequency (Hz)", svg)
        self.assertIn("Gain (dB)", svg)
        self.assertIn("Phase (deg)", svg)
        self.assertIn("<polyline", svg)

    def test_waveform_has_units_and_two_series(self):
        points = ((0.0, 0.01, -0.02), (0.001, 0.01, -0.02))
        svg = svg_waveform(points)
        self.assertIn("<svg", svg)
        self.assertIn("Time (ms)", svg)
        self.assertIn("Voltage (V)", svg)
        self.assertIn("Vin", svg)
        self.assertIn("Vout", svg)
        self.assertEqual(svg.count("<polyline"), 2)


if __name__ == "__main__":
    unittest.main()
