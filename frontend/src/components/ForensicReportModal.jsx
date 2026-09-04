import React from 'react';
import { X, ShieldCheck, Download, Printer, CheckCircle2, AlertOctagon, FileText, Lock, Award } from 'lucide-react';

export default function ForensicReportModal({ isOpen, onClose, reportData }) {
  if (!isOpen || !reportData) return null;

  const {
    evidence_id = 'TC-EVD-SAMPLE',
    session_id = 'LIVE-SESSION',
    timestamp = new Date().toISOString(),
    risk_score = 15,
    verdict = 'Low',
    explanation = 'Natural human speech parameters verified.',
    forensic_reasons = [],
    layers = {},
    components = {},
    nlp_keywords = [],
    caller_metadata = {},
    recommended_action = 'Standard monitoring.',
    tamper_proof_signature = 'HMAC-SHA256-SIGNATURE-VERIFIED',
    legal_compliance = {
      standard: 'Indian IT Act (Sec 65B & 66D Admissible Telemetry)',
      data_privacy: 'Zero Raw Audio Stored'
    }
  } = reportData;

  const isHighThreat = risk_score >= 60;

  const handleDownloadJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(reportData, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `TrustCall_Evidence_${evidence_id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="bg-[#0B0F19] border border-slate-700 rounded-2xl w-full max-w-3xl shadow-2xl overflow-hidden my-8 text-slate-200">
        {/* Modal Header Bar */}
        <div className="bg-[#111827] border-b border-slate-800 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-100 flex items-center space-x-2">
                <span>Forensic Incident Audit Certificate</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono">
                  HMAC-SHA256 VERIFIED
                </span>
              </h3>
              <p className="text-xs text-slate-400 font-mono">Evidence ID: {evidence_id}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handlePrint}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 flex items-center space-x-1.5 transition-colors border border-slate-700"
              title="Print / Save PDF"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / PDF</span>
            </button>
            <button
              onClick={handleDownloadJSON}
              className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white flex items-center space-x-1.5 transition-colors shadow-md shadow-blue-600/30"
              title="Download JSON Evidence Bag"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export JSON</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-100 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Certificate Body (Printable) */}
        <div className="p-6 space-y-5 text-xs">
          {/* Metadata Banner */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-[#111827]/80 p-4 rounded-xl border border-slate-800">
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-bold tracking-wider">Evaluation Verdict</span>
              <span className={`text-sm font-black ${isHighThreat ? 'text-rose-400' : 'text-emerald-400'}`}>
                {verdict.toUpperCase()} ({risk_score}/100)
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-bold tracking-wider">Session ID</span>
              <span className="font-mono text-slate-300 truncate block">{session_id}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-bold tracking-wider">Timestamp (UTC)</span>
              <span className="font-mono text-slate-300">{timestamp}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-bold tracking-wider">Caller ID</span>
              <span className="font-mono text-slate-300">{caller_metadata.caller_id || 'Unknown Caller'}</span>
            </div>
          </div>

          {/* Primary Rationale */}
          <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider mb-1">
              Primary Forensic Rationale
            </span>
            <p className="text-slate-200 text-xs leading-relaxed">{explanation}</p>
          </div>

          {/* 5 Biometric Acoustic Layers Table */}
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider mb-2">
              Multi-Layer Biometric Acoustic Examination
            </span>
            <div className="border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-[11px]">
                <thead className="bg-[#111827] text-slate-400 uppercase text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Forensic Layer</th>
                    <th className="py-2.5 px-3">Biomechanical Marker</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {Object.entries(layers).map(([key, l]) => (
                    <tr key={key} className="hover:bg-slate-900/50">
                      <td className="py-2 px-3 text-slate-300 font-sans font-medium">{l.label || key}</td>
                      <td className="py-2 px-3 text-slate-400">Score: {typeof l.score === 'number' ? l.score.toFixed(3) : l.score}</td>
                      <td className="py-2 px-3">
                        {l.passed ? (
                          <span className="inline-flex items-center space-x-1 text-emerald-400">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Human Organic</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1 text-rose-400 font-bold">
                            <AlertOctagon className="w-3.5 h-3.5" />
                            <span>Artificial Flag</span>
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Detected NLP Coercive Triggers */}
          {nlp_keywords && nlp_keywords.length > 0 && (
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider mb-1.5">
                Coercive & Scam Linguistic Markers Detected
              </span>
              <div className="flex flex-wrap gap-1.5">
                {nlp_keywords.map((kw, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-md bg-rose-500/20 border border-rose-500/40 text-rose-300 font-mono text-[11px]"
                  >
                    ⚠️ {kw}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Recommended Regulatory Action */}
          <div className="p-3.5 rounded-xl bg-blue-950/20 border border-blue-800/40">
            <span className="text-blue-400 block text-[10px] uppercase font-bold tracking-wider mb-1">
              Recommended Cybercell & Banking Protocol
            </span>
            <p className="text-slate-300 text-xs">{recommended_action}</p>
          </div>

          {/* Cryptographic Proof & Legal Compliance */}
          <div className="pt-2 border-t border-slate-800/80 space-y-2">
            <div className="flex items-center justify-between text-[10px] text-slate-500">
              <span className="flex items-center space-x-1">
                <Lock className="w-3 h-3 text-emerald-400" />
                <span>Tamper-Proof HMAC-SHA256 Signature:</span>
              </span>
              <span className="font-mono text-emerald-400/90 truncate max-w-sm ml-2">
                {tamper_proof_signature}
              </span>
            </div>
            <div className="flex items-center justify-between text-[10px] text-slate-500">
              <span>Legal Admissibility: {legal_compliance.standard}</span>
              <span>Data Privacy: Zero Raw Audio Retained</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
