import React from 'react';

const Dashboard = () => {
  return (
    <div className="dashboard grid grid-cols-3 gap-4">
      <div className="tasks bg-white p-4 rounded-lg shadow-md">
        <h3 className="text-xl font-semibold mb-2">Tasks</h3>
        <p className="text-sm">Task list goes here...</p>
      </div>
      <div className="calendar bg-white p-4 rounded-lg shadow-md">
        <h3 className="text-xl font-semibold mb-2">Calendar</h3>
        <p className="text-sm">Calendar goes here...</p>
      </div>
    </div>
  );
};

export default Dashboard; 