import React, { useState } from 'react';
import { Prospect } from '../types';
import { GlobeHero } from '../components/GlobeHero';
import { SearchModeSelector, SearchMode } from '../components/SearchModeSelector';
import { SearchPanel, SearchParams } from '../components/SearchPanel';
import { FiltersPanel, Filters } from '../components/FiltersPanel';
import { ResultsTable } from '../components/ResultsTable';
import { ProposalModal } from '../components/ProposalModal';

export const Dashboard: React.FC = () => {
  const [mode, setMode] = useState<SearchMode>('area');
  const [searchParams, setSearchParams] = useState<SearchParams>({});
  const [filters, setFilters] = useState<Filters>({});
  const [results, setResults] = useState<Prospect[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchMessage, setSearchMessage] = useState('');
  const [proposalOpen, setProposalOpen] = useState(false);
  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null);

  const handleSearch = async () => {
    setLoading(true);
    setSearchMessage('');
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      // Build search payload based on mode
      const payload: any = {
        mode,
        radius_m: filters.radius || 500,
      };

      if (mode === 'address') {
        payload.street_number = searchParams.street?.split(' ')[0];
        payload.street_name = searchParams.street?.substring(searchParams.street.indexOf(' ') + 1);
        payload.suburb = searchParams.area;
        payload.city = searchParams.city;
        payload.province = searchParams.province;
        payload.postcode = searchParams.postalCode;
      } else if (mode === 'area') {
        payload.suburb = searchParams.area;
        payload.city = searchParams.city;
        payload.province = searchParams.province;
      } else if (mode === 'city') {
        payload.city = searchParams.city;
        payload.province = searchParams.province;
      } else if (mode === 'province') {
        payload.province = searchParams.province;
      } else if (mode === 'country') {
        // Country mode searches all
      }

      // Add building type filters
      if (filters.buildingTypes && filters.buildingTypes.length > 0) {
        payload.building_types = filters.buildingTypes;
      }

      // Add roof size filter
      if (filters.minRoofSqm) {
        payload.min_roof_sqm = filters.minRoofSqm;
      }

      const response = await fetch(`${apiUrl}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data.results || []);
      setSearchMessage(data.message || '');
    } catch (error) {
      console.error('Search error:', error);
      setSearchMessage(`❌ Search failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header with Globe */}
      <GlobeHero />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Panel: Search Controls (35%) */}
          <div>
            {/* Mode Selector */}
            <div className="mb-6">
              <SearchModeSelector mode={mode} onModeChange={setMode} />
            </div>

            {/* Search Panel */}
            <div className="mb-6">
              <SearchPanel
                mode={mode}
                params={searchParams}
                onParamsChange={setSearchParams}
                onSearch={handleSearch}
                loading={loading}
              />
            </div>

            {/* Filters Panel */}
            <div>
              <FiltersPanel filters={filters} onFiltersChange={setFilters} />
            </div>
          </div>

          {/* Right Panel: Results (65%) */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-lg p-6">
              {/* Header */}
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-900">
                  {results.length > 0
                    ? `✓ Found ${results.length} Solar Opportunities`
                    : 'Solar Prospects'}
                </h2>
                {searchMessage && (
                  <p className="text-sm text-gray-600 mt-2">{searchMessage}</p>
                )}
              </div>

              {/* Results Table */}
              <ResultsTable
                prospects={results}
                loading={loading}
                onSelectProspect={(prospect) => {
                  setSelectedProspect(prospect);
                  setProposalOpen(true);
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Proposal Modal */}
      {selectedProspect && (
        <ProposalModal
          isOpen={proposalOpen}
          onClose={() => setProposalOpen(false)}
          prospect={selectedProspect}
        />
      )}
    </div>
  );
  );
};

export default Dashboard;
