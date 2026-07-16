# Jarvis Project (Core Brain + Microservices)

ระบบผู้ช่วยอัจฉริยะแบบแยกส่วน (Core Brain + Microservices) เพื่อประมวลผลคำสั่ง, วิเคราะห์ภาพ/มือ และควบคุมทีวีผ่านสัญญาณบลูทูธ

---

## 🛠️ โครงสร้างระบบและโมดูลย่อย

*   **`web-speaker/` - [Core Brain Web UI (Next.js)](./web-speaker/README.md) [รันพอร์ต 3000]**
    *   หน้าจอหลักของจาร์วิส รับคำส่งการด้วยเสียง/ข้อความและเชื่อมต่อ Google Gemini API
    *   มี API `POST /api/trigger` เพื่อรับคำสั่งปลุก (Wake) หรือสั่งงานจากภายนอก
*   **`services/camera-streamer/` - [Logitech MeetUp Camera API (Flask)](./services/camera-streamer/README.md) [รันพอร์ต 5000]**
    *   บริการเปิดและแชร์วิดีโอสตรีมภาพสดแบบเรียลไทม์จากกล้องผ่าน MJPEG `/api/video_feed`
    *   รองรับคำสั่งควบคุมทิศทางกล้อง Pan, Tilt, Zoom (PTZ)
*   **`services/hand-detection/` - [Hand Gesture Control (Python MediaPipe)](./services/hand-detection/README.md)**
    *   ตรวจจับจุดเชื่อมต่อของมือ (Hand Landmarks) เพื่อจำลองการขยับเมาส์ คลิก และเลื่อนหน้าจอ
    *   ดึงภาพผ่านสตรีมพอร์ต 5000 (ตัดปัญหาดีเลย์ด้วยระบบ Latest Frame Thread)
    *   **Async API Mode:** ส่งพิกัดผ่าน HTTP API ไปควบคุมทีวีโดยไม่แย่งพอร์ตบอร์ด
*   **`services/bluetooth-controller/` - [Bluetooth Controller (Flask & ESP32-C3)](./services/bluetooth-controller/README.md) [รันพอร์ต 5001]**
    *   เซิร์ฟเวอร์หลักที่เชื่อมต่อ USB Serial (เช่น `COM19`) ไปหาบอร์ด ESP32-C3
    *   **Firmware (BLE Keyboard + Mouse Combo):** บอร์ดทำหน้าที่แปลงคำสั่ง Serial เป็นบลูทูธควบคุมทีวี (มีไฟบอกสถานะและระบบป้องการค้างจากการตัดการเชื่อมต่ออัตโนมัติ)
*   **`tests/` - สคริปต์สำหรับการทดสอบเชื่อมต่อและความสามารถการทำงาน**

---

## 🚀 วิธีการเริ่มต้นรันระบบอย่างรวดเร็ว (Quick Start)

กรุณาเปิด Git Bash แยกในแต่ละหน้าต่าง (รันจาก Root Folder) ดังนี้:

### 1. รัน Core Brain Web UI
```bash
pnpm --prefix web-speaker dev
```

### 2. รัน Camera Streamer (เว็บสตรีมกล้อง)
```bash
services/camera-streamer/venv/Scripts/python services/camera-streamer/main.py
```

### 3. รัน Bluetooth Controller (ตัวคุยบอร์ด USB)
```bash
services/bluetooth-controller/venv/Scripts/python services/bluetooth-controller/main.py
```

### 4. รัน Hand Mouse Control (ในโหมด API - แนะนำ)
```bash
python services/hand-detection/main.py api
```

---

## 📈 สถานะการพัฒนาในปัจจุบัน (Project Status)
*   **Phase 1: Streaming & Gesture (เสร็จสมบูรณ์):** ดึงภาพเรียลไทม์ผ่านเครือข่ายสำเร็จ ขยับเมาส์ด้วยนิ้วชี้และควบคุมระบบข้ามพอร์ตได้ไม่มีหน่วงสะสม
*   **Phase 2: Bluetooth & Smart TV (เสร็จสมบูรณ์):** สั่งงานทีวีจริงผ่านบลูทูธของบอร์ด ESP32-C3 ทั้งการเพิ่ม/ลดเสียง และจำลองพิกัดเมาส์ไร้สายผ่าน API แบบรันร่วมกันได้ทุกตัว
*   **Phase 3: Integration (กำลังดำเนินการ):** การเอาคำสั่งจากเสียงและ Gemini Live มาแปลงเป็นทริกเกอร์สั่งงานแบบเรียลไทม์เข้าหน้าเว็บและ Smart TV