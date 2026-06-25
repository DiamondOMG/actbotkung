# Jarvis Project

โปรเจค Jarvis ที่สร้างขึ้นเพื่อเป็นตัวกลางในการควบคุมโปรแกรมและอุปกรณ์ต่างๆ โดยใช้ AI ในการประมวลผลคำสั่ง รับ Input ได้หลากหลาย (Chat, SSH, Camera, Microphone)

## โครงสร้างระบบ
- **Core Brain**: เลือกใช้รูปแบบ Core Brain (Next.js/Gemini Live + Hermes) + Microservices
- **Camera Streamer**: Flask Server (พอร์ต 5000) ดึงภาพกล้อง Logitech MeetUp และส่งภาพผ่าน REST API
- **Hand Detection**: ประมวลผลภาพจากตัวสตรีมเพื่อตรวจจับท่าทางมือ

## เทคโนโลยีและการตั้งค่าเครื่อง
- **API Cloud**: ใช้การดึง API จาก Cloud ทั้งหมด (Gemini + Nous Portal) เนื่องจากเซิร์ฟเวอร์หลัก (DIGITAL00) ไม่มี GPU แยก การรันบน Cloud จะลื่นที่สุด

---

## วิธีการใช้งานระบบ (Quick Start)

### 1. เปิดใช้งานบริการ Camera Streamer
เปิด Git Bash และพิมพ์คำสั่งดังนี้เพื่อรัน Flask Service บนพอร์ต 5000:
```bash
# เปิด venv และรันโปรแกรม
source camera-streamer/venv/Scripts/activate
python camera-streamer/main.py
```
*ตัวสตรีมจะทำงานที่ http://localhost:5000/api/video_feed*

### 2. เปิดใช้งานระบบตรวจจับมือ (Hand Detection)
เปิด Git Bash อีกหน้าต่างหนึ่ง แล้วพิมพ์คำสั่ง:
```bash
python hand/main.py
```