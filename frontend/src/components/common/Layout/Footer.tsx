import React from 'react';

interface FooterProps {
  className?: string;
}

const Footer: React.FC<FooterProps> = ({ className = '' }) => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className={`bg-white border-t border-gray-200 ${className}`}>
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="text-gray-500 text-sm">
            &copy; {currentYear} セーリング戦略分析システム - All rights reserved.
          </div>
          <div className="mt-4 md:mt-0">
            <nav className="flex space-x-4">
              <a
                href="#"
                className="text-gray-500 hover:text-gray-700 text-sm"
              >
                プライバシーポリシー
              </a>
              <a
                href="#"
                className="text-gray-500 hover:text-gray-700 text-sm"
              >
                利用規約
              </a>
              <a
                href="#"
                className="text-gray-500 hover:text-gray-700 text-sm"
              >
                お問い合わせ
              </a>
            </nav>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;