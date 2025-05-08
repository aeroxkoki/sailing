import React, { useRef, useEffect } from 'react';

interface MenuItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  onClick?: () => void;
}

interface MenuProps {
  items: MenuItem[];
  isOpen: boolean;
  onClose: () => void;
  position?: 'left' | 'right';
  className?: string;
}

const Menu: React.FC<MenuProps> = ({
  items,
  isOpen,
  onClose,
  position = 'right',
  className = ''
}) => {
  const menuRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    // クリックイベントのリスナーを追加
    const handleClickOutside = (event: MouseEvent) => {
      if (isOpen && menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);
  
  if (!isOpen) return null;
  
  return (
    <div 
      ref={menuRef}
      className={`absolute top-full mt-1 ${position === 'right' ? 'right-0' : 'left-0'} 
                 bg-gray-800 rounded-md shadow-lg py-1 w-48 z-50 ${className}`}
    >
      {items.map((item) => (
        <button
          key={item.id}
          onClick={() => {
            if (item.onClick) {
              item.onClick();
            }
            onClose();
          }}
          className="w-full text-left px-4 py-2 text-sm text-gray-200 hover:bg-gray-700 flex items-center"
        >
          {item.icon && <span className="mr-2">{item.icon}</span>}
          {item.label}
        </button>
      ))}
    </div>
  );
};

export default Menu;
