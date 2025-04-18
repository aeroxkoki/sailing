import React, { useState } from 'react';
import { useRouter } from 'next/router';
import SessionCard, { Session } from './SessionCard';
import Button from '../common/Button';
import Input from '../forms/Input';

interface SessionListProps {
  sessions: Session[];
  onCreateSession?: () => void;
  onSessionClick?: (session: Session) => void;
  projectId?: string;
  loading?: boolean;
  className?: string;
}

const SessionList: React.FC<SessionListProps> = ({
  sessions,
  onCreateSession,
  onSessionClick,
  projectId,
  loading = false,
  className = '',
}) => {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState('');
  const [dataTypeFilter, setDataTypeFilter] = useState<string>('all');
  const [tagFilter, setTagFilter] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('date-desc');

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  // Handle data type filter change
  const handleDataTypeFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setDataTypeFilter(e.target.value);
  };

  // Handle tag filter change
  const handleTagFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTagFilter(e.target.value);
  };

  // Handle sort change
  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSortBy(e.target.value);
  };

  // Filter sessions based on search term and filters
  const filteredSessions = sessions
    .filter((session) => {
      // Filter by project if projectId is provided
      if (projectId && session.projectId !== projectId) {
        return false;
      }

      // Apply search filter
      const matchesSearch =
        !searchTerm ||
        session.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (session.description &&
          session.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (session.location &&
          session.location.toLowerCase().includes(searchTerm.toLowerCase()));

      // Apply data type filter
      const matchesDataType =
        dataTypeFilter === 'all' || session.dataType === dataTypeFilter;

      // Apply tag filter
      const matchesTag =
        !tagFilter ||
        (session.tags &&
          session.tags.some((tag) =>
            tag.toLowerCase().includes(tagFilter.toLowerCase())
          ));

      return matchesSearch && matchesDataType && matchesTag;
    })
    .sort((a, b) => {
      // Sort based on selected sort option
      switch (sortBy) {
        case 'date-asc':
          return new Date(a.date).getTime() - new Date(b.date).getTime();
        case 'date-desc':
          return new Date(b.date).getTime() - new Date(a.date).getTime();
        case 'name-asc':
          return a.name.localeCompare(b.name);
        case 'name-desc':
          return b.name.localeCompare(a.name);
        case 'windSpeed-desc':
          return (b.avgWindSpeed || 0) - (a.avgWindSpeed || 0);
        case 'boatSpeed-desc':
          return (b.avgBoatSpeed || 0) - (a.avgBoatSpeed || 0);
        default:
          return new Date(b.date).getTime() - new Date(a.date).getTime();
      }
    });

  // Handle session click
  const handleSessionClick = (session: Session) => {
    if (onSessionClick) {
      onSessionClick(session);
    } else {
      router.push(`/sessions/${session.id}`);
    }
  };

  // Get unique tags from all sessions
  const allTags = Array.from(
    new Set(
      sessions
        .filter((session) => session.tags && session.tags.length > 0)
        .flatMap((session) => session.tags || [])
    )
  ).sort();

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-xl font-semibold">セッション一覧</h2>
        {onCreateSession && (
          <Button variant="primary" onClick={onCreateSession}>
            新規セッション
          </Button>
        )}
      </div>

      <div className="bg-white p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <Input
            placeholder="セッションを検索..."
            value={searchTerm}
            onChange={handleSearchChange}
            fullWidth
          />

          <div>
            <label
              htmlFor="data-type-filter"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              データタイプ
            </label>
            <select
              id="data-type-filter"
              value={dataTypeFilter}
              onChange={handleDataTypeFilterChange}
              className="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="all">すべて</option>
              <option value="gps">GPS</option>
              <option value="wind">風向風速</option>
              <option value="combined">複合データ</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="tag-filter"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              タグ
            </label>
            <input
              id="tag-filter"
              type="text"
              list="tag-options"
              value={tagFilter}
              onChange={handleTagFilterChange}
              className="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="タグで絞り込み..."
            />
            <datalist id="tag-options">
              {allTags.map((tag) => (
                <option key={tag} value={tag} />
              ))}
            </datalist>
          </div>

          <div>
            <label
              htmlFor="sort-by"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              並び替え
            </label>
            <select
              id="sort-by"
              value={sortBy}
              onChange={handleSortChange}
              className="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="date-desc">日付（新しい順）</option>
              <option value="date-asc">日付（古い順）</option>
              <option value="name-asc">名前（昇順）</option>
              <option value="name-desc">名前（降順）</option>
              <option value="windSpeed-desc">風速（高い順）</option>
              <option value="boatSpeed-desc">艇速（高い順）</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="py-12 flex justify-center">
            <div className="animate-spin h-8 w-8 border-4 border-blue-500 rounded-full border-t-transparent"></div>
          </div>
        ) : filteredSessions.length === 0 ? (
          <div className="py-12 text-center text-gray-500">
            {searchTerm || dataTypeFilter !== 'all' || tagFilter ? (
              <p>検索条件に一致するセッションがありません。</p>
            ) : (
              <p>
                セッションがまだありません。「新規セッション」ボタンをクリックして作成してみましょう。
              </p>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredSessions.map((session) => (
              <SessionCard
                key={session.id}
                session={session}
                onClick={handleSessionClick}
                showProjectBadge={!projectId}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SessionList;