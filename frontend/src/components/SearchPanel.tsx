import React, { useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../services/api';

export interface SearchParams {
  query: string;
  city?: string;
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
  onParamsChange: (params: SearchParams) => void;
  onModeChange: (mode: 'area' | 'single-property') => void;
  onFindLeads: () => void;
  loading: boolean;
}

interface PlacesSuggestion {
  placeId: string;
  mainText: string;
  secondaryText: string;
  fullText: string;
}

export const SearchPanel: React.FC<SearchPanelProps> = ({
  params,
  mode,
  onParamsChange,
  onModeChange,
  onFindLeads,
  loading,
}) => {
  const blurTimerRef = useRef<number | null>(null);
  const sessionTokenRef = useRef<string>(crypto.randomUUID());
  const [suggestions, setSuggestions] = useState<PlacesSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [suggestionRequestTick, setSuggestionRequestTick] = useState(0);
  const [fetchingDetails, setFetchingDetails] = useState(false);

  const canSearch = !!params.query.trim();
  const locationSelected = !!params.place_id;
  const placeholder = useMemo(
    () =>
      mode === 'area' ? 'Enter suburb / area / city' : 'Enter full address or business name...',
    [mode]
  );

  useEffect(() => {
    const query = params.query.trim();
    if (query.length < 1) {
      setSuggestions([]);
      setLoadingSuggestions(false);
      return;
    }

    const timer = window.setTimeout(async () => {
      try {
        setLoadingSuggestions(true);
        const response = await api.placesAutocomplete({
          input: query,
          session_token: sessionTokenRef.current,
          region_code: 'za',
        });

        const mapped: PlacesSuggestion[] = (response.data?.suggestions || []).map((s) => ({
          placeId: s.place_id,
          mainText: s.main_text,
          secondaryText: s.secondary_text || '',
          fullText: s.full_text,
        }));

        setSuggestions(mapped);
      } catch {
        setSuggestions([]);
      } finally {
        setLoadingSuggestions(false);
      }
    }, 250);

    return () => window.clearTimeout(timer);
  }, [params.query, suggestionRequestTick]);

  const handleSuggestionSelect = async (suggestion: PlacesSuggestion) => {
    setFetchingDetails(true);
    try {
      const response = await api.placeDetails(suggestion.placeId, sessionTokenRef.current);
      const place = response.data;

      onParamsChange({
        ...params,
        query: place.formatted_address || suggestion.fullText,
        place_id: place.place_id || suggestion.placeId,
        formatted_address: place.formatted_address || suggestion.fullText,
        business_name: place.business_name || '',
        lat: place.lat,
        lng: place.lng,
        city: place.city,
        province: place.province,
        country: place.country || 'South Africa',
      });

      setShowSuggestions(false);
      setSuggestions([]);
      sessionTokenRef.current = crypto.randomUUID();
    } catch {
      // Keep existing query untouched on transient API failures.
    } finally {
      setFetchingDetails(false);
    }
  };

  const handleInputBlur = () => {
    blurTimerRef.current = window.setTimeout(() => {
      setShowSuggestions(false);
    }, 140);
  };

  const handleInputFocus = () => {
    if (blurTimerRef.current) {
      window.clearTimeout(blurTimerRef.current);
      blurTimerRef.current = null;
    }
    setShowSuggestions(true);
    if (params.query.trim().length >= 1) {
      setSuggestionRequestTick((tick) => tick + 1);
    }
  };

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

      <div className="space-y-2">
        <div className="relative">
          <input
            type="text"
            placeholder={placeholder}
            autoComplete="off"
            spellCheck={false}
            autoCorrect="off"
            autoCapitalize="none"
            className={`w-full rounded-xl border px-4 py-4 text-lg text-slate-100 placeholder-slate-500 focus:outline-none transition ${
              locationSelected
                ? 'border-emerald-500 bg-slate-800 focus:border-emerald-400'
                : 'border-slate-600 bg-slate-800 focus:border-emerald-400'
            }`}
            value={params.query}
            onFocus={handleInputFocus}
            onBlur={handleInputBlur}
            onChange={(e) => {
              onParamsChange({
                ...params,
                query: e.target.value,
                place_id: undefined,
                formatted_address: undefined,
                business_name: undefined,
                lat: undefined,
                lng: undefined,
                city: undefined,
                province: undefined,
                country: undefined,
              });
              setShowSuggestions(true);
            }}
          />
          {fetchingDetails && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent"></div>
            </div>
          )}
          {showSuggestions && (loadingSuggestions || suggestions.length > 0) && (
            <div className="absolute z-20 mt-2 max-h-72 w-full overflow-y-auto rounded-xl border border-slate-700 bg-slate-900 shadow-2xl">
              {loadingSuggestions && (
                <div className="px-4 py-3 text-sm text-slate-400">Searching places...</div>
              )}
              {!loadingSuggestions &&
                suggestions.map((suggestion) => (
                  <button
                    key={suggestion.placeId}
                    type="button"
                    onMouseDown={() => {
                      void handleSuggestionSelect(suggestion);
                    }}
                    className="w-full border-b border-slate-800 px-4 py-3 text-left last:border-b-0 hover:bg-slate-800"
                  >
                    <div className="text-sm font-semibold text-slate-100">
                      {suggestion.mainText}
                    </div>
                    {!!suggestion.secondaryText && (
                      <div className="text-xs text-slate-400">{suggestion.secondaryText}</div>
                    )}
                  </button>
                ))}
            </div>
          )}
        </div>
        <p className="text-xs text-slate-400">
          {locationSelected ? (
            <span className="text-emerald-400">✓ Location confirmed</span>
          ) : (
            'Start typing a suburb, area, or city name, then select from the dropdown'
          )}
        </p>
      </div>

      <div className="space-y-2">
        <label htmlFor="min-roof-size" className="block text-sm font-medium text-slate-300">
          Minimum Roof Size (optional)
        </label>
        <div className="relative">
          <input
            id="min-roof-size"
            type="number"
            min="0"
            step="10"
            placeholder="e.g., 100"
            className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-3 text-slate-100 placeholder-slate-500 focus:border-emerald-400 focus:outline-none"
            value={params.min_roof_sqm || ''}
            onChange={(e) => {
              const value = e.target.value;
              onParamsChange({
                ...params,
                min_roof_sqm: value ? parseInt(value, 10) : undefined,
              });
            }}
          />
          <span className="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-slate-500">
            m²
          </span>
        </div>
        <p className="text-xs text-slate-400">
          Filter buildings by minimum roof area in square meters
        </p>
      </div>

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
