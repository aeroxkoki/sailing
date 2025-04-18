import React, { useState } from 'react';
import Input from '../forms/Input';
import Button from '../common/Button';
import FileUpload from '../forms/FileUpload';
import { Session } from './SessionCard';
import { Project } from '../project/ProjectCard';

interface SessionFormProps {
  session?: Partial<Session>;
  projects?: Project[];
  onSubmit: (session: Partial<Session>, file?: File) => void;
  onCancel?: () => void;
  isSubmitting?: boolean;
  className?: string;
}

const SessionForm: React.FC<SessionFormProps> = ({
  session,
  projects = [],
  onSubmit,
  onCancel,
  isSubmitting = false,
  className = '',
}) => {
  // Initialize form state
  const [formData, setFormData] = useState<Partial<Session>>({
    name: '',
    description: '',
    date: new Date().toISOString().split('T')[0],
    dataType: 'gps',
    tags: [],
    status: 'raw',
    ...session,
  });

  // Initialize file state
  const [file, setFile] = useState<File | null>(null);

  // Initialize form errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Handle input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
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

  // Handle file upload
  const handleFileUpload = (uploadedFile: File | null) => {
    setFile(uploadedFile);
    
    // If file is uploaded, set dataType based on file extension
    if (uploadedFile) {
      const extension = uploadedFile.name.split('.').pop()?.toLowerCase();
      let dataType: 'gps' | 'wind' | 'combined' = 'gps';
      
      // Set data type based on file extension
      if (extension === 'csv' || extension === 'gpx' || extension === 'tcx') {
        dataType = 'gps';
      } else if (extension === 'json') {
        dataType = 'wind';
      }
      
      setFormData((prev) => ({ ...prev, dataType }));
    }
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    const newErrors: Record<string, string> = {};
    
    if (!formData.name?.trim()) {
      newErrors.name = 'セッション名を入力してください';
    }
    
    if (!formData.date) {
      newErrors.date = '日付を入力してください';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    // Submit form
    onSubmit(formData, file || undefined);
  };

  return (
    <form onSubmit={handleSubmit} className={`space-y-4 ${className}`}>
      <Input
        id="name"
        name="name"
        label="セッション名"
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
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          id="date"
          name="date"
          type="date"
          label="日付"
          value={typeof formData.date === 'string' ? formData.date.split('T')[0] : new Date(formData.date || Date.now()).toISOString().split('T')[0]}
          onChange={handleChange}
          error={errors.date}
          fullWidth
          required
        />
        
        <Input
          id="location"
          name="location"
          label="場所"
          value={formData.location || ''}
          onChange={handleChange}
          fullWidth
        />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="mb-4">
          <label
            htmlFor="dataType"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            データタイプ
          </label>
          <select
            id="dataType"
            name="dataType"
            value={formData.dataType || 'gps'}
            onChange={handleChange}
            className="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="gps">GPS</option>
            <option value="wind">風向風速</option>
            <option value="combined">複合データ</option>
          </select>
        </div>
        
        {projects.length > 0 && (
          <div className="mb-4">
            <label
              htmlFor="projectId"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              プロジェクト
            </label>
            <select
              id="projectId"
              name="projectId"
              value={formData.projectId || ''}
              onChange={handleChange}
              className="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="">プロジェクトを選択</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>
        )}
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
      
      <FileUpload
        label="データファイル"
        acceptedFileTypes=".csv,.gpx,.tcx,.json"
        onChange={handleFileUpload}
        helperText="GPSデータ（CSV, GPX, TCX）または風向風速データ（JSON）"
        fullWidth
      />
      
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
          {isSubmitting ? '保存中...' : (session?.id ? '更新' : '作成')}
        </Button>
      </div>
    </form>
  );
};

export default SessionForm;