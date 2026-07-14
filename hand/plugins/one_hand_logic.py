import math
import time
import cv2
from .base_logic import BaseGestureLogic

class OneHandLogic(BaseGestureLogic):
    def __init__(self, mouse, sensitivity_x=2.0, sensitivity_y=2.5, smoothening=5):
        super().__init__(mouse)
        self.sensitivity_x = sensitivity_x
        self.sensitivity_y = sensitivity_y
        self.smoothening = smoothening
        
        self.ploc_x, self.ploc_y = 0, 0
        self.cloc_x, self.cloc_y = 0, 0
        self.thumb_was_extended = False
        
        # Pause states
        self.paused = False
        self.thumbs_up_start_time = None
        self.THUMBS_UP_HOLD_SEC = 2.0
        self.TOGGLE_COOLDOWN_SEC = 5.0
        self.toggle_cooldown_until = 0

    def process(self, img, hands_list, screen_width, screen_height, cam_width, cam_height):
        # หากตรวจไม่พบมือใดๆ
        if not hands_list:
            if self.thumb_was_extended:
                self.mouse.mouse_up()
                self.thumb_was_extended = False
            return "Searching...", (0, 255, 0)

        # ใช้มือแรกที่เจอ
        hand = hands_list[0]
        hand_landmarks = hand['landmarks']
        lm = hand_landmarks.landmark

        # === ตรวจจับท่าชูนิ้วโป้ง (Pause/Resume) ===
        thumb_tip = lm[4]
        all_landmarks_y = [l.y for l in lm]
        thumb_is_highest = thumb_tip.y <= min(all_landmarks_y) + 0.01
        wrist = lm[0]
        finger_tips = [lm[8], lm[12], lm[16], lm[20]]
        fingers_curled = all(math.hypot(ft.x - wrist.x, ft.y - wrist.y) < 0.25 for ft in finger_tips)
        is_thumbs_up = thumb_is_highest and fingers_curled

        cooldown_left = self.toggle_cooldown_until - time.time()
        if cooldown_left > 0:
            cv2.putText(img, f"COOLDOWN: {cooldown_left:.1f}s", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 140, 255), 2)
            is_thumbs_up = False

        if is_thumbs_up:
            if self.thumbs_up_start_time is None:
                self.thumbs_up_start_time = time.time()
            held = time.time() - self.thumbs_up_start_time
            remaining = max(0, self.THUMBS_UP_HOLD_SEC - held)
            if held >= self.THUMBS_UP_HOLD_SEC:
                self.paused = not self.paused
                self.thumbs_up_start_time = None
                self.toggle_cooldown_until = time.time() + self.TOGGLE_COOLDOWN_SEC
                print(f">>> {'PAUSED' if self.paused else 'RESUMED'} <<<")
                
                # หากสลับไป Pause ให้ยกเลิกการคลิกซ้าย
                if self.paused and self.thumb_was_extended:
                    self.mouse.mouse_up()
                    self.thumb_was_extended = False
                return "PAUSED" if self.paused else "RESUMED", (128, 128, 128)
            else:
                cv2.putText(img, f"THUMBS UP: {remaining:.1f}s", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
        else:
            self.thumbs_up_start_time = None

        if self.paused:
            return "PAUSED", (128, 128, 128)

        color = (0, 255, 0)  # สีเริ่มต้น (เขียว)

        # 1. คำนวณพิกัด (ใช้ข้อมือ Wrist - Landmark 0 เป็นจุดควบคุมเมาส์)
        wrist_0 = lm[0]
        target_x = (wrist_0.x - 0.5) * self.sensitivity_x * screen_width + (screen_width / 2)
        target_y = (wrist_0.y - 0.5) * self.sensitivity_y * screen_height + (screen_height / 2)

        # 2. Smoothing
        self.cloc_x = self.ploc_x + (target_x - self.ploc_x) / self.smoothening
        self.cloc_y = self.ploc_y + (target_y - self.ploc_y) / self.smoothening

        self.mouse.move_to(self.cloc_x, self.cloc_y)
        self.ploc_x, self.ploc_y = self.cloc_x, self.cloc_y

        # 3. คำนวณระยะห่างระหว่างปลายนิ้วโป้ง (4) กับนิ้วชี้ (8)
        thumb_tip = lm[4]
        index_tip = lm[8]
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
            if not self.thumb_was_extended:
                self.mouse.mouse_down()
                self.thumb_was_extended = True
            status = "LEFT DRAG (PINCH)"
            color = (0, 0, 255)  # แดงตอนคลิกค้าง
        else:
            if self.thumb_was_extended:
                self.mouse.mouse_up()
                self.thumb_was_extended = False
            status = "MOVING"
            color = (0, 255, 0)  # เขียวตอนขยับปกติ

        cv2.line(img, pt_thumb, pt_index, color, 3)

        # วาดจุดเมาส์สีตามสถานะที่ตำแหน่งข้อมือ (Wrist)
        cv2.circle(img, (int(wrist_0.x * cam_width), int(wrist_0.y * cam_height)), 10, color, cv2.FILLED)

        return status, color

    def cleanup(self):
        if self.thumb_was_extended:
            self.mouse.mouse_up()
            self.thumb_was_extended = False
