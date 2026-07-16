import asyncio
import os
import sys
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

async def test_live_connection():
    try:
        if not api_key:
            raise ValueError("ไม่พบ GEMINI_API_KEY ใน Environment หรือไฟล์ .env")
        client = genai.Client(api_key=api_key)
        print("🔗 กำลังเชื่อมต่อ WebSocket...")
        
        # กำหนดคอนฟิกให้ดึงคำถอดความ (Transcript) ของเสียงกลับมาด้วย
        # (หากต้องการรับเฉพาะ Text โดยไม่มีเสียง ให้เปลี่ยน response_modalities เป็น ["TEXT"])
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription=types.AudioTranscriptionConfig()
        )
        
        async with client.aio.live.connect(model="gemini-2.5-flash-native-audio-latest", config=config) as session:
            print("✅ เชื่อมต่อ WebSocket สำเร็จ!")
            print("💬 กำลังส่งข้อความ: 'Hello, testing connection.'")
            
            # ส่งข้อความ Text ไปหาโมเดล
            await session.send_client_content(
                turns=types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="Hello, testing connection.")]
                ),
                turn_complete=True
            )
            
            print("⏳ รอรับข้อมูลตอบกลับจากเซิร์ฟเวอร์...")
            
            # รอรับข้อมูลตอบกลับ
            async for response in session.receive():
                server_content = response.server_content
                if server_content is not None:
                    # แสดงผลข้อความถอดความจากเสียงตอบกลับ (Audio Transcript)
                    if server_content.output_transcription is not None:
                        text = server_content.output_transcription.text
                        if text:
                            print(f"🗣️ AI พูด (Transcript): {text}")
                            
                    model_turn = server_content.model_turn
                    if model_turn is not None:
                        for part in model_turn.parts:
                            if part.text is not None:
                                print(f"🤖 ความคิด/ข้อความ (Text): {part.text}")
                            if part.inline_data is not None:
                                print("🎵 ได้รับข้อมูลเสียงกลับมา (Audio Chunk)")
                                
                    # เมื่อจบเทิร์นตอบกลับของ AI (turn_complete = True) ให้สิ้นสุดการทำงาน
                    if server_content.turn_complete:
                        print("\n🏁 การตอบกลับเสร็จสิ้นอย่างสมบูรณ์ ปิดการเชื่อมต่อ.")
                        return
                        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}", file=sys.stderr)

if __name__ == "__main__":
    # รัน Event Loop สำหรับ asyncio
    asyncio.run(test_live_connection())
