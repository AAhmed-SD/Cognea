import React from 'react';
import Sidebar from '../Sidebar/Sidebar';
import Hero from '../Hero/Hero';
import Dashboard from '../Dashboard/Dashboard';

const Layout = () => {
  return (
    <div className="layout flex bg-background text-primaryText">
      <Sidebar className="w-1/4" />
      <div className="main-content flex-1 p-4">
        <Hero className="mb-4" />
        <Dashboard />
      </div>
    </div>
  );
};

export default Layout; 