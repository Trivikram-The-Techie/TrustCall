import React, { useRef, useEffect } from 'react';
import { Volume2 } from 'lucide-react';

export default function LiveWaveform({ isStreaming, audioEnergy = 0, isSynthetic = false }) {
  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);
  const phaseRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      // Background grid line in soft warm stone
      ctx.strokeStyle = '#E3DDD2';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, height / 2);
      ctx.lineTo(width, height / 2);
      ctx.stroke();

      const numBars = 48;
      const barWidth = width / numBars - 2;
      const centerY = height / 2;

      phaseRef.current += isStreaming ? 0.08 : 0.02;

      for (let i = 0; i < numBars; i++) {
        const x = i * (barWidth + 2);
        
        // Amplitude formula
        let barHeight = 4;
        if (isStreaming) {
          const energyBoost = Math.max(0.15, audioEnergy * 4);
          const wave = Math.sin(phaseRef.current + i * 0.3) * Math.cos(phaseRef.current * 0.5 + i * 0.15);
          barHeight = Math.max(4, Math.abs(wave) * height * 0.45 * energyBoost + Math.random() * 6);
        } else {
          barHeight = 4 + Math.sin(phaseRef.current + i * 0.2) * 2;
        }

        // Color based on synthetic risk
        const gradient = ctx.createLinearGradient(0, centerY - barHeight, 0, centerY + barHeight);
        if (isSynthetic) {
          gradient.addColorStop(0, '#DC2626');
          gradient.addColorStop(0.5, '#EA580C');
          gradient.addColorStop(1, '#DC2626');
        } else {
          gradient.addColorStop(0, '#0D9488');
          gradient.addColorStop(0.5, '#2563EB');
          gradient.addColorStop(1, '#0D9488');
        }

        ctx.fillStyle = gradient;
        ctx.fillRect(x, centerY - barHeight / 2, barWidth, barHeight);
      }

      animFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [isStreaming, audioEnergy, isSynthetic]);

  return (
    <div className="glass-card rounded-2xl p-4.5 shadow-sm border border-[#E6E0D2]">
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center space-x-2">
          <div className={`p-1.5 rounded-xl border transition-all ${
            isStreaming 
              ? 'bg-amber-100/70 text-amber-900 border-amber-300 shadow-sm' 
              : 'bg-stone-100 text-stone-500 border-stone-200'
          }`}>
            <Volume2 className="w-4 h-4" />
          </div>
          <span className="text-xs font-bold text-[#1C1917] uppercase tracking-wider font-mono">
            Real-Time Spectral Waveform
          </span>
        </div>
        <div className="flex items-center space-x-2 bg-white px-2.5 py-1 rounded-full border border-[#E6E0D2] shadow-sm">
          <span className={`inline-block w-2 h-2 rounded-full ${isStreaming ? 'bg-emerald-500 animate-pulse' : 'bg-stone-400'}`} />
          <span className="text-[10px] font-mono font-bold text-[#44403C]">
            {isStreaming ? 'INGESTING 16kHz PCM' : 'STANDBY'}
          </span>
        </div>
      </div>

      <div className="w-full bg-[#F5F2EB] rounded-xl p-2 border border-[#E2DDD0] shadow-inner">
        <canvas
          ref={canvasRef}
          width={600}
          height={80}
          className="w-full h-20 rounded-lg"
        />
      </div>

      <div className="flex justify-between items-center mt-2 text-[10px] font-mono text-[#78716C]">
        <span>0 Hz</span>
        <span>4,000 Hz</span>
        <span>8,000 Hz (Nyquist)</span>
      </div>
    </div>
  );
}
