import atexit
import cv2
from flask import Flask, Response, request, jsonify
from flask_cors import CORS

from drivers.logitech_meetup import LogitechMeetupDriver

app = Flask(__name__)
# ปลดล็อก CORS เพื่อให้ Next.js หรือเว็บเพจอื่นๆ ยิงดึงข้อมูลข้ามพอร์ตได้
CORS(app)

print("กำลังเริ่มเชื่อมต่อเข้ากับกล้องตัวหลัก (Camera 0)...")
# เปิดกล้องตัวแรกของเครื่องผ่าน DirectShow บน Windows
camera_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera_capture.isOpened():
    print("❌ ไม่สามารถเปิดการเชื่อมต่อกับกล้องหลักได้ กรุณาตรวจสอบว่ามีโปรแกรมอื่นใช้งานอยู่หรือไม่")
else:
    print("✅ เชื่อมต่อกล้องหลักสำเร็จ")

import threading
import time

# ล็อกสำหรับควบคุมความปลอดภัยในการเข้าถึงออบเจกต์กล้องข้าม Thread
camera_lock = threading.Lock()

# เรียกใช้งานไดรเวอร์สำหรับควบคุมกล้อง Logitech MeetUp
camera_driver = LogitechMeetupDriver(camera_capture)

def generate_frames():
    """ดึงภาพจากกล้องแบบวนลูปแล้วสตรีมเป็น JPEG bytes (แบบ Thread-safe)"""
    while True:
        with camera_lock:
            if not camera_capture.isOpened():
                break
            success, frame = camera_capture.read()
            
        if not success:
            # ป้องกันลูปทำงานหนักเกินไปถ้ากล้องดึงภาพไม่ได้ชั่วคราว
            time.sleep(0.03)
            continue
        
        # เข้ารหัสภาพเป็น JPEG format
        success_encode, jpeg_buffer = cv2.imencode('.jpg', frame)
        if not success_encode:
            continue
            
        frame_bytes = jpeg_buffer.tobytes()
        # ส่งข้อมูลแบบ Multipart Stream
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/api/video_feed', methods=['GET'])
def video_feed():
    """Endpoint สำหรับดึง MJPEG Stream เพื่อไปแสดงผลบนหน้าเว็บหรือประมวลผลต่อ"""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/api/capabilities', methods=['GET'])
def get_capabilities():
    """Endpoint สำหรับตรวจสอบความสามารถของไดรเวอร์กล้องปัจจุบัน"""
    return jsonify({
        "status": "success",
        "capabilities": camera_driver.get_capabilities()
    })

@app.route('/api/ptz', methods=['POST'])
def control_ptz():
    """Endpoint สำหรับส่งคำสั่งขยับกล้อง (Pan, Tilt, Zoom) (แบบ Thread-safe)"""
    try:
        payload = request.json or {}
        axis = payload.get('axis')          # เช่น 'pan', 'tilt', 'zoom'
        value = payload.get('value')        # ค่าองศา/ระดับการหมุนตัวเลข float
        
        if axis not in camera_driver.get_capabilities():
            return jsonify({
                "status": "error",
                "message": f"ไดรเวอร์ของกล้องนี้ไม่รองรับคุณสมบัติแกน: {axis}"
            }), 400

        try:
            value_float = float(value)
        except (TypeError, ValueError):
            return jsonify({
                "status": "error",
                "message": "ค่า value จะต้องเป็นตัวเลข"
            }), 400

        success = False
        with camera_lock:
            if axis == 'pan':
                success = camera_driver.set_pan(value_float)
            elif axis == 'tilt':
                success = camera_driver.set_tilt(value_float)
            elif axis == 'zoom':
                success = camera_driver.set_zoom(value_float)

        # ส่งคืนผลลัพธ์
        return jsonify({
            "status": "success",
            "axis": axis,
            "value_applied": value_float,
            "driver_acknowledged": bool(success)
        })

    except Exception as error:
        return jsonify({"status": "error", "message": str(error)}), 500

    except Exception as error:
        return jsonify({"status": "error", "message": str(error)}), 500

@atexit.register
def cleanup_camera():
    """คืนทรัพยากรกล้องให้ OS อัตโนมัติเมื่อปิดโปรแกรม"""
    if camera_capture.isOpened():
        camera_capture.release()
        print("🛑 คืนทรัพยากรกล้องตัวหลักเรียบร้อยแล้ว")

if __name__ == '__main__':
    print("--- Camera Streamer Service เริ่มทำงานที่พอร์ต 5000 ---")
    # use_reloader=False เพื่อป้องกันไม่ให้ Flask รันกระบวนการซ้อน
    # ซึ่งจะส่งผลให้โปรเซสที่สองเปิดกล้องไม่สำเร็จเพราะโดนล็อก
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
