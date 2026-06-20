'use client';

import { useState } from 'react';
import Sidebar from '../components/Sidebar';
import ChatInterface from '../components/ChatInterface';

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <>
      <Sidebar isOpen={sidebarOpen} toggleSidebar={() => setSidebarOpen(false)} />
      
      {/* Mobile sidebar toggle button */}
      <div 
        className="sidebar-toggle" 
        onClick={() => setSidebarOpen(true)}
        style={{ position: 'absolute', top: '12px', left: '12px', zIndex: 50 }}
      >
        ☰
      </div>
      
      <ChatInterface />
    </>
  );
}
