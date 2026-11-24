# AGENTS.md — conventions สำหรับ AI coding agent

ไฟล์นี้อธิบายกติกาของโปรเจกต์นี้ ให้ agent (OpenCode / Superpowers หรืออื่น ๆ) อ่านก่อนแก้โค้ด
เป้าหมาย: รักษาความถูกต้องของสมการ และรักษาสถาปัตยกรรมที่แยก logic ออกจาก presentation

## 1. ขอบเขตของโปรเจกต์

งานนี้คือ **Flask Web App เดิมของ Lab 03 + Lab 04 Amplifier Simulator v1** (ENG29 2121)

**Lab 03 — DC Bias 3 โหมด (ห้ามลบ ห้ามแก้สมการ)**

| โหมด | ตัวต้านทานที่ใช้ | ฟังก์ชันใน `dc_bias.py` |
|---|---|---|
| Fixed Bias | RB, RC | `calculate_fixed_bias()` |
| Emitter Bias (แหล่งจ่ายเดียว) | RB, RC, RE | `calculate_emitter_bias()` |
| Voltage Divider Bias | R1, R2, RC, RE | `calculate_dc_bias()` |

**Lab 04 — SPICE เฉพาะ CE Voltage Divider อ้างอิง 1 วงจร ผ่าน `spice_engine.py`**

- ✅ ทำได้: DC bias 3 โหมดเดิม, validation/warning/test เดิม, และ `.op/.ac/.tran`
  ของวงจรขยาย CE อ้างอิงด้วย ngspice จริง + กราฟ SVG ที่ render จากข้อมูลจริง
- ❌ ห้ามเพิ่ม: circuit editor, SPICE ของ Fixed/Emitter Bias, emitter bypass capacitor,
  Animated overlay, FET, การเขียน SPICE solver เอง, deploy ภายนอก
- ❌ ห้ามใช้ผล analytical แทนผล SPICE หรือเรียกผล mock ว่า "success"

ถ้าโจทย์ใหม่จะพาออกนอกขอบเขตนี้ ให้ถามมนุษย์ก่อนเสมอ

## 2. กติกาที่ห้ามละเมิด

1. **`dc_bias.py` ห้าม `import flask`** และห้ามอ้างถึง HTML, HTTP, request, template
   ไฟล์นี้ต้องเป็นฟังก์ชันบริสุทธิ์ (pure function) ที่ import ไปใช้ที่อื่นได้
2. **`app.py` ห้ามมีสมการ** — ทำได้แค่อ่านค่าจากฟอร์ม, แปลงหน่วยด้วย `parse_resistance`,
   เรียก `calculate_dc_bias`, แล้ว render ถ้าต้องคำนวณอะไรเพิ่ม ให้ย้ายไป `dc_bias.py`
3. **ห้ามฮาร์ดโค้ดผลลัพธ์ใน template** — ทุกตัวเลขที่แสดงต้องมาจาก `result.*` หรือ `form.*`
   ผ่าน Jinja เท่านั้น
4. **ห้ามใช้ JavaScript ฝั่ง client** — ไม่มี `<script>`, ไม่มี `onclick=`, ไม่มี `fetch`
   ผลลัพธ์ทุกตัวต้องคำนวณเสร็จที่ Python ก่อนส่ง HTML กลับ
5. **ทุกสมการต้องมี test** — เพิ่ม/แก้สมการเมื่อไร ต้องมี test ใน `tests/test_dc_bias.py`
   ที่พิสูจน์ค่าตัวเลขจริง ไม่ใช่แค่ assert ว่าไม่ error
   **ยกเว้นงาน Lab 03:** ใบงานกำหนดให้เก็บชุดทดสอบเดิมและตรวจผลผ่าน Browser (A1–A5)
   จึงไม่เพิ่ม `unittest` ใหม่ในรอบนี้ — งานหลังจากนี้ให้กลับมาทำตามกฎนี้ตามปกติ
6. **เพิ่มโหมดใหม่ได้ที่ `MODES` ใน `app.py` เท่านั้น** — ต้องประกาศรายการตัวต้านทานที่โหมดนั้น
   ใช้จริง แล้วให้ route เลือกฟังก์ชันใน `dc_bias.py` — ห้ามเขียนสมการใน `app.py` หรือ template
