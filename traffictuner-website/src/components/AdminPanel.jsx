import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../utils/api';

const AdminPanel = () => {
  const { user, isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboardData, setDashboardData] = useState(null);
  const [llmConfigs, setLlmConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddConfig, setShowAddConfig] = useState(false);

  useEffect(() => {
    if (isAdmin) {
      loadDashboardData();
      loadLLMConfigs();
    }
  }, [isAdmin]);

  const loadDashboardData = async () => {
    try {
      const response = await apiClient.getAdminDashboard();
      setDashboardData(response);
    } catch (error) {
      setError('Failed to load dashboard data');
      console.error('Error loading dashboard:', error);
    }
  };

  const loadLLMConfigs = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getLLMConfigs();
      setLlmConfigs(response.configs);
    } catch (error) {
      setError('Failed to load LLM configurations');
      console.error('Error loading LLM configs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInitDefaults = async () => {
    try {
      setError(null);
      await apiClient.initDefaultConfigs();
      loadLLMConfigs();
    } catch (error) {
      setError(error.message);
    }
  };

  const handleTestConfig = async (configId) => {
    try {
      setError(null);
      const response = await apiClient.testLLMConfig(configId);
      alert(`Test successful: ${response.response}`);
    } catch (error) {
      alert(`Test failed: ${error.message}`);
    }
  };

  const handleDeleteConfig = async (configId) => {
    if (!confirm('Are you sure you want to delete this configuration?')) return;
    
    try {
      setError(null);
      await apiClient.deleteLLMConfig(configId);
      loadLLMConfigs();
    } catch (error) {
      setError(error.message);
    }
  };

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-center">
          <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
          <p>You don't have permission to access the admin panel.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-lime-400 bg-clip-text text-transparent">
              Admin Panel
            </h1>
            <div className="flex items-center space-x-4">
              <span className="text-gray-300">{user?.name} (Admin)</span>
              <a
                href="/dashboard"
                className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors"
              >
                Back to Dashboard
              </a>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="flex space-x-1 mb-8">
          {[
            { id: 'dashboard', label: 'Dashboard' },
            { id: 'llm-configs', label: 'LLM Configurations' },
            { id: 'users', label: 'Users' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-cyan-500 text-black'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && dashboardData && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold">System Overview</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                <h3 className="text-lg font-semibold text-gray-300 mb-2">Total Users</h3>
                <p className="text-3xl font-bold text-cyan-400">{dashboardData.users?.total || 0}</p>
                <p className="text-sm text-gray-400">+{dashboardData.users?.new_today || 0} today</p>
              </div>
              
              <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                <h3 className="text-lg font-semibold text-gray-300 mb-2">Total Domains</h3>
                <p className="text-3xl font-bold text-lime-400">{dashboardData.domains?.total || 0}</p>
                <p className="text-sm text-gray-400">{dashboardData.domains?.active || 0} active</p>
              </div>
              
              <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                <h3 className="text-lg font-semibold text-gray-300 mb-2">Analyses</h3>
                <p className="text-3xl font-bold text-yellow-400">{dashboardData.analyses?.total || 0}</p>
                <p className="text-sm text-gray-400">{dashboardData.analyses?.pending || 0} pending</p>
              </div>
              
              <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                <h3 className="text-lg font-semibold text-gray-300 mb-2">LLM Cost</h3>
                <p className="text-3xl font-bold text-purple-400">
                  ${dashboardData.llm_usage?.total_cost?.toFixed(2) || '0.00'}
                </p>
                <p className="text-sm text-gray-400">{dashboardData.llm_usage?.total_requests || 0} requests</p>
              </div>
            </div>
          </div>
        )}

        {/* LLM Configurations Tab */}
        {activeTab === 'llm-configs' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold">LLM Configurations</h2>
              <div className="space-x-4">
                <button
                  onClick={handleInitDefaults}
                  className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors"
                >
                  Initialize Defaults
                </button>
                <button
                  onClick={() => setShowAddConfig(true)}
                  className="bg-gradient-to-r from-cyan-500 to-lime-500 text-black px-4 py-2 rounded-lg font-medium hover:opacity-90 transition-opacity"
                >
                  Add Configuration
                </button>
              </div>
            </div>

            {/* Add Config Form */}
            {showAddConfig && (
              <AddLLMConfigForm
                onSuccess={() => {
                  setShowAddConfig(false);
                  loadLLMConfigs();
                }}
                onCancel={() => setShowAddConfig(false)}
                onError={setError}
              />
            )}

            {/* Configurations List */}
            {loading ? (
              <div className="text-center py-8">Loading configurations...</div>
            ) : llmConfigs.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-400 mb-4">No LLM configurations found</div>
                <button
                  onClick={handleInitDefaults}
                  className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  Initialize Default Configurations
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {llmConfigs.map((config) => (
                  <div key={config.id} className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-4 mb-2">
                          <h3 className="text-lg font-semibold">{config.name}</h3>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            config.is_active ? 'bg-green-900 text-green-300' : 'bg-gray-700 text-gray-400'
                          }`}>
                            {config.is_active ? 'Active' : 'Inactive'}
                          </span>
                          <span className="bg-blue-900 text-blue-300 px-2 py-1 rounded-full text-xs font-medium">
                            Priority: {config.priority}
                          </span>
                        </div>
                        <p className="text-gray-400 text-sm mb-2">{config.description}</p>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-400">Provider:</span>
                            <span className="ml-2 text-white">{config.provider}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Model:</span>
                            <span className="ml-2 text-white">{config.model_name}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Requests:</span>
                            <span className="ml-2 text-white">{config.total_requests}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Cost:</span>
                            <span className="ml-2 text-white">${config.total_cost?.toFixed(2) || '0.00'}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleTestConfig(config.config_id)}
                          disabled={!config.is_active}
                          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-3 py-1 rounded text-sm transition-colors"
                        >
                          Test
                        </button>
                        <button
                          onClick={() => handleDeleteConfig(config.config_id)}
                          className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold">User Management</h2>
            <div className="text-gray-400">User management features coming soon...</div>
          </div>
        )}
      </div>
    </div>
  );
};

// Add LLM Config Form Component
const AddLLMConfigForm = ({ onSuccess, onCancel, onError }) => {
  const [formData, setFormData] = useState({
    provider: 'openai',
    name: '',
    description: '',
    model_name: '',
    api_key: '',
    api_endpoint: '',
    priority: 1,
    cost_per_1k_tokens: 0.0,
    is_active: true,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await apiClient.createLLMConfig(formData);
      onSuccess();
    } catch (error) {
      onError(error.message);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  return (
    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
      <h3 className="text-lg font-bold mb-4">Add LLM Configuration</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Provider</label>
            <select
              name="provider"
              value={formData.provider}
              onChange={handleChange}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
              required
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="google">Google</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Name</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
              required
            />
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows={2}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Model Name</label>
            <input
              type="text"
              name="model_name"
              value={formData.model_name}
              onChange={handleChange}
              placeholder="e.g., gpt-4, claude-3-sonnet-20240229"
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">API Endpoint</label>
            <input
              type="url"
              name="api_endpoint"
              value={formData.api_endpoint}
              onChange={handleChange}
              placeholder="e.g., https://api.openai.com/v1"
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">API Key</label>
          <input
            type="password"
            name="api_key"
            value={formData.api_key}
            onChange={handleChange}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
            required
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Priority</label>
            <input
              type="number"
              name="priority"
              value={formData.priority}
              onChange={handleChange}
              min="1"
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Cost per 1K Tokens</label>
            <input
              type="number"
              name="cost_per_1k_tokens"
              value={formData.cost_per_1k_tokens}
              onChange={handleChange}
              step="0.001"
              min="0"
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
            />
          </div>
          <div className="flex items-center">
            <label className="flex items-center space-x-2 text-sm font-medium text-gray-300">
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
                className="rounded"
              />
              <span>Active</span>
            </label>
          </div>
        </div>

        <div className="flex space-x-4">
          <button
            type="submit"
            className="bg-cyan-500 text-black px-6 py-2 rounded-lg font-medium hover:bg-cyan-400 transition-colors"
          >
            Add Configuration
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-500 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default AdminPanel;

