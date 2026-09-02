import React from 'react';
import { History, ShieldAlert, AlertTriangle, CheckCircle, ShieldX } from 'lucide-react';

export default function AlertTimeline({ events = [] }) {
  const getBadge = (tier) => {
    switch (tier) {
      case 'Critical':
        return {
          bg: 'bg-rose-500/20 text-rose-400 border-rose-500/40',
          icon: ShieldX
        };
      case 'High':
        return {
          bg: 'bg-orange-500/20 text-orange-400 border-orange-500/40',
          icon: ShieldAlert
        };
      case 'Medium':
        return {
          bg: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
          icon: AlertTriangle
        };
      default:
        return {
          bg: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
          icon: CheckCircle
        };
    }
  };

  return (
    <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-md bg-indigo-500/20 text-indigo-400">
            <History className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
            Alert & Audit Timeline
          </h3>
        </div>
        <span className="text-[11px] font-mono text-slate-400">
          PRIVACY ENFORCED (NO RAW AUDIO STORED)
        </span>
      </div>

      <div className="flex-1 overflow-y-auto max-h-64 space-y-2.5 pr-1 mt-2">
        {events.length === 0 ? (
          <div className="h-44 flex flex-col items-center justify-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg p-4">
            <CheckCircle className="w-8 h-8 text-slate-600 mb-2" />
            <p>No threat anomalies or alerts logged yet.</p>
            <p className="text-[11px] text-slate-600 mt-1">Streaming session clean.</p>
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
                className="bg-[#0B0F19] p-3 rounded-lg border border-slate-800/80 flex items-start space-x-3 transition-all hover:border-slate-700"
              >
                <div className={`p-1 rounded border mt-0.5 ${badge.bg}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-xs font-bold uppercase tracking-wider ${badge.bg.split(' ')[1]}`}>
                      {evt.alert_tier || evt.verdict} Alert — Score: {evt.risk_score}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">
                      {timeStr}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-snug">
                    {evt.explanation || evt.message || 'Threat detection threshold crossed'}
                  </p>
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="mt-3 pt-2.5 border-t border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-500">
        <span>Session TTL: 300s</span>
        <span className="text-emerald-400">Cryptographic Salt Active</span>
      </div>
    </div>
  );
}
