import React, { useEffect, useMemo, useState } from 'react';
import { CITIES_BY_PROVINCE, COUNTRIES, PROVINCES_BY_COUNTRY } from '../data/locationOptions';
import { api } from '../services/api';

export type SearchMode = 'area' | 'property';

export interface SelectedPlace {
  place_id: string;
  formatted_address: string;
  lat: number;
  lng: number;
  city?: string;
  province?: string;
  country?: string;
}

export interface SearchParams {
  mode: SearchMode;
  country: string;
  province: string;
  city: string;
  area: string;
  radiusM: number;
  selectedAreaPlace?: SelectedPlace;
  propertyQuery?: string;
  selectedPropertyPlace?: SelectedPlace;
}

interface SearchPanelProps {
  params: SearchParams;
  onParamsChange: (params: SearchParams) => void;
  onSearch: () => void;
  loading: boolean;
}

export const SearchPanel: React.FC<SearchPanelProps> = ({
  params,
  onParamsChange,
  onSearch,
  loading,
}) => {
  const [suggestions, setSuggestions] = useState<Array<{ place_id: string; full_text: string }>>(
    []
  );
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const provinceOptions = PROVINCES_BY_COUNTRY[params.country] || [];
  const cityOptions = CITIES_BY_PROVINCE[params.province] || [];
  const canSearch =
    (params.mode === 'area' && !!params.selectedAreaPlace) ||
    (params.mode === 'property' && !!params.selectedPropertyPlace);

  const sessionToken = useMemo(
    () => `solarware-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
    []
  );

  const updateParam = (key: keyof SearchParams, value: string) => {
    onParamsChange({ ...params, [key]: value });
  };

  const updateNumber = (key: keyof SearchParams, value: string) => {
    const parsed = Number(value);
    onParamsChange({
      ...params,
      [key]: Number.isNaN(parsed) ? undefined : parsed,
    });
  };

  useEffect(() => {
    const query = (params.mode === 'property' ? params.propertyQuery : params.area) || '';
    if (query.trim().length < 2) {
      setSuggestions([]);
      return;
    }

    const timer = window.setTimeout(async () => {
      try {
        setLoadingSuggestions(true);
        const response = await api.placesAutocomplete(query, sessionToken, 'za');
        setSuggestions(
          (response.data.suggestions || []).map((item) => ({
            place_id: item.place_id,
            full_text: item.full_text,
          }))
        );
      } catch {
        setSuggestions([]);
      } finally {
        setLoadingSuggestions(false);
      }
    }, 250);

    return () => window.clearTimeout(timer);
  }, [params.area, params.propertyQuery, params.mode, sessionToken]);

  const handleSelectArea = async (placeId: string, label: string) => {
    try {
      const details = await api.placeDetails(placeId, sessionToken);
      const place = details.data;
      onParamsChange({
        ...params,
        area: place.formatted_address || label,
        city: place.city || params.city,
        province: place.province || params.province,
        country: place.country || params.country,
        selectedAreaPlace: {
          place_id: place.place_id,
          formatted_address: place.formatted_address || label,
          lat: Number(place.lat || 0),
          lng: Number(place.lng || 0),
          city: place.city,
          province: place.province,
          country: place.country,
        },
      });
      setSuggestions([]);
    } catch {
      setSuggestions([]);
    }
  };

  const handleSelectProperty = async (placeId: string, label: string) => {
    try {
      const details = await api.placeDetails(placeId, sessionToken);
      const place = details.data;
      onParamsChange({
        ...params,
        propertyQuery: place.formatted_address || label,
        city: place.city || params.city,
        province: place.province || params.province,
        country: place.country || params.country,
        selectedPropertyPlace: {
          place_id: place.place_id,
          formatted_address: place.formatted_address || label,
          lat: Number(place.lat || 0),
          lng: Number(place.lng || 0),
          city: place.city,
          province: place.province,
          country: place.country,
        },
      });
      setSuggestions([]);
    } catch {
      setSuggestions([]);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-6 shadow-xl backdrop-blur-sm space-y-4">
      <div>
        <h2 className="text-xl font-bold text-slate-100">Target Search</h2>
        <p className="text-sm text-slate-400 mt-1">
          Two modes only: Area Search and Single Property.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => onParamsChange({ ...params, mode: 'area' })}
          className={`rounded-lg border px-3 py-2 text-sm font-semibold ${
            params.mode === 'area'
              ? 'border-emerald-400 bg-emerald-500/20 text-emerald-200'
              : 'border-slate-600 bg-slate-800 text-slate-300'
          }`}
        >
          Area Search
        </button>
        <button
          type="button"
          onClick={() => onParamsChange({ ...params, mode: 'property' })}
          className={`rounded-lg border px-3 py-2 text-sm font-semibold ${
            params.mode === 'property'
              ? 'border-emerald-400 bg-emerald-500/20 text-emerald-200'
              : 'border-slate-600 bg-slate-800 text-slate-300'
          }`}
        >
          Single Property
        </button>
      </div>

      {params.mode === 'property' && (
        <>
          <div>
            <label className="block text-sm font-semibold text-slate-200 mb-2">
              Business Name or Full Address
            </label>
            <input
              type="text"
              placeholder="Makro Cape Gate or 12 Jip St Goodwood"
              value={params.propertyQuery || ''}
              onChange={(e) =>
                onParamsChange({
                  ...params,
                  propertyQuery: e.target.value,
                  selectedPropertyPlace: undefined,
                })
              }
              className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-3 text-slate-100 placeholder-slate-500 focus:border-emerald-400 focus:outline-none"
            />
            {!!suggestions.length && (
              <div className="mt-2 max-h-56 overflow-y-auto rounded-xl border border-slate-700 bg-slate-900">
                {suggestions.map((item) => (
                  <button
                    key={item.place_id}
                    type="button"
                    onClick={() => {
                      void handleSelectProperty(item.place_id, item.full_text);
                    }}
                    className="block w-full border-b border-slate-800 px-4 py-3 text-left text-sm text-slate-200 hover:bg-slate-800"
                  >
                    {item.full_text}
                  </button>
                ))}
              </div>
            )}
            {loadingSuggestions && (
              <p className="mt-2 text-xs text-slate-400">Loading property suggestions...</p>
            )}
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-800/80 px-4 py-3 text-sm text-slate-300">
            Analyze the selected property only. No area-wide scan.
          </div>
        </>
      )}

      {params.mode === 'area' && (
        <>
          <div>
            <label className="block text-sm font-semibold text-slate-200 mb-2">Area Query</label>
            <input
              type="text"
              placeholder="Goodwood"
              value={params.area}
              onChange={(e) =>
                onParamsChange({
                  ...params,
                  area: e.target.value,
                  selectedAreaPlace: undefined,
                })
              }
              className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-3 text-slate-100 placeholder-slate-500 focus:border-emerald-400 focus:outline-none"
            />
            {!!suggestions.length && (
              <div className="mt-2 max-h-56 overflow-y-auto rounded-xl border border-slate-700 bg-slate-900">
                {suggestions.map((item) => (
                  <button
                    key={item.place_id}
                    type="button"
                    onClick={() => {
                      void handleSelectArea(item.place_id, item.full_text);
                    }}
                    className="block w-full border-b border-slate-800 px-4 py-3 text-left text-sm text-slate-200 hover:bg-slate-800"
                  >
                    {item.full_text}
                  </button>
                ))}
              </div>
            )}
            {loadingSuggestions && (
              <p className="mt-2 text-xs text-slate-400">Loading area suggestions...</p>
            )}
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-semibold text-slate-200 mb-2">Country</label>
              <select
                title="Country"
                value={params.country}
                onChange={(e) => {
                  const country = e.target.value;
                  const firstProvince = (PROVINCES_BY_COUNTRY[country] || [])[0] || '';
                  const firstCity = (CITIES_BY_PROVINCE[firstProvince] || [])[0] || '';
                  onParamsChange({ ...params, country, province: firstProvince, city: firstCity });
                }}
                className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-3 text-slate-100 focus:border-emerald-400 focus:outline-none"
              >
                {COUNTRIES.map((country) => (
                  <option key={country} value={country}>
                    {country}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-200 mb-2">
                Province / State
              </label>
              <select
                title="Province or state"
                value={params.province}
                onChange={(e) => {
                  const province = e.target.value;
                  const firstCity = (CITIES_BY_PROVINCE[province] || [])[0] || '';
                  onParamsChange({ ...params, province, city: firstCity });
                }}
                className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-3 text-slate-100 focus:border-emerald-400 focus:outline-none"
              >
                {provinceOptions.map((province) => (
                  <option key={province} value={province}>
                    {province}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-200 mb-2">City</label>
              <select
                title="City"
                value={params.city}
                onChange={(e) => updateParam('city', e.target.value)}
                className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-3 text-slate-100 focus:border-emerald-400 focus:outline-none"
              >
                {cityOptions.map((city) => (
                  <option key={city} value={city}>
                    {city}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-200 mb-2">Radius (m)</label>
              <input
                type="number"
                title="Area search radius in meters"
                min={300}
                max={4000}
                step={100}
                value={params.radiusM || 1500}
                onChange={(e) => updateNumber('radiusM', e.target.value)}
                className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-3 text-slate-100 placeholder-slate-500 focus:border-emerald-400 focus:outline-none"
              />
            </div>
          </div>
        </>
      )}

      <button
        onClick={onSearch}
        disabled={loading || !canSearch}
        className="mt-2 w-full rounded-xl bg-emerald-500 py-3 text-sm font-bold uppercase tracking-wide text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? 'Processing...' : params.mode === 'area' ? 'Generate Leads' : 'Analyze Property'}
      </button>
    </div>
  );
};
