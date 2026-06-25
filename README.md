# Jarvis Project

ระบบผู้ช่วยอัจฉริยะ (Jarvis Workspace Assistant) โครงสร้างแบบ Core Brain + Microservices

## โครงสร้างโปรเจคและ Microservices
- `web-speaker/` - [Core Brain Web UI (Next.js)](./web-speaker/README.md)
- `camera-streamer/` - [MeetUp Camera Streaming API (Python Flask)](./camera-streamer/README.md)
- `hand/` - [Hand Gesture Mouse Control (Python Mediapipe)](./hand/README.md)
- `bluetooth-controller/` - [Bluetooth Remote Control (Python Flask & ESP32-C3)](./bluetooth-controller/README.md)

---

## วิธีการเริ่มต้นรันระบบอย่างรวดเร็ว (Quick Start)

กรุณาเปิด Git Bash และรันคำสั่งแยกในแต่ละหน้าต่าง (จาก Root Folder) ดังนี้:

### 1. รัน Core Brain Web UI
```bash
pnpm --prefix web-speaker dev
```

### 2. รัน Camera Streamer
```bash
camera-streamer/venv/Scripts/python camera-streamer/main.py
```

### 3. รัน Bluetooth Controller
```bash
bluetooth-controller/venv/Scripts/python bluetooth-controller/main.py
```

### 4. รัน Hand Mouse Control
```bash
python hand/main.py
```

สำหรับรายละเอียดการติดตั้งและการดีบั๊กเฉพาะส่วน กรุณาเปิดอ่านไฟล์ `README.md` ในโฟลเดอร์ของแต่ละโมดูลย่อย