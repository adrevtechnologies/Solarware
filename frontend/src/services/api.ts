import axios from 'axios';
import { MailPack, Prospect, SearchRequestV1 } from '../types';

// In production, set VITE_API_URL to the deployed backend URL.
// In local dev, leave it empty and rely on Vite proxy.
const rawApiUrl = import.meta.env.VITE_API_URL || '';
const API_URL = rawApiUrl.replace(/\/$/, '');

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  searchProspects: (searchParams: SearchRequestV1) =>
    apiClient.post<{ results: Prospect[]; count: number; search_area: string; message: string }>(
      '/api/search',
      searchParams
    ),

  generateMailPack: (prospect: Prospect) =>
    apiClient.post<MailPack>('/api/search/mail-pack', {
      prospect,
    }),

  sendMailPack: (mailing_pack: Record<string, unknown>, recipient_email: string) =>
    apiClient.post('/api/search/mail-pack/send', { mailing_pack, recipient_email }),

  healthCheck: () => apiClient.get('/health'),

  suggestAreas: (payload: { country?: string; province?: string; city?: string; query?: string }) =>
    apiClient.post<{ areas: string[] }>('/api/areas/suggest', payload),
};

export default apiClient;
