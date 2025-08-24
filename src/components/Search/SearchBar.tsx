import React, { useState, useRef, useEffect } from 'react';
import { Button, Input } from '../Common';

interface SearchFilter {
  sources: string[];
  dateRange: {
    start: string;
    end: string;
  };
  meetingTypes: string[];
}

interface SearchBarProps {
  onSearch: (query: string, filters: SearchFilter) => void;
  placeholder?: string;
  className?: string;
  isLoading?: boolean;
  recentQueries?: string[];
  suggestions?: string[];
}

const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  placeholder = '회의록, 문서, 내용을 검색하세요...',
  className = '',
  isLoading = false,
  recentQueries = [],
  suggestions = [],
}) => {
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilter>({
    sources: [],
    dateRange: { start: '', end: '' },
    meetingTypes: [],
  });

  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  const sourceOptions = [
    { value: 'meetings', label: '회의록' },
    { value: 'notion', label: 'Notion' },
    { value: 'github', label: 'GitHub' },
    { value: 'google_drive', label: 'Google Drive' },
  ];

  const meetingTypeOptions = [
    { value: 'team', label: '팀 미팅' },
    { value: 'project', label: '프로젝트 회의' },
    { value: 'weekly', label: '주간 회의' },
    { value: 'monthly', label: '월간 회의' },
    { value: 'planning', label: '기획 회의' },
    { value: 'review', label: '검토 회의' },
  ];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = () => {
    if (query.trim()) {
      onSearch(query.trim(), filters);
      setShowSuggestions(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleQueryClick = (selectedQuery: string) => {
    setQuery(selectedQuery);
    setShowSuggestions(false);
    onSearch(selectedQuery, filters);
  };

  const handleFilterChange = (filterType: keyof SearchFilter, value: any) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value,
    }));
  };

  const clearFilters = () => {
    setFilters({
      sources: [],
      dateRange: { start: '', end: '' },
      meetingTypes: [],
    });
  };

  const hasActiveFilters = () => {
    return (
      filters.sources.length > 0 ||
      filters.dateRange.start ||
      filters.dateRange.end ||
      filters.meetingTypes.length > 0
    );
  };

  return (
    <div className={`relative ${className}`}>
      {/* Main Search Input */}
      <div className="relative">
        <Input
          ref={inputRef}
          type="text"
          placeholder={placeholder}
          value={query}
          onChange={setQuery}
          onKeyPress={handleKeyPress}
          onFocus={() => setShowSuggestions(true)}
          className="pr-24"
        />
        
        {/* Search Button */}
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex space-x-2">
          <Button
            size="sm"
            onClick={handleSearch}
            disabled={!query.trim() || isLoading}
            loading={isLoading}
          >
            검색
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            icon={showFilters ? '🔽' : '🔽'}
          >
            필터
          </Button>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Sources */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                검색 소스
              </label>
              <div className="space-y-2">
                {sourceOptions.map((option) => (
                  <label key={option.value} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.sources.includes(option.value)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          handleFilterChange('sources', [...filters.sources, option.value]);
                        } else {
                          handleFilterChange('sources', filters.sources.filter(s => s !== option.value));
                        }
                      }}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">{option.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                날짜 범위
              </label>
              <div className="space-y-2">
                <input
                  type="date"
                  value={filters.dateRange.start}
                  onChange={(e) => handleFilterChange('dateRange', { ...filters.dateRange, start: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
                <input
                  type="date"
                  value={filters.dateRange.end}
                  onChange={(e) => handleFilterChange('dateRange', { ...filters.dateRange, end: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
            </div>

            {/* Meeting Types */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                회의 유형
              </label>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {meetingTypeOptions.map((option) => (
                  <label key={option.value} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.meetingTypes.includes(option.value)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          handleFilterChange('meetingTypes', [...filters.meetingTypes, option.value]);
                        } else {
                          handleFilterChange('meetingTypes', filters.meetingTypes.filter(t => t !== option.value));
                        }
                      }}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">{option.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Filter Actions */}
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center space-x-2">
              {hasActiveFilters() && (
                <span className="text-sm text-gray-600">
                  {filters.sources.length + filters.meetingTypes.length}개 필터 적용됨
                </span>
              )}
            </div>
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={clearFilters}
                disabled={!hasActiveFilters()}
              >
                필터 초기화
              </Button>
              <Button
                size="sm"
                onClick={handleSearch}
                disabled={!query.trim()}
              >
                필터 적용 검색
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Suggestions */}
      {showSuggestions && (query || recentQueries.length > 0 || suggestions.length > 0) && (
        <div
          ref={suggestionsRef}
          className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 max-h-96 overflow-y-auto"
        >
          {/* Recent Queries */}
          {recentQueries.length > 0 && !query && (
            <div className="p-3 border-b border-gray-200">
              <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                최근 검색어
              </h4>
              <div className="space-y-1">
                {recentQueries.slice(0, 5).map((recentQuery, index) => (
                  <button
                    key={index}
                    onClick={() => handleQueryClick(recentQuery)}
                    className="w-full text-left px-2 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded"
                  >
                    {recentQuery}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Search Suggestions */}
          {suggestions.length > 0 && (
            <div className="p-3 border-b border-gray-200">
              <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                추천 검색어
              </h4>
              <div className="space-y-1">
                {suggestions.slice(0, 5).map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleQueryClick(suggestion)}
                    className="w-full text-left px-2 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Query Suggestions */}
          {query && (
            <div className="p-3">
              <div className="space-y-1">
                <button
                  onClick={() => handleQueryClick(query)}
                  className="w-full text-left px-2 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded font-medium"
                >
                  "{query}" 검색하기
                </button>
                {query.includes('회의') && (
                  <button
                    onClick={() => handleQueryClick(query.replace('회의', '미팅'))}
                    className="w-full text-left px-2 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded"
                  >
                    "{query.replace('회의', '미팅')}" 검색하기
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
