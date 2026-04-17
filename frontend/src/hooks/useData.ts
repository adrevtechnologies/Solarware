import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { SearchArea } from '../types';

export const useSearchAreas = () => {
  const [areas, setAreas] = useState<SearchArea[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAreas = async (country?: string) => {
    setLoading(true);
    try {
      const response = await api.listSearchAreas(country);
      setAreas(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch search areas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAreas();
  }, []);

  return { areas, loading, error, fetchAreas };
};

export const useProspects = (searchAreaId?: string) => {
  const [prospects, setProspects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProspects = async () => {
    setLoading(true);
    try {
      const response = await api.listProspects(searchAreaId);
      setProspects(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch prospects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (searchAreaId) {
      fetchProspects();
    }
  }, [searchAreaId]);

  return { prospects, loading, error, fetchProspects };
};
