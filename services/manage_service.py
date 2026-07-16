import os
import sys
import subprocess
import asyncio
import httpx

# Dictionary เก็บออบเจกต์ Subprocess ของแต่ละ Service
running_processes = {}

# รายละเอียดและคู่มือการใช้งานของแต่ละบริการ (Service Manuals)
SERVICES_INFO = {
    "camera-streamer": {
        "port": 5000,
        "url": "http://localhost:5000",
        "description": "บริการควบคุมกล้องหลัก Logitech MeetUp และการดึงสตรีมภาพ",
        "cmd_name": "main.py"
    },
    "bluetooth-controller": {
        "port": 5001,
        "url": "http://localhost:5001",
        "description": "บริการเชื่อมต่อบอร์ด ESP32-C3 เพื่อส่งคำสั่ง Bluetooth ควบคุมทีวี",
        "cmd_name": "main.py"
    },
    "hand-detection": {
        "port": None,
        "url": None,
        "description": "ระบบตรวจจับจุดเชื่อมต่อของมือด้วย MediaPipe เพื่อจำลองเมาส์บน OS",
        "cmd_name": "main.py api"
    },
    "web-speaker": {
        "port": 3000,
        "url": "http://localhost:3000",
        "description": "Core Brain Web UI พัฒนาด้วย Next.js สำหรับประสานงานหลักและรับคำสั่งเว็บ",
        "cmd_name": "pnpm dev"
    }
}

