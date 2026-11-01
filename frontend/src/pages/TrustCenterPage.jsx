import React, { useState } from 'react';
import { 
  ShieldCheck, Lock, EyeOff, Server, Clock, FileText, 
  CheckCircle2, AlertTriangle, ArrowRight, Database, KeyRound,
  ExternalLink, Download, Layers, ShieldAlert, Cpu
} from 'lucide-react';

export default function TrustCenterPage() {
  const [activeSection, setActiveSection] = useState('overview');

  const retentionPolicy = [
    {
      data_type: 'Raw Audio Stream (PCM/WAV)',
      storage_location: 'Volatile RAM Buffer Only',
      retention_period: '0 ms (Destroyed post-inference)',
      purpose: 'Real-time neural vocoder feature extraction',
      dpdp_alignment: 'Section 6: Absolute Data Minimization'
    },
    {
      data_type: 'Acoustic Feature Vectors',
      storage_location: 'In-Memory Ring Buffer',
      retention_period: '1.5 seconds (Sliding Window)',
      purpose: 'Pitch F0 intonation, jitter, spectral continuity',
      dpdp_alignment: 'Section 4: Purpose Limitation'
    },
    {
      data_type: 'Speaker Biometric Signature',
      storage_location: 'In-Memory Key-Value Cache',
      retention_period: '300 seconds (Session TTL)',
      purpose: 'Irreversible HMAC-SHA256 repeat scammer flag',
      dpdp_alignment: 'Section 8: Cryptographic Safeguards'
    },
    {
      data_type: 'Fraud Risk Telemetry',
      storage_location: 'Session Store / Prometheus Gauge',
      retention_period: '300 seconds TTL',
      purpose: 'Risk tier display & banking webhook trigger',
      dpdp_alignment: 'Section 12: Right to Erasure'
    },
    {
      data_type: 'Forensic Audit Certificate',
      storage_location: 'Client Download / Bank SOC',
      retention_period: 'User / Enterprise Discretion',
      purpose: 'MeitY / BNS Section 65B legal evidence bag',
      dpdp_alignment: 'Section 7: Lawful Record of Incident'
    }
  ];

  const dpdpPillars = [
    {
      section: 'Section 4',
      title: 'Lawful Grounds & User Consent',
      desc: 'Processing is strictly restricted to defending the call recipient from fraudulent financial impersonation and unauthorized electronic extraction.',
      status: 'Fully Compliant'
    },
    {
      section: 'Section 6',
      title: 'Absolute Data Minimization',
      desc: 'No voice recordings or voiceprints are retained. Raw audio frames are ingested into RAM, processed through AASIST-L, and immediately zeroed.',
      status: 'Engineered by Design'
    },
    {
      section: 'Section 8',
      title: 'Security Safeguards & Encryption',
      desc: 'All inter-service telemetry uses RFC-2104 HMAC-SHA256 with timestamp drift limits and replay-prevention nonces. Strict CSP, HSTS, and frame-ancestors none enforced.',
      status: 'Hardware & Crypto Validated'
    },
    {
      section: 'Section 12',
      title: 'Right to Erasure & Zero Retention',
      desc: 'Session state is governed by an automated 300s garbage collection loop. Once a call is terminated, all associated acoustic artifacts vanish from memory.',
      status: 'Automated TTL Purge'
    }
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Hero Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center space-x-2 bg-emerald-50 border border-emerald-300 rounded-full px-4 py-1.5 shadow-sm">
          <ShieldCheck className="w-4 h-4 text-emerald-700" />
          <span className="text-xs font-mono font-bold text-emerald-800 uppercase tracking-wider">
            DPDP Act 2023 Verified • Zero Raw Audio Retained
          </span>
        </div>
        <h1 className="text-3xl font-extrabold text-[#1C1917] tracking-tight sm:text-4xl">
          Trust, Privacy & Security Center
        </h1>
        <p className="text-sm text-[#78716C] max-w-2xl mx-auto leading-relaxed">
          TrustCall is architected from the silicon level up to defend citizens and banking infrastructure without ever becoming a surveillance tool.
        </p>
      </div>

      {/* 3 Core Architecture Guarantees */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white rounded-2xl border border-[#E6E0D2] p-5 shadow-sm space-y-3">
          <div className="p-3 w-fit rounded-xl bg-amber-100 border border-amber-300 text-amber-900">
            <EyeOff className="w-5 h-5 text-amber-800" />
          </div>
          <h3 className="text-sm font-bold text-[#1C1917] font-mono uppercase tracking-wide">
            Zero Raw Audio Retained
          </h3>
          <p className="text-xs text-[#57534E] leading-relaxed">
            Audio never touches hard drives or persistent databases. Ingested 250ms chunks are analyzed entirely in volatile RAM buffers and immediately overwritten.
          </p>
          <div className="pt-2 text-[11px] font-mono font-bold text-amber-800 flex items-center space-x-1">
            <span>Disk Write Calls:</span>
            <span className="bg-amber-100 px-2 py-0.5 rounded">0 / sec</span>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-[#E6E0D2] p-5 shadow-sm space-y-3">
          <div className="p-3 w-fit rounded-xl bg-indigo-100 border border-indigo-300 text-indigo-900">
            <KeyRound className="w-5 h-5 text-indigo-800" />
          </div>
          <h3 className="text-sm font-bold text-[#1C1917] font-mono uppercase tracking-wide">
            Irreversible Speaker Hashing
          </h3>
          <p className="text-xs text-[#57534E] leading-relaxed">
            Repeat scammer tracking utilizes a one-way HMAC-SHA256 signature salted with an institutional master key. It is mathematically impossible to reconstruct the caller's voice from this signature.
          </p>
          <div className="pt-2 text-[11px] font-mono font-bold text-indigo-800 flex items-center space-x-1">
            <span>Algorithm:</span>
            <span className="bg-indigo-100 px-2 py-0.5 rounded font-mono">HMAC-SHA256 + Salt</span>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-[#E6E0D2] p-5 shadow-sm space-y-3">
          <div className="p-3 w-fit rounded-xl bg-emerald-100 border border-emerald-300 text-emerald-900">
            <Cpu className="w-5 h-5 text-emerald-800" />
          </div>
          <h3 className="text-sm font-bold text-[#1C1917] font-mono uppercase tracking-wide">
            150ms Strict Fail-Open Policy
          </h3>
          <p className="text-xs text-[#57534E] leading-relaxed">
            To protect telecom safety, if the neural pipeline experiences latency jitter exceeding 150ms, the packet fails open. Critical emergency calls are never blocked or delayed.
          </p>
          <div className="pt-2 text-[11px] font-mono font-bold text-emerald-800 flex items-center space-x-1">
            <span>Timeout Budget:</span>
            <span className="bg-emerald-100 px-2 py-0.5 rounded font-mono">&lt; 150 ms</span>
          </div>
        </div>
      </div>

      {/* Visual Data Flow Diagram */}
      <div className="bg-white rounded-2xl border border-[#E6E0D2] p-6 shadow-sm space-y-5">
        <div className="flex items-center justify-between border-b border-[#E6E0D2] pb-3">
          <div className="flex items-center space-x-2">
            <Layers className="w-5 h-5 text-amber-700" />
            <h2 className="text-sm font-bold text-[#1C1917] uppercase tracking-wider font-mono">
              Privacy-by-Design Data Flow Pipeline
            </h2>
          </div>
          <span className="text-[10px] font-mono font-bold px-2.5 py-1 rounded-full bg-[#FAF8F5] border border-[#E0D9CC] text-[#78716C]">
            ISO/IEC 27001 &amp; DPDP 2023 ALIGNED
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="p-4 rounded-xl bg-[#FAF8F5] border border-[#E6E0D2] space-y-2">
            <div className="text-[10px] font-mono font-bold text-[#78716C] uppercase">Step 1 • Ingestion</div>
            <p className="text-xs font-bold text-[#1C1917]">Encrypted Telemetry</p>
            <p className="text-[11px] text-[#57534E] leading-relaxed">
              Browser mic or SIP trunk audio streams over TLS/WSS in 250ms chunks. No persistent disk cache exists on the gateway.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#FAF8F5] border border-[#E6E0D2] space-y-2">
            <div className="text-[10px] font-mono font-bold text-[#78716C] uppercase">Step 2 • RAM Buffer</div>
            <p className="text-xs font-bold text-[#1C1917]">Ephemeral Ring Memory</p>
            <p className="text-[11px] text-[#57534E] leading-relaxed">
              1.5-second sliding window holds active voice frames in volatile memory for acoustic DSP feature extraction.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#FAF8F5] border border-[#E6E0D2] space-y-2">
            <div className="text-[10px] font-mono font-bold text-[#78716C] uppercase">Step 3 • Inference</div>
            <p className="text-xs font-bold text-[#1C1917]">AASIST-L Graph Attention</p>
            <p className="text-[11px] text-[#57534E] leading-relaxed">
              AntiSpoofNet detects vocoder artifacts and pitch contours. Raw audio frames are immediately cleared from RAM.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-300 space-y-2">
            <div className="text-[10px] font-mono font-bold text-emerald-800 uppercase">Step 4 • Score Out</div>
            <p className="text-xs font-bold text-emerald-900">Zeroed &amp; Deallocated</p>
            <p className="text-[11px] text-emerald-800 leading-relaxed">
              Only the 0-100 risk score and HMAC signature are transmitted to the user and bank webhook. 0 bytes retained.
            </p>
          </div>
        </div>
      </div>

      {/* DPDP Act 2023 Compliance Matrix */}
      <div className="bg-white rounded-2xl border border-[#E6E0D2] p-6 shadow-sm space-y-5">
        <div className="flex items-center space-x-2 border-b border-[#E6E0D2] pb-3">
          <Server className="w-5 h-5 text-indigo-700" />
          <h2 className="text-sm font-bold text-[#1C1917] uppercase tracking-wider font-mono">
            Digital Personal Data Protection (DPDP) Act 2023 Alignment
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {dpdpPillars.map((p) => (
            <div key={p.section} className="p-4 rounded-xl bg-[#FAF8F5] border border-[#E6E0D2] space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                  {p.section}
                </span>
                <span className="text-[10px] font-mono font-bold text-emerald-700 flex items-center space-x-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                  <span>{p.status}</span>
                </span>
              </div>
              <h3 className="text-xs font-bold text-[#1C1917] pt-1">{p.title}</h3>
              <p className="text-[11px] text-[#57534E] leading-relaxed">{p.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Retention Schedule Table */}
      <div className="bg-white rounded-2xl border border-[#E6E0D2] p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-[#E6E0D2] pb-3">
          <div className="flex items-center space-x-2">
            <Clock className="w-5 h-5 text-amber-700" />
            <h2 className="text-sm font-bold text-[#1C1917] uppercase tracking-wider font-mono">
              Official Data Retention &amp; Lifecycle Schedule
            </h2>
          </div>
          <span className="text-[10px] font-mono text-[#78716C]">Schedule ID: RET-2024-V1</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#E6E0D2] text-[#78716C] font-mono text-[10px] uppercase">
                <th className="py-2.5 px-3">Data Category</th>
                <th className="py-2.5 px-3">Storage Layer</th>
                <th className="py-2.5 px-3">Retention Duration</th>
                <th className="py-2.5 px-3">DPDP Act Alignment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E6E0D2] font-mono text-[11px]">
              {retentionPolicy.map((row, idx) => (
                <tr key={idx} className="hover:bg-[#FAF8F5] transition-colors">
                  <td className="py-3 px-3 font-semibold text-[#1C1917]">{row.data_type}</td>
                  <td className="py-3 px-3 text-[#57534E]">{row.storage_location}</td>
                  <td className="py-3 px-3">
                    <span className={`px-2 py-0.5 rounded font-bold ${
                      row.retention_period.startsWith('0 ms')
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                        : 'bg-stone-100 text-stone-800 border border-stone-300'
                    }`}>
                      {row.retention_period}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-[#78716C]">{row.dpdp_alignment}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Security Architecture & SECURITY.md Link */}
      <div className="bg-stone-900 text-stone-100 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border border-stone-800">
        <div className="space-y-1.5">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
            <h3 className="text-sm font-bold font-mono tracking-wide uppercase text-amber-300">
              Complete Threat Model &amp; Security Policy (SECURITY.md)
            </h3>
          </div>
          <p className="text-xs text-stone-400 max-w-2xl leading-relaxed">
            Read our full threat modeling matrix detailing adversary profiles, Red-Team Lab evasion attacks, residual risks, and vulnerability disclosure SLAs.
          </p>
        </div>

        <a
          href="https://github.com/Trivikram-The-Techie/TrustCall/blob/main/SECURITY.md"
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 inline-flex items-center space-x-2 px-4 py-2.5 bg-amber-400 hover:bg-amber-300 text-stone-950 rounded-xl font-mono font-bold text-xs shadow-md transition-all"
        >
          <span>View SECURITY.md</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>
    </div>
  );
}