7. **`spice_engine.py` ห้าม `import flask`** — รับเฉพาะค่าที่ validate แล้ว, เป็น adapter
   บริสุทธิ์ที่คืน `SimResult` ให้ `app.py` เป็นคน render
8. **ห้าม `shell=True` / ห้ามต่อข้อความจากฟอร์มเข้า netlist โดยตรง** — ทุกค่าต้องผ่าน
   `_fmt()` และ command ต้องเป็น list; engine ต้องเป็น `ngspice_con.exe` (ไม่ใช่ GUI `ngspice.exe`)
9. **ห้ามฮาร์ดโค้ดผล ngspice/กราฟใน template** — ต้องมาจาก `SimResult` เสมอ;
   ทุก error ต้องล้างผลเก่าออก (`result=None`) และห้ามโชว์ "SUCCESS" ปลอม
10. **ผล SPICE กับผล `dc_bias.py` ต้องมีป้ายแยกกันเสมอ** — ผล analytical
   ต้องระบุว่า `NOT a SPICE result` พร้อมสมมติฐาน (β/VBE คงที่, ไม่มี Early effect)

## 3. เครื่องมือและคำสั่ง

| งาน | คำสั่ง |
|---|---|
| ติดตั้ง | `"C:\Program Files\Python314\python.exe" -m pip install -r requirements.txt` |
| รัน | `"C:\Program Files\Python314\python.exe" -m flask --app app run --debug` |
| ทดสอบ | `"C:\Program Files\Python314\python.exe" -m unittest discover -s tests -v` |
| SPICE engine | `%LOCALAPPDATA%\Programs\ngspice-47\Spice64\bin\ngspice_con.exe` (ngspice-47) |

- ใช้ **`unittest`** เท่านั้น (ไม่ใช้ pytest) เพราะเป็นสิ่งที่หลักสูตรกำหนด
- Python 3.14, Flask 3.x — **ห้ามเพิ่ม dependency ใหม่** โดยไม่ถามมนุษย์ก่อน
- `python` บน PATH เป็น Microsoft Store alias (ใช้ไม่ได้) → ใช้ path เต็มด้านบนเสมอ
- ngspice ต้องเรียกแบบ console (`ngspice_con.exe`); ตัว `ngspice.exe` เป็น GUI ไม่คืน output

## 4. สไตล์โค้ด

- ตัวแปรและฟังก์ชันภาษาอังกฤษ (`calculate_dc_bias`, `parse_resistance`, `BiasResult`)
- ข้อความที่ผู้ใช้เห็น (error, warning, label) เป็น **สองภาษา: อังกฤษนำ ไทยในวงเล็บ**
  เช่น `R1 must be greater than 0 (R1 ต้องมากกว่า 0)` — ข้อความ error/warning มาจาก `dc_bias.py`
  ที่เดียว ไม่กระจายไปใน template
- ตัวเลขที่แสดง: แรงดัน 3 ตำแหน่งทศนิยม + `V`, กระแส `mA` 3 ตำแหน่ง, `IB` แสดง `µA`
- ค่าคงที่ทางวิศวกรรม (`VCE_SAT`, `VBE_MIN`, `VBE_MAX`) ประกาศที่ `dc_bias.py` ที่เดียว

## 5. กติกา Git

- **commit ทำผ่าน GitHub Desktop โดยมนุษย์กดเอง** — agent ห้ามรัน `git commit` หรือ `git push`
- agent stage ไฟล์ได้ (`git add`) แต่ต้องหยุดและรายงานให้มนุษย์ commit
- ห้าม commit `.venv/`, `__pycache__/`, `.env`
- ข้อความ commit ใช้ภาษาอังกฤษ รูปแบบ imperative เช่น
  `Add README and validation notes for Lab 02`

## 6. ลำดับการทำงาน

1. อ่าน `docs/design-note.md` และ design doc ใน `docs/superpowers/specs/` ก่อนแก้โค้ด
2. แก้สมการ → เขียน failing test ก่อน → แก้ให้ผ่าน → รัน suite ทั้งหมด
3. ถ้าแตะ UI ต้องเปิด Browser ตรวจด้วยตาจริง ไม่ใช่ดูแค่ HTML
4. อัปเดต `docs/validation.md` ถ้าค่าอ้างอิงหรือสมการเปลี่ยน
