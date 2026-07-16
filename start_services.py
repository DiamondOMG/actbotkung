import asyncio
import os
import sys

# เพิ่มพาธสำหรับการดึงโมดูลใน services
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import services.manage_service as ms

async def monitor_services():
    """คอยตรวจสอบสถานะของบริการย่อยที่รันอยู่เป็นระยะ และแจ้งเตือนหากมีบริการดับกลางคัน"""
    last_status = {}
    services_to_monitor = ["web-speaker", "camera-streamer"]
    
    # หน่วงเวลาเริ่มตรวจเช็คครั้งแรก 5 วินาที
    await asyncio.sleep(5)
    
    while True:
        try:
            for service_name in services_to_monitor:
                status = ms.get_service_status(service_name)
                is_running = status["is_running"]
                
                # หากสถานะเปลี่ยนจาก รันอยู่ -> ดับไป
                if service_name in last_status and last_status[service_name] != is_running:
                    if not is_running:
                        print(f"\n⚠️  [ALERT] บริการ '{service_name}' ดับกะทันหัน! (โปรเซสภายนอกถูกปิดลง)")
                    else:
                        print(f"\nℹ️  [INFO] บริการ '{service_name}' ได้รับการกู้คืนและเปิดรันอีกครั้ง")
                
                # อัปเดตสถานะของบริการ
                last_status[service_name] = is_running
                
            await asyncio.sleep(3)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(3)

async def main():
    print("🚀 กำลังเริ่มต้นเปิดบริการย่อย Jarvis (Jarvis Bootstrap Services)...")
    print("----------------------------------------------------------------")
    print("📋 แผนผังการแบ่ง Port (Port Allocation):")
    print("  🔹 [Port 3000] - web-speaker (Next.js Core Brain UI)")
    print("  🔹 [Port 5000] - camera-streamer (Flask Logitech MeetUp Camera & PTZ)")
    print("  🔹 [Port 5001] - bluetooth-controller (Flask ESP32-C3 TV Remote)")
    print("----------------------------------------------------------------")
    
    # 1. สั่งเปิดเว็บอินเตอร์เฟสหลัก (web-speaker)
    res_web = await ms.start_service("web-speaker")
    print(f"🌐 Core Web Speaker: {res_web}")
    
    # 2. สั่งเปิดบริการกล้อง (camera-streamer)
    res_cam = await ms.start_service("camera-streamer")
    print(f"📸 Camera Streamer: {res_cam}")
    
    print("----------------------------------------------------------------")
    print("🌐 กำลังเปิดเบราว์เซอร์ไปที่ http://localhost:3000...")
    import webbrowser
    webbrowser.open("http://localhost:3000")
    
    print("✅ บริการทั้งหมดถูกเปิดแยกหน้าต่าง Terminal และเริ่มทำงานแล้ว!")
    print("💡 คุณสามารถกด Ctrl+C ในหน้าต่างนี้เพื่อปิดบริการทั้งหมดพร้อมกัน")
    
    # เริ่มการรัน Task ตรวจสอบสถานะบริการเบื้องหลัง
    monitor_task = asyncio.create_task(monitor_services())
    
    # รันลูปค้างไว้เพื่อเฝ้าดูและรองรับการกด Ctrl+C เพื่อล้างโปรเซสเบื้องหลัง
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        # สั่งยกเลิกการตรวจเช็คสถานะเบื้องหลัง
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        # เคลียร์และปิดหน้าต่างเซอร์วิสทั้งหมดที่เปิดไว้เมื่อปิดสคริปต์
        await ms.cleanup_all()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 ปิดระบบและบริการย่อยทั้งหมดสำเร็จ.")


