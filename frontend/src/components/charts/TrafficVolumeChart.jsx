import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import EmptyState from '../common/EmptyState';
import { Activity } from 'lucide-react';

export default function TrafficVolumeChart({ traffic = [] }) {
  if (!traffic || traffic.length === 0) {
    return (
      <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
        <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          API Traffic Volume Over Time
        </h3>
        <EmptyState
          title="No Historical Traffic"
          description="Traffic telemetry will populate dynamically as API requests arrive."
        />
      </div>
    );
  }

  // Aggregate traffic by minute / time slices (in chronological order)
  const sorted = [...traffic].reverse(); // Oldest to newest
  const chartData = sorted.map((item, idx) => {
    const time = item.timestamp ? new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : `T-${idx}`;
    return {
      time,
      requestsPerMin: item.requests_per_minute || 1,
      latency: Math.round(item.response_time_ms || 0),
      isAnomaly: item.is_anomaly === 1 || item.is_anomaly === true ? 1 : 0,
    };
  });

  return (
    <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            API Request Velocity & Volume
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Rolling requests per minute across historical telemetry events
          </p>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
          {chartData.length} Data Points
        </span>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="volumeGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
            <XAxis
              dataKey="time"
              stroke="#64748B"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: '#1E293B' }}
            />
            <YAxis
              stroke="#64748B"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: '#1E293B' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#090E1A',
                borderColor: '#1E293B',
                borderRadius: '8px',
                color: '#E2E8F0',
                fontSize: '11px',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
              }}
              labelStyle={{ color: '#38BDF8', fontWeight: 'bold' }}
            />
            <Area
              type="monotone"
              dataKey="requestsPerMin"
              name="Req / Min"
              stroke="#06B6D4"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#volumeGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

