import React, { useState } from 'react';
import { GlobeHero } from '../components/GlobeHero';
import { SearchModeSelector, SearchMode } from '../components/SearchModeSelector';
import { SearchPanel, SearchParams } from '../components/SearchPanel';
import { FiltersPanel, Filters } from '../components/FiltersPanel';
import { ResultsTable, Prospect } from '../components/ResultsTable';
import { ProposalModal } from '../components/ProposalModal';

export const Dashboard: React.FC = () => {
  const [mode, setMode] = useState<SearchMode>('area');
  const [searchParams, setSearchParams] = useState<SearchParams>({});
  const [filters, setFilters] = useState<Filters>({});
  const [results, setResults] = useState<Prospect[]>([]);
  const [loading, setLoading] = useState(false);
  const [proposalOpen, setProposalOpen] = useState(false);
  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      const payload = {
        mode,
        ...searchParams,
        filters,
      };

      const response = await fetch(`${apiUrl}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error('Search failed');
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error('Search error:', error);
      alert('Failed to search. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleProposal = (prospectId: string) => {
    const prospect = results.find((p) => p.id === prospectId);
    if (prospect) {
      setSelectedProspect(prospect);
      setProposalOpen(true);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header with Globe */}
      <GlobeHero />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Panel: Search Controls */}
          <div className="lg:col-span-1">
            {/* Mode Selector */}
            <SearchModeSelector mode={mode} onModeChange={setMode} />

            {/* Search Panel */}
            <SearchPanel
              mode={mode}
              params={searchParams}
              onParamsChange={setSearchParams}
              onSearch={handleSearch}
              loading={loading}
            />

            {/* Filters Panel */}
            <FiltersPanel filters={filters} onFiltersChange={setFilters} />
          </div>

          {/* Right Panel: Results */}
          <div className="lg:col-span-2">
            <div className="bg-gray-50 rounded-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                {results.length > 0
                  ? `Found ${results.length} Solar Opportunities`
                  : 'Ready to search'}
              </h2>
              <ResultsTable prospects={results} loading={loading} onProposal={handleProposal} />
            </div>
          </div>
        </div>
      </div>

      {/* Proposal Modal */}
      <ProposalModal
        isOpen={proposalOpen}
        onClose={() => setProposalOpen(false)}
        prospect={selectedProspect || undefined}
      />
    </div>
  );
};

export default Dashboard;
