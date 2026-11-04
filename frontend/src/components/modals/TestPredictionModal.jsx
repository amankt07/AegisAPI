import React, { useState } from 'react';
import { X, Send, ShieldAlert, ShieldCheck, CheckCircle2, AlertTriangle, Sparkles } from 'lucide-react';
import { predictTraffic } from '../../services/api';
import MethodBadge from '../common/MethodBadge';
import ThreatBadge from '../common/ThreatBadge';

const PRESET_TEMPLATES = [
  {
    name: 'Benign Product Catalog Request',
    type: 'normal',
    data: {
      endpoint: '/api/v1/products',
      http_method: 'GET',
      status_code: 200,
      response_time_ms: 55.0,
      request_size_bytes: 180,
      response_size_bytes: 3200,
      requests_per_minute: 12,
      failed_requests: 0,
      source_ip: '192.168.1.45',
      user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    },
  },
  {
    name: 'Authentication Brute-Force Burst',
    type: 'anomaly',
    data: {
      endpoint: '/api/v1/auth/login',
      http_method: 'POST',
      status_code: 401,
      response_time_ms: 48.0,
      request_size_bytes: 260,
      response_size_bytes: 140,
      requests_per_minute: 240,
      failed_requests: 92,
      source_ip: '198.51.100.22',
      user_agent: 'Hydra/9.5 (Kali Linux)',
    },
  },
  {
    name: 'Large Payload Data Exfiltration',
    type: 'anomaly',
    data: {
      endpoint: '/api/v1/users/export',
      http_method: 'GET',
      status_code: 200,
      response_time_ms: 2850.0,
      request_size_bytes: 420,
      response_size_bytes: 18500000,
      requests_per_minute: 8,
      failed_requests: 0,
      source_ip: '203.0.113.8',
      user_agent: 'curl/8.4.0',
    },
  },
  {
    name: 'Volumetric Rate Spike (DDoS)',
    type: 'anomaly',
    data: {
      endpoint: '/api/v1/search',
      http_method: 'GET',
      status_code: 429,
      response_time_ms: 320.0,
      request_size_bytes: 200,
      response_size_bytes: 450,
      requests_per_minute: 650,
      failed_requests: 15,
      source_ip: '198.51.100.77',
      user_agent: 'python-requests/2.31.0',
    },
  },
];

