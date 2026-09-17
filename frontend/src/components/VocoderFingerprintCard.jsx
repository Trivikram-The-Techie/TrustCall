import React from 'react';
import { Fingerprint, CheckCircle2, AlertOctagon } from 'lucide-react';

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
      return 'bg-emerald-50 text-emerald-900 border-emerald-300';
    }
    if (arch.includes('Diffusion')) {
      return 'bg-purple-50 text-purple-900 border-purple-300';
    }
    if (arch.includes('HiFi-GAN') || arch.includes('Vocoder')) {
      return 'bg-rose-50 text-rose-900 border-rose-300';
    }
    return 'bg-stone-100 text-stone-900 border-stone-300';
  };

  return (
    <div className="glass-card rounded-2xl p-5 shadow-sm border border-[#E6E0D2] space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#E6E0D2] pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-amber-100 text-amber-900 border border-amber-300 shadow-sm">
            <Fingerprint className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-[#1C1917] uppercase tracking-wider font-mono">
              Neural Vocoder & Synthesis Architecture Profiler
            </h3>
            <p className="text-[11px] text-[#78716C]">
              Fingerprints underlying generative speech model artifacts
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-[10px] text-[#78716C] block font-mono uppercase">Fingerprint Match</span>
          <span className="text-xs font-mono font-bold text-[#1C1917]">
            {Math.round(confidence * 100)}% Match
          </span>
        </div>
      </div>

      {/* Primary Detected Architecture Box */}
      <div className={`p-3 rounded-xl border flex items-center justify-between gap-3 shadow-sm ${getArchBadgeStyle(primary_architecture)}`}>
        <div className="flex items-center space-x-2.5 min-w-0">
          {isSynthetic ? (
            <AlertOctagon className="w-5 h-5 text-rose-600 shrink-0" />
          ) : (
            <CheckCircle2 className="w-5 h-5 text-emerald-700 shrink-0" />
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
      <p className="text-xs text-[#292524] leading-relaxed bg-[#F5F2EB] p-3 rounded-xl border border-[#E0D8CA]">
        {fingerprint_summary}
      </p>

      {/* Architecture Probability Distribution Bars */}
      <div className="space-y-2 pt-1">
        <span className="text-[10px] text-[#57534E] uppercase font-bold tracking-wider block">
          Architecture Probability Distribution
        </span>
        <div className="space-y-1.5">
          {Object.entries(architecture_scores).map(([arch, score]) => {
            const pct = Math.round(score * 100);
            return (
              <div key={arch} className="space-y-0.5">
                <div className="flex justify-between text-[11px]">
                  <span className="text-[#1C1917] truncate font-mono font-medium">{arch}</span>
                  <span className="text-[#78716C] font-mono font-semibold ml-2">{pct}%</span>
                </div>
                <div className="w-full bg-[#EAE5DA] h-1.5 rounded-full overflow-hidden border border-[#DDD6C8]">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      arch.includes('Organic')
                        ? 'bg-emerald-600'
                        : arch.includes('Diffusion')
                        ? 'bg-purple-600'
                        : arch.includes('HiFi-GAN')
                        ? 'bg-rose-600'
                        : 'bg-sky-600'
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
      <div className="grid grid-cols-3 gap-2.5 pt-1">
        <div className="bg-[#FAF8F5] p-2.5 rounded-xl border border-[#E6E0D2] text-center shadow-sm">
          <span className="text-[9px] text-[#78716C] block uppercase font-mono font-bold">Comb Ripple</span>
          <span className="text-xs font-mono font-black text-[#1C1917]">{comb_ripple_index}</span>
        </div>
        <div className="bg-[#FAF8F5] p-2.5 rounded-xl border border-[#E6E0D2] text-center shadow-sm">
          <span className="text-[9px] text-[#78716C] block uppercase font-mono font-bold">Phase Continuity</span>
          <span className="text-xs font-mono font-black text-[#1C1917]">{phase_continuity_index}</span>
        </div>
        <div className="bg-[#FAF8F5] p-2.5 rounded-xl border border-[#E6E0D2] text-center shadow-sm">
          <span className="text-[9px] text-[#78716C] block uppercase font-mono font-bold">Pitch Flatness</span>
          <span className="text-xs font-mono font-black text-[#1C1917]">{pitch_stability_index}</span>
        </div>
      </div>
    </div>
  );
}
