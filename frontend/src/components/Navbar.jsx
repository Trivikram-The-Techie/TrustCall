import React from 'react';
import { Shield, Radio, UploadCloud, Code, Activity } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, systemHealthy = true }) {
  const tabs = [
    { id: 'live', label: 'Live Call Monitor', icon: Radio },
    { id: 'upload', label: 'Upload & Analyze', icon: UploadCloud },
    { id: 'docs', label: 'Integration & SDK', icon: Code },
  ];

  return (
    <header className="border-b border-slate-800 bg-[#0E1526]/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 shadow-lg shadow-blue-500/10">
            <Shield className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-blue-400 via-indigo-300 to-cyan-400 bg-clip-text text-transparent">
                TrustCall
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-950 text-blue-300 border border-blue-800/60 font-mono">
                VoiceShield v1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              AI-Powered Real-Time Voice Cloning Detection (SIH)
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 sm:space-x-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Status Indicator */}
        <div className="hidden md:flex items-center space-x-3 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded-full text-xs font-mono">
          <div className="flex items-center space-x-2">
            <span className={`w-2 h-2 rounded-full ${systemHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span className="text-slate-300">NEURAL DEFENSE ACTIVE</span>
          </div>
          <span className="text-slate-600">|</span>
          <span className="text-cyan-400 text-[11px]">16kHz AASIST/CNN</span>
        </div>
      </div>
    </header>
  );
}
