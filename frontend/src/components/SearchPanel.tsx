import React, { useCallback, useEffect, useRef, useState } from 'react';
import { COUNTRIES, PROVINCES_BY_COUNTRY } from '../data/locationOptions';
import { api } from '../services/api';

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

interface Suggestion {
  place_id: string;
  main_text: string;
  secondary_text: string;
  full_text: string;
}

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
  const containerRef = useRef<HTMLDivElement | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const canSearch = !!params.query.trim();
  const provinceOptions = PROVINCES_BY_COUNTRY[params.country || 'South Africa'] || [];

  const fetchSuggestions = useCallback(async (query: string) => {
    if (!query.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    try {
      const res = await api.placesAutocomplete(query);
      setSuggestions(res.data.suggestions || []);
      setShowSuggestions(true);
    } catch {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    onParamsChange({
      ...params,
      query: value,
      place_id: undefined,
      lat: undefined,
      lng: undefined,
      formatted_address: undefined,
      business_name: undefined,
    });
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(value), 300);
  };

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  const handleSelectSuggestion = async (suggestion: Suggestion) => {
    setShowSuggestions(false);
    setSuggestions([]);
    try {
      const details = await api.placeDetails(suggestion.place_id);
      onParamsChange({
        ...params,
        query: details.data.formatted_address || suggestion.full_text,
        place_id: details.data.place_id,
        lat: details.data.lat,
        lng: details.data.lng,
        formatted_address: details.data.formatted_address || '',
        business_name: details.data.business_name || '',
      });
    } catch {
      onParamsChange({ ...params, query: suggestion.full_text });
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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

      <div ref={containerRef} className="relative search-autocomplete-container">
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
          onChange={handleInputChange}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          autoComplete="off"
        />
        {showSuggestions && suggestions.length > 0 && (
          <ul className="absolute z-50 mt-1 w-full rounded-xl border border-slate-600 bg-slate-800 py-1 shadow-xl">
            {suggestions.map((s) => (
              <li
                key={s.place_id}
                onMouseDown={() => handleSelectSuggestion(s)}
                className="cursor-pointer px-4 py-3 text-sm text-slate-100 hover:bg-slate-700"
              >
                <span className="font-medium">{s.main_text}</span>
                {s.secondary_text && (
                  <span className="ml-1 text-slate-400">{s.secondary_text}</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

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
