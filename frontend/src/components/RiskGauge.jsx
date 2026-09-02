import React from 'react';
import { AlertTriangle, ShieldCheck, ShieldAlert, AlertOctagon } from 'lucide-react';

export default function RiskGauge({ riskScore = 0, verdict = 'Low', statusText = 'Authentic Voice' }) {
  // Clamp risk score to [0, 100]
  const score = Math.min(100, Math.max(0, Math.round(riskScore)));

  // SVG Gauge calculations
  // Semi-circle arc from 180deg to 0deg (radius 80, stroke 14)
  const radius = 75;
  const circumference = Math.PI * radius; // Half circle circumference
  const strokeDashoffset = circumference - (score / 100) * circumference;

  // Tier configuration
  const getTierConfig = (v, s) => {
    if (s >= 85 || v === 'Critical') {
      return {
        label: 'CRITICAL ATTACK',
        sublabel: 'Terminate Call Immediately',
        color: '#EF4444',
        bgColor: 'bg-rose-950/40',
        borderColor: 'border-rose-500/50',
        textColor: 'text-rose-400',
        icon: AlertOctagon,
        glow: 'threat-active'
      };
    }
    if (s >= 60 || v === 'High') {
      return {
        label: 'HIGH RISK',
        sublabel: 'Probable Voice Clone',
        color: '#F97316',
        bgColor: 'bg-orange-950/40',
        borderColor: 'border-orange-500/50',
        textColor: 'text-orange-400',
        icon: ShieldAlert,
        glow: 'shadow-orange-500/20'
      };
    }
    if (s >= 30 || v === 'Medium') {
      return {
        label: 'MEDIUM CAUTION',
        sublabel: 'Acoustic Irregularities',
        color: '#F59E0B',
        bgColor: 'bg-amber-950/40',
        borderColor: 'border-amber-500/50',
        textColor: 'text-amber-400',
        icon: AlertTriangle,
        glow: 'shadow-amber-500/20'
      };
    }
    return {
      label: 'LOW RISK',
      sublabel: 'Natural Human Voice',
      color: '#10B981',
      bgColor: 'bg-emerald-950/40',
      borderColor: 'border-emerald-500/50',
      textColor: 'text-emerald-400',
      icon: ShieldCheck,
      glow: 'shadow-emerald-500/20'
    };
  };

  const tier = getTierConfig(verdict, score);
  const TierIcon = tier.icon;

  return (
    <div className={`bg-[#111827] border ${tier.borderColor} rounded-xl p-5 shadow-2xl flex flex-col items-center justify-between relative overflow-hidden transition-all duration-500 ${tier.glow}`}>
      {/* Background radial accent glow */}
      <div
        className="absolute -top-10 left-1/2 -translate-x-1/2 w-48 h-48 rounded-full blur-3xl opacity-15 pointer-events-none"
        style={{ backgroundColor: tier.color }}
      />

      <div className="w-full flex items-center justify-between mb-1">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">
          Impersonation Risk Gauge
        </span>
        <div className={`flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${tier.bgColor} ${tier.borderColor} ${tier.textColor}`}>
          <TierIcon className="w-3.5 h-3.5" />
          <span>{tier.label}</span>
        </div>
      </div>

      {/* Radial Semi-Circle SVG */}
      <div className="relative w-56 h-32 flex items-end justify-center mt-2">
        <svg viewBox="0 0 200 115" className="w-full h-full overflow-visible">
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10B981" />
              <stop offset="35%" stopColor="#F59E0B" />
              <stop offset="70%" stopColor="#F97316" />
              <stop offset="100%" stopColor="#EF4444" />
            </linearGradient>
          </defs>

          {/* Background Track Arc */}
          <path
            d="M 25 105 A 75 75 0 0 1 175 105"
            fill="none"
            stroke="#1F2937"
            strokeWidth="14"
            strokeLinecap="round"
          />

          {/* Animated Value Arc */}
          <path
            d="M 25 105 A 75 75 0 0 1 175 105"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="14"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
          />
        </svg>

        {/* Center Readout */}
        <div className="absolute bottom-0 flex flex-col items-center">
          <span className="text-4xl font-extrabold font-mono tracking-tight text-white drop-shadow">
            {score}
          </span>
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest -mt-1">
            SCORE / 100
          </span>
        </div>
      </div>

      {/* Threshold Markers */}
      <div className="w-full flex justify-between px-6 text-[10px] font-mono text-slate-500 mt-1">
        <span>0 (Genuine)</span>
        <span>30</span>
        <span>60</span>
        <span>85</span>
        <span>100 (Clone)</span>
      </div>

      {/* Status Summary Banner */}
      <div className={`w-full mt-3 p-2.5 rounded-lg border text-center ${tier.bgColor} ${tier.borderColor}`}>
        <p className={`text-xs font-semibold ${tier.textColor}`}>
          {statusText || tier.sublabel}
        </p>
      </div>
    </div>
  );
}
