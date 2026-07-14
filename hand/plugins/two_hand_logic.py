import math
import time
import cv2
from .base_logic import BaseGestureLogic

class TwoHandLogic(BaseGestureLogic):
    def __init__(self, mouse, sensitivity_x=2.0, sensitivity_y=2.5, smoothening=5):
        super().__init__(mouse)
        self.sensitivity_x = sensitivity_x
        self.sensitivity_y = sensitivity_y
        self.smoothening = smoothening
        
        self.ploc_x, self.ploc_y = 0, 0
        self.cloc_x, self.cloc_y = 0, 0
        
        # Click states
        self.left_pressed = False
        self.right_pressed = False
        
        # Debounce histories
        self.index_history = []
        self.middle_history = []
        
        # Tap vs Drag timing states
        self.index_extended_start_time = None
        self.drag_triggered = False
        
        # Pause states
        self.paused = False
        self.toggle_cooldown_until = 0

    def _is_finger_extended(self, lm, mcp_idx, tip_idx):
        """
        วิเคราะห์การเหยียดนิ้วแบบไร้ทิศทางและสเกล:
        1. เทียบอัตราส่วนความยาวของนิ้ว (โคนนิ้วถึงปลายนิ้ว) กับขนาดฝ่ามือ (ข้อมือถึงโคนนิ้วกลาง) เพื่อตรวจการงอ
        2. เช็คทิศทางเวกเตอร์ (ทิศโคนนิ้วไปปลายนิ้ว ต้องชี้พุ่งออกจากข้อมือ)
        """
        p_wrist = lm[0]
        p_mcp = lm[mcp_idx]
        p_tip = lm[tip_idx]
        p_ref = lm[9]  # โคนนิ้วกลาง (MCP) ใช้เป็นตัวชี้วัดขนาดฝ่ามือที่เสถียรที่สุด
        
        # 1. เช็คอัตราส่วนเทียบขนาดฝ่ามือ
        palm_size = math.hypot(p_ref.x - p_wrist.x, p_ref.y - p_wrist.y)
        finger_len = math.hypot(p_tip.x - p_mcp.x, p_tip.y - p_mcp.y)
        if palm_size == 0:
            return False
        len_ratio = finger_len / palm_size
        
        # 2. เช็คทิศทางเวกเตอร์ (ทิศ MCP -> TIP ต้องมีทิศทางเดียวกับ Wrist -> MCP)
        v_hand_x = p_mcp.x - p_wrist.x
        v_hand_y = p_mcp.y - p_wrist.y
        
        v_finger_x = p_tip.x - p_mcp.x
        v_finger_y = p_tip.y - p_mcp.y
        
        dot_prod = v_hand_x * v_finger_x + v_hand_y * v_finger_y
        len_hand = math.hypot(v_hand_x, v_hand_y)
        len_finger = math.hypot(v_finger_x, v_finger_y)
        
        cos_angle = dot_prod / (len_hand * len_finger) if (len_hand * len_finger) > 0 else 0
        
        # นิ้วต้องเหยียดค่อนข้างสุดเทียบกับฝ่ามือ (> 0.65) และชี้พุ่งออกจากข้อมือ (> 0.5 หรือน้อยกว่า 60 องศา)
        return len_ratio > 0.65 and cos_angle > 0.5

    def process(self, img, hands_list, screen_width, screen_height, cam_width, cam_height):
        # === กรองมุมเอียงของมือที่วิเคราะห์ยาก (คว่ำ หรือ หันข้างมากเกินไป) ===
        valid_hands = []
        bad_angle_detected = False
        
        for hand in hands_list:
            lm = hand['landmarks'].landmark
            p_wrist = lm[0]
            p_mcp = lm[9]  # โคนนิ้วกลาง (MCP)
            dx = p_mcp.x - p_wrist.x
            dy = p_wrist.y - p_mcp.y  # กลับทิศทาง Y ของจอภาพให้ขึ้นเป็นบวก
            angle = math.atan2(dy, dx) * 180.0 / math.pi
            
            # มุมตั้งขึ้นปกติคือ 90 องศา ยอมรับช่วงเอนเอียงได้ 40 ถึง 140 องศา
            if 40.0 <= angle <= 140.0:
                valid_hands.append(hand)
            else:
                bad_angle_detected = True
                # วาดวงกลมแดงเตือนที่ข้อมือ
                pt_wrist = (int(p_wrist.x * cam_width), int(p_wrist.y * cam_height))
                cv2.circle(img, pt_wrist, 15, (0, 0, 255), 3)

        if bad_angle_detected:
            cv2.putText(img, "BAD HAND ANGLE DETECTED", (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        hands_list = valid_hands

        if not hands_list:
            self._release_clicks()
            return "Searching...", (0, 255, 0)

        # จำแนกมือซ้ายและขวา
        mouse_hand = None  # มือขวา (คุมเคอร์เซอร์)
        click_hand = None  # มือซ้าย (คุมคลิก)

        if len(hands_list) >= 2:
            # หากเจอ 2 มือ จัดเรียงตามค่า x ของข้อมือ (เรียงซ้ายไปขวา)
            # มือทางซ้ายของหน้าจอ (x น้อยกว่า) คือ มือซ้าย (Click Hand)
            # มือทางขวาของหน้าจอ (x มากกว่า) คือ มือขวา (Mouse Hand)
            click_hand = hands_list[0]
            mouse_hand = hands_list[1]
        else:
            # หากเจอเพียงมือเดียว ใช้ข้อมูล Classification (ที่มีการกลับซ้ายขวาจากการ Mirror)
            # มือขวาทางกายภาพ จะถูกวิเคราะห์เป็น 'Left'
            # มือซ้ายทางกายภาพ จะถูกวิเคราะห์เป็น 'Right'
            hand = hands_list[0]
            if hand['label'] == 'Left':
                mouse_hand = hand
            else:
                click_hand = hand

        # === 1. ตรวจจับการหยุด/เริ่มระบบ (Pause/Resume) ด้วยการ แบมือทั้งสองข้าง โดยทุกปลายนิ้วเหยียดขึ้นข้างบน ===
        if len(hands_list) >= 2:
            def is_hand_open_pointing_up(hand_obj):
                lm = hand_obj['landmarks'].landmark
                
                # เช็คการเหยียดนิ้วโดยใช้ฟังก์ชันร่วมของคลาส
                ext_states = [
                    self._is_finger_extended(lm, 5, 8),    # นิ้วชี้
                    self._is_finger_extended(lm, 9, 12),   # นิ้วกลาง
                    self._is_finger_extended(lm, 13, 16),  # นิ้วนาง
                    self._is_finger_extended(lm, 17, 20)   # นิ้วก้อย
                ]
                
                # ทุกปลายนิ้วต้องชี้เหยียดขึ้นข้างบน (y ของ tip < y ของ pip < y ของ mcp)
                pointing_up = all(lm[tip].y < lm[pip].y < lm[mcp].y for mcp, pip, tip in [(5,6,8), (9,10,12), (13,14,16), (17,18,20)])
                
                return all(ext_states) and pointing_up

            open_0 = is_hand_open_pointing_up(hands_list[0])
            open_1 = is_hand_open_pointing_up(hands_list[1])

            # หากแบมือเหยียดชี้ฟ้าทั้ง 2 ข้างพร้อมกัน จะทำการสลับโหมดหยุด/ทำงาน (Toggle)
            if open_0 and open_1:
                if time.time() > self.toggle_cooldown_until:
                    self.paused = not self.paused
                    self.toggle_cooldown_until = time.time() + 3.0  # คูลดาวน์ 3 วินาทีเพื่อป้องกันการสลับรัวๆ ตามที่ผู้ใช้แจ้ง
                    print(f">>> TOGGLED PAUSE STATE: {'PAUSED' if self.paused else 'RESUMED'} <<<")

        if self.paused:
            self._release_clicks()
            return "PAUSED", (128, 128, 128)

        # === ระบบความปลอดภัยป้องกันลั่น: ต้องเห็นทั้ง 2 มือพร้อมกัน และไม่มีมือใดที่มีมุมเอียงผิดปกติ ===
        if len(hands_list) < 2 or bad_angle_detected:
            self._release_clicks()
            status = "NEED BOTH HANDS" if len(hands_list) < 2 else "BAD HAND ANGLE"
            color = (0, 165, 255)  # สีส้ม/เหลือง สำหรับแจ้งเตือน
            return status, color

        # === 2. โลจิกควบคุมทิศทางเมาส์ (มือขวา) ===
        if mouse_hand:
            lm_m = mouse_hand['landmarks'].landmark
            # ใช้ปลายนิ้วชี้ (Landmark 8) เป็นจุดอ้างอิงเคอร์เซอร์
            index_tip = lm_m[8]
            target_x = (index_tip.x - 0.5) * self.sensitivity_x * screen_width + (screen_width / 2)
            target_y = (index_tip.y - 0.5) * self.sensitivity_y * screen_height + (screen_height / 2)

            # การหน่วงตำแหน่งเมาส์ (Smoothing)
            self.cloc_x = self.ploc_x + (target_x - self.ploc_x) / self.smoothening
            self.cloc_y = self.ploc_y + (target_y - self.ploc_y) / self.smoothening

            self.mouse.move_to(self.cloc_x, self.cloc_y)
            self.ploc_x, self.ploc_y = self.cloc_x, self.cloc_y
            
            # วาดเป้าบนภาพ
            pt_index = (int(index_tip.x * cam_width), int(index_tip.y * cam_height))
            cv2.circle(img, pt_index, 12, (255, 0, 255), 2)

        # === 3. โลจิกการควบคุมปุ่มกด (มือซ้าย) ===
        status = "MOVING"
        color = (0, 255, 0)
        
        # หากตรวจพบมือคลิก และไม่มีมือใดมีมุมบิดเบี้ยว/คว่ำ (Bad Angle)
        if click_hand and not bad_angle_detected:
            lm_c = click_hand['landmarks'].landmark
            
            # เรียกใช้การประเมินการเหยียดนิ้วด้วยอัตราส่วนขนาดฝ่ามือและทิศทางเวกเตอร์ชี้ออก
            raw_index = self._is_finger_extended(lm_c, 5, 8)    # นิ้วชี้: โคน (5), ปลาย (8)
            raw_middle = self._is_finger_extended(lm_c, 9, 12)  # นิ้วกลาง: โคน (9), ปลาย (12)

            # ทำ Debounce เพื่อป้องกันอาการคลิกรัว (ใช้เสียงข้างมากจาก 3 เฟรมล่าสุด)
            self.index_history.append(raw_index)
            if len(self.index_history) > 3:
                self.index_history.pop(0)
            index_extended = self.index_history.count(True) >= 2

            self.middle_history.append(raw_middle)
            if len(self.middle_history) > 3:
                self.middle_history.pop(0)
            middle_extended = self.middle_history.count(True) >= 2
            
            # จำแนกท่าทาง
            # 1. นิ้วชี้ = คลิ๊กซ้าย (แตะสั้น = คลิกเดี่ยว, แตะค้างเกิน 1 วิ = ลาก/กดค้าง)
            if index_extended and not middle_extended:
                self.right_pressed = False
                
                if self.index_extended_start_time is None:
                    self.index_extended_start_time = time.time()
                    self.drag_triggered = False
                
                # หากค้างไว้เกิน 1 วินาที ให้สั่งกดเมาส์ค้าง (เริ่มลาก)
                if not self.drag_triggered and (time.time() - self.index_extended_start_time > 1.0):
                    self.mouse.mouse_down()
                    self.drag_triggered = True
                    self.left_pressed = True
                    print(">>> DRAG START (Held > 1s) <<<")
                
                if self.drag_triggered:
                    status = "LEFT DRAG"
                else:
                    status = "LEFT TAP PENDING"
                color = (0, 0, 255)  # สีแดง
                
            # 2. นิ้วชี้+กลาง = คลิ๊กขวา
            elif index_extended and middle_extended:
                self._release_left_click()
                
                if not self.right_pressed:
                    self.mouse.right_click()
                    self.right_pressed = True
                status = "RIGHT CLICK"
                color = (255, 0, 0)  # สีน้ำเงิน
                
            # 3. นอกเหนือจากนั้น (เช่น กำมือ / ท่าทางอื่น) = ไม่กด
            else:
                self._release_left_click()
                self.right_pressed = False
                status = "MOVING"
                color = (0, 255, 0)  # สีเขียว

            # แสดงจุด Landmark ของมือซ้ายที่สำคัญ
            for pt_idx in [8, 12]:
                pt = (int(lm_c[pt_idx].x * cam_width), int(lm_c[pt_idx].y * cam_height))
                cv2.circle(img, pt, 6, color, cv2.FILLED)
        else:
            # หากตรวจไม่พบมือคลิก ให้ปล่อยปุ่มเมาส์
            self._release_clicks()

        # วาดตำแหน่งจุดเมาส์ที่ปลายนิ้วชี้มือขวา (ถ้าตรวจพบ)
        if mouse_hand:
            lm_m = mouse_hand['landmarks'].landmark
            pt_index = (int(lm_m[8].x * cam_width), int(lm_m[8].y * cam_height))
            cv2.circle(img, pt_index, 10, color, cv2.FILLED)

        return status, color

    def _release_left_click(self):
        """จัดการการปล่อยนิ้วชี้ซ้ายและการคลิกประเภทต่างๆ"""
        if self.index_extended_start_time is not None:
            duration = time.time() - self.index_extended_start_time
            if duration <= 1.0 and not self.drag_triggered:
                # ปล่อยไวกว่า 1 วิ = คลิกซ้ายเดี่ยวๆ
                self.mouse.click()
                print(">>> LEFT CLICK (Short Tap) <<<")
            elif self.left_pressed:
                # ปล่อยเมาส์ที่กดค้างไว้ (ลาก)
                self.mouse.mouse_up()
                self.left_pressed = False
                print(">>> DRAG END <<<")
            self.index_extended_start_time = None
            self.drag_triggered = False

    def _release_clicks(self):
        """ยกเลิกสถานะคลิกทั้งหมด"""
        self._release_left_click()
        self.right_pressed = False

    def cleanup(self):
        self._release_clicks()
