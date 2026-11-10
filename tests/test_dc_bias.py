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
