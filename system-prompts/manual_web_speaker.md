### [Manual] web-speaker (Port 3000)
เว็บแอปพลิเคชัน Next.js ทำหน้าที่เป็น Core Brain ส่วนกลาง คอยแสดงผลลัพธ์และรองรับ REST API Trigger จากอุปกรณ์อื่น

**Endpoints ที่เปิดให้บริการ:**
1. `POST /api/trigger`
   - **หน้าที่**: สั่งคำสั่งดำเนินการหรือปลุกแสดงผลหน้าเว็บ
   - **Payload Schema**:
     ```json
     {
       "action": "toggle" | "start" | "stop" | "sendText" | "wakeAndGreet",
       "message": string // ตัวเลือกเพิ่มเติมสำหรับข้อความทักทายหรือส่งคำสั่งเสียง
     }
     ```
