import axios from 'axios';

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
  // REAL SEARCH - using Nominatim + Overpass
  searchProspects: (searchParams: {
    mode: 'address' | 'area' | 'city' | 'province' | 'country';
    street_number?: string;
    street_name?: string;
    suburb?: string;
    city?: string;
    province?: string;
    postcode?: string;
    radius_m?: number;
    building_types?: string[];
    min_roof_sqm?: number;
  }) => apiClient.post('/api/search', searchParams),

  // Search Areas (legacy, keeping for compatibility)
  createSearchArea: (data: any) => apiClient.post('/api/search-areas', data),
  listSearchAreas: (country?: string) => {
    const params = country ? { country } : {};
    return apiClient.get('/api/search-areas', { params });
  },
  getSearchArea: (id: string) => apiClient.get(`/api/search-areas/${id}`),
  updateSearchArea: (id: string, data: any) => apiClient.put(`/api/search-areas/${id}`, data),

  // Prospects (legacy)
  listProspects: (searchAreaId?: string, skip?: number, limit?: number) => {
    const params: Record<string, string | number> = { skip: skip || 0, limit: limit || 50 };
    if (searchAreaId) params['search_area_id'] = searchAreaId;
    return apiClient.get('/api/prospects', { params });
  },
  getProspect: (id: string) => apiClient.get(`/api/prospects/${id}`),
  getProspectContact: (id: string) => apiClient.get(`/api/prospects/${id}/contact`),

  // Processing
  processSearchArea: (searchAreaId: string, config?: any) =>
    apiClient.post(`/api/process/search-area/${searchAreaId}`, {}, { params: config }),
  getProcessingStatus: (searchAreaId: string) =>
    apiClient.get(`/api/process/status/${searchAreaId}`),

  // Health
  healthCheck: () => apiClient.get('/health'),
};

export default apiClient;
