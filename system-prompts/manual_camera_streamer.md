### [Manual] camera-streamer (Port 5000)
บริการเปิดและแชร์วิดีโอสตรีมภาพสดแบบเรียลไทม์จากกล้อง และควบคุม PTZ (Pan, Tilt, Zoom)

**Endpoints ที่เปิดให้บริการ:**
1. `GET /api/video_feed`
   - **หน้าที่**: ดึง MJPEG Stream ไปแสดงผลหรือประมวลผลต่อ (เช่น ส่งต่อให้ hand-detection)
2. `GET /api/capabilities`
   - **หน้าที่**: ตรวจสอบความสามารถของแกนควบคุมกล้องปัจจุบัน
3. `POST /api/ptz`
   - **หน้าที่**: สั่งควบคุมการขยับกล้องจริง
   - **Headers**: `Content-Type: application/json`
   - **Payload Schema**:
     ```json
     {
       "axis": "pan" | "tilt" | "zoom",
       "value": float  // เช่น 15.0 (หันขวา/ก้มเงย) หรือ -15.0 (หันซ้าย)
     }
     ```
