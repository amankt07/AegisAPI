import React from 'react';

export default function MethodBadge({ method = 'GET' }) {
  const m = method.toUpperCase();
  let colorStyles = 'bg-slate-800 text-slate-300 border-slate-700';

  if (m === 'GET') {
    colorStyles = 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
  } else if (m === 'POST') {
    colorStyles = 'bg-blue-500/10 text-blue-400 border-blue-500/30';
  } else if (m === 'PUT' || m === 'PATCH') {
    colorStyles = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  } else if (m === 'DELETE') {
    colorStyles = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
  }

  return (
    <span className={`inline-block font-mono text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${colorStyles}`}>
      {m}
    </span>
  );
}

