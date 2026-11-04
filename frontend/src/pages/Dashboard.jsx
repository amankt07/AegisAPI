import React, { useState, useEffect } from 'react';
import {
  Activity,
  ShieldCheck,
  ShieldAlert,
  Percent,
  Clock,
  AlertTriangle,
  ArrowUpRight,
  TrendingUp,
} from 'lucide-react';
import MetricCard from '../components/common/MetricCard';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import TrafficVolumeChart from '../components/charts/TrafficVolumeChart';
import NormalVsAnomalyChart from '../components/charts/NormalVsAnomalyChart';
import ResponseTimeChart from '../components/charts/ResponseTimeChart';
import StatusDistributionChart from '../components/charts/StatusDistributionChart';
import EndpointDistributionChart from '../components/charts/EndpointDistributionChart';
import MethodBadge from '../components/common/MethodBadge';
import ThreatBadge from '../components/common/ThreatBadge';
import { Link } from 'react-router-dom';

export default function Dashboard({ stats, traffic = [], anomalies = [], loading, error, onRetry }) {
  if (loading && !stats) {
    return <LoadingState message="Connecting to AegisAPI Detection Engine..." height="h-96" />;
  }

  if (error && !stats) {
    return (
      <ErrorState
        title="Dashboard Telemetry Offline"
        message={error}
        onRetry={onRetry}
      />
    );
  }

  const total = stats?.total_processed_requests ?? 0;
  const normal = stats?.normal_requests ?? 0;
  const anomalous = stats?.anomalous_requests ?? 0;
  const anomalyPct = stats?.anomaly_percentage !== undefined ? `${stats.anomaly_percentage.toFixed(2)}%` : '--';
  const avgLatency = stats?.average_response_time_ms !== undefined ? `${stats.average_response_time_ms.toFixed(1)} ms` : '--';
  const httpErrors = stats?.http_error_count ?? 0;

  return (
    <div className="space-y-6">
      {/* Page Title & Context Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            API Security Operations Center
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time API traffic anomaly detection powered by an unsupervised Isolation Forest model.
          </p>
        </div>
      </div>

      {/* 6 Core KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {/* 1. Total Requests */}
        <MetricCard
          title="Total Requests"
          value={total.toLocaleString()}
          subtext="Inspected API events"
          icon={Activity}
          accentColor="cyan"
          badgeText="All Traffic"
          badgeType="cyan"
        />

        {/* 2. Normal Requests */}
        <MetricCard
          title="Normal Traffic"
          value={normal.toLocaleString()}
          subtext="Benign execution"
          icon={ShieldCheck}
          accentColor="emerald"
          badgeText="Verified"
          badgeType="emerald"
        />

        {/* 3. Detected Anomalies */}
        <MetricCard
          title="Anomalies"
          value={anomalous.toLocaleString()}
          subtext="Flagged security alerts"
          icon={ShieldAlert}
          accentColor="rose"
          badgeText={anomalous > 0 ? 'Active' : 'Zero'}
          badgeType={anomalous > 0 ? 'rose' : 'emerald'}
        />

        {/* 4. Anomaly Percentage */}
        <MetricCard
          title="Anomaly Rate"
          value={anomalyPct}
          subtext="Telemetry threat ratio"
          icon={Percent}
          accentColor={parseFloat(anomalyPct) > 10 ? 'rose' : 'amber'}
          badgeText="Ratio"
          badgeType={parseFloat(anomalyPct) > 10 ? 'rose' : 'amber'}
        />

        {/* 5. Average Latency */}
        <MetricCard
          title="Avg Latency"
          value={avgLatency}
          subtext="Round-trip response"
          icon={Clock}
          accentColor="amber"
          badgeText="Global"
          badgeType="default"
        />

        {/* 6. HTTP Error Count */}
        <MetricCard
          title="HTTP Errors"
          value={httpErrors.toLocaleString()}
          subtext="4xx client & 5xx server"
          icon={AlertTriangle}
          accentColor={httpErrors > 0 ? 'rose' : 'emerald'}
          badgeText={httpErrors > 0 ? 'Errors' : 'None'}
          badgeType={httpErrors > 0 ? 'rose' : 'emerald'}
        />
      </div>

      {/* Primary Analytics Charts Row (2 columns) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TrafficVolumeChart traffic={traffic} />
        </div>
        <div className="lg:col-span-1">
          <NormalVsAnomalyChart stats={stats} />
        </div>
      </div>

      {/* Secondary Analytics Charts Row (3 columns) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <ResponseTimeChart
          traffic={traffic}
          averageLatency={stats?.average_response_time_ms || 0}
        />
        <StatusDistributionChart traffic={traffic} />
        <EndpointDistributionChart
          traffic={traffic}
          topAnomalous={stats?.top_anomalous_endpoints || {}}
        />
      </div>

      {/* Recent Security Incidents Feed Table */}
      <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              Recent Detected Anomaly Incidents
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Live threat queue flagged by Isolation Forest decision thresholds
            </p>
          </div>
          <Link
            to="/anomalies"
            className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 font-medium transition-colors"
          >
            <span>View All Incidents</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-900/60 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                <th className="px-4 py-2.5">Timestamp</th>
                <th className="px-4 py-2.5">Source IP</th>
                <th className="px-4 py-2.5">Method</th>
                <th className="px-4 py-2.5">Endpoint</th>
                <th className="px-4 py-2.5">HTTP Status</th>
                <th className="px-4 py-2.5">Latency</th>
                <th className="px-4 py-2.5">Anomaly Score</th>
                <th className="px-4 py-2.5">Threat Level</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {anomalies && anomalies.length > 0 ? (
                anomalies.slice(0, 5).map((incident) => (
                  <tr key={incident.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-4 py-2.5 text-slate-400 text-[11px] whitespace-nowrap">
                      {incident.timestamp
                        ? new Date(incident.timestamp).toLocaleString([], {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                          })
                        : 'Just now'}
                    </td>
                    <td className="px-4 py-2.5 text-cyan-400">{incident.source_ip}</td>
                    <td className="px-4 py-2.5">
                      <MethodBadge method={incident.http_method} />
                    </td>
                    <td className="px-4 py-2.5 text-slate-200 font-medium">{incident.endpoint}</td>
                    <td className="px-4 py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                          incident.status_code >= 400
                            ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                            : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                        }`}
                      >
                        {incident.status_code}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-slate-300">
                      {Math.round(incident.response_time_ms)} ms
                    </td>
                    <td className="px-4 py-2.5 text-rose-400 font-bold">
                      {incident.anomaly_score !== undefined
                        ? incident.anomaly_score.toFixed(4)
                        : '--'}
                    </td>
                    <td className="px-4 py-2.5">
                      <ThreatBadge level={incident.threat_level} isAnomaly={true} />
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="py-6 text-center text-xs text-slate-500">
                    No security anomalies detected yet. Ingest traffic to trigger analysis.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

