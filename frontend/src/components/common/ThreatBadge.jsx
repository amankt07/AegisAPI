import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, AlertOctagon, Info } from 'lucide-react';

export default function ThreatBadge({ level, isAnomaly }) {
  // Normalize level
  const normalized = (level || (isAnomaly ? 'Critical Threat' : 'Safe')).trim();

  switch (normalized) {
    case 'Critical Threat':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
          <AlertOctagon className="w-3 h-3" />
          Critical
        </span>
      );
    case 'High Threat':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-500/15 text-red-400 border border-red-500/30">
          <ShieldAlert className="w-3 h-3" />
          High
        </span>
      );
    case 'Medium Threat':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
          <AlertTriangle className="w-3 h-3" />
          Medium
        </span>
      );
    case 'Low Threat':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-yellow-500/15 text-yellow-400 border border-yellow-500/30">
          <Info className="w-3 h-3" />
          Low
        </span>
      );
    case 'Safe':
    default:
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          <ShieldCheck className="w-3 h-3" />
          Safe
        </span>
      );
  }
}

