import React from 'react';
import { Prospect } from './ResultsTable';

interface LeadCardProps {
  prospect: Prospect;
  onProposal: (prospectId: string) => void;
}

export const LeadCard: React.FC<LeadCardProps> = ({ prospect, onProposal }) => {
  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 p-4 border-b border-gray-200">
        <h3 className="font-bold text-gray-900 text-lg">
          {prospect.business_name || prospect.address}
        </h3>
        <p className="text-sm text-gray-600 mt-1">{prospect.address}</p>
      </div>

      {/* Body */}
      <div className="p-4 space-y-3">
        {/* Property Info */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-500 font-semibold">Property Type</p>
            <p className="text-sm font-medium text-gray-900">{prospect.property_type || '-'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 font-semibold">Roof Area</p>
            <p className="text-sm font-medium text-gray-900">
              {prospect.roof_size_sqft.toLocaleString()} sqft
            </p>
          </div>
        </div>

        {/* Solar Score */}
        <div>
          <p className="text-xs text-gray-500 font-semibold mb-2">Solar Score</p>
          <div className="flex items-center gap-2">
            <span
              className={`inline-block px-3 py-1 rounded-full text-white font-bold text-sm ${
                prospect.solar_score >= 80
                  ? 'bg-green-600'
                  : prospect.solar_score >= 60
                    ? 'bg-yellow-600'
                    : 'bg-orange-600'
              }`}
            >
              {prospect.solar_score}/100
            </span>
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  prospect.solar_score >= 80
                    ? 'bg-green-600'
                    : prospect.solar_score >= 60
                      ? 'bg-yellow-600'
                      : 'bg-orange-600'
                }`}
                style={{ width: `${prospect.solar_score}%` }}
              />
            </div>
          </div>
        </div>

        {/* Contact Status */}
        <div>
          <p className="text-xs text-gray-500 font-semibold mb-1">Contact Status</p>
          <span
            className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
              prospect.contact_status === 'Verified'
                ? 'bg-green-100 text-green-800'
                : prospect.contact_status === 'Partial'
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-red-100 text-red-800'
            }`}
          >
            {prospect.contact_status}
          </span>
        </div>

        {/* Contact Info */}
        <div className="bg-gray-50 rounded-lg p-3 space-y-2">
          {prospect.phone && (
            <div>
              <p className="text-xs text-gray-500 font-semibold">Phone</p>
              <p className="text-sm text-gray-900">{prospect.phone}</p>
            </div>
          )}
          {prospect.email && (
            <div>
              <p className="text-xs text-gray-500 font-semibold">Email</p>
              <p className="text-sm text-gray-900">{prospect.email}</p>
            </div>
          )}
          {!prospect.phone && !prospect.email && (
            <p className="text-xs text-gray-500">No contact info available</p>
          )}
        </div>
      </div>

      {/* Footer */}
      <button
        onClick={() => onProposal(prospect.id)}
        className="w-full bg-green-600 text-white font-bold py-3 hover:bg-green-700 transition border-t border-gray-200"
      >
        View Proposal
      </button>
    </div>
  );
};
