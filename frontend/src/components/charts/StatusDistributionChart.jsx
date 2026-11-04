import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { CheckCircle2 } from 'lucide-react';
import EmptyState from '../common/EmptyState';

export default function StatusDistributionChart({ traffic = [] }) {
  if (!traffic || traffic.length === 0) {
    return (
      <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
        <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          HTTP Status Distribution
        </h3>
        <EmptyState
          title="No Status Codes"
          description="Status code distribution will appear when requests are recorded."
        />
      </div>
    );
  }

  // Count occurrences of status codes
  const counts = {};
  traffic.forEach((item) => {
    const code = item.status_code || 200;
    counts[code] = (counts[code] || 0) + 1;
  });

  const chartData = Object.keys(counts)
    .sort()
    .map((code) => {
      const statusCode = Number(code);
      let color = '#10B981'; // 2xx
      if (statusCode >= 300 && statusCode < 400) color = '#38BDF8'; // 3xx
      if (statusCode >= 400 && statusCode < 500) color = '#F59E0B'; // 4xx
      if (statusCode >= 500) color = '#F43F5E'; // 5xx

      return {
        status: `HTTP ${code}`,
        count: counts[code],
        code: statusCode,
        color,
      };
    });

  return (
    <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            HTTP Response Status Code Breakdown
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Frequency of HTTP response statuses across recorded API traffic
          </p>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
            <XAxis
              dataKey="status"
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
              cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
              contentStyle={{
                backgroundColor: '#090E1A',
                borderColor: '#1E293B',
                borderRadius: '8px',
                color: '#E2E8F0',
                fontSize: '11px',
              }}
            />
            <Bar dataKey="count" name="Total Requests" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

