import React from 'react';

type SortKey = 'suitability_score' | 'roof_area_sqft' | 'business_name' | 'business_type';

interface ProspectListProps {
  prospects: any[];
  onGenerateProposal: (prospectId: string) => void;
  proposalLoadingId?: string | null;
}

export const ProspectList: React.FC<ProspectListProps> = ({
  prospects,
  onGenerateProposal,
  proposalLoadingId,
}) => {
  const [sortKey, setSortKey] = React.useState<SortKey>('suitability_score');
  const [sortAsc, setSortAsc] = React.useState(false);

  const onSort = (nextKey: SortKey) => {
    if (sortKey === nextKey) {
      setSortAsc((prev) => !prev);
      return;
    }
    setSortKey(nextKey);
    setSortAsc(nextKey === 'business_name' || nextKey === 'business_type');
  };

  const sorted = React.useMemo(() => {
    const rows = [...prospects];
    rows.sort((a, b) => {
      const av = a?.[sortKey];
      const bv = b?.[sortKey];

      if (typeof av === 'string' || typeof bv === 'string') {
        const aText = String(av || '').toLowerCase();
        const bText = String(bv || '').toLowerCase();
        if (aText < bText) return sortAsc ? -1 : 1;
        if (aText > bText) return sortAsc ? 1 : -1;
        return 0;
      }

      const aNum = Number(av || 0);
      const bNum = Number(bv || 0);
      return sortAsc ? aNum - bNum : bNum - aNum;
    });
    return rows;
  }, [prospects, sortAsc, sortKey]);

  const sortLabel = (key: SortKey, label: string) => (
    <button
      type="button"
      onClick={() => onSort(key)}
      className="font-semibold hover:text-blue-700"
      title="Sort"
    >
      {label} {sortKey === key ? (sortAsc ? '↑' : '↓') : ''}
    </button>
  );

  return (
    <div className="overflow-x-auto rounded border border-gray-200">
      <table className="min-w-full border-collapse bg-white">
        <thead className="bg-gray-100">
          <tr>
            <th className="border-b border-gray-200 px-4 py-3 text-left">Address</th>
            <th className="border-b border-gray-200 px-4 py-3 text-left">
              {sortLabel('business_name', 'Company Name')}
            </th>
            <th className="border-b border-gray-200 px-4 py-3 text-left">
              {sortLabel('business_type', 'Business Type')}
            </th>
            <th className="border-b border-gray-200 px-4 py-3 text-right">
              {sortLabel('roof_area_sqft', 'Roof Size')}
            </th>
            <th className="border-b border-gray-200 px-4 py-3 text-left">Contact Details</th>
            <th className="border-b border-gray-200 px-4 py-3 text-right">
              {sortLabel('suitability_score', 'Score')}
            </th>
            <th className="border-b border-gray-200 px-4 py-3 text-center">Proposal</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((prospect) => {
            const score = Number(prospect.suitability_score || 0);
            const scoreClass =
              score >= 80
                ? 'text-green-700 bg-green-100'
                : score >= 60
                  ? 'text-amber-700 bg-amber-100'
                  : 'text-gray-700 bg-gray-100';

            return (
              <tr key={prospect.id} className="hover:bg-gray-50">
                <td className="border-b border-gray-100 px-4 py-3 text-sm">{prospect.address}</td>
                <td className="border-b border-gray-100 px-4 py-3 text-sm font-medium">
                  {prospect.business_name || '-'}
                </td>
                <td className="border-b border-gray-100 px-4 py-3 text-sm">
                  {prospect.business_type || 'Unknown'}
                </td>
                <td className="border-b border-gray-100 px-4 py-3 text-right text-sm">
                  {(prospect.roof_area_sqft || 0).toLocaleString()} sq ft
                </td>
                <td className="border-b border-gray-100 px-4 py-3 text-sm">
                  <div>{prospect.contact_name || 'Needs Research'}</div>
                  <div className="text-xs text-gray-500">
                    {prospect.contact_email || 'No email'}
                  </div>
                  <div className="text-xs text-gray-500">
                    {prospect.contact_phone || 'No phone'}
                  </div>
                </td>
                <td className="border-b border-gray-100 px-4 py-3 text-right text-sm">
                  <span className={`rounded px-2 py-1 font-semibold ${scoreClass}`}>
                    {score}/100
                  </span>
                </td>
                <td className="border-b border-gray-100 px-4 py-3 text-center">
                  <button
                    type="button"
                    onClick={() => onGenerateProposal(prospect.id)}
                    disabled={proposalLoadingId === prospect.id}
                    className="rounded bg-blue-600 px-3 py-1 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
                  >
                    {proposalLoadingId === prospect.id ? 'Generating...' : 'Generate'}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
