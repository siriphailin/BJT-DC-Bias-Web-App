# Test Log — Lab 04 (BJT CE Amplifier Simulator)

บันทึกผลการรันชุดทดสอบอัตโนมัติของโปรเจกต์กับโค้ดสุดท้าย

| รายการ | ค่า |
|---|---|
| วันที่รัน | 2026-11-24 18:18:07 +07:00 (SE Asia Standard Time) |
| โค้ดที่ทดสอบ | `e34fcaaedad1d35c4c8e24a0af29155c2121e267` (`lab04`) |
| คำสั่ง | `python -m unittest discover -s tests -v` |
| Python | 3.14.2 |
| Flask | 3.1.3 |
| ngspice | ngspice-47 (`%LOCALAPPDATA%\Programs\ngspice-47\Spice64\bin\ngspice_con.exe`) |
| ผลรวม | `Ran 64 tests in 0.492s` / `OK` / exit code 0 |
| ข้อความ skip | **ไม่มี** — รวม test ที่เรียก ngspice จริงผ่าน `run_analysis()` และ `POST /simulate` end-to-end |

แยกตามไฟล์: `test_dc_bias.py` 14, `test_web.py` 7, `test_spice_engine.py` 28,
`test_simulator_web.py` 15 (รวม 64)

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
test_engine_fail_clears_old_result (test_simulator_web.TestSimulatorPage.test_engine_fail_clears_old_result) ... ok
test_get (test_simulator_web.TestSimulatorPage.test_get) ... ok
test_get_selects_requested_analysis_and_keeps_values (test_simulator_web.TestSimulatorPage.test_get_selects_requested_analysis_and_keeps_values) ... ok
test_index_links_to_simulator (test_simulator_web.TestSimulatorPage.test_index_links_to_simulator) ... ok
test_invalid_returns_400_and_no_result (test_simulator_web.TestSimulatorPage.test_invalid_returns_400_and_no_result) ... ok
test_invalid_rl_returns_400 (test_simulator_web.TestSimulatorPage.test_invalid_rl_returns_400) ... ok
test_no_client_javascript (test_simulator_web.TestSimulatorPage.test_no_client_javascript) ... ok
test_real_end_to_end (test_simulator_web.TestSimulatorPage.test_real_end_to_end) ... ok
test_schematic_has_bjt_circle_and_short_vcc_rail (test_simulator_web.TestSimulatorPage.test_schematic_has_bjt_circle_and_short_vcc_rail) ... ok
test_schematic_uses_impedance_boxes_and_vin_arrow (test_simulator_web.TestSimulatorPage.test_schematic_uses_impedance_boxes_and_vin_arrow) ... ok
test_success_renders_both_illustrative_plots (test_simulator_web.TestSimulatorPage.test_success_renders_both_illustrative_plots) ... ok
test_success_renders_three_result_tables (test_simulator_web.TestSimulatorPage.test_success_renders_three_result_tables) ... ok
test_success_shows_low_cutoff_when_found (test_simulator_web.TestSimulatorPage.test_success_shows_low_cutoff_when_found) ... ok
test_three_analysis_radio_buttons (test_simulator_web.TestSimulatorPage.test_three_analysis_radio_buttons) ... ok
test_unknown_analysis_returns_400 (test_simulator_web.TestSimulatorPage.test_unknown_analysis_returns_400) ... ok
test_ac_directives (test_spice_engine.TestNetlist.test_ac_directives) ... ok
test_custom_rl_in_netlist (test_spice_engine.TestNetlist.test_custom_rl_in_netlist) ... ok
test_dc_directives (test_spice_engine.TestNetlist.test_dc_directives) ... ok
test_fmt_is_finite (test_spice_engine.TestNetlist.test_fmt_is_finite) ... ok
test_tran_directives (test_spice_engine.TestNetlist.test_tran_directives) ... ok
test_unknown_analysis (test_spice_engine.TestNetlist.test_unknown_analysis) ... ok
test_values_are_formatted_not_raw (test_spice_engine.TestNetlist.test_values_are_formatted_not_raw) ... ok
test_empty_log (test_spice_engine.TestParsers.test_empty_log) ... ok
test_parse_ac_radians_to_degrees (test_spice_engine.TestParsers.test_parse_ac_radians_to_degrees) ... ok
test_parse_op_real_table_format (test_spice_engine.TestParsers.test_parse_op_real_table_format) ... ok
test_parse_tran (test_spice_engine.TestParsers.test_parse_tran) ... ok
test_engine_version_from_real_engine (test_spice_engine.TestRunAnalysis.test_engine_version_from_real_engine) ... ok
test_env_override_can_simulate_engine_not_ready (test_spice_engine.TestRunAnalysis.test_env_override_can_simulate_engine_not_ready) ... ok
test_missing_engine_status (test_spice_engine.TestRunAnalysis.test_missing_engine_status) ... ok
test_real_ngspice_ac_and_tran (test_spice_engine.TestRunAnalysis.test_real_ngspice_ac_and_tran) ... ok
test_real_ngspice_dc (test_spice_engine.TestRunAnalysis.test_real_ngspice_dc) ... ok
test_bode_has_axes_and_units (test_spice_engine.TestSvg.test_bode_has_axes_and_units) ... ok
test_no_data (test_spice_engine.TestSvg.test_no_data) ... ok
test_waveform_has_units_and_two_series (test_spice_engine.TestSvg.test_waveform_has_units_and_two_series) ... ok
test_bad_unit_rejected (test_spice_engine.TestValidate.test_bad_unit_rejected) ... ok
test_injection_rejected (test_spice_engine.TestValidate.test_injection_rejected) ... ok
test_legacy_source_fields_still_work (test_spice_engine.TestValidate.test_legacy_source_fields_still_work) ... ok
test_missing_field_rejected (test_spice_engine.TestValidate.test_missing_field_rejected) ... ok
test_out_of_range (test_spice_engine.TestValidate.test_out_of_range) ... ok
test_selectable_source_units (test_spice_engine.TestValidate.test_selectable_source_units) ... ok
test_valid (test_spice_engine.TestValidate.test_valid) ... ok
test_zero_re_rejected (test_spice_engine.TestValidate.test_zero_re_rejected) ... ok
test_zero_rl_rejected (test_spice_engine.TestValidate.test_zero_rl_rejected) ... ok
test_cutoff_shows_warning_and_200 (test_web.TestCalculate.test_cutoff_shows_warning_and_200) ... ok
test_diagram_renders_computed_vce (test_web.TestCalculate.test_diagram_renders_computed_vce) ... ok
test_non_numeric_returns_400 (test_web.TestCalculate.test_non_numeric_returns_400) ... ok
test_valid_input_computes_in_backend (test_web.TestCalculate.test_valid_input_computes_in_backend) ... ok
test_zero_resistance_returns_400_with_field_name (test_web.TestCalculate.test_zero_resistance_returns_400_with_field_name) ... ok
test_get_index_returns_200_and_form (test_web.TestIndex.test_get_index_returns_200_and_form) ... ok
test_lab_switch_above_first_block (test_web.TestIndex.test_lab_switch_above_first_block) ... ok

----------------------------------------------------------------------
Ran 64 tests in 0.492s

OK
```

## ภาพหน้าจอประกอบ (รอบสุดท้าย)

| ไฟล์ | เนื้อหา |
|---|---|
| `docs/screenshots/lab04-final-desktop-1280x900.png` | `/simulator` หลังรัน ngspice จริง: ปุ่มสลับ Lab 03/04, schematic, 2 กราฟ, ตารางผล DC/AC/Transient + analytical, บล็อก `Engine ngspice` ด้านล่างสุด |
| `docs/screenshots/lab04-final-phone-390x844.png` | หน้าเดียวกันที่ viewport 390×844 (ภาพ full page 406×5513): layout collapse บนจอแคบ |

รายละเอียดการตรวจ browser B1–B8 และ `impeccable detect` อยู่ใน
[`docs/validation.md`](validation.md) หัวข้อ 9.8

## วิธีรันซ้ำ

```bash
python -m unittest discover -s tests -v
```

ผลที่ต้องได้: `Ran 64 tests` … `OK` (ไม่มี `skipped` ถ้าติดตั้ง ngspice ตาม README)
