import React from 'react';
import { useRouter } from 'next/router';
import Card from '../common/Card';
import Button from '../common/Button';

interface Project {
  id: string;
  name: string;
  description?: string;
  tags?: string[];
  createdAt: string;
  sessionCount?: number;
}

interface ProjectCardProps {
  project: Project;
  onDelete: (id: string) => void;
}

export function ProjectCard({ project, onDelete }: ProjectCardProps) {
  const router = useRouter();
  
  return (
    <Card variant="dark" className="h-full">
      <div className="p-4 flex flex-col h-full">
        <h3 className="text-lg font-medium text-blue-300">{project.name}</h3>
        {project.description && (
          <p className="text-gray-400 mt-2 flex-grow">{project.description}</p>
        )}
        
        <div className="mt-3 text-sm text-gray-500">
          セッション: {project.sessionCount || 0}
        </div>
        
        <div className="mt-2 flex flex-wrap gap-2">
          {project.tags && project.tags.map((tag) => (
            <span key={tag} className="inline-block px-2 py-1 text-xs bg-gray-800 text-gray-300 rounded">
              {tag}
            </span>
          ))}
        </div>
        
        <div className="mt-4 pt-3 border-t border-gray-700 flex justify-between">
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push(`/projects/${project.id}`)}
          >
            詳細
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              if (confirm('このプロジェクトを削除しますか？')) {
                onDelete(project.id);
              }
            }}
          >
            削除
          </Button>
        </div>
      </div>
    </Card>
  );
}

interface ProjectListProps {
  projects: Project[];
  onDeleteProject: (id: string) => void;
}

export default function ProjectList({ projects, onDeleteProject }: ProjectListProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {projects.map((project) => (
        <ProjectCard
          key={project.id}
          project={project}
          onDelete={onDeleteProject}
        />
      ))}
    </div>
  );
}