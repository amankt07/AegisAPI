import React from 'react';

export default function MetricCard({
  title,
  value,
  subtext,
  icon: Icon,
  badgeText,
  badgeType = 'default', // 'emerald', 'rose', 'cyan', 'amber'
  accentColor = 'cyan',  // 'cyan', 'emerald', 'rose', 'amber', 'indigo'
}) {
  const accentClasses = {
    cyan: {
      border: 'hover:border-cyan-500/40',
      iconBg: 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20',
      valueColor: 'text-cyan-400',
    },
    emerald: {
      border: 'hover:border-emerald-500/40',
      iconBg: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
      valueColor: 'text-emerald-400',
    },
    rose: {
      border: 'hover:border-rose-500/40',
      iconBg: 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
      valueColor: 'text-rose-400',
    },
    amber: {
      border: 'hover:border-amber-500/40',
      iconBg: 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
      valueColor: 'text-amber-400',
    },
    indigo: {
      border: 'hover:border-indigo-500/40',
      iconBg: 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20',
      valueColor: 'text-indigo-400',
    },
  }[accentColor] || {
    border: 'hover:border-slate-700',
    iconBg: 'bg-slate-800 text-slate-300 border border-slate-700',
    valueColor: 'text-slate-100',
  };

  const badgeClasses = {
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    rose: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    cyan: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    default: 'bg-slate-800 text-slate-400 border-slate-700',
  }[badgeType] || 'bg-slate-800 text-slate-400 border-slate-700';

  return (
    <div
      className={`relative bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 transition-all duration-200 shadow-lg shadow-black/20 ${accentClasses.border}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</p>
          <h4 className="text-2xl font-bold tracking-tight text-white mt-1.5 font-mono">
            {value !== undefined && value !== null ? value : '--'}
          </h4>
        </div>
        {Icon && (
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${accentClasses.iconBg}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/60">
        <span className="truncate">{subtext || 'Telemetry metric'}</span>
        {badgeText && (
          <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${badgeClasses}`}>
            {badgeText}
          </span>
        )}
      </div>
    </div>
  );
}

