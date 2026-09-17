import React from 'react';
import { History, ShieldAlert, AlertTriangle, CheckCircle, ShieldX } from 'lucide-react';

export default function AlertTimeline({ events = [] }) {
  const getBadge = (tier) => {
    switch (tier) {
      case 'Critical':
        return {
          bg: 'bg-rose-50 text-rose-900 border-rose-300',
          textColor: 'text-rose-900',
          icon: ShieldX
        };
      case 'High':
        return {
          bg: 'bg-orange-50 text-orange-900 border-orange-300',
          textColor: 'text-orange-900',
          icon: ShieldAlert
        };
      case 'Medium':
        return {
          bg: 'bg-amber-50 text-amber-900 border-amber-300',
          textColor: 'text-amber-900',
          icon: AlertTriangle
        };
      default:
        return {
          bg: 'bg-emerald-50 text-emerald-900 border-emerald-300',
          textColor: 'text-emerald-900',
          icon: CheckCircle
        };
    }
  };

  return (
    <div className="glass-card rounded-2xl p-5 shadow-sm border border-[#E6E0D2] flex flex-col h-full">
      <div className="flex items-center justify-between mb-3 border-b border-[#E6E0D2] pb-2.5">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-amber-100 text-amber-900 border border-amber-300 shadow-sm">
            <History className="w-4 h-4" />
          </div>
          <h3 className="text-xs font-bold text-[#1C1917] uppercase tracking-wider font-mono">
            Alert & Audit Timeline
          </h3>
        </div>
        <span className="text-[10px] font-mono font-bold text-[#78716C] bg-stone-100 px-2.5 py-0.5 rounded-full border border-stone-200">
          PRIVACY ENFORCED (NO RAW AUDIO STORED)
        </span>
      </div>

      <div className="flex-1 overflow-y-auto max-h-64 space-y-2.5 pr-1 mt-1">
        {events.length === 0 ? (
          <div className="h-40 flex flex-col items-center justify-center text-[#78716C] text-xs border border-dashed border-[#DDD5C5] rounded-xl p-4 bg-[#FBF9F5]">
            <CheckCircle className="w-7 h-7 text-emerald-600 mb-2" />
            <p className="font-semibold text-[#44403C]">No threat anomalies or alerts logged yet.</p>
            <p className="text-[11px] text-[#78716C] mt-0.5">Streaming session is clean.</p>
          </div>
        ) : (
          events.slice().reverse().map((evt, idx) => {
            const badge = getBadge(evt.alert_tier || evt.verdict);
            const Icon = badge.icon;
            const timeStr = evt.timestamp 
              ? new Date(evt.timestamp * 1000).toLocaleTimeString() 
              : new Date().toLocaleTimeString();

            return (
              <div
                key={idx}
                className="bg-[#FAF8F5] p-3 rounded-xl border border-[#E8E2D6] flex items-start space-x-3 transition-all hover:border-[#D4CBBF] shadow-sm"
              >
                <div className={`p-1.5 rounded-lg border mt-0.5 shrink-0 ${badge.bg}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-xs font-bold uppercase tracking-wider ${badge.textColor}`}>
                      {evt.alert_tier || evt.verdict} Alert — Score: {evt.risk_score}
                    </span>
                    <span className="text-[10px] font-mono text-[#78716C]">
                      {timeStr}
                    </span>
                  </div>
                  <p className="text-xs text-[#292524] leading-snug">
                    {evt.explanation || evt.message || 'Threat detection threshold crossed'}
                  </p>
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="mt-3 pt-2.5 border-t border-[#E6E0D2] flex items-center justify-between text-[11px] font-mono text-[#78716C]">
        <span>Session TTL: 300s</span>
        <span className="text-emerald-700 font-bold">Cryptographic Salt Active</span>
      </div>
    </div>
  );
}
