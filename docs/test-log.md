# Test Log — Lab 02 (BJT DC Bias Web App)

บันทึกผลการรันชุดทดสอบอัตโนมัติของโปรเจกต์

| รายการ | ค่า |
|---|---|
| วันที่รัน | 2026-11-10 18:28:31 SE Asia Standard Time |
| คำสั่ง | `python -m unittest discover -s tests -v` |
| Python | 3.14.2 |
| ผลรวม | Ran 20 tests in 0.046s / OK |

## ผลลัพธ์ทั้งหมด

```text
test_beta_increases_ic_monotonically (test_dc_bias.TestReferenceCase.test_beta_increases_ic_monotonically) ... ok
test_reference_values (test_dc_bias.TestReferenceCase.test_reference_values) ... ok
test_cutoff (test_dc_bias.TestRegions.test_cutoff) ... ok
test_extreme_beta_is_finite (test_dc_bias.TestRegions.test_extreme_beta_is_finite) ... ok
test_saturation (test_dc_bias.TestRegions.test_saturation) ... ok
test_parse_kohm (test_dc_bias.TestUnits.test_parse_kohm) ... ok
test_parse_ohm (test_dc_bias.TestUnits.test_parse_ohm) ... ok
test_reject_text (test_dc_bias.TestUnits.test_reject_text) ... ok
test_reject_unknown_unit (test_dc_bias.TestUnits.test_reject_unknown_unit) ... ok
test_unit_equivalence (test_dc_bias.TestUnits.test_unit_equivalence) ... ok
test_non_positive_beta_rejected (test_dc_bias.TestValidation.test_non_positive_beta_rejected) ... ok
test_vbe_out_of_range_rejected (test_dc_bias.TestValidation.test_vbe_out_of_range_rejected) ... ok
test_zero_re_rejected (test_dc_bias.TestValidation.test_zero_re_rejected) ... ok
test_zero_resistance_rejected (test_dc_bias.TestValidation.test_zero_resistance_rejected) ... ok
test_cutoff_shows_warning_and_200 (test_web.TestCalculate.test_cutoff_shows_warning_and_200) ... ok
test_diagram_renders_computed_vce (test_web.TestCalculate.test_diagram_renders_computed_vce) ... ok
test_non_numeric_returns_400 (test_web.TestCalculate.test_non_numeric_returns_400) ... ok
test_valid_input_computes_in_backend (test_web.TestCalculate.test_valid_input_computes_in_backend) ... ok
test_zero_resistance_returns_400_with_field_name (test_web.TestCalculate.test_zero_resistance_returns_400_with_field_name) ... ok
test_get_index_returns_200_and_form (test_web.TestIndex.test_get_index_returns_200_and_form) ... ok

----------------------------------------------------------------------
Ran 20 tests in 0.046s

OK
```

## ภาพหน้าจอประกอบ

| ไฟล์ | เนื้อหา |
|---|---|
| `docs/screenshots/calculate-success.png` | กรอกชุดค่าตัวอย่างจากใบงาน แล้วกด Calculate — เห็นผล DC Bias ครบ (VCE = 8.052 V, IC = 1.230 mA) พร้อมสถานะ Active Region Approximation OK |
| `docs/screenshots/validation-error.png` | กรอก `R1 = 0` — ระบบปฏิเสธด้วย HTTP 400 แสดงข้อความสองภาษาและคงค่าที่กรอกไว้ |

## วิธีรันซ้ำ

```bash
python -m unittest discover -s tests -v
```

ผลที่ต้องได้: `Ran 20 tests` … `OK`
