import React from 'react';
import { useRouter } from 'next/router';
import Card from '../common/Card';
import Badge from '../common/Badge';

export interface Project {
  id: string;
  name: string;
  description?: string;
  createdAt: string | number | Date;
  updatedAt?: string | number | Date;
  sessionCount?: number;
  tags?: string[];
  status?: 'active' | 'archived' | 'completed';
}

interface ProjectCardProps {
  project: Project;
  onClick?: (project: Project) => void;
  className?: string;
}

const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onClick,
  className = '',
}) => {
  const router = useRouter();
  const { id, name, description, createdAt, updatedAt, sessionCount, tags, status } = project;

  // Format dates
  const formattedCreatedAt = new Date(createdAt).toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  const formattedUpdatedAt = updatedAt
    ? new Date(updatedAt).toLocaleDateString('ja-JP', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : null;

  // Handle click
  const handleClick = () => {
    if (onClick) {
      onClick(project);
    } else {
      router.push(`/projects/${id}`);
    }
  };

  // Get status badge variant
  const getStatusVariant = () => {
    switch (status) {
      case 'active':
        return 'primary';
      case 'completed':
        return 'success';
      case 'archived':
        return 'default';
      default:
        return 'default';
    }
  };

  // Get status label
  const getStatusLabel = () => {
    switch (status) {
      case 'active':
        return '進行中';
      case 'completed':
        return '完了';
      case 'archived':
        return 'アーカイブ';
      default:
        return '';
    }
  };

  return (
    <Card
      hoverable
      className={`h-full ${className}`}
      onClick={handleClick}
    >
      <div className="flex flex-col h-full">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-lg font-medium text-gray-900 mr-2">{name}</h3>
          {status && (
            <Badge variant={getStatusVariant() as any} size="sm">
              {getStatusLabel()}
            </Badge>
          )}
        </div>
        
        {description && (
          <p className="text-gray-600 text-sm mb-4 line-clamp-2">
            {description}
          </p>
        )}

        <div className="mt-auto pt-4">
          {tags && tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-2">
              {tags.map((tag) => (
                <Badge key={tag} variant="default" size="sm" className="bg-gray-100 text-gray-700">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
          
          <div className="flex justify-between items-center text-xs text-gray-500">
            <div>
              作成: {formattedCreatedAt}
            </div>
            <div className="flex items-center">
              {sessionCount !== undefined && (
                <span className="mr-2">
                  セッション数: {sessionCount}
                </span>
              )}
              {formattedUpdatedAt && (
                <span>
                  更新: {formattedUpdatedAt}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default ProjectCard;