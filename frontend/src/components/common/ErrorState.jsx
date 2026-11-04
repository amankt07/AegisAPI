import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function ErrorState({
  title = 'Telemetry Connection Failure',
  message = 'Unable to synchronize with the backend service. Please check that FastAPI is running.',
  onRetry,
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 bg-rose-950/20 border border-rose-900/40 rounded-xl text-center max-w-lg mx-auto my-6">
      <div className="w-12 h-12 rounded-full bg-rose-900/30 border border-rose-800/50 flex items-center justify-center mb-3">
        <AlertTriangle className="w-6 h-6 text-rose-400" />
      </div>
      <h3 className="text-base font-semibold text-rose-200">{title}</h3>
      <p className="text-xs text-slate-400 mt-2 leading-relaxed max-w-md">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Request
        </button>
      )}
    </div>
  );
}

