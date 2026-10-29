import React, { useState, useEffect } from 'react';
import { 
  Skull, 
  ShieldAlert, 
  ShieldCheck, 
  AlertTriangle, 
  Zap, 
  Sliders, 
  Radio, 
  RefreshCw, 
  FileAudio, 
  UploadCloud,
  CheckCircle2,
  Info,
  Layers,
  Activity,
  ArrowRight
} from 'lucide-react';

export default function RedTeamLab() {
  const [selectedPreset, setSelectedPreset] = useState('cloned_scam');
  const [uploadedBase64, setUploadedBase64] = useState(null);
  const [uploadedFileName, setUploadedFileName] = useState('');
  const [attackType, setAttackType] = useState('codec_laundering');
  
  // Attack Parameters
  const [codec, setCodec] = useState('amr_nb');
  const [dropRate, setDropRate] = useState(0.10);
  const [snrDb, setSnrDb] = useState(10.0);
  const [noiseType, setNoiseType] = useState('ambient');
  const [roomSize, setRoomSize] = useState('medium');
  const [spliceRatio, setSpliceRatio] = useState(0.50);
  const [spliceMode, setSpliceMode] = useState('prefix_suffix');

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const runAttack = async () => {
    setLoading(true);
    setError(null);

    const payload = {
      preset_id: uploadedBase64 ? null : selectedPreset,
      audio_base64: uploadedBase64,
      attack_type: attackType,
      parameters: {}
    };

    if (attackType === 'codec_laundering') payload.parameters = { codec };
    else if (attackType === 'packet_loss') payload.parameters = { drop_rate: Number(dropRate) };
    else if (attackType === 'noise_mix') payload.parameters = { snr_db: Number(snrDb), noise_type: noiseType };
    else if (attackType === 're_recording') payload.parameters = { room_size: roomSize };
    else if (attackType === 'splicing') payload.parameters = { splice_ratio: Number(spliceRatio), splice_mode: spliceMode };

    try {
      const res = await fetch('/v1/redteam/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error('Red team attack failed:', err);
      setError('Attack simulation failed. Ensure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runAttack();
  }, [attackType, selectedPreset]);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadedFileName(file.name);
    const reader = new FileReader();
    reader.onload = (event) => {
      const b64 = event.target.result.split(',')[1];
      setUploadedBase64(b64);
    };
    reader.readAsDataURL(file);
  };

  const clearUpload = () => {
    setUploadedBase64(null);
    setUploadedFileName('');
    setSelectedPreset('cloned_scam');
  };

  // Helper to draw SVG waveform path from downsampled points
  const renderWaveformSvg = (points = [], color = '#6366F1') => {
    if (!points || points.length === 0) return null;
    const width = 300;
    const height = 64;
    const step = width / points.length;
    const mid = height / 2;

    const pathData = points
      .map((pt, i) => {
        const x = i * step;
        const barH = Math.max(2, pt * (height * 0.45));
        return `M ${x.toFixed(1)} ${(mid - barH).toFixed(1)} L ${x.toFixed(1)} ${(mid + barH).toFixed(1)}`;
      })
      .join(' ');

    return (
      <svg className="w-full h-16 bg-stone-900 rounded-xl overflow-hidden" viewBox={`0 0 ${width} ${height}`}>
        <path d={pathData} stroke={color} strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    );
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Title & Badge */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#E6E0D2] pb-6">
        <div>
          <div className="flex items-center space-x-2.5 mb-1.5">
            <span className="text-xs font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-900 border border-rose-300 flex items-center space-x-1.5">
              <Skull className="w-3.5 h-3.5 text-rose-700" />
              <span>SIMULATED RED-TEAM ATTACK LAB</span>
            </span>
            <span className="text-xs font-mono font-semibold text-stone-500">
              Adversarial Stress Testing
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#1C1917] tracking-tight">
            Red-Team Evasion & Mitigation Lab
          </h1>
          <p className="text-sm text-[#78716C] mt-1 max-w-2xl">
            Simulate realistic telecommunications attacks and physical re-recording against voice clone detection. Compare baseline detector evasion with active CUSUM and burst-pooling mitigation.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono px-3 py-1.5 rounded-xl bg-white border border-[#E6E0D2] text-[#44403C] shadow-sm flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Active Mitigation: CUSUM + Max-Burst</span>
          </span>
        </div>
      </div>

      {/* Main Grid: Controls on Top, Side-by-Side Results Below */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Source Audio Selector */}
        <div className="bg-white rounded-2xl p-5 border border-[#E6E0D2] shadow-sm space-y-4">
          <h3 className="text-xs font-mono uppercase tracking-wider font-bold text-[#57534E] flex items-center space-x-1.5">
            <Radio className="w-3.5 h-3.5 text-amber-700" />
            <span>1. Audio Input Source</span>
          </h3>

          <div className="space-y-2">
            <button
              onClick={() => { setSelectedPreset('cloned_scam'); setUploadedBase64(null); }}
              className={`w-full text-left p-3 rounded-xl border text-xs transition-all ${
                selectedPreset === 'cloned_scam' && !uploadedBase64
                  ? 'bg-rose-50 border-rose-300 font-semibold text-rose-950 shadow-sm'
                  : 'bg-stone-50 border-[#E6E0D2] text-[#44403C] hover:bg-white'
              }`}
            >
              <div className="font-bold flex items-center justify-between">
                <span>Preset B: Cloned Scam Call</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-200/80 text-rose-900">Synthetic</span>
              </div>
              <p className="text-[11px] text-stone-500 mt-1">ElevenLabs vocoder impersonation sample (Score: ~92)</p>
            </button>

            <button
              onClick={() => { setSelectedPreset('genuine_call'); setUploadedBase64(null); }}
              className={`w-full text-left p-3 rounded-xl border text-xs transition-all ${
                selectedPreset === 'genuine_call' && !uploadedBase64
                  ? 'bg-emerald-50 border-emerald-300 font-semibold text-emerald-950 shadow-sm'
                  : 'bg-stone-50 border-[#E6E0D2] text-[#44403C] hover:bg-white'
              }`}
            >
              <div className="font-bold flex items-center justify-between">
                <span>Preset A: Genuine Family Call</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-200/80 text-emerald-900">Human</span>
              </div>
              <p className="text-[11px] text-stone-500 mt-1">Authentic human glottal vocal dynamics (Score: ~14)</p>
            </button>
          </div>

          {/* File Upload Option */}
          <div className="pt-2 border-t border-[#F0ECE1]">
            <label className="text-[11px] font-mono text-stone-500 block mb-1.5">Or upload custom audio clip:</label>
            <input
              type="file"
              accept="audio/*"
              onChange={handleFileUpload}
              className="text-xs file:mr-2 file:py-1 file:px-2.5 file:rounded-lg file:border file:border-stone-300 file:text-xs file:bg-stone-100 hover:file:bg-stone-200 text-stone-600 cursor-pointer w-full"
            />
            {uploadedFileName && (
              <div className="flex items-center justify-between mt-2 p-2 bg-indigo-50 border border-indigo-200 rounded-lg text-xs text-indigo-900">
                <span className="truncate max-w-[180px]">{uploadedFileName}</span>
                <button onClick={clearUpload} className="text-[10px] text-rose-600 font-bold hover:underline">Clear</button>
              </div>
            )}
          </div>
        </div>

        {/* Attack Type Selector (Takes 2 cols on lg) */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-5 border border-[#E6E0D2] shadow-sm space-y-4">
          <h3 className="text-xs font-mono uppercase tracking-wider font-bold text-[#57534E] flex items-center space-x-1.5">
            <Sliders className="w-3.5 h-3.5 text-amber-700" />
            <span>2. Select Adversarial Attack Vector</span>
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {[
              { id: 'codec_laundering', name: 'Codec Laundering', desc: 'AMR-NB / G.711 / MP3' },
              { id: 'packet_loss', name: 'RTP Packet Loss', desc: '5% / 10% / 20% drops' },
              { id: 'noise_mix', name: 'Noise / Music Mix', desc: 'Selectable SNR' },
              { id: 're_recording', name: 'Re-Recording Sim', desc: 'RIR Reverb + Speaker' },
              { id: 'splicing', name: 'Segment Splicing', desc: 'Hybrid Real/Clone Mix' }
            ].map((atk) => (
              <button
                key={atk.id}
                onClick={() => setAttackType(atk.id)}
                className={`text-left p-3 rounded-xl border text-xs transition-all ${
                  attackType === atk.id
                    ? 'bg-amber-100/70 border-amber-400 font-bold text-amber-950 shadow-sm'
                    : 'bg-stone-50 border-[#E6E0D2] text-[#44403C] hover:bg-stone-100'
                }`}
              >
                <div className="font-semibold">{atk.name}</div>
                <div className="text-[10px] text-stone-500 mt-0.5">{atk.desc}</div>
              </button>
            ))}
          </div>

          {/* Dynamic Attack Parameter Sliders / Selects */}
          <div className="p-4 rounded-xl bg-[#FAF8F5] border border-[#E6E0D2] space-y-3">
            <div className="text-xs font-mono font-bold text-stone-700 uppercase tracking-wider">
              Attack Parameters
            </div>

            {attackType === 'codec_laundering' && (
              <div className="flex flex-wrap items-center gap-4 text-xs">
                <label className="font-semibold text-stone-700">Target Codec:</label>
                {['amr_nb', 'g711', 'mp3'].map((c) => (
                  <label key={c} className="flex items-center space-x-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="codec"
                      value={c}
                      checked={codec === c}
                      onChange={(e) => setCodec(e.target.value)}
                      className="text-amber-600 focus:ring-amber-500"
                    />
                    <span className="uppercase font-mono">{c === 'amr_nb' ? 'AMR-NB (8 kHz)' : c === 'g711' ? 'G.711 μ-law' : 'MP3 MDCT'}</span>
                  </label>
                ))}
              </div>
            )}

            {attackType === 'packet_loss' && (
              <div className="flex flex-wrap items-center gap-4 text-xs">
                <label className="font-semibold text-stone-700">RTP Packet Drop Rate:</label>
                {[0.05, 0.10, 0.20].map((rate) => (
                  <label key={rate} className="flex items-center space-x-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="droprate"
                      value={rate}
                      checked={dropRate === rate}
                      onChange={(e) => setDropRate(Number(e.target.value))}
                      className="text-amber-600 focus:ring-amber-500"
                    />
                    <span className="font-mono font-bold">{rate * 100}% Loss (PLC Concealment)</span>
                  </label>
                ))}
              </div>
            )}

            {attackType === 'noise_mix' && (
              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-stone-700">Target SNR (dB):</span>
                  <span className="font-mono font-bold text-amber-900 bg-amber-100 px-2 py-0.5 rounded">{snrDb} dB</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="25"
                  step="5"
                  value={snrDb}
                  onChange={(e) => setSnrDb(Number(e.target.value))}
                  className="w-full accent-amber-600"
                />
                <div className="flex items-center space-x-4">
                  <span className="font-semibold text-stone-700">Noise Profile:</span>
                  {['ambient', 'music', 'white'].map((n) => (
                    <label key={n} className="flex items-center space-x-1 cursor-pointer">
                      <input
                        type="radio"
                        name="noisetype"
                        value={n}
                        checked={noiseType === n}
                        onChange={(e) => setNoiseType(e.target.value)}
                        className="text-amber-600 focus:ring-amber-500"
                      />
                      <span className="capitalize">{n}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {attackType === 're_recording' && (
              <div className="flex flex-wrap items-center gap-4 text-xs">
                <label className="font-semibold text-stone-700">Acoustic Room Size:</label>
                {['small', 'medium', 'large'].map((room) => (
                  <label key={room} className="flex items-center space-x-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="roomsize"
                      value={room}
                      checked={roomSize === room}
                      onChange={(e) => setRoomSize(e.target.value)}
                      className="text-amber-600 focus:ring-amber-500"
                    />
                    <span className="capitalize font-mono">{room} ({room === 'small' ? 'RT60 200ms' : room === 'medium' ? 'RT60 450ms' : 'RT60 800ms'})</span>
                  </label>
                ))}
              </div>
            )}

            {attackType === 'splicing' && (
              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-stone-700">Splice Replacement Ratio:</span>
                  <span className="font-mono font-bold text-amber-900 bg-amber-100 px-2 py-0.5 rounded">{spliceRatio * 100}%</span>
                </div>
                <input
                  type="range"
                  min="0.25"
                  max="0.75"
                  step="0.25"
                  value={spliceRatio}
                  onChange={(e) => setSpliceRatio(Number(e.target.value))}
                  className="w-full accent-amber-600"
                />
                <div className="flex flex-wrap items-center gap-3">
                  <span className="font-semibold text-stone-700">Mode:</span>
                  {[
                    { id: 'prefix_suffix', label: 'Greeting + Clone + Signoff' },
                    { id: 'interleaved', label: 'Interleaved (Real/Clone)' },
                    { id: 'silence_bursts', label: 'Silence Bursts' }
                  ].map((m) => (
                    <label key={m.id} className="flex items-center space-x-1 cursor-pointer">
                      <input
                        type="radio"
                        name="splicemode"
                        value={m.id}
                        checked={spliceMode === m.id}
                        onChange={(e) => setSpliceMode(e.target.value)}
                        className="text-amber-600 focus:ring-amber-500"
                      />
                      <span>{m.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={runAttack}
              disabled={loading}
              className="mt-2 w-full py-2.5 rounded-xl bg-[#1C1917] hover:bg-stone-800 text-amber-300 text-xs font-mono font-bold flex items-center justify-center space-x-2 shadow-sm transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Executing Attack Transformation...' : 'Run Attack Simulation & Stress Test'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Honest Evasion Verdict Callout */}
      {result && (
        <div className={`p-5 rounded-2xl border transition-all shadow-sm ${
          result.evasion_detected
            ? 'bg-amber-50/80 border-amber-300'
            : 'bg-emerald-50/80 border-emerald-300'
        }`}>
          <div className="flex items-start space-x-3.5">
            {result.evasion_detected ? (
              <AlertTriangle className="w-6 h-6 text-amber-700 flex-shrink-0 mt-0.5" />
            ) : (
              <ShieldCheck className="w-6 h-6 text-emerald-700 flex-shrink-0 mt-0.5" />
            )}
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <span className="font-mono text-xs font-extrabold uppercase tracking-wider px-2 py-0.5 rounded bg-white border border-[#E6E0D2]">
                  {result.evasion_detected ? 'DETECTOR BYPASS DEMONSTRATED' : 'BASELINE DETECTOR ROBUST'}
                </span>
                <span className="text-xs font-mono text-stone-500">
                  Latency: {result.execution_time_ms} ms
                </span>
              </div>
              <h3 className="text-sm font-bold text-[#1C1917]">
                {result.verdict_summary}
              </h3>
              <p className="text-xs text-[#57534E] leading-relaxed">
                {result.evasion_detected ? (
                  result.mitigation_effective ? (
                    <span>
                      <strong>Attack Mechanism:</strong> The attack successfully lowered the baseline rolling median score from {result.original.risk_score} down to {result.attacked_baseline.risk_score}. However, the <strong>CUSUM Anomaly Accumulator ($S_t = {result.attacked_mitigated.cusum_statistic}$)</strong> and max-burst pooling intercepted the transient synthetic burst, maintaining active threat posture ({result.attacked_mitigated.risk_score}/100 - {result.attacked_mitigated.verdict}).
                    </span>
                  ) : (
                    <span>
                      <strong>Attack Mechanism:</strong> Severe degradation degraded the signal below threshold. Population scale re-training with codec augmentation is recommended.
                    </span>
                  )
                ) : (
                  <span>
                    <strong>Resilience:</strong> AASIST-L spectral graph attention and SincNet filterbanks retained discriminative vocoder phase cues under {result.attack_description}.
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Side-by-Side Comparison: Before vs Baseline After vs Mitigated After */}
      {result && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Original Pre-Attack */}
          <div className="bg-white rounded-2xl p-5 border border-[#E6E0D2] shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#F0ECE1]">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-stone-500">
                1. Original Speech
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-100 text-stone-700">
                Pre-Attack
              </span>
            </div>

            <div className="flex items-baseline justify-between">
              <div>
                <div className="text-3xl font-mono font-extrabold text-[#1C1917]">
                  {result.original.risk_score} <span className="text-sm font-normal text-stone-400">/ 100</span>
                </div>
                <div className="text-xs font-semibold text-stone-600 mt-0.5">
                  Tier: <span style={{ color: result.original.color }}>{result.original.verdict}</span>
                </div>
              </div>
              <div className="text-right font-mono text-xs text-stone-500">
                Prob: {(result.original.model_probability * 100).toFixed(1)}%
              </div>
            </div>

            <div className="space-y-1.5">
              <span className="text-[11px] font-mono text-stone-500">Waveform Envelope:</span>
              {renderWaveformSvg(result.original.waveform, '#6366F1')}
            </div>

            <div className="pt-2 border-t border-stone-100 space-y-1 text-xs">
              <span className="text-[11px] font-mono text-stone-500 block">Spectral Profile:</span>
              <div className="grid grid-cols-3 gap-1 font-mono text-[11px] text-center">
                <div className="bg-stone-50 p-1.5 rounded border border-stone-200">
                  <div className="text-stone-400 text-[10px]">Low</div>
                  <div className="font-bold text-stone-800">{result.original.spectral.low_band_pct}%</div>
                </div>
                <div className="bg-stone-50 p-1.5 rounded border border-stone-200">
                  <div className="text-stone-400 text-[10px]">Mid</div>
                  <div className="font-bold text-stone-800">{result.original.spectral.mid_band_pct}%</div>
                </div>
                <div className="bg-stone-50 p-1.5 rounded border border-stone-200">
                  <div className="text-stone-400 text-[10px]">High</div>
                  <div className="font-bold text-stone-800">{result.original.spectral.high_band_pct}%</div>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Attacked (Baseline Detector) */}
          <div className={`bg-white rounded-2xl p-5 border shadow-sm space-y-4 ${
            result.evasion_detected ? 'border-rose-300 ring-1 ring-rose-300' : 'border-[#E6E0D2]'
          }`}>
            <div className="flex items-center justify-between pb-3 border-b border-[#F0ECE1]">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-rose-800">
                2. Attacked (Baseline)
              </span>
              <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                result.evasion_detected ? 'bg-rose-100 text-rose-900 border border-rose-300' : 'bg-stone-100 text-stone-700'
              }`}>
                {result.evasion_detected ? 'EVADED' : 'DEFENDED'}
              </span>
            </div>

            <div className="flex items-baseline justify-between">
              <div>
                <div className="text-3xl font-mono font-extrabold text-[#1C1917]">
                  {result.attacked_baseline.risk_score} <span className="text-sm font-normal text-stone-400">/ 100</span>
                </div>
                <div className="text-xs font-semibold text-stone-600 mt-0.5">
                  Tier: <span style={{ color: result.attacked_baseline.color }}>{result.attacked_baseline.verdict}</span>
                </div>
              </div>
              <div className="text-right font-mono text-xs text-stone-500">
                Prob: {(result.attacked_baseline.model_probability * 100).toFixed(1)}%
              </div>
            </div>

            <div className="space-y-1.5">
              <span className="text-[11px] font-mono text-stone-500">Degraded Waveform:</span>
              {renderWaveformSvg(result.attacked_baseline.waveform, '#F43F5E')}
            </div>

            <div className="pt-2 border-t border-stone-100 space-y-1 text-xs">
              <span className="text-[11px] font-mono text-stone-500 block">Attacked Spectral Profile:</span>
              <div className="grid grid-cols-3 gap-1 font-mono text-[11px] text-center">
                <div className="bg-stone-50 p-1.5 rounded border border-stone-200">
                  <div className="text-stone-400 text-[10px]">Low</div>
                  <div className="font-bold text-stone-800">{result.attacked_baseline.spectral.low_band_pct}%</div>
                </div>
                <div className="bg-stone-50 p-1.5 rounded border border-stone-200">
                  <div className="text-stone-400 text-[10px]">Mid</div>
                  <div className="font-bold text-stone-800">{result.attacked_baseline.spectral.mid_band_pct}%</div>
                </div>
                <div className="bg-stone-50 p-1.5 rounded border border-stone-200">
                  <div className="text-stone-400 text-[10px]">High</div>
                  <div className="font-bold text-stone-800">{result.attacked_baseline.spectral.high_band_pct}%</div>
                </div>
              </div>
            </div>
          </div>

          {/* Card 3: Attacked (Mitigated Active Defense) */}
          <div className="bg-white rounded-2xl p-5 border border-emerald-300 ring-1 ring-emerald-300 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#F0ECE1]">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-800">
                3. Attacked (Mitigated)
              </span>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-900 border border-emerald-300">
                ACTIVE DEFENSE
              </span>
            </div>

            <div className="flex items-baseline justify-between">
              <div>
                <div className="text-3xl font-mono font-extrabold text-emerald-800">
                  {result.attacked_mitigated.risk_score} <span className="text-sm font-normal text-stone-400">/ 100</span>
                </div>
                <div className="text-xs font-semibold text-stone-600 mt-0.5">
                  Tier: <span style={{ color: result.attacked_mitigated.color }}>{result.attacked_mitigated.verdict}</span>
                </div>
              </div>
              <div className="text-right font-mono text-xs text-stone-500">
                Prob: {(result.attacked_mitigated.model_probability * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-emerald-50/60 p-3 rounded-xl border border-emerald-200 space-y-2 text-xs">
              <div className="flex items-center justify-between font-mono">
                <span className="text-emerald-950 font-semibold">CUSUM Anomaly Stat:</span>
                <span className="font-bold text-emerald-800">{result.attacked_mitigated.cusum_statistic}</span>
              </div>
              <div className="flex items-center justify-between font-mono">
                <span className="text-emerald-950 font-semibold">Burst Alarm Latched:</span>
                <span className={`px-2 py-0.2 rounded font-bold ${
                  result.attacked_mitigated.burst_detected ? 'bg-emerald-200 text-emerald-950' : 'bg-stone-200 text-stone-700'
                }`}>
                  {result.attacked_mitigated.burst_detected ? 'LATCHED' : 'CLEAR'}
                </span>
              </div>
              <div className="text-[11px] text-emerald-900 pt-1 border-t border-emerald-200/60">
                Combines CUSUM change-point accumulator + max-window pooling to prevent burst dilution.
              </div>
            </div>

            <div className="pt-2 border-t border-stone-100 space-y-1 text-xs text-[#57534E]">
              <span className="text-[11px] font-mono text-stone-500 block">Defense Mechanisms:</span>
              <ul className="list-disc list-inside space-y-1 text-[11px] text-stone-600">
                <li>Telephony bandpass pre-emphasis filter</li>
                <li>Waveform median dither sanitizer</li>
                <li>Max-window pooling (retains peak threat)</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Methodology & Red-Team Documentation Callout */}
      <div className="bg-[#FAF8F5] border border-[#E0D8C8] rounded-2xl p-6 shadow-sm">
        <div className="flex items-start space-x-3.5">
          <Info className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
          <div className="space-y-2 text-xs text-[#44403C]">
            <h3 className="text-sm font-bold text-[#1C1917]">
              Adversarial Threat Modeling & Mitigation Philosophy
            </h3>
            <p className="leading-relaxed">
              In real-world cybercrime operations across India, scammers rarely transmit clean uncompressed WAV audio. They utilize VoIP PBX trunks, low-bitrate mobile codecs (AMR-NB), acoustic loudspeakers, or interleave genuine human conversational greetings with brief cloned extortion payloads.
            </p>
            <p className="leading-relaxed">
              Standard anti-spoofing systems rely on rolling median filters that completely wash out brief synthetic bursts (dilution evasion). TrustCall VoiceShield addresses this vulnerability via a <strong>dual-path CUSUM accumulator and max-window pooling architecture</strong>, ensuring that any high-confidence synthetic burst is immediately latched and escalated to the threat gauge.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
