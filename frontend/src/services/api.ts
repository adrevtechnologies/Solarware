import axios from 'axios';
import {
  AreaSearchRequest,
  AreaSearchResponse,
  MailPack,
  PropertySearchRequest,
  PropertySearchResponse,
  Prospect,
  SearchRequestV1,
} from '../types';

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
  areaSearch: (payload: AreaSearchRequest) =>
    apiClient.post<AreaSearchResponse>('/api/area-search', payload),

  placesAutocomplete: (input: string, session_token?: string, region_code = 'za') =>
    apiClient.post<{
      suggestions: Array<{
        place_id: string;
        main_text: string;
        secondary_text: string;
        full_text: string;
      }>;
    }>('/api/places/autocomplete', { input, session_token, region_code }),

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
      params: sessionToken ? { session_token: sessionToken } : undefined,
    }),

  propertySearch: (payload: PropertySearchRequest) =>
    apiClient.post<PropertySearchResponse>('/api/property-search', payload),

  searchProspects: (searchParams: SearchRequestV1) =>
    apiClient.post<{ results: Prospect[]; count: number; search_area: string; message: string }>(
      '/api/search',
      searchParams
    ),

  enrichLead: (prospect: Prospect) =>
    apiClient.post<Prospect>('/api/search/lead/enrich', {
      prospect,
    }),

  generateMailPack: (lead_id: string) => apiClient.post<MailPack>('/api/mailpack', { lead_id }),

  sendMailPack: (mailing_pack: Record<string, unknown>, recipient_email: string) =>
    apiClient.post('/api/search/mail-pack/send', { mailing_pack, recipient_email }),

  healthCheck: () => apiClient.get('/health'),
};

export default apiClient;
