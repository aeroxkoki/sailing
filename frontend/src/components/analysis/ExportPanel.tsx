import React, { useState } from 'react';
import { useAnalysis } from '@/context/AnalysisContext';

interface ExportPanelProps {
  className?: string;
  onClose?: () => void;
}

type ExportFormat = 'pdf' | 'csv' | 'gpx' | 'json';

interface ExportOption {
  id: ExportFormat;
  label: string;
  icon: React.ReactNode;
  description: string;
}

const ExportPanel: React.FC<ExportPanelProps> = ({ className = '', onClose }) => {
  const { data, exportResults } = useAnalysis();
  const [isExporting, setIsExporting] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('pdf');
  const [includeSettings, setIncludeSettings] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // エクスポートオプション
  const exportOptions: ExportOption[] = [
    {
      id: 'pdf',
      label: 'PDF レポート',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
        </svg>
      ),
      description: '詳細な分析レポートをPDF形式でエクスポート',
    },
    {
      id: 'csv',
      label: 'CSV データ',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
        </svg>
      ),
      description: 'GPSデータ、風推定、戦略ポイントをCSV形式で保存',
    },
    {
      id: 'gpx',
      label: 'GPX トラック',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M12 1.586l-4 4v12.828l4-4V1.586zM3.707 3.293A1 1 0 002 4v10a1 1 0 00.293.707L6 18.414V5.586L3.707 3.293zM17.707 5.293L14 1.586v12.828l2.293 2.293A1 1 0 0018 16V6a1 1 0 00-.293-.707z" clipRule="evenodd" />
        </svg>
      ),
      description: 'GPS航跡をGPX形式で保存（他のGPSアプリで使用可能）',
    },
    {
      id: 'json',
      label: 'JSON データ',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M14.5 3a1 1 0 011 1v12a1 1 0 01-1 1h-9a1 1 0 01-1-1V4a1 1 0 011-1h9zm-1 1h-7v10h7V4z" clipRule="evenodd" />
          <path d="M6.5 6a.5.5 0 000 1h7a.5.5 0 000-1h-7zM6.5 9a.5.5 0 000 1h7a.5.5 0 000-1h-7zM6.5 12a.5.5 0 000 1h7a.5.5 0 000-1h-7z" />
        </svg>
      ),
      description: 'すべての分析データをJSON形式で保存（開発者向け）',
    },
  ];

  // エクスポート処理
  const handleExport = async () => {
    if (!data.sessionId) {
      setError('エクスポートするセッションがありません');
      return;
    }

    setIsExporting(true);
    setError(null);

    try {
      const blob = await exportResults(selectedFormat, includeSettings);
      
      // ファイル名の生成
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const fileName = `sailing-analysis-${data.fileName ? data.fileName.split('.')[0] : timestamp}.${selectedFormat}`;
      
      // ダウンロード
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      
      // クリーンアップ
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 0);
      
    } catch (err: any) {
      setError(err.message || 'エクスポート中にエラーが発生しました');
      console.error('Export error:', err);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className={`bg-gray-900 border border-gray-700 rounded-lg shadow-lg p-5 ${className}`}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-medium text-gray-200">分析データのエクスポート</h2>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-300 focus:outline-none"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>

      <div className="mb-5">
        <label className="block text-sm font-medium text-gray-400 mb-2">エクスポート形式を選択</label>
        <div className="grid grid-cols-1 gap-2">
          {exportOptions.map((option) => (
            <label
              key={option.id}
              className={`flex items-start p-3 rounded-lg cursor-pointer transition-colors ${
                selectedFormat === option.id ? 'bg-blue-600 bg-opacity-20 border border-blue-500' : 'bg-gray-800 border border-transparent hover:border-gray-700'
              }`}
            >
              <input
                type="radio"
                className="sr-only"
                name="exportFormat"
                value={option.id}
                checked={selectedFormat === option.id}
                onChange={() => setSelectedFormat(option.id)}
              />
              <div className="flex-shrink-0 text-blue-500 mr-3">{option.icon}</div>
              <div>
                <div className="text-sm font-medium text-gray-200">{option.label}</div>
                <div className="text-xs text-gray-400 mt-1">{option.description}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div className="mb-5">
        <label className="flex items-center">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-gray-600 text-blue-600 focus:ring-blue-500 focus:ring-offset-gray-900"
            checked={includeSettings}
            onChange={(e) => setIncludeSettings(e.target.checked)}
          />
          <span className="ml-2 text-sm text-gray-300">分析設定を含める</span>
        </label>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-900 bg-opacity-50 border border-red-800 rounded-md">
          <p className="text-sm text-red-200">{error}</p>
        </div>
      )}

      <button
        onClick={handleExport}
        disabled={isExporting || !data.sessionId}
        className={`w-full py-2 rounded-md font-medium transition-colors ${
          isExporting || !data.sessionId
            ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 text-white'
        }`}
      >
        {isExporting ? (
          <span className="flex items-center justify-center">
            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            エクスポート中...
          </span>
        ) : !data.sessionId ? (
          'セッションがありません'
        ) : (
          `${selectedFormat.toUpperCase()}としてエクスポート`
        )}
      </button>
    </div>
  );
};

export default ExportPanel;
