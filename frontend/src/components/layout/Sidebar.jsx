import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldAlert,
  Activity,
  Layers,
  BrainCircuit,
  Radio,
  Server,
  ExternalLink,
} from 'lucide-react';

const NAV_ITEMS = [
  {
    name: 'Dashboard Overview',
    path: '/',
    icon: Activity,
    badge: null,
  },
  {
    name: 'Anomaly Incidents',
    path: '/anomalies',
    icon: ShieldAlert,
    badge: 'Live',
    badgeColor: 'rose',
  },
  {
    name: 'Traffic Explorer',
    path: '/traffic',
    icon: Layers,
    badge: null,
  },
  {
    name: 'Model Information',
    path: '/model-info',
    icon: BrainCircuit,
    badge: 'Audit',
    badgeColor: 'cyan',
  },
];

export default function Sidebar({ isOpen, onClose }) {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-[#090E1A] border-r border-slate-800/80 flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center gap-3 px-5 border-b border-slate-800/80">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white font-bold">
            <Radio className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-wider text-white uppercase flex items-center gap-1.5 font-mono">
              AegisAPI
              <span className="text-[10px] px-1.5 py-0.2 bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded font-sans font-semibold">
                SOC
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 font-medium">Threat Monitoring</p>
          </div>
        </div>

        {/* Navigation Links */}
        <div className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <p className="px-3 mb-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            Security Monitoring
          </p>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 font-semibold shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold ${
                      item.badgeColor === 'rose'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </div>

        {/* Engine Status / System Footer */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/30">
          <div className="p-3 rounded-lg bg-[#0D1322] border border-slate-800 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1.5">
                <Server className="w-3.5 h-3.5 text-cyan-400" />
                Backend Engine
              </span>
              <span className="flex items-center gap-1 text-[11px] font-mono text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 pulse-radar" />
                Active
              </span>
            </div>
            <p className="mt-2 text-[10px] text-slate-500 font-mono">
              Model: Isolation Forest (42 Features)
            </p>
            <a
              href="http://127.0.0.1:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2.5 flex items-center justify-between text-[11px] text-cyan-400 hover:text-cyan-300 font-medium transition-colors pt-2 border-t border-slate-800/60"
            >
              <span>Swagger OpenAPI</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </aside>
    </>
  );
}

