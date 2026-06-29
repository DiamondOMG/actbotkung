import urllib.request
import json
import pyautogui
import queue
import threading
import time
from .base_mouse import BaseMouse

class APIMouse(BaseMouse):
    """ส่งคำสั่งเมาส์ผ่าน HTTP API ไปยังเซิร์ฟเวอร์บลูทูธ (Flask) แบบ Asynchronous (ไม่บล็อกเฟรม)"""

    def __init__(self, api_url="http://localhost:5001"):
        self.api_url = api_url.rstrip('/')
        self.screen_width, self.screen_height = pyautogui.size()
        self.prev_x = self.screen_width / 2
        self.prev_y = self.screen_height / 2
        
        # ตั้งค่า Queue และ Thread สำหรับส่งคำสั่งเบื้องหลัง
        self.queue = queue.Queue()
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        print(f"[Plugin] APIMouse (Async) loaded pointing to {self.api_url}")

    def _worker(self):
        """Thread ดึงคำสั่งจาก Queue ไปส่งผ่าน HTTP เพื่อไม่ให้บล็อกการทำงานหลัก"""
        while self.running:
            try:
                command = self.queue.get(timeout=0.05)
                self._send_command_sync(command)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[Plugin] Worker exception: {e}")

    def _send_command(self, command):
        """รับคำสั่งมาใส่ Queue (ถ้าคิวขยับเมาส์เริ่มยาวเกิน 2 คำสั่งจะข้ามคำสั่งเก่าเพื่อไม่ให้แลกสะสม)"""
        if command.startswith("M ") and self.queue.qsize() > 2:
            return  # ข้ามเพื่อรักษาความสดใหม่ของพิกัดเมาส์ (Real-time)
        self.queue.put(command)

    def _send_command_sync(self, command):
        """ยิง HTTP Request จริงแบบ Synchronous"""
        url = f"{self.api_url}/api/send"
        data = json.dumps({"command": command}).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=0.1) as response:
                pass
        except Exception as e:
            # แจ้งเตือนข้อผิดพลาดเบาๆ
            print(f"[Plugin] APIMouse Send Error: {e}")

    def move_to(self, x, y):
        # แปลง Absolute -> Relative (dx, dy)
        dx = int(x - self.prev_x)
        dy = int(y - self.prev_y)
        self.prev_x = x
        self.prev_y = y
        self._send_command(f"M {dx} {dy}")

    def click(self):
        self._send_command("C L")

    def double_click(self):
        self._send_command("C L")
        self._send_command("C L")

    def right_click(self):
        self._send_command("C R")

    def mouse_down(self):
        self._send_command("P L")

    def mouse_up(self):
        self._send_command("R L")

    def scroll(self, amount):
        scaled = max(-10, min(10, amount // 5)) if abs(amount) > 5 else amount
        self._send_command(f"S {scaled}")

    def cleanup(self):
        self.running = False
        # เคลียร์คำสั่งในคิว
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except queue.Empty:
                break
        print("[Plugin] APIMouse worker stopped.")
