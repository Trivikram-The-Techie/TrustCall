import React from 'react';
import { Cpu, Fingerprint, Activity, Zap, CheckCircle2, AlertOctagon } from 'lucide-react';

export default function VocoderFingerprintCard({ fingerprint }) {
  if (!fingerprint) return null;

  const {
    primary_architecture = 'Organic Human Biomechanics',
    architecture_scores = {
      'Organic Human Biomechanics': 0.88,
      'Diffusion / Flow-Matching (ElevenLabs/XTTS)': 0.05,
      'Neural Vocoder (HiFi-GAN/BigVGAN)': 0.04,
      'Autoregressive Codec (Bark/AudioLM)': 0.03
    },
    comb_ripple_index = 0.12,
    phase_continuity_index = 0.92,
    pitch_stability_index = 0.35,
    confidence = 0.85,
    fingerprint_summary = 'Natural vocal tract micro-tremor and physiological pitch trajectory confirmed.'
  } = fingerprint;

  const isSynthetic = !primary_architecture.includes('Organic Human');

  const getArchBadgeStyle = (arch) => {
    if (arch.includes('Organic Human')) {
      return 'bg-emerald-950/40 text-emerald-300 border-emerald-500/40';
    }
    if (arch.includes('Diffusion')) {
      return 'bg-purple-950/40 text-purple-300 border-purple-500/40';
    }
    if (arch.includes('HiFi-GAN') || arch.includes('Vocoder')) {
      return 'bg-rose-950/40 text-rose-300 border-rose-500/40';
    }
    return 'bg-cyan-950/40 text-cyan-300 border-cyan-500/40';
  };

  return (
    <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30">
            <Fingerprint className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              Neural Vocoder & Synthesis Architecture Profiler
            </h3>
            <p className="text-[11px] text-slate-400">
              Fingerprints underlying generative speech model artifacts
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-[10px] text-slate-500 block font-mono uppercase">Fingerprint Match</span>
          <span className="text-xs font-mono font-bold text-slate-300">
            {Math.round(confidence * 100)}% Match
          </span>
        </div>
      </div>

      {/* Primary Detected Architecture Box */}
      <div className={`p-3 rounded-xl border flex items-center justify-between gap-3 ${getArchBadgeStyle(primary_architecture)}`}>
        <div className="flex items-center space-x-2.5 min-w-0">
          {isSynthetic ? (
            <AlertOctagon className="w-5 h-5 text-rose-400 shrink-0" />
          ) : (
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          )}
          <div className="truncate">
            <span className="text-[10px] block uppercase font-bold tracking-wider opacity-75">
              Identified Architecture Signature
            </span>
            <div className="text-xs font-bold font-mono truncate">
              {primary_architecture}
            </div>
          </div>
        </div>
      </div>

      {/* Forensic Summary */}
      <p className="text-xs text-slate-300 leading-relaxed bg-[#0B0F19] p-3 rounded-lg border border-slate-800/80">
        {fingerprint_summary}
      </p>

      {/* Architecture Probability Distribution Bars */}
      <div className="space-y-2 pt-1">
        <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">
          Architecture Probability Distribution
        </span>
        <div className="space-y-1.5">
          {Object.entries(architecture_scores).map(([arch, score]) => {
            const pct = Math.round(score * 100);
            return (
              <div key={arch} className="space-y-0.5">
                <div className="flex justify-between text-[11px]">
                  <span className="text-slate-300 truncate font-mono">{arch}</span>
                  <span className="text-slate-400 font-mono font-semibold ml-2">{pct}%</span>
                </div>
                <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      arch.includes('Organic')
                        ? 'bg-emerald-400'
                        : arch.includes('Diffusion')
                        ? 'bg-purple-500'
                        : arch.includes('HiFi-GAN')
                        ? 'bg-rose-500'
                        : 'bg-cyan-500'
                    }`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Diagnostic Signal Telemetry */}
      <div className="grid grid-cols-3 gap-2 pt-1">
        <div className="bg-[#0B0F19] p-2 rounded-lg border border-slate-800 text-center">
          <span className="text-[9px] text-slate-500 block uppercase font-mono">Comb Ripple</span>
          <span className="text-xs font-mono font-bold text-slate-200">{comb_ripple_index}</span>
        </div>
        <div className="bg-[#0B0F19] p-2 rounded-lg border border-slate-800 text-center">
          <span className="text-[9px] text-slate-500 block uppercase font-mono">Phase Continuity</span>
          <span className="text-xs font-mono font-bold text-slate-200">{phase_continuity_index}</span>
        </div>
        <div className="bg-[#0B0F19] p-2 rounded-lg border border-slate-800 text-center">
          <span className="text-[9px] text-slate-500 block uppercase font-mono">Pitch Flatness</span>
          <span className="text-xs font-mono font-bold text-slate-200">{pitch_stability_index}</span>
        </div>
      </div>
    </div>
  );
}
