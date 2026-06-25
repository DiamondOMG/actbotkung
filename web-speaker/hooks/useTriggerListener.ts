'use client';

import { useEffect, useRef, useCallback, useState } from 'react';

interface TriggerEvent {
  action: 'toggle' | 'start' | 'stop' | 'sendText' | 'connected' | 'wakeAndGreet';
  message?: string;
  timestamp?: number;
}

interface UseTriggerListenerOptions {
  onToggle: () => void;
  onOpen?: () => void;  // Idempotent open
  onClose?: () => void; // Idempotent close
  onSendText?: (message: string) => void;
  isActive?: boolean;   // ใช้เช็คสถานะก่อน wakeAndGreet
  enabled?: boolean;
}

export function useTriggerListener({
  onToggle,
  onOpen,
  onClose,
  onSendText,
  isActive = false,
  enabled = true
}: UseTriggerListenerOptions) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (!enabled) return;
    
    // ปิด connection เดิมถ้ามี
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    console.log('🔌 Connecting to trigger service...');
    const eventSource = new EventSource('/api/trigger');
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data: TriggerEvent = JSON.parse(event.data);
        console.log('📨 Trigger event received:', data);

        switch (data.action) {
          case 'connected':
            console.log('✅ Connected to trigger service');
            break;
          case 'toggle':
            onToggle();
            break;
          case 'start':
            onOpen?.(); // Idempotent - ถ้าเปิดอยู่แล้วจะไม่ทำอะไร
            break;
          case 'stop':
            onClose?.(); // Idempotent - ถ้าปิดอยู่แล้วจะไม่ทำอะไร
            break;
          case 'sendText':
            if (data.message) {
              onSendText?.(data.message);
            }
            break;
          case 'wakeAndGreet':
            if (data.message) {
              // ใช้ onOpen แทน toggle เพื่อให้ idempotent
              if (!isActive) {
                onOpen?.();
              }
              
              // รอ 1.5 วินาที แล้วส่งข้อความ
              setTimeout(() => {
                onSendText?.(data.message!);
              }, 1500);
            }
            break;
        }
      } catch (error) {
        console.error('❌ Error parsing trigger event:', error);
      }
    };

    eventSource.onerror = () => {
      console.warn('⚠️ Trigger connection lost. Reconnecting in 3s...');
      eventSource.close();
      
      // Reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };
  }, [enabled, onToggle, onOpen, onClose, onSendText, isActive]);

  useEffect(() => {
    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined' || !eventSourceRef.current) return;
    
    const checkStatus = () => {
      setConnected(eventSourceRef.current?.readyState === 1);
    };

    const interval = setInterval(checkStatus, 1000);
    return () => clearInterval(interval);
  }, []);

  return {
    isConnected: connected
  };
}
