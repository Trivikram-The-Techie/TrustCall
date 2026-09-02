import React from 'react';
import { Cpu, Activity, MessageSquareWarning, PhoneCall, CheckCircle2, AlertTriangle, Layers } from 'lucide-react';

export default function ExplanationPanel({ 
  components = {}, 
  explanation = "Awaiting call stream...", 
  forensicReasons = [],
  actionRecommendation = "Monitoring in progress"
}) {
  const modelConf = components.model_confidence || 0;
  const spectralDisc = components.spectral_discontinuity || 0;
  const prosodyScore = components.prosodic_irregularity || 0;
  const urgencyScore = components.urgency_nlp || 0;
  const metaScore = components.caller_metadata || 0;

  const features = [
    {
      id: 'model',
      label: 'Deep Neural Vocoder Confidence',
      score: modelConf,
      weight: '45%',
      icon: Cpu,
      desc: 'Spectral CNN / AASIST artifact detector'
    },
    {
      id: 'prosody',
      label: 'Pitch Flatness & Jitter Distortion',
      score: prosodyScore,
      weight: '15%',
      icon: Activity,
      desc: 'Cycle-to-cycle tremor & robotic pitch contour'
    },
    {
      id: 'spectral',
      label: 'Phase & Splice Discontinuity',
      score: spectralDisc,
      weight: '15%',
      icon: Layers,
      desc: 'Frame concatenation & diffusion boundaries'
    },
    {
      id: 'urgency',
      label: 'Scam Urgency & Coercion Keywords',
      score: urgencyScore,
      weight: '15%',
      icon: MessageSquareWarning,
      desc: 'Multilingual OTP / Digital Arrest / Extortion NLP'
    },
    {
      id: 'meta',
      label: 'Caller ID & Route Reputation',
      score: metaScore,
      weight: '10%',
      icon: PhoneCall,
      desc: 'VoIP gateway spoof & first-time number check'
    }
  ];

  const getBarColor = (score) => {
    if (score >= 70) return 'bg-rose-500';
    if (score >= 40) return 'bg-amber-500';
    return 'bg-emerald-500';
  };

  return (
    <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-md bg-blue-500/20 text-blue-400">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
              Forensic Explainability Engine
            </h3>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            MULTI-SIGNAL FUSION BREAKDOWN
          </span>
        </div>

        {/* Feature Contribution Bars */}
        <div className="space-y-3 mt-4">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div key={f.id} className="bg-[#0B0F19]/60 p-2.5 rounded-lg border border-slate-800/80">
                <div className="flex items-center justify-between text-xs mb-1">
                  <div className="flex items-center space-x-2">
                    <Icon className="w-3.5 h-3.5 text-slate-400" />
                    <span className="font-medium text-slate-300">{f.label}</span>
                    <span className="text-[10px] text-slate-500 font-mono">({f.weight} wt)</span>
                  </div>
                  <span className="font-mono font-bold text-slate-200">
                    {Math.round(f.score)}%
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-slate-800/80 h-2 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 rounded-full ${getBarColor(f.score)}`}
                    style={{ width: `${Math.min(100, Math.max(0, f.score))}%` }}
                  />
                </div>
                <p className="text-[10px] text-slate-500 mt-1">{f.desc}</p>
              </div>
            );
          })}
        </div>

        {/* Forensic Reasons List */}
        <div className="mt-4 pt-3 border-t border-slate-800">
          <span className="text-[11px] font-mono font-semibold text-slate-400 uppercase tracking-wider block mb-2">
            Identified Threat Vectors:
          </span>
          {forensicReasons && forensicReasons.length > 0 ? (
            <div className="space-y-1.5">
              {forensicReasons.map((reason, idx) => (
                <div key={idx} className="flex items-start space-x-2 text-xs text-slate-300 bg-slate-900/90 p-2 rounded border border-slate-800">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                  <span>{reason}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic bg-slate-900/60 p-2 rounded">
              {explanation}
            </p>
          )}
        </div>
      </div>

      {/* Recommended Action Card */}
      <div className="mt-4 p-3 rounded-lg bg-blue-950/30 border border-blue-800/50 flex items-center justify-between">
        <div className="text-xs">
          <span className="text-[10px] uppercase font-mono font-bold text-blue-400 block">
            DEFENSIVE PROTOCOL:
          </span>
          <span className="text-slate-200 font-medium">
            {actionRecommendation}
          </span>
        </div>
      </div>
    </div>
  );
}
