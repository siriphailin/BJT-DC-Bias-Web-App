# Design — BJT DC Bias Web App (Lab 02)

- **วันที่:** 2026-11-10
- **รายวิชา:** ENG29 2121 Computer Programming for Electrical Engineers (2/2569)
- **ที่มา:** ใบงาน Lab 02 — Building the First BJT DC Bias Web App
- **สถานะ:** รออนุมัติ (ยังไม่เริ่มเขียนโค้ด)

---

## 1. Intent และเหตุผล

นักศึกษาต้องส่ง Flask Web Application ที่คำนวณ **DC Operating Point** ของวงจร
NPN Common-Emitter แบบ **Voltage-Divider Bias** ได้จริง ภายในคาบ 3 ชั่วโมง

เหตุผลที่ไม่ใช่แค่ HTML: ใบงานต้องการให้เห็นว่า `.html` เป็นเพียง Template ที่ Server
นำมาแสดง ตัวเลขทั้งหมดต้องมาจาก Python Backend ที่รับ HTTP Request — เพื่อให้
นักศึกษาอธิบาย Frontend / Backend / Template / Static / HTTP Request ได้

## 2. Goals

1. เปิดผ่าน Browser ที่ `http://127.0.0.1:5000/` ได้ (HTTP 200) และเห็นฟอร์ม
2. รับ `VCC, R1, R2, RC, RE, β, VBE` แล้วคำนวณ `VB, VE, VC, VCE, IC` (แสดง `IB, IE` ด้วย)
3. ผลลัพธ์ตรงกับสมการในใบงาน ภายใต้ Forward-Active Approximation (β และ VBE คงที่)
4. Validation: ค่าผิด/ไม่ครบ/ไม่ใช่ตัวเลข → ข้อความ error ที่อ่านได้ และหน้าไม่ล้ม
5. Warning: นอก Active Region (Cutoff / Saturation) → แจ้งข้อจำกัด ไม่รายงานว่าแม่นยำ
6. Automated tests: ≥3 test ด้าน engineering math + ≥1 test ผ่าน Flask test client
7. โครงสร้างหลายไฟล์ตามใบงาน พร้อม README ที่ clone แล้วรันได้

## 3. Non-goals (ห้ามทำใน Lab นี้)

- AC small-signal, Gain, Bode plot
- Transient, Signal Generator, Amplitude/Frequency control
- DC Load Line, Interactive schematic, Overlay animation
- SPICE / ngspice solver
- Bias type อื่น (Fixed, Emitter bias), FET
- ระบบ login, ฐานข้อมูล, deploy ขึ้น cloud

## 4. Anti-goals (ถ้าเกิดขึ้นถือว่าล้มเหลว แม้เว็บจะเปิดได้)

- ตัวเลข DC Bias ถูกฮาร์ดโค้ดใน HTML หรือคำนวณด้วย JavaScript ฝั่ง client
- `dc_bias.py` import Flask หรือรู้จัก HTML/HTTP
- เปิดด้วย `file://` แล้วได้ผล (แปลว่าคำนวณฝั่ง client)
- Test ผ่านโดยไม่เคยรันจริง หรือ test ที่ assert ค่าที่เขียนค้างไว้ในเทมเพลต
- แสดงค่าที่ออกนอก Active Region โดยไม่มี warning

## 5. Constraints

| ข้อ | ค่า |
|---|---|
| ภาษา/เฟรมเวิร์ก | Python 3.14 + Flask 3.x (ตามใบงาน) |
| เทสต์ | `unittest` (ใบงานใช้ `python -m unittest discover -s tests -v`) |
| พอร์ต | 5000 (`python -m flask --app app run --debug`) |
| หน้าจอ | Server-rendered เท่านั้น ไม่ใช้ JavaScript |
| เวลา | 3 ชั่วโมง รวมติดตั้ง/ทดสอบ/commit |
| Repo | `C:\Users\B6837020\Documents\GitHub\BJT DC Bias Web App` (root = project root) |
| Commit | ผ่าน GitHub Desktop ตามที่ผู้ใช้กำหนด |

