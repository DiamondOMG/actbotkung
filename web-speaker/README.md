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
