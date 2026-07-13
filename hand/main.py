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

# Class สำหรับอ่านเฟรมล่าสุดแบบเรียลไทม์เพื่อตัดปัญหาดีเลย์สะสม (Buffer Delay) ของ OpenCV
class LatestFrameReader:
    def __init__(self, src):
        self.cap = cv2.VideoCapture(src)
        self.ret = False
        self.frame = None
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._reader)
        self.thread.daemon = True
        self.thread.start()

    def _reader(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
                    self.ret = True
            else:
                time.sleep(0.01)

    def read(self):
        with self.lock:
            if self.ret:
                return True, self.frame.copy()
            return False, None

    def is_opened(self):
        return self.cap.isOpened()

    def release(self):
        self.running = False
        self.cap.release()

if len(sys.argv) > 1:
    mode = sys.argv[1].lower()
    if mode == 'ble':
        port = sys.argv[2] if len(sys.argv) > 2 else None
        mouse = BLEMouse(port=port)
    elif mode == 'api':
        url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5001"
        mouse = APIMouse(api_url=url)
    else:
        mouse = SoftwareMouse()
else:
    mouse = SoftwareMouse()

# --- [Sensitivity & Smoothing Settings] ---
# ปรับความไว (ยิ่งตัวเลขมาก เมาส์ยิ่งขยับไกล)
sensitivity_x = 2.0  
sensitivity_y = 2.5  

# การหน่วงเมาส์ (ยิ่งมากยิ่งนุ่มแต่จะรู้สึกหน่วงขึ้น)
smoothening = 5
ploc_x, ploc_y = 0, 0
cloc_x, cloc_y = 0, 0
# ------------------------------------------

# ตั้งค่า MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# ตั้งค่าหน้าจอ
screen_width, screen_height = pyautogui.size()
cam_width, cam_height = 640, 480

thumb_was_extended = False
last_click_time = 0

# --- [Pause Toggle] ---
paused = False
thumbs_up_start_time = None
THUMBS_UP_HOLD_SEC = 2.0
TOGGLE_COOLDOWN_SEC = 5.0
toggle_cooldown_until = 0

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

    status = "Searching..."
    dist_val = 0

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            lm = hand_landmarks.landmark
            
            # === ตรวจจับท่าชูนิ้วโป้ง (Pause/Resume) ===
            thumb_tip = lm[4]
            all_landmarks_y = [l.y for l in lm]
            thumb_is_highest = thumb_tip.y <= min(all_landmarks_y) + 0.01
            wrist = lm[0]
            finger_tips = [lm[8], lm[12], lm[16], lm[20]]
            fingers_curled = all(math.hypot(ft.x - wrist.x, ft.y - wrist.y) < 0.25 for ft in finger_tips)
            is_thumbs_up = thumb_is_highest and fingers_curled

            cooldown_left = toggle_cooldown_until - time.time()
            if cooldown_left > 0:
                cv2.putText(img, f"COOLDOWN: {cooldown_left:.1f}s", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 140, 255), 2)
                is_thumbs_up = False

            if is_thumbs_up:
                if thumbs_up_start_time is None: thumbs_up_start_time = time.time()
                held = time.time() - thumbs_up_start_time
                remaining = max(0, THUMBS_UP_HOLD_SEC - held)
                if held >= THUMBS_UP_HOLD_SEC:
                    paused = not paused
                    thumbs_up_start_time = None
                    toggle_cooldown_until = time.time() + TOGGLE_COOLDOWN_SEC
                    print(f">>> {'PAUSED' if paused else 'RESUMED'} <<<")
                    continue
                else:
                    cv2.putText(img, f"THUMBS UP: {remaining:.1f}s", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
            else:
                thumbs_up_start_time = None

            if paused:
                status = "PAUSED"
                color = (128, 128, 128)
                continue

            color = (0, 255, 0)  # สีเริ่มต้น (เขียว)

            # 1. คำนวณพิกัด (ใช้ข้อมือ Wrist - Landmark 0 เป็นจุดควบคุมเมาส์)
            wrist_0 = hand_landmarks.landmark[0]
            target_x = (wrist_0.x - 0.5) * sensitivity_x * screen_width + (screen_width / 2)
            target_y = (wrist_0.y - 0.5) * sensitivity_y * screen_height + (screen_height / 2)

            # 2. Smoothing
            cloc_x = ploc_x + (target_x - ploc_x) / smoothening
            cloc_y = ploc_y + (target_y - ploc_y) / smoothening

            mouse.move_to(cloc_x, cloc_y)
            ploc_x, ploc_y = cloc_x, cloc_y

            # 3. คำนวณระยะห่างระหว่างปลายนิ้วโป้ง (4) กับนิ้วชี้ (8)
            thumb_tip = hand_landmarks.landmark[4]
            index_tip = hand_landmarks.landmark[8]
            thumb_index_dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
            
            # เกณฑ์ระยะห่างมองว่าหนีบกัน (Pinch)
            PINCH_THRESHOLD = 0.05
            is_pinched = thumb_index_dist < PINCH_THRESHOLD

            # Debug: แสดงค่าระยะห่างบนจอ
            dist_val = round(thumb_index_dist, 3)
            cv2.putText(img, f"Pinch Dist: {dist_val:.3f}", (20, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # วาดเส้นและจุด debug ระหว่างนิ้วโป้งกับนิ้วชี้
            pt_thumb = (int(thumb_tip.x * cam_width), int(thumb_tip.y * cam_height))
            pt_index = (int(index_tip.x * cam_width), int(index_tip.y * cam_height))
            
            if is_pinched:
                if not thumb_was_extended: # ใช้เป็น flag was_pinched ค้างไว้
                    mouse.mouse_down()
                    thumb_was_extended = True
                status = "LEFT DRAG (PINCH)"
                color = (0, 0, 255) # แดงตอนคลิกค้าง
            else:
                if thumb_was_extended:
                    mouse.mouse_up()
                    thumb_was_extended = False
                status = "MOVING"
                color = (0, 255, 0) # เขียวตอนขยับปกติ

            cv2.line(img, pt_thumb, pt_index, color, 3)

            # วาดจุดเมาส์สีตามสถานะที่ตำแหน่งข้อมือ (Wrist)
            cv2.circle(img, (int(wrist_0.x * cam_width), int(wrist_0.y * cam_height)), 10, color, cv2.FILLED)

    cv2.putText(img, f"Status: {status}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imshow("Hand Mouse Control (No Boundaries)", img)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'): break

mouse.cleanup()
cap.release()
cv2.destroyAllWindows()