## 6. Approaches ที่พิจารณา

| | วิธี | ข้อดี | ข้อเสีย | สรุป |
|---|---|---|---|---|
| **A** | Server-rendered POST + Jinja | ตรงกับ data-flow ในใบงาน, ไม่มี JS, test client ตรงไปตรงมา | หน้า reload ทุกครั้ง | **เลือก** |
| B | JSON API + `fetch` | ตอบสนองไว ต่อยอด knob ได้ | โค้ดสองฝั่ง เสี่ยงไม่ทันคาบ | ไม่เลือก (เป็น upgrade path ของ W5–W7) |
| C | HTMX partial swap | ไม่ reload | เพิ่ม dependency นอกหลักสูตร | ไม่เลือก |

**เหตุผลที่เลือก A:** Acceptance A1–A7 วัดที่ Flask route + test client และใบงานระบุ
"HTML response rendered for Browser" ชัดเจน — A คือเส้นทางที่สั้นที่สุดที่ผ่านทุกข้อ
`dc_bias.py` จะถูกเขียนเป็นฟังก์ชันบริสุทธิ์ เพื่อให้ย้ายไป B ภายหลังได้โดยไม่แตะสมการ

## 7. โครงสร้างไฟล์

```
BJT DC Bias Web App/          # repo root = project root
├── app.py                    # Flask app + routes (GET /, POST /calculate)
├── dc_bias.py                # สมการ DC Bias ล้วน (ไม่ import Flask)
├── templates/
│   └── index.html            # ฟอร์ม + ผลลัพธ์ (Jinja)
├── static/
│   └── style.css             # responsive layout
├── tests/
│   ├── test_dc_bias.py       # unit tests ของสมการ/validation/warning
│   └── test_web.py           # Flask test client
├── requirements.txt          # Flask
├── README.md                 # วิธีติดตั้ง/รัน/ทดสอบ
├── AGENTS.md                 # conventions สำหรับ AI
├── .gitignore                # .venv/, __pycache__/, .env
└── docs/
    ├── design-note.md
    ├── validation.md         # สมมติฐาน + ค่าอ้างอิงที่คำนวณมือ
    └── superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md
```

## 8. แบบจำลองและสมการ (ตามใบงาน)

```
VTH = VCC · R2 / (R1 + R2)
RTH = R1 · R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β + 1)·RE)
IC  = β · IB
IE  = (β + 1) · IB
VE  = IE · RE
VB  = VE + VBE
VC  = VCC − IC · RC
VCE = VC − VE
```

### ค่าอ้างอิงสำหรับตรวจ (คำนวณมือโดยไม่ใช้เว็บ)

VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V

| ปริมาณ | ค่าในใบงาน | ค่าที่คำนวณเต็มความละเอียด | หมายเหตุ |
|---|---|---|---|
| VTH | 2.1639 V | 2.16393 V | |
| RTH | 18.0328 kΩ | 18.03279 kΩ | |
| IB | 12.298 µA | 12.2986 µA | ใบงานปัดเป็น 12.298 µA |
| IC | 1.2298 mA | 1.22986 mA | ใบงานคำนวณจาก IB ที่ปัดแล้ว |
| IE | 1.2421 mA | 1.24216 mA | |
| VE | 1.2421 V | 1.24216 V | |
| VB | 1.9421 V | 1.94216 V | |
| VC | 9.2944 V | 9.29431 V | |
| VCE | 8.0523 V | 8.05216 V | ต่างกัน 0.0002 V (0.002 %) |

**ความต่างจากค่าที่ปัดในใบงาน:** ใบงานปัด `IB = 12.298 µA` ก่อน แล้วเอาไปคูณต่อ
(`IC = 100 × 12.298 µA = 1.2298 mA`) ทำให้ค่าปลายทางต่างจากการคำนวณเต็มความละเอียด
ในหลักที่ 4–5 — โปรแกรม **ไม่ปัดกลางทาง** (ถูกต้องกว่า) จึงได้ `VCE = 8.05216 V`
ทั้งสองค่าแสดงเป็น 3 ตำแหน่งทศนิยมได้ `8.052 V` เท่ากัน

