import React from 'react';
import { AlertTriangle, ShieldCheck, ShieldAlert, AlertOctagon } from 'lucide-react';

export default function RiskGauge({ riskScore = 0, verdict = 'Low', statusText = 'Authentic Voice' }) {
  // Clamp risk score to [0, 100]
  const score = Math.min(100, Math.max(0, Math.round(riskScore)));

  // SVG Gauge calculations
  const radius = 75;
  const circumference = Math.PI * radius; // Half circle circumference
  const strokeDashoffset = circumference - (score / 100) * circumference;

  // Tier configuration for warm professional aesthetic
  const getTierConfig = (v, s) => {
    if (s >= 85 || v === 'Critical') {
      return {
        label: 'CRITICAL ATTACK',
        sublabel: 'Terminate Call Immediately',
        color: '#DC2626',
        bgColor: 'bg-rose-50',
        borderColor: 'border-rose-300',
        textColor: 'text-rose-900',
        icon: AlertOctagon,
        glow: 'threat-active'
      };
    }
    if (s >= 60 || v === 'High') {
      return {
        label: 'HIGH RISK',
        sublabel: 'Probable Voice Clone',
        color: '#EA580C',
        bgColor: 'bg-orange-50',
        borderColor: 'border-orange-300',
        textColor: 'text-orange-900',
        icon: ShieldAlert,
        glow: 'glow-orange border-orange-300'
      };
    }
    if (s >= 30 || v === 'Medium') {
      return {
        label: 'MEDIUM CAUTION',
        sublabel: 'Acoustic Irregularities',
        color: '#D97706',
        bgColor: 'bg-amber-50',
        borderColor: 'border-amber-300',
        textColor: 'text-amber-900',
        icon: AlertTriangle,
        glow: 'glow-amber border-amber-300'
      };
    }
    return {
      label: 'LOW RISK',
      sublabel: 'Natural Human Voice',
      color: '#16A34A',
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-300',
      textColor: 'text-emerald-900',
      icon: ShieldCheck,
      glow: 'glow-emerald border-emerald-300'
    };
  };

  const tier = getTierConfig(verdict, score);
  const TierIcon = tier.icon;

  return (
    <div className={`glass-card rounded-2xl p-5 shadow-sm flex flex-col items-center justify-between relative overflow-hidden transition-all duration-500 ${tier.glow}`}>
      {/* Dynamic Ambient Warm Radial Aura */}
      <div
        className="absolute -top-12 left-1/2 -translate-x-1/2 w-64 h-64 rounded-full blur-3xl opacity-15 pointer-events-none transition-colors duration-700"
        style={{ backgroundColor: tier.color }}
      />

      <div className="w-full flex items-center justify-between mb-1 z-10">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: tier.color }} />
          <span className="text-xs font-bold text-[#44403C] uppercase tracking-wider font-mono">
            Impersonation Risk Gauge
          </span>
        </div>
        <div className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-[11px] font-bold border backdrop-blur-md shadow-sm transition-all ${tier.bgColor} ${tier.borderColor} ${tier.textColor}`}>
          <TierIcon className="w-3.5 h-3.5" />
          <span>{tier.label}</span>
        </div>
      </div>

      {/* Radial Semi-Circle SVG */}
      <div className="relative w-60 h-32 flex items-end justify-center mt-3 z-10">
        <svg viewBox="0 0 200 115" className="w-full h-full overflow-visible">
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#16A34A" />
              <stop offset="35%" stopColor="#D97706" />
              <stop offset="70%" stopColor="#EA580C" />
              <stop offset="100%" stopColor="#DC2626" />
            </linearGradient>
            <filter id="glowArc" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Background Track Arc in Warm Stone */}
          <path
            d="M 25 105 A 75 75 0 0 1 175 105"
            fill="none"
            stroke="#E7E2D6"
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
            filter="url(#glowArc)"
            className="transition-all duration-700 ease-out"
          />
        </svg>

        {/* Center Readout in Rich Charcoal */}
        <div className="absolute bottom-0 flex flex-col items-center pointer-events-none">
          <span 
            className="text-4xl font-black font-mono tracking-tight text-[#1C1917] transition-colors duration-500"
          >
            {score}
          </span>
          <span className="text-[10px] font-mono text-[#78716C] uppercase tracking-widest -mt-1 font-bold">
            SCORE / 100
          </span>
        </div>
      </div>

      {/* Threshold Markers */}
      <div className="w-full flex justify-between px-6 text-[10px] font-mono text-[#78716C] mt-2 z-10">
        <span className="text-emerald-700 font-semibold">0 (Authentic)</span>
        <span>30</span>
        <span>60</span>
        <span>85</span>
        <span className="text-rose-700 font-semibold">100 (Clone)</span>
      </div>

      {/* Status Summary Banner */}
      <div className={`w-full mt-3 p-2.5 rounded-xl border text-center transition-all z-10 shadow-sm ${tier.bgColor} ${tier.borderColor}`}>
        <p className={`text-xs font-bold ${tier.textColor}`}>
          {statusText || tier.sublabel}
        </p>
      </div>
    </div>
  );
}
