# Hand Tracking & Mouse Control

สคริปต์ Python ใช้ไลบรารี Mediapipe และ OpenCV ดึงภาพจากบริการ Camera Streamer เพื่อแปลงการเคลื่อนไหวของมือเป็นการควบคุมเมาส์บนระบบปฏิบัติการ

## การรันคำสั่งจาก Root
```bash
python hand/main.py
```

## ข้อมูลการทำงาน
- ดึงภาพสตรีมวิดีโอจาก `http://localhost:5000/api/video_feed` แทนการต่อตรงกับพอร์ตกล้อง
- ใช้ปลั๊กอิน `SoftwareMouse` (เรียกใช้งาน PyAutoGUI) ในการจำลองการเลื่อนเมาส์และการคลิก
- ปิดระบบ FAILSAFE ของ PyAutoGUI เพื่อป้องกันไม่ให้โปรแกรมแครชเมื่อเมาส์เข้าใกลุมุมจอ