def get_project_root():
    """หาที่อยู่โฟลเดอร์ Root ของโปรเจกต์"""
    # สมมติว่าไฟล์นี้อยู่ที่ root/services/manage_service.py
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_service_manual(service_name: str) -> str:
    """ส่งคืนคู่มือการใช้งานแบบละเอียดของบริการนั้นๆ โดยอ่านจากไฟล์ใน system-prompts"""
    if service_name not in SERVICES_INFO:
        return f"Error: ไม่พบข้อมูลบริการสำหรับ '{service_name}'"
        
    project_root = get_project_root()
    # แปลงขีดกลางเป็นขีดล่างสำหรับชื่อไฟล์คู่มือ เช่น camera-streamer -> manual_camera_streamer.md
    safe_name = service_name.replace('-', '_')
    manual_path = os.path.join(project_root, "system-prompts", f"manual_{safe_name}.md")
    
    try:
        if os.path.exists(manual_path):
            with open(manual_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        else:
            return f"Error: ไม่พบไฟล์คู่มือ {manual_path}"
    except Exception as e:
        return f"Error (อ่านไฟล์คู่มือไม่สำเร็จ): {str(e)}"

def get_service_status(service_name: str) -> dict:
    """เช็คสถานะการทำงานของบริการ"""
    global running_processes
    info = SERVICES_INFO.get(service_name, {})
    is_running = service_name in running_processes and running_processes[service_name].poll() is None
    pid = running_processes[service_name].pid if is_running else None
    
    return {
        "service_name": service_name,
        "is_running": is_running,
        "pid": pid,
        "port": info.get("port"),
        "url": info.get("url"),
        "description": info.get("description")
    }

def list_services() -> list:
    """แสดงรายการบริการทั้งหมดพร้อมสถานะปัจจุบัน"""
    services_list = []
    for name in SERVICES_INFO:
        services_list.append(get_service_status(name))
    return services_list

async def start_service(service_name: str) -> str:
    """สั่งเปิดบริการแบบรันเบื้องหลัง (Background Subprocess)"""
    global running_processes
    
    if service_name not in SERVICES_INFO:
        return f"Error: ไม่พบข้อมูลบริการ '{service_name}'"
        
    status = get_service_status(service_name)
    if status["is_running"]:
        return f"บริการ '{service_name}' กำลังรันอยู่แล้ว (PID: {status['pid']})"
        
    project_root = get_project_root()
    
    # กำหนดรายละเอียดตัวแปรโปรแกรมของแต่ละฝั่ง
    configs = {
        "camera-streamer": {
            "cmd": [
                os.path.join(project_root, "services/camera-streamer/venv/Scripts/python.exe"),
                os.path.join(project_root, "services/camera-streamer/main.py")
            ],
            "cwd": os.path.join(project_root, "services/camera-streamer")
        },
        "bluetooth-controller": {
            "cmd": [
                os.path.join(project_root, "services/bluetooth-controller/venv/Scripts/python.exe"),
                os.path.join(project_root, "services/bluetooth-controller/main.py")
            ],
            "cwd": os.path.join(project_root, "services/bluetooth-controller")
        },
        "hand-detection": {
            "cmd": [
                os.path.join(project_root, "services/hand-detection/venv/Scripts/python.exe"),
                os.path.join(project_root, "services/hand-detection/main.py"),
                "api"
            ],
            "cwd": os.path.join(project_root, "services/hand-detection")
        },
        "web-speaker": {
            # ใช้ pnpm dev ในการรัน
            "cmd": ["pnpm", "dev"],
            "cwd": os.path.join(project_root, "web-speaker"),
            "shell": True # รันผ่าน shell สำหรับคำสั่ง pnpm บน Windows
        }
    }
    
    cfg = configs.get(service_name)
    if not cfg:
        return f"Error: ไม่พบคอนฟิกเริ่มต้นสำหรับ '{service_name}'"
        
    try:
        print(f"[Router Manager] กำลังสั่งเปิดบริการ '{service_name}' ใน Background...")
        
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NEW_CONSOLE
            
        proc = subprocess.Popen(
            cfg["cmd"],
            cwd=cfg["cwd"],
            shell=cfg.get("shell", False),
            creationflags=creationflags
        )
        running_processes[service_name] = proc
        
        # หน่วงเวลาสั้นๆ รอให้ตัวเซิร์ฟเวอร์เปิดพอร์ตสำเร็จ
        await asyncio.sleep(2.0)
        
        # ตรวจสอบว่าโปรเซสสิ้นสุดลงกลางคันหรือไม่ (เช่น เปิดกล้องไม่ได้แล้ว exit(1))
        exit_code = proc.poll()
        if exit_code is not None:
            del running_processes[service_name]
            return f"Failed to start: process exited with code {exit_code} (โปรเซสหยุดทำงานหลังเริ่มรัน)"
            
        return f"Successfully started '{service_name}' (PID: {proc.pid})"
        
    except Exception as e:
        return f"Failed to start '{service_name}': {str(e)}"

async def stop_service(service_name: str) -> str:
    """สั่งปิดบริการเบื้องหลัง"""
    global running_processes
    
    if service_name not in running_processes:
        return f"บริการ '{service_name}' ไม่ได้กำลังรันอยู่"
        
    proc = running_processes[service_name]
    try:
        print(f"[Router Manager] กำลังส่งสัญญาณปิดบริการ '{service_name}'...")
        proc.terminate()
        # รอให้เคลียร์ทรัพยากรเสร็จ 3 วินาที
        for _ in range(30):
            if proc.poll() is not None:
                break
            await asyncio.sleep(0.1)
            
        if proc.poll() is None:
            print(f"[Router Manager] บริการ '{service_name}' ไม่ตอบสนอง ทำการยิงโปรเซสทิ้ง...")
            proc.kill()
            proc.wait()
            
        del running_processes[service_name]
        return f"Successfully stopped '{service_name}'"
    except Exception as e:
        return f"Failed to stop '{service_name}': {str(e)}"

async def cleanup_all():
    """ปิดบริการเบื้องหลังทั้งหมดเมื่อจบการทำงาน"""
    global running_processes
    if not running_processes:
        return
        
    print("\n[Router Manager] เคลียร์ระบบ: กำลังปิดบริการย่อยทั้งหมดที่เปิดทิ้งไว้...")
    for name, proc in list(running_processes.items()):
        if proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=2.0)
                print(f"🛑 ปิดบริการ {name} สำเร็จ")
            except Exception:
                proc.kill()
    running_processes.clear()
