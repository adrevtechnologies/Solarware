import React from 'react';
import { CITIES_BY_PROVINCE, COUNTRIES, PROVINCES_BY_COUNTRY } from '../data/locationOptions';

export interface SearchParams {
  country: string;
  province: string;
  city: string;
  area: string;
  street?: string;
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
  const provinceOptions = PROVINCES_BY_COUNTRY[params.country] || [];
  const cityOptions = CITIES_BY_PROVINCE[params.province] || [];

  const updateParam = (key: keyof SearchParams, value: string) => {
    onParamsChange({ ...params, [key]: value });
  };

  const canSearch =
    !!params.country.trim() &&
    !!params.province.trim() &&
    !!params.city.trim() &&
    !!params.area.trim();

  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-6 shadow-xl backdrop-blur-sm space-y-4">
      <div>
        <h2 className="text-xl font-bold text-slate-100">Target Search</h2>
        <p className="text-sm text-slate-400 mt-1">
          Street address is optional. When provided, Solarware performs exact address search only.
        </p>
      </div>

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
        <label className="block text-sm font-semibold text-slate-200 mb-2">Province / State</label>
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
        <label className="block text-sm font-semibold text-slate-200 mb-2">Area / Suburb</label>
        <input
          type="text"
          placeholder="Goodwood"
          value={params.area}
          onChange={(e) => updateParam('area', e.target.value)}
          className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-3 text-slate-100 placeholder-slate-500 focus:border-emerald-400 focus:outline-none"
        />
      </div>

      <div>
        <label className="block text-sm font-semibold text-slate-200 mb-2">
          Street Address (optional)
        </label>
        <input
          type="text"
          placeholder="98 Richmond Street"
          value={params.street || ''}
          onChange={(e) => updateParam('street', e.target.value)}
          className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-3 text-slate-100 placeholder-slate-500 focus:border-emerald-400 focus:outline-none"
        />
      </div>

      <button
        onClick={onSearch}
        disabled={loading || !canSearch}
        className="mt-2 w-full rounded-xl bg-emerald-500 py-3 text-sm font-bold uppercase tracking-wide text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? 'Searching...' : 'Search'}
      </button>
    </div>
  );
};
