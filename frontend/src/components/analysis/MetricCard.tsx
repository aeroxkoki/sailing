import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  icon?: React.ReactNode;
  color?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onClick?: () => void;
}

const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit,
  icon,
  color = 'default',
  size = 'md',
  className = '',
  onClick,
}) => {
  // カラースタイルの決定
  const colorClasses = {
    default: 'bg-gray-800 text-gray-200',
    success: 'bg-green-900 bg-opacity-50 text-green-200',
    warning: 'bg-yellow-900 bg-opacity-50 text-yellow-200',
    danger: 'bg-red-900 bg-opacity-50 text-red-200',
    info: 'bg-blue-900 bg-opacity-50 text-blue-200',
  };
  
  // サイズスタイルの決定
  const sizeClasses = {
    sm: 'p-2',
    md: 'p-3',
    lg: 'p-4',
  };
  
  // ラベルとバリューのサイズ
  const labelSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };
  
  const valueSizes = {
    sm: 'text-lg',
    md: 'text-xl',
    lg: 'text-2xl',
  };
  
  return (
    <div 
      className={`
        ${colorClasses[color]} 
        ${sizeClasses[size]} 
        rounded-md shadow-sm backdrop-filter backdrop-blur-sm
        ${onClick ? 'cursor-pointer hover:bg-opacity-80 transition-colors' : ''}
        ${className}
      `}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className={`${labelSizes[size]} font-medium text-opacity-75`}>
          {label}
        </div>
        {icon && (
          <div className="text-opacity-75">
            {icon}
          </div>
        )}
      </div>
      
      <div className="flex items-baseline mt-1">
        <div className={`${valueSizes[size]} font-semibold`}>
          {value}
        </div>
        {unit && (
          <div className={`${labelSizes[size]} ml-1 text-opacity-75`}>
            {unit}
          </div>
        )}
      </div>
    </div>
  );
};

export default MetricCard;
