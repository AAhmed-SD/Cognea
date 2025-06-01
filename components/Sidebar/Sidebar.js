import React from 'react';

const Sidebar = () => {
  return (
    <div className="sidebar bg-white shadow-md p-4">
      <h2 className="text-xl font-bold mb-4">Sidebar</h2>
      <ul className="space-y-2">
        <li className="hover:text-primaryAccent">Home</li>
        <li className="hover:text-primaryAccent">Tasks</li>
        <li className="hover:text-primaryAccent">Calendar</li>
        <li className="hover:text-primaryAccent">Settings</li>
      </ul>
    </div>
  );
};

export default Sidebar; 