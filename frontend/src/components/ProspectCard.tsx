import React from 'react';
import { Prospect, Contact } from '../types';

interface ProspectCardProps {
  prospect: Prospect;
  contact?: Contact;
}

export const ProspectCard: React.FC<ProspectCardProps> = ({ prospect, contact }) => {
  const [expandCosts, setExpandCosts] = React.useState(false);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-4 border-l-4 border-blue-500 hover:shadow-xl transition">
      {/* Header */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <h3 className="font-bold text-lg mb-2">
            📍 {prospect.business_name || prospect.address}
          </h3>
          <p className="text-sm text-gray-600">{prospect.address}</p>
          {prospect.building_name && (
            <p className="text-sm text-gray-500">{prospect.building_name}</p>
          )}
        </div>

        <div className="text-right">
          <div className="text-3xl font-bold text-green-600">
            R
            {prospect.estimated_annual_savings_usd?.toLocaleString('en-ZA', {
              maximumFractionDigits: 0,
            }) || 'N/A'}
          </div>
          <p className="text-xs text-gray-600">📊 Annual Savings</p>
          {prospect.roi_simple_payback_years && (
            <p className="text-xs text-green-700 font-semibold mt-1">
              💰 Payback: {prospect.roi_simple_payback_years.toFixed(1)} years
            </p>
          )}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-5 gap-3 pt-4 border-t mb-4">
        <div className="bg-blue-50 p-3 rounded text-center">
          <p className="text-xs text-gray-600">Roof Area</p>
          <p className="font-semibold text-sm">{prospect.roof_area_sqft?.toLocaleString()} sqft</p>
        </div>
        <div className="bg-blue-50 p-3 rounded text-center">
          <p className="text-xs text-gray-600">System Size</p>
          <p className="font-semibold text-sm">
            {prospect.estimated_system_capacity_kw?.toFixed(1)} kW
          </p>
        </div>
        <div className="bg-blue-50 p-3 rounded text-center">
          <p className="text-xs text-gray-600">Panels</p>
          <p className="font-semibold text-sm">{prospect.estimated_panel_count}</p>
        </div>
        <div className="bg-green-50 p-3 rounded text-center">
          <p className="text-xs text-gray-600">Annual Output</p>
          <p className="font-semibold text-sm">
            {prospect.estimated_annual_production_kwh?.toLocaleString(undefined, {
              maximumFractionDigits: 0,
            })}{' '}
            kWh
          </p>
        </div>
        <div className="bg-purple-50 p-3 rounded text-center">
          <p className="text-xs text-gray-600">Layout Efficiency</p>
          <p className="font-semibold text-sm">{prospect.layout_efficiency?.toFixed(1)}%</p>
        </div>
      </div>

      {/* Cost Breakdown Toggle */}
      {prospect.total_bos_cost && (
        <button
          onClick={() => setExpandCosts(!expandCosts)}
          className="w-full text-left py-2 px-3 bg-gradient-to-r from-orange-50 to-yellow-50 hover:from-orange-100 hover:to-yellow-100 rounded font-semibold text-sm text-gray-800 flex justify-between items-center transition"
        >
          💵 System Cost: R
          {prospect.total_bos_cost?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
          <span className={`transform transition ${expandCosts ? 'rotate-180' : ''}`}>▼</span>
        </button>
      )}

      {/* Cost Breakdown Details */}
      {expandCosts && prospect.total_bos_cost && (
        <div className="mt-4 space-y-2 bg-orange-50 p-4 rounded-md">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-700">🔆 Panels:</span>
              <span className="font-semibold">
                R{prospect.panel_cost?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">⚡ Inverter:</span>
              <span className="font-semibold">
                R{prospect.inverter_cost?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">🔌 Cables:</span>
              <span className="font-semibold">
                R{prospect.cable_cost?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">👷 Labor:</span>
              <span className="font-semibold">
                R
                {prospect.installation_labor?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
              </span>
            </div>
            {prospect.battery_cost && prospect.battery_cost > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-700">🔋 Batteries:</span>
                <span className="font-semibold">
                  R{prospect.battery_cost?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
                </span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-700">📋 Soft Costs:</span>
              <span className="font-semibold">
                R{prospect.soft_costs?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
              </span>
            </div>
          </div>

          {/* Installation Timeline */}
          {prospect.installation_calendar_days && (
            <div className="mt-4 pt-4 border-t border-orange-200">
              <p className="font-semibold text-sm mb-2">📅 Installation Timeline</p>
              <div className="grid grid-cols-2 gap-2 text-xs text-gray-700">
                <div>
                  ⏱️ Duration:{' '}
                  <span className="font-semibold">{prospect.installation_calendar_days} days</span>
                </div>
                <div>
                  👥 Team:{' '}
                  <span className="font-semibold">
                    {prospect.installation_team_size} + {prospect.installation_casual_workers}{' '}
                    casuals
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* ROI Metrics */}
          {prospect.roi_npv_25_years && (
            <div className="mt-4 pt-4 border-t border-orange-200">
              <p className="font-semibold text-sm mb-2">📈 25-Year ROI Analysis</p>
              <div className="grid grid-cols-2 gap-2 text-xs text-gray-700">
                <div>
                  💰 25Y Savings:{' '}
                  <span className="font-semibold text-green-700">
                    R
                    {prospect.roi_cumulative_savings_25_years?.toLocaleString('en-ZA', {
                      maximumFractionDigits: 0,
                    })}
                  </span>
                </div>
                <div>
                  🎯 NPV:{' '}
                  <span className="font-semibold text-green-700">
                    R
                    {prospect.roi_npv_25_years?.toLocaleString('en-ZA', {
                      maximumFractionDigits: 0,
                    })}
                  </span>
                </div>
                <div>
                  % Return:{' '}
                  <span className="font-semibold text-green-700">
                    {prospect.roi_percentage?.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Contact Information */}
      {contact && (
        <div className="mt-4 pt-4 border-t bg-blue-50 p-3 rounded">
          <h4 className="font-semibold text-sm mb-2">📞 Contact Information</h4>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-gray-600">Name:</span> {contact.contact_name || 'N/A'}
            </div>
            <div>
              <span className="text-gray-600">Title:</span> {contact.title || 'N/A'}
            </div>
            <div>
              <span className="text-gray-600">Email:</span> {contact.email || 'N/A'}
            </div>
            <div>
              <span className="text-gray-600">Phone:</span> {contact.phone || 'N/A'}
            </div>
          </div>
          {!contact.data_complete && (
            <p className="text-xs text-orange-600 mt-2">
              ⚠️ Contact data incomplete - manual research needed
            </p>
          )}
        </div>
      )}
    </div>
  );
};
