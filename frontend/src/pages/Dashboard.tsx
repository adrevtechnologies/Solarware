import React, { useEffect, useState } from 'react';

import { SearchAreaForm } from '../components/SearchAreaForm';
import { ProspectList } from '../components/ProspectList';
import { api } from '../services/api';
import { SearchArea } from '../types';

export const Dashboard: React.FC = () => {
  const [searchAreas, setSearchAreas] = useState<SearchArea[]>([]);
  const [selectedArea, setSelectedArea] = useState<SearchArea | null>(null);
  const [prospects, setProspects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [proposal, setProposal] = useState<any | null>(null);
  const [proposalLoadingId, setProposalLoadingId] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<string | null>(null);

  useEffect(() => {
    loadSearchAreas();
  }, []);

  const loadSearchAreas = async () => {
    try {
      const response = await api.listSearchAreas();
      const rows = Array.isArray(response.data) ? response.data : [];
      setSearchAreas(rows);
      if (rows.length > 0) {
        setSelectedArea(rows[0]);
        await loadProspects(rows[0].id as string);
      }
    } catch (error) {
      console.error('Failed to load search areas:', error);
    }
  };

  const loadProspects = async (areaId: string) => {
    setLoading(true);
    try {
      const response = await api.listProspects(areaId);
      setProspects(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Failed to load prospects:', error);
      setProspects([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateArea = async (data: SearchArea) => {
    try {
      const response = await api.createSearchArea(data);
      const area = response.data;
      setSearchAreas((prev) => [...prev, area]);
      setSelectedArea(area);

      setProcessing(true);
      setProcessingStatus('Queued...');
      await api.processSearchArea(area.id);

      const maxAttempts = 60;
      for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        const statusResp = await api.getProcessingStatus(area.id);
        const status = statusResp.data?.status || 'unknown';
        setProcessingStatus(status);

        if (status === 'completed') {
          break;
        }
        if (status === 'failed') {
          throw new Error(statusResp.data?.errors?.join(', ') || 'Processing failed');
        }
      }

      await loadProspects(area.id);
    } catch (error: any) {
      console.error('Error creating area:', error);
      alert(`Error: ${error?.response?.data?.detail || error.message || 'Unknown error'}`);
    } finally {
      setProcessing(false);
      setProcessingStatus(null);
    }
  };

  const handleGenerateProposal = async (prospectId: string) => {
    try {
      setProposalLoadingId(prospectId);
      const response = await api.generateProposal(prospectId);
      setProposal(response.data);
    } catch (error) {
      console.error('Failed to generate proposal:', error);
      alert('Unable to generate proposal right now.');
    } finally {
      setProposalLoadingId(null);
    }
  };

  const exportCSV = async () => {
    try {
      const response = await api.exportProspectsCSV();
      const blob = response.data;
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'prospects.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to export CSV:', error);
    }
  };

  const summary = React.useMemo(() => {
    const totalLeads = prospects.length;
    const avgScore =
      totalLeads > 0
        ? Math.round(
            prospects.reduce((sum, p) => sum + Number(p.suitability_score || 0), 0) / totalLeads
          )
        : 0;
    const totalRoofSqft = prospects.reduce((sum, p) => sum + Number(p.roof_area_sqft || 0), 0);
    const contactCoverage =
      totalLeads > 0
        ? Math.round(
            (prospects.filter((p) => p.contact_email || p.contact_phone).length / totalLeads) * 100
          )
        : 0;

    return {
      totalLeads,
      avgScore,
      totalRoofSqft,
      contactCoverage,
    };
  }, [prospects]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Solarware</h1>
          <p className="mt-1 text-gray-600">Lead Discovery MVP</p>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <SearchAreaForm onSubmit={handleCreateArea} loading={processing} />
          </div>

          <div className="lg:col-span-2">
            {selectedArea && (
              <div className="rounded-lg bg-white p-6 shadow">
                <div className="mb-4 flex items-start justify-between">
                  <div>
                    <h2 className="text-2xl font-bold">{selectedArea.name}</h2>
                    <p className="text-gray-600">
                      {selectedArea.country} {selectedArea.region && `- ${selectedArea.region}`}
                    </p>
                  </div>
                  <button
                    onClick={exportCSV}
                    className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
                  >
                    Export CSV
                  </button>
                </div>

                <div className="mb-6 grid grid-cols-2 gap-3 rounded bg-blue-50 p-4 md:grid-cols-4">
                  <div>
                    <p className="text-xs text-gray-500">Leads</p>
                    <p className="text-xl font-semibold text-gray-900">{summary.totalLeads}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Average Score</p>
                    <p className="text-xl font-semibold text-gray-900">{summary.avgScore}/100</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Total Roof</p>
                    <p className="text-xl font-semibold text-gray-900">
                      {summary.totalRoofSqft.toLocaleString()} sqft
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Contact Coverage</p>
                    <p className="text-xl font-semibold text-gray-900">
                      {summary.contactCoverage}%
                    </p>
                  </div>
                </div>

                <h3 className="mb-4 text-lg font-semibold">Ranked Leads</h3>
                {processing && processingStatus && (
                  <div className="mb-4 rounded bg-amber-50 px-3 py-2 text-sm text-amber-900">
                    Processing status: {processingStatus}
                  </div>
                )}
                {loading ? (
                  <div className="py-8 text-center text-gray-500">Loading leads...</div>
                ) : prospects.length === 0 ? (
                  <div className="py-8 text-center text-gray-500">
                    No leads yet. Start processing a search area.
                  </div>
                ) : (
                  <ProspectList
                    prospects={prospects}
                    onGenerateProposal={handleGenerateProposal}
                    proposalLoadingId={proposalLoadingId}
                  />
                )}
              </div>
            )}
          </div>
        </div>

        {proposal && (
          <section className="rounded-lg bg-white p-6 shadow">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-xl font-bold">Generated Proposal</h3>
              <button
                onClick={() => setProposal(null)}
                className="rounded bg-gray-100 px-3 py-1 text-sm text-gray-700 hover:bg-gray-200"
              >
                Close
              </button>
            </div>

            <p className="mb-4 text-sm text-gray-700">{proposal.sales_message}</p>

            <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded border border-gray-200 p-3">
                <p className="mb-1 text-xs font-semibold text-gray-500">Mockup Image</p>
                {proposal.mockup_image ? (
                  <img
                    src={proposal.mockup_image}
                    alt="Solar mockup"
                    className="max-h-80 w-full rounded border border-gray-200 object-contain"
                  />
                ) : (
                  <p className="break-all text-xs text-gray-700">Unavailable</p>
                )}
              </div>
              <div className="rounded border border-gray-200 p-3">
                <p className="mb-1 text-xs font-semibold text-gray-500">Before/After Image</p>
                {proposal.before_after_image ? (
                  <img
                    src={proposal.before_after_image}
                    alt="Before and after"
                    className="max-h-80 w-full rounded border border-gray-200 object-contain"
                  />
                ) : (
                  <p className="break-all text-xs text-gray-700">Unavailable</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="rounded bg-blue-50 p-3">
                <p className="mb-2 text-xs font-semibold text-gray-600">Cold Email</p>
                <p className="whitespace-pre-wrap text-sm text-gray-800">
                  {proposal.outreach?.cold_email || 'Not generated'}
                </p>
              </div>
              <div className="rounded bg-green-50 p-3">
                <p className="mb-2 text-xs font-semibold text-gray-600">WhatsApp Intro</p>
                <p className="whitespace-pre-wrap text-sm text-gray-800">
                  {proposal.outreach?.whatsapp_intro || 'Not generated'}
                </p>
              </div>
              <div className="rounded bg-amber-50 p-3">
                <p className="mb-2 text-xs font-semibold text-gray-600">Follow-up Text</p>
                <p className="whitespace-pre-wrap text-sm text-gray-800">
                  {proposal.outreach?.follow_up_text || 'Not generated'}
                </p>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
