import serial
import math
import time
import sys
import threading
import ctypes

# ปรับปรุงระบบเวลาบน Windows ให้มีความละเอียดระดับ 1ms เพื่อแก้ปัญหา OS Jitter
try:
    winmm = ctypes.WinDLL('winmm')
    winmm.timeBeginPeriod(1)
    print("[OS Timer] Windows timer resolution set to 1ms successfully.")
except Exception as e:
    print(f"[OS Timer] Warning: Could not set Windows timer resolution: {e}")
    winmm = None

# เปลี่ยนเป็นพอร์ต COM ที่ ESP32-S3 เชื่อมต่ออยู่ (เช่น COM22)
PORT = 'COM22'
BAUD_RATE = 115200

try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=0.1)
    print(f"Connected to ESP32-S3 on {PORT}")
    print("Waiting 3 seconds for BLE connection and GATT setup...")
    time.sleep(3)
except Exception as e:
    print(f"Error connecting to Serial: {e}")
    if winmm:
        winmm.timeEndPeriod(1)
    sys.exit(1)

# Thread สำหรับคอยอ่านข้อมูลที่ส่งกลับจาก ESP32-C3/S3
def serial_reader():
    while ser.is_open:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"[ESP32 Output]: {line}")
        except Exception:
            break

reader_thread = threading.Thread(target=serial_reader)
reader_thread.daemon = True
reader_thread.start()

# ตั้งค่าพารามิเตอร์วงกลม
RADIUS = 100       # รัศมีของวงกลม
STEPS = 60         # จำนวนขั้นตอนต่อรอบ (ยิ่งเยอะยิ่งเคลื่อนที่เนียน)
DELAY = 0.025      # 25ms ต่อเฟรม (40Hz)

print("Starting circle movement with High-Resolution Windows Timer. Press Ctrl+C to stop.")

try:
    angle = 0
    # บันทึกพิกัดก่อนหน้าเพื่อคำนวณการเปลี่ยนแปลงสัมพัทธ์ (Relative dx, dy)
    prev_x = RADIUS * math.cos(0)
    prev_y = RADIUS * math.sin(0)

    while True:
        # คำนวณมุมถัดไป (เรเดียน)
        rad = math.radians(angle)
        
        # คำนวณจุดตำแหน่งเป้าหมายบนวงกลม
        curr_x = RADIUS * math.cos(rad)
        curr_y = RADIUS * math.sin(rad)
        
        # หาค่าความต่างสัมพัทธ์ (dx, dy)
        dx = int(curr_x - prev_x)
        dy = int(curr_y - prev_y)
        
        # อัปเดตค่าพิกัดก่อนหน้า
        prev_x = curr_x
        prev_y = curr_y
        
        # ส่งคำสั่งหากมีการเคลื่อนที่จริง
        if dx != 0 or dy != 0:
            cmd = f"M {dx} {dy}\n"
            ser.write(cmd.encode())
            
        angle = (angle + (360 / STEPS)) % 360
        time.sleep(DELAY)

except KeyboardInterrupt:
    print("\nStopped.")
finally:
    ser.close()
    if winmm:
        winmm.timeEndPeriod(1)
        print("[OS Timer] Windows timer resolution restored.")
