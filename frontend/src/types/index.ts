export interface SearchArea {
  id?: string;
  name: string;
  country: string;
  region?: string;
  street?: string;
  area?: string;
  district?: string;
  city?: string;
  min_latitude?: number;
  max_latitude?: number;
  min_longitude?: number;
  max_longitude?: number;
  min_roof_area_sqft: number;
  created_at?: string;
}

export interface Prospect {
  id: string;
  address: string;
  business_name?: string;
  property_type?: string;
  roof_size_sqft: number;
  solar_score: number;
  contact_status: string;
  phone?: string;
  email?: string;
}

export interface Contact {
  id: string;
  prospect_id: string;
  contact_name?: string;
  title?: string;
  email?: string;
  phone?: string;
  data_complete: boolean;
  confidence_score?: number;
}

export interface MailingPack {
  id: string;
  prospect_id: string;
  email_subject: string;
  email_body: string;
  status: 'prepared' | 'reviewed' | 'sent';
  created_at: string;
  sent_at?: string;
}

export interface ProcessingResult {
  search_area_id: string;
  prospects_discovered: number;
  prospects_analyzed: number;
  contacts_enriched: number;
  visualizations_generated: number;
  mailing_packs_generated: number;
  status: string;
  errors: string[];
}
