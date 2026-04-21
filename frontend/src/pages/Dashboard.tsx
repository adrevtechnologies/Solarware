import React, { useCallback, useEffect, useState } from 'react';
import { MailPack, Prospect } from '../types';
import { SearchPanel, SearchParams } from '../components/SearchPanel';
import { ResultsTable } from '../components/ResultsTable';
import { ProposalModal } from '../components/ProposalModal';
import { MailPackModal } from '../components/MailPackModal';
import { api } from '../services/api';

export const Dashboard: React.FC = () => {
  const apiBase = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

  const [searchParams, setSearchParams] = useState<SearchParams>({
    query: '',
    country: 'South Africa',
    province: '',
  });
  const [searchMode, setSearchMode] = useState<'area' | 'single-property'>('area');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [results, setResults] = useState<Prospect[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchMessage, setSearchMessage] = useState('');
  const [backendReady, setBackendReady] = useState(false);

  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null);
  const [imageModalOpen, setImageModalOpen] = useState(false);

  const [generatingPackId, setGeneratingPackId] = useState<string | null>(null);
  const [mailPack, setMailPack] = useState<MailPack | null>(null);
  const [mailPackOpen, setMailPackOpen] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(false);

  const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  const ensureBackendReady = useCallback(async (): Promise<boolean> => {
    if (backendReady) {
      return true;
    }

    for (let attempt = 1; attempt <= 3; attempt += 1) {
      try {
        await api.healthCheck();
        setBackendReady(true);
        return true;
      } catch (error) {
        console.warn('[Solarware] backend:wakeup:attempt_failed', { attempt, error });
        if (attempt < 3) {
          await sleep(1500 * attempt);
        }
      }
    }

    return false;
  }, [backendReady]);

  useEffect(() => {
    void ensureBackendReady();
  }, [ensureBackendReady]);

  const buildSearchPayload = (radiusM: number) => ({
    country: searchParams.country || 'South Africa',
    province: searchParams.province || '',
    city: '',
    suburb: searchParams.query.trim(),
    radius_m: radiusM,
    min_roof_sqm: searchParams.min_roof_sqm,
  });

  const handleAnalyzeProperty = async () => {
    setLoading(true);
    setSearchMessage('Analyzing property...');

    try {
      const ready = await ensureBackendReady();
      if (!ready) {
        setResults([]);
        setSearchMessage('Service temporarily unavailable. Please retry.');
        return;
      }

      const response = await api.searchProspects(buildSearchPayload(500));
      const propertyResults = (response.data.results || []).slice(0, 1);

      setResults(propertyResults);
      setSearchMessage(response.data.message || 'Property analyzed successfully.');
    } catch (error) {
      console.error('[Solarware] property-search:error', error);
      setResults([]);
      setSearchMessage(
        `Search failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAreaSearch = async () => {
    setLoading(true);
    setSearchMessage('Generating area leads...');

    try {
      const ready = await ensureBackendReady();
      if (!ready) {
        setResults([]);
        setSearchMessage('Service temporarily unavailable. Please retry.');
        return;
      }

      const response = await api.searchProspects(buildSearchPayload(1600));
      setResults(response.data.results || []);
      setSearchMessage(
        response.data.message ||
          `Lead generation complete: ${(response.data.results || []).length} viable properties ranked.`
      );
    } catch (error) {
      console.error('[Solarware] area-scan:error', error);
      setResults([]);
      setSearchMessage(
        `Area search failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleModeSearch = async () => {
    if (searchMode === 'area') {
      await handleAreaSearch();
      return;
    }

    await handleAnalyzeProperty();
  };

  const handleOpenImage = (prospect: Prospect) => {
    setSelectedProspect(prospect);
    setImageModalOpen(true);
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
        <header className="mb-8 flex min-h-[120px] w-full flex-row items-center gap-8 rounded-2xl bg-white px-8">
          <img src="/logo.png" alt="Solarware logo" className="h-32 w-auto object-contain" />
          <div className="flex flex-col justify-center">
            <h1 className="mb-1 text-2xl font-bold text-slate-900 sm:text-3xl">
              Your AI Solar Sales Rep
            </h1>
            <p className="max-w-xl text-base text-slate-700 sm:text-lg">
              Find qualified roof owners, generate proposals,{' '}
              <span className="whitespace-nowrap">book more deals automatically.</span>
            </p>
          </div>
        </header>

        <div className="grid gap-6 lg:grid-cols-12">
          <div className="lg:col-span-4">
            <SearchPanel
              params={searchParams}
              mode={searchMode}
              showAdvanced={showAdvanced}
              onParamsChange={setSearchParams}
              onModeChange={setSearchMode}
              onToggleAdvanced={() => setShowAdvanced((prev) => !prev)}
              onFindLeads={handleModeSearch}
              loading={loading}
            />
          </div>

          <div className="lg:col-span-8">
            <div className="mb-4 rounded-xl border border-slate-700 bg-slate-900/70 p-4">
              <h2 className="text-lg font-semibold text-slate-100">Results</h2>
              {searchMessage && <p className="mt-1 text-sm text-slate-300">{searchMessage}</p>}
              {!searchMessage && (
                <p className="mt-1 text-sm text-slate-400">
                  {searchMode === 'area'
                    ? 'Generate leads for a suburb-level search area.'
                    : 'Analyze one property with detailed roof and solar output.'}
                </p>
              )}
            </div>

            <ResultsTable
              prospects={results}
              loading={loading}
              noResultsMessage={'No viable commercial roofs found for this search.'}
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
