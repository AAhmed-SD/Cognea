const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = null;
  }

  setToken(token) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  getToken() {
    if (!this.token && typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
    return this.token;
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: this.getHeaders(),
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (response.status === 401) {
        this.clearToken();
        throw new Error('Unauthorized');
      }
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentication endpoints
  async signup(userData) {
    return this.request('/auth/signup', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async login(credentials) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  // AI Planning endpoints
  async planDay(planData) {
    return this.request('/plan-day', {
      method: 'POST',
      body: JSON.stringify(planData),
    });
  }

  async getPlan(planId) {
    return this.request(`/plan/${planId}`);
  }

  async generateFlashcards(flashcardData) {
    return this.request('/generate-flashcards', {
      method: 'POST',
      body: JSON.stringify(flashcardData),
    });
  }

  async completeReview(reviewData) {
    return this.request('/complete-review', {
      method: 'POST',
      body: JSON.stringify(reviewData),
    });
  }

  async trackGoal(goalData) {
    return this.request('/goals/track', {
      method: 'POST',
      body: JSON.stringify(goalData),
    });
  }

  async suggestHabits(habitData) {
    return this.request('/habits/suggest', {
      method: 'POST',
      body: JSON.stringify(habitData),
    });
  }

  async analyzeProductivity(analysisData) {
    return this.request('/productivity/analyze', {
      method: 'POST',
      body: JSON.stringify(analysisData),
    });
  }

  async optimizeSchedule(scheduleData) {
    return this.request('/schedule/optimize', {
      method: 'POST',
      body: JSON.stringify(scheduleData),
    });
  }

  async getWeeklySummary() {
    return this.request('/insights/weekly-summary');
  }

  async getLatestInsights() {
    return this.request('/insights/latest');
  }

  async generateInsights(insightData) {
    return this.request('/insights', {
      method: 'POST',
      body: JSON.stringify(insightData),
    });
  }

  // Notion integration endpoints
  async getNotionAuthUrl() {
    return this.request('/notion/auth/url');
  }

  async handleNotionCallback(callbackData) {
    return this.request('/notion/auth/callback', {
      method: 'POST',
      body: JSON.stringify(callbackData),
    });
  }

  async getNotionDatabases() {
    return this.request('/notion/databases');
  }

  async syncNotionDatabase(databaseData) {
    return this.request('/notion/sync/database', {
      method: 'POST',
      body: JSON.stringify(databaseData),
    });
  }

  async createNotionTask(taskData, databaseId) {
    return this.request(`/notion/tasks/create?database_id=${databaseId}`, {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }

  async getNotionStatus() {
    return this.request('/notion/status');
  }

  async disconnectNotion() {
    return this.request('/notion/disconnect', {
      method: 'DELETE',
    });
  }

  // Calendar endpoints
  async getCalendarEvents(dateRange) {
    return this.request(`/calendar/events?start=${dateRange.start}&end=${dateRange.end}`);
  }

  async createCalendarEvent(eventData) {
    return this.request('/calendar/events', {
      method: 'POST',
      body: JSON.stringify(eventData),
    });
  }

  async updateCalendarEvent(eventId, eventData) {
    return this.request(`/calendar/events/${eventId}`, {
      method: 'PUT',
      body: JSON.stringify(eventData),
    });
  }

  async deleteCalendarEvent(eventId) {
    return this.request(`/calendar/events/${eventId}`, {
      method: 'DELETE',
    });
  }

  // Habits endpoints
  async getHabits() {
    return this.request('/habits');
  }

  async createHabit(habitData) {
    return this.request('/habits', {
      method: 'POST',
      body: JSON.stringify(habitData),
    });
  }

  async updateHabit(habitId, habitData) {
    return this.request(`/habits/${habitId}`, {
      method: 'PUT',
      body: JSON.stringify(habitData),
    });
  }

  async deleteHabit(habitId) {
    return this.request(`/habits/${habitId}`, {
      method: 'DELETE',
    });
  }

  async trackHabit(habitId, trackingData) {
    return this.request(`/habits/${habitId}/track`, {
      method: 'POST',
      body: JSON.stringify(trackingData),
    });
  }

  // Analytics endpoints
  async getAnalytics(dateRange) {
    return this.request(`/analytics?start=${dateRange.start}&end=${dateRange.end}`);
  }

  async getProductivityMetrics() {
    return this.request('/analytics/productivity');
  }

  async getLearningProgress() {
    return this.request('/analytics/learning');
  }

  async getHabitStreaks() {
    return this.request('/analytics/habits');
  }
}

// Create a singleton instance
const apiService = new ApiService();

export default apiService; 