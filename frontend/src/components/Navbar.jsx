import React, { useState, useEffect } from 'react';
import { Shield, Bell, BellRing, BellOff, PhoneCall, BarChart3, UploadCloud, BookOpen, Skull, Cpu } from 'lucide-react';

export default function Navbar({ systemHealthy = true, activeTab = 'live', setActiveTab }) {
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
            body: 'Active Defense Notifications Enabled. Real-time voice clone interception is active.',
            icon: '/favicon.ico'
          });
        }
      } catch (e) {
        console.warn('Notification permission error', e);
      }
    }
  };

  const navItems = [
    { id: 'live', label: 'Live Shield', icon: PhoneCall },
    { id: 'redteam', label: 'Red-Team Lab', icon: Skull, badge: 'Stress' },
    { id: 'benchmarks', label: 'Benchmarks', icon: BarChart3, badge: 'EER' },
    { id: 'scale', label: 'Scale', icon: Cpu, badge: '1M' },
    { id: 'upload', label: 'Upload & Score', icon: UploadCloud },
    { id: 'docs', label: 'API & Specs', icon: BookOpen }
  ];

  return (
    <header className="border-b border-[#E6E0D2] bg-[#FDFBF7]/90 backdrop-blur-xl sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="h-16 flex items-center justify-between">
          {/* Brand */}
          <div 
            className="flex items-center space-x-3.5 cursor-pointer"
            onClick={() => setActiveTab && setActiveTab('live')}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-stone-900 via-stone-800 to-indigo-950 border border-stone-700 flex items-center justify-center text-amber-200 shadow-md">
              <Shield className="w-5 h-5 text-amber-300" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-tight text-[#1C1917]">
                  TrustCall
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#F5F1E8] text-[#57534E] border border-[#E0D8C8] font-mono font-semibold tracking-wide">
                  VoiceShield v1.0
                </span>
              </div>
              <p className="text-[11px] text-[#78716C] font-medium hidden sm:block">
                AI-Powered Real-Time Voice Clone Detection & Defense (SIH)
              </p>
            </div>
          </div>

          {/* Navigation Tabs (Desktop) */}
          <nav className="hidden md:flex items-center space-x-1 bg-[#F5F1E8]/70 p-1 rounded-xl border border-[#E0D8C8]">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab && setActiveTab(item.id)}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-white text-[#1C1917] shadow-sm font-bold border border-[#E6E0D2]'
                      : 'text-[#78716C] hover:text-[#292524] hover:bg-white/50'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-amber-700' : 'text-stone-400'}`} />
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded-full bg-amber-100 text-amber-900 border border-amber-200">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Status Indicators & Notification Toggle */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            <button
              onClick={requestNotification}
              title={
                notifState === 'granted'
                  ? 'Desktop Threat Alerts: Active'
                  : notifState === 'denied'
                  ? 'Desktop Threat Alerts: Blocked in browser'
                  : 'Click to enable Desktop Security Alerts'
              }
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border text-xs font-mono font-semibold transition-all shadow-sm ${
                notifState === 'granted'
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                  : notifState === 'denied'
                  ? 'bg-stone-100 text-stone-500 border-stone-300'
                  : 'bg-amber-50 text-amber-900 border-amber-300 hover:bg-amber-100'
              }`}
            >
              {notifState === 'granted' ? (
                <BellRing className="w-3.5 h-3.5 text-emerald-600 animate-pulse" />
              ) : notifState === 'denied' ? (
                <BellOff className="w-3.5 h-3.5 text-stone-400" />
              ) : (
                <Bell className="w-3.5 h-3.5 text-amber-600" />
              )}
              <span className="hidden sm:inline text-[11px]">
                {notifState === 'granted' ? 'ALERTS ON' : 'ENABLE ALERTS'}
              </span>
            </button>

            <div className="hidden lg:flex items-center space-x-3 bg-white/90 border border-[#E6E0D2] px-3.5 py-1.5 rounded-full text-xs font-mono shadow-sm">
              <div className="flex items-center space-x-2">
                <span className={`w-2.5 h-2.5 rounded-full ${systemHealthy ? 'bg-emerald-500 animate-pulse shadow-sm shadow-emerald-400' : 'bg-rose-500'}`} />
                <span className="text-[#44403C] font-semibold tracking-wider text-[11px]">NEURAL SHIELD</span>
              </div>
              <span className="text-[#D6CEBF] font-bold">|</span>
              <span className="text-indigo-900 font-bold text-[11px] bg-indigo-50/80 px-2 py-0.5 rounded border border-indigo-200">
                AASIST-L (EER: 0.99%)
              </span>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Bar */}
        <div className="md:hidden flex items-center justify-around py-2 border-t border-[#EAE4D7] overflow-x-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab && setActiveTab(item.id)}
                className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-semibold whitespace-nowrap ${
                  isActive
                    ? 'bg-amber-100/70 text-amber-950 font-bold'
                    : 'text-stone-600 hover:text-stone-900'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-amber-800' : 'text-stone-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
}
