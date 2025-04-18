import React, { useState, useRef, InputHTMLAttributes } from 'react';

interface FileUploadProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange' | 'type'> {
  label?: string;
  helperText?: string;
  error?: string;
  acceptedFileTypes?: string;
  maxSize?: number; // in bytes
  onChange?: (file: File | null) => void;
  fullWidth?: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({
  label,
  helperText,
  error,
  acceptedFileTypes,
  maxSize,
  onChange,
  fullWidth = false,
  className = '',
  id,
  ...rest
}) => {
  const [fileName, setFileName] = useState<string>('');
  const [fileError, setFileError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadId = id || `file-upload-${Math.random().toString(36).substring(2, 9)}`;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files ? e.target.files[0] : null;
    validateAndSetFile(file);
  };

  const validateAndSetFile = (file: File | null) => {
    setFileError(null);

    if (!file) {
      setFileName('');
      if (onChange) onChange(null);
      return;
    }

    // Check file type
    if (acceptedFileTypes) {
      const fileType = file.type;
      const fileExtension = file.name.split('.').pop()?.toLowerCase();
      const acceptedTypes = acceptedFileTypes.split(',').map(type => type.trim());
      
      const isTypeAccepted = acceptedTypes.some(type => {
        if (type.startsWith('.')) {
          // Check by extension
          return `.${fileExtension}` === type;
        } else {
          // Check by MIME type
          return fileType === type || type === '*/*' || type === `${fileType.split('/')[0]}/*`;
        }
      });

      if (!isTypeAccepted) {
        setFileError(`許可されていないファイル形式です。${acceptedFileTypes} 形式のファイルを選択してください。`);
        if (onChange) onChange(null);
        return;
      }
    }

    // Check file size
    if (maxSize && file.size > maxSize) {
      const sizeInMB = maxSize / (1024 * 1024);
      setFileError(`ファイルサイズが大きすぎます。最大 ${sizeInMB.toFixed(2)} MB までのファイルを選択してください。`);
      if (onChange) onChange(null);
      return;
    }

    setFileName(file.name);
    if (onChange) onChange(file);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    validateAndSetFile(file);
  };

  const handleClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleRemoveFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setFileName('');
    setFileError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (onChange) onChange(null);
  };

  return (
    <div className={`mb-4 ${fullWidth ? 'w-full' : ''}`}>
      {label && (
        <label
          htmlFor={uploadId}
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
        </label>
      )}
      <div
        className={`
          border-2 border-dashed rounded-md p-4 text-center cursor-pointer transition-colors
          ${isDragging ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${error || fileError ? 'border-red-300 bg-red-50' : ''}
          ${fullWidth ? 'w-full' : ''}
          ${className}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          id={uploadId}
          type="file"
          className="sr-only"
          onChange={handleFileChange}
          accept={acceptedFileTypes}
          {...rest}
        />
        
        {fileName ? (
          <div className="flex items-center justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5 text-blue-500 mr-2"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
            <span className="text-sm text-gray-700 truncate max-w-xs">{fileName}</span>
            <button
              type="button"
              onClick={handleRemoveFile}
              className="ml-2 text-gray-400 hover:text-gray-500"
            >
              <span className="sr-only">削除</span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        ) : (
          <div>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className="mt-1 text-sm text-gray-600">
              ファイルをここにドラッグ＆ドロップするか<br />
              <span className="text-blue-600 hover:text-blue-500">クリックしてファイルを選択</span>してください
            </p>
            <p className="mt-1 text-xs text-gray-500">
              {acceptedFileTypes && `許可されているファイル形式: ${acceptedFileTypes}`}
              {acceptedFileTypes && maxSize && `, `}
              {maxSize && `最大サイズ: ${(maxSize / (1024 * 1024)).toFixed(2)} MB`}
            </p>
          </div>
        )}
      </div>
      
      {helperText && !error && !fileError && (
        <p className="mt-1 text-sm text-gray-500">
          {helperText}
        </p>
      )}
      
      {(error || fileError) && (
        <p className="mt-1 text-sm text-red-600" role="alert">
          {error || fileError}
        </p>
      )}
    </div>
  );
};

export default FileUpload;