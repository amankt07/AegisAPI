import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Zap } from 'lucide-react';
import EmptyState from '../common/EmptyState';

export default function ResponseTimeChart({ traffic = [], averageLatency = 0 }) {
  if (!traffic || traffic.length === 0) {
    return (
      <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
        <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-400" />
          API Response Latency Trends
        </h3>
        <EmptyState
          title="No Latency Records"
          description="Latency data will display when requests are logged."
        />
      </div>
    );
  }

  // Chronological order (oldest to newest)
  const sorted = [...traffic].reverse();
  const chartData = sorted.map((item, idx) => {
    const time = item.timestamp
      ? new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      : `#${idx + 1}`;
    return {
      index: idx + 1,
      time,
      latency: Math.round(item.response_time_ms || 0),
      endpoint: item.endpoint || 'API',
      isAnomaly: item.is_anomaly === 1 || item.is_anomaly === true,
    };
  });

  return (
    <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" />
            API Latency & Execution Delays (ms)
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Round-trip response latency across chronological requests
          </p>
        </div>
        {averageLatency > 0 && (
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
            Avg: {averageLatency.toFixed(1)} ms
          </span>
        )}
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-[#090E1A] border border-slate-700 rounded-lg p-2.5 text-xs shadow-xl font-mono">
                      <p className="text-cyan-400 font-bold mb-1">{data.time}</p>
                      <p className="text-slate-300">Endpoint: <span className="text-slate-100">{data.endpoint}</span></p>
                      <p className="text-amber-400">Latency: <span className="font-bold">{data.latency} ms</span></p>
                      <p className={data.isAnomaly ? 'text-rose-400 font-semibold' : 'text-emerald-400 font-semibold'}>
                        {data.isAnomaly ? 'Flagged Anomaly' : 'Normal Range'}
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            {averageLatency > 0 && (
              <ReferenceLine
                y={averageLatency}
                stroke="#F59E0B"
                strokeDasharray="4 4"
                label={{
                  value: 'AVG',
                  fill: '#F59E0B',
                  fontSize: 10,
                  position: 'insideRight',
                }}
              />
            )}
            <Line
              type="monotone"
              dataKey="latency"
              name="Latency (ms)"
              stroke="#F59E0B"
              strokeWidth={2}
              dot={{ r: 3, fill: '#090E1A', stroke: '#F59E0B', strokeWidth: 1.5 }}
              activeDot={{ r: 6, fill: '#F59E0B', stroke: '#FFF' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

