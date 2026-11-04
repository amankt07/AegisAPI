import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import EmptyState from './EmptyState';

export default function DataTable({
  columns = [],
  data = [],
  keyField = 'id',
  currentPage = 1,
  pageSize = 10,
  totalRecords,
  onPageChange,
  emptyTitle = 'No Records Found',
  emptyDescription = 'No traffic telemetry matching your search criteria.',
}) {
  const totalPages = totalRecords ? Math.ceil(totalRecords / pageSize) : Math.ceil(data.length / pageSize) || 1;
  const isServerPaginated = totalRecords !== undefined && onPageChange !== undefined;

  // Client-side slice if not server paginated
  const displayData = isServerPaginated ? data : data.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div className="w-full bg-[#0D1322] border border-slate-800/80 rounded-xl overflow-hidden shadow-lg shadow-black/20">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  className={`px-4 py-3 whitespace-nowrap ${col.className || ''}`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {displayData.length > 0 ? (
              displayData.map((row, rowIdx) => (
                <tr
                  key={row[keyField] || rowIdx}
                  className="hover:bg-slate-800/40 transition-colors"
                >
                  {columns.map((col, colIdx) => (
                    <td
                      key={colIdx}
                      className={`px-4 py-3 whitespace-nowrap ${col.cellClassName || 'text-slate-300'}`}
                    >
                      {col.render ? col.render(row) : row[col.accessor]}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} className="py-8">
                  <EmptyState title={emptyTitle} description={emptyDescription} />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {(totalRecords > pageSize || data.length > pageSize) && (
        <div className="flex items-center justify-between px-4 py-3 bg-slate-900/50 border-t border-slate-800/80 text-xs text-slate-400">
          <div>
            Showing{' '}
            <span className="font-semibold text-slate-200">
              {data.length === 0 ? 0 : (currentPage - 1) * pageSize + 1}
            </span>{' '}
            to{' '}
            <span className="font-semibold text-slate-200">
              {Math.min(currentPage * pageSize, totalRecords || data.length)}
            </span>{' '}
            of{' '}
            <span className="font-semibold text-slate-200">{totalRecords || data.length}</span> entries
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange && onPageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              className="p-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40 disabled:pointer-events-none transition-colors"
              title="Previous Page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-slate-400 font-medium px-2">
              Page <span className="text-slate-200">{currentPage}</span> of{' '}
              <span className="text-slate-200">{totalPages}</span>
            </span>
            <button
              onClick={() => onPageChange && onPageChange(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="p-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40 disabled:pointer-events-none transition-colors"
              title="Next Page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

