from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2

app = Flask(__name__)
# ปลดล็อก CORS เพื่อให้ไฟล์ index.html ที่เปิดบนเบราว์เซอร์ ยิงข้อมูลข้ามมาหา Python ได้
CORS(app) 

# รหัสอ้างอิงคุณสมบัติฮาร์ดแวร์ (UVC Control Constants)
# กล้องส่วนใหญ่รวมถึง Logitech MeetUp จะใช้เลขโครงสร้างชุดนี้
CAP_PROP_PAN = 1004
CAP_PROP_TILT = 1005
CAP_PROP_ZOOM = 1006

@app.route('/api/ptz', methods=['POST'])
def control_camera():
    try:
        data = request.json
        axis = data.get('axis')      # รับค่าประเภทแกน: 'pan', 'tilt', 'zoom'
        val = float(data.get('value')) # รับค่าตัวเลของศาจากตัวสไลเดอร์
        
        # เชื่อมต่อกล้องตัวแรกของเครื่อง (ดักจับผ่าน DirectShow บน Windows เพื่อความเสถียร)
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        if not cap.isOpened():
            return jsonify({"status": "error", "message": "ไม่สามารถเปิดการเชื่อมต่อกับกล้อง MeetUp ได้"}), 500
        
        # ประมวลผลและยิงคำสั่งระดับฮาร์ดแวร์ตามแกนที่กดลาก
        if axis == 'pan':
            cap.set(CAP_PROP_PAN, val)
        elif axis == 'tilt':
            cap.set(CAP_PROP_TILT, val)
        elif axis == 'zoom':
            cap.set(CAP_PROP_ZOOM, val)
            
        # เคลียร์การเชื่อมต่อทันที เพื่อไม่ให้โปรแกรมบล็อกภาพกล้องตัวนี้ไว้
        cap.release() 
        
        return jsonify({"status": "success", "axis": axis, "value_applied": val})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # รันเซิร์ฟเวอร์ที่พอร์ต 5000
    print("--- Local PTZ API Server กำลังทำงานที่พอร์ต 5000 ---")
    app.run(port=5000, debug=True)