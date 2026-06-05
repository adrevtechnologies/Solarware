import React, { useState } from 'react';
import { api } from '../services/api';
import { UserRewardEvent, UserSummary } from '../types';

export const UserAccountPanel: React.FC = () => {
  const [desiredUserId, setDesiredUserId] = useState('');
  const [lookupUserId, setLookupUserId] = useState('');
  const [currentUser, setCurrentUser] = useState<UserSummary | null>(null);
  const [events, setEvents] = useState<UserRewardEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(
    'Create an account to receive a unique user ID and wallet.'
  );

  const loadUserData = async (userId: string) => {
    const trimmed = userId.trim();
    if (!trimmed) {
      setMessage('Enter a user ID to load wallet and activity.');
      return;
    }

    setLoading(true);
    try {
      const [summaryRes, eventsRes] = await Promise.all([
        api.getUser(trimmed),
        api.getUserEvents(trimmed, 25),
      ]);
      setCurrentUser(summaryRes.data);
      setEvents(eventsRes.data.events || []);
      setLookupUserId(trimmed);
      setMessage(`Loaded account ${trimmed}.`);
    } catch (error) {
      setMessage(
        `Failed to load account: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async () => {
    setLoading(true);
    try {
      const created = await api.signupUser(desiredUserId.trim() || undefined);
      const user = created.data;
      setDesiredUserId('');
      setCurrentUser({
        user_id: user.user_id,
        is_active: user.is_active,
        created_at: user.created_at,
        last_event_at: null,
        wallet: user.wallet,
      });
      setLookupUserId(user.user_id);
      setEvents([]);
      setMessage(`Account created successfully. Your user ID is ${user.user_id}.`);
    } catch (error) {
      setMessage(
        `Account creation failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="mb-6 rounded-xl border border-slate-700 bg-slate-900/70 p-4">
      <h2 className="text-lg font-semibold text-slate-100">User Account & Wallet</h2>
      <p className="mt-1 text-sm text-slate-300">{message}</p>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-slate-700 bg-slate-950/60 p-4">
          <h3 className="text-sm font-semibold text-slate-200">Create account</h3>
          <p className="mt-1 text-xs text-slate-400">Leave blank to auto-generate a user ID.</p>
          <input
            type="text"
            value={desiredUserId}
            onChange={(e) => setDesiredUserId(e.target.value)}
            placeholder="Optional desired ID (e.g. SW001)"
            className="mt-3 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:border-emerald-400"
          />
          <button
            onClick={() => void handleSignup()}
            disabled={loading}
            className="mt-3 rounded-md bg-emerald-500 px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? 'Working...' : 'Create account'}
          </button>
        </div>

        <div className="rounded-lg border border-slate-700 bg-slate-950/60 p-4">
          <h3 className="text-sm font-semibold text-slate-200">Load account</h3>
          <p className="mt-1 text-xs text-slate-400">
            Check wallet and activity for an existing user.
          </p>
          <input
            type="text"
            value={lookupUserId}
            onChange={(e) => setLookupUserId(e.target.value)}
            placeholder="Enter user ID"
            className="mt-3 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:border-sky-400"
          />
          <button
            onClick={() => void loadUserData(lookupUserId)}
            disabled={loading}
            className="mt-3 rounded-md bg-sky-500 px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Load account'}
          </button>
        </div>
      </div>

      {currentUser && (
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-slate-700 bg-slate-950/60 p-4">
            <p className="text-xs uppercase tracking-wide text-slate-400">User ID</p>
            <p className="mt-1 text-base font-semibold text-slate-100">{currentUser.user_id}</p>
          </div>
          <div className="rounded-lg border border-slate-700 bg-slate-950/60 p-4">
            <p className="text-xs uppercase tracking-wide text-slate-400">Wallet balance</p>
            <p className="mt-1 text-base font-semibold text-emerald-300">
              {currentUser.wallet.points_balance} points
            </p>
          </div>
          <div className="rounded-lg border border-slate-700 bg-slate-950/60 p-4">
            <p className="text-xs uppercase tracking-wide text-slate-400">Last activity</p>
            <p className="mt-1 text-sm font-medium text-slate-200">
              {currentUser.last_event_at
                ? new Date(currentUser.last_event_at).toLocaleString()
                : 'No activity yet'}
            </p>
          </div>
        </div>
      )}

      {currentUser && (
        <div className="mt-4 rounded-lg border border-slate-700 bg-slate-950/60 p-4">
          <h3 className="text-sm font-semibold text-slate-200">Activity history</h3>
          <p className="mt-1 text-xs text-slate-400">
            Reward events from future ad integrations will appear here automatically.
          </p>
          {events.length === 0 ? (
            <p className="mt-2 text-sm text-slate-400">No events yet.</p>
          ) : (
            <div className="mt-2 overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="border-b border-slate-700 text-xs uppercase text-slate-400">
                  <tr>
                    <th className="px-2 py-2">Time</th>
                    <th className="px-2 py-2">Type</th>
                    <th className="px-2 py-2">Delta</th>
                    <th className="px-2 py-2">Balance</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((event) => (
                    <tr key={event.id} className="border-b border-slate-800">
                      <td className="px-2 py-2">{new Date(event.created_at).toLocaleString()}</td>
                      <td className="px-2 py-2">{event.event_type}</td>
                      <td className="px-2 py-2">{event.points_delta}</td>
                      <td className="px-2 py-2">{event.balance_after}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </section>
  );
};

export default UserAccountPanel;
