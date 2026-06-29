# Web Speaker (Core Brain UI)

ระบบส่วนหน้าเว็บ (Web UI) พัฒนาด้วย Next.js และ React ทำหน้าที่เชื่อมต่อการประมวลผลเสียงและคำสั่งของ Jarvis เข้ากับผู้ใช้

## การติดตั้งและการใช้งานจาก Root
```bash
# ติดตั้ง dependencies
pnpm --prefix web-speaker install

# รันในโหมดพัฒนา
pnpm --prefix web-speaker dev
```

## ตัวแปรสภาพแวดล้อม (.env.local)
ก่อนรันระบบ ต้องตั้งค่าคีย์ในไฟล์ `web-speaker/.env.local` ดังนี้:
- `NEXT_PUBLIC_GEMINI_API_KEY` - คีย์ของ Google Gemini API
- `PUSHER_APP_ID`, `PUSHER_KEY`, `PUSHER_SECRET`, `PUSHER_CLUSTER` - ตั้งค่าสำหรับการเชื่อมต่อ Pusher real-time
- `URL_TARGETR`, `USERNAME_TARGETR`, `PASSWORD_TARGETR` - ข้อมูลยืนยันตัวตนสำหรับดึงข้อมูล Targetr API


## API สำหรับสั่งการ & เชื่อมต่อภายนอก (REST API Trigger)

ตัวเว็บรองรับการรับคำสั่งจากไมโครเซอร์วิสอื่น (เช่น สคริปต์ตรวจจับท่าทางมือ หรือสคริปต์ตรวจจับคำพูด) ผ่าน **SSE (Server-Sent Events)** บนพอร์ต `3000`:

*   **`POST /api/trigger`** - สั่งการทำงานไปยังหน้าเว็บ
    *   **Headers:** `Content-Type: application/json`
    *   **Payload:** 
        ```json
        {
          "action": "toggle" | "start" | "stop" | "sendText" | "wakeAndGreet",
          "message": "ข้อความสำหรับการส่งคำสั่งหรือทักทาย (สำหรับ sendText/wakeAndGreet)"
        }
        ```

### ตัวอย่างคำสั่งทดสอบด้วย curl:

1. **สั่ง Toggle เปิด/ปิด Jarvis:**
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"action": "toggle"}' http://localhost:3000/api/trigger
   ```

2. **สั่งตื่นและเริ่มทักทายทันที (Wake and Greet):**
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"action": "wakeAndGreet", "message": "สวัสดีจาร์วิส แนะนำตัวเองหน่อย"}' http://localhost:3000/api/trigger
   ```

3. **สั่งปิดการทำงาน (Standby):**
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"action": "stop"}' http://localhost:3000/api/trigger
   ```
