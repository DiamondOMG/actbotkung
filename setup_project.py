import os
import sys
import subprocess
import shutil

def run_command(cmd, cwd=None, shell=False):
    print(f"📦 Executing: {' '.join(cmd) if isinstance(cmd, list) else cmd} in {cwd or '.'}")
    try:
        subprocess.run(cmd, cwd=cwd, shell=shell, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ เกิดข้อผิดพลาดในการรันคำสั่ง: {e}")
        return False

def setup_python_service(service_path):
    print(f"\n--- 🐍 กำลังติดตั้ง Python Service: {os.path.basename(service_path)} ---")
    venv_dir = os.path.join(service_path, "venv")
    requirements = os.path.join(service_path, "requirements.txt")
    
    # 1. สร้าง venv หากยังไม่มี
    if not os.path.exists(venv_dir):
        print(f"⚙️ กำลังสร้าง Virtual Environment (venv) ที่ {venv_dir}...")
        if not run_command([sys.executable, "-m", "venv", "venv"], cwd=service_path):
            return False
            
    # 2. ติดตั้งไลบรารีจาก requirements.txt
    pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe") if sys.platform == "win32" else os.path.join(venv_dir, "bin", "pip")
    if os.path.exists(requirements):
        print(f"📥 กำลังติดตั้งไลบรารีจาก requirements.txt...")
        if not run_command([pip_exe, "install", "-r", "requirements.txt"], cwd=service_path):
            return False
    return True

def setup_node_project(project_path):
    print(f"\n--- 🟢 กำลังติดตั้ง Node Project: {os.path.basename(project_path)} ---")
    # ตรวจสอบหา pnpm บนเครื่อง
    has_pnpm = shutil.which("pnpm") is not None
    if has_pnpm:
        print("⚡ พบ pnpm ในระบบ! จะติดตั้ง Dependencies ผ่าน pnpm...")
        return run_command(["pnpm", "install"], cwd=project_path, shell=True)
    else:
        print("⚠️ ไม่พบ pnpm ในระบบ. จะใช้ npm ในการติดตั้งแทน...")
        return run_command(["npm", "install"], cwd=project_path, shell=True)

def main():
    print("🚀 เริ่มการตั้งค่าสภาพแวดล้อมโปรเจกต์ Jarvis (Jarvis Setup Launcher)...")
    print("----------------------------------------------------------------")
    
    project_root = os.path.abspath(os.path.dirname(__file__))
    
    # 1. ติดตั้งไลบรารี Python สำหรับรันตัวสคริปต์หลัก/สคริปต์ทดสอบ
    print("\n--- 🌐 กำลังติดตั้งไลบรารีระดับ Global สำหรับ Python ---")
    global_libs = ["google-genai", "httpx", "groq", "websockets", "python-dotenv"]
    run_command([sys.executable, "-m", "pip", "install"] + global_libs)
    
    # 2. ตั้งค่า Services ย่อยทั้งหมด
    services_dir = os.path.join(project_root, "services")
    if os.path.exists(services_dir):
        for name in os.listdir(services_dir):
            service_path = os.path.join(services_dir, name)
            if os.path.isdir(service_path):
                setup_python_service(service_path)
                
    # 3. ตั้งค่า Next.js Web UI
    web_speaker_path = os.path.join(project_root, "web-speaker")
    if os.path.exists(web_speaker_path):
        setup_node_project(web_speaker_path)
        
    print("\n----------------------------------------------------------------")
    print("✅ สิ้นสุดการติดตั้งและเตรียมสภาพแวดล้อมโปรเจกต์สำเร็จ!")
    print("💡 คุณสามารถรันบริการทั้งหมดทันทีโดยใช้คำสั่ง: python start_services.py")

if __name__ == "__main__":
    main()
