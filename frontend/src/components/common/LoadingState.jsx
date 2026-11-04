import React from 'react';
import { Loader2, Shield } from 'lucide-react';

export default function LoadingState({ message = 'Loading security telemetry...', height = 'h-64' }) {
  return (
    <div className={`flex flex-col items-center justify-center ${height} w-full text-slate-400`}>
      <div className="relative flex items-center justify-center mb-3">
        <div className="absolute w-12 h-12 rounded-full border border-cyan-500/20 animate-ping" />
        <div className="w-10 h-10 rounded-full border-2 border-cyan-500/30 border-t-cyan-400 animate-spin" />
        <Shield className="w-4 h-4 text-cyan-400 absolute" />
      </div>
      <p className="text-sm font-medium text-slate-300">{message}</p>
      <p className="text-xs text-slate-500 mt-1 font-mono">Synchronizing with AegisAPI Engine...</p>
    </div>
  );
}

