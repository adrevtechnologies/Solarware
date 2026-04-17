import React from 'react';
import { SearchArea } from '../types';

interface SearchAreaFormProps {
  onSubmit: (data: SearchArea) => void;
  loading?: boolean;
}

export const SearchAreaForm: React.FC<SearchAreaFormProps> = ({ onSubmit, loading = false }) => {
  const [formMode, setFormMode] = React.useState<'address' | 'coordinates'>('address');
  const [formData, setFormData] = React.useState({
    name: '',
    country: 'ZA',
    region: '',
    street: '',
    area: '',
    district: '',
    city: '',
    min_latitude: undefined as number | undefined,
    max_latitude: undefined as number | undefined,
    min_longitude: undefined as number | undefined,
    max_longitude: undefined as number | undefined,
    min_roof_area_sqft: 5000,
  });

  const countries = [
    { code: 'ZA', name: '🇿🇦 South Africa' },
    { code: 'US', name: '🇺🇸 United States' },
    { code: 'UK', name: '🇬🇧 United Kingdom' },
    { code: 'DE', name: '🇩🇪 Germany' },
    { code: 'AU', name: '🇦🇺 Australia' },
    { code: 'BR', name: '🇧🇷 Brazil' },
  ];

  const regions = {
    ZA: [
      { code: 'WC', name: 'Western Cape' },
      { code: 'GP', name: 'Gauteng' },
      { code: 'KZN', name: 'KwaZulu-Natal' },
      { code: 'EC', name: 'Eastern Cape' },
      { code: 'LP', name: 'Limpopo' },
    ],
    US: [
      { code: 'CA', name: 'California' },
      { code: 'NY', name: 'New York' },
      { code: 'TX', name: 'Texas' },
      { code: 'FL', name: 'Florida' },
      { code: 'AZ', name: 'Arizona' },
    ],
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validate that at least one field is filled
    const hasAddress = formData.street || formData.area || formData.city;
    const hasCoordinates =
      formData.min_latitude !== undefined &&
      formData.max_latitude !== undefined &&
      formData.min_longitude !== undefined &&
      formData.max_longitude !== undefined;

    if (!hasAddress && !hasCoordinates) {
      alert('Please provide either an address or geographic coordinates');
      return;
    }

    const submitData: any = {
      name: formData.name || `${formData.city || formData.area || 'Search Area'}`,
      country: formData.country,
      region: formData.region || undefined,
      street: formData.street || undefined,
      area: formData.area || undefined,
      district: formData.district || undefined,
      city: formData.city || undefined,
      min_roof_area_sqft: formData.min_roof_area_sqft,
    };

    if (hasCoordinates) {
      submitData.min_latitude = formData.min_latitude;
      submitData.max_latitude = formData.max_latitude;
      submitData.min_longitude = formData.min_longitude;
      submitData.max_longitude = formData.max_longitude;
    }

    onSubmit(submitData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 p-6 bg-white rounded-lg shadow-lg">
      <div>
        <h2 className="text-2xl font-bold mb-2">🌍 Define Search Area</h2>
        <p className="text-gray-600 text-sm">
          Enter an address or geographic coordinates to begin solar prospect discovery
        </p>
      </div>

      {/* Country & Region Selection */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-semibold mb-2">Country *</label>
          <select
            value={formData.country}
            onChange={(e) => setFormData({ ...formData, country: e.target.value, region: '' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {countries.map((c) => (
              <option key={c.code} value={c.code}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-semibold mb-2">Province/State (optional)</label>
          <select
            value={formData.region}
            onChange={(e) => setFormData({ ...formData, region: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select a region...</option>
            {(regions[formData.country as keyof typeof regions] || []).map((r) => (
              <option key={r.code} value={r.code}>
                {r.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Mode Selection */}
      <div className="flex gap-4 border-t pt-4">
        <button
          type="button"
          onClick={() => setFormMode('address')}
          className={`flex-1 py-2 px-4 rounded-md font-medium transition ${
            formMode === 'address'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          📍 Address Search
        </button>
        <button
          type="button"
          onClick={() => setFormMode('coordinates')}
          className={`flex-1 py-2 px-4 rounded-md font-medium transition ${
            formMode === 'coordinates'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          🗺️ Coordinates
        </button>
      </div>

      {/* Address-based Search */}
      {formMode === 'address' && (
        <div className="space-y-4 bg-blue-50 p-4 rounded-md">
          <p className="text-sm text-gray-700 font-medium">
            Enter any combination of address fields:
          </p>

          <div>
            <label className="block text-sm font-medium mb-1">Street Address</label>
            <input
              type="text"
              value={formData.street}
              onChange={(e) => setFormData({ ...formData, street: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., 98 Richmond Street"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Area/Suburb</label>
              <input
                type="text"
                value={formData.area}
                onChange={(e) => setFormData({ ...formData, area: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Goodwood"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">District</label>
              <input
                type="text"
                value={formData.district}
                onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Central"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">City/Town</label>
            <input
              type="text"
              value={formData.city}
              onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Cape Town"
            />
          </div>

          <div className="bg-blue-100 border border-blue-300 rounded p-3 text-sm text-blue-800">
            ✓ Fill in any combination above. The system will search from that level.
          </div>
        </div>
      )}

      {/* Coordinate-based Search */}
      {formMode === 'coordinates' && (
        <div className="space-y-4 bg-orange-50 p-4 rounded-md">
          <p className="text-sm text-gray-700 font-medium">Define geographic search bounds:</p>

          <fieldset>
            <legend className="text-sm font-semibold text-gray-700 mb-3">Geographic Bounds</legend>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium mb-1">Min Latitude</label>
                <input
                  type="number"
                  value={formData.min_latitude ?? ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      min_latitude: e.target.value ? parseFloat(e.target.value) : undefined,
                    })
                  }
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="-34.2"
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">Max Latitude</label>
                <input
                  type="number"
                  value={formData.max_latitude ?? ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      max_latitude: e.target.value ? parseFloat(e.target.value) : undefined,
                    })
                  }
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="-33.8"
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">Min Longitude</label>
                <input
                  type="number"
                  value={formData.min_longitude ?? ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      min_longitude: e.target.value ? parseFloat(e.target.value) : undefined,
                    })
                  }
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="18.3"
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">Max Longitude</label>
                <input
                  type="number"
                  value={formData.max_longitude ?? ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      max_longitude: e.target.value ? parseFloat(e.target.value) : undefined,
                    })
                  }
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="18.8"
                />
              </div>
            </div>
          </fieldset>

          <div className="bg-orange-100 border border-orange-300 rounded p-3 text-sm text-orange-800">
            💡 Enter all four coordinates to define the exact search area bounds.
          </div>
        </div>
      )}

      {/* Minimum Roof Area */}
      <div>
        <label className="block text-sm font-semibold mb-2">Minimum Roof Area (sq ft)</label>
        <input
          type="number"
          value={formData.min_roof_area_sqft}
          onChange={(e) =>
            setFormData({ ...formData, min_roof_area_sqft: parseFloat(e.target.value) })
          }
          required
          min={100}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <p className="text-xs text-gray-500 mt-1">Buildings smaller than this will be excluded</p>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-3 rounded-md font-bold hover:bg-blue-700 disabled:opacity-50 transition text-lg"
      >
        {loading ? '⏳ Processing Search Area...' : '🚀 Start Solar Prospect Discovery'}
      </button>
    </form>
  );
};
