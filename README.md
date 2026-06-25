# Jarvis Project

โปรเจค Jarvis ที่สร้างขึ้นเพื่อเป็นตัวกลางในการควบคุมโปรแกรมและอุปกรณ์ต่างๆ โดยใช้ AI ในการประมวลผลคำสั่ง รับ Input ได้หลากหลาย (Chat, SSH, Camera, Microphone)

## โครงสร้างระบบ
- **Core Brain**: เลือกใช้รูปแบบ Core Brain (Next.js/Gemini Live + Hermes) + Microservices
- **Camera Streamer**: Flask Server (พอร์ต 5000) ดึงภาพกล้อง Logitech MeetUp และส่งภาพผ่าน REST API
- **Hand Detection**: ประมวลผลภาพจากตัวสตรีมเพื่อตรวจจับท่าทางมือ

## เทคโนโลยีและการตั้งค่าเครื่อง
- **API Cloud**: ใช้การดึง API จาก Cloud ทั้งหมด (Gemini + Nous Portal) เนื่องจากเซิร์ฟเวอร์หลัก (DIGITAL00) ไม่มี GPU แยก การรันบน Cloud จะลื่นที่สุด

---

## ขั้นตอนการติดตั้งและการใช้งานจาก Root Folder (ไม่ต้อง cd)

### 1. บริการ Web Speaker (Next.js)
ติดตั้งและรันจาก Root ด้วยคำสั่ง:
```bash
# ติดตั้ง dependencies
pnpm --prefix web-speaker install

# รันโหมดพัฒนา (Development)
pnpm --prefix web-speaker dev
```

### 2. บริการ Camera Streamer (Python Flask)
ติดตั้ง dependencies และรันจาก Root ด้วยคำสั่ง:
```bash
# สร้าง virtual environment (ถ้ายังไม่มี)
python -m venv camera-streamer/venv

# ติดตั้ง dependencies
camera-streamer/venv/Scripts/pip install -r camera-streamer/requirements.txt

# รัน Flask Service (รันบนพอร์ต 5000)
camera-streamer/venv/Scripts/python camera-streamer/main.py
```

### 3. บริการตรวจจับมือ Hand Detection (Python)
รันจาก Root ด้วยคำสั่ง:
```bash
python hand/main.py
```