import axios from 'axios';
import {
  AreaMassSearchRequest,
  AreaMassSearchResponse,
  MailPack,
  Prospect,
  SearchRequestV1,
} from '../types';

// In production, set VITE_API_URL to the deployed backend URL.
// In local dev, leave it empty and rely on Vite proxy.
const rawApiUrl = import.meta.env.VITE_API_URL || 'https://solarware-api.onrender.com';
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

  suggestCities: (payload: { country?: string; province?: string; query?: string }) =>
    apiClient.post<{ cities: string[] }>('/api/cities/suggest', payload),

  areaMassSearch: (payload: AreaMassSearchRequest) =>
    apiClient.post<AreaMassSearchResponse>('/api/area-mass-search', payload),

  placesAutocomplete: (payload: { input: string; session_token?: string; region_code?: string }) =>
    apiClient.post<{
      suggestions: Array<{
        place_id: string;
        main_text: string;
        secondary_text: string;
        full_text: string;
      }>;
    }>('/api/places/autocomplete', payload),

  placeDetails: (placeId: string, sessionToken?: string) =>
    apiClient.get<{
      place_id: string;
      formatted_address: string;
      business_name: string;
      lat?: number;
      lng?: number;
      city?: string;
      province?: string;
      country?: string;
    }>(`/api/places/${placeId}`, {
      params: {
        session_token: sessionToken,
      },
    }),
};

export default apiClient;
