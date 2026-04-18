import React from 'react';

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

interface ResultsTableProps {
  prospects: Prospect[];
  loading: boolean;
  onProposal: (prospectId: string) => void;
}

export const ResultsTable: React.FC<ResultsTableProps> = ({ prospects, loading, onProposal }) => {
  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin text-3xl">⏳</div>
        <p className="mt-3 text-gray-600">Searching properties...</p>
      </div>
    );
  }

  if (prospects.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg">
        <p className="text-gray-600">Enter search criteria and click "Find Solar Leads"</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-gray-100 border-b-2 border-gray-300">
          <tr>
            <th className="px-4 py-3 text-left font-semibold text-gray-700">Address</th>
            <th className="px-4 py-3 text-left font-semibold text-gray-700">Business</th>
            <th className="px-4 py-3 text-left font-semibold text-gray-700">Type</th>
            <th className="px-4 py-3 text-left font-semibold text-gray-700">Roof (sqft)</th>
            <th className="px-4 py-3 text-center font-semibold text-gray-700">Solar Score</th>
            <th className="px-4 py-3 text-left font-semibold text-gray-700">Contact Status</th>
            <th className="px-4 py-3 text-left font-semibold text-gray-700">Phone</th>
            <th className="px-4 py-3 text-left font-semibold text-gray-700">Email</th>
            <th className="px-4 py-3 text-center font-semibold text-gray-700">Action</th>
          </tr>
        </thead>
        <tbody>
          {prospects.map((prospect, idx) => (
            <tr
              key={prospect.id}
              className={`border-b ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'} hover:bg-green-50 transition`}
            >
              <td className="px-4 py-3 font-medium text-gray-900">{prospect.address}</td>
              <td className="px-4 py-3 text-gray-600">{prospect.business_name || '-'}</td>
              <td className="px-4 py-3 text-gray-600">{prospect.property_type || '-'}</td>
              <td className="px-4 py-3 text-gray-600">
                {prospect.roof_size_sqft.toLocaleString()}
              </td>
              <td className="px-4 py-3 text-center">
                <span
                  className={`inline-block px-3 py-1 rounded-full text-white font-semibold text-xs ${
                    prospect.solar_score >= 80
                      ? 'bg-green-600'
                      : prospect.solar_score >= 60
                        ? 'bg-yellow-600'
                        : 'bg-orange-600'
                  }`}
                >
                  {prospect.solar_score}
                </span>
              </td>
              <td className="px-4 py-3">
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
              </td>
              <td className="px-4 py-3 text-gray-600 text-xs">{prospect.phone || '-'}</td>
              <td className="px-4 py-3 text-gray-600 text-xs">{prospect.email || '-'}</td>
              <td className="px-4 py-3 text-center">
                <button
                  onClick={() => onProposal(prospect.id)}
                  className="bg-green-600 text-white px-3 py-1 rounded text-xs font-semibold hover:bg-green-700 transition"
                >
                  Proposal
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
