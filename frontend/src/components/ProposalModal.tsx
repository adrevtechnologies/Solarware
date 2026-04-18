import React from 'react';
import { Prospect } from '../types';

interface ProposalModalProps {
  isOpen: boolean;
  onClose: () => void;
  prospect?: Prospect;
}

export const ProposalModal: React.FC<ProposalModalProps> = ({ isOpen, onClose, prospect }) => {
  if (!isOpen || !prospect) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl max-w-md w-full">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-600 to-green-700 text-white p-6 rounded-t-lg">
          <h2 className="text-2xl font-bold">{prospect.address}</h2>
          <p className="text-green-100 mt-1">{prospect.business_name || 'Commercial Property'}</p>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Capacity */}
          <div className="border-b pb-4">
            <p className="text-sm text-gray-600 mb-1">Estimated Solar Capacity</p>
            <p className="text-3xl font-bold text-green-600">
              {prospect.capacity_low_kw.toFixed(1)} - {prospect.capacity_high_kw.toFixed(1)} kW
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Based on {Math.round(prospect.roof_area_sqm).toLocaleString()} m2 roof area
            </p>
          </div>

          {/* Annual Generation */}
          <div className="border-b pb-4">
            <p className="text-sm text-gray-600 mb-1">Estimated Annual Generation</p>
            <p className="text-2xl font-bold text-green-600">
              {Math.round(prospect.annual_kwh).toLocaleString()} kWh
            </p>
            <p className="text-xs text-gray-500 mt-1">Based on regional solar yield</p>
          </div>

          {/* Savings */}
          <div className="bg-green-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">Estimated Annual Savings Potential</p>
            <p className="text-3xl font-bold text-green-600">
              {prospect.savings_potential_display}
            </p>
            <p className="text-xs text-gray-500 mt-1">Tariff scenarios R1.80 to R3.20 per kWh</p>
          </div>

          {/* Solar Score */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Solar Score:</span>
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full font-bold text-sm">
              {prospect.solar_score}/100
            </span>
          </div>

          {/* CTA */}
          <button className="w-full bg-green-600 text-white font-bold py-3 rounded-lg hover:bg-green-700 transition">
            Generate Proposal
          </button>
        </div>

        {/* Footer */}
        <div className="border-t bg-gray-50 px-6 py-4 rounded-b-lg flex justify-between">
          <p className="text-xs text-gray-500">*Estimates based on local averages</p>
          <button onClick={onClose} className="text-gray-600 hover:text-gray-900 font-semibold">
            ✕
          </button>
        </div>
      </div>
    </div>
  );
};
