import asyncio
import os
import sys
import json
import httpx
from groq import Groq

# เพิ่มพาธของ root โปรเจกต์เพื่อให้ import โมดูลในโฟลเดอร์ services ได้
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import services.manage_service as ms

def get_env_var(name):
    # ดึงค่าตัวแปรจาก Environment หรืออ่านไฟล์ .env ตรงๆ
    val = os.environ.get(name)
    if val:
        return val
    try:
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.env'))
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith(f"{name}="):
                        return line.strip().split("=", 1)[1].strip()
    except Exception:
        pass
    return None

groq_api_key = get_env_var("GROQ_API_KEY")

async def execute_tool(name: str, args: dict) -> str:
    """ฟังก์ชันทำงานภายในเครื่องเพื่อเรียก API หรือสั่งการผ่าน Router Manager (ms)"""
    try:
        if name == "manage_service":
            service_name = args.get("service_name")
            action = args.get("action")
            
            if action == "start":
                return await ms.start_service(service_name)
            elif action == "stop":
                return await ms.stop_service(service_name)
            elif action == "status":
                status = ms.get_service_status(service_name)
                return f"Service {service_name} status: is_running={status['is_running']}, PID={status['pid']}"
                
        elif name == "get_service_manual":
            service_name = args.get("service_name")
            return ms.get_service_manual(service_name)
            
        elif name == "list_services":
            services = ms.list_services()
            result = []
            for s in services:
                result.append(f"- {s['service_name']}: is_running={s['is_running']}, port={s['port']}, desc={s['description']}")
            return "\n".join(result)
            
        elif name == "control_ptz":
            url = "http://localhost:5000/api/ptz"
            payload = {
                "axis": args.get("axis"),
                "value": args.get("value")
            }
            print(f"📤 [API Call] กำลังยิง API ไปที่ {url} ด้วย payload {payload}")
            async with httpx.AsyncClient() as client:
                r = await client.post(url, json=payload, timeout=5.0)
                return f"PTZ Action Response: {r.json()}"
                
        elif name == "trigger_web_ui":
            url = "http://localhost:3000/api/trigger"
            payload = {
                "action": args.get("action"),
                "message": args.get("message", "")
            }
            print(f"📤 [API Call] กำลังยิง API ไปที่ {url} ด้วย payload {payload}")
            async with httpx.AsyncClient() as client:
                r = await client.post(url, json=payload, timeout=5.0)
                return f"Web UI Action Response: status code {r.status_code}"
                
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการรัน Tool {name}: {e}")
        return f"Error (โปรเซสหรือพอร์ตอาจจะปิดอยู่): {str(e)}"
    return "Unknown tool"

