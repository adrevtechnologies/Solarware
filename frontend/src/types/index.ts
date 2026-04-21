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
  osm_id: string;
  address: string;
  suburb?: string;
  city?: string;
  business_name?: string;
  building_type: string;
  website?: string;
  phone?: string;
  email?: string;
  contact_person?: string;
  roof_area_sqm: number;
  estimated_panel_count: number;
  capacity_low_kw: number;
  capacity_high_kw: number;
  annual_kwh: number;
  savings_low: number;
  savings_high: number;
  savings_potential_display: string; // "R xxx k – R xxx k / year"
  solar_score: number; // 0-100
  satellite_image_url: string;
  latitude: number;
  longitude: number;
}

export interface SearchRequestV1 {
  country: string;
  province: string;
  city: string;
  suburb: string;
  street_name?: string;
  street_number?: string;
  postcode?: string;
  radius_m?: number;
  min_roof_sqm?: number;
  include_residential?: boolean;
}

export interface MailPack {
  id: string;
  before_image_url: string;
  after_image_url: string;
  before_after_image_url: string;
  pdf_url: string;
  email_subject: string;
  email_body: string;
  outreach_email: string;
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
