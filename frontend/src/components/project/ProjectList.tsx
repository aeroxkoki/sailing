import React, { useState } from 'react';
import { useRouter } from 'next/router';
import ProjectCard, { Project } from './ProjectCard';
import Button from '../common/Button';
import Input from '../forms/Input';

interface ProjectListProps {
  projects: Project[];
  onCreateProject?: () => void;
  onProjectClick?: (project: Project) => void;
  loading?: boolean;
  className?: string;
}

const ProjectList: React.FC<ProjectListProps> = ({
  projects,
  onCreateProject,
  onProjectClick,
  loading = false,
  className = '',
}) => {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [tagFilter, setTagFilter] = useState<string>('');

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  // Handle status filter change
  const handleStatusFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value);
  };

  // Handle tag filter change
  const handleTagFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTagFilter(e.target.value);
  };

  // Filter projects based on search term and filters
  const filteredProjects = projects.filter((project) => {
    // Apply search filter
    const matchesSearch =
      !searchTerm ||
      project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (project.description &&
        project.description.toLowerCase().includes(searchTerm.toLowerCase()));

    // Apply status filter
    const matchesStatus =
      statusFilter === 'all' || project.status === statusFilter;

    // Apply tag filter
    const matchesTag =
      !tagFilter ||
      (project.tags &&
        project.tags.some((tag) =>
          tag.toLowerCase().includes(tagFilter.toLowerCase())
        ));

    return matchesSearch && matchesStatus && matchesTag;
  });

  // Handle project click
  const handleProjectClick = (project: Project) => {
    if (onProjectClick) {
      onProjectClick(project);
    } else {
      router.push(`/projects/${project.id}`);
    }
  };

  // Get unique tags from all projects
  const allTags = Array.from(
    new Set(
      projects
        .filter((project) => project.tags && project.tags.length > 0)
        .flatMap((project) => project.tags || [])
    )
  ).sort();

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-xl font-semibold">プロジェクト一覧</h2>
        {onCreateProject && (
          <Button variant="primary" onClick={onCreateProject}>
            新規プロジェクト
          </Button>
        )}
      </div>

      <div className="bg-white p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <Input
            placeholder="プロジェクトを検索..."
            value={searchTerm}
            onChange={handleSearchChange}
            fullWidth
          />

          <div>
            <label
              htmlFor="status-filter"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              ステータス
            </label>
            <select
              id="status-filter"
              value={statusFilter}
              onChange={handleStatusFilterChange}
              className="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="all">すべて</option>
              <option value="active">進行中</option>
              <option value="completed">完了</option>
              <option value="archived">アーカイブ</option>
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
        </div>

        {loading ? (
          <div className="py-12 flex justify-center">
            <div className="animate-spin h-8 w-8 border-4 border-blue-500 rounded-full border-t-transparent"></div>
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="py-12 text-center text-gray-500">
            {searchTerm || statusFilter !== 'all' || tagFilter ? (
              <p>検索条件に一致するプロジェクトがありません。</p>
            ) : (
              <p>
                プロジェクトがまだありません。「新規プロジェクト」ボタンをクリックして作成してみましょう。
              </p>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredProjects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onClick={handleProjectClick}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectList;