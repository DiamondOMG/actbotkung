'use server';

import { NextRequest, NextResponse } from 'next/server';

// เก็บ clients ที่ subscribe อยู่
const clients = new Set<ReadableStreamDefaultController>();

// POST - รับ trigger จากภายนอก
export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({}));
    const action = body.action || 'toggle';
    const message = body.message || '';

    console.log(`🎯 Trigger received: ${action}`, message ? `- ${message}` : '');

    // ส่ง event ไปยัง clients ทั้งหมด
    const eventData = JSON.stringify({ action, message, timestamp: Date.now() });
    
    clients.forEach((controller) => {
      try {
        controller.enqueue(`data: ${eventData}\n\n`);
      } catch (error) {
        // Client disconnected, remove from set
        clients.delete(controller);
      }
    });

    return NextResponse.json({ 
      success: true, 
      action,
      clientsNotified: clients.size 
    });
  } catch (error) {
    console.error('❌ Trigger error:', error);
    return NextResponse.json({ success: false, error: String(error) }, { status: 500 });
  }
}

// GET - SSE subscription สำหรับ browser
export async function GET() {
  const stream = new ReadableStream({
    start(controller) {
      clients.add(controller);
      console.log(`📡 Client connected. Total: ${clients.size}`);

      // ส่ง heartbeat ทุก 30 วินาที เพื่อ keep connection alive
      const heartbeat = setInterval(() => {
        try {
          controller.enqueue(`: heartbeat\n\n`);
        } catch {
          clearInterval(heartbeat);
          clients.delete(controller);
        }
      }, 30000);

      // Initial connection message
      controller.enqueue(`data: ${JSON.stringify({ action: 'connected' })}\n\n`);
    },
    cancel() {
      console.log(`📴 Client disconnected. Total: ${clients.size - 1}`);
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
