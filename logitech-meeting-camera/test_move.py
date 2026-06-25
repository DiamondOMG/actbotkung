import cv2
import time  # <--- เพิ่มตัวนี้เข้าไปด้วยครับ ไม่งั้นพัง
import ctypes
from ctypes import wintypes

# รหัส Property สำหรับ Pan/Tilt/Zoom ของ OpenCV
CAP_PROP_PAN = 1004
CAP_PROP_TILT = 1005

print("กำลังเชื่อมต่อเข้ากับกล้อง...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("❌ เปิดกล้องไม่ได้")
    exit()

try:
    print("➡️ ส่งคำสั่งหมุนขวา (ค่า 1)...")
    # เก็บค่า ret เพื่อดูว่าคำสั่งทำงานสำเร็จไหม (True / False)
    ret_pan = cap.set(CAP_PROP_PAN, 1) 
    print(f"ผลลัพธ์จาก Driver: {ret_pan}")
    
    time.sleep(2)
    
    print("🛑 สั่งหยุดหมุน (ค่า 0)...")
    cap.set(CAP_PROP_PAN, 0)
    time.sleep(1)
    
except Exception as e:
    print(f"เกิดข้อผิดพลาด: {e}")
finally:
    cap.release()
    print("ปิดการเชื่อมต่อกล้องเรียบร้อย")