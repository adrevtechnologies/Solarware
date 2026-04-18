import React, { useState } from 'react';

export interface Filters {
  minRoofSize?: number;
  maxRoofSize?: number;
  businessOnly?: boolean;
  warehousesOnly?: boolean;
  schoolsOnly?: boolean;
  hasContactInfo?: boolean;
  highSolarScore?: boolean;
}

interface FiltersPanelProps {
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
}

export const FiltersPanel: React.FC<FiltersPanelProps> = ({ filters, onFiltersChange }) => {
  const [expanded, setExpanded] = useState(false);

  const toggleFilter = (key: keyof Filters) => {
    onFiltersChange({
      ...filters,
      [key]: !filters[key],
    });
  };

  const updateFilterValue = (key: keyof Filters, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value,
    });
  };

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 p-4 mt-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full font-semibold text-gray-700 hover:text-gray-900"
      >
        <span>Optional Filters</span>
        <span className={`transform transition ${expanded ? 'rotate-180' : ''}`}>▼</span>
      </button>

      {expanded && (
        <div className="mt-4 space-y-3">
          {/* Minimum Roof Size */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={!!filters.minRoofSize}
              onChange={() => toggleFilter('minRoofSize')}
              className="w-4 h-4 accent-green-600 cursor-pointer"
            />
            <label className="text-sm font-medium text-gray-700 flex-1">Minimum Roof Size</label>
            {filters.minRoofSize && (
              <input
                type="number"
                value={filters.minRoofSize}
                onChange={(e) => updateFilterValue('minRoofSize', Number(e.target.value))}
                placeholder="sqft"
                className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
              />
            )}
          </div>

          {/* Maximum Roof Size */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={!!filters.maxRoofSize}
              onChange={() => toggleFilter('maxRoofSize')}
              className="w-4 h-4 accent-green-600 cursor-pointer"
            />
            <label className="text-sm font-medium text-gray-700 flex-1">Maximum Roof Size</label>
            {filters.maxRoofSize && (
              <input
                type="number"
                value={filters.maxRoofSize}
                onChange={(e) => updateFilterValue('maxRoofSize', Number(e.target.value))}
                placeholder="sqft"
                className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
              />
            )}
          </div>

          {/* Business Only */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={!!filters.businessOnly}
              onChange={() => toggleFilter('businessOnly')}
              className="w-4 h-4 accent-green-600 cursor-pointer"
            />
            <label className="text-sm font-medium text-gray-700">Business Only</label>
          </div>

          {/* Warehouses Only */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={!!filters.warehousesOnly}
              onChange={() => toggleFilter('warehousesOnly')}
              className="w-4 h-4 accent-green-600 cursor-pointer"
            />
            <label className="text-sm font-medium text-gray-700">Warehouses Only</label>
          </div>

          {/* Schools Only */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={!!filters.schoolsOnly}
              onChange={() => toggleFilter('schoolsOnly')}
              className="w-4 h-4 accent-green-600 cursor-pointer"
            />
            <label className="text-sm font-medium text-gray-700">Schools Only</label>
          </div>

          {/* Has Contact Info */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={!!filters.hasContactInfo}
              onChange={() => toggleFilter('hasContactInfo')}
              className="w-4 h-4 accent-green-600 cursor-pointer"
            />
            <label className="text-sm font-medium text-gray-700">Has Contact Info</label>
          </div>

          {/* High Solar Score Only */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={!!filters.highSolarScore}
              onChange={() => toggleFilter('highSolarScore')}
              className="w-4 h-4 accent-green-600 cursor-pointer"
            />
            <label className="text-sm font-medium text-gray-700">High Solar Score Only (80+)</label>
          </div>
        </div>
      )}
    </div>
  );
};
