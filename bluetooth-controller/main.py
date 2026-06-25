import sys
import time
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import serial
import serial.tools.list_ports

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Serial Settings
BAUD_RATE = 115200
ser = None
connected_port = None

def find_esp32_port():
    """ค้นหาพอร์ต COM ที่เป็นของ ESP32-C3 หรือพอร์ตที่ใช้งานได้"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        logging.info(f"พบพอร์ต: {port.device} - {port.description}")
        if "USB Serial" in port.description or "CH340" in port.description or "CP210" in port.description or "UART" in port.description:
            return port.device
    if ports:
        return ports[0].device
    return None

def connect_serial():
    global ser, connected_port
    if ser and ser.is_open:
        return True
        
    port = find_esp32_port()
    if not port:
        logging.error("ไม่พบพอร์ต Serial สำหรับ ESP32-C3")
        return False
        
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=1)
        connected_port = port
        logging.info(f"เชื่อมต่อกับ ESP32-C3 สำเร็จบนพอร์ต {port}")
        return True
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ Serial บนพอร์ต {port}: {e}")
        ser = None
        connected_port = None
        return False

# พยายามเชื่อมต่อเมื่อรันโปรแกรม
connect_serial()

@app.route('/api/status', methods=['GET'])
def get_status():
    is_connected = ser is not None and ser.is_open
    return jsonify({
        "status": "success",
        "serial_connected": is_connected,
        "port": connected_port
    })

@app.route('/api/tv', methods=['POST'])
def tv_control():
    global ser
    if not ser or not ser.is_open:
        if not connect_serial():
            return jsonify({
                "status": "error",
                "message": "บอร์ด ESP32-C3 ไม่ได้เชื่อมต่อกับพอร์ต Serial"
            }), 503
            
    try:
        data = request.json or {}
        action = data.get('action')
        
        if not action:
            return jsonify({
                "status": "error",
                "message": "ไม่พบพารามิเตอร์ action"
            }), 400
            
        payload = f"TV:{action}\n"
        ser.write(payload.encode('utf-8'))
        logging.info(f"ส่งคำสั่ง Serial: {payload.strip()}")
        
        return jsonify({
            "status": "success",
            "sent_command": payload.strip()
        })
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการส่งคำสั่ง: {e}")
        ser = None
        connected_port = None
        return jsonify({
            "status": "error",
            "message": f"ข้อผิดพลาด Serial: {e}"
        }), 500

@app.route('/api/send', methods=['POST'])
def send_raw_command():
    global ser
    if not ser or not ser.is_open:
        if not connect_serial():
            return jsonify({
                "status": "error",
                "message": "บอร์ด ESP32-C3 ไม่ได้เชื่อมต่อกับพอร์ต Serial"
            }), 503
            
    try:
        data = request.json or {}
        command = data.get('command')
        
        if not command:
            return jsonify({
                "status": "error",
                "message": "ไม่พบพารามิเตอร์ command"
            }), 400
            
        payload = f"{command}\n"
        ser.write(payload.encode('utf-8'))
        logging.info(f"ส่งคำสั่งดิบ Serial: {payload.strip()}")
        
        return jsonify({
            "status": "success",
            "sent_command": payload.strip()
        })
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการส่งคำสั่งดิบ: {e}")
        ser = None
        connected_port = None
        return jsonify({
            "status": "error",
            "message": f"ข้อผิดพลาด Serial: {e}"
        }), 500

if __name__ == '__main__':
    logging.info("เริ่มต้นเซิร์ฟเวอร์ Bluetooth Controller...")
    app.run(host='0.0.0.0', port=5001, debug=False)
