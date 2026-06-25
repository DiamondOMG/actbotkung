# Camera Streamer (Camera service)

บริการดึงสตรีมภาพวิดีโอจากกล้อง Logitech MeetUp และเป็น REST API ควบคุม PTZ แบบเรียลไทม์ผ่านไดรเวอร์ `duvc-ctl`

## การติดตั้งและการใช้งานจาก Root
```bash
# สร้าง virtual environment
python -m venv camera-streamer/venv

# ติดตั้ง dependencies
camera-streamer/venv/Scripts/pip install -r camera-streamer/requirements.txt

# รันระบบสตรีมเมอร์
camera-streamer/venv/Scripts/python camera-streamer/main.py
```

## REST API Endpoints
- `GET /api/video_feed` - ดึง MJPEG Stream (วิดีโอสตรีมสด)
- `GET /api/capabilities` - ตรวจสอบความสามารถของไดรเวอร์กล้อง
- `POST /api/ptz` - ส่งคำสั่ง Pan, Tilt, Zoom ไปยังกล้อง Logitech MeetUp
  - Payload: `{"axis": "pan" | "tilt" | "zoom", "value": float}`
