import React, { useState } from 'react';
import { MailPack, Prospect } from '../types';
import { SearchPanel, SearchParams } from '../components/SearchPanel';
import { ResultsTable } from '../components/ResultsTable';
import { ProposalModal } from '../components/ProposalModal';
import { MailPackModal } from '../components/MailPackModal';
import { api } from '../services/api';

export const Dashboard: React.FC = () => {
  const apiBase = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

  const [searchParams, setSearchParams] = useState<SearchParams>({
    mode: 'area',
    country: 'South Africa',
    province: 'Western Cape',
    city: 'Cape Town',
    area: 'Goodwood',
    radiusM: 1500,
    propertyQuery: '',
  });

  const [results, setResults] = useState<Prospect[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchMessage, setSearchMessage] = useState('');

  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null);
  const [imageModalOpen, setImageModalOpen] = useState(false);

  const [generatingPackId, setGeneratingPackId] = useState<string | null>(null);
  const [mailPack, setMailPack] = useState<MailPack | null>(null);
  const [mailPackOpen, setMailPackOpen] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    setSearchMessage('');

    try {
      if (searchParams.mode === 'area') {
        const selected = searchParams.selectedAreaPlace;
        if (!selected) {
          setResults([]);
          setSearchMessage('Select an area from the Google dropdown before generating leads.');
          return;
        }

        const response = await api.areaSearch({
          place_id: selected.place_id,
          query: selected.formatted_address,
          lat: selected.lat,
          lng: selected.lng,
          radius_m: searchParams.radiusM || 1500,
        });

        const mapped: Prospect[] = (response.data.results || []).map((lead) => ({
          lead_id: lead.lead_id,
          address: lead.address,
          suburb: selected.formatted_address,
          city: selected.city || searchParams.city,
          business_name: lead.name,
          building_type: lead.building_type,
          roof_area_sqm: lead.roof_area_sqm,
          estimated_panel_count: 0,
          capacity_low_kw: 0,
          capacity_high_kw: 0,
          annual_kwh: 0,
          savings_low: 0,
          savings_high: 0,
          savings_potential_display: '',
          solar_score: lead.score,
          latitude: lead.lat,
          longitude: lead.lng,
        }));

        setResults(mapped);
        setSearchMessage(`Found ${response.data.count} leads in ${selected.formatted_address}.`);
        return;
      }

      const selectedProperty = searchParams.selectedPropertyPlace;
      if (!selectedProperty) {
        setResults([]);
        setSearchMessage('Select a property from the Google dropdown before analyzing.');
        return;
      }

      const propertyResponse = await api.propertySearch({
        place_id: selectedProperty.place_id,
        query: searchParams.propertyQuery || selectedProperty.formatted_address,
      });
      const d = propertyResponse.data;
      const oneResult: Prospect = {
        lead_id: d.lead_id,
        address: d.address,
        suburb: selectedProperty.formatted_address,
        city: selectedProperty.city || searchParams.city,
        business_name: d.name,
        building_type: d.building_type,
        roof_area_sqm: d.roof_area_sqm,
        estimated_panel_count: d.panel_count,
        capacity_low_kw: d.capacity_kw,
        capacity_high_kw: d.capacity_kw,
        annual_kwh: d.annual_kwh,
        savings_low: d.savings_year,
        savings_high: d.savings_year,
        savings_potential_display: `R ${Math.round(d.savings_year).toLocaleString()} / year`,
        solar_score: d.score,
        latitude: d.lat,
        longitude: d.lng,
      };
      setResults([oneResult]);
      setSearchMessage(`Analyzed property: ${d.name}`);
    } catch (error) {
      setResults([]);
      setSearchMessage(
        `Search failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleOpenImage = (prospect: Prospect) => {
    void (async () => {
      try {
        setGeneratingPackId(prospect.lead_id);
        const enriched = await api.enrichLead(prospect);
        setSelectedProspect(enriched.data);
        setImageModalOpen(true);
      } catch (error) {
        setSelectedProspect(prospect);
        setImageModalOpen(true);
        setSearchMessage(
          `Lead enrichment partial: ${error instanceof Error ? error.message : 'Unknown error'}`
        );
      } finally {
        setGeneratingPackId(null);
      }
    })();
  };

  const handleGenerateMailPack = async (prospect: Prospect) => {
    try {
      setGeneratingPackId(prospect.lead_id);
      const response = await api.generateMailPack(prospect.lead_id);
      const pack = response.data;

      const withAbsoluteUrls: MailPack = {
        ...pack,
        before_image_url:
          pack.before_image_url.startsWith('http') || !apiBase
            ? pack.before_image_url
            : `${apiBase}${pack.before_image_url}`,
        after_image_url:
          pack.after_image_url.startsWith('http') || !apiBase
            ? pack.after_image_url
            : `${apiBase}${pack.after_image_url}`,
        before_after_image_url:
          pack.before_after_image_url.startsWith('http') || !apiBase
            ? pack.before_after_image_url
            : `${apiBase}${pack.before_after_image_url}`,
        pdf_url:
          pack.pdf_url.startsWith('http') || !apiBase ? pack.pdf_url : `${apiBase}${pack.pdf_url}`,
      };

      setMailPack(withAbsoluteUrls);
      setSelectedProspect(prospect);
      setMailPackOpen(true);
      setImageModalOpen(false);
    } catch (error) {
      setSearchMessage(
        `Mail pack generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    } finally {
      setGeneratingPackId(null);
    }
  };

  const handleSendEmail = async (recipientEmail: string) => {
    if (!mailPack || !recipientEmail) {
      return;
    }

    try {
      setSendingEmail(true);
      await api.sendMailPack(
        {
          email_subject: mailPack.email_subject,
          email_body: mailPack.email_body,
        },
        recipientEmail
      );
      setSearchMessage('Email sent successfully.');
    } catch (error) {
      setSearchMessage(
        `Email send failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    } finally {
      setSendingEmail(false);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_#1f2937_0%,_#0f172a_55%,_#020617_100%)] text-slate-100">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:py-10">
        <header className="mb-8 rounded-2xl border border-slate-700 bg-slate-900/70 p-6">
          <h1 className="text-3xl font-bold tracking-tight">Solarware V1</h1>
          <p className="mt-2 text-sm text-slate-300">
            Real commercial roof discovery for area-targeted outreach.
          </p>
        </header>

        <div className="grid gap-6 lg:grid-cols-12">
          <div className="lg:col-span-4">
            <SearchPanel
              params={searchParams}
              onParamsChange={setSearchParams}
              onSearch={handleSearch}
              loading={loading}
            />
          </div>

          <div className="lg:col-span-8">
            <div className="mb-4 rounded-xl border border-slate-700 bg-slate-900/70 p-4">
              <h2 className="text-lg font-semibold text-slate-100">Results</h2>
              {searchMessage && <p className="mt-1 text-sm text-slate-300">{searchMessage}</p>}
              {!searchMessage && (
                <p className="mt-1 text-sm text-slate-400">
                  {searchParams.mode === 'area'
                    ? `Area mode active for ${searchParams.area || 'selected area'}.`
                    : 'Single Property mode active.'}
                </p>
              )}
            </div>

            <ResultsTable
              prospects={results}
              loading={loading}
              noResultsMessage={`No viable commercial roofs found in ${searchParams.area}.`}
              generatingPackId={generatingPackId}
              onViewImage={handleOpenImage}
              onGenerateMailPack={handleGenerateMailPack}
            />
          </div>
        </div>
      </div>

      <ProposalModal
        isOpen={imageModalOpen}
        onClose={() => setImageModalOpen(false)}
        prospect={selectedProspect || undefined}
        generating={!!(selectedProspect && generatingPackId === selectedProspect.lead_id)}
        onGenerateMailPack={() => {
          if (selectedProspect) {
            void handleGenerateMailPack(selectedProspect);
          }
        }}
      />

      <MailPackModal
        isOpen={mailPackOpen}
        onClose={() => setMailPackOpen(false)}
        pack={mailPack}
        prospect={selectedProspect}
        sendingEmail={sendingEmail}
        onSendEmail={handleSendEmail}
      />
    </div>
  );
};

export default Dashboard;
