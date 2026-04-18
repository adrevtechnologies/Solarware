import React, { useState } from 'react';
import { Prospect } from '../types';

interface ResultsTableProps {
  prospects: Prospect[];
  loading: boolean;
  noResultsMessage?: string;
  onSelectProspect?: (prospect: Prospect) => void;
}

export const ResultsTable: React.FC<ResultsTableProps> = ({
  prospects,
  loading,
  noResultsMessage = "Enter search criteria and click 'Find Solar Leads'",
  onSelectProspect,
}) => {
  const [selectedRow, setSelectedRow] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin text-3xl">⏳</div>
        <p className="mt-3 text-gray-600">Searching real buildings nearby...</p>
      </div>
    );
  }

  if (prospects.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <p className="text-gray-600">{noResultsMessage}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gradient-to-r from-blue-600 to-blue-700 text-white sticky top-0">
            <tr>
              <th className="px-4 py-3 text-left font-semibold">Address</th>
              <th className="px-4 py-3 text-left font-semibold">Business</th>
              <th className="px-4 py-3 text-left font-semibold">Type</th>
              <th className="px-4 py-3 text-right font-semibold">Roof (m²)</th>
              <th className="px-4 py-3 text-right font-semibold">Capacity (kW)</th>
              <th className="px-4 py-3 text-right font-semibold">Annual kWh</th>
              <th className="px-4 py-3 text-right font-semibold">Savings Potential</th>
              <th className="px-4 py-3 text-center font-semibold">Score</th>
              <th className="px-4 py-3 text-center font-semibold">Action</th>
            </tr>
          </thead>
          <tbody>
            {prospects.map((prospect) => (
              <tr
                key={prospect.osm_id}
                className={`border-b transition-colors cursor-pointer ${
                  selectedRow === prospect.osm_id ? 'bg-blue-50' : 'bg-white hover:bg-gray-50'
                }`}
                onClick={() => {
                  setSelectedRow(prospect.osm_id);
                  onSelectProspect?.(prospect);
                }}
              >
                {/* Address */}
                <td className="px-4 py-3 font-medium text-gray-900 truncate max-w-xs">
                  {prospect.address}
                </td>

                {/* Business Name */}
                <td className="px-4 py-3 text-gray-600 truncate">
                  {prospect.business_name || '—'}
                </td>

                {/* Building Type */}
                <td className="px-4 py-3">
                  <span className="inline-block px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-semibold">
                    {prospect.building_type}
                  </span>
                </td>

                {/* Roof Size */}
                <td className="px-4 py-3 text-right text-gray-600">
                  {Math.round(prospect.roof_area_sqm).toLocaleString()}
                </td>

                {/* Capacity Range */}
                <td className="px-4 py-3 text-right text-gray-600 font-mono">
                  {prospect.capacity_low_kw.toFixed(1)} – {prospect.capacity_high_kw.toFixed(1)}
                </td>

                {/* Annual Generation */}
                <td className="px-4 py-3 text-right text-gray-600 font-mono">
                  {Math.round(prospect.annual_kwh).toLocaleString()}
                </td>

                {/* Savings Potential */}
                <td className="px-4 py-3 text-right font-semibold text-green-700">
                  {prospect.savings_potential_display}
                </td>

                {/* Solar Score Badge */}
                <td className="px-4 py-3 text-center">
                  <div
                    className={`inline-flex items-center justify-center w-10 h-10 rounded-full font-bold text-white ${
                      prospect.solar_score >= 75
                        ? 'bg-green-600'
                        : prospect.solar_score >= 60
                          ? 'bg-yellow-600'
                          : prospect.solar_score >= 40
                            ? 'bg-orange-600'
                            : 'bg-red-600'
                    }`}
                  >
                    {prospect.solar_score}
                  </div>
                </td>

                {/* Detail Button */}
                <td className="px-4 py-3 text-center">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectProspect?.(prospect);
                    }}
                    className="px-3 py-1 bg-green-600 text-white rounded font-semibold text-xs hover:bg-green-700 transition"
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      <div className="bg-gray-50 px-4 py-3 border-t border-gray-200">
        <p className="text-sm text-gray-600">
          Found <strong>{prospects.length}</strong> commercial buildings with solar potential
        </p>
      </div>
    </div>
  );
};
