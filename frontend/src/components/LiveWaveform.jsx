import React, { useRef, useEffect } from 'react';
import { Volume2, Mic } from 'lucide-react';

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

      // Background grid lines
      ctx.strokeStyle = '#1F2937';
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
          gradient.addColorStop(0, '#EF4444');
          gradient.addColorStop(0.5, '#F97316');
          gradient.addColorStop(1, '#EF4444');
        } else {
          gradient.addColorStop(0, '#3B82F6');
          gradient.addColorStop(0.5, '#06B6D4');
          gradient.addColorStop(1, '#3B82F6');
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
    <div className="bg-[#111827] border border-slate-800 rounded-xl p-4 shadow-xl">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <div className={`p-1.5 rounded-md ${isStreaming ? 'bg-blue-600/20 text-blue-400' : 'bg-slate-800 text-slate-500'}`}>
            <Volume2 className="w-4 h-4" />
          </div>
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Real-Time Spectral Waveform
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`inline-block w-2 h-2 rounded-full ${isStreaming ? 'bg-emerald-400 animate-ping' : 'bg-slate-600'}`} />
          <span className="text-[11px] font-mono text-slate-400">
            {isStreaming ? 'INGESTING 16kHz PCM' : 'STANDBY'}
          </span>
        </div>
      </div>

      <div className="w-full bg-[#0B0F19] rounded-lg p-2 border border-slate-900">
        <canvas
          ref={canvasRef}
          width={600}
          height={80}
          className="w-full h-20 rounded"
        />
      </div>

      <div className="flex justify-between items-center mt-2 text-[10px] font-mono text-slate-500">
        <span>0 Hz</span>
        <span>4,000 Hz</span>
        <span>8,000 Hz (Nyquist)</span>
      </div>
    </div>
  );
}
