import React, { useState, useEffect } from 'react';
import { Shield, Radio, UploadCloud, Code, Bell, BellRing, BellOff } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, systemHealthy = true }) {
  const [notifState, setNotifState] = useState('default');

  useEffect(() => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      setNotifState(Notification.permission);
    }
  }, []);

  const requestNotification = async () => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      try {
        const perm = await Notification.requestPermission();
        setNotifState(perm);
        if (perm === 'granted') {
          new Notification('TrustCall VoiceShield', {
            body: 'Active Defense Notifications Enabled. Real-time clone interception is live.',
            icon: '/favicon.ico'
          });
        }
      } catch (e) {
        console.warn('Notification permission error', e);
      }
    }
  };

  const tabs = [
    { id: 'live', label: 'Live Call Monitor', icon: Radio },
    { id: 'upload', label: 'Upload & Analyze', icon: UploadCloud },
    { id: 'docs', label: 'Integration & SDK', icon: Code },
  ];

  return (
    <header className="border-b border-slate-800/80 bg-[#0B0F19]/85 backdrop-blur-xl sticky top-0 z-50 shadow-xl shadow-black/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600/30 via-indigo-600/20 to-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-lg shadow-cyan-500/20 glow-cyan">
            <Shield className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">
                TrustCall
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-950/80 text-cyan-300 border border-cyan-800/60 font-mono font-semibold tracking-wide">
                VoiceShield v1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium hidden sm:block">
              AI-Powered Real-Time Voice Clone Detection (SIH)
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 sm:space-x-2 bg-slate-900/60 p-1 rounded-xl border border-slate-800/80">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-600/40 border border-blue-400/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Status Indicators & Notification Toggle */}
        <div className="flex items-center space-x-2.5">
          <button
            onClick={requestNotification}
            title={
              notifState === 'granted'
                ? 'Desktop Notifications: Active'
                : notifState === 'denied'
                ? 'Desktop Notifications: Blocked in browser'
                : 'Click to enable Desktop Security Alerts'
            }
            className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-xl border text-xs font-mono font-semibold transition-all ${
              notifState === 'granted'
                ? 'bg-cyan-950/40 text-cyan-300 border-cyan-700/60 glow-cyan'
                : notifState === 'denied'
                ? 'bg-slate-900/60 text-slate-500 border-slate-800'
                : 'bg-amber-950/30 text-amber-300 border-amber-700/60 hover:bg-amber-900/40'
            }`}
          >
            {notifState === 'granted' ? (
              <BellRing className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            ) : notifState === 'denied' ? (
              <BellOff className="w-3.5 h-3.5 text-slate-500" />
            ) : (
              <Bell className="w-3.5 h-3.5 text-amber-400" />
            )}
            <span className="hidden lg:inline text-[11px]">
              {notifState === 'granted' ? 'ALERTS ON' : 'ENABLE ALERTS'}
            </span>
          </button>

          <div className="hidden md:flex items-center space-x-3 bg-slate-900/80 border border-slate-800/90 px-3.5 py-1.5 rounded-full text-xs font-mono shadow-inner">
            <div className="flex items-center space-x-2">
              <span className={`w-2.5 h-2.5 rounded-full ${systemHealthy ? 'bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400' : 'bg-rose-500'}`} />
              <span className="text-slate-300 font-semibold tracking-wider text-[11px]">NEURAL SHIELD ACTIVE</span>
            </div>
            <span className="text-slate-700 font-bold">|</span>
            <span className="text-cyan-400 font-bold text-[11px] bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/50">
              AASIST-L (EER: 0.99%)
            </span>
          </div>
        </div>

      </div>
    </header>
  );
}
