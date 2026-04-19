import React, { useCallback, useEffect, useState } from 'react';
import { MailPack, Prospect } from '../types';
import { SearchPanel, SearchParams } from '../components/SearchPanel';
import { ResultsSort, ResultsTable } from '../components/ResultsTable';
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
  });
  const [sortBy, setSortBy] = useState<ResultsSort>('largest_roof');

  const [results, setResults] = useState<Prospect[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchMessage, setSearchMessage] = useState('');
  const [warmingBackend, setWarmingBackend] = useState(false);
  const [backendReady, setBackendReady] = useState(false);
  const [areaOptions, setAreaOptions] = useState<string[]>([]);

  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null);
  const [imageModalOpen, setImageModalOpen] = useState(false);

  const [generatingPackId, setGeneratingPackId] = useState<string | null>(null);
  const [mailPack, setMailPack] = useState<MailPack | null>(null);
  const [mailPackOpen, setMailPackOpen] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(false);

  const hasStreetQuery = !!searchParams.street?.trim();

  const splitStreetInput = (
    street?: string
  ): { street_number?: string; street_name?: string; hasPartial: boolean } => {
    const raw = (street || '').trim();
    if (!raw) {
      return { street_number: undefined, street_name: undefined, hasPartial: false };
    }

    const match = raw.match(/^(\d+[a-zA-Z]?)\s+(.+)$/);
    if (!match) {
      return { street_number: undefined, street_name: undefined, hasPartial: true };
    }

    return {
      street_number: match[1].trim(),
      street_name: match[2].trim(),
      hasPartial: false,
    };
  };

  const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  const ensureBackendReady = useCallback(async (): Promise<boolean> => {
    if (backendReady) {
      return true;
    }

    setWarmingBackend(true);

    for (let attempt = 1; attempt <= 3; attempt += 1) {
      try {
        await api.healthCheck();
        setBackendReady(true);
        setWarmingBackend(false);
        return true;
      } catch (error) {
        console.warn('[Solarware] backend:wakeup:attempt_failed', { attempt, error });
        if (attempt < 3) {
          await sleep(1500 * attempt);
        }
      }
    }

    setWarmingBackend(false);
    return false;
  }, [backendReady]);

  useEffect(() => {
    void ensureBackendReady();
  }, [ensureBackendReady]);

  const loadAreaSuggestions = useCallback(
    async (query: string) => {
      try {
        const response = await api.suggestAreas({
          country: searchParams.country,
          province: searchParams.province,
          city: searchParams.city,
          query,
        });
        const values = response.data.areas || [];
        setAreaOptions(values);
      } catch (error) {
        console.warn('[Solarware] area:suggest:error', error);
      }
    },
    [searchParams.country, searchParams.province, searchParams.city]
  );

  useEffect(() => {
    const timer = setTimeout(() => {
      void loadAreaSuggestions(searchParams.area || '');
    }, 250);

    return () => clearTimeout(timer);
  }, [
    searchParams.area,
    searchParams.city,
    searchParams.province,
    searchParams.country,
    loadAreaSuggestions,
  ]);

  const handleSearch = async () => {
    setLoading(true);
    setSearchMessage('Searching...');

    try {
      const ready = await ensureBackendReady();
      if (!ready) {
        setResults([]);
        setSearchMessage('Service temporarily unavailable. Please retry.');
        return;
      }

      const streetParts = splitStreetInput(searchParams.street);
      if (streetParts.hasPartial) {
        setResults([]);
        setSearchMessage(
          'Enter full street address as "98 Richmond Street" for exact search, or leave it blank for area search.'
        );
        return;
      }

      const isExactMode = !!streetParts.street_number && !!streetParts.street_name;
      let resolvedArea = searchParams.area;

      if (!isExactMode) {
        const inCurrentOptions = areaOptions.some(
          (a) => a.trim().toLowerCase() === (searchParams.area || '').trim().toLowerCase()
        );
        if (!inCurrentOptions) {
          try {
            const areaSuggest = await api.suggestAreas({
              country: searchParams.country,
              province: searchParams.province,
              city: searchParams.city,
              query: searchParams.area,
            });
            const suggested = areaSuggest.data.areas || [];
            if (suggested.length > 0) {
              resolvedArea = suggested[0];
              setSearchParams((prev) => ({ ...prev, area: suggested[0] }));
              setAreaOptions(suggested);
            }
          } catch (error) {
            console.warn('[Solarware] area:suggest:search_fallback_error', error);
          }
        }
      }

      const payload = {
        country: searchParams.country,
        province: searchParams.province,
        city: searchParams.city,
        suburb: resolvedArea,
        street_number: streetParts.street_number,
        street_name: streetParts.street_name,
        radius_m: isExactMode ? 300 : 1500,
      };

      console.info('[Solarware] search:start', {
        mode: isExactMode ? 'address' : 'area',
        suburb: payload.suburb,
        city: payload.city,
        province: payload.province,
      });

      let response;
      try {
        response = await api.searchProspects(payload);
      } catch (firstError) {
        console.warn('[Solarware] search:first_attempt_failed_retrying', firstError);
        await sleep(1200);
        response = await api.searchProspects(payload);
      }
      const exactCount = response.data.count ?? (response.data.results || []).length;

      console.info('[Solarware] search:done', {
        mode: isExactMode ? 'address' : 'area',
        count: exactCount,
        message: response.data.message,
      });

      setResults(response.data.results || []);
      setSearchMessage(response.data.message || '');
    } catch (error) {
      console.error('[Solarware] search:error', error);
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
          <div className="flex items-center gap-4">
            <img
              src="/logo.png"
              alt="Solarware logo"
              className="h-14 w-14 rounded-lg border border-slate-500 bg-slate-950/60 object-contain p-1.5"
            />
            <h1 className="text-3xl font-bold tracking-tight">Solarware</h1>
          </div>
        </header>

        <div className="grid gap-6 lg:grid-cols-12">
          <div className="lg:col-span-4">
            <SearchPanel
              params={searchParams}
              onParamsChange={setSearchParams}
              areaOptions={areaOptions}
              onAreaQueryChange={(q) => {
                void loadAreaSuggestions(q);
              }}
              onSearch={handleSearch}
              loading={loading || warmingBackend}
            />
          </div>

          <div className="lg:col-span-8">
            <div className="mb-4 rounded-xl border border-slate-700 bg-slate-900/70 p-4">
              <h2 className="text-lg font-semibold text-slate-100">Results</h2>
              {searchMessage && <p className="mt-1 text-sm text-slate-300">{searchMessage}</p>}
              {!searchMessage && (
                <p className="mt-1 text-sm text-slate-400">
                  {searchParams.street?.trim()
                    ? 'Exact address mode active.'
                    : `Area mode active for ${searchParams.area}, ${searchParams.city}.`}
                </p>
              )}
            </div>

            <ResultsTable
              prospects={results}
              loading={loading}
              sortBy={sortBy}
              onSortChange={setSortBy}
              noResultsMessage={
                hasStreetQuery
                  ? 'No targetable mapped roof found for this exact street address.'
                  : `No viable commercial roofs found in ${searchParams.area}.`
              }
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
