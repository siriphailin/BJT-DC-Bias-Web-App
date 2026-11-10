# AGENTS.md — conventions สำหรับ AI coding agent

ไฟล์นี้อธิบายกติกาของโปรเจกต์นี้ ให้ agent (OpenCode / Superpowers หรืออื่น ๆ) อ่านก่อนแก้โค้ด
เป้าหมาย: รักษาความถูกต้องของสมการ และรักษาสถาปัตยกรรมที่แยก logic ออกจาก presentation

## 1. ขอบเขตของโปรเจกต์

งานนี้เป็น **DC Bias ของ BJT แบบ Common Emitter + voltage divider เท่านั้น**

- ✅ ทำได้: คำนวณ DC bias, validation, warning, แผนภาพวงจร, test, เอกสาร
- ❌ ห้ามเพิ่ม: AC analysis, small-signal, gain, Bode plot, transient, SPICE/ngspice,
  signal generator, load line, bias แบบอื่น (fixed bias, emitter bias), FET

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

## 3. เครื่องมือและคำสั่ง

| งาน | คำสั่ง |
|---|---|
| ติดตั้ง | `python -m venv .venv` แล้ว `pip install -r requirements.txt` |
| รัน | `python -m flask --app app run --debug` |
| ทดสอบ | `python -m unittest discover -s tests -v` |

- ใช้ **`unittest`** เท่านั้น (ไม่ใช้ pytest) เพราะเป็นสิ่งที่หลักสูตรกำหนด
- Python 3.14, Flask 3.x — **ห้ามเพิ่ม dependency ใหม่** โดยไม่ถามมนุษย์ก่อน

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
  `Add README, validation notes and reflection for Lab 02`

## 6. ลำดับการทำงาน

1. อ่าน `docs/design-note.md` และ design doc ใน `docs/superpowers/specs/` ก่อนแก้โค้ด
2. แก้สมการ → เขียน failing test ก่อน → แก้ให้ผ่าน → รัน suite ทั้งหมด
3. ถ้าแตะ UI ต้องเปิด Browser ตรวจด้วยตาจริง ไม่ใช่ดูแค่ HTML
4. อัปเดต `docs/validation.md` ถ้าค่าอ้างอิงหรือสมการเปลี่ยน
