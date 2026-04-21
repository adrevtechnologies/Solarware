import React from 'react';
import { Prospect } from '../types';

interface ProposalModalProps {
  isOpen: boolean;
  onClose: () => void;
  prospect?: Prospect;
  generating?: boolean;
  onGenerateMailPack?: () => void;
}

export const ProposalModal: React.FC<ProposalModalProps> = ({
  isOpen,
  onClose,
  prospect,
  generating,
  onGenerateMailPack,
}) => {
  if (!isOpen || !prospect) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
      <div className="w-full max-w-4xl overflow-hidden rounded-xl border border-slate-700 bg-slate-900 shadow-2xl">
        <div className="border-b border-slate-700 px-6 py-4">
          <h2 className="text-lg font-bold text-slate-100">{prospect.address}</h2>
          <p className="mt-1 text-sm text-slate-400">{prospect.building_type}</p>
        </div>

        <div className="p-6">
          <div className="overflow-hidden rounded-lg border border-slate-700">
            {prospect.satellite_image_url ? (
              <img
                src={prospect.satellite_image_url}
                alt={`Satellite roof view for ${prospect.address}`}
                className="h-auto w-full"
              />
            ) : (
              <div className="flex h-64 items-center justify-center bg-slate-800 text-sm text-slate-300">
                Loading enriched satellite image...
              </div>
            )}
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-slate-300 sm:grid-cols-4">
            <div className="rounded-lg border border-slate-700 bg-slate-800 p-3">
              Roof: {Math.round(prospect.roof_area_sqm)} sqm
            </div>
            <div className="rounded-lg border border-slate-700 bg-slate-800 p-3">
              Panels: {prospect.estimated_panel_count}
            </div>
            <div className="rounded-lg border border-slate-700 bg-slate-800 p-3">
              Capacity: {prospect.capacity_high_kw.toFixed(1)} kW
            </div>
            <div className="rounded-lg border border-slate-700 bg-slate-800 p-3">
              Savings: {prospect.savings_potential_display}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 border-t border-slate-700 px-6 py-4">
          <button
            onClick={onClose}
            className="rounded-md border border-slate-600 px-4 py-2 text-sm font-semibold text-slate-200 hover:bg-slate-800"
          >
            Close
          </button>
          <button
            onClick={onGenerateMailPack}
            disabled={generating}
            className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-60"
          >
            {generating ? 'Generating Pack...' : 'Generate Mail Pack'}
          </button>
        </div>
      </div>
    </div>
  );
};
