# BJT DC Bias Web App — Fixed, Emitter and Voltage Divider

เครื่องคำนวณ **DC Bias** ของทรานซิสเตอร์ BJT แบบ Common Emitter **สามวงจรไบอัส**
ป้อนที่ขา Base — งาน Lab 03 รายวิชา ENG29 2121 Electronics Laboratory
(ต่อยอดจาก Lab 02 ที่มีเฉพาะวงจรแบ่งแรงดัน)

| โหมด | อินพุตตัวต้านทาน | สมการกระแส Base |
|---|---|---|
| **Fixed Bias** | RB, RC | `IB = (VCC − VBE) / RB` |
| **Emitter Bias** (แหล่งจ่ายเดียว) | RB, RC, RE | `IB = (VCC − VBE) / [RB + (β+1)·RE]` |
| **Voltage Divider Bias** | R1, R2, RC, RE | `IB = (VTH − VBE) / [RTH + (β+1)·RE]` |

กดปุ่มโหมด (Fixed Bias / Emitter Bias / Voltage Divider Bias) ครั้งเดียว — แผนภาพและฟอร์ม
จะเปลี่ยนตามทันที ฟอร์มแสดงครบทุกช่องแต่ช่องที่โหมดนั้นไม่ใช้จะจางและกดไม่ได้
กรอกค่าแล้วกด **Calculate DC Bias (คำนวณ DC Bias)** หน้าเว็บจะคำนวณ
`VB, VE, VC, VCE, IC, IB, IE` **ด้วย Python ฝั่ง server** แล้วส่ง HTML
ที่คำนวณเสร็จแล้วกลับมาให้ Browser — ไม่มี JavaScript ฝั่ง client และไม่มีค่าที่ฮาร์ดโค้ดไว้ในหน้าเว็บ

หน้าเว็บแสดงเพิ่มเติม:

- แผนภาพวงจร (SVG) ที่เปลี่ยนตามโหมด และเติมค่าอุปกรณ์กับแรงดันที่ node ตามผลคำนวณจริง
- สถานะการทำงานของทรานซิสเตอร์: **Forward Active / Cutoff / Saturation**
- ข้อความยืนยัน **Active Region Approximation OK** เมื่อทรานซิสเตอร์อยู่ในช่วงขยาย
- คำเตือนเมื่อแบบจำลอง Forward-Active ใช้ไม่ได้
- ข้อความ error ที่ระบุชื่อช่องเมื่ออินพุตผิด (เช่น `RB = 0`) และไม่ค้างผลลัพธ์รอบก่อนไว้
- เลือกหน่วยความต้านทานได้ 3 หน่วย: `Ω`, `kΩ`, `MΩ` (1 MΩ = 1,000 kΩ) — ค่าที่เลือกจะแสดงบนแผนภาพ SVG ด้วย

> ⚠️ **ข้อจำกัดของแบบจำลอง:** นี่คือ **Forward-Active approximation** (β คงที่, VBE คงที่,
> ไม่คิด Early effect) **ไม่ใช่ผลจาก SPICE** และไม่ใช่ผลจากการวัดจริง
> เมื่อทรานซิสเตอร์อยู่นอกช่วงขยาย ค่าที่แสดงเป็นเพียงการประมาณเพื่อการสอน — อย่าใช้ตัดสินใจทางวิศวกรรม

---

## ลิงก์ส่งงาน (Lab 03)

| รายการ | ค่า |
|---|---|
| GitHub repository | <https://github.com/siriphailin/BJT-DC-Bias-Web-App> |
| Commit SHA ของ Lab 03 | `442c05cd329660c48b4ca142e22bedc554d99e99` |
| วิธีตรวจผลจริง | **OpenCode Browser** |

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

## ผลตรวจบน Browser — A1–A5 (Lab 03)

ตรวจด้วย **OpenCode Browser** เปิด `http://127.0.0.1:5000/` จริง: กดปุ่มโหมด กรอกฟอร์ม
กด Calculate แล้วอ่านค่าจากหน้าเว็บ (ไม่ได้อ่านจากโค้ด)
เกณฑ์: `|ΔIC| ≤ 0.01 mA` และ `|ΔVCE| ≤ 0.02 V` เทียบกับค่าอ้างอิงที่ยังไม่ปัด
ค่าคงที่ร่วม: `VCC = 12 V`, `RC = 2.2 kΩ`, `β = 100`, `VBE = 0.70 V`

| กรณี | โหมด | อินพุต | ค่าคาดหมาย (คำนวณมือ) | ผลจริง | หน่วย | วิธีตรวจ | สถานะ |
|---|---|---|---|---|---|---|---|
| A1 | Divider | R1=100 kΩ, R2=22 kΩ, RE=1 kΩ | IC 1.2299 · VCE 8.0522 | IC **1.230** · VCE **8.052** | mA · V | OpenCode Browser | **PASS** |
| A2 | Fixed | RB=1 MΩ | IC 1.1300 · VCE 9.5140 | IC **1.130** · VCE **9.514** | mA · V | OpenCode Browser | **PASS** |
| A3 | Emitter | RB=1 MΩ, RE=1 kΩ | IC 1.02634 · VCE 8.70545 | IC **1.026** · VCE **8.705** | mA · V | OpenCode Browser | **PASS** |
| A4 | Emitter | RB=1 MΩ, RE=2 kΩ (เปลี่ยนค่าเดียว) | IC **ลดลง** → 0.94010 · VCE 8.03278 | IC **0.940** · VCE **8.033** | mA · V | OpenCode Browser | **PASS** |
| A5 | Fixed | RB=0 | ต้องแจ้งให้แก้ RB และไม่ค้างผลเดิม | `RB: Resistance must be greater than 0 Ω` | — | OpenCode Browser | **PASS** |

สมการ ค่าอ้างอิง ชุดค่าตัวอย่างจากใบงาน คำตอบ A5 และเส้นทางข้อมูล RE อยู่ใน
[`docs/validation.md`](docs/validation.md) (หัวข้อ 8)
ภาพหน้าจอ 4 ไฟล์: [`docs/screenshots/`](docs/screenshots/) — `lab03-A1-baseline.jpeg`,
`lab03-A2-fixed.jpeg`, `lab03-A3-emitter.jpeg`, `lab03-A5-invalid-input.jpeg`

## โครงสร้างไฟล์

```
BJT DC Bias Web App/
├── app.py               # Flask routes: GET / (เลือกโหมด), POST /calculate (เลือกฟังก์ชันตามโหมด)
├── dc_bias.py           # สมการ DC Bias ทั้งสามโหมด (ไม่ import Flask)
├── templates/index.html # ปุ่มเลือกโหมด 3 ปุ่ม + ฟอร์มครบทุกช่อง + แผนภาพ SVG + ผลลัพธ์ (Jinja)
├── static/style.css     # layout, badge, warning
├── tests/               # unittest 20 ตัว (ชุดเดิมของ Lab 02 — ตามใบงาน Lab 03 ไม่เพิ่ม test ใหม่)
├── docs/                # design-note, validation, test-log, screenshots
├── requirements.txt
└── AGENTS.md            # conventions สำหรับ AI coding agent
```

**หลักการสำคัญ:** `app.py` ไม่มีสมการแม้บรรทัดเดียว — มันอ่านค่าจากฟอร์ม แปลงหน่วย
เลือกฟังก์ชันตาม `mode` แล้วเรียกฟังก์ชันใน `dc_bias.py` สมการทั้งหมดจึงอยู่ที่เดียว
ถ้าต้องแก้สมการ ให้แก้ที่ `dc_bias.py` ที่เดียว ไม่ต้องแตะ HTML


