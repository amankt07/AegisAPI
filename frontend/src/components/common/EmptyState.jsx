import React from 'react';
import { ShieldCheck, Inbox } from 'lucide-react';

export default function EmptyState({
  icon: Icon = ShieldCheck,
  title = 'No Records Found',
  description = 'No telemetry data matches your current query or filter criteria.',
  action,
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="w-12 h-12 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center mb-3 text-slate-500 shadow-inner">
        <Icon className="w-6 h-6 text-slate-400" />
      </div>
      <h3 className="text-sm font-semibold text-slate-300">{title}</h3>
      <p className="text-xs text-slate-500 mt-1 max-w-sm">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

