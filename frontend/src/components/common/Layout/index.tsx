import React, { ReactNode } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import Footer from './Footer';

interface LayoutProps {
  children: ReactNode;
  useSidebar?: boolean;
}

const Layout: React.FC<LayoutProps> = ({ children, useSidebar = true }) => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {useSidebar ? (
        <div className="flex flex-col md:flex-row">
          <div className="hidden md:block md:w-64">
            <Sidebar />
          </div>
          <div className="flex-1 flex flex-col">
            <Header />
            <main className="flex-1 p-4 sm:p-6 lg:p-8">{children}</main>
            <Footer />
          </div>
        </div>
      ) : (
        <>
          <Header />
          <main className="flex-1 p-4 sm:p-6 lg:p-8">{children}</main>
          <Footer />
        </>
      )}
    </div>
  );
};

export default Layout;