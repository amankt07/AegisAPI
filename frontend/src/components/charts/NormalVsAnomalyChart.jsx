import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { ShieldCheck, ShieldAlert } from 'lucide-react';
import EmptyState from '../common/EmptyState';

const COLORS = {
  Normal: '#10B981',      // Emerald
  Anomalous: '#F43F5E',   // Rose
};

export default function NormalVsAnomalyChart({ stats }) {
  const normal = stats?.normal_requests || 0;
  const anomalous = stats?.anomalous_requests || 0;
  const total = stats?.total_processed_requests || 0;

  if (total === 0) {
    return (
      <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20">
        <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-400" />
          Traffic Classification Ratio
        </h3>
        <EmptyState
          title="No Traffic Inspected"
          description="Traffic ratio chart will render once API events are processed."
        />
      </div>
    );
  }

  const data = [
    { name: 'Normal Traffic', value: normal, color: COLORS.Normal },
    { name: 'Anomalous Traffic', value: anomalous, color: COLORS.Anomalous },
  ];

  return (
    <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-black/20 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            Normal vs Anomalous Distribution
          </h3>
          <span className="text-xs font-mono font-bold text-rose-400">
            {stats.anomaly_percentage?.toFixed(1)}% Anomaly Rate
          </span>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          Unsupervised Isolation Forest threat separation across all ingested traffic
        </p>
      </div>

      <div className="h-56 w-full relative flex items-center justify-center">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={80}
              paddingAngle={4}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="#090E1A" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#090E1A',
                borderColor: '#1E293B',
                borderRadius: '8px',
                color: '#E2E8F0',
                fontSize: '11px',
              }}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              wrapperStyle={{ fontSize: '11px', color: '#94A3B8' }}
            />
          </PieChart>
        </ResponsiveContainer>

        {/* Center Total Counter */}
        <div className="absolute flex flex-col items-center justify-center pointer-events-none pb-8">
          <span className="text-xl font-bold font-mono text-white">{total}</span>
          <span className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">Total</span>
        </div>
      </div>
    </div>
  );
}

