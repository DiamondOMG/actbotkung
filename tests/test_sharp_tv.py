import socket
import sys

def probe_port(ip, port, timeout=1.5):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((ip, port))
            return result == 0
    except Exception:
        return False

def main():
    if len(sys.argv) < 2:
        print("วิธีใช้: python test_sharp_tv.py <IP_ของทีวี>")
        sys.exit(1)
        
    ip = sys.argv[1]
    print(f"กำลังสแกนหาช่องทางควบคุมสำหรับ Sharp TV ที่ IP: {ip} ...\n")
    
    ports_to_check = {
        10002: "Sharp AQUOS IP Control (พอร์ตควบคุมดั้งเดิม)",
        5555: "Android TV / Google TV (พอร์ต ADB)",
        8008: "Google Cast / Chromecast (พอร์ตสำหรับแคสต์จอ)",
        8060: "Roku OS / Sharp Roku TV (พอร์ต REST API)",
    }
    
    found_any = False
    for port, description in ports_to_check.items():
        print(f"กำลังเช็คพอร์ต {port} ({description}) ... ", end="", flush=True)
        if probe_port(ip, port):
            print("เปิดอยู่! (FOUND) ✅")
            found_any = True
        else:
            print("ปิด ❌")
            
    if found_any:
        print("\nสรุป: ทีวีเครื่องนี้รองรับการควบคุมผ่านพอร์ตที่แสดงสถานะ 'เปิดอยู่! ✅' ครับ")
    else:
        print("\nสรุป: ไม่พบพอร์ตสำหรับสั่งงาน")
        print("  - กรุณาเช็คว่าคอมกับทีวีต่อ Wi-Fi/LAN วงเดียวกันหรือไม่ (เช่น 192.168.x.x เหมือนกัน)")
        print("  - เช็คว่าเปิดโหมด 'AQUOS Remote Control' หรือ 'IP Control' ในตั้งค่าของทีวีหรือยัง")

if __name__ == "__main__":
    main()
