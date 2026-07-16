'use client';

import { useRef, useState, useCallback, useEffect } from 'react';
import { GoogleGenAI, Modality } from '@google/genai';
import { base64ToFloat32, floatToBase64PCM } from '@/lib/audioConverter';
import instructions from '@/lib/instructions.json';
import { say_hello } from '@/app/actions/say_hello';
import { change_monitor_screen } from '@/app/actions/change_monitor_screen';

const SAMPLE_RATE = 24000;

// Tool handlers - เพิ่ม function ใหม่ได้ที่นี่
const toolHandlers: Record<string, (args: any) => Promise<any>> = {
  say_hello: async () => say_hello(),
  monitor_screen: async (args: { screen_id: string; name: string; sequence_id: string }) => {
    // แปลง screen_id เป็น array ตามที่ action ต้องการ
    return change_monitor_screen([args.screen_id], args.sequence_id, args.name);
  }
};

export type JarvisStatus = 'idle' | 'listening' | 'thinking' | 'speaking';

export function useJarvis() {
  const [active, setActive] = useState(false);
  const [status, setStatus] = useState<JarvisStatus>('idle');
  const [userVolume, setUserVolume] = useState(0);
  const refs = useRef<any>({});
  const speakTimeout = useRef<NodeJS.Timeout | null>(null);
  const inactivityTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastSpokenTimeRef = useRef<number>(0);

  // ค่า timeout (ms) ที่จะรอหลังจาก chunk สุดท้าย ถ้าไม่มี chunk ใหม่มา → ถือว่าจบการพูด
  const SPEAKING_TIMEOUT_MS = 4000; // ปรับได้ 2200–3500 ตามความเหมาะสม

  // ฟังก์ชันรีเซ็ตเวลาสำหรับปิดการทำงานอัตโนมัติ (Inactivity Timeout)
  const resetInactivityTimer = useCallback(() => {
    if (inactivityTimeoutRef.current) {
      clearTimeout(inactivityTimeoutRef.current);
    }
    
    // ตั้งเวลาปิด 15 วินาทีหากไม่มีความเคลื่อนไหว (ทั้งคนเงียบและบอทเงียบ)
    inactivityTimeoutRef.current = setTimeout(() => {
      console.log('💤 Auto closing due to inactivity...');
      if (refs.current.session) {
        refs.current.stream?.getTracks().forEach((t: any) => t.stop());
        refs.current.audioCtx?.close();
        refs.current.session?.close();
      }
      setActive(false);
      setStatus('idle');
      setUserVolume(0);
    }, 15000);
  }, []);

  // เคลียร์ Timeout ตอน Unmount
  useEffect(() => {
    return () => {
      if (inactivityTimeoutRef.current) {
        clearTimeout(inactivityTimeoutRef.current);
      }
    };
  }, []);

  // ส่งข้อความแทนการพูด
  const sendText = useCallback((message: string) => {
    if (!refs.current.session) {
      console.warn('⚠️ Session not active');
      return;
    }
    resetInactivityTimer(); // รีเซ็ตเวลา inactivity เมื่อส่งคำสั่งตัวอักษร
    setStatus('thinking');
    refs.current.session.sendClientContent({
      turns: [{ role: 'user', parts: [{ text: message }] }]
    });
    console.log('📝 Text sent:', message);
  }, [resetInactivityTimer]);

  // ปิด Jarvis (idempotent - ถ้าปิดอยู่แล้วจะไม่ทำอะไร)
  const close = useCallback(() => {
    if (!active) return; // ถ้าปิดอยู่แล้ว ไม่ต้องทำอะไร
    
    if (inactivityTimeoutRef.current) {
      clearTimeout(inactivityTimeoutRef.current);
    }
    refs.current.stream?.getTracks().forEach((t: any) => t.stop());
    refs.current.audioCtx?.close();
    refs.current.session?.close();
    setActive(false);
    setStatus('idle');
    setUserVolume(0);
    if (speakTimeout.current) clearTimeout(speakTimeout.current);
  }, [active]);

  // เปิด Jarvis (idempotent - ถ้าเปิดอยู่แล้วจะไม่ทำอะไร)
  const open = useCallback(async () => {
    if (active) return; // ถ้าเปิดอยู่แล้ว ไม่ต้องทำอะไร

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const audioCtx = new AudioContext({ sampleRate: SAMPLE_RATE });
      const genAI = new GoogleGenAI({ apiKey: process.env.NEXT_PUBLIC_GEMINI_API_KEY! });

      let nextStartTime = 0;

      const session = await genAI.live.connect({
        model: 'gemini-2.5-flash-native-audio-latest',
        config: {
          systemInstruction: { parts: [{ text: instructions.instructions }] },
          responseModalities: [Modality.AUDIO],
          tools: instructions.tools as any,
          speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Puck' } } }
        },
        callbacks: {
          onmessage: async (msg) => {
            // Handle Tool Calls
            const toolCall = msg.toolCall;
            if (toolCall?.functionCalls) {
              setStatus('thinking');
              for (const fc of toolCall.functionCalls) {
                console.log(`🔧 Tool called: ${fc.name}`, fc.args);

                if (!fc.name || !fc.id) continue;

                if (fc.name === 'close_session') {
                  console.log('👋 Closing session via tool call');
                  session.sendToolResponse({
                    functionResponses: [{ id: fc.id, name: fc.name, response: { success: true } }]
                  });
                  stream.getTracks().forEach((t: any) => t.stop());
                  audioCtx.close();
                  session.close();
                  setActive(false);
                  setStatus('idle');
                  return;
                }

                const handler = toolHandlers[fc.name];
                if (handler) {
                  try {
                    const result = await handler(fc.args);
                    console.log(`✅ Tool result:`, result);
                    session.sendToolResponse({
                      functionResponses: [{
                        id: fc.id,
                        name: fc.name,
                        response: result
                      }]
                    });
                  } catch (error) {
                    console.error(`❌ Tool error:`, error);
                    session.sendToolResponse({
                      functionResponses: [{
                        id: fc.id,
                        name: fc.name,
                        response: { error: String(error) }
                      }]
                    });
                  }
                } else {
                  console.warn(`⚠️ Unknown tool: ${fc.name}`);
                }
              }
              return;
            }

            // ────────────────────────────────────────────────
            // Handle audio response (ส่วนที่แก้ไขหลัก)
            // ────────────────────────────────────────────────
            const audioData = msg.serverContent?.modelTurn?.parts?.[0]?.inlineData?.data;
            if (audioData) {
              resetInactivityTimer(); // รีเซ็ตเวลาปิดตัวเมื่อบอทพูด/ส่งข้อมูลมา
              const float32 = base64ToFloat32(audioData);
              const buffer = audioCtx.createBuffer(1, float32.length, SAMPLE_RATE);
              buffer.copyToChannel(float32 as any, 0);

              const source = audioCtx.createBufferSource();
              source.buffer = buffer;
              source.connect(audioCtx.destination);

              const playTime = Math.max(audioCtx.currentTime, nextStartTime);
              source.start(playTime);
              nextStartTime = playTime + buffer.duration;

              // ตั้ง / reset timeout ทุกครั้งที่มี chunk ใหม่
              setStatus('speaking');

              if (speakTimeout.current) {
                clearTimeout(speakTimeout.current);
              }

              speakTimeout.current = setTimeout(() => {
                setStatus('listening');
                console.log('🗣️ No more audio chunks → back to listening');
              }, SPEAKING_TIMEOUT_MS);
            }
          }
        }
      });

      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processor.onaudioprocess = (e) => {
        // 1. ป้องกันการขัดจังหวะ (Interruption Prevention)
        // ถ้า AI กำลังพูดอยู่ (status === 'speaking') จะข้ามการประมวลผลและไม่ส่งเสียงคนพูดไปขัด
        if (status === 'speaking') {
          setUserVolume(0);
          return;
        }

        const inputData = e.inputBuffer.getChannelData(0);
        
        // คำนวณระดับความดังเสียงจากไมค์ (RMS)
        let sum = 0;
        for (let i = 0; i < inputData.length; i++) {
          sum += inputData[i] * inputData[i];
        }
        const rms = Math.sqrt(sum / inputData.length);
        const volume = Math.min(Math.round(rms * 300), 100);

        // 2. ระบบ Noise Gate (ตัวกรองเสียงเบา)
        // กำหนด Threshold ที่ 0.005 (เสียงพูดปกติจะอยู่ราวๆ 0.01 - 0.1)
        const NOISE_GATE_THRESHOLD = 0.005;
        const now = Date.now();
        let isSpeaking = false;

        if (rms >= NOISE_GATE_THRESHOLD) {
          isSpeaking = true;
          lastSpokenTimeRef.current = now;
        } else if (now - lastSpokenTimeRef.current < 800) {
          // หน่วงเวลา Hold Time 800ms ป้องกันเสียงขาดตอนระหว่างเว้นวรรคคำพูด
          isSpeaking = true;
        }

        if (isSpeaking) {
          setUserVolume(volume);
          resetInactivityTimer();
        } else {
          setUserVolume(0);
          return; // ประตูเสียงปิด (เงียบเกินไป) -> ไม่ส่งเสียงไปหา API ประหยัดเน็ตและลดเสียงรบกวน
        }

        try {
          session.sendRealtimeInput({
            media: {
              data: floatToBase64PCM(inputData),
              mimeType: `audio/pcm;rate=${SAMPLE_RATE}`
            }
          });
        } catch (err) {
          console.warn('⚠️ WebSocket disconnected. Stopping microphone processor...');
          processor.disconnect();
          stream.getTracks().forEach((t: any) => t.stop());
          audioCtx.close();
          setActive(false);
          setStatus('idle');
          setUserVolume(0);
        }
      };

      audioCtx.createMediaStreamSource(stream).connect(processor);
      processor.connect(audioCtx.destination);

      refs.current = { stream, audioCtx, session };
      setActive(true);
      setStatus('listening');
      resetInactivityTimer(); // เริ่มจับเวลานับถอยหลังเมื่อระบบเปิดตัว
    } catch (error) {
      console.error('Failed to start Jarvis:', error);
      setActive(false);
      setStatus('idle');
      setUserVolume(0);
    }
  }, [active, resetInactivityTimer]);

  // toggle สำหรับ backward compatibility
  const toggle = useCallback(async () => {
    if (active) {
      close();
    } else {
      await open();
    }
  }, [active, open, close]);

  return { active, toggle, open, close, sendText, status, userVolume };
}