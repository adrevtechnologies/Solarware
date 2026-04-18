import React from 'react';

export type SearchMode = 'country' | 'province' | 'city' | 'area' | 'address';

interface SearchModeSelectorProps {
  mode: SearchMode;
  onModeChange: (mode: SearchMode) => void;
}

export const SearchModeSelector: React.FC<SearchModeSelectorProps> = ({ mode, onModeChange }) => {
  const modes: { value: SearchMode; label: string }[] = [
    { value: 'country', label: 'Country' },
    { value: 'province', label: 'Province' },
    { value: 'city', label: 'City' },
    { value: 'area', label: 'Area' },
    { value: 'address', label: 'Address' },
  ];

  return (
    <div className="flex gap-2 flex-wrap justify-center mb-6">
      {modes.map((m) => (
        <button
          key={m.value}
          onClick={() => onModeChange(m.value)}
          className={`px-4 py-2 rounded-full font-semibold transition ${
            mode === m.value
              ? 'bg-green-600 text-white shadow-lg'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
};
