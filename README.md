# BJT DC Bias Web App — Common Emitter, Voltage Divider

เครื่องคำนวณ **DC Bias** ของทรานซิสเตอร์ BJT แบบ Common Emitter ที่ใช้วงจรแบ่งแรงดัน
(voltage divider) ป้อนที่ขา Base — งาน Lab 02 รายวิชา ENG29 2121 Electronics Laboratory

กรอกค่า `VCC, R1, R2, RC, RE, β, VBE` แล้วกด **Calculate DC Bias (คำนวณ DC Bias)**
หน้าเว็บจะคำนวณ `VB, VE, VC, VCE, IC, IB, IE` **ด้วย Python ฝั่ง server** แล้วส่ง HTML
ที่คำนวณเสร็จแล้วกลับมาให้ Browser — ไม่มี JavaScript ฝั่ง client และไม่มีค่าที่ฮาร์ดโค้ดไว้ในหน้าเว็บ

หน้าเว็บแสดงเพิ่มเติม:

- แผนภาพวงจร (SVG) ที่เติมค่าอุปกรณ์และแรงดันที่ node ต่าง ๆ ตามผลคำนวณจริง
- สถานะการทำงานของทรานซิสเตอร์: **Forward Active / Cutoff / Saturation**
- ข้อความยืนยัน **Active Region Approximation OK** เมื่อทรานซิสเตอร์อยู่ในช่วงขยาย
- คำเตือนเมื่อแบบจำลอง Forward-Active ใช้ไม่ได้

> ⚠️ **ข้อจำกัดของแบบจำลอง:** นี่คือ **Forward-Active approximation** (β คงที่, VBE คงที่,
> ไม่คิด Early effect) **ไม่ใช่ผลจาก SPICE** และไม่ใช่ผลจากการวัดจริง
> เมื่อทรานซิสเตอร์อยู่นอกช่วงขยาย ค่าที่แสดงเป็นเพียงการประมาณเพื่อการสอน — อย่าใช้ตัดสินใจทางวิศวกรรม

---

## ความต้องการของระบบ (Requirements)

| รายการ | เวอร์ชัน |
|---|---|
| Python | 3.14 (พัฒนาและทดสอบบน 3.14.2) |
| Flask | 3.x (ดู `requirements.txt`) |

ไม่มีการใช้ dependency อื่นนอกเหนือจาก Flask และไม่มีการใช้ JavaScript ฝั่ง client เลย

---

## การติดตั้ง (Installation)

```bash
# 1) สร้าง virtual environment
python -m venv .venv

# 2) เปิดใช้งาน (activate)
#    Windows — PowerShell
.venv\Scripts\Activate.ps1
#    Windows — cmd
.venv\Scripts\activate.bat
#    macOS / Linux
source .venv/bin/activate

# 3) ติดตั้ง dependency
pip install -r requirements.txt
```

ถ้า PowerShell ไม่ยอมให้รัน `Activate.ps1` ให้สั่งครั้งเดียว:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

หรือจะไม่ activate ก็ได้ แล้วเรียก interpreter ตรง ๆ ด้วย path ของ `.venv`

---

## การรัน (Run)

```bash
python -m flask --app app run --debug
```

แล้วเปิด Browser ไปที่ **<http://127.0.0.1:5000/>**

ถ้าไม่ได้ activate venv ให้ใช้:

```powershell
.venv\Scripts\python.exe -m flask --app app run --debug
```

---

## การทดสอบ (Tests)

```bash
python -m unittest discover -s tests -v
```

ผลที่ต้องได้: **`Ran 20 tests` … `OK`**

ชุดทดสอบแบ่งเป็นสองชั้น

| ไฟล์ | จำนวน | ตรวจอะไร |
|---|---|---|
| `tests/test_dc_bias.py` | 14 | สมการ, การแปลงหน่วย, การปฏิเสธค่าผิด, การแบ่ง Region และ warning |
| `tests/test_web.py` | 6 | Flask route: `GET /` 200, `POST /calculate` 200/400, ค่าที่คำนวณขึ้นหน้าเว็บ |

---

## ชุดค่าตัวอย่างจากใบงาน (Reference Case)

| พารามิเตอร์ | ค่า |
|---|---|
| VCC | 12 V |
| R1 | 100 kΩ |
| R2 | 22 kΩ |
| RC | 2.2 kΩ |
| RE | 1 kΩ |
| β | 100 |
| VBE | 0.70 V |

ผลที่หน้าเว็บแสดง (3 ตำแหน่งทศนิยม)

| ปริมาณ | ค่า |
|---|---|
| VB | 1.942 V |
| VE | 1.242 V |
| VC | 9.294 V |
| VCE | 8.052 V |
| IC | 1.230 mA |
| IB | 12.299 µA |
| IE | 1.242 mA |

ค่าที่คำนวณเต็มความละเอียดและวิธีคำนวณมือทีละขั้นอยู่ใน [`docs/validation.md`](docs/validation.md)

---

## โครงสร้างไฟล์

```
BJT DC Bias Web App/
├── app.py               # Flask routes: GET / , POST /calculate
├── dc_bias.py           # สมการ DC Bias ทั้งหมด (ไม่ import Flask)
├── templates/index.html # ฟอร์ม + แผนภาพ SVG + ตารางผลลัพธ์ (Jinja)
├── static/style.css     # layout, badge, warning
├── tests/               # unittest 20 ตัว
├── docs/                # design-note, validation, reflection, test-log, screenshots
├── requirements.txt
└── AGENTS.md            # conventions สำหรับ AI coding agent
```

**หลักการสำคัญ:** `app.py` ไม่มีสมการแม้บรรทัดเดียว — มันอ่านค่าจากฟอร์ม แปลงหน่วย
แล้วเรียก `calculate_dc_bias()` ใน `dc_bias.py` สมการทั้งหมดจึงอยู่ที่เดียวและมี test ครอบคลุม
ถ้าต้องแก้สมการ ให้แก้ที่ `dc_bias.py` ที่เดียว ไม่ต้องแตะ HTML

---

## เอกสารประกอบ

| ไฟล์ | เนื้อหา |
|---|---|
| [`docs/design-note.md`](docs/design-note.md) | เหตุผลการออกแบบ: ทำไม Flask, ทำไมแยก `dc_bias.py`, data flow |
| [`docs/validation.md`](docs/validation.md) | สมมติฐาน, สมการ, ค่าอ้างอิง, วิธีคำนวณมือ, กรณีที่แบบจำลองใช้ไม่ได้ |
| [`docs/reflection.md`](docs/reflection.md) | คำถามสะท้อนความคิด 4 ข้อ (นักศึกษาเขียนคำตอบเอง) |
| [`docs/test-log.md`](docs/test-log.md) | บันทึกผลการรัน test |
| [`docs/screenshots/`](docs/screenshots/) | ภาพหน้าจอผลคำนวณสำเร็จ และกรณีกรอกค่าผิด |
| [`docs/superpowers/`](docs/superpowers/) | Design doc และ implementation plan ที่ใช้ขับเคลื่อนงานนี้ |
