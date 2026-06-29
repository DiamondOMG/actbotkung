"""
ทดสอบเชื่อมต่อ Gemini Live API ผ่าน WebSocket อย่างง่าย
ใช้: python test_gemini_live.py
"""
import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("❌ ต้องติดตั้ง websockets ก่อน:")
    print("   pip install websockets")
    sys.exit(1)

API_KEY = "AIzaSyCFB3cJbQjOZmDUn8l6J2KqVcCx8h7Jyzk"
MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"

WS_URL = (
    f"wss://generativelanguage.googleapis.com/ws/"
    f"google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent"
    f"?key={API_KEY}"
)

async def test_live_api():
    print(f"🔌 กำลังเชื่อมต่อ WebSocket ไปยัง Gemini Live API...")
    print(f"   Model: {MODEL}")
    print()

    try:
        async with websockets.connect(WS_URL, additional_headers={}) as ws:
            print("✅ WebSocket เชื่อมต่อสำเร็จ! (101 Switching Protocols)")

            # ส่ง setup message
            setup_msg = {
                "setup": {
                    "model": f"models/{MODEL}",
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {"voiceName": "Puck"}
                            }
                        }
                    },
                    "systemInstruction": {
                        "parts": [{"text": "You are Jarvis. Say hello briefly."}]
                    }
                }
            }

            print("📤 ส่ง setup message...")
            await ws.send(json.dumps(setup_msg))
            print("   ส่งสำเร็จ! รอ response จากเซิร์ฟเวอร์...")

            # รอรับข้อความแรกจากเซิร์ฟเวอร์ (timeout 10 วินาที)
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=10)
                data = json.loads(response)
                print(f"📨 ได้รับ response:")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:500])

                if "setupComplete" in data:
                    print()
                    print("🎉🎉🎉 SETUP COMPLETE! โมเดลพร้อมใช้งาน! 🎉🎉🎉")
                    print()

                    # ทดสอบส่งข้อความ text
                    text_msg = {
                        "clientContent": {
                            "turns": [
                                {"role": "user", "parts": [{"text": "Hello Jarvis"}]}
                            ],
                            "turnComplete": True
                        }
                    }
                    print("📤 ส่งข้อความทดสอบ: 'Hello Jarvis'...")
                    await ws.send(json.dumps(text_msg))

                    # รับ response หลายชิ้น
                    for i in range(5):
                        try:
                            resp = await asyncio.wait_for(ws.recv(), timeout=10)
                            resp_data = json.loads(resp)
                            # แสดงเฉพาะ key หลักๆ
                            keys = list(resp_data.keys())
                            print(f"   📨 Response #{i+1}: keys={keys}")
                            if "serverContent" in resp_data:
                                sc = resp_data["serverContent"]
                                if "modelTurn" in sc:
                                    parts = sc["modelTurn"].get("parts", [])
                                    for p in parts:
                                        if "inlineData" in p:
                                            mime = p["inlineData"].get("mimeType", "?")
                                            data_len = len(p["inlineData"].get("data", ""))
                                            print(f"       🔊 Audio chunk: {mime}, size={data_len}")
                                        if "text" in p:
                                            print(f"       💬 Text: {p['text']}")
                                if sc.get("turnComplete"):
                                    print("   ✅ Turn complete!")
                                    break
                        except asyncio.TimeoutError:
                            print(f"   ⏰ Timeout รอ response #{i+1}")
                            break

                else:
                    print()
                    print("⚠️ ไม่ได้รับ setupComplete - อาจมีปัญหา:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))

            except asyncio.TimeoutError:
                print("❌ Timeout 10 วินาที - ไม่ได้รับ response จากเซิร์ฟเวอร์เลย")

            print()
            print("🔌 ปิดการเชื่อมต่อ...")

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ เชื่อมต่อไม่สำเร็จ! Status: {e.status_code}")
        if e.status_code == 403:
            print("   → API Key ไม่ถูกต้อง หรือไม่มีสิทธิ์")
        elif e.status_code == 404:
            print("   → โมเดลไม่มีอยู่จริง หรือ URL ผิด")
        else:
            print(f"   → {e}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_live_api())
