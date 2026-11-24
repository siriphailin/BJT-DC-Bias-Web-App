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

    def test_lab_switch_above_first_block(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('class="lab-switch"', body)
        self.assertIn('href="/simulator"', body)
        self.assertIn('aria-current="page"', body)
        self.assertIn("Lab 04 · CE Amplifier Simulator", body)
        self.assertLess(body.index('class="lab-switch"'), body.index("<section"))


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
