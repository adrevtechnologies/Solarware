import React from 'react';

interface ProposalModalProps {
  isOpen: boolean;
  onClose: () => void;
  prospect?: {
    id: string;
    address: string;
    business_name?: string;
    roof_size_sqft: number;
    solar_score: number;
  };
}

export const ProposalModal: React.FC<ProposalModalProps> = ({ isOpen, onClose, prospect }) => {
  if (!isOpen || !prospect) return null;

  // Simple estimation calculations
  const systemSizeKw = Math.round((prospect.roof_size_sqft / 100) * 0.15);
  const monthlySavingsLow = Math.round(systemSizeKw * 300);
  const monthlySavingsHigh = Math.round(systemSizeKw * 500);
  const paybackYears = Math.round(((systemSizeKw * 100000) / (monthlySavingsLow * 12)) * 10) / 10;

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
          {/* System Size */}
          <div className="border-b pb-4">
            <p className="text-sm text-gray-600 mb-1">Estimated System Size</p>
            <p className="text-3xl font-bold text-green-600">{systemSizeKw} kW</p>
            <p className="text-xs text-gray-500 mt-1">
              Based on {prospect.roof_size_sqft} sqft roof
            </p>
          </div>

          {/* Monthly Savings */}
          <div className="border-b pb-4">
            <p className="text-sm text-gray-600 mb-1">Estimated Monthly Savings</p>
            <p className="text-2xl font-bold text-green-600">
              R{monthlySavingsLow.toLocaleString()} - R{monthlySavingsHigh.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500 mt-1">ZAR per month</p>
          </div>

          {/* Payback Period */}
          <div className="bg-green-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">Estimated Payback Period</p>
            <p className="text-3xl font-bold text-green-600">{paybackYears} years</p>
            <p className="text-xs text-gray-500 mt-1">Before full ROI</p>
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
            📅 Book Appointment
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
