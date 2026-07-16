import asyncio
import os
import sys
import httpx
from google import genai
from google.genai import types

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
    """ฟังก์ชันทำงานภายในเครื่องเพื่อเรียก API สั่งการอุปกรณ์จริง"""
    try:
        async with httpx.AsyncClient() as client:
            if name == "control_ptz":
                url = "http://localhost:5000/api/ptz"
                payload = {
                    "axis": args.get("axis"),
                    "value": args.get("value")
                }
                print(f"📤 กำลังยิง API ไปที่ {url} ด้วย payload {payload}")
                r = await client.post(url, json=payload, timeout=5.0)
                return f"PTZ Action Response: {r.json()}"
                
            elif name == "trigger_web_ui":
                url = "http://localhost:3000/api/trigger"
                payload = {
                    "action": args.get("action"),
                    "message": args.get("message", "")
                }
                print(f"📤 กำลังยิง API ไปที่ {url} ด้วย payload {payload}")
                r = await client.post(url, json=payload, timeout=5.0)
                return f"Web UI Action Response: status code {r.status_code}"
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการรัน Tool {name}: {e}")
        return f"Error: {str(e)}"
    return "Unknown tool"

async def test_live_tools():
    try:
        if not api_key:
            raise ValueError("ไม่พบ GEMINI_API_KEY ใน Environment หรือไฟล์ .env")
        client = genai.Client(api_key=api_key)
        print("🔗 กำลังเชื่อมต่อ WebSocket (Gemini Live API)...")
        
        # กำหนดเครื่องมือ (Tool Declarations) ให้กับ Gemini
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription=types.AudioTranscriptionConfig(),
            system_instruction=types.Content(
                parts=[types.Part.from_text(
                    text="คุณคือผู้ช่วยอัจฉริยะ คุณสามารถสั่งขยับกล้อง PTZ หรือสั่งงานหน้าจอ Web UI ได้ตามความต้องการของผู้ใช้"
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
                                        description="องศาหรือค่าที่ต้องการปรับ (เช่น 10.0 หรือ -10.0)"
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
                        )
                    ]
                )
            ]
        )
        
        async with client.aio.live.connect(model="gemini-2.5-flash-native-audio-latest", config=config) as session:
            print("✅ เชื่อมต่อ WebSocket สำเร็จ!")
            
            # ส่งคำสั่งให้ขยับกล้องเพื่อทดสอบ API
            test_prompt = "กรุณาหันกล้องไปทางซ้าย 15 องศาให้ฉันหน่อย"
            print(f"💬 กำลังส่งคำขอ: '{test_prompt}'")
            
            await session.send_client_content(
                turns=types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=test_prompt)]
                ),
                turn_complete=True
            )
            
            print("⏳ รอการเรียกใช้ Tool และตอบกลับ...")
            
            async for response in session.receive():
                # 1. จัดการการเรียกใช้งาน Tool (Function Call)
                if response.tool_call is not None:
                    function_responses = []
                    for call in response.tool_call.function_calls:
                        name = call.name
                        args = call.args
                        call_id = call.id
                        print(f"\n🔧 Gemini สั่งเรียกใช้ Tool: {name} (Args: {args})")
                        
                        # รันคำสั่งควบคุมอุปกรณ์
                        result = await execute_tool(name, args)
                        
                        # ส่งผลลัพธ์การทำงานกลับไปให้โมเดลประมวลผลต่อ
                        function_responses.append(
                            types.FunctionResponse(
                                name=name,
                                id=call_id,
                                response={"status": "success", "result": result}
                            )
                        )
                    
                    # ส่งผลลัพธ์กลับไปยัง Live Session
                    print("📤 ส่งผลลัพธ์ของเครื่องมือกลับไปยัง Gemini...")
                    await session.send_tool_response(function_responses=function_responses)
                
                # 2. จัดการข้อมูลตอบกลับทั่วไป
                server_content = response.server_content
                if server_content is not None:
                    # แสดงผลคำถอดความเสียงพูด
                    if server_content.output_transcription is not None:
                        text = server_content.output_transcription.text
                        if text:
                            print(f"🗣️ AI พูด (Transcript): {text}")
                            
                    model_turn = server_content.model_turn
                    if model_turn is not None:
                        for part in model_turn.parts:
                            if part.text is not None:
                                print(f"🤖 ความคิด/ข้อความ (Text): {part.text}")
                                
                    if server_content.turn_complete:
                        print("\n🏁 การตอบกลับเสร็จสิ้นอย่างสมบูรณ์ ปิดการเชื่อมต่อ.")
                        return
                        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(test_live_tools())
