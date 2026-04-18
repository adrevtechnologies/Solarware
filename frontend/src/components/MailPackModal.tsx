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

  useEffect(() => {
    if (isOpen) {
      setRecipientEmail(prospect?.email || '');
    }
  }, [isOpen, prospect?.email]);

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
      <div className="max-h-[92vh] w-full max-w-5xl overflow-y-auto rounded-xl border border-slate-700 bg-slate-900 shadow-2xl">
        <div className="border-b border-slate-700 px-6 py-4">
          <h2 className="text-lg font-bold text-slate-100">Mail Pack</h2>
          <p className="text-sm text-slate-400">{prospect.address}</p>
        </div>

        <div className="grid gap-6 p-6 lg:grid-cols-2">
          <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
              Before Image
            </h3>
            <img
              src={pack.before_image_url}
              alt="Before roof"
              className="w-full rounded-lg border border-slate-700"
            />
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
              After Image
            </h3>
            <img
              src={pack.after_image_url}
              alt="After roof with panel overlay"
              className="w-full rounded-lg border border-slate-700"
            />
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

        <div className="border-t border-slate-700 px-6 py-4 text-right">
          <button
            onClick={onClose}
            className="rounded-md border border-slate-600 px-4 py-2 text-sm text-slate-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
