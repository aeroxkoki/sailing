import React, { useState } from 'react';
import Input from '../forms/Input';
import Button from '../common/Button';
import { Project } from './ProjectCard';

interface ProjectFormProps {
  project?: Partial<Project>;
  onSubmit: (project: Partial<Project>) => void;
  onCancel?: () => void;
  isSubmitting?: boolean;
  className?: string;
}

const ProjectForm: React.FC<ProjectFormProps> = ({
  project,
  onSubmit,
  onCancel,
  isSubmitting = false,
  className = '',
}) => {
  // Initialize form state
  const [formData, setFormData] = useState<Partial<Project>>({
    name: '',
    description: '',
    tags: [],
    status: 'active',
    ...project,
  });

  // Initialize form errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Handle input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    
    // Clear error when field is changed
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  // Handle tags input
  const handleTagsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const tags = value.split(',').map((tag) => tag.trim()).filter(Boolean);
    setFormData((prev) => ({ ...prev, tags }));
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    const newErrors: Record<string, string> = {};
    
    if (!formData.name?.trim()) {
      newErrors.name = 'プロジェクト名を入力してください';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    // Submit form
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className={`space-y-4 ${className}`}>
      <Input
        id="name"
        name="name"
        label="プロジェクト名"
        value={formData.name || ''}
        onChange={handleChange}
        error={errors.name}
        fullWidth
        required
      />
      
      <div className="mb-4">
        <label
          htmlFor="description"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          説明
        </label>
        <textarea
          id="description"
          name="description"
          rows={3}
          value={formData.description || ''}
          onChange={handleChange}
          className="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
      </div>
      
      <Input
        id="tags"
        name="tags"
        label="タグ (カンマ区切り)"
        value={formData.tags?.join(', ') || ''}
        onChange={handleTagsChange}
        helperText="例: 練習, レース, トレーニング"
        fullWidth
      />
      
      <div className="mb-4">
        <label
          htmlFor="status"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          ステータス
        </label>
        <select
          id="status"
          name="status"
          value={formData.status || 'active'}
          onChange={(e) => setFormData((prev) => ({ ...prev, status: e.target.value as any }))}
          className="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        >
          <option value="active">進行中</option>
          <option value="completed">完了</option>
          <option value="archived">アーカイブ</option>
        </select>
      </div>
      
      <div className="flex justify-end space-x-3 pt-4">
        {onCancel && (
          <Button
            variant="secondary"
            onClick={onCancel}
            type="button"
          >
            キャンセル
          </Button>
        )}
        <Button
          variant="primary"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? '保存中...' : (project?.id ? '更新' : '作成')}
        </Button>
      </div>
    </form>
  );
};

export default ProjectForm;