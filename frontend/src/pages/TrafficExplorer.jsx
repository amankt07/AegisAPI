import React, { useState, useMemo } from 'react';
import {
  Layers,
  Search,
  Filter,
  ArrowUpDown,
  FileText,
  HardDrive,
  Clock,
} from 'lucide-react';
import DataTable from '../components/common/DataTable';
import ThreatBadge from '../components/common/ThreatBadge';
import MethodBadge from '../components/common/MethodBadge';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';

export default function TrafficExplorer({ traffic = [], loading, error, onRefresh }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [verdictFilter, setVerdictFilter] = useState('ALL'); // 'ALL' | 'NORMAL' | 'ANOMALOUS'
  const [methodFilter, setMethodFilter] = useState('ALL');
  const [sortField, setSortField] = useState('timestamp'); // 'timestamp' | 'response_time_ms' | 'status_code'
  const [sortOrder, setSortOrder] = useState('desc');
  const [page, setPage] = useState(1);
  const pageSize = 12;

  // Format payload bytes helper
  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const filteredTraffic = useMemo(() => {
    return traffic
      .filter((item) => {
        // Search filter
        const matchSearch =
          searchTerm === '' ||
          item.endpoint?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.source_ip?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.user_agent?.toLowerCase().includes(searchTerm.toLowerCase());

        // Verdict filter
        let matchVerdict = true;
        const isAnom = item.is_anomaly === 1 || item.is_anomaly === true;
        if (verdictFilter === 'NORMAL') matchVerdict = !isAnom;
        if (verdictFilter === 'ANOMALOUS') matchVerdict = isAnom;

        // Method filter
        let matchMethod = true;
        if (methodFilter !== 'ALL') {
          matchMethod = item.http_method?.toUpperCase() === methodFilter;
        }

        return matchSearch && matchVerdict && matchMethod;
      })
      .sort((a, b) => {
        let valA = a[sortField];
        let valB = b[sortField];

        if (sortField === 'timestamp') {
          valA = new Date(valA || 0).getTime();
          valB = new Date(valB || 0).getTime();
        }

        if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
        if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
  }, [traffic, searchTerm, verdictFilter, methodFilter, sortField, sortOrder]);

  const columns = [
    {
      header: 'Timestamp',
      accessor: 'timestamp',
      render: (row) => (
        <span className="text-slate-400 text-[11px] whitespace-nowrap">
          {row.timestamp
            ? new Date(row.timestamp).toLocaleString([], {
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
      render: (row) => (
        <span className="text-slate-200 font-medium max-w-[200px] truncate block" title={row.endpoint}>
          {row.endpoint}
        </span>
      ),
    },
    {
      header: 'Status',
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
        <span className={row.response_time_ms > 1000 ? 'text-amber-400 font-bold' : 'text-slate-300'}>
          {Math.round(row.response_time_ms)} ms
        </span>
      ),
    },
    {
      header: 'Payload (In / Out)',
      accessor: 'request_size_bytes',
      render: (row) => (
        <span className="text-slate-400 text-[11px]">
          {formatBytes(row.request_size_bytes)} / <span className="text-slate-200">{formatBytes(row.response_size_bytes)}</span>
        </span>
      ),
    },
    {
      header: 'Rate (RPM / Fail)',
      accessor: 'requests_per_minute',
      render: (row) => (
        <span className="text-slate-300 text-[11px]">
          {row.requests_per_minute} rpm
          {row.failed_requests > 0 && (
            <span className="text-rose-400 ml-1 font-bold">({row.failed_requests} fail)</span>
          )}
        </span>
      ),
    },
    {
      header: 'Status',
      accessor: 'is_anomaly',
      render: (row) => {
        const isAnom = row.is_anomaly === 1 || row.is_anomaly === true;
        return isAnom ? (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
            ANOMALY
          </span>
        ) : (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            NORMAL
          </span>
        );
      },
    },
  ];

  if (loading && traffic.length === 0) {
    return <LoadingState message="Streaming historical telemetry from SQLite..." height="h-96" />;
  }

  if (error && traffic.length === 0) {
    return (
      <ErrorState
        title="Failed to Load Traffic Telemetry"
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
            <Layers className="w-5 h-5 text-cyan-400" />
            API Traffic Telemetry Explorer
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Complete chronological ledger of raw API events, latency metrics, and payload sizes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-3 py-1 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-semibold">
            {filteredTraffic.length} Ingested Events
          </span>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-4 flex flex-col md:flex-row gap-3 items-center justify-between shadow-lg shadow-black/20">
        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search endpoint, IP, user-agent..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(1);
            }}
            className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono transition-colors"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          {/* Classification Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
            <span>Verdict:</span>
            <select
              value={verdictFilter}
              onChange={(e) => {
                setVerdictFilter(e.target.value);
                setPage(1);
              }}
              className="bg-transparent text-slate-200 font-mono text-xs focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-slate-900">All Traffic</option>
              <option value="NORMAL" className="bg-slate-900">Normal Only</option>
              <option value="ANOMALOUS" className="bg-slate-900">Anomalous Only</option>
            </select>
          </div>

          {/* HTTP Method Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
            <span>Method:</span>
            <select
              value={methodFilter}
              onChange={(e) => {
                setMethodFilter(e.target.value);
                setPage(1);
              }}
              className="bg-transparent text-slate-200 font-mono text-xs focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-slate-900">All Verbs</option>
              <option value="GET" className="bg-slate-900">GET</option>
              <option value="POST" className="bg-slate-900">POST</option>
              <option value="PUT" className="bg-slate-900">PUT</option>
              <option value="DELETE" className="bg-slate-900">DELETE</option>
            </select>
          </div>

          {/* Sort Field */}
          <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
            <span>Sort:</span>
            <select
              value={sortField}
              onChange={(e) => setSortField(e.target.value)}
              className="bg-transparent text-slate-200 font-mono text-xs focus:outline-none cursor-pointer"
            >
              <option value="timestamp" className="bg-slate-900">Timestamp</option>
              <option value="response_time_ms" className="bg-slate-900">Latency</option>
              <option value="status_code" className="bg-slate-900">HTTP Status</option>
            </select>
          </div>

          {/* Direction */}
          <button
            onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
            className="p-2 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium transition-colors"
            title="Toggle Sort Direction"
          >
            <ArrowUpDown className="w-3.5 h-3.5 text-cyan-400" />
          </button>
        </div>
      </div>

      {/* Traffic Table */}
      <DataTable
        columns={columns}
        data={filteredTraffic}
        keyField="id"
        currentPage={page}
        pageSize={pageSize}
        totalRecords={filteredTraffic.length}
        onPageChange={setPage}
        emptyTitle="No Traffic Telemetry Found"
        emptyDescription="No events match your current search terms or filters."
      />
    </div>
  );
}

