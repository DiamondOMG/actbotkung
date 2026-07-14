from abc import ABC, abstractmethod

class BaseGestureLogic(ABC):
    def __init__(self, mouse):
        self.mouse = mouse

    @abstractmethod
    def process(self, img, hands_list, screen_width, screen_height, cam_width, cam_height):
        """
        ประมวลผลท่าทางและควบคุมเมาส์
        img: เฟรมภาพ OpenCV
        hands_list: ข้อมูลมือเรียงจากซ้ายไปขวาบนหน้าจอ
        screen_width, screen_height: ขนาดหน้าจอ
        cam_width, cam_height: ขนาดวิดีโอจากกล้อง
        
        ส่งกลับ: (status_text, draw_color) เพื่อวาดข้อมูลลงหน้าจอ
        """
        pass

    def cleanup(self):
        """เรียกใช้เมื่อโปรแกรมหยุดการทำงานเพื่อล้างข้อมูลหรือปล่อยสถานะที่ค้างอยู่"""
        pass
