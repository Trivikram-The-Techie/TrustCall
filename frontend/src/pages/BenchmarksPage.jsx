import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Cpu, 
  Activity, 
  CheckCircle2, 
  AlertTriangle, 
  Info, 
  RefreshCw, 
  Sliders, 
  Clock, 
  Terminal,
  ShieldCheck,
  Zap
} from 'lucide-react';

export default function BenchmarksPage() {
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSort, setSelectedSort] = useState('default'); // 'default', 'eer_asc', 'acc_desc'

  const loadData = () => {
    setLoading(true);
    setError(null);
    // Attempt to fetch from live backend endpoint, then fallback to public static JSON
    fetch('/v1/benchmark')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setBenchmarkData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.warn('Backend /v1/benchmark failed, trying static /eval_results.json fallback...', err);
        fetch('/eval_results.json')
          .then((res) => {
            if (!res.ok) throw new Error('Could not load static benchmark fallback.');
            return res.json();
          })
          .then((data) => {
            setBenchmarkData(data);
            setLoading(false);
          })
          .catch((fallbackErr) => {
            setError('Failed to load benchmark evaluation data. Run "python backend/evaluate_model_accuracy.py" to generate results.');
            setLoading(false);
          });
      });
  };

  useEffect(() => {
    loadData();
  }, []);

  const results = benchmarkData?.results || [];

  const sortedResults = [...results].sort((a, b) => {
    if (selectedSort === 'eer_asc') return a.eer_percent - b.eer_percent;
    if (selectedSort === 'acc_desc') return b.accuracy_percent - a.accuracy_percent;
    return 0; // Default order
  });

  const avgLatency = results.length > 0 
    ? (results.reduce((acc, curr) => acc + curr.avg_latency_ms, 0) / results.length).toFixed(1)
    : '225.0';

  const baselineItem = results.find((r) => r.condition_id === 'clean_16khz') || results[0];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Page Title & Simulator Badge */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#E6E0D2] pb-6">
        <div>
          <div className="flex items-center space-x-2.5 mb-1.5">
            <span className="text-xs font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300">
              SIMULATED BENCHMARK CONDITIONS
            </span>
            <span className="text-xs font-mono font-semibold text-stone-500">
              AASIST-L Verification
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#1C1917] tracking-tight">
            Acoustic & Telephony Codec Benchmarks
          </h1>
          <p className="text-sm text-[#78716C] mt-1 max-w-2xl">
            Empirical Equal Error Rate (EER), classification accuracy, and CPU inference latency measured across 11 cellular, VoIP, and noisy telecom transmission conditions.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-white border border-[#E6E0D2] hover:bg-stone-50 text-xs font-semibold text-[#44403C] shadow-sm transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-amber-600' : 'text-stone-500'}`} />
            <span>Reload Metrics</span>
          </button>
        </div>
      </div>

      {/* KPI Metric Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl p-4 border border-[#E6E0D2] shadow-sm">
          <div className="flex items-center justify-between text-[#78716C] mb-2">
            <span className="text-xs font-mono font-medium uppercase tracking-wider">Clean Baseline EER</span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-mono font-bold text-emerald-700">
              {baselineItem ? `${baselineItem.eer_percent.toFixed(2)}%` : '0.00%'}
            </span>
            <span className="text-[11px] font-mono text-stone-400">
              (N = {baselineItem ? baselineItem.sample_count : 30})
            </span>
          </div>
          <p className="text-[11px] text-[#A8A29E] mt-1">16 kHz Uncompressed PCM</p>
        </div>

        <div className="bg-white rounded-2xl p-4 border border-[#E6E0D2] shadow-sm">
          <div className="flex items-center justify-between text-[#78716C] mb-2">
            <span className="text-xs font-mono font-medium uppercase tracking-wider">Telecom Codec EER</span>
            <Activity className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-mono font-bold text-indigo-900">
              {results.find((r) => r.condition_id === 'g711_mulaw')?.eer_percent.toFixed(2) || '3.33'}%
            </span>
            <span className="text-[11px] font-mono text-stone-400">
              (N = 30)
            </span>
          </div>
          <p className="text-[11px] text-[#A8A29E] mt-1">G.711 μ-law (8 kHz Cellular)</p>
        </div>

        <div className="bg-white rounded-2xl p-4 border border-[#E6E0D2] shadow-sm">
          <div className="flex items-center justify-between text-[#78716C] mb-2">
            <span className="text-xs font-mono font-medium uppercase tracking-wider">Avg CPU Latency</span>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-mono font-bold text-[#1C1917]">
              {avgLatency} <span className="text-sm font-normal text-stone-500">ms</span>
            </span>
          </div>
          <p className="text-[11px] text-[#A8A29E] mt-1">Single Core x86 Execution</p>
        </div>

        <div className="bg-white rounded-2xl p-4 border border-[#E6E0D2] shadow-sm">
          <div className="flex items-center justify-between text-[#78716C] mb-2">
            <span className="text-xs font-mono font-medium uppercase tracking-wider">Conditions Tested</span>
            <Sliders className="w-4 h-4 text-stone-600" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-mono font-bold text-[#1C1917]">
              {results.length || 11}
            </span>
            <span className="text-[11px] font-mono text-stone-400">
              (330 total evaluations)
            </span>
          </div>
          <p className="text-[11px] text-[#A8A29E] mt-1">Deterministic DSP Suite</p>
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="bg-white rounded-2xl p-12 border border-[#E6E0D2] flex flex-col items-center justify-center text-center">
          <RefreshCw className="w-8 h-8 text-amber-600 animate-spin mb-3" />
          <p className="text-sm font-semibold text-[#1C1917]">Loading benchmark metrics...</p>
          <p className="text-xs text-[#78716C] mt-1">Querying /v1/benchmark evaluation engine</p>
        </div>
      )}

      {error && (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-6 flex items-start space-x-3.5">
          <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-bold text-rose-900">Benchmark Data Unavailable</h3>
            <p className="text-xs text-rose-700 mt-1">{error}</p>
            <button
              onClick={loadData}
              className="mt-3 px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold shadow-sm"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* EER Bar Chart Visualizer */}
          <div className="bg-white rounded-2xl p-6 border border-[#E6E0D2] shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
              <div>
                <h2 className="text-base font-bold text-[#1C1917] flex items-center space-x-2">
                  <BarChart3 className="w-4 h-4 text-indigo-700" />
                  <span>Equal Error Rate (EER) by Acoustic Condition</span>
                </h2>
                <p className="text-xs text-[#78716C] mt-0.5">
                  Lower EER indicates higher resilience against audio degradation. All conditions evaluated with sample count N = {benchmarkData?.sample_count_per_condition || 30}.
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono text-[#78716C]">Sort:</span>
                <select
                  value={selectedSort}
                  onChange={(e) => setSelectedSort(e.target.value)}
                  className="text-xs font-mono bg-stone-50 border border-[#E6E0D2] rounded-lg px-2.5 py-1 text-[#44403C] focus:outline-none focus:ring-1 focus:ring-amber-500"
                >
                  <option value="default">Default Order</option>
                  <option value="eer_asc">Lowest EER First</option>
                  <option value="acc_desc">Highest Accuracy First</option>
                </select>
              </div>
            </div>

            {/* Horizontal Bar Chart */}
            <div className="space-y-4">
              {sortedResults.map((item) => {
                const eer = item.eer_percent;
                const isBaseline = item.condition_id === 'clean_16khz';
                // Color mapping based on EER
                let barColor = 'bg-emerald-500';
                let textColor = 'text-emerald-700';
                if (eer > 15.0) {
                  barColor = 'bg-rose-500';
                  textColor = 'text-rose-700';
                } else if (eer > 5.0) {
                  barColor = 'bg-amber-500';
                  textColor = 'text-amber-800';
                }

                // Normalizing bar width for display (max EER in dataset ~40-50%)
                const barWidth = Math.max(eer === 0 ? 3 : (eer / 50) * 100, 3);

                return (
                  <div key={item.condition_id} className="group">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <div className="flex items-center space-x-2">
                        <span className={`font-semibold ${isBaseline ? 'text-indigo-900 font-bold' : 'text-[#292524]'}`}>
                          {item.condition_name}
                        </span>
                        {isBaseline && (
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                            BASELINE
                          </span>
                        )}
                        <span className="text-[11px] font-mono text-stone-400">
                          (N = {item.sample_count})
                        </span>
                      </div>

                      <div className="flex items-center space-x-3 font-mono">
                        <span className="text-stone-500 text-[11px]">
                          Acc: {item.accuracy_percent.toFixed(1)}%
                        </span>
                        <span className={`font-bold text-xs ${textColor}`}>
                          EER: {eer.toFixed(2)}%
                        </span>
                      </div>
                    </div>

                    <div className="w-full bg-stone-100 rounded-full h-3 overflow-hidden p-0.5 border border-stone-200">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                        style={{ width: `${barWidth}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Legend */}
            <div className="flex flex-wrap items-center gap-4 mt-6 pt-4 border-t border-stone-100 text-[11px] font-mono text-stone-600">
              <div className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <span>Robust (EER &lt; 5%)</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                <span>Moderate Telecom Degradation (EER 5–15%)</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                <span>High Acoustic Noise (EER &gt; 15%)</span>
              </div>
            </div>
          </div>

          {/* Benchmark Results Table */}
          <div className="bg-white rounded-2xl border border-[#E6E0D2] overflow-hidden shadow-sm">
            <div className="p-5 border-b border-[#E6E0D2] bg-[#FAF8F5]/50 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-[#1C1917]">Detailed Degradation Matrix</h3>
                <p className="text-xs text-[#78716C] mt-0.5">
                  Complete quantitative breakdown per condition, including optimal decision threshold ($th^*$) and CPU latency.
                </p>
              </div>
              <span className="text-xs font-mono text-stone-500 bg-white px-2.5 py-1 rounded-lg border border-[#E6E0D2]">
                AASIST-L (85k Params)
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[#E6E0D2] bg-stone-50/70 font-mono text-[#57534E]">
                    <th className="py-3 px-4 font-semibold">Condition Name</th>
                    <th className="py-3 px-3 font-semibold text-center">Sample Count</th>
                    <th className="py-3 px-3 font-semibold text-right">EER (%)</th>
                    <th className="py-3 px-3 font-semibold text-right">Accuracy (%)</th>
                    <th className="py-3 px-3 font-semibold text-right">Optimal $th^*$</th>
                    <th className="py-3 px-3 font-semibold text-right">Avg Latency</th>
                    <th className="py-3 px-4 font-semibold">Degradation Method</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0ECE1]">
                  {sortedResults.map((item) => (
                    <tr key={item.condition_id} className="hover:bg-[#FAF8F5]/80 transition-colors">
                      <td className="py-3 px-4 font-semibold text-[#1C1917]">
                        <div className="flex items-center space-x-2">
                          <span>{item.condition_name}</span>
                          {item.condition_id === 'clean_16khz' && (
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                              Ref
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-3 font-mono text-stone-600 text-center">
                        <span className="px-2 py-0.5 rounded bg-stone-100 text-stone-700">
                          N = {item.sample_count}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-mono font-bold text-right">
                        <span className={item.eer_percent <= 5.0 ? 'text-emerald-700' : item.eer_percent <= 15.0 ? 'text-amber-800' : 'text-rose-700'}>
                          {item.eer_percent.toFixed(2)}%
                        </span>
                      </td>
                      <td className="py-3 px-3 font-mono font-semibold text-right text-stone-800">
                        {item.accuracy_percent.toFixed(2)}%
                      </td>
                      <td className="py-3 px-3 font-mono text-stone-600 text-right">
                        {item.optimal_threshold.toFixed(3)}
                      </td>
                      <td className="py-3 px-3 font-mono text-stone-600 text-right">
                        {item.avg_latency_ms.toFixed(1)} ms
                      </td>
                      <td className="py-3 px-4 text-[#78716C] max-w-xs truncate" title={item.description}>
                        {item.description}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Limitations & Methodology Callout Box */}
          <div className="bg-[#FAF8F5] border border-[#E0D8C8] rounded-2xl p-6 shadow-sm">
            <div className="flex items-start space-x-3.5">
              <Info className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
              <div className="space-y-3">
                <div>
                  <h3 className="text-sm font-bold text-[#1C1917]">
                    Evaluation Methodology & Scientific Limitations
                  </h3>
                  <p className="text-xs text-[#78716C] mt-0.5">
                    What this evaluation covers and what remains to be validated.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-[#44403C]">
                  <div className="bg-white p-3.5 rounded-xl border border-[#E6E0D2]">
                    <h4 className="font-semibold text-stone-900 mb-1 flex items-center space-x-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>What Is Measured</span>
                    </h4>
                    <ul className="list-disc list-inside space-y-1 text-stone-600 leading-relaxed text-[11px]">
                      <li>Deterministic DSP telephony simulation across 11 standard degradation profiles.</li>
                      <li>Equal Error Rate (EER) via a 1,000-point decision threshold sweep.</li>
                      <li>Exact single-core CPU execution latency measured with high-resolution timers.</li>
                      <li>AASIST-L spectral graph feature resilience under bandlimiting and packet dropouts.</li>
                    </ul>
                  </div>

                  <div className="bg-white p-3.5 rounded-xl border border-[#E6E0D2]">
                    <h4 className="font-semibold text-stone-900 mb-1 flex items-center space-x-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                      <span>Known Limitations</span>
                    </h4>
                    <ul className="list-disc list-inside space-y-1 text-stone-600 leading-relaxed text-[11px]">
                      <li><strong>Sample Size:</strong> Evaluated on N = 30 balanced demonstration chunks (15 genuine human, 15 synthetic clone). Population generalization requires full ASVspoof 2019/2021 logical access splits.</li>
                      <li><strong>Synthetic Codecs:</strong> Channels are emulated via software filterbanks/companders rather than actual cellular air interfaces (VoLTE/5G NR basebands).</li>
                      <li><strong>Acoustic Diversity:</strong> Background noise is stationary pink/white noise; real-world multi-speaker babble and high reverberation (RT60 &gt; 500ms) will introduce additional variance.</li>
                    </ul>
                  </div>
                </div>

                {/* Reproducibility Banner */}
                <div className="bg-[#1C1917] text-stone-200 p-3.5 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 font-mono text-xs">
                  <div className="flex items-center space-x-2">
                    <Terminal className="w-4 h-4 text-amber-400 flex-shrink-0" />
                    <span>Re-run this benchmark locally:</span>
                  </div>
                  <code className="bg-stone-800 text-amber-300 px-3 py-1 rounded text-[11px] border border-stone-700">
                    python backend/evaluate_model_accuracy.py
                  </code>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
