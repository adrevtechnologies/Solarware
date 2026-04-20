import React, { useRef } from 'react';
import { Autocomplete, useJsApiLoader } from '@react-google-maps/api';
import { COUNTRIES, PROVINCES_BY_COUNTRY } from '../data/locationOptions';

export interface SearchParams {
  query: string;
  country?: string;
  province?: string;
  place_id?: string;
  lat?: number;
  lng?: number;
  formatted_address?: string;
  business_name?: string;
  min_roof_sqm?: number;
}

interface SearchPanelProps {
  params: SearchParams;
  mode: 'area' | 'single-property';
  showAdvanced: boolean;
  onParamsChange: (params: SearchParams) => void;
  onModeChange: (mode: 'area' | 'single-property') => void;
  onToggleAdvanced: () => void;
  onFindLeads: () => void;
  loading: boolean;
}

const GOOGLE_LIBRARIES = ['places'];

export const SearchPanel: React.FC<SearchPanelProps> = ({
  params,
  mode,
  showAdvanced,
  onParamsChange,
  onModeChange,
  onToggleAdvanced,
  onFindLeads,
  loading,
}) => {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: import.meta.env.NEXT_PUBLIC_GOOGLE_MAPS_KEY,
    libraries: GOOGLE_LIBRARIES as ['places'],
  });

  const canSearch = !!params.query.trim();
  const provinceOptions = PROVINCES_BY_COUNTRY[params.country || 'South Africa'] || [];

  const handlePlaceChanged = () => {
    const place = autocompleteRef.current?.getPlace();
    if (!place || !place.geometry || !place.place_id) {
      return;
    }

    onParamsChange({
      ...params,
      query: place.formatted_address || place.name || params.query,
      place_id: place.place_id,
      lat: place.geometry.location?.lat(),
      lng: place.geometry.location?.lng(),
      formatted_address: place.formatted_address || '',
      business_name: place.name || '',
    });
  };

  if (!isLoaded) {
    return (
      <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-6 text-slate-300">
        Loading Google Maps...
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-6 shadow-xl backdrop-blur-sm space-y-6">
      <div className="flex gap-2 rounded-xl border border-slate-700 bg-slate-950/50 p-1">
        <button
          type="button"
          onClick={() => onModeChange('area')}
          className={`flex-1 rounded-lg px-3 py-2 text-sm font-semibold transition ${
            mode === 'area' ? 'bg-emerald-500 text-slate-950' : 'text-slate-300 hover:bg-slate-800'
          }`}
        >
          Area Search
        </button>
        <button
          type="button"
          onClick={() => onModeChange('single-property')}
          className={`flex-1 rounded-lg px-3 py-2 text-sm font-semibold transition ${
            mode === 'single-property'
              ? 'bg-emerald-500 text-slate-950'
              : 'text-slate-300 hover:bg-slate-800'
          }`}
        >
          Single Property
        </button>
      </div>

      <div>
        <h2 className="text-xl font-bold text-slate-100">
          {mode === 'area' ? 'Search Area' : 'Search Property'}
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          {mode === 'area'
            ? 'Find viable commercial rooftops in this area.'
            : 'Run a detailed roof and solar estimate.'}
        </p>
      </div>

      <Autocomplete
        onLoad={(autocomplete) => {
          autocompleteRef.current = autocomplete;
        }}
        onPlaceChanged={handlePlaceChanged}
      >
        <input
          ref={inputRef}
          type="text"
          placeholder={
            mode === 'area'
              ? 'Enter suburb here , eg. Montague Gardens...'
              : 'Enter full address or business name...'
          }
          className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-4 text-lg text-slate-100 placeholder-slate-500 focus:border-emerald-400 focus:outline-none"
          value={params.query}
          onChange={(e) => onParamsChange({ ...params, query: e.target.value })}
        />
      </Autocomplete>

      <button
        type="button"
        onClick={onToggleAdvanced}
        className="w-fit text-sm font-medium text-slate-300 underline-offset-2 hover:text-slate-100 hover:underline"
      >
        Advanced Search
      </button>

      {showAdvanced && mode === 'area' && (
        <div className="space-y-4 rounded-xl border border-slate-700 bg-slate-950/40 p-4">
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-200">Country</label>
            <select
              title="Country"
              value={params.country || 'South Africa'}
              onChange={(e) =>
                onParamsChange({
                  ...params,
                  country: e.target.value,
                  province: '',
                })
              }
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
            <label className="mb-2 block text-sm font-semibold text-slate-200">
              Province / State
            </label>
            <select
              title="Province or state"
              value={params.province || ''}
              onChange={(e) => onParamsChange({ ...params, province: e.target.value })}
              className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-3 text-slate-100 focus:border-emerald-400 focus:outline-none"
            >
              <option value="">Auto detect</option>
              {provinceOptions.map((province) => (
                <option key={province} value={province}>
                  {province}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-200">
              Min Roof Size (sqm)
            </label>
            <input
              type="number"
              title="Minimum roof size in square meters"
              min={0}
              step={10}
              placeholder="Optional"
              className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-3 text-slate-100 placeholder-slate-500 focus:border-emerald-400 focus:outline-none"
              value={params.min_roof_sqm ?? ''}
              onChange={(e) => {
                const raw = e.target.value.trim();
                const parsed = raw ? Number(raw) : undefined;
                onParamsChange({
                  ...params,
                  min_roof_sqm:
                    parsed !== undefined && Number.isFinite(parsed)
                      ? Math.max(0, Math.floor(parsed))
                      : undefined,
                });
              }}
            />
          </div>
        </div>
      )}

      <div className="grid grid-cols-1">
        <button
          onClick={onFindLeads}
          disabled={loading || !canSearch}
          className="rounded-xl bg-emerald-500 py-3 text-sm font-bold uppercase tracking-wide text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? 'Working...' : mode === 'area' ? 'Generate Leads' : 'Analyze Property'}
        </button>
      </div>
    </div>
  );
};
