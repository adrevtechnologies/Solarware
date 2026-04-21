import React, { useState } from 'react';
import { Prospect } from '../types';

interface ResultsTableProps {
  prospects: Prospect[];
  loading: boolean;
  noResultsMessage?: string;
  generatingPackId?: string | null;
  onViewImage?: (prospect: Prospect) => void;
  onGenerateMailPack?: (prospect: Prospect) => void;
}

export const ResultsTable: React.FC<ResultsTableProps> = ({
  prospects,
  loading,
  noResultsMessage = 'No viable commercial roofs found for this search.',
  generatingPackId,
  onViewImage,
  onGenerateMailPack,
}) => {
  const [sortOrder, setSortOrder] = useState<'largest' | 'smallest'>('largest');

  const sortedProspects = [...prospects].sort((a, b) => {
    if (sortOrder === 'largest') {
      return b.roof_area_sqm - a.roof_area_sqm;
    }
    return a.roof_area_sqm - b.roof_area_sqm;
  });

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-10 text-center">
        <p className="text-slate-200">Searching...</p>
      </div>
    );
  }

  if (prospects.length === 0) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-10 text-center">
        <p className="text-slate-300">{noResultsMessage}</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-700 bg-slate-900 shadow-lg">
      <div className="flex items-center justify-between border-b border-slate-700 px-4 py-3">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
          Solar Prospects
        </h3>
        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Sort
          </label>
          <select
            title="Roof size sort order"
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as 'largest' | 'smallest')}
            className="rounded-md border border-slate-600 bg-slate-800 px-2 py-1 text-sm text-slate-100"
          >
            <option value="largest">Largest Roof - Smallest Roof</option>
            <option value="smallest">Smallest Roof - Largest Roof</option>
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-800 text-slate-200">
            <tr>
              <th className="px-4 py-3 text-left font-semibold">Address</th>
              <th className="px-4 py-3 text-left font-semibold">Building Type</th>
              <th className="px-4 py-3 text-right font-semibold">Roof Size</th>
              <th className="px-4 py-3 text-right font-semibold">Panels</th>
              <th className="px-4 py-3 text-center font-semibold">View Img</th>
              <th className="px-4 py-3 text-center font-semibold">Generate Mail Pack</th>
            </tr>
          </thead>
          <tbody>
            {sortedProspects.map((prospect) => (
              <tr key={prospect.lead_id} className="border-t border-slate-800 text-slate-100">
                <td className="max-w-sm truncate px-4 py-3">{prospect.address}</td>
                <td className="px-4 py-3 text-slate-300">{prospect.building_type}</td>
                <td className="px-4 py-3 text-right text-slate-300">
                  {Math.round(prospect.roof_area_sqm).toLocaleString()} sqm
                </td>
                <td className="px-4 py-3 text-right text-slate-300">
                  {prospect.estimated_panel_count.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-center">
                  <button
                    onClick={() => onViewImage?.(prospect)}
                    className="rounded-md border border-cyan-500 px-3 py-1 text-xs font-semibold text-cyan-300 hover:bg-cyan-500/10"
                  >
                    View Img
                  </button>
                </td>
                <td className="px-4 py-3 text-center">
                  <button
                    onClick={() => onGenerateMailPack?.(prospect)}
                    disabled={generatingPackId === prospect.lead_id}
                    className="rounded-md bg-emerald-500 px-3 py-1 text-xs font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
                  >
                    {generatingPackId === prospect.lead_id
                      ? 'Generating Pack...'
                      : 'Generate Mail Pack'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="border-t border-slate-700 px-4 py-3 text-sm text-slate-400">
        {sortedProspects.length} real commercial properties found
      </div>
    </div>
  );
};
