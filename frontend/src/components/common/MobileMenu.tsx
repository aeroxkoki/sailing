import React from 'react';
import { useRouter } from 'next/router';

interface MenuItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  onClick?: () => void;
  href?: string;
}

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  items: MenuItem[];
}

const MobileMenu: React.FC<MobileMenuProps> = ({ isOpen, onClose, items }) => {
  const router = useRouter();
  
  if (!isOpen) return null;
  
  const handleItemClick = (item: MenuItem) => {
    if (item.onClick) {
      item.onClick();
    } else if (item.href) {
      router.push(item.href);
    }
    onClose();
  };
  
  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Menu panel */}
      <div className="fixed right-0 top-0 h-full w-64 bg-gray-900 shadow-lg overflow-y-auto transition-transform transform">
        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
          <h2 className="text-lg font-medium text-gray-200">メニュー</h2>
          <button 
            className="p-2 rounded-full hover:bg-gray-800 text-gray-400"
            onClick={onClose}
            aria-label="Close menu"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <nav className="p-4">
          <ul className="space-y-2">
            {items.map((item) => (
              <li key={item.id}>
                <button
                  className="w-full flex items-center p-3 rounded-md hover:bg-gray-800 text-gray-300 hover:text-white transition-colors"
                  onClick={() => handleItemClick(item)}
                >
                  {item.icon && <span className="mr-3">{item.icon}</span>}
                  <span>{item.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </div>
  );
};

export default MobileMenu;
