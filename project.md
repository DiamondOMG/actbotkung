# โครงสร้างโปรเจค Jarvis

## 1. โครงสร้างโฟลเดอร์ปัจจุบัน
- `camera-streamer` - Flask Server ดึงสตรีมภาพและควบคุม PTZ กล้อง Logitech MeetUp
- `hand` - ระบบตรวจจับมือและแปลงเป็นการขยับเมาส์
- `bluetooth-controller` (กำลังจะสร้าง) - โมดูลควบคุมทีวีผ่าน ESP32-C3

## 2. โฟลวการทำงานของระบบ
1. **Core Brain** (Next.js / Gemini Live + Hermes) เป็นแกนกลางรับส่งข้อมูล
2. **Camera Streamer** รันที่พอร์ต `5000` ดึงภาพจากกล้องและแชร์สตรีมที่ `/api/video_feed` รวมถึงส่งคำสั่งควบคุม PTZ ผ่าน `/api/ptz` แบบเรียลไทม์ด้วยไดรเวอร์ `duvc-ctl`
3. **Hand Detection** ดึงภาพจาก `/api/video_feed` ของ Flask Server มาใช้ประมวลผลท่าทางมือและจำลองเมาส์บน OS
4. **Bluetooth Controller** (ถัดไป) รับคำสั่งส่งต่อไปยังทีวีผ่าน USB Serial ไป ESP32-C3

## 3. Tasks ในแต่ละเฟส
- **เฟส 1: Camera Streaming & Input Interface**
  - [x] ย้ายกล้องไปรันบน Flask Server แชร์ผ่าน REST API
  - [x] คอนโทรล PTZ แบบ Realtime ไม่กระตุกผ่านไดรเวอร์ `duvc-ctl`
  - [x] ปรับสคริปต์ตรวจจับมือให้ดึงข้อมูลภาพจาก API แทนต่อตรงกล้อง
  - [x] ลบโฟลเดอร์เก่า `logitech-meeting-camera`
- **เฟส 2: Bluetooth Integration**
  - [x] พัฒนาโมดูล `bluetooth-controller` บน PC (Python service)
  - [x] ส่งคำสั่งควบคุมทีวีผ่าน USB Serial ไปยัง ESP32-C3
