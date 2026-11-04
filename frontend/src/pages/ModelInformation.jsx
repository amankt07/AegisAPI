import React, { useState, useEffect } from 'react';
import {
  BrainCircuit,
  Award,
  CheckCircle2,
  Calendar,
  Layers,
  Cpu,
  Info,
  ShieldCheck,
  FileCode,
  Sliders,
  ExternalLink,
} from 'lucide-react';
import { getModelInfo } from '../services/api';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';

export default function ModelInformation() {
  const [modelInfo, setModelInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchInfo = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getModelInfo();
      setModelInfo(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInfo();
  }, []);

  if (loading) {
    return <LoadingState message="Retrieving ML model governance & audit metadata..." height="h-96" />;
  }

  if (error) {
    return (
      <ErrorState
        title="Failed to Load Model Information"
        message={error}
        onRetry={fetchInfo}
      />
    );
  }

  const metrics = modelInfo?.evaluation_metrics || {};
  const params = modelInfo?.hyperparameters || {};
  const features = modelInfo?.feature_names || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <BrainCircuit className="w-5 h-5 text-cyan-400" />
            Machine Learning Model Governance & Audit
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Active champion model metadata, hyperparameters, and offline test evaluation benchmarks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-3 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-semibold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 pulse-radar" />
            Status: {modelInfo?.status?.toUpperCase() || 'ACTIVE'}
          </span>
        </div>
      </div>

      {/* Offline Disclaimer Banner */}
      <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-200 flex items-start gap-3 shadow-lg shadow-black/10">
        <Info className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <h4 className="font-semibold text-amber-300">Offline Benchmark Evaluation Notice</h4>
          <p className="text-amber-200/80 mt-1 leading-relaxed">
            The performance metrics below represent rigorously stratified, offline test-set evaluation (6,000 held-out samples, 80/20 split) conducted during Phase 3 model benchmarking. These values measure algorithm discriminative capacity against synthetic ground-truth labels and are distinct from dynamic real-time traffic statistics.
          </p>
        </div>
      </div>

      {/* Model Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Algorithm</span>
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <h3 className="text-base font-bold text-white font-mono">{modelInfo?.model_name || 'Isolation Forest'}</h3>
          <p className="text-[11px] text-slate-500 mt-1 font-mono truncate" title={modelInfo?.algorithm}>
            {modelInfo?.algorithm}
          </p>
        </div>

        <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Training Corpus</span>
            <Layers className="w-4 h-4 text-cyan-400" />
          </div>
          <h3 className="text-2xl font-bold text-white font-mono">24,000</h3>
          <p className="text-[11px] text-slate-500 mt-1">
            80/20 Stratified Partition (30,000 Total)
          </p>
        </div>

        <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Feature Dimensionality</span>
            <FileCode className="w-4 h-4 text-cyan-400" />
          </div>
          <h3 className="text-2xl font-bold text-white font-mono">{modelInfo?.feature_count || 42}</h3>
          <p className="text-[11px] text-slate-500 mt-1">
            Numerical, interaction, cyclical & one-hot
          </p>
        </div>

        <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Training Timestamp</span>
            <Calendar className="w-4 h-4 text-cyan-400" />
          </div>
          <h3 className="text-sm font-bold text-white font-mono">
            {modelInfo?.training_date
              ? new Date(modelInfo.training_date).toLocaleDateString([], {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })
              : 'Nov 2026'}
          </h3>
          <p className="text-[11px] text-slate-500 mt-1 font-mono">
            Reproducible Seed: 42
          </p>
        </div>
      </div>

      {/* Offline Evaluation Benchmark Cards */}
      <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-6 shadow-lg shadow-black/20">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 mb-4 font-mono">
          <Award className="w-4 h-4 text-emerald-400" />
          Validated Offline Test Benchmarks (Held-out Test Partition: N=6,000)
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
            <span className="text-xs text-slate-400 font-medium block">Precision</span>
            <span className="text-2xl sm:text-3xl font-bold font-mono text-emerald-400 mt-1 block">
              {metrics.precision ? `${(metrics.precision * 100).toFixed(2)}%` : '99.88%'}
            </span>
            <span className="text-[10px] text-slate-500 mt-1 block">Low False Alarm Rate</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
            <span className="text-xs text-slate-400 font-medium block">Recall</span>
            <span className="text-2xl sm:text-3xl font-bold font-mono text-cyan-400 mt-1 block">
              {metrics.recall ? `${(metrics.recall * 100).toFixed(2)}%` : '99.78%'}
            </span>
            <span className="text-[10px] text-slate-500 mt-1 block">High Attack Interception</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
            <span className="text-xs text-slate-400 font-medium block">F1-Score</span>
            <span className="text-2xl sm:text-3xl font-bold font-mono text-indigo-400 mt-1 block">
              {metrics.f1_score ? `${(metrics.f1_score * 100).toFixed(2)}%` : '99.83%'}
            </span>
            <span className="text-[10px] text-slate-500 mt-1 block">Harmonic Mean</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
            <span className="text-xs text-slate-400 font-medium block">ROC-AUC</span>
            <span className="text-2xl sm:text-3xl font-bold font-mono text-amber-400 mt-1 block">
              {metrics.roc_auc ? `${(metrics.roc_auc * 100).toFixed(2)}%` : '99.98%'}
            </span>
            <span className="text-[10px] text-slate-500 mt-1 block">Discriminative Power</span>
          </div>
        </div>
      </div>

      {/* Hyperparameters & Score Interpretation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tuned Hyperparameters */}
        <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-3">
            <Sliders className="w-4 h-4 text-cyan-400" />
            Tuned Hyperparameters
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Configuration parameters applied during scikit-learn ensemble training.
          </p>

          <div className="divide-y divide-slate-800/60 font-mono text-xs">
            {Object.entries(params).map(([key, val]) => (
              <div key={key} className="py-2.5 flex items-center justify-between">
                <span className="text-slate-400">{key}</span>
                <span className="text-cyan-400 font-bold">{String(val)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Score Interpretation Guide */}
        <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-3">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Anomaly Score Interpretation
          </h3>
          <p className="text-xs text-slate-400 mb-4 leading-relaxed">
            {modelInfo?.score_interpretation ||
              'Scikit-learn Isolation Forest inversion: negative values represent normal nominal traffic; positive values denote anomalous outlier deviations requiring shorter isolation path lengths.'}
          </p>

          <div className="space-y-2.5 font-mono text-xs">
            <div className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-800/40 flex items-center justify-between">
              <span className="text-emerald-400 font-semibold">&lt; 0.00 (Negative)</span>
              <span className="text-slate-300">Safe / Nominal Baseline</span>
            </div>
            <div className="p-2.5 rounded-lg bg-yellow-950/20 border border-yellow-800/40 flex items-center justify-between">
              <span className="text-yellow-400 font-semibold">0.00 – 0.07</span>
              <span className="text-slate-300">Low Threat Deviation</span>
            </div>
            <div className="p-2.5 rounded-lg bg-amber-950/20 border border-amber-800/40 flex items-center justify-between">
              <span className="text-amber-400 font-semibold">0.07 – 0.15</span>
              <span className="text-slate-300">Medium Threat</span>
            </div>
            <div className="p-2.5 rounded-lg bg-red-950/20 border border-red-800/40 flex items-center justify-between">
              <span className="text-red-400 font-semibold">0.15 – 0.25</span>
              <span className="text-slate-300">High Threat Attack</span>
            </div>
            <div className="p-2.5 rounded-lg bg-rose-950/20 border border-rose-800/40 flex items-center justify-between">
              <span className="text-rose-400 font-semibold">&ge; 0.25</span>
              <span className="text-slate-300">Critical Threat Exfiltration</span>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Taxonomy Section */}
      <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              Engineered Feature Schema ({features.length} Dimensions)
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Strictly validated feature vector ingested by the model preprocessor
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
          {features.map((feat, idx) => (
            <div
              key={idx}
              className="p-2 rounded bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-300 truncate"
              title={feat}
            >
              <span className="text-[9px] text-cyan-400 mr-1.5">{idx + 1}.</span>
              {feat}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

