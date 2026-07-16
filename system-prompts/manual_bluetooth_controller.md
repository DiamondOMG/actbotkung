### [Manual] bluetooth-controller (Port 5001)
บริการหลักเพื่อเชื่อมต่อ USB Serial ไปหาบอร์ด ESP32-C3 แล้วแปลงคำสั่งไปควบคุม Smart TV ผ่านบลูทูธ

**Endpoints ที่เปิดให้บริการ:**
1. `GET /api/status`
   - **หน้าที่**: ตรวจสอบสถานะการเชื่อมต่อ Serial และสถานะบลูทูธของบอร์ด
2. `POST /api/tv`
   - **หน้าที่**: ส่งคำสั่งปุ่มควบคุมทีวีมาตรฐาน
   - **Payload Schema**:
     ```json
     {
       "action": "POWER" | "VOLUMEUP" | "VOLUMEDOWN" | "MUTE" | "UP" | "DOWN" | "LEFT" | "RIGHT" | "ENTER" | "BACK" | "HOME"
     }
     ```
3. `POST /api/send`
   - **หน้าที่**: ส่งคำสั่งดิบ (Raw Serial Command) ไปยังบอร์ดโดยตรง
   - **Payload Schema**:
     ```json
     {
       "command": string  // เช่น "M dx dy" สำหรับควบคุมเมาส์ หรือคำสั่งปุ่มเฉพาะ
     }
     ```
