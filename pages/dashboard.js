import { useState, useEffect } from 'react';
import Head from 'next/head';

export default function Dashboard() {
  const [tasks, setTasks] = useState([]);
  const [goals, setGoals] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate loading data
    setTimeout(() => {
      setTasks([
        { id: 1, title: 'Review calculus notes', priority: 'high', status: 'pending' },
        { id: 2, title: 'Complete project proposal', priority: 'medium', status: 'in_progress' },
        { id: 3, title: 'Exercise routine', priority: 'low', status: 'completed' }
      ]);
      setGoals([
        { id: 1, title: 'Master Calculus', progress: 75, target_date: '2024-02-15' },
        { id: 2, title: 'Launch MVP', progress: 45, target_date: '2024-03-01' }
      ]);
      setIsLoading(false);
    }, 1000);
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Dashboard - Cognie</title>
        <meta name="description" content="Your AI-powered productivity dashboard" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold text-indigo-600">Cognie</h1>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-gray-600">Welcome back!</span>
                <button className="text-gray-600 hover:text-gray-900">Settings</button>
                <button className="text-gray-600 hover:text-gray-900">Logout</button>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* AI Assistant Section */}
          <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg p-6 mb-8 text-white">
            <div className="flex items-center mb-4">
              <span className="text-2xl mr-3">🤖</span>
              <h2 className="text-2xl font-bold">AI Assistant</h2>
            </div>
            <p className="text-indigo-100 mb-4">
              Your AI has analyzed your patterns and suggests optimizing your schedule for better productivity.
            </p>
            <button className="bg-white text-indigo-600 px-4 py-2 rounded-md font-semibold hover:bg-gray-100">
              Get AI Recommendations
            </button>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center">
                <span className="text-2xl mr-3">📋</span>
                <div>
                  <p className="text-sm text-gray-600">Tasks Today</p>
                  <p className="text-2xl font-bold text-gray-900">{tasks.length}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center">
                <span className="text-2xl mr-3">✅</span>
                <div>
                  <p className="text-sm text-gray-600">Completed</p>
                  <p className="text-2xl font-bold text-green-600">
                    {tasks.filter(t => t.status === 'completed').length}
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center">
                <span className="text-2xl mr-3">🎯</span>
                <div>
                  <p className="text-sm text-gray-600">Active Goals</p>
                  <p className="text-2xl font-bold text-gray-900">{goals.length}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center">
                <span className="text-2xl mr-3">📊</span>
                <div>
                  <p className="text-sm text-gray-600">Productivity Score</p>
                  <p className="text-2xl font-bold text-indigo-600">87%</p>
                </div>
              </div>
            </div>
          </div>

          {/* Main Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Tasks */}
            <div className="bg-white rounded-lg shadow-sm">
              <div className="p-6 border-b">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Today's Tasks</h3>
                  <button className="text-indigo-600 hover:text-indigo-700 font-medium">
                    Add Task
                  </button>
                </div>
              </div>
              <div className="p-6">
                {tasks.map((task) => (
                  <div key={task.id} className="flex items-center justify-between py-3 border-b last:border-b-0">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        checked={task.status === 'completed'}
                        className="mr-3 h-4 w-4 text-indigo-600"
                      />
                      <span className={`${task.status === 'completed' ? 'line-through text-gray-500' : 'text-gray-900'}`}>
                        {task.title}
                      </span>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      task.priority === 'high' ? 'bg-red-100 text-red-800' :
                      task.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {task.priority}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Goals */}
            <div className="bg-white rounded-lg shadow-sm">
              <div className="p-6 border-b">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Goals Progress</h3>
                  <button className="text-indigo-600 hover:text-indigo-700 font-medium">
                    Add Goal
                  </button>
                </div>
              </div>
              <div className="p-6">
                {goals.map((goal) => (
                  <div key={goal.id} className="mb-6 last:mb-0">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">{goal.title}</h4>
                      <span className="text-sm text-gray-500">{goal.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${goal.progress}%` }}
                      ></div>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">Target: {goal.target_date}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* AI Features Showcase */}
          <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button className="p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:bg-indigo-50 transition-colors">
                <div className="text-center">
                  <span className="text-2xl mb-2 block">🧠</span>
                  <h4 className="font-medium text-gray-900">Smart Scheduling</h4>
                  <p className="text-sm text-gray-600">AI optimizes your day</p>
                </div>
              </button>
              <button className="p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:bg-indigo-50 transition-colors">
                <div className="text-center">
                  <span className="text-2xl mb-2 block">📚</span>
                  <h4 className="font-medium text-gray-900">Flashcard Generation</h4>
                  <p className="text-sm text-gray-600">From your Notion content</p>
                </div>
              </button>
              <button className="p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:bg-indigo-50 transition-colors">
                <div className="text-center">
                  <span className="text-2xl mb-2 block">📊</span>
                  <h4 className="font-medium text-gray-900">Productivity Insights</h4>
                  <p className="text-sm text-gray-600">AI-powered analytics</p>
                </div>
              </button>
            </div>
          </div>
        </main>
      </div>
    </>
  );
} 