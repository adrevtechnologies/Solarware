import React from 'react';
import { SearchMode } from './SearchModeSelector';

export interface SearchParams {
  country?: string;
  province?: string;
  city?: string;
  area?: string;
  street?: string;
  postalCode?: string;
}

interface SearchPanelProps {
  mode: SearchMode;
  params: SearchParams;
  onParamsChange: (params: SearchParams) => void;
  onSearch: () => void;
  loading: boolean;
}

export const SearchPanel: React.FC<SearchPanelProps> = ({
  mode,
  params,
  onParamsChange,
  onSearch,
  loading,
}) => {
  const updateParam = (key: keyof SearchParams, value: string) => {
    onParamsChange({ ...params, [key]: value });
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
      {/* Country - always shown except in country mode */}
      {mode !== 'country' && (
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">Country</label>
          <input
            type="text"
            placeholder="South Africa"
            value={params.country || ''}
            onChange={(e) => updateParam('country', e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>
      )}

      {/* Province - shown for province, city, area, address modes */}
      {(mode === 'province' || mode === 'city' || mode === 'area' || mode === 'address') && (
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">Province</label>
          <input
            type="text"
            placeholder="Western Cape"
            value={params.province || ''}
            onChange={(e) => updateParam('province', e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>
      )}

      {/* City - shown for city, area, address modes */}
      {(mode === 'city' || mode === 'area' || mode === 'address') && (
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">City</label>
          <input
            type="text"
            placeholder="Cape Town"
            value={params.city || ''}
            onChange={(e) => updateParam('city', e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>
      )}

      {/* Area/Suburb - shown for area and address modes */}
      {(mode === 'area' || mode === 'address') && (
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">Area / Suburb</label>
          <input
            type="text"
            placeholder="Goodwood"
            value={params.area || ''}
            onChange={(e) => updateParam('area', e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>
      )}

      {/* Address fields - shown only for address mode */}
      {mode === 'address' && (
        <>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Street Number + Name
            </label>
            <input
              type="text"
              placeholder="98 Richmond Street"
              value={params.street || ''}
              onChange={(e) => updateParam('street', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Postal Code</label>
            <input
              type="text"
              placeholder="7460"
              value={params.postalCode || ''}
              onChange={(e) => updateParam('postalCode', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
        </>
      )}

      {/* Search Button */}
      <button
        onClick={onSearch}
        disabled={loading}
        className="w-full bg-gradient-to-r from-green-600 to-green-700 text-white font-bold py-3 rounded-lg hover:from-green-700 hover:to-green-800 disabled:opacity-50 transition mt-6"
      >
        {loading ? '🔍 Searching properties...' : '🚀 Find Solar Leads'}
      </button>
    </div>
  );
};
