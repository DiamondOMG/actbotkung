'use client';

import { useJarvis } from '@/hooks/useJarvis';
import { useTriggerListener } from '@/hooks/useTriggerListener';

export default function Page() {
  const { active, toggle, open, close, sendText, status } = useJarvis();

  // Subscribe to external triggers
  useTriggerListener({
    onToggle: toggle,
    onOpen: open,     // Idempotent - ยิงซ้ำกี่ครั้งก็ไม่ปิด
    onClose: close,   // Idempotent - ยิงซ้ำกี่ครั้งก็ไม่เปิด
    onSendText: sendText,
    isActive: active,
    enabled: true,
  });

  const statusLabel = {
    idle: 'STANDBY',
    listening: 'LISTENING',
    thinking: 'ANALYZING',
    speaking: 'SPEAKING',
  }[status];

  return (
    <div className="w-screen h-screen bg-black flex items-center justify-center overflow-hidden">
      {/* Frame จำลองมือถือ (ถ้ารันบนจอคอม) */}
      <div className="relative w-full h-full md:w-[450px] md:h-[800px] border-0 md:border-2 md:border-stone-900 rounded-none md:rounded-3xl bg-black flex flex-col items-center justify-center shadow-2xl overflow-hidden">
        {/* Visualizer Area */}
        <div className="flex-1 flex items-center justify-center w-full relative">
          {/* Background Glow (Orange with enhanced effects) */}
          {active && (
            <div
              className={[
                'absolute inset-0 pointer-events-none blur-[120px] opacity-80',
                status === 'speaking'
                  ? 'bg-orange-500/20 animate-pulse-fast'
                  : status === 'thinking'
                  ? 'bg-orange-500/15 animate-glow'
                  : 'bg-orange-900/15 animate-pulse-slow',
              ].join(' ')}
            />
          )}

          {/* Enhanced Scanline Overlay with glitch effect */}
          <div className="scanlines mix-blend-overlay opacity-25 animate-glitch-subtle" />

          {/* Remove SYSTEM OFFLINE for pure black idle */}
          {/* FUTURISTIC CORE - Larger and more intricate */}
          {active && (
            <div className="relative w-[400px] h-[400px] flex items-center justify-center">
              {/* Outer aura with multi-layer gradients */}
              <div
                className={[
                  'absolute inset-0 rounded-full blur-3xl opacity-80',
                  status === 'speaking'
                    ? 'animate-jarvisA'
                    : status === 'thinking'
                    ? 'animate-jarvisB'
                    : status === 'listening'
                    ? 'animate-jarvisC'
                    : 'animate-jarvisD',
                ].join(' ')}
              />
              <div className="absolute inset-[-20px] rounded-full blur-xl opacity-50 bg-gradient-radial from-orange-400/20 to-transparent" />

              {/* Enhanced Orbiting particles - more orbs with trails */}
              <div className="absolute inset-0 pointer-events-none">
                <div className={`orb orb-1 ${status} with-trail`} />
                <div className={`orb orb-2 ${status} with-trail`} />
                <div className={`orb orb-3 ${status} with-trail`} />
                <div className={`orb orb-4 ${status} with-trail`} />
              </div>

              {/* Rotating rings - added more rings with varying speeds */}
              <div className="absolute inset-0 rounded-full ring ring-a" />
              <div className="absolute inset-[16px] rounded-full ring ring-b" />
              <div className="absolute inset-[38px] rounded-full ring ring-c" />
              <div className="absolute inset-[60px] rounded-full ring ring-d" />

              {/* HUD ticks - added more layers */}
              <div className="absolute inset-[10px] rounded-full hud-ticks" />
              <div className="absolute inset-[54px] rounded-full hud-ticks hud-ticks-soft" />
              <div className="absolute inset-[80px] rounded-full hud-ticks hud-ticks-faint" />

              {/* Core lens - with added holographic effect */}
              <div className="absolute inset-[84px] rounded-full core-lens">
                <div className="absolute inset-0 rounded-full core-shine" />
                <div
                  className={[
                    'absolute inset-[10px] rounded-full core-inner',
                    status === 'speaking'
                      ? 'core-speaking'
                      : status === 'thinking'
                      ? 'core-thinking'
                      : status === 'listening'
                      ? 'core-listening'
                      : 'core-idle',
                  ].join(' ')}
                />
                {/* Enhanced waveform bars - more bars, dynamic height */}
                <div className={`absolute inset-0 flex items-center justify-center gap-[4px] waveform ${status}`}>
                  {Array.from({ length: 12 }).map((_, i) => (
                    <div key={i} className={`bar bar-${i + 1}`} />
                  ))}
                </div>
              </div>

              {/* Enhanced Crosshair + subtle lines with glow */}
              <div className="absolute w-[140%] h-[1px] bg-gradient-to-r from-transparent via-orange-500/30 to-transparent top-1/2 -translate-y-1/2 glow-line" />
              <div className="absolute h-[140%] w-[1px] bg-gradient-to-b from-transparent via-orange-500/30 to-transparent left-1/2 -translate-x-1/2 glow-line" />

              {/* Status chip - with futuristic border and glow */}
              <div className="absolute -bottom-4 px-4 py-1.5 rounded-full border border-orange-500/20 bg-black/50 backdrop-blur-lg shadow-glow">
                <div className="flex items-center gap-2">
                  <span className={`status-dot ${status}`} />
                  <span className="text-[11px] text-orange-200/70 font-mono tracking-[0.25em]">
                    {statusLabel}
                  </span>
                </div>
              </div>

              {/* Added holographic data streams */}
              <div className="absolute inset-0 holographic-streams">
                <div className="stream stream-1" />
                <div className="stream stream-2" />
              </div>
            </div>
          )}
        </div>

        {/* Hidden Button (Bottom Right) - kept the same */}
        <button
          onClick={toggle}
          className="absolute bottom-8 right-8 w-14 h-14 rounded-full bg-stone-900/40 hover:bg-stone-800/80 active:bg-stone-700 backdrop-blur-sm transition-all cursor-pointer flex items-center justify-center group border border-white/5"
          aria-label="Toggle Jarvis"
        >
          <div
            className={`w-2 h-2 rounded-full transition-all duration-500 ${
              active ? 'bg-orange-500 shadow-[0_0_8px_orange]' : 'bg-red-900/50'
            }`}
          />
        </button>

        {/* Remove Debug State text for cleaner look */}
        {/* <div className="absolute bottom-4 left-4 text-[10px] text-white/5 font-mono pointer-events-none">
          {status.toUpperCase()}
        </div> */}

        {/* Component-scoped styles - enhanced for more wow */}
        <style jsx>{`
          /* Enhanced scanlines with glitch */
          .scanlines {
            position: absolute;
            inset: 0;
            pointer-events: none;
            background: repeating-linear-gradient(
              to bottom,
              rgba(255, 255, 255, 0.08),
              rgba(255, 255, 255, 0.08) 1px,
              rgba(0, 0, 0, 0) 3px,
              rgba(0, 0, 0, 0) 6px
            );
          }
          @keyframes glitch-subtle {
            0% { transform: translate(0, 0); opacity: 0.25; }
            98% { transform: translate(0, 0); opacity: 0.25; }
            99% { transform: translate(1px, 0); opacity: 0.3; }
            100% { transform: translate(0, 0); opacity: 0.25; }
          }
          .animate-glitch-subtle {
            animation: glitch-subtle 5s infinite;
          }

          /* ======= AURA ANIMS - faster and more intense ======= */
          @keyframes jarvisA {
            0% { transform: scale(0.95) rotate(0deg); filter: blur(40px); opacity: 0.7; }
            50% { transform: scale(1.05) rotate(180deg); filter: blur(50px); opacity: 1; }
            100% { transform: scale(0.95) rotate(360deg); filter: blur(40px); opacity: 0.7; }
          }
          @keyframes jarvisB {
            0% { transform: scale(0.97) rotate(0deg); opacity: 0.6; }
            50% { transform: scale(1.03) rotate(180deg); opacity: 0.85; }
            100% { transform: scale(0.97) rotate(360deg); opacity: 0.6; }
          }
          @keyframes jarvisC {
            0% { transform: scale(0.99) rotate(0deg); opacity: 0.5; }
            50% { transform: scale(1.02) rotate(180deg); opacity: 0.7; }
            100% { transform: scale(0.99) rotate(360deg); opacity: 0.5; }
          }
          @keyframes jarvisD {
            0% { transform: scale(0.99); opacity: 0.4; }
            50% { transform: scale(1.01); opacity: 0.5; }
            100% { transform: scale(0.99); opacity: 0.4; }
          }
          .animate-jarvisA {
            background: radial-gradient(
                circle at 25% 25%,
                rgba(255, 140, 0, 0.35),
                rgba(255, 90, 0, 0.12) 40%,
                rgba(0, 0, 0, 0) 65%
              ),
              radial-gradient(
                circle at 75% 70%,
                rgba(255, 200, 120, 0.22),
                rgba(0, 0, 0, 0) 55%
              ),
              radial-gradient(
                circle at 50% 50%,
                rgba(255, 100, 0, 0.15),
                rgba(0, 0, 0, 0) 70%
              );
            animation: jarvisA 1.8s linear infinite;
          }
          .animate-jarvisB {
            background: radial-gradient(
                circle at 30% 30%,
                rgba(255, 160, 60, 0.28),
                rgba(0, 0, 0, 0) 60%
              ),
              radial-gradient(
                circle at 75% 65%,
                rgba(255, 110, 0, 0.15),
                rgba(0, 0, 0, 0) 58%
              );
            animation: jarvisB 2.4s linear infinite;
          }
          .animate-jarvisC {
            background: radial-gradient(
                circle at 35% 35%,
                rgba(255, 170, 80, 0.24),
                rgba(0, 0, 0, 0) 60%
              ),
              radial-gradient(
                circle at 75% 70%,
                rgba(255, 120, 0, 0.12),
                rgba(0, 0, 0, 0) 58%
              );
            animation: jarvisC 3.2s linear infinite;
          }
          .animate-jarvisD {
            background: radial-gradient(
              circle at 50% 50%,
              rgba(255, 130, 20, 0.18),
              rgba(0, 0, 0, 0) 60%
            );
            animation: jarvisD 3.4s ease-in-out infinite;
          }

          /* New glow animations */
          @keyframes pulse-fast {
            0% { opacity: 0.2; }
            50% { opacity: 0.4; }
            100% { opacity: 0.2; }
          }
          @keyframes glow {
            0% { filter: brightness(1); }
            50% { filter: brightness(1.2); }
            100% { filter: brightness(1); }
          }
          @keyframes pulse-slow {
            0% { opacity: 0.15; }
            50% { opacity: 0.3; }
            100% { opacity: 0.15; }
          }
          .animate-pulse-fast { animation: pulse-fast 1s infinite; }
          .animate-glow { animation: glow 2s infinite; }
          .animate-pulse-slow { animation: pulse-slow 4s infinite; }

          /* ======= RINGS - added fourth ring ======= */
          .ring {
            border: 1px solid rgba(255, 140, 0, 0.22);
            box-shadow: inset 0 0 25px rgba(255, 140, 0, 0.1);
            mask-image: radial-gradient(circle, black 65%, transparent 66%);
          }

          @keyframes spinSlow {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          @keyframes spinReverse {
            from { transform: rotate(360deg); }
            to { transform: rotate(0deg); }
          }
          .ring-a {
            animation: spinSlow 6s linear infinite;
            border-color: rgba(255, 170, 60, 0.22);
          }
          .ring-b {
            animation: spinReverse 4.5s linear infinite;
            border-color: rgba(255, 120, 0, 0.2);
          }
          .ring-c {
            animation: spinSlow 3.2s linear infinite;
            border-color: rgba(255, 210, 120, 0.16);
          }
          .ring-d {
            animation: spinReverse 5.5s linear infinite;
            border-color: rgba(255, 140, 0, 0.18);
          }

          /* ======= HUD TICKS - added faint layer ======= */
          .hud-ticks {
            border: 1px solid rgba(255, 140, 0, 0.15);
            box-shadow: inset 0 0 20px rgba(255, 140, 0, 0.06);
            background: conic-gradient(
              from 0deg,
              rgba(255, 140, 0, 0.25),
              rgba(0, 0, 0, 0) 7%,
              rgba(255, 140, 0, 0.18) 9%,
              rgba(0, 0, 0, 0) 16%,
              rgba(255, 140, 0, 0.25) 18%,
              rgba(0, 0, 0, 0) 25%,
              rgba(255, 140, 0, 0.18) 27%,
              rgba(0, 0, 0, 0) 34%,
              rgba(255, 140, 0, 0.25) 36%,
              rgba(0, 0, 0, 0) 43%,
              rgba(255, 140, 0, 0.18) 45%,
              rgba(0, 0, 0, 0) 52%,
              rgba(255, 140, 0, 0.25) 54%,
              rgba(0, 0, 0, 0) 61%,
              rgba(255, 140, 0, 0.18) 63%,
              rgba(0, 0, 0, 0) 70%,
              rgba(255, 140, 0, 0.25) 72%,
              rgba(0, 0, 0, 0) 79%,
              rgba(255, 140, 0, 0.18) 81%,
              rgba(0, 0, 0, 0) 88%,
              rgba(255, 140, 0, 0.25) 90%,
              rgba(0, 0, 0, 0) 97%
            );
            opacity: 0.6;
          }
          .hud-ticks-soft {
            opacity: 0.3;
            filter: blur(0.3px);
          }
          .hud-ticks-faint {
            opacity: 0.15;
            filter: blur(0.5px);
          }

          /* ======= CORE ======= */
          .core-lens {
            border: 1px solid rgba(255, 140, 0, 0.18);
            background: radial-gradient(
              circle at 50% 35%,
              rgba(255, 170, 80, 0.12),
              rgba(0, 0, 0, 0) 60%
            );
            box-shadow: inset 0 0 35px rgba(255, 140, 0, 0.08);
            overflow: hidden;
          }
          .core-shine {
            background: radial-gradient(
              circle at 30% 25%,
              rgba(255, 220, 160, 0.18),
              rgba(0, 0, 0, 0) 45%
            );
            filter: blur(0.3px);
          }
          .core-inner {
            background: radial-gradient(
              circle at 50% 50%,
              rgba(255, 140, 0, 0.28),
              rgba(0, 0, 0, 0) 60%
            );
            filter: saturate(1.4);
            transition: transform 300ms ease, opacity 300ms ease;
          }

          @keyframes corePulse {
            0% { transform: scale(0.98); opacity: 0.75; }
            50% { transform: scale(1.06); opacity: 1; }
            100% { transform: scale(0.98); opacity: 0.75; }
          }
          @keyframes coreScan {
            0% { transform: scale(0.98) rotate(0deg); opacity: 0.75; }
            50% { transform: scale(1.04) rotate(180deg); opacity: 1; }
            100% { transform: scale(0.98) rotate(360deg); opacity: 0.75; }
          }
          @keyframes coreTalk {
            0% { transform: scale(0.98) rotate(0deg); opacity: 0.9; }
            50% { transform: scale(1.08) rotate(180deg); opacity: 1; }
            100% { transform: scale(0.98) rotate(360deg); opacity: 0.9; }
          }

          .core-idle {
            opacity: 0.6;
          }
          .core-listening {
            opacity: 0.8;
            animation: corePulse 1.8s ease-in-out infinite;
          }
          .core-thinking {
            opacity: 0.95;
            animation: coreScan 1.2s linear infinite;
          }
          .core-speaking {
            opacity: 1;
            animation: coreTalk 0.9s linear infinite;
          }

          /* ======= STATUS DOT ======= */
          .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 999px;
            box-shadow: 0 0 14px rgba(255, 140, 0, 0.25);
            background: rgba(255, 120, 0, 0.5);
            transition: opacity 250ms ease, transform 250ms ease;
          }
          .status-dot.speaking {
            background: rgba(255, 140, 0, 1);
            box-shadow: 0 0 20px rgba(255, 140, 0, 0.6);
            transform: scale(1.15);
          }
          .status-dot.thinking {
            background: rgba(255, 140, 0, 0.8);
            box-shadow: 0 0 18px rgba(255, 140, 0, 0.4);
          }
          .status-dot.listening {
            background: rgba(255, 140, 0, 0.6);
            box-shadow: 0 0 16px rgba(255, 140, 0, 0.3);
          }
          .status-dot.idle {
            opacity: 0.4;
          }
          .shadow-glow {
            box-shadow: 0 0 10px rgba(255, 140, 0, 0.2);
          }

          /* ======= ORBS - added fourth orb and trails ======= */
          .orb {
            position: absolute;
            width: 12px;
            height: 12px;
            border-radius: 999px;
            background: rgba(255, 140, 0, 0.7);
            box-shadow: 0 0 20px rgba(255, 140, 0, 0.45);
            filter: blur(0.3px);
          }
          .with-trail::after {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 999px;
            background: rgba(255, 140, 0, 0.3);
            filter: blur(5px);
            transform: scale(1.5);
            opacity: 0.5;
          }
          @keyframes orbit1 {
            from { transform: rotate(0deg) translateX(190px) rotate(0deg); opacity: 0.4; }
            50% { opacity: 1; }
            to { transform: rotate(360deg) translateX(190px) rotate(-360deg); opacity: 0.4; }
          }
          @keyframes orbit2 {
            from { transform: rotate(0deg) translateX(165px) rotate(0deg); opacity: 0.3; }
            50% { opacity: 0.8; }
            to { transform: rotate(-360deg) translateX(165px) rotate(360deg); opacity: 0.3; }
          }
          @keyframes orbit3 {
            from { transform: rotate(0deg) translateX(140px) rotate(0deg); opacity: 0.25; }
            50% { opacity: 0.7; }
            to { transform: rotate(360deg) translateX(140px) rotate(-360deg); opacity: 0.25; }
          }
          @keyframes orbit4 {
            from { transform: rotate(0deg) translateX(115px) rotate(0deg); opacity: 0.2; }
            50% { opacity: 0.6; }
            to { transform: rotate(-360deg) translateX(115px) rotate(360deg); opacity: 0.2; }
          }
          .orb-1 {
            left: 50%;
            top: 50%;
            transform-origin: 0 0;
            animation: orbit1 3.8s linear infinite;
          }
          .orb-2 {
            left: 50%;
            top: 50%;
            transform-origin: 0 0;
            animation: orbit2 5s linear infinite;
          }
          .orb-3 {
            left: 50%;
            top: 50%;
            transform-origin: 0 0;
            animation: orbit3 6.5s linear infinite;
          }
          .orb-4 {
            left: 50%;
            top: 50%;
            transform-origin: 0 0;
            animation: orbit4 8s linear infinite;
          }

          /* Faster orbs when speaking/thinking */
          .orb-1.speaking, .orb-1.thinking { animation-duration: 2s; }
          .orb-2.speaking, .orb-2.thinking { animation-duration: 2.5s; }
          .orb-3.speaking, .orb-3.thinking { animation-duration: 3s; }
          .orb-4.speaking, .orb-4.thinking { animation-duration: 3.5s; }

          /* ======= WAVEFORM - more bars, varied animation ======= */
          .waveform {
            pointer-events: none;
            opacity: 1;
            mix-blend-mode: screen;
            transform: translateZ(0);
          }
          .waveform .bar {
            width: 3px;
            height: 20px;
            border-radius: 999px;
            background: rgba(255, 140, 0, 0.6);
            box-shadow: 0 0 16px rgba(255, 140, 0, 0.25);
            transform-origin: center;
          }

          @keyframes bar {
            0% { transform: scaleY(0.3); opacity: 0.6; }
            50% { transform: scaleY(1.3); opacity: 1; }
            100% { transform: scaleY(0.3); opacity: 0.6; }
          }

          /* default (idle/listening) */
          .waveform.idle .bar,
          .waveform.listening .bar {
            animation: bar 1.6s ease-in-out infinite;
            opacity: 0.6;
            filter: blur(0.15px);
          }

          /* thinking = tighter, smoother */
          .waveform.thinking .bar {
            animation: bar 1s ease-in-out infinite;
            opacity: 0.8;
          }

          /* speaking = punchy */
          .waveform.speaking .bar {
            animation: bar 0.65s ease-in-out infinite;
            opacity: 1;
          }

          /* stagger delays */
          .bar-1 { animation-delay: -0.05s; }
          .bar-2 { animation-delay: -0.1s; }
          .bar-3 { animation-delay: -0.15s; }
          .bar-4 { animation-delay: -0.2s; }
          .bar-5 { animation-delay: -0.25s; }
          .bar-6 { animation-delay: -0.3s; }
          .bar-7 { animation-delay: -0.25s; }
          .bar-8 { animation-delay: -0.2s; }
          .bar-9 { animation-delay: -0.15s; }
          .bar-10 { animation-delay: -0.1s; }
          .bar-11 { animation-delay: -0.05s; }
          .bar-12 { animation-delay: 0s; }

          /* ======= HOLOGRAPHIC STREAMS ======= */
          .holographic-streams {
            position: absolute;
            inset: 0;
            overflow: hidden;
            opacity: 0.2;
            mix-blend-mode: screen;
          }
          .stream {
            position: absolute;
            width: 100%;
            height: 2px;
            background: linear-gradient(to right, transparent, rgba(255, 140, 0, 0.3), transparent);
            animation: stream-flow 2s linear infinite;
          }
          .stream-1 {
            top: 20%;
            animation-duration: 2.5s;
          }
          .stream-2 {
            top: 80%;
            animation-duration: 3s;
            animation-direction: reverse;
          }
          @keyframes stream-flow {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
          }

          /* Glow lines */
          .glow-line {
            box-shadow: 0 0 10px rgba(255, 140, 0, 0.3);
          }
        `}</style>
      </div>
    </div>
  );
}