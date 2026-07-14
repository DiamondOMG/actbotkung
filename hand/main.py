import cv2
import mediapipe as mp
import pyautogui
pyautogui.FAILSAFE = False
import numpy as np
import math
import time
import sys
import threading
import ctypes

# ปรับระดับความละเอียดของ Windows Timer เป็น 1ms เพื่อความสมูทในการส่งคำสั่ง
try:
    winmm = ctypes.WinDLL('winmm')
    winmm.timeBeginPeriod(1)
except Exception:
    winmm = None

# === เลือก Plugin ตรงนี้ ===
from plugins import SoftwareMouse, BLEMouse, APIMouse
from plugins import OneHandLogic, TwoHandLogic

# Class สำหรับอ่านเฟรมล่าสุดแบบเรียลไทม์เพื่อตัดปัญหาดีเลย์สะสม (Buffer Delay) ของ OpenCV
class LatestFrameReader:
    def __init__(self, src):
        self.src = src
        self.cap = cv2.VideoCapture(src)
        self.ret = False
        self.frame = None
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._reader)
        self.thread.daemon = True
        self.thread.start()

    def _reader(self):
        consecutive_failures = 0
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                consecutive_failures = 0
                with self.lock:
                    self.frame = frame
                    self.ret = True
            else:
                consecutive_failures += 1
                # หากดึงเฟรมล้มเหลวต่อเนื่องเกิน 30 ครั้ง (ประมาณ 1 วินาที)
                # แสดงว่าสตรีมหรือการเชื่อมต่อมีปัญหา ให้ทำ Auto-reconnect
                if consecutive_failures >= 30:
                    print("[Camera] Stream disconnected. Reconnecting...")
                    self.cap.release()
                    time.sleep(1.0) # รอ 1 วินาทีก่อนสร้างการเชื่อมต่อใหม่
                    self.cap = cv2.VideoCapture(self.src)
                    consecutive_failures = 0
                time.sleep(0.01)

    def read(self):
        with self.lock:
            if self.ret:
                self.ret = False  # เคลียร์สถานะเมื่อหยิบเฟรมไปใช้แล้ว ป้องกันการดึงเฟรมเดิมซ้ำ (แก้จอค้าง)
                return True, self.frame.copy()
            return False, None

    def is_opened(self):
        return self.cap.isOpened()

    def release(self):
        self.running = False
        self.cap.release()

# --- [Sensitivity & Smoothing Settings] ---
sensitivity_x = 2.0  
sensitivity_y = 2.5  
smoothening = 5
# ------------------------------------------

# เลือกโหมดและ Logic ผ่าน Command Line Arguments หรือใช้ดีฟอลต์ที่นี่
# ตัวอย่าง: python main.py [device: software|ble|api] [logic: one|two] [port/url]
mouse_mode = 'software'
logic_mode = 'one'
extra_arg = None

if len(sys.argv) > 1:
    mouse_mode = sys.argv[1].lower()
if len(sys.argv) > 2:
    logic_mode = sys.argv[2].lower()
if len(sys.argv) > 3:
    extra_arg = sys.argv[3]

# ตั้งค่าอุปกรณ์เมาส์ปลายทาง (Output Device)
if mouse_mode == 'ble':
    mouse = BLEMouse(port=extra_arg)
elif mouse_mode == 'api':
    mouse = APIMouse(api_url=extra_arg or "http://localhost:5001")
else:
    mouse = SoftwareMouse()

# ตั้งค่า Logic การทำเมาส์มือ
if logic_mode == 'two':
    print("[Logic] Using TwoHandLogic (มือขวาคุมทิศทาง, มือซ้ายคุมคลิก)")
    logic = TwoHandLogic(mouse, sensitivity_x=sensitivity_x, sensitivity_y=sensitivity_y, smoothening=smoothening)
else:
    print("[Logic] Using OneHandLogic (มือเดียวแบบเดิม)")
    logic = OneHandLogic(mouse, sensitivity_x=sensitivity_x, sensitivity_y=sensitivity_y, smoothening=smoothening)

# ตั้งค่า MediaPipe (ปรับ max_num_hands เป็น 2 เพื่อให้รองรับสองมือ)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# ตั้งค่าหน้าจอ
screen_width, screen_height = pyautogui.size()
cam_width, cam_height = 640, 480

cap = LatestFrameReader("http://localhost:5000/api/video_feed")

print("Starting Hand Mouse (Full Camera Mode)... Press 'q' to quit.")

while cap.is_opened():
    success, img = cap.read()
    if not success:
        time.sleep(0.01)
        continue

    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    hands_list = []
    if results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # ดึงประเภทของมือ (Left / Right) และพิกัด landmarks
            lbl = results.multi_handedness[idx].classification[0].label
            hands_list.append({
                'landmarks': hand_landmarks,
                'label': lbl
            })
        
        # จัดเรียงลำดับมือจากซ้ายไปขวาบนหน้าจอ เพื่อแยกระหว่างมือซ้ายและมือขวาจริงทางกายภาพ
        hands_list.sort(key=lambda h: h['landmarks'].landmark[0].x)

    # ประมวลผลตรรกะท่าทาง
    status, color = logic.process(img, hands_list, screen_width, screen_height, cam_width, cam_height)

    cv2.putText(img, f"Status: {status}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imshow("Hand Mouse Control (No Boundaries)", img)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'): break

logic.cleanup()
mouse.cleanup()
cap.release()
cv2.destroyAllWindows()