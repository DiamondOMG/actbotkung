# โครงสร้างโปรเจค Jarvis

## 1. โครงสร้างโฟลเดอร์ปัจจุบัน
- `services/camera-streamer` - Flask Server ดึงสตรีมภาพและควบคุม PTZ กล้อง Logitech MeetUp
- `services/hand-detection` - ระบบตรวจจับมือและแปลงเป็นการขยับเมาส์
- `services/bluetooth-controller` - โมดูลควบคุมทีวีผ่าน ESP32-C3
- `system-prompts` - โฟลเดอร์เก็บ System Prompts ของสมองจาร์วิส
- `web-speaker` - Next.js Web UI และจุดประสานงาน (Core Brain)
- `tests` - โฟลเดอร์เก็บสคริปต์สำหรับการทดสอบเชื่อมต่อและความสามารถการทำงาน

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

- **เฟส 3: Dual-Brain & Shared Memory Framework**
  - [x] ออกแบบและสร้างโฟลเดอร์เก็บ System Prompts สำหรับสมองสองส่วน (`system-prompts/`)
  - [ ] สร้างบอร์ดหรือเซิร์ฟเวอร์สำหรับ Shared Memory State ในการเก็บข้อมูลตัวแปรของกล้อง/ทีวี และผลการสแกนแบบสด
  - [ ] เพิ่มความสามารถให้ `web-speaker` ในการดึงข้อมูล State กลางมาอัปเดตบนหน้าจอ
  - [ ] เพิ่มคำสั่ง Tool Calling ควบคุมอุปกรณ์ต่างๆ (เช่น สั่งขยับกล้อง PTZ หรือปรับเสียงทีวี) ผ่าน API จากหน้าเว็บ
  - [ ] พัฒนาระบบแจ้งเตือนขัดจังหวะ (Event Trigger) เมื่อมีเหตุการณ์สำคัญเกิดขึ้นขณะกำลังสนทนา

- **เฟส 4: Vision & Automation**
  - [ ] สร้างระบบ On-Demand Vision Tool ให้ Jarvis สามารถสั่งดึงรูปภาพ 1 เฟรมไปประมวลผลด้วย Gemini API เพื่อลดการใช้ Token
  - [ ] พัฒนาโมดูลตรวจจับวัตถุหรือคนแบบโลคอล (Local Motion/Face Detection) ทำงานเป็นเบื้องหลัง
  - [ ] ตั้งค่าการแจ้งเตือนจากโมดูลตรวจจับโลคอลไปหาหน้าเว็บเพื่อปลุก Jarvis (wakeAndGreet)

- **เฟส 5: Long-term Memory Vault**
  - [x] ยืนยันตำแหน่งความจำระยะยาวใน Google Drive (พิกัดไฟล์ดัชนี: `G:\My Drive\AI Agent Vault\00_INDEX.md`)
    > [!NOTE]
    > หากย้ายเครื่องใหม่ ต้องเปิดสิทธิ์ Google Drive ให้ Mount มาที่ไดรฟ์ `G:\` เสมอ เพื่อไม่ให้ Path ของความจำระยะยาวพัง
  - [ ] สร้างระบบบันทึกความจำสอดคล้องกับสารบัญคลังข้อมูลเมื่อจบบทสนทนา


