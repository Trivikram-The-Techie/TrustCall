import React, { useState, useEffect } from 'react';
import { Shield, AlertOctagon, Clock, Phone, Lock, RefreshCw, ExternalLink, CheckCircle2, Ban } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function BankWebhookPage() {
  const [demoState, setDemoState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [manualInput, setManualInput] = useState({
    session_id: 'demo-session',
    risk_score: 92,
    verdict: 'Critical',
    caller_number: '+91 8800012345',
    account_last4: '4321',
    amount: '₹50,000',
  });
  const [manualResult, setManualResult] = useState(null);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    fetchDemoState();
  }, []);

  const fetchDemoState = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API}/v1/alert/bank-webhook/demo`);
      const data = await resp.json();
      setDemoState(data);
    } catch (e) {
      setError('Could not reach backend. Is the server running?');
    } finally {
      setLoading(false);
    }
  };

  const triggerWebhook = async () => {
    setSending(true);
    setManualResult(null);
    try {
      const resp = await fetch(`${API}/v1/alert/bank-webhook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(manualInput),
      });
      const data = await resp.json();
      setManualResult(data);
    } catch (e) {
      setManualResult({ error: 'Request failed — is backend running?' });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] p-6">
      <div className="max-w-4xl mx-auto space-y-6">

        {/* Header */}
        <div className="text-center">
          <div className="inline-flex items-center space-x-2 bg-rose-50 border border-rose-200 rounded-full px-4 py-1.5 mb-4">
            <Ban className="w-3.5 h-3.5 text-rose-600" />
            <span className="text-xs font-mono font-bold text-rose-700 uppercase tracking-wider">
              SIMULATED DEMO — No real bank integration
            </span>
          </div>
          <h1 className="text-2xl font-bold text-[#1C1917]">Bank Webhook Consumer</h1>
          <p className="text-sm text-[#78716C] mt-1">
            Demonstrates how a bank-side system receives TrustCall alerts and places transactions on hold.
          </p>
        </div>

        {/* Demo State Panel */}
        {loading ? (
          <div className="text-center py-12 text-[#78716C]">Loading demo state…</div>
        ) : error ? (
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 text-rose-800 text-sm">{error}</div>
        ) : demoState && (
          <div className="bg-white border-2 border-rose-300 rounded-2xl p-6 shadow-lg">
            {/* Transaction Held Banner */}
            <div className="flex items-center justify-between mb-5 pb-4 border-b border-[#E6E0D2]">
              <div className="flex items-center space-x-3">
                <div className="p-3 bg-rose-100 rounded-xl border border-rose-300">
                  <Lock className="w-6 h-6 text-rose-700" />
                </div>
                <div>
                  <p className="text-xs font-mono text-rose-600 uppercase tracking-wider font-bold">Bank Action</p>
                  <h2 className="text-xl font-bold text-rose-800">TRANSACTION HELD</h2>
                </div>
              </div>
              <span className="bg-rose-600 text-white text-xs font-mono font-bold px-3 py-1.5 rounded-full">
                {demoState.hold_id}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-5">
              <InfoCard label="Hold Amount" value={demoState.hold_amount} highlight />
              <InfoCard label="Account (last 4)" value={`****${demoState.account_last4}`} />
              <InfoCard label="Caller Flagged" value={demoState.caller_flagged} highlight />
              <InfoCard label="Risk Level" value={demoState.hold_reason?.split(':')[1]?.trim() || '—'} />
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4">
              <p className="text-xs font-mono font-bold text-amber-800 uppercase tracking-wider mb-1">
                Recommended Action
              </p>
              <p className="text-sm text-amber-900">{demoState.recommended_action}</p>
            </div>

            <div className="bg-stone-50 border border-stone-200 rounded-xl p-3">
              <p className="text-[10px] font-mono text-stone-500">
                ⚠ {demoState.disclaimer}
              </p>
            </div>

            <button
              onClick={fetchDemoState}
              className="mt-4 flex items-center space-x-1.5 text-xs text-[#78716C] hover:text-[#1C1917] transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh demo state</span>
            </button>
          </div>
        )}

        {/* Webhook Trigger Simulator */}
        <div className="bg-white border border-[#E6E0D2] rounded-2xl p-6 shadow-sm">
          <div className="flex items-center space-x-2 mb-4 pb-3 border-b border-[#E6E0D2]">
            <div className="p-2 bg-amber-100 rounded-xl border border-amber-300">
              <ExternalLink className="w-4 h-4 text-amber-800" />
            </div>
            <h2 className="text-sm font-bold text-[#1C1917] uppercase font-mono tracking-wider">
              POST /v1/alert/bank-webhook — Trigger Simulator
            </h2>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-4">
            {[
              { key: 'session_id', label: 'Session ID' },
              { key: 'risk_score', label: 'Risk Score', type: 'number' },
              { key: 'verdict', label: 'Verdict' },
              { key: 'caller_number', label: 'Caller Number' },
              { key: 'account_last4', label: 'Account Last 4' },
              { key: 'amount', label: 'Hold Amount' },
            ].map(({ key, label, type }) => (
              <div key={key}>
                <label className="text-[10px] font-mono uppercase text-[#78716C] block mb-1">{label}</label>
                <input
                  type={type || 'text'}
                  value={manualInput[key]}
                  onChange={(e) => setManualInput((p) => ({ ...p, [key]: type === 'number' ? Number(e.target.value) : e.target.value }))}
                  className="w-full px-3 py-1.5 text-xs border border-[#E6E0D2] rounded-lg bg-[#FAF8F5] text-[#1C1917] font-mono focus:outline-none focus:ring-1 focus:ring-amber-400"
                />
              </div>
            ))}
          </div>

          <button
            onClick={triggerWebhook}
            disabled={sending}
            className="px-4 py-2 bg-rose-600 text-white text-xs font-mono font-bold rounded-xl hover:bg-rose-700 disabled:opacity-50 transition-colors"
          >
            {sending ? 'Sending…' : 'POST Webhook (SIMULATED)'}
          </button>

          {manualResult && (
            <div className="mt-4 bg-[#FAF8F5] border border-[#E6E0D2] rounded-xl p-3 overflow-auto max-h-64">
              <p className="text-[10px] font-mono font-bold text-[#78716C] uppercase mb-2">Response:</p>
              <pre className="text-[11px] text-[#1C1917] font-mono whitespace-pre-wrap">
                {JSON.stringify(manualResult, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Alert Payload Schema */}
        <div className="bg-white border border-[#E6E0D2] rounded-2xl p-6 shadow-sm">
          <h2 className="text-sm font-bold text-[#1C1917] uppercase font-mono tracking-wider mb-3">
            Alert Payload Schema
          </h2>
          <pre className="text-[11px] text-[#1C1917] font-mono bg-[#FAF8F5] border border-[#E6E0D2] rounded-xl p-4 overflow-auto">
{`POST /v1/alert/bank-webhook
{
  "session_id": "string",
  "risk_score": 0–100,
  "verdict": "High" | "Critical",
  "caller_number": "E.164 string",
  "account_last4": "4-digit string",
  "amount": "formatted amount string"
}

Response:
{
  "simulated": true,
  "disclaimer": "SIMULATED DEMO…",
  "hold_id": "HOLD-XXXXXXXXXXXX",
  "timestamp": "ISO 8601",
  "bank_action": "TRANSACTION_HELD",
  "hold_reason": "TrustCall risk alert: Critical (92/100)",
  "recommended_action": "...",
  "release_url": "/v1/alert/bank-webhook/release (SIMULATED)"
}`}
          </pre>
        </div>

      </div>
    </div>
  );
}

function InfoCard({ label, value, highlight }) {
  return (
    <div className={`p-3 rounded-xl border ${highlight ? 'bg-rose-50 border-rose-200' : 'bg-[#FAF8F5] border-[#E6E0D2]'}`}>
      <p className="text-[10px] font-mono uppercase text-[#78716C] mb-0.5">{label}</p>
      <p className={`text-sm font-bold font-mono ${highlight ? 'text-rose-800' : 'text-[#1C1917]'}`}>{value}</p>
    </div>
  );
}
