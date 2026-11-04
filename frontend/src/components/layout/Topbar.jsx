import React from 'react';
import {
  Menu,
  RefreshCw,
  Clock,
  ShieldCheck,
  ShieldAlert,
  Send,
  SlidersHorizontal,
} from 'lucide-react';

export default function Topbar({
  onToggleSidebar,
  lastUpdated,
  isRefreshing,
  onRefresh,
  pollInterval,
  onPollIntervalChange,
  isHealthy,
  onOpenTestModal,
}) {
  return (
    <header className="h-16 bg-[#090E1A]/90 backdrop-blur-md border-b border-slate-800/80 px-4 lg:px-8 flex items-center justify-between sticky top-0 z-30">
      {/* Left: Mobile Toggle & Status */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 lg:hidden"
          title="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5">
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-mono font-medium ${
              isHealthy
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isHealthy ? 'bg-emerald-400 pulse-radar' : 'bg-rose-400'
              }`}
            />
            <span>{isHealthy ? 'SYSTEM OPERATIONAL' : 'BACKEND DISCONNECTED'}</span>
          </div>
        </div>
      </div>

      {/* Right Controls: Auto-refresh, Last Updated & Test Action */}
      <div className="flex items-center gap-3">
        {/* Polling Interval Selector */}
        <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 bg-slate-900/80 border border-slate-800 px-2.5 py-1 rounded-lg">
          <SlidersHorizontal className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-[11px] text-slate-400">Polling:</span>
          <select
            value={pollInterval}
            onChange={(e) => onPollIntervalChange(Number(e.target.value))}
            className="bg-transparent text-slate-200 font-mono text-xs focus:outline-none cursor-pointer"
          >
            <option value={10000} className="bg-slate-900 text-slate-200">10s</option>
            <option value={15000} className="bg-slate-900 text-slate-200">15s</option>
            <option value={30000} className="bg-slate-900 text-slate-200">30s</option>
            <option value={0} className="bg-slate-900 text-slate-200">Manual</option>
          </select>
        </div>

        {/* Last Updated Timestamp */}
        <div className="hidden md:flex items-center gap-1.5 text-xs font-mono text-slate-400 bg-slate-900/60 border border-slate-800/80 px-2.5 py-1 rounded-lg">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span>
            {lastUpdated ? lastUpdated.toLocaleTimeString() : 'Syncing...'}
          </span>
        </div>

        {/* Manual Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors disabled:opacity-50"
          title="Refresh Data Now"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
        </button>

        {/* Test Injection Button */}
        <button
          onClick={onOpenTestModal}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-medium shadow-md shadow-cyan-600/20 transition-all font-sans"
        >
          <Send className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Simulate Traffic</span>
          <span className="sm:hidden">Test</span>
        </button>
      </div>
    </header>
  );
}

