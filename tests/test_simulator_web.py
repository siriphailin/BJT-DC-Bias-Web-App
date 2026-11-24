import unittest
from pathlib import Path
from unittest.mock import patch

from app import app
from spice_engine import SimResult

REAL_ENGINE = (
    Path.home() / "AppData" / "Local" / "Programs" / "ngspice-47"
    / "Spice64" / "bin" / "ngspice_con.exe"
)

VALID = {
    "analysis": "dc", "vcc": "12",
    "r1": "100", "r1_unit": "kohm", "r2": "22", "r2_unit": "kohm",
    "rc": "2.2", "rc_unit": "kohm", "re": "1", "re_unit": "kohm",
    "rl": "10", "rl_unit": "kohm",
    "amplitude": "10", "amplitude_unit": "mv",
    "frequency": "1", "frequency_unit": "khz",
}


def fake_runs(status):
    """Three runs so the page can render both plots and all result tables."""
    ok = status == "SUCCESS"
    values = (
        {"vb": 1.949, "ve": 1.289, "vc": 9.189, "vce": 7.900, "ic_mA": 1.278}
        if ok else None
    )
    ac_points = ((1000.0, 4.8, -179.9, 1.7),) if ok else None
    tran_points = (
        ((0.0, 0.01, -0.02), (0.0005, -0.01, 0.02), (0.001, 0.01, -0.02))
        if ok else None
    )
    provenance = {
        "engine_path": "ngspice_con.exe", "engine_version": "ngspice-47",
        "model": "QNPN teaching model", "analysis_directive": ".op",
        "timestamp": "2026-11-24T00:00:00", "netlist_path": "circuit.cir",
        "log_path": "run.log",
    }
    return {
        key: SimResult(
            analysis=key, status=status,
            message="ok" if ok else "engine missing",
            netlist="* fake netlist for route test",
            log_excerpt="log",
            values=values, ac_points=ac_points, tran_points=tran_points,
            provenance=provenance,
        )
        for key in ("dc", "ac", "tran")
    }


