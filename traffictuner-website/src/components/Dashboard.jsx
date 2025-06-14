import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext.jsx';
import apiClient from '../utils/api';
import TrackingManager from './TrackingManager.jsx';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('domains');
  const [domains, setDomains] = useState([]);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newDomainUrl, setNewDomainUrl] = useState('');
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    loadDomains();
  }, []);

  const loadDomains = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getDomains();
      setDomains(response.domains);
    } catch (error) {
      setError('Failed to load domains');
      console.error('Error loading domains:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddDomain = async (e) => {
    e.preventDefault();
    if (!newDomainUrl.trim()) return;

    try {
      setError(null);
      await apiClient.addDomain({ url: newDomainUrl });
      setNewDomainUrl('');
      setShowAddDomain(false);
      loadDomains();
    } catch (error) {
      setError(error.message);
    }
  };

  const handleAnalyzeDomain = async (domainId) => {
    try {
      setAnalyzing(true);
      setError(null);
      await apiClient.analyzeDomain(domainId);
      // Refresh domains to show updated status
      loadDomains();
    } catch (error) {
      setError(error.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-500';
      case 'analyzing': return 'text-blue-500';
      case 'error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-lime-400 bg-clip-text text-transparent">
                TrafficTuner Dashboard
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-300">Welcome, {user?.name}</span>
              <span className="bg-cyan-500 text-black px-3 py-1 rounded-full text-sm font-medium">
                {user?.credits} Credits
              </span>
              <button
                onClick={logout}
                className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-300 mb-2">Total Domains</h3>
            <p className="text-3xl font-bold text-cyan-400">{domains.length}</p>
          </div>
          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-300 mb-2">Available Credits</h3>
            <p className="text-3xl font-bold text-lime-400">{user?.credits || 0}</p>
          </div>
          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-300 mb-2">Active Analyses</h3>
            <p className="text-3xl font-bold text-yellow-400">
              {domains.filter(d => d.status === 'analyzing').length}
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 mb-6">
          <div className="flex border-b border-gray-700">
            <button
              onClick={() => setActiveTab('domains')}
              className={`px-6 py-4 font-medium transition-colors ${
                activeTab === 'domains'
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              🌐 Domains
            </button>
            <button
              onClick={() => setActiveTab('tracking')}
              className={`px-6 py-4 font-medium transition-colors ${
                activeTab === 'tracking'
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              📊 Tracking & Analytics
            </button>
            <button
              onClick={() => setActiveTab('reports')}
              className={`px-6 py-4 font-medium transition-colors ${
                activeTab === 'reports'
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              📈 Reports
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'domains' && (
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">Your Domains</h2>
              <button
                onClick={() => setShowAddDomain(true)}
                className="bg-gradient-to-r from-cyan-500 to-lime-500 text-black px-4 py-2 rounded-lg font-medium hover:opacity-90 transition-opacity"
              >
                Add Domain
              </button>
            </div>

          {/* Add Domain Form */}
          {showAddDomain && (
            <div className="bg-gray-700 p-4 rounded-lg mb-6">
              <form onSubmit={handleAddDomain} className="flex gap-4">
                <input
                  type="url"
                  value={newDomainUrl}
                  onChange={(e) => setNewDomainUrl(e.target.value)}
                  placeholder="Enter domain URL (e.g., https://example.com)"
                  className="flex-1 bg-gray-600 border border-gray-500 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-cyan-400"
                  required
                />
                <button
                  type="submit"
                  className="bg-cyan-500 text-black px-6 py-2 rounded-lg font-medium hover:bg-cyan-400 transition-colors"
                >
                  Add
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddDomain(false)}
                  className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-500 transition-colors"
                >
                  Cancel
                </button>
              </form>
            </div>
          )}

          {/* Domains List */}
          {domains.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">No domains added yet</div>
              <button
                onClick={() => setShowAddDomain(true)}
                className="bg-gradient-to-r from-cyan-500 to-lime-500 text-black px-6 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity"
              >
                Add Your First Domain
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {domains.map((domain) => (
                <div key={domain.domain_id} className="bg-gray-700 p-4 rounded-lg border border-gray-600">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-white mb-1">
                        {domain.name || domain.url}
                      </h3>
                      <p className="text-gray-400 text-sm mb-2">{domain.url}</p>
                      <div className="flex items-center space-x-4 text-sm">
                        <span className={`font-medium ${getStatusColor(domain.status)}`}>
                          Status: {domain.status}
                        </span>
                        {domain.seo_score && (
                          <span className="text-cyan-400">
                            SEO: {domain.seo_score.toFixed(1)}
                          </span>
                        )}
                        {domain.aeo_score && (
                          <span className="text-lime-400">
                            AEO: {domain.aeo_score.toFixed(1)}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      {domain.status === 'active' && (
                        <button
                          onClick={() => handleAnalyzeDomain(domain.domain_id)}
                          disabled={analyzing || user?.credits <= 0}
                          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                        >
                          {analyzing ? 'Analyzing...' : 'Analyze'}
                        </button>
                      )}
                      {domain.latest_report && (
                        <button
                          onClick={() => window.open(`/report/${domain.latest_report.report_id}`, '_blank')}
                          className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                        >
                          View Report
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        )}

        {/* Tracking Tab */}
        {activeTab === 'tracking' && (
          <TrackingManager user={user} />
        )}

        {/* Reports Tab */}
        {activeTab === 'reports' && (
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <h2 className="text-xl font-bold mb-6">Analysis Reports</h2>
            <div className="text-gray-400 text-center py-8">
              <div className="text-4xl mb-4">📊</div>
              <p>Your analysis reports will appear here</p>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h3 className="text-lg font-bold mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button className="w-full bg-gradient-to-r from-cyan-500 to-lime-500 text-black py-3 rounded-lg font-medium hover:opacity-90 transition-opacity">
                Generate LLMs.txt File
              </button>
              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-medium transition-colors">
                View All Reports
              </button>
              <button className="w-full bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg font-medium transition-colors">
                Upgrade Plan
              </button>
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h3 className="text-lg font-bold mb-4">Recent Activity</h3>
            <div className="text-gray-400 text-sm">
              No recent activity to display
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;

