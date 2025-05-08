import React from 'react';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  footer?: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
  variant?: 'default' | 'dark' | 'outlined';
}

const Card: React.FC<CardProps> = ({
  children,
  title,
  footer,
  className = '',
  onClick,
  hoverable = false,
  variant = 'default',
}) => {
  // バリアントに基づくスタイル
  const variantStyles = {
    default: 'bg-white rounded-lg shadow-md text-gray-800',
    dark: 'bg-gray-800 rounded-lg shadow-md text-gray-200 border border-gray-700',
    outlined: 'bg-transparent rounded-lg border border-gray-300 text-gray-800',
  };

  // タイトル部分のバリアントスタイル
  const titleVariantStyles = {
    default: 'border-b border-gray-200 font-medium text-gray-700',
    dark: 'border-b border-gray-700 font-medium text-gray-200',
    outlined: 'border-b border-gray-300 font-medium text-gray-700',
  };

  // フッター部分のバリアントスタイル
  const footerVariantStyles = {
    default: 'bg-gray-50 border-t border-gray-200',
    dark: 'bg-gray-900 border-t border-gray-700',
    outlined: 'bg-gray-50 border-t border-gray-300',
  };

  return (
    <div
      className={`
        ${variantStyles[variant]} overflow-hidden
        ${hoverable ? 'hover:shadow-lg transition-shadow duration-200' : ''}
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
      onClick={onClick}
    >
      {title && (
        <div className={`px-4 py-3 ${titleVariantStyles[variant]}`}>
          {title}
        </div>
      )}
      <div className="p-4">{children}</div>
      {footer && (
        <div className={`px-4 py-3 ${footerVariantStyles[variant]}`}>
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;