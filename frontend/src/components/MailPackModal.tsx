import React, { useEffect, useMemo, useState } from 'react';
import { MailPack, Prospect } from '../types';

interface MailPackModalProps {
  isOpen: boolean;
  pack: MailPack | null;
  prospect: Prospect | null;
  sendingEmail?: boolean;
  onClose: () => void;
  onSendEmail: (recipientEmail: string) => void;
}

export const MailPackModal: React.FC<MailPackModalProps> = ({
  isOpen,
  pack,
  prospect,
  sendingEmail,
  onClose,
  onSendEmail,
}) => {
  const [recipientEmail, setRecipientEmail] = useState('');
  const [beforeImageError, setBeforeImageError] = useState(false);
  const [afterImageError, setAfterImageError] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setRecipientEmail(prospect?.email || '');
    }
  }, [isOpen, prospect?.email]);

  useEffect(() => {
    setBeforeImageError(false);
    setAfterImageError(false);
  }, [pack?.before_image_url, pack?.after_image_url]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      window.addEventListener('keydown', onKeyDown);
    }

    return () => {
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [isOpen, onClose]);

  const defaultEmail = useMemo(() => {
    return recipientEmail;
  }, [recipientEmail]);

  if (!isOpen || !pack || !prospect) {
    return null;
  }

  const copyEmail = async () => {
    await navigator.clipboard.writeText(pack.outreach_email);
  };

  const saveLead = () => {
    const key = 'solarware_saved_leads_v1';
    const currentRaw = localStorage.getItem(key);
    const current = currentRaw ? JSON.parse(currentRaw) : [];
    const already = current.find((item: { osm_id: string }) => item.osm_id === prospect.osm_id);
    if (!already) {
      current.push({
        osm_id: prospect.osm_id,
        address: prospect.address,
        building_type: prospect.building_type,
        roof_area_sqm: prospect.roof_area_sqm,
        saved_at: new Date().toISOString(),
      });
      localStorage.setItem(key, JSON.stringify(current));
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-3 sm:p-4"
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="max-h-[92vh] w-full max-w-5xl overflow-y-auto rounded-xl border border-slate-700 bg-slate-900 shadow-2xl">
        <div className="sticky top-0 z-10 flex items-start justify-between border-b border-slate-700 bg-slate-900/95 px-4 py-3 backdrop-blur sm:px-6 sm:py-4">
          <h2 className="text-lg font-bold text-slate-100">Mail Pack</h2>
          <button
            onClick={onClose}
            className="ml-4 rounded-md border border-slate-600 px-3 py-1 text-sm font-semibold text-slate-200 hover:bg-slate-800"
          >
            Close
          </button>
        </div>
        <div className="px-4 pb-2 pt-3 sm:px-6">
          <p className="text-sm text-slate-400">{prospect.address}</p>
        </div>

        <div className="grid gap-6 p-6 lg:grid-cols-2">
          <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
              Before Image
            </h3>
            <div className="overflow-hidden rounded-lg border border-slate-700">
              <div className="relative">
                {!beforeImageError ? (
                  <img
                    src={pack.before_image_url}
                    alt="Before roof"
                    className="max-h-[44vh] w-full object-contain"
                    onError={() => setBeforeImageError(true)}
                  />
                ) : (
                  <div className="flex min-h-[220px] items-center justify-center bg-slate-800 px-4 text-center text-sm text-slate-300">
                    Before image failed to load.
                  </div>
                )}
                <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                  <div className="h-4 w-4 rounded-full border-2 border-red-400 bg-red-500/80 shadow-[0_0_0_3px_rgba(15,23,42,0.75)]" />
                </div>
              </div>
              <div className="border-t border-slate-700 bg-slate-800 px-3 py-2 text-xs text-slate-300">
                Red marker shows the searched address at image center.
              </div>
            </div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
              After Image
            </h3>
            <div className="overflow-hidden rounded-lg border border-slate-700">
              <div className="relative">
                {!afterImageError ? (
                  <img
                    src={pack.after_image_url}
                    alt="After roof with panel overlay"
                    className="max-h-[44vh] w-full object-contain"
                    onError={() => setAfterImageError(true)}
                  />
                ) : (
                  <div className="flex min-h-[220px] items-center justify-center bg-slate-800 px-4 text-center text-sm text-slate-300">
                    After image failed to load.
                  </div>
                )}
                <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                  <div className="h-4 w-4 rounded-full border-2 border-red-400 bg-red-500/80 shadow-[0_0_0_3px_rgba(15,23,42,0.75)]" />
                </div>
              </div>
            </div>

            <a
              href={`https://www.google.com/maps?q=${prospect.latitude},${prospect.longitude}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center rounded-md border border-cyan-500 px-3 py-2 text-xs font-semibold text-cyan-300 hover:bg-cyan-500/10"
            >
              Open exact location in Maps
            </a>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
              Outreach Email
            </h3>
            <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
              <p className="mb-2 text-sm font-semibold text-slate-200">{pack.email_subject}</p>
              <pre className="whitespace-pre-wrap text-xs text-slate-300">{pack.email_body}</pre>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-400">
                Recipient Email
              </label>
              <input
                type="email"
                value={defaultEmail}
                onChange={(e) => setRecipientEmail(e.target.value)}
                placeholder="lead@business.com"
                className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100"
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <a
                href={pack.pdf_url}
                target="_blank"
                rel="noreferrer"
                className="rounded-md bg-cyan-500 px-3 py-2 text-xs font-bold text-slate-950 hover:bg-cyan-400"
              >
                Download PDF
              </a>
              <button
                onClick={copyEmail}
                className="rounded-md border border-slate-500 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800"
              >
                Copy Email
              </button>
              <button
                onClick={() => onSendEmail(defaultEmail)}
                disabled={sendingEmail || !defaultEmail}
                className="rounded-md bg-emerald-500 px-3 py-2 text-xs font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
              >
                {sendingEmail ? 'Sending Email...' : 'Send Email'}
              </button>
              <button
                onClick={saveLead}
                className="rounded-md border border-amber-500 px-3 py-2 text-xs font-semibold text-amber-300 hover:bg-amber-500/10"
              >
                Save Lead
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
