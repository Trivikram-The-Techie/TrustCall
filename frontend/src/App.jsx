import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LiveCallDemo from './pages/LiveCallDemo';
import UploadAndAnalyze from './pages/UploadAndAnalyze';
import IntegrationDocs from './pages/IntegrationDocs';
import { ShieldCheck, Lock, EyeOff } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('live');
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
    <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col justify-between">
      <div>
        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          systemHealthy={systemHealthy}
        />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {activeTab === 'live' && <LiveCallDemo />}
          {activeTab === 'upload' && <UploadAndAnalyze />}
          {activeTab === 'docs' && <IntegrationDocs />}
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#0E1526]/60 py-5 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between text-xs text-slate-500 gap-3">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-blue-400" />
            <span>Smart India Hackathon Prototype — TrustCall / VoiceShield</span>
          </div>

          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-1.5 text-slate-400">
              <EyeOff className="w-3.5 h-3.5 text-emerald-400" />
              <span>Zero Raw Audio Retained</span>
            </div>
            <div className="flex items-center space-x-1.5 text-slate-400">
              <Lock className="w-3.5 h-3.5 text-cyan-400" />
              <span>HMAC-SHA256 Irreversible Salt</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
