// API configuration and utilities
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5002/api';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = localStorage.getItem('access_token');
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  }

  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
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
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP error! status: ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Auth endpoints
  async register(userData) {
    return this.request('/auth/register', {
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

  async updateProfile(profileData) {
    return this.request('/auth/profile', {
      method: 'PATCH',
      body: JSON.stringify(profileData),
    });
  }

  // Domain endpoints
  async getDomains() {
    return this.request('/domains');
  }

  async addDomain(domainData) {
    return this.request('/domains', {
      method: 'POST',
      body: JSON.stringify(domainData),
    });
  }

  async getDomain(domainId) {
    return this.request(`/domains/${domainId}`);
  }

  async analyzeDomain(domainId, analysisType = 'full') {
    return this.request(`/domains/${domainId}/analyze`, {
      method: 'POST',
      body: JSON.stringify({ analysis_type: analysisType }),
    });
  }

  // Analysis endpoints
  async getReport(reportId) {
    return this.request(`/analysis/reports/${reportId}`);
  }

  async generateLLMsFile(domainId) {
    return this.request('/analysis/llms-generator', {
      method: 'POST',
      body: JSON.stringify({ domain_id: domainId }),
    });
  }

  async getRecommendations() {
    return this.request('/analysis/recommendations');
  }

  // Billing endpoints
  async getPricingPlans() {
    return this.request('/billing/plans');
  }

  async getSubscription() {
    return this.request('/billing/subscription');
  }

  async createCheckoutSession(plan, successUrl, cancelUrl) {
    return this.request('/billing/create-checkout-session', {
      method: 'POST',
      body: JSON.stringify({
        plan,
        success_url: successUrl,
        cancel_url: cancelUrl,
      }),
    });
  }

  async createPortalSession(returnUrl) {
    return this.request('/billing/create-portal-session', {
      method: 'POST',
      body: JSON.stringify({ return_url: returnUrl }),
    });
  }

  async getUsageStats() {
    return this.request('/billing/usage');
  }

  // Admin endpoints
  async getAdminDashboard() {
    return this.request('/admin/dashboard');
  }

  async getLLMConfigs() {
    return this.request('/admin/llm-configs');
  }

  async createLLMConfig(configData) {
    return this.request('/admin/llm-configs', {
      method: 'POST',
      body: JSON.stringify(configData),
    });
  }

  async updateLLMConfig(configId, configData) {
    return this.request(`/admin/llm-configs/${configId}`, {
      method: 'PATCH',
      body: JSON.stringify(configData),
    });
  }

  async deleteLLMConfig(configId) {
    return this.request(`/admin/llm-configs/${configId}`, {
      method: 'DELETE',
    });
  }

  async testLLMConfig(configId) {
    return this.request(`/admin/llm-configs/${configId}/test`, {
      method: 'POST',
    });
  }

  async initDefaultConfigs() {
    return this.request('/admin/system/init-defaults', {
      method: 'POST',
    });
  }
}

// Create singleton instance
const apiClient = new ApiClient();

export default apiClient;

