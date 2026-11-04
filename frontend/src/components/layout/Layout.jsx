import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

export default function Layout({
  lastUpdated,
  isRefreshing,
  onRefresh,
  pollInterval,
  onPollIntervalChange,
  isHealthy,
  onOpenTestModal,
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#080C14] text-slate-100 flex">
      {/* Persistent Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-w-0">
        <Topbar
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          lastUpdated={lastUpdated}
          isRefreshing={isRefreshing}
          onRefresh={onRefresh}
          pollInterval={pollInterval}
          onPollIntervalChange={onPollIntervalChange}
          isHealthy={isHealthy}
          onOpenTestModal={onOpenTestModal}
        />

        <main className="flex-1 p-4 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

