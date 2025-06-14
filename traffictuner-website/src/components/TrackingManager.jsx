import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../utils/api';

const TrackingManager = () => {
  const { user } = useAuth();
  const [trackingConfigs, setTrackingConfigs] = useState([]);
  const [platforms, setPlatforms] = useState({});
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [selectedDomain, setSelectedDomain] = useState('');
  const [showCodeModal, setShowCodeModal] = useState(false);
  const [generatedCode, setGeneratedCode] = useState('');

  // Form state
  const [formData, setFormData] = useState({
    platform: '',
    tracking_id: '',
    name: '',
    domain_id: '',
    is_active: true
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load tracking platforms info
      const platformsResponse = await apiClient.get('/api/tracking/platforms');
      setPlatforms(platformsResponse.platforms);
      
      // Load user's tracking configs
      const configsResponse = await apiClient.get('/api/tracking');
      setTrackingConfigs(configsResponse.tracking_configs);
      
      // Load user's domains
      const domainsResponse = await apiClient.get('/api/domains');
      setDomains(domainsResponse.domains);
      
    } catch (error) {
      console.error('Error loading tracking data:', error);
      alert('Failed to load tracking data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (editingConfig) {
        // Update existing config
        await apiClient.put(`/api/tracking/${editingConfig.config_id}`, formData);
        alert('Tracking configuration updated successfully!');
      } else {
        // Create new config
        await apiClient.post('/api/tracking', formData);
        alert('Tracking configuration created successfully!');
      }
      
      // Reset form and reload data
      resetForm();
      loadData();
      
    } catch (error) {
      console.error('Error saving tracking config:', error);
      alert(`Failed to save tracking configuration: ${error.message}`);
    }
  };

  const handleEdit = (config) => {
    setEditingConfig(config);
    setFormData({
      platform: config.platform,
      tracking_id: config.tracking_id,
      name: config.name,
      domain_id: config.domain_id || '',
      is_active: config.is_active
    });
    setShowAddModal(true);
  };

  const handleDelete = async (configId) => {
    if (!confirm('Are you sure you want to delete this tracking configuration?')) {
      return;
    }
    
    try {
      await apiClient.delete(`/api/tracking/${configId}`);
      alert('Tracking configuration deleted successfully!');
      loadData();
    } catch (error) {
      console.error('Error deleting tracking config:', error);
      alert(`Failed to delete tracking configuration: ${error.message}`);
    }
  };

  const handleToggleActive = async (configId, isActive) => {
    try {
      await apiClient.put(`/api/tracking/${configId}`, { is_active: !isActive });
      loadData();
    } catch (error) {
      console.error('Error toggling tracking config:', error);
      alert(`Failed to update tracking configuration: ${error.message}`);
    }
  };

  const handleGenerateCode = async (configId) => {
    try {
      const response = await apiClient.get(`/api/tracking/${configId}/code`);
      setGeneratedCode(response.tracking_code);
      setShowCodeModal(true);
    } catch (error) {
      console.error('Error generating tracking code:', error);
      alert(`Failed to generate tracking code: ${error.message}`);
    }
  };

  const handleGenerateDomainCode = async (domainId) => {
    try {
      const response = await apiClient.get(`/api/tracking/domain/${domainId}/code`);
      setGeneratedCode(response.combined_code);
      setShowCodeModal(true);
    } catch (error) {
      console.error('Error generating domain tracking code:', error);
      alert(`Failed to generate domain tracking code: ${error.message}`);
    }
  };

  const resetForm = () => {
    setFormData({
      platform: '',
      tracking_id: '',
      name: '',
      domain_id: '',
      is_active: true
    });
    setEditingConfig(null);
    setShowAddModal(false);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Code copied to clipboard!');
    }).catch(() => {
      alert('Failed to copy code to clipboard');
    });
  };

  const getPlatformIcon = (platform) => {
    const icons = {
      meta_pixel: '📘',
      ga4: '📊',
      gtm: '🏷️',
      clarity: '🔍'
    };
    return icons[platform] || '📈';
  };

  const getPlatformColor = (platform) => {
    const colors = {
      meta_pixel: 'from-blue-500 to-blue-600',
      ga4: 'from-orange-500 to-orange-600',
      gtm: 'from-green-500 to-green-600',
      clarity: 'from-purple-500 to-purple-600'
    };
    return colors[platform] || 'from-gray-500 to-gray-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400 mx-auto mb-4"></div>
              <p className="text-gray-300">Loading tracking configurations...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">
            Tracking Manager
            <span className="ml-3 text-lg font-normal text-gray-400">
              📈 No-Code Analytics Setup
            </span>
          </h1>
          <p className="text-gray-300 mb-6">
            Add and manage your tracking codes for Meta Pixel, Google Analytics 4, Google Tag Manager, and Microsoft Clarity.
            Generate ready-to-use code snippets without any technical knowledge required.
          </p>
          
          <div className="flex flex-wrap gap-4">
            <button
              onClick={() => setShowAddModal(true)}
              className="bg-gradient-to-r from-cyan-500 to-lime-500 text-black px-6 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity"
            >
              ➕ Add Tracking Code
            </button>
            
            {domains.length > 0 && (
              <div className="flex items-center gap-2">
                <select
                  value={selectedDomain}
                  onChange={(e) => setSelectedDomain(e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white"
                >
                  <option value="">Select domain for code generation</option>
                  {domains.map(domain => (
                    <option key={domain.domain_id} value={domain.domain_id}>
                      {domain.url}
                    </option>
                  ))}
                </select>
                
                {selectedDomain && (
                  <button
                    onClick={() => handleGenerateDomainCode(selectedDomain)}
                    className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity"
                  >
                    🔗 Generate All Codes
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Platform Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {Object.entries(platforms).map(([key, platform]) => (
            <div key={key} className="bg-gray-800/50 p-6 rounded-xl border border-gray-700">
              <div className="flex items-center mb-3">
                <span className="text-2xl mr-3">{getPlatformIcon(key)}</span>
                <h3 className="font-bold text-lg">{platform.name}</h3>
              </div>
              <p className="text-gray-300 text-sm mb-4">{platform.description}</p>
              <div className="space-y-2">
                <p className="text-xs text-gray-400">
                  <strong>ID Format:</strong> {platform.id_format}
                </p>
                <a
                  href={platform.setup_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block text-cyan-400 hover:text-cyan-300 text-sm"
                >
                  🔗 Setup Guide
                </a>
              </div>
            </div>
          ))}
        </div>

        {/* Tracking Configurations */}
        <div className="bg-gray-800/50 rounded-xl border border-gray-700 overflow-hidden">
          <div className="p-6 border-b border-gray-700">
            <h2 className="text-xl font-bold">Your Tracking Configurations</h2>
            <p className="text-gray-300 text-sm mt-1">
              {trackingConfigs.length} tracking code{trackingConfigs.length !== 1 ? 's' : ''} configured
            </p>
          </div>
          
          {trackingConfigs.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">📊</div>
              <h3 className="text-xl font-bold mb-2">No Tracking Codes Yet</h3>
              <p className="text-gray-300 mb-6">
                Add your first tracking code to start monitoring your website performance.
              </p>
              <button
                onClick={() => setShowAddModal(true)}
                className="bg-gradient-to-r from-cyan-500 to-lime-500 text-black px-6 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity"
              >
                Add Your First Tracking Code
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-700">
              {trackingConfigs.map(config => (
                <div key={config.config_id} className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${getPlatformColor(config.platform)} flex items-center justify-center text-white text-xl`}>
                        {getPlatformIcon(config.platform)}
                      </div>
                      
                      <div>
                        <h3 className="font-bold text-lg">{config.name}</h3>
                        <p className="text-gray-300">
                          {platforms[config.platform]?.name} • ID: {config.tracking_id}
                        </p>
                        {config.domain_id && (
                          <p className="text-gray-400 text-sm">
                            Domain: {domains.find(d => d.domain_id === config.domain_id)?.url || 'Unknown'}
                          </p>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleToggleActive(config.config_id, config.is_active)}
                        className={`px-3 py-1 rounded-full text-sm font-medium ${
                          config.is_active 
                            ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                            : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                        }`}
                      >
                        {config.is_active ? '✅ Active' : '⏸️ Inactive'}
                      </button>
                      
                      <button
                        onClick={() => handleGenerateCode(config.config_id)}
                        className="bg-blue-500/20 text-blue-400 border border-blue-500/30 px-3 py-1 rounded-lg text-sm hover:bg-blue-500/30 transition-colors"
                      >
                        📋 Get Code
                      </button>
                      
                      <button
                        onClick={() => handleEdit(config)}
                        className="bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 px-3 py-1 rounded-lg text-sm hover:bg-yellow-500/30 transition-colors"
                      >
                        ✏️ Edit
                      </button>
                      
                      <button
                        onClick={() => handleDelete(config.config_id)}
                        className="bg-red-500/20 text-red-400 border border-red-500/30 px-3 py-1 rounded-lg text-sm hover:bg-red-500/30 transition-colors"
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Add/Edit Modal */}
        {showAddModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-xl border border-gray-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-gray-700">
                <h2 className="text-xl font-bold">
                  {editingConfig ? 'Edit Tracking Configuration' : 'Add New Tracking Code'}
                </h2>
              </div>
              
              <form onSubmit={handleSubmit} className="p-6 space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Platform</label>
                  <select
                    value={formData.platform}
                    onChange={(e) => setFormData({...formData, platform: e.target.value})}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white"
                    required
                    disabled={editingConfig} // Don't allow changing platform when editing
                  >
                    <option value="">Select a platform</option>
                    {Object.entries(platforms).map(([key, platform]) => (
                      <option key={key} value={key}>
                        {getPlatformIcon(key)} {platform.name}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Configuration Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white"
                    placeholder="e.g., Main Website Pixel"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Tracking ID
                    {formData.platform && platforms[formData.platform] && (
                      <span className="text-gray-400 text-sm ml-2">
                        ({platforms[formData.platform].id_format})
                      </span>
                    )}
                  </label>
                  <input
                    type="text"
                    value={formData.tracking_id}
                    onChange={(e) => setFormData({...formData, tracking_id: e.target.value})}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white"
                    placeholder={formData.platform && platforms[formData.platform] ? platforms[formData.platform].id_format : "Enter your tracking ID"}
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Domain (Optional)</label>
                  <select
                    value={formData.domain_id}
                    onChange={(e) => setFormData({...formData, domain_id: e.target.value})}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white"
                  >
                    <option value="">Apply to all domains</option>
                    {domains.map(domain => (
                      <option key={domain.domain_id} value={domain.domain_id}>
                        {domain.url}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                    className="mr-3"
                  />
                  <label htmlFor="is_active" className="text-sm">
                    Active (tracking code will be included in generated code)
                  </label>
                </div>
                
                <div className="flex justify-end space-x-4 pt-4">
                  <button
                    type="button"
                    onClick={resetForm}
                    className="px-6 py-3 border border-gray-600 rounded-lg text-gray-300 hover:bg-gray-700 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="bg-gradient-to-r from-cyan-500 to-lime-500 text-black px-6 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity"
                  >
                    {editingConfig ? 'Update Configuration' : 'Add Tracking Code'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Code Generation Modal */}
        {showCodeModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-xl border border-gray-700 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-gray-700">
                <h2 className="text-xl font-bold">Generated Tracking Code</h2>
                <p className="text-gray-300 text-sm mt-1">
                  Copy this code and paste it into your website's &lt;head&gt; section
                </p>
              </div>
              
              <div className="p-6">
                <div className="bg-gray-900 rounded-lg p-4 mb-4">
                  <pre className="text-sm text-gray-300 whitespace-pre-wrap overflow-x-auto">
                    {generatedCode}
                  </pre>
                </div>
                
                <div className="flex justify-end space-x-4">
                  <button
                    onClick={() => copyToClipboard(generatedCode)}
                    className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-6 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity"
                  >
                    📋 Copy to Clipboard
                  </button>
                  <button
                    onClick={() => setShowCodeModal(false)}
                    className="px-6 py-3 border border-gray-600 rounded-lg text-gray-300 hover:bg-gray-700 transition-colors"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TrackingManager;

