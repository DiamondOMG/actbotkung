import asyncio
import os
import sys
import httpx
from google import genai
from google.genai import types

# เพิ่มพาธของ root โปรเจกต์เพื่อให้ import โมดูลในโฟลเดอร์ services ได้
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import services.manage_service as ms

def get_api_key():
    # ดึง API Key จาก Environment
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("NEXT_PUBLIC_GEMINI_API_KEY")
    if key:
        return key
    # อ่านจากไฟล์ .env ย้อนขึ้นไป 1 ระดับ
    try:
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.env'))
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith("NEXT_PUBLIC_GEMINI_API_KEY="):
                        return line.strip().split("=", 1)[1].strip()
                    elif line.strip().startswith("GEMINI_API_KEY="):
                        return line.strip().split("=", 1)[1].strip()
    except Exception:
        pass
    return None

api_key = get_api_key()

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

async def receive_responses(session):
    """ฟังก์ชันรองรับข้อมูลตอบกลับและการเรียกใช้งานเครื่องมือจาก Gemini"""
    async for response in session.receive():
        # 1. จัดการการเรียกใช้งาน Tool (Function Call)
        if response.tool_call is not None:
            function_responses = []
            for call in response.tool_call.function_calls:
                name = call.name
                args = call.args
                call_id = call.id
                print(f"\n🔧 Gemini สั่งเรียกใช้ Tool: {name} (Args: {args})")
                
                # รันคำสั่งจริง
                result = await execute_tool(name, args)
                
                # ส่งผลลัพธ์กลับ
                function_responses.append(
                    types.FunctionResponse(
                        name=name,
                        id=call_id,
                        response={"status": "success", "result": result}
                    )
                )
            
            print("📤 ส่งผลลัพธ์ของเครื่องมือกลับไปยัง Gemini...")
            await session.send_tool_response(function_responses=function_responses)
            
        # 2. จัดการข้อความทั่วไป
        server_content = response.server_content
        if server_content is not None:
            if server_content.output_transcription is not None:
                text = server_content.output_transcription.text
                if text:
                    print(f"🗣️ AI พูด (Transcript): {text}")
                    
            model_turn = server_content.model_turn
            if model_turn is not None:
                for part in model_turn.parts:
                    if part.text is not None:
                        print(f"🤖 ความคิด/ข้อความ (Text): {part.text}")

async def send_user_input(session):
    """ฟังก์ชันวนลูปรับ input จากคีย์บอร์ดของผู้ใช้เพื่อส่งให้ Gemini"""
    loop = asyncio.get_running_loop()
    while True:
        try:
            user_msg = await loop.run_in_executor(None, input, "\n💬 พิมพ์คำสั่ง (หรือพิมพ์ 'exit' เพื่อออก): ")
            if user_msg.strip().lower() == 'exit':
                print("👋 กำลังปิดเซสชัน...")
                break
            if user_msg.strip():
                await session.send_client_content(
                    turns=types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=user_msg)]
                    ),
                    turn_complete=True
                )
                await asyncio.sleep(0.5) # ป้องกันการขัดจังหวะทันที
        except (KeyboardInterrupt, EOFError):
            break
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการส่งข้อความ: {e}")
            break

