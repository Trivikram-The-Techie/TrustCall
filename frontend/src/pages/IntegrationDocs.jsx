import React, { useState } from 'react';
import { Code, Copy, Check, Terminal, Smartphone, Globe, Shield, Webhook } from 'lucide-react';

export default function IntegrationDocs() {
  const [copiedId, setCopiedId] = useState(null);

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const jsSnippet = `// 5-Line Bank / WebRTC Integration with VoiceShield SDK
import VoiceShieldClient from './voiceshield-sdk';

const shield = new VoiceShieldClient({ baseUrl: "https://api.voiceshield.bank" });

shield.connectStream({
  onScore: (telemetry) => updateRiskGauge(telemetry.risk_score),
  onAlert: (alert) => {
    if (alert.verdict === 'Critical') terminateCallAndLockAccount();
  }
});

// Stream raw audio chunks from WebRTC call peer
peerConnection.ontrack = (event) => shield.sendAudioChunk(event.audioChunk);`;

  const androidSnippet = `// Android Kotlin Integration for Banking App Call Screening
val shield = VoiceShieldClient(baseUrl = "https://api.voiceshield.bank")

shield.listener = object : VoiceShieldClient.ScoreListener {
    override fun onScoreUpdate(riskScore: Int, verdict: String, explanation: String) {
        updateCallOverlay(riskScore, verdict)
    }
    override fun onAlertTriggered(alertTier: String, actionRecommendation: String) {
        if (alertTier == "Critical") promptEmergencyHangup()
    }
}
shield.startStreamingSession()`;

  const restCurl = `# Instant Single-Clip Scoring REST API
curl -X POST "http://localhost:8000/v1/score" \\
  -H "Content-Type: application/json" \\
  -d '{
    "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAA...",
    "sample_rate": 16000,
    "language_hint": "hi",
    "text_transcript": "Transfer money now OTP code",
    "caller_metadata": { "is_unknown_number": true }
  }'`;

  const webhookJson = `// Enterprise Webhook Payload (Dispatched to Bank Fraud Gateway on Critical Alert)
{
  "event": "CRITICAL_IMPERSONATION_DETECTED",
  "session_id": "f83a21b4-793e-4b21-8172-e192931a9801",
  "timestamp": 1725372400,
  "risk_score": 92,
  "alert_tier": "Critical",
  "recommended_action": "TERMINATE_CALL_AND_LOCK_ACCOUNT",
  "forensic_breakdown": {
    "vocoder_confidence": 0.88,
    "pitch_flatness": 0.91,
    "coercion_keywords": ["transfer money", "OTP", "CBI"]
  },
  "speaker_hash_sha256": "4b68e9182390a1f0c29302e1..."
}`;

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Overview Banner */}
      <div className="bg-[#111827] border border-slate-800 rounded-xl p-6 shadow-xl">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-100">Enterprise & Telecom Integration Surface</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Deployable directly into bank mobile applications, enterprise PBX switches, telecom carrier gateways, and customer support softphones.
            </p>
          </div>
        </div>
      </div>

      {/* Code Snippets */}
      <div className="space-y-6">
        {/* JS SDK */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          <div className="flex items-center justify-between px-4 py-3 bg-[#0B0F19] border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <Globe className="w-4 h-4 text-blue-400" />
              <span className="text-xs font-semibold text-slate-200">5-Line JavaScript / WebRTC Client SDK</span>
            </div>
            <button
              onClick={() => copyToClipboard(jsSnippet, 'js')}
              className="flex items-center space-x-1 text-xs text-slate-400 hover:text-slate-200"
            >
              {copiedId === 'js' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedId === 'js' ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <pre className="p-4 text-xs font-mono text-cyan-300 bg-[#0B0F19]/80 overflow-x-auto">
            {jsSnippet}
          </pre>
        </div>

        {/* Android SDK */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          <div className="flex items-center justify-between px-4 py-3 bg-[#0B0F19] border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <Smartphone className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-semibold text-slate-200">Android Kotlin SDK (Banking Dialer Integration)</span>
            </div>
            <button
              onClick={() => copyToClipboard(androidSnippet, 'android')}
              className="flex items-center space-x-1 text-xs text-slate-400 hover:text-slate-200"
            >
              {copiedId === 'android' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedId === 'android' ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <pre className="p-4 text-xs font-mono text-emerald-300 bg-[#0B0F19]/80 overflow-x-auto">
            {androidSnippet}
          </pre>
        </div>

        {/* REST API cURL */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          <div className="flex items-center justify-between px-4 py-3 bg-[#0B0F19] border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-amber-400" />
              <span className="text-xs font-semibold text-slate-200">cURL REST Endpoint (Single Clip / IVR Scoring)</span>
            </div>
            <button
              onClick={() => copyToClipboard(restCurl, 'curl')}
              className="flex items-center space-x-1 text-xs text-slate-400 hover:text-slate-200"
            >
              {copiedId === 'curl' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedId === 'curl' ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <pre className="p-4 text-xs font-mono text-amber-200 bg-[#0B0F19]/80 overflow-x-auto">
            {restCurl}
          </pre>
        </div>

        {/* Bank Fraud Gateway Webhook */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          <div className="flex items-center justify-between px-4 py-3 bg-[#0B0F19] border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <Webhook className="w-4 h-4 text-rose-400" />
              <span className="text-xs font-semibold text-slate-200">Automated Bank Fraud Webhook Schema</span>
            </div>
            <button
              onClick={() => copyToClipboard(webhookJson, 'webhook')}
              className="flex items-center space-x-1 text-xs text-slate-400 hover:text-slate-200"
            >
              {copiedId === 'webhook' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedId === 'webhook' ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <pre className="p-4 text-xs font-mono text-rose-300 bg-[#0B0F19]/80 overflow-x-auto">
            {webhookJson}
          </pre>
        </div>
      </div>
    </div>
  );
}