export default function TestPredictionModal({ isOpen, onClose, onSuccess }) {
  const [formData, setFormData] = useState(PRESET_TEMPLATES[0].data);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleApplyPreset = (preset) => {
    setFormData(preset.data);
    setResult(null);
    setError(null);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: ['status_code', 'request_size_bytes', 'response_size_bytes', 'requests_per_minute', 'failed_requests'].includes(name)
        ? Number(value)
        : name === 'response_time_ms'
        ? parseFloat(value)
        : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await predictTraffic(formData);
      setResult(response);
      if (onSuccess) onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm overflow-y-auto">
      <div className="bg-[#090E1A] border border-slate-800 rounded-xl max-w-2xl w-full p-6 shadow-2xl relative my-8">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Simulate API Traffic Ingestion</h2>
              <p className="text-xs text-slate-400">
                Trigger real-time Isolation Forest evaluation & persist to SQLite
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Quick Presets */}
        <div className="mt-4">
          <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
            Load Predefined Threat Vector:
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {PRESET_TEMPLATES.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleApplyPreset(preset)}
                className={`text-left p-2.5 rounded-lg border text-xs transition-all flex items-center justify-between ${
                  formData.endpoint === preset.data.endpoint && formData.http_method === preset.data.http_method
                    ? 'bg-cyan-500/10 border-cyan-500/40 text-cyan-300'
                    : 'bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800/80 hover:border-slate-700'
                }`}
              >
                <span className="font-medium truncate">{preset.name}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold shrink-0 ml-2 ${
                    preset.type === 'anomaly'
                      ? 'bg-rose-500/20 text-rose-400'
                      : 'bg-emerald-500/20 text-emerald-400'
                  }`}
                >
                  {preset.type.toUpperCase()}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-[11px] font-medium text-slate-400 block mb-1">Method</label>
              <select
                name="http_method"
                value={formData.http_method}
                onChange={handleChange}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="text-[11px] font-medium text-slate-400 block mb-1">API Endpoint</label>
              <input
                type="text"
                name="endpoint"
                value={formData.endpoint}
                onChange={handleChange}
                required
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <label className="text-[11px] font-medium text-slate-400 block mb-1">Status Code</label>
              <input
                type="number"
                name="status_code"
                value={formData.status_code}
                onChange={handleChange}
                min={100}
                max={599}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
            <div>
              <label className="text-[11px] font-medium text-slate-400 block mb-1">Latency (ms)</label>
              <input
                type="number"
                step="0.1"
                name="response_time_ms"
                value={formData.response_time_ms}
                onChange={handleChange}
                min={0}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
            <div>
              <label className="text-[11px] font-medium text-slate-400 block mb-1">RPM (Freq)</label>
              <input
                type="number"
                name="requests_per_minute"
                value={formData.requests_per_minute}
                onChange={handleChange}
                min={0}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
            <div>
              <label className="text-[11px] font-medium text-slate-400 block mb-1">Failed Req</label>
              <input
                type="number"
                name="failed_requests"
                value={formData.failed_requests}
                onChange={handleChange}
                min={0}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] font-medium text-slate-400 block mb-1">Source IP</label>
              <input
                type="text"
                name="source_ip"
                value={formData.source_ip}
                onChange={handleChange}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
            <div>
              <label className="text-[11px] font-medium text-slate-400 block mb-1">User Agent</label>
              <input
                type="text"
                name="user_agent"
                value={formData.user_agent}
                onChange={handleChange}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono truncate"
              />
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold shadow-lg shadow-cyan-600/20 disabled:opacity-50 transition-all cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              {loading ? 'Evaluating Model...' : 'Send to Detection Engine'}
            </button>
          </div>
        </form>

        {/* Inference Result Display */}
        {result && (
          <div
            className={`mt-5 p-4 rounded-xl border ${
              result.is_anomaly
                ? 'bg-rose-950/20 border-rose-800/60'
                : 'bg-emerald-950/20 border-emerald-800/60'
            }`}
          >
            <div className="flex items-center justify-between pb-3 border-b border-slate-800/60">
              <div className="flex items-center gap-2">
                {result.is_anomaly ? (
                  <ShieldAlert className="w-5 h-5 text-rose-400" />
                ) : (
                  <ShieldCheck className="w-5 h-5 text-emerald-400" />
                )}
                <div>
                  <h4 className="text-xs font-bold text-white uppercase font-mono tracking-wider">
                    Inference Verdict: {result.prediction_label}
                  </h4>
                  <p className="text-[11px] text-slate-400">
                    Model: {result.model_name}
                  </p>
                </div>
              </div>
              <ThreatBadge level={result.threat_level} isAnomaly={result.is_anomaly} />
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3 text-xs font-mono">
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
                <span className="text-[10px] text-slate-400 block">Anomaly Score</span>
                <span className="font-bold text-slate-200">{result.anomaly_score.toFixed(4)}</span>
              </div>
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
                <span className="text-[10px] text-slate-400 block">Threat Level</span>
                <span className="font-bold text-slate-200">{result.threat_level}</span>
              </div>
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
                <span className="text-[10px] text-slate-400 block">HTTP Status</span>
                <span className="font-bold text-slate-200">{formData.status_code}</span>
              </div>
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
                <span className="text-[10px] text-slate-400 block">Persistence</span>
                <span className="font-bold text-emerald-400">Saved to SQLite</span>
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-950/30 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>
    </div>
  );
}