class TestSimulatorPage(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get(self):
        resp = self.client.get("/simulator")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn('name="analysis"', body)
        self.assertIn('action="/simulate"', body)
        self.assertIn("Lab 04", body)
        self.assertIn("Circuit &amp; Parameters", body)
        self.assertIn("CE Amplifier Lab: DC Bias / AC / Transient", body)
        self.assertLess(
            body.index("CE Amplifier Lab: DC Bias / AC / Transient"),
            body.index('id="circuit-parameters"'),
        )
        self.assertIn("Simulation &amp; Plots", body)
        self.assertIn("Engineering Results", body)
        self.assertIn("Engine ngspice", body)
        self.assertIn("Units used in this page", body)
        self.assertLess(body.index('id="engineering-results"'), body.index('id="engine-ngspice"'))
        self.assertNotIn("Engine detected on this machine", body)
        self.assertNotIn("Model assumption", body)
        self.assertIn('class="sim-mono"', body)

    def test_no_client_javascript(self):
        for path in ("/", "/simulator"):
            with self.subTest(path=path):
                body = self.client.get(path).get_data(as_text=True).lower()
                self.assertNotIn("<script", body)
                self.assertNotIn("onclick=", body)
                self.assertNotIn("fetch(", body)

    def test_index_links_to_simulator(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('href="/simulator"', body)

    def test_get_selects_requested_analysis_and_keeps_values(self):
        resp = self.client.get(
            "/simulator?analysis=ac&re=2&re_unit=kohm&rl=4.7&rl_unit=kohm"
            "&amplitude=30&amplitude_unit=mv&frequency=2&frequency_unit=khz"
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn('name="analysis" value="ac"', body)
        self.assertIn("checked", body)
        self.assertNotIn("next_analysis", body)
        self.assertNotIn('formmethod="get"', body)
        self.assertIn('name="rl"', body)
        self.assertIn('value="4.7"', body)
        self.assertIn('name="amplitude"', body)
        self.assertIn('value="30"', body)
        self.assertIn('name="frequency"', body)
        self.assertIn('name="frequency_unit"', body)
        self.assertIn('form="sim-form"', body)
        self.assertIn("BJT voltage-divider common-emitter amplifier schematic", body)

    def test_three_analysis_radio_buttons(self):
        body = self.client.get("/simulator").get_data(as_text=True)
        self.assertEqual(body.count('type="radio" name="analysis"'), 3)
        for value in ("dc", "ac", "tran"):
            self.assertIn(f'name="analysis" value="{value}"', body)

    def test_schematic_has_bjt_circle_and_short_vcc_rail(self):
        body = self.client.get("/simulator").get_data(as_text=True)
        self.assertIn('<circle cx="400" cy="170" r="34" fill="none"/>', body)
        self.assertIn('<line x1="250" y1="40" x2="450" y2="40"/>', body)
        self.assertNotIn('<line x1="70" y1="40" x2="620" y2="40"/>', body)

    def test_schematic_uses_impedance_boxes_and_vin_arrow(self):
        body = self.client.get("/simulator").get_data(as_text=True)
        for rect in (
            '<rect x="238" y="60" width="24" height="80"/>',
            '<rect x="238" y="200" width="24" height="80"/>',
            '<rect x="438" y="60" width="24" height="40"/>',
            '<rect x="438" y="250" width="24" height="32"/>',
            '<rect x="588" y="160" width="24" height="80"/>',
        ):
            self.assertIn(rect, body)
        self.assertNotIn('L240 72 L260 80', body)
        self.assertIn('class="sim-arrow" d="M70 151 L75 159 L65 159 Z"', body)
        schematic = body.split('<div class="sim-schematic">', 1)[1].split('</svg>', 1)[0]
        self.assertNotIn('class="sim-value"', schematic)
        self.assertNotIn('10 µF', schematic)
        self.assertNotIn('kΩ', schematic)

    def test_invalid_returns_400_and_no_result(self):
        resp = self.client.post("/simulate", data=dict(VALID, re="0"))
        self.assertEqual(resp.status_code, 400)
        body = resp.get_data(as_text=True)
        self.assertIn("RE", body)
        self.assertNotIn("ENGINE_NOT_FOUND", body)

    def test_invalid_rl_returns_400(self):
        resp = self.client.post("/simulate", data=dict(VALID, rl="0"))
        self.assertEqual(resp.status_code, 400)
        body = resp.get_data(as_text=True)
        self.assertIn("RL", body)
        self.assertNotIn("SUCCESS", body)

    def test_unknown_analysis_returns_400(self):
        resp = self.client.post("/simulate", data=dict(VALID, analysis="foobar"))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("analysis", resp.get_data(as_text=True).lower())

    @patch("app.run_all_for_request")
    def test_success_renders_three_result_tables(self, run):
        run.return_value = fake_runs("SUCCESS")
        resp = self.client.post("/simulate", data=VALID)
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        run.assert_called_once()
        self.assertIn("ngspice-47", body)
        self.assertIn("SUCCESS", body)
        self.assertIn("1.949", body)
        self.assertIn("DC Operating Point", body)
        self.assertIn("AC Frequency Response", body)
        self.assertIn("Transient Response", body)
        self.assertIn("NOT a SPICE result", body)
        self.assertIn("Netlist &amp; engine log", body)
        self.assertIn("fake netlist for route test", body)
        self.assertIn("<th>IC</th>", body)
        self.assertIn("1.278", body)
        self.assertIn("QNPN teaching model", body)
        self.assertIn(".ac dec 20 1 1Meg", body)
        self.assertIn("not determined in sweep range", body)
        self.assertIn("Run Status", body)
        self.assertIn("Run timestamp", body)
        self.assertIn("Engine ngspice", body)
        self.assertIn("Units used in this page", body)
        self.assertNotIn("Engine detected on this machine", body)
        self.assertNotIn("Model assumption", body)

    @patch("app.run_all_for_request")
    @patch("app.find_low_cutoff", return_value=15.8)
    def test_success_shows_low_cutoff_when_found(self, cutoff, run):
        run.return_value = fake_runs("SUCCESS")
        body = self.client.post("/simulate", data=VALID).get_data(as_text=True)
        self.assertIn("15.8 Hz", body)
        self.assertNotIn("not determined in sweep range", body)
        cutoff.assert_called_once()

    @patch("app.run_all_for_request")
    def test_success_renders_both_illustrative_plots(self, run):
        run.return_value = fake_runs("SUCCESS")
        resp = self.client.post("/simulate", data=dict(VALID, analysis="ac"))
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn("Bode response (illustrative)", body)
        self.assertIn("Input/Output waveforms (illustrative)", body)
        self.assertIn("Frequency (Hz)", body)
        self.assertIn("Gain (dB)", body)
        self.assertIn("Phase (deg)", body)
        self.assertIn("Time (ms)", body)
        self.assertIn("Voltage (V)", body)
        self.assertIn("<polyline", body)
        self.assertNotIn("<script", body)

    @patch("app.run_all_for_request")
    def test_engine_fail_clears_old_result(self, run):
        run.return_value = fake_runs("ENGINE_NOT_FOUND")
        resp = self.client.post("/simulate", data=VALID)
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("ENGINE_NOT_FOUND", body)
        self.assertIn("What to try", body)
        self.assertNotIn("SUCCESS", body)
        self.assertNotIn("1.949", body)
        self.assertNotIn("4.8", body)
        self.assertIn("NOT a SPICE result", body)

    @unittest.skipUnless(REAL_ENGINE.is_file(), "ngspice not installed")
    def test_real_end_to_end(self):
        resp = self.client.post("/simulate", data=VALID)
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn("SUCCESS", body)
        self.assertIn("1.949", body)
        self.assertIn("ngspice-47", body)
        self.assertIn("Bode response (illustrative)", body)
        self.assertIn("Input/Output waveforms (illustrative)", body)
        self.assertIn("DC Operating Point", body)


if __name__ == "__main__":
    unittest.main()
