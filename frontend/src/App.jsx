import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LiveCallDemo from './pages/LiveCallDemo';
import { ShieldCheck, Lock, EyeOff } from 'lucide-react';

export default function App() {
  const [systemHealthy, setSystemHealthy] = useState(true);

  useEffect(() => {
    // Probe backend health check
    fetch('/health')
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'healthy') setSystemHealthy(true);
      })
      .catch(() => setSystemHealthy(false));
  }, []);

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-[#1C1917] flex flex-col justify-between selection:bg-amber-200 selection:text-amber-950">
      <div>
        <Navbar systemHealthy={systemHealthy} />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <LiveCallDemo />
        </main>
      </div>

      {/* Warm Linen Footer */}
      <footer className="border-t border-[#E6E0D2] bg-[#F7F4EC]/80 backdrop-blur-sm py-5 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between text-xs text-[#78716C] gap-3">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-amber-700" />
            <span className="font-medium text-[#44403C]">Smart India Hackathon Prototype — TrustCall / VoiceShield</span>
          </div>

          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-1.5 text-[#57534E]">
              <EyeOff className="w-3.5 h-3.5 text-emerald-600" />
              <span className="font-mono text-[11px]">Zero Raw Audio Retained</span>
            </div>
            <div className="flex items-center space-x-1.5 text-[#57534E]">
              <Lock className="w-3.5 h-3.5 text-indigo-600" />
              <span className="font-mono text-[11px]">HMAC-SHA256 Irreversible Salt</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
