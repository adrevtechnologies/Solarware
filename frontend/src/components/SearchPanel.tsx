import React, { useRef } from 'react';
import { Autocomplete, useJsApiLoader } from '@react-google-maps/api';

export interface SearchParams {
  query: string;
  place_id?: string;
  lat?: number;
  lng?: number;
  formatted_address?: string;
  business_name?: string;
  min_roof_sqm?: number;
}

interface SearchPanelProps {
  params: SearchParams;
  onParamsChange: (params: SearchParams) => void;
  onSearchLeads: () => void;
  onScanArea: () => void;
  onSingleProperty: () => void;
  loading: boolean;
}

const GOOGLE_LIBRARIES = ['places'];

export const SearchPanel: React.FC<SearchPanelProps> = ({
  params,
  onParamsChange,
  onSearchLeads,
  onScanArea,
  onSingleProperty,
  loading,
}) => {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: import.meta.env.NEXT_PUBLIC_GOOGLE_MAPS_KEY,
    libraries: GOOGLE_LIBRARIES as ['places'],
  });

  const canSearch = !!params.query.trim();

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
      <div>
        <h2 className="text-xl font-bold text-slate-100">Find Solar Leads</h2>
        <p className="text-sm text-slate-400 mt-1">Search suburb, company, street, or area.</p>
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
          placeholder="Search suburb / company / street / area"
          className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-4 text-lg text-slate-100 placeholder-slate-500 focus:border-emerald-400 focus:outline-none"
          value={params.query}
          onChange={(e) => onParamsChange({ ...params, query: e.target.value })}
        />
      </Autocomplete>

      <div className="flex flex-wrap gap-2 text-xs text-slate-400">
        <span className="bg-slate-700 px-2 py-1 rounded">Goodwood</span>
        <span className="bg-slate-700 px-2 py-1 rounded">Makro Cape Gate</span>
        <span className="bg-slate-700 px-2 py-1 rounded">Montague Gardens</span>
        <span className="bg-slate-700 px-2 py-1 rounded">Parow Industrial</span>
      </div>

      <div>
        <label className="mb-2 block text-sm font-semibold text-slate-200">
          Min Roof Size (sqm)
        </label>
        <input
          type="number"
          min={0}
          step={10}
          placeholder="120"
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

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <button
          onClick={onSearchLeads}
          disabled={loading || !canSearch}
          className="rounded-xl bg-emerald-500 py-3 text-sm font-bold uppercase tracking-wide text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? 'Searching...' : 'Search Leads'}
        </button>
        <button
          onClick={onScanArea}
          disabled={loading || !canSearch}
          className="rounded-xl bg-blue-600 py-3 text-sm font-bold uppercase tracking-wide text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Scan Area
        </button>
        <button
          onClick={onSingleProperty}
          disabled={loading || !canSearch}
          className="rounded-xl bg-slate-600 py-3 text-sm font-bold uppercase tracking-wide text-white transition hover:bg-slate-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Single Property
        </button>
      </div>
    </div>
  );
};
