import React, { useState, useMemo } from 'react';
import {
  ShieldAlert,
  Search,
  Filter,
  ArrowUpDown,
  RefreshCw,
  AlertOctagon,
  Download,
} from 'lucide-react';
import DataTable from '../components/common/DataTable';
import ThreatBadge from '../components/common/ThreatBadge';
import MethodBadge from '../components/common/MethodBadge';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';

export default function AnomalyMonitoring({ anomalies = [], loading, error, onRefresh }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [threatFilter, setThreatFilter] = useState('ALL');
  const [sortOrder, setSortOrder] = useState('desc'); // 'desc' | 'asc'
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // Filter and sort anomaly incidents
  const filteredAnomalies = useMemo(() => {
    return anomalies
      .filter((item) => {
        // Search term filter
        const matchSearch =
          searchTerm === '' ||
          item.endpoint?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.source_ip?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.http_method?.toLowerCase().includes(searchTerm.toLowerCase());

        // Status code filter
        let matchStatus = true;
        if (statusFilter === '2XX') matchStatus = item.status_code >= 200 && item.status_code < 300;
        if (statusFilter === '4XX') matchStatus = item.status_code >= 400 && item.status_code < 500;
        if (statusFilter === '5XX') matchStatus = item.status_code >= 500;

        // Threat filter
        let matchThreat = true;
        if (threatFilter !== 'ALL') {
          matchThreat = (item.threat_level || '').toLowerCase().includes(threatFilter.toLowerCase());
        }

        return matchSearch && matchStatus && matchThreat;
      })
      .sort((a, b) => {
        const timeA = new Date(a.timestamp || 0).getTime();
        const timeB = new Date(b.timestamp || 0).getTime();
        return sortOrder === 'desc' ? timeB - timeA : timeA - timeB;
      });
  }, [anomalies, searchTerm, statusFilter, threatFilter, sortOrder]);

  const columns = [
    {
      header: 'Timestamp',
      accessor: 'timestamp',
      render: (row) => (
        <span className="text-slate-400 text-[11px] whitespace-nowrap">
          {row.timestamp
            ? new Date(row.timestamp).toLocaleString([], {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
              })
            : '--'}
        </span>
      ),
    },
    {
      header: 'Source IP',
      accessor: 'source_ip',
      render: (row) => <span className="text-cyan-400 font-semibold">{row.source_ip || '127.0.0.1'}</span>,
    },
    {
      header: 'Method',
      accessor: 'http_method',
      render: (row) => <MethodBadge method={row.http_method} />,
    },
    {
      header: 'API Endpoint',
      accessor: 'endpoint',
      render: (row) => <span className="text-slate-200 font-medium">{row.endpoint}</span>,
    },
    {
      header: 'HTTP Status',
      accessor: 'status_code',
      render: (row) => (
        <span
          className={`px-2 py-0.5 rounded text-[11px] font-bold ${
            row.status_code >= 500
              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
              : row.status_code >= 400
              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
              : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
          }`}
        >
          {row.status_code}
        </span>
      ),
    },
    {
      header: 'Latency',
      accessor: 'response_time_ms',
      render: (row) => (
        <span className={row.response_time_ms > 1000 ? 'text-rose-400 font-bold' : 'text-slate-300'}>
          {Math.round(row.response_time_ms)} ms
        </span>
      ),
    },
    {
      header: 'Anomaly Score',
      accessor: 'anomaly_score',
      render: (row) => (
        <div className="flex flex-col">
          <span className="font-bold text-rose-400">
            {row.anomaly_score !== undefined ? row.anomaly_score.toFixed(4) : '--'}
          </span>
          <span className="text-[9px] text-slate-500">Continuous Offset</span>
        </div>
      ),
    },
    {
      header: 'Verdict',
      accessor: 'prediction_label',
      render: (row) => (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20 uppercase">
          {row.prediction_label || 'Anomaly'}
        </span>
      ),
    },
    {
      header: 'Threat Tier',
      accessor: 'threat_level',
      render: (row) => <ThreatBadge level={row.threat_level} isAnomaly={true} />,
    },
    {
      header: 'Engine',
      accessor: 'model_name',
      render: (row) => (
        <span className="text-[10px] text-slate-400 font-mono">
          {row.model_name || 'Isolation Forest'}
        </span>
      ),
    },
  ];

  if (loading && anomalies.length === 0) {
    return <LoadingState message="Loading anomaly incident records from SQLite..." height="h-96" />;
  }

  if (error && anomalies.length === 0) {
    return (
      <ErrorState
        title="Failed to Load Anomaly Incidents"
        message={error}
        onRetry={onRefresh}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            Security Anomaly Monitoring
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time incident log of traffic streams flagged by the unsupervised Isolation Forest model.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-3 py-1 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/30 font-semibold flex items-center gap-1.5">
            <AlertOctagon className="w-3.5 h-3.5" />
            {filteredAnomalies.length} Incidents Flagged
          </span>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-4 flex flex-col md:flex-row gap-3 items-center justify-between shadow-lg shadow-black/20">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by endpoint, IP or method..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(1);
            }}
            className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono transition-colors"
          />
        </div>

        {/* Filter Dropdowns */}
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          {/* Status Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <span>HTTP Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="bg-transparent text-slate-200 font-mono text-xs focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-slate-900">All Statuses</option>
              <option value="2XX" className="bg-slate-900">2xx Success</option>
              <option value="4XX" className="bg-slate-900">4xx Client Errors</option>
              <option value="5XX" className="bg-slate-900">5xx Server Errors</option>
            </select>
          </div>

          {/* Threat Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
            <span>Threat Tier:</span>
            <select
              value={threatFilter}
              onChange={(e) => {
                setThreatFilter(e.target.value);
                setPage(1);
              }}
              className="bg-transparent text-slate-200 font-mono text-xs focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-slate-900">All Tiers</option>
              <option value="Critical" className="bg-slate-900">Critical Threat</option>
              <option value="High" className="bg-slate-900">High Threat</option>
              <option value="Medium" className="bg-slate-900">Medium Threat</option>
              <option value="Low" className="bg-slate-900">Low Threat</option>
            </select>
          </div>

          {/* Sort Order Toggle */}
          <button
            onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-xs text-slate-300 font-medium transition-colors"
            title="Toggle chronological sorting"
          >
            <ArrowUpDown className="w-3.5 h-3.5 text-cyan-400" />
            <span>{sortOrder === 'desc' ? 'Newest First' : 'Oldest First'}</span>
          </button>
        </div>
      </div>

      {/* Incident Data Table */}
      <DataTable
        columns={columns}
        data={filteredAnomalies}
        keyField="id"
        currentPage={page}
        pageSize={pageSize}
        totalRecords={filteredAnomalies.length}
        onPageChange={setPage}
        emptyTitle="No Anomaly Incidents Matching Criteria"
        emptyDescription="All evaluated API traffic matches the normal learned distribution."
      />

      {/* Methodology Explainer Note */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 flex items-start gap-3">
        <AlertOctagon className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-200">Isolation Forest Continuous Scoring: </span>
          Anomalies are detected by measuring the average number of recursive splittings required to isolate a telemetry sample across 100 random decision trees. Positive anomaly scores signify multi-variate deviations (e.g. concurrent credential bursts, payload overflows, or latency spikes). Scores are presented without artificial probability rounding to preserve forensic veracity.
        </div>
      </div>
    </div>
  );
}

