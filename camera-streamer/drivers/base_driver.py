class BaseCameraDriver:
    def __init__(self, cap):
        """
        :param cap: อ็อบเจกต์ cv2.VideoCapture ที่กำลังเปิดใช้งานอยู่
        """
        self.cap = cap
        self.capabilities = []

    def set_pan(self, value: float) -> bool:
        """
        หมุนกล้องในแนวราบ (Pan)
        :param value: ค่าควบคุมองศาหรือทิศทาง
        :return: True หากส่งคำสั่งสำเร็จ, False หากไม่สำเร็จ
        """
        raise NotImplementedError("ต้องอิมพลีเมนต์ set_pan ในคลาสลูก")

    def set_tilt(self, value: float) -> bool:
        """
        ก้ม/เงยกล้อง (Tilt)
        :param value: ค่าควบคุมองศาหรือทิศทาง
        :return: True หากส่งคำสั่งสำเร็จ, False หากไม่สำเร็จ
        """
        raise NotImplementedError("ต้องอิมพลีเมนต์ set_tilt ในคลาสลูก")

    def set_zoom(self, value: float) -> bool:
        """
        ซูมภาพ (Zoom)
        :param value: ค่าระดับการซูม
        :return: True หากส่งคำสั่งสำเร็จ, False หากไม่สำเร็จ
        """
        raise NotImplementedError("ต้องอิมพลีเมนต์ set_zoom ในคลาสลูก")

    def get_capabilities(self) -> list:
        """
        ส่งคืนรายการความสามารถของกล้องที่รองรับ
        :return: รายการ string เช่น ['pan', 'tilt', 'zoom']
        """
        return self.capabilities