ใช้ชุดนี้เป็นตัวเลขขั้นต่ำ 1 เคสใน test (tolerance 1e-3) และใช้ตรวจซ้ำด้วยมือใน
`docs/validation.md` — ในเอกสารให้แสดง **ค่าที่คำนวณเต็มความละเอียด** เป็นหลัก
และอธิบายว่าใบงานปัดเศษกลางทาง

## 9. Decisions (ข้อที่ใบงานเปิดไว้ — ผมตัดสินให้ และแก้ได้)

| # | เรื่อง | ข้อตัดสิน | เหตุผล |
|---|---|---|---|
| D1 | หน่วยตัวต้านทาน | dropdown `kΩ` / `Ω` ต่อช่อง (เลือกโดยผู้ใช้) | ตรงกับการเขียนวงจรจริง (100k, 2.2k) และได้ทดสอบ logic แปลงหน่วย |
| D2 | เกณฑ์ Cutoff | `VTH ≤ VBE` → warning "Cutoff: วงจรไม่อยู่ใน Forward-Active" | ตามใบงาน; IB ≤ 0 ทำให้สมการไม่มีความหมาย |
| D3 | เกณฑ์ Saturation | `VCE < 0.3 V` → warning "Saturation: แบบจำลองใช้ไม่ได้" (ชั้นเดียว ไม่มีสถานะ "ใกล้ Saturation") | ใบงานกำหนด warning แค่ Cutoff และ Saturation (A5) — เพิ่มสถานะที่ 3 จะเป็นการขยาย scope ที่อาจารย์ไม่ได้สั่ง; 0.3 V เป็นค่าอ้างอิงมาตรฐานของ VCE(sat) |
| D4 | ค่าที่แสดงเมื่อมี warning | ยังแสดงตัวเลข แต่ติดป้าย "ค่าประมาณ — อย่าใช้ตัดสินใจ" | ใบงานห้ามอ้างว่าแม่นยำ แต่ไม่ห้ามแสดง เพื่อการเรียน |
| D5 | HTTP status | GET `/` = 200, POST `/calculate` สำเร็จ = 200, input ผิด = 400 (re-render ฟอร์มพร้อม error) | ตรวจด้วย test client ได้ตรง และ semantically ถูก |
| D6 | ค่าเริ่มต้นในฟอร์ม | prefill ค่าตัวอย่างจากใบงาน | ทำให้ demo เร็วและลดพิมพ์ผิด |
| D7 | ภาษา UI | ป้ายภาษาไทย + สัญลักษณ์ทางวิศวกรรม (VCC, R1, …) | ผู้ใช้เป็นนักศึกษาไทย |
| D8 | รูปแบบตัวเลข | แรงดัน 3 ตำแหน่งทศนิยม (V), กระแสแสดง mA 3 ตำแหน่ง (IB แสดง µA ด้วย) | หน่วยกำกับชัดตามใบงาน |
| D9 | เก็บค่าที่กรอกเมื่อ error | คงค่าที่ผู้ใช้กรอกไว้ในฟอร์ม | ลดการพิมพ์ซ้ำ |
| D10 | ชื่อ route | `GET /` และ `POST /calculate` | ใบงานระบุ "POST /calculate หรือ POST /" — เลือกแบบชัดเจน |
| D11 | แผนภาพวงจร | inline SVG ใน `templates/index.html` แสดงค่าอุปกรณ์ (VCC, R1, R2, RC, RE, β) และแรงดันที่ node (VB, VE, VC) พร้อมแผง VCE/IC/IB — ตัวเลขเติมด้วย Jinja จากค่าที่ผู้ใช้กรอกและผลที่ Python คำนวณ | ผู้ใช้เลือก (ตัวเลือก ข); inline SVG ไม่ต้องใช้ JavaScript จึงไม่ขัดข้อห้าม JS ฝั่ง client และผลทุกตัวยังมาจาก Python |

