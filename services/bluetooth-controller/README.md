# Bluetooth Controller (ESP32-C3 & Python Bridge)

โมดูลรับคำสั่งจาก PC และส่งต่อผ่าน Serial ไปยังบอร์ด ESP32-C3 เพื่อสั่งงานอุปกรณ์บลูทูธภายนอก (เช่น เพิ่ม/ลดเสียง หรือขยับเมาส์บนสมาร์ททีวี)

## โครงสร้าง
- **Python Service (`main.py`)**: รัน Flask Server พอร์ต `5001` เพื่อรับส่งคำสั่งจาก HTTP API ไปยัง Serial พอร์ตของบอร์ด
- **Firmware (`firmware/`)**: โค้ด PlatformIO สำหรับบอร์ด ESP32-C3 ทำหน้าที่เป็น BLE Keyboard/Mouse Combo ไร้สายในชื่อ **"ActbotKung BLE"**

## การติดตั้งและการใช้งานจาก Root
```bash
# สร้าง virtual environment
python -m venv bluetooth-controller/venv

# ติดตั้ง dependencies
bluetooth-controller/venv/Scripts/pip install -r bluetooth-controller/requirements.txt

# รันตัวควบคุมบลูทูธ
bluetooth-controller/venv/Scripts/python bluetooth-controller/main.py
```

## REST API Endpoints
- `GET /api/status` - เช็คสถานะการเชื่อมต่อ Serial พอร์ต
- `POST /api/tv` - ส่งคำสั่งควบคุมทีวี (มัลติมีเดีย)
  - Payload: `{"action": "volume_up" | "volume_down" | "mute" | "click"}`
- `POST /api/send` - ส่งคำสั่งตรงไปยัง ESP32-C3
  - Payload: `{"command": string}` (เช่น `"M 100 0"`)

## ข้อควรระวัง & การแก้ไขปัญหา (Troubleshooting)

### 1. ปัญหาพอร์ต Serial ถูกล็อก (Access is denied / PermissionError)
พอร์ต Serial (เช่น `COM19`) สามารถเชื่อมต่อได้เพียง **1 โปรแกรมในเวลาเดียวกัน**เท่านั้น:
*   หากรัน `main.py` แล้วขึ้นข้อผิดพลาด `Access is denied` แสดงว่ามี **PlatformIO Serial Monitor** หรือโปรเซสอื่นเชื่อมต่อค้างอยู่
*   **วิธีแก้:** ให้ปิดมอนิเตอร์ตัวอื่นก่อน (กด `Ctrl + C` หรือ `Ctrl + ]`) หากยังมีโปรเซสค้างในเบื้องหลัง ให้รันคำสั่งเคลียร์โปรเซสใน Git Bash:
    ```bash
    taskkill //F //IM python.exe
    ```

### 2. บอร์ดรีบูตตัวเองเมื่อเปิด/ปิดการเชื่อมต่อ
*   เนื่องจากบอร์ดมีวงจร Auto-Reset เมื่อมีการเปิดหรือปิดโปรแกรมเชื่อมต่อ Serial (เช่น ปิดเทอร์มินัลด้วย `Ctrl + C`) บอร์ดจะทำการ Reset ตัวเองและเริ่มทำงานใหม่โดยอัตโนมัติ เป็นเรื่องปกติของฮาร์ดแวร์