async def test_live_tools():
    try:
        if not api_key:
            raise ValueError("ไม่พบ GEMINI_API_KEY ใน Environment หรือไฟล์ .env")
        client = genai.Client(api_key=api_key)
        print("🔗 กำลังเชื่อมต่อ WebSocket (Gemini Live API)...")
        
        # กำหนดคอนฟิกของ Live Session
        # หมายเหตุ: ใช้ gemini-2.0-flash-exp เพื่อความเสถียรสูงสุดในการใช้ Tool Calling ควบคู่กับเสียงพูด
        config = types.LiveConnectConfig(
            response_modalities=["TEXT"],
            system_instruction=types.Content(
                parts=[types.Part.from_text(
                    text=(
                        "คุณคือ Jarvis สมองส่วนควบคุมเสียงเรียลไทม์ (Live Speech Brain) "
                        "หน้าที่ของคุณคือรับฟังคำสั่งผู้ใช้ ควบคุมกล้อง PTZ หรือปรับแต่ง Web UI และจัดการบริการย่อย\n\n"
                        "ข้อมูลสถาปัตยกรรมและกฎการใช้ระบบ:\n"
                        "1. คุณเป็นเราเตอร์ควบคุมบริการต่างๆ หากต้องการทราบว่าระบบของคุณมีบริการอะไรบ้างและพร้อมใช้หรือไม่ ให้เรียกใช้ `list_services()`\n"
                        "2. เมื่อคุณเรียกใช้บริการ/เครื่องมือใดๆ เช่น control_ptz แล้วเกิดข้อผิดพลาดในการเชื่อมต่อ (Connection Refused/Failed) "
                        "แสดงว่าบริการนั้นปิดอยู่ ให้คุณเรียกใช้เครื่องมือ `manage_service` เพื่อเปิดใช้งานมันขึ้นมาก่อน (action='start') จากนั้นจึงส่งคำสั่งเดิมอีกครั้ง\n"
                        "3. หากคุณต้องการทราบรายละเอียดการใช้งานพอร์ต, endpoints หรือคู่มือการควบคุมบริการใดๆ อย่างละเอียด ให้เรียกใช้ `get_service_manual(service_name)` เพื่ออ่านคู่มือบริการนั้น\n"
                        "4. ตอบกลับผู้ใช้สั้นๆ และกระชับในระหว่างดำเนินการย่อย"
                    )
                )]
            ),
            tools=[
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name="control_ptz",
                            description="ควบคุมการขยับกล้อง Logitech MeetUp (pan, tilt, zoom)",
                            parameters=types.Schema(
                                type="OBJECT",
                                properties={
                                    "axis": types.Schema(
                                        type="STRING",
                                        enum=["pan", "tilt", "zoom"],
                                        description="แกนควบคุมที่ต้องการปรับ"
                                    ),
                                    "value": types.Schema(
                                        type="NUMBER",
                                        description="องศาหรือค่าที่ต้องการปรับ (เช่น 15.0 หรือ -15.0)"
                                    )
                                },
                                required=["axis", "value"]
                            )
                        ),
                        types.FunctionDeclaration(
                            name="trigger_web_ui",
                            description="ส่งคำสั่งควบคุมหน้าเว็บหลัก (เช่น toggle, start, stop, wakeAndGreet)",
                            parameters=types.Schema(
                                type="OBJECT",
                                properties={
                                    "action": types.Schema(
                                        type="STRING",
                                        enum=["toggle", "start", "stop", "sendText", "wakeAndGreet"],
                                        description="คำสั่งดำเนินการ"
                                    ),
                                    "message": types.Schema(
                                        type="STRING",
                                        description="ข้อความที่ต้องการส่งไปหน้าจอ"
                                    )
                                },
                                required=["action"]
                            )
                        ),
                        types.FunctionDeclaration(
                            name="manage_service",
                            description="จัดการสถานะการทำงานของบริการย่อยเบื้องหลัง (เช่น camera-streamer, bluetooth-controller, hand-detection)",
                            parameters=types.Schema(
                                type="OBJECT",
                                properties={
                                    "service_name": types.Schema(
                                        type="STRING",
                                        enum=["camera-streamer", "bluetooth-controller", "hand-detection"],
                                        description="ชื่อบริการที่ต้องการจัดการ"
                                    ),
                                    "action": types.Schema(
                                        type="STRING",
                                        enum=["start", "stop", "status"],
                                        description="คำสั่งดำเนินการ"
                                    )
                                },
                                required=["service_name", "action"]
                            )
                        ),
                        types.FunctionDeclaration(
                            name="get_service_manual",
                            description="ดึงคู่มือการใช้งานและ endpoints อย่างละเอียดของบริการย่อย เพื่อนำไปอ้างอิงวิธีการเรียกใช้งาน",
                            parameters=types.Schema(
                                type="OBJECT",
                                properties={
                                    "service_name": types.Schema(
                                        type="STRING",
                                        enum=["camera-streamer", "bluetooth-controller", "hand-detection", "web-speaker"],
                                        description="ชื่อบริการที่ต้องการขอดึงคู่มือ"
                                    )
                                },
                                required=["service_name"]
                            )
                        ),
                        types.FunctionDeclaration(
                            name="list_services",
                            description="แสดงรายชื่อบริการย่อยทั้งหมดในระบบและสถานะการรันปัจจุบันเพื่อตรวจสอบความพร้อมใช้งาน",
                            parameters=types.Schema(
                                type="OBJECT",
                                properties={}
                            )
                        )
                    ]
                )
            ]
        )
        
        # ใช้โมเดล gemini-2.5-flash-native-audio-latest เพื่อรองรับ WebSocket
        async with client.aio.live.connect(model="gemini-2.5-flash-native-audio-latest", config=config) as session:
            print("✅ เชื่อมต่อ WebSocket สำเร็จ!")
            print("💡 พิมพ์คุยกับ Jarvis ได้เลย เช่น 'ขอคู่มือกล้องหน่อย', 'ขยับกล้อง', หรือ 'รันเซิร์ฟเวอร์กล้องให้หน่อย' (พิมพ์ exit เพื่อออก)")
            
            # รันการรับส่งข้อมูลพร้อมๆ กันแบบ Non-blocking
            receive_task = asyncio.create_task(receive_responses(session))
            input_task = asyncio.create_task(send_user_input(session))
            
            await input_task
            
            # ปิดการรับข้อมูลหลังจากผู้ใช้ออกจากโปรแกรม
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass
                
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}", file=sys.stderr)
    finally:
        await ms.cleanup_all()

if __name__ == "__main__":
    try:
        asyncio.run(test_live_tools())
    except KeyboardInterrupt:
        print("\n👋 ปิดโปรแกรมทดสอบ.")