## 10. Validation ที่ต้องมี

- `VCC ≤ 0`, `R1 ≤ 0`, `R2 ≤ 0`, `RC ≤ 0`, `RE ≤ 0`, `β ≤ 0` → error (ทุกตัวต้านทานต้อง > 0 ตาม A4 ของใบงาน)
- `VBE` ต้องอยู่ในช่วง `0 < VBE < 1.0` V → error ถ้านอกช่วง
- ช่องว่าง / ไม่ใช่ตัวเลข / ค่าติดลบ → error ระบุชื่อช่องที่ผิด
- error ทุกกรณีต้องไม่ทำให้เกิด HTTP 500

## 11. Tests ที่ต้องมี (ขั้นต่ำตามใบงาน A6)

`tests/test_dc_bias.py` (engineering)
1. ค่าอ้างอิงชุดตัวอย่าง → ตรงกับตารางข้อ 8
2. แปลงหน่วย: 100 kΩ + 22 kΩ ให้ผลเท่ากับ 100000 Ω + 22000 Ω
3. `β` เปลี่ยน → IC เพิ่มขึ้นแบบ monotonic และตรงกับสมการที่คำนวณสด (ไม่ assert proportional เพราะ IC ไม่เป็นสัดส่วนตรงกับ β เมื่อ RE > 0)
4. `VTH ≤ VBE` → คืน warning Cutoff
5. `VCE < 0.3` → คืน warning Saturation
6. ค่าผิด (R ≤ 0, β ≤ 0, ไม่ใช่ตัวเลข) → raise/คืน error ที่อ่านได้

`tests/test_web.py` (HTTP)
7. `GET /` → 200 และมีช่องกรอกครบ
8. `POST /calculate` ค่าถูกต้อง → 200 และ HTML มี `8.052` (VCE) — พิสูจน์ว่าเป็นค่าจาก backend
9. `POST /calculate` ค่าผิด → 400 และมีข้อความ error

## 12. Acceptance mapping

| ใบงาน | ครอบด้วย |
|---|---|
| A1 GET / | test 7 |
| A2 POST คำนวณจริง | test 8 + route เรียก `dc_bias` |
| A3 ตรงกับการคำนวณอิสระ | test 1 + `docs/validation.md` |
| A4 Validation | test 6, 9 + D5 |
| A5 Warning นอก Active Region | test 4, 5 + D2–D4 |
| A6 Unit + HTTP tests | tests 1–9 |
| A7 GitHub reproducibility | README + `.gitignore` + commit ผ่าน GitHub Desktop |

## 13. ความเสี่ยง

| ความเสี่ยง | การรับมือ |
|---|---|
| Python 3.14 ใหม่มาก อาจมีปัญหา wheel ของ dependency | ใช้ Flask เดียว (pure Python) — ถ้าติดตั้งไม่ได้ ใช้ `py -3.7` ไม่ได้ (EOL) → ติดตั้ง 3.12 เพิ่ม |
| เวลาคาบไม่พอ | ทำ A ก่อน (route + สมการ + test) แล้วค่อยแต่ง CSS |
| ค่าตัวอย่างในภาพใบงานไม่ตรงกับสมการ | ยึดสมการ + ตารางข้อ 8 ที่คำนวณมือ ไม่ยึดภาพ |
| commit `.venv/` | `.gitignore` ตั้งแต่ commit แรก |

## 14. สิ่งที่เหลือให้ผู้วางแผน (plan) ตัดสิน

- ลำดับงานย่อยและจุด commit ที่เหมาะสม (แนะนำ 3–4 commit)
- การแบ่งหน้าจอ CSS (layout ละเอียด) — ไม่กระทบ acceptance
- จำนวน test เพิ่มเติมเกินขั้นต่ำ (ถ้ามีเวลา)