# การลงทะเบียนโครงสร้างเครื่องมือสำหรับ Qwen (OpenAI Format)
tools = [
    {
        "type": "function",
        "function": {
            "name": "control_ptz",
            "description": "ควบคุมการขยับกล้อง Logitech MeetUp (pan, tilt, zoom)",
            "parameters": {
                "type": "object",
                "properties": {
                    "axis": {
                        "type": "string",
                        "enum": ["pan", "tilt", "zoom"],
                        "description": "แกนควบคุมที่ต้องการปรับ"
                    },
                    "value": {
                        "type": "number",
                        "description": "องศาหรือค่าที่ต้องการปรับ (เช่น 15.0 หรือ -15.0)"
                    }
                },
                "required": ["axis", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_web_ui",
            "description": "ส่งคำสั่งควบคุมหน้าเว็บหลัก (เช่น toggle, start, stop, wakeAndGreet)",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["toggle", "start", "stop", "sendText", "wakeAndGreet"],
                        "description": "คำสั่งดำเนินการ"
                    },
                    "message": {
                        "type": "string",
                        "description": "ข้อความที่ต้องการส่งไปหน้าจอ"
                    }
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_service",
            "description": "จัดการสถานะการทำงานของบริการย่อยเบื้องหลัง (เช่น camera-streamer, bluetooth-controller, hand-detection)",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "enum": ["camera-streamer", "bluetooth-controller", "hand-detection"],
                        "description": "ชื่อบริการที่ต้องการจัดการ"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["start", "stop", "status"],
                        "description": "คำสั่งดำเนินการ"
                    }
                },
                "required": ["service_name", "action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_service_manual",
            "description": "ดึงคู่มือการใช้งานและ endpoints อย่างละเอียดของบริการย่อย เพื่อนำไปอ้างอิงวิธีการเรียกใช้งาน",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "enum": ["camera-streamer", "bluetooth-controller", "hand-detection", "web-speaker"],
                        "description": "ชื่อบริการที่ต้องการขอดึงคู่มือ"
                    }
                },
                "required": ["service_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_services",
            "description": "แสดงรายชื่อบริการย่อยทั้งหมดในระบบและสถานะการรันปัจจุบันเพื่อตรวจสอบความพร้อมใช้งาน",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

SYSTEM_INSTRUCTION = (
    "คุณคือ Jarvis สมองส่วนหลังบ้านวิเคราะห์คำสั่ง (Orchestrator Brain/Qwen) "
    "หน้าที่ของคุณคือรับฟังคำสั่งผู้ใช้ ควบคุมกล้อง PTZ หรือปรับแต่ง Web UI และจัดการบริการย่อย\n\n"
    "ข้อมูลสถาปัตยกรรมและกฎการใช้ระบบ:\n"
    "1. คุณเป็นเราเตอร์ควบคุมบริการต่างๆ หากต้องการทราบว่าระบบของคุณมีบริการอะไรบ้างและพร้อมใช้หรือไม่ ให้เรียกใช้ `list_services`\n"
    "2. เมื่อคุณเรียกใช้บริการ/เครื่องมือใดๆ เช่น control_ptz แล้วเกิดข้อผิดพลาดในการเชื่อมต่อ (Connection Refused/Failed) "
    "แสดงว่าบริการนั้นปิดอยู่ ให้คุณเรียกใช้เครื่องมือ `manage_service` เพื่อเปิดใช้งานมันขึ้นมาก่อน (action='start') จากนั้นจึงส่งคำสั่งเดิมอีกครั้ง\n"
    "3. หากคุณต้องการทราบรายละเอียดการใช้งานพอร์ต, endpoints หรือคู่มือการควบคุมบริการใดๆ อย่างละเอียด ให้เรียกใช้ `get_service_manual` เพื่ออ่านคู่มือบริการนั้น\n"
    "4. ทำงานแบบฉลาดและอัตโนมัติ หากบริการปิดอยู่ให้จัดการเปิดตัวเองโดยไม่ต้องรอถามซ้ำ\n"
    "5. ตอบกลับผู้ใช้ภาษาไทยสั้นๆ กระชับ และเป็นธรรมชาติ"
)

async def main():
    if not groq_api_key:
        print("❌ ไม่พบ GROQ_API_KEY ในไฟล์ .env")
        sys.exit(1)
        
    client = Groq(api_key=groq_api_key)
    print("✅ เชื่อมต่อกับ Groq API (Qwen Model) สำเร็จ!")
    print("💡 พิมพ์คุยกับ Qwen ได้เลย เช่น 'หันกล้องไปทางซ้าย 10 องศา', 'ขอดูคู่มือของกล้อง', 'เช็คสถานะเซอร์วิส' (พิมพ์ exit เพื่อออก)")
    
    # เก็บประวัติการคุยเพื่อให้รักษา Context ได้
    conversation_history = [
        {"role": "system", "content": SYSTEM_INSTRUCTION}
    ]
    
    while True:
        try:
            user_msg = input("\n💬 พิมพ์คำสั่ง: ")
            if user_msg.strip().lower() == 'exit':
                print("👋 กำลังปิดโปรแกรม...")
                break
                
            if not user_msg.strip():
                continue
                
            conversation_history.append({"role": "user", "content": user_msg})
            
            # ลูปสำหรับรัน Tool Call (วนลูปได้สูงสุด 5 ครั้งเพื่อตอบสนองต่อผลลัพธ์ของเครื่องมือย่อย)
            for step in range(5):
                print("⏳ Qwen กำลังคิดวิเคราะห์...", end="\r")
                response = client.chat.completions.create(
                    model="qwen-2.5-coder-32b",
                    messages=conversation_history,
                    tools=tools,
                    tool_choice="auto"
                )
                
                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls
                
                # เช็คว่า Qwen ต้องการเรียกใช้ Tool หรือไม่
                if tool_calls:
                    # ใส่ข้อความแจ้งเครื่องมือกลับเข้าไปในประวัติ
                    conversation_history.append(response_message)
                    
                    for tool_call in tool_calls:
                        name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)
                        call_id = tool_call.id
                        
                        print(f"\n🔧 Qwen สั่งเรียกใช้ Tool: {name} (Args: {args})")
                        
                        # รันคำสั่งจริงในเครื่องคอมพิวเตอร์
                        result = await execute_tool(name, args)
                        
                        # บันทึกผลลัพธ์ลงประวัติเพื่อให้โมเดลนำไปตัดสินใจต่อ
                        conversation_history.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "name": name,
                            "content": result
                        })
                    # วนลูปรอบถัดไปส่งให้ Qwen พิจารณาผลลัพธ์
                    continue
                else:
                    # หากไม่มีการเรียกใช้ Tool แสดงว่าได้คำตอบสุดท้ายแล้ว
                    answer = response_message.content
                    print(f"\n🤖 Qwen: {answer}")
                    # ใส่คำตอบลงประวัติเพื่อการสนทนาต่อเนื่อง
                    conversation_history.append({"role": "assistant", "content": answer})
                    break
                    
        except KeyboardInterrupt:
            print("\n👋 ปิดโปรแกรมทดสอบ.")
            break
        except Exception as e:
            print(f"\n❌ เกิดข้อผิดพลาด: {e}")
            break
            
    # ปิดบริการย่อยทั้งหมดที่เปิดขึ้นมาระหว่างเทส
    await ms.cleanup_all()

if __name__ == "__main__":
    asyncio.run(main())
