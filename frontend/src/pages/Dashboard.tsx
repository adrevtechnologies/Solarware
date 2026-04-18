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
    country: 'South Africa',
    province: 'Western Cape',
    city: 'Cape Town',
    area: 'Goodwood',
    minRoofSqm: 150,
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

  const splitStreetInput = (street?: string): { street_number?: string; street_name?: string } => {
    const raw = (street || '').trim();
    if (!raw) {
      return { street_number: undefined, street_name: undefined };
    }

    const firstSpace = raw.indexOf(' ');
    if (firstSpace <= 0) {
      return { street_number: undefined, street_name: raw };
    }

    return {
      street_number: raw.slice(0, firstSpace).trim(),
      street_name: raw.slice(firstSpace + 1).trim(),
    };
  };

  const handleSearch = async () => {
    setLoading(true);
    setSearchMessage('');

    try {
      const streetParts = splitStreetInput(searchParams.street);
      const payload = {
        mode: 'area',
        country: searchParams.country,
        province: searchParams.province,
        city: searchParams.city,
        suburb: searchParams.area,
        street_number: streetParts.street_number,
        street_name: streetParts.street_name,
        exact_address: false,
        postcode: searchParams.postalCode,
        radius_m: 1500,
        include_residential: false,
        min_roof_sqm: searchParams.minRoofSqm || 150,
      };

      const response = await api.searchProspects(payload);
      setResults(response.data.results || []);
      setSearchMessage(response.data.message || '');
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
    setSelectedProspect(prospect);
    setImageModalOpen(true);
  };

  const handleGenerateMailPack = async (prospect: Prospect) => {
    try {
      setGeneratingPackId(prospect.osm_id);
      const response = await api.generateMailPack(prospect);
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
                  {`Area mode active for ${searchParams.area}, ${searchParams.city}.`}
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
        generating={!!(selectedProspect && generatingPackId === selectedProspect.osm_id)}
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
