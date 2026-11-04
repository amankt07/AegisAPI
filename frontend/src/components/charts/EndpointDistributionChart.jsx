import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Network } from 'lucide-react';
import EmptyState from '../common/EmptyState';

export default function EndpointDistributionChart({ traffic = [], topAnomalous = {} }) {
  // If topAnomalous is provided, combine with overall endpoints
  const endpointCounts = {};

  if (traffic && traffic.length > 0) {
    traffic.forEach((item) => {
      const ep = item.endpoint || 'Unknown';
      endpointCounts[ep] = (endpointCounts[ep] || 0) + 1;
    });
  } else if (topAnomalous && Object.keys(topAnomalous).length > 0) {
    Object.entries(topAnomalous).forEach(([ep, count]) => {
      endpointCounts[ep] = count;
    });
  }

  const chartData = Object.entries(endpointCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6) // Top 6 endpoints
    .map(([endpoint, count]) => ({
      endpoint,
      count,
      anomalousCount: topAnomalous?.[endpoint] || 0,
    }));

  if (chartData.length === 0) {
    return (
      <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
        <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <Network className="w-4 h-4 text-cyan-400" />
          Traffic Endpoint Distribution
        </h3>
        <EmptyState
          title="No Endpoints Logged"
          description="Endpoint distribution will populate as API requests are inspected."
        />
      </div>
    );
  }

  return (
    <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Network className="w-4 h-4 text-cyan-400" />
            Top API Endpoints Ingestion
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Most frequently accessed routes and attack target correlation
          </p>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 10, right: 20, left: 20, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" horizontal={false} />
            <XAxis
              type="number"
              stroke="#64748B"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: '#1E293B' }}
            />
            <YAxis
              type="category"
              dataKey="endpoint"
              stroke="#94A3B8"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: '#1E293B' }}
              width={140}
              tickFormatter={(val) => (val.length > 20 ? `${val.substring(0, 18)}...` : val)}
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
            <Bar
              dataKey="count"
              name="Total Ingested"
              fill="#06B6D4"
              radius={[0, 4, 4, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

