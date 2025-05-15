import React, { useState, useRef } from 'react';

interface FileUploaderProps {
  onFileSelect: (files: File[]) => void;
  multiple?: boolean;
  acceptedFileTypes?: string;
  maxSize?: number; // MB
  className?: string;
}

const FileUploader: React.FC<FileUploaderProps> = ({
  onFileSelect,
  acceptedFileTypes = ".gpx,.csv,.fit,.tcx",
  maxSize = 10, // 10MB
  className = '',
  multiple = false,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    const selectedFiles = multiple ? Array.from(files) : [files[0]];
    validateAndProcessFiles(selectedFiles);
  };
  
  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(false);
    
    const files = event.dataTransfer.files;
    if (!files || files.length === 0) return;
    
    const selectedFiles = multiple ? Array.from(files) : [files[0]];
    validateAndProcessFiles(selectedFiles);
  };
  
  const validateAndProcessFiles = (files: File[]) => {
    // ファイル数チェック
    if (!multiple && files.length > 1) {
      setError('複数ファイルの選択は無効です。1つのファイルを選択してください。');
      return;
    }
    
    // 各ファイルをバリデーション
    const invalidFiles: string[] = [];
    const oversizedFiles: string[] = [];
    
    files.forEach(file => {
      // ファイルタイプチェック
      const fileExt = file.name.split('.').pop()?.toLowerCase() || '';
      const isValidType = acceptedFileTypes
        .split(',')
        .some(type => type.includes(fileExt));
      
      if (!isValidType) {
        invalidFiles.push(file.name);
      }
      
      // サイズチェック
      if (file.size > maxSize * 1024 * 1024) {
        oversizedFiles.push(file.name);
      }
    });
    
    // エラーを報告
    if (invalidFiles.length > 0) {
      setError(`対応していないファイル形式があります: ${invalidFiles.join(', ')}。${acceptedFileTypes}のファイルをアップロードしてください。`);
      return;
    }
    
    if (oversizedFiles.length > 0) {
      setError(`ファイルサイズが大きすぎるものがあります: ${oversizedFiles.join(', ')}。${maxSize}MB以下のファイルをアップロードしてください。`);
      return;
    }
    
    setError(null);
    onFileSelect(files);
  };
  
  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(true);
  };
  
  const handleDragLeave = () => {
    setIsDragging(false);
  };
  
  const openFileDialog = () => {
    fileInputRef.current?.click();
  };
  
  return (
    <div className={`${className}`}>
      <div 
        className={`
          border-2 border-dashed rounded-xl p-4 sm:p-8 text-center transition-colors
          ${isDragging 
            ? 'border-blue-500 bg-blue-900 bg-opacity-10' 
            : 'border-gray-600 hover:border-gray-500'
          }
        `}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={openFileDialog}
      >
        <div className="flex flex-col items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 sm:h-16 sm:w-16 mx-auto text-gray-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          
          <h2 className="text-lg sm:text-xl font-medium text-gray-300 mb-2">GPSログをアップロード</h2>
          
          <p className="text-sm sm:text-base text-gray-500 mb-4 sm:mb-6">
            <span className="hidden sm:inline">GPX, FIT, CSVなどのファイルを<br />ドラッグ＆ドロップ</span>
            <span className="sm:hidden">クリックして選択</span>
            <span className="hidden sm:inline">または</span>
            <span className="sm:hidden">または</span>
            <span className="sm:hidden">ドラッグ＆ドロップ</span>
            <span className="hidden sm:inline">クリックして選択</span>
          </p>
          
          <div className="text-xs text-gray-600">
            対応フォーマット: {acceptedFileTypes.replace(/\./g, '').toUpperCase()}
          </div>
        </div>
        
        <input 
          ref={fileInputRef}
          type="file" 
          className="hidden" 
          onChange={handleFileChange}
          accept={acceptedFileTypes}
          multiple={multiple}
        />
      </div>
      
      {error && (
        <div className="mt-4 p-3 bg-red-900 bg-opacity-50 border border-red-800 rounded text-red-200 text-sm">
          <div className="flex items-start">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>{error}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUploader;
