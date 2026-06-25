import duvc_ctl as duvc
from drivers.base_driver import BaseCameraDriver

class LogitechMeetupDriver(BaseCameraDriver):
    def __init__(self, cap, device_index=0):
        super().__init__(cap)
        self.device_index = device_index
        self.capabilities = ['pan', 'tilt', 'zoom']

    def set_pan(self, value: float) -> bool:
        try:
            # ใช้ duvc_ctl สั่งงานโดยตรงผ่าน DirectShow
            with duvc.CameraController(device_index=self.device_index) as camera_ctrl:
                camera_ctrl.pan = int(value)
            return True
        except Exception as error:
            print(f"LogitechMeetupDriver (duvc) set_pan error: {error}")
            return False

    def set_tilt(self, value: float) -> bool:
        try:
            with duvc.CameraController(device_index=self.device_index) as camera_ctrl:
                camera_ctrl.tilt = int(value)
            return True
        except Exception as error:
            print(f"LogitechMeetupDriver (duvc) set_tilt error: {error}")
            return False

    def set_zoom(self, value: float) -> bool:
        try:
            with duvc.CameraController(device_index=self.device_index) as camera_ctrl:
                camera_ctrl.zoom = int(value)
            return True
        except Exception as error:
            print(f"LogitechMeetupDriver (duvc) set_zoom error: {error}")
            return False
