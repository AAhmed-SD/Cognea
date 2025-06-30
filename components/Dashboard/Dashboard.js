import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import apiService from '../../services/api';

const Dashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [trendsData, setTrendsData] = useState(null);
  const [weeklyReview, setWeeklyReview] = useState(null);
  const [productivityPatterns, setProductivityPatterns] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [dashboard, trends, review, patterns] = await Promise.all([
        apiService.getDashboard(),
        apiService.getTrends(),
        apiService.getWeeklyReview(),
        apiService.getProductivityPatterns()
      ]);
      
      setDashboardData(dashboard.dashboard);
      setTrendsData(trends.trends);
      setWeeklyReview(review);
      setProductivityPatterns(patterns);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      // Set default data if API fails
      setDashboardData({
        habits: [],
        focus_time: [],
        goals: [],
        task_stats: { total: 0, completed: 0, pending: 0, completion_rate: 0 },
        productivity_score: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePlanDay = async () => {
    try {
      const planData = {
        date: new Date().toISOString().split('T')[0],
        preferences: {
          focus_areas: ['work', 'learning', 'health'],
          duration: '8h'
        }
      };
      const response = await apiService.planDay(planData);
      console.log('Day planned:', response);
      // Refresh dashboard data after planning
      await loadDashboardData();
    } catch (error) {
      console.error('Failed to plan day:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="dashboard space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">
          Welcome back, {user?.name || 'User'}! 👋
        </h1>
        <p className="text-indigo-100">
          Ready to make today productive? Let's get started with your AI-powered schedule.
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={handlePlanDay}
          className="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-blue-100 p-2 rounded-lg">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Plan My Day</h3>
              <p className="text-sm text-gray-600">AI-powered scheduling</p>
            </div>
          </div>
        </button>

        <button className="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="bg-green-100 p-2 rounded-lg">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Track Habits</h3>
              <p className="text-sm text-gray-600">Build consistency</p>
            </div>
          </div>
        </button>

        <button className="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="bg-purple-100 p-2 rounded-lg">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">AI Insights</h3>
              <p className="text-sm text-gray-600">Get personalized tips</p>
            </div>
          </div>
        </button>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {['overview', 'productivity', 'learning', 'habits'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                  activeTab === tab
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Productivity Score */}
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Productivity Score</h3>
                <div className="flex items-center space-x-4">
                  <div className="relative">
                    <svg className="w-16 h-16 transform -rotate-90">
                      <circle
                        cx="32"
                        cy="32"
                        r="28"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="transparent"
                        className="text-gray-200"
                      />
                      <circle
                        cx="32"
                        cy="32"
                        r="28"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="transparent"
                        strokeDasharray={`${(dashboardData?.productivity_score || 0) * 1.76} 176`}
                        className="text-blue-600"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-xl font-bold text-gray-900">
                        {dashboardData?.productivity_score || 0}%
                      </span>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">This week</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {dashboardData?.task_stats?.completion_rate > 80 ? 'Excellent progress!' : 
                       dashboardData?.task_stats?.completion_rate > 60 ? 'Good progress!' : 
                       'Keep going!'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Task Stats */}
              <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Task Overview</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-700">Total Tasks</span>
                    <span className="font-semibold text-gray-900">{dashboardData?.task_stats?.total || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-700">Completed</span>
                    <span className="font-semibold text-green-600">{dashboardData?.task_stats?.completed || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-700">Pending</span>
                    <span className="font-semibold text-orange-600">{dashboardData?.task_stats?.pending || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-700">Completion Rate</span>
                    <span className="font-semibold text-gray-900">{Math.round(dashboardData?.task_stats?.completion_rate || 0)}%</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'productivity' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Productivity Analysis</h3>
              
              {/* Productivity Patterns */}
              {productivityPatterns && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-medium text-gray-900">Peak Hours</h4>
                    <p className="text-sm text-gray-600 mt-1 capitalize">{productivityPatterns.best_time || 'Morning'}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-medium text-gray-900">Best Day</h4>
                    <p className="text-sm text-gray-600 mt-1">{productivityPatterns.best_day || 'Monday'}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-medium text-gray-900">Focus Blocks</h4>
                    <p className="text-sm text-gray-600 mt-1">{productivityPatterns.focus_blocks?.length || 0} scheduled</p>
                  </div>
                </div>
              )}

              {/* Focus Time Chart */}
              {dashboardData?.focus_time && dashboardData.focus_time.length > 0 && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-4">Focus Time (Last 7 Days)</h4>
                  <div className="flex items-end space-x-2 h-32">
                    {dashboardData.focus_time.slice(-7).map((day, index) => (
                      <div key={index} className="flex-1 flex flex-col items-center">
                        <div 
                          className="bg-blue-500 rounded-t w-full"
                          style={{ height: `${Math.max(10, (day.minutes / 480) * 100)}%` }}
                        ></div>
                        <span className="text-xs text-gray-600 mt-1">{day.date.split('-')[2]}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'learning' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Learning Progress</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900">Active Goals</h4>
                  <div className="mt-2 space-y-2">
                    {dashboardData?.goals?.slice(0, 3).map((goal, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <span className="text-sm text-gray-700">{goal}</span>
                      </div>
                    ))}
                    {(!dashboardData?.goals || dashboardData.goals.length === 0) && (
                      <p className="text-sm text-gray-500">No active goals</p>
                    )}
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900">Current Habits</h4>
                  <div className="mt-2 space-y-2">
                    {dashboardData?.habits?.slice(0, 3).map((habit, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="text-sm text-gray-700">{habit}</span>
                      </div>
                    ))}
                    {(!dashboardData?.habits || dashboardData.habits.length === 0) && (
                      <p className="text-sm text-gray-500">No active habits</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'habits' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Habit Tracking</h3>
              
              {/* Weekly Review */}
              {weeklyReview && (
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-lg">
                  <h4 className="font-semibold text-gray-900 mb-4">Weekly Summary</h4>
                  <p className="text-gray-700 mb-4">{weeklyReview.summary}</p>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">{weeklyReview.completed_tasks}</div>
                      <div className="text-sm text-gray-600">Completed</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">{weeklyReview.missed_tasks}</div>
                      <div className="text-sm text-gray-600">Missed</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{weeklyReview.streak}</div>
                      <div className="text-sm text-gray-600">Day Streak</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{weeklyReview.total_tasks}</div>
                      <div className="text-sm text-gray-600">Total</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Trends Chart */}
              {trendsData && trendsData.length > 0 && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-4">Productivity Trends (Last 30 Days)</h4>
                  <div className="flex items-end space-x-1 h-32">
                    {trendsData.slice(-30).map((day, index) => (
                      <div key={index} className="flex-1 flex flex-col items-center">
                        <div 
                          className="bg-green-500 rounded-t w-full"
                          style={{ height: `${Math.max(2, day.score)}%` }}
                        ></div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 