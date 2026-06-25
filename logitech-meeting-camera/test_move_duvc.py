import cv2
import duvc_ctl as duvc
import time

print("กำลังเริ่มสตรีมกล้องด้วย OpenCV...")
# เชื่อมต่อกล้องผ่าน OpenCV ด้วย DirectShow
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("❌ ไม่สามารถเปิดกล้องผ่าน OpenCV ได้")
    exit()

try:
    print("กำลังเชื่อมต่อตัวควบคุม UVC...")
    with duvc.CameraController(device_index=0) as cam:
        print("เชื่อมต่อสำเร็จ!")
        
        current_pan = cam.pan
        print(f"ค่า Pan ปัจจุบัน: {current_pan}")
        
        # สั่งหมุนกล้องไปขวา
        target_pan = 15
        print(f"➡️ กำลังสั่งหมุน Pan ไปที่: {target_pan} ...")
        cam.pan = target_pan
        
        # แสดงหน้าต่างและสตรีมภาพเป็นเวลา 3 วินาที
        print("กำลังแสดงวิดีโอสดในขณะที่กล้องหมุน (3 วินาที)...")
        start_time = time.time()
        while time.time() - start_time < 3:
            ret, frame = cap.read()
            if ret:
                # แสดงหน้าต่างวิดีโอ
                cv2.imshow("Logitech MeetUp PTZ Test", frame)
            cv2.waitKey(10)  # ยิงคำสั่งอัปเดต GUI หน้าต่าง OpenCV
            
        # สั่งรีเซ็ตกลับมาจุดกึ่งกลาง
        print("🛑 กำลังรีเซ็ตกล้องกลับจุดกึ่งกลาง...")
        cam.center_camera()
        
        # สตรีมภาพต่ออีก 2 วินาทีเพื่อดูขากลับ
        start_time = time.time()
        while time.time() - start_time < 2:
            ret, frame = cap.read()
            if ret:
                cv2.imshow("Logitech MeetUp PTZ Test", frame)
            cv2.waitKey(10)
            
        print("เสร็จสิ้นการทดสอบ")
        
except Exception as e:
    print(f"เกิดข้อผิดพลาดในการควบคุม: {e}")
finally:
    cap.release()
    cv2.destroyAllWindows()
    print("ปิดการเชื่อมต่อกล้องและปิดหน้าต่างเรียบร้อย")
