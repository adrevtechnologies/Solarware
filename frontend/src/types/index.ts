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
  search_area_id: string;
  address: string;
  building_name?: string;
  business_name?: string;
  latitude: number;
  longitude: number;
  roof_area_sqft: number;
  roof_area_sqm: number;
  estimated_panel_count?: number;
  estimated_system_capacity_kw?: number;
  estimated_annual_production_kwh?: number;
  estimated_annual_savings_usd?: number;
  has_existing_solar: boolean;

  // Cost breakdown
  panel_cost?: number;
  inverter_cost?: number;
  battery_cost?: number;
  cable_cost?: number;
  installation_labor?: number;
  soft_costs?: number;
  total_bos_cost?: number;

  // Installation timeline
  installation_calendar_days?: number;
  installation_team_size?: number;
  installation_casual_workers?: number;

  // ROI metrics
  roi_simple_payback_years?: number;
  roi_npv_25_years?: number;
  roi_cumulative_savings_25_years?: number;
  roi_percentage?: number;

  // Layout efficiency
  strings?: number;
  rows?: number;
  layout_efficiency?: number;

  created_at: string;
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
