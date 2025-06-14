import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext.jsx';
import Dashboard from './components/Dashboard.jsx';
import AdminPanel from './components/AdminPanel.jsx';
import apiClient from './utils/api';
import './App.css';

// Router component for handling different views
const AppRouter = () => {
  const { isAuthenticated, isAdmin } = useAuth();
  const [currentView, setCurrentView] = useState('landing');

  useEffect(() => {
    // Handle URL routing
    const path = window.location.pathname;
    if (path === '/dashboard' && isAuthenticated) {
      setCurrentView('dashboard');
    } else if (path === '/admin' && isAdmin) {
      setCurrentView('admin');
    } else {
      setCurrentView('landing');
    }
  }, [isAuthenticated, isAdmin]);

  // Update URL when view changes
  useEffect(() => {
    const newPath = currentView === 'landing' ? '/' : `/${currentView}`;
    if (window.location.pathname !== newPath) {
      window.history.pushState({}, '', newPath);
    }
  }, [currentView]);

  if (currentView === 'dashboard' && isAuthenticated) {
    return <Dashboard />;
  }

  if (currentView === 'admin' && isAdmin) {
    return <AdminPanel />;
  }

  return <LandingPage onNavigate={setCurrentView} />;
};

// Updated Landing Page Component
const LandingPage = ({ onNavigate }) => {
  const { isAuthenticated, isAdmin } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showSignupModal, setShowSignupModal] = useState(false);
  const [url, setUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    if (!isAuthenticated) {
      setShowSignupModal(true);
      return;
    }

    try {
      setIsAnalyzing(true);
      // Add domain and start analysis
      const domainResponse = await apiClient.addDomain({ url });
      await apiClient.analyzeDomain(domainResponse.domain.domain_id);
      
      // Navigate to dashboard
      onNavigate('dashboard');
    } catch (error) {
      alert(`Analysis failed: ${error.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-gray-900/95 backdrop-blur-sm border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <img src="/src/assets/traffictuner-logo.jpg" alt="TrafficTuner" className="h-8 w-auto mr-3" />
              <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-lime-400 bg-clip-text text-transparent">
                TrafficTuner
              </span>
            </div>
            <nav className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-gray-300 hover:text-white transition-colors">Features</a>
              <a href="#pricing" className="text-gray-300 hover:text-white transition-colors">Pricing</a>
              <a href="#blog" className="text-gray-300 hover:text-white transition-colors">Blog</a>
            </nav>
            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <>
                  <button
                    onClick={() => onNavigate('dashboard')}
                    className="text-gray-300 hover:text-white transition-colors"
                  >
                    Dashboard
                  </button>
                  {isAdmin && (
                    <button
                      onClick={() => onNavigate('admin')}
                      className="text-gray-300 hover:text-white transition-colors"
                    >
                      Admin
                    </button>
                  )}
                </>
              ) : (
                <>
                  <button
                    onClick={() => setShowLoginModal(true)}
                    className="text-gray-300 hover:text-white transition-colors"
                  >
                    Login
                  </button>
                  <button
                    onClick={() => setShowSignupModal(true)}
                    className="bg-gradient-to-r from-cyan-500 to-lime-500 text-black px-6 py-2 rounded-lg font-medium hover:opacity-90 transition-opacity"
                  >
                    Sign Up
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0">
          <div className="particle-field"></div>
        </div>
        <div className="relative max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-6xl font-bold mb-6">
            Get Found by{' '}
            <span className="bg-gradient-to-r from-cyan-400 to-lime-400 bg-clip-text text-transparent">
              Search Engines & AI
            </span>
          </h1>
          <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
            We'll show you exactly how to get more traffic—no matter how the web evolves.
          </p>
          
          <form onSubmit={handleAnalyze} className="max-w-2xl mx-auto mb-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Enter your website URL..."
                className="flex-1 bg-gray-800/50 border border-cyan-500/30 rounded-lg px-6 py-4 text-white placeholder-gray-400 focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                required
              />
              <button
                type="submit"
                disabled={isAnalyzing}
                className="bg-gradient-to-r from-cyan-500 to-lime-500 text-black px-8 py-4 rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isAnalyzing ? 'Analyzing...' : 'Analyze Free'}
              </button>
            </div>
          </form>
          
          <p className="text-gray-400 text-sm">
            No credit card needed. No tech skills required.
          </p>
        </div>
      </section>

      {/* Social Proof Section */}
      <section id="social-proof" className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">
            Trusted by{' '}
            <span className="bg-gradient-to-r from-cyan-400 to-lime-400 bg-clip-text text-transparent">
              Innovators
            </span>{' '}
            Ready for the{' '}
            <span className="bg-gradient-to-r from-lime-400 to-cyan-400 bg-clip-text text-transparent">
              Future of Search
            </span>
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                name: "Sarah Chen",
                role: "Tech Startup CEO",
                content: "TrafficTuner helped us prepare for the AI revolution in search. Our traffic increased 300%!",
                rating: 5
              },
              {
                name: "Marcus Rodriguez",
                role: "Marketing Director",
                content: "Finally, a tool that thinks beyond just Google. The AI optimization features are game-changing.",
                rating: 5
              },
              {
                name: "Emily Watson",
                role: "E-commerce Owner",
                content: "The LLMs.txt generator alone saved us weeks of work. This is the future of SEO.",
                rating: 5
              }
            ].map((testimonial, index) => (
              <div key={index} className="bg-gray-800/50 p-6 rounded-xl border border-gray-700">
                <div className="flex items-center mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <span key={i} className="text-yellow-400">★</span>
                  ))}
                </div>
                <p className="text-gray-300 mb-4">"{testimonial.content}"</p>
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-gradient-to-r from-cyan-500 to-lime-500 rounded-full flex items-center justify-center text-black font-bold mr-3">
                    {testimonial.name.charAt(0)}
                  </div>
                  <div>
                    <div className="font-semibold">{testimonial.name}</div>
                    <div className="text-gray-400 text-sm">{testimonial.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">
            Unlock Your Full Potential in{' '}
            <span className="bg-gradient-to-r from-cyan-400 to-lime-400 bg-clip-text text-transparent">
              3 Simple Steps
            </span>
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: "🔍",
                title: "Instant Analysis",
                description: "Enter your domain to instantly scan for both SEO and AEO opportunities.",
                color: "from-blue-500 to-cyan-500"
              },
              {
                icon: "✅",
                title: "Get Your Action Plan",
                description: "Receive a clear, step-by-step plan. We even generate a unique LLMs.txt file for you.",
                color: "from-lime-500 to-green-500"
              },
              {
                icon: "📈",
                title: "Watch Your Traffic Grow",
                description: "Implement our jargon-free guidance and see real growth in traffic and authority.",
                color: "from-yellow-500 to-orange-500"
              }
            ].map((step, index) => (
              <div key={index} className="bg-gray-800/50 p-8 rounded-xl border border-gray-700 text-center">
                <div className={`w-16 h-16 mx-auto mb-6 rounded-full bg-gradient-to-r ${step.color} flex items-center justify-center text-2xl`}>
                  {step.icon}
                </div>
                <h3 className="text-xl font-bold mb-4">{step.title}</h3>
                <p className="text-gray-300">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-4">
            Tune Your Traffic for the{' '}
            <span className="bg-gradient-to-r from-cyan-400 to-lime-400 bg-clip-text text-transparent">
              AI Era
            </span>
          </h2>
          <p className="text-gray-300 text-center mb-12 max-w-3xl mx-auto">
            Discover powerful features designed to optimize your website not just for Google, 
            but for the rapidly evolving world of AI-driven search and answer engines.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: "⚡",
                title: "AI-Powered SEO Analysis",
                description: "Leverage cutting-edge AI to dissect your website's SEO performance, identifying critical areas for improvement beyond traditional metrics.",
                color: "cyan"
              },
              {
                icon: "📝",
                title: "LLMs.txt Generator",
                description: "Automatically create and optimize LLMs.txt files to guide Large Language Models, ensuring your content is accurately represented and prioritized by AI.",
                color: "lime"
              },
              {
                icon: "📊",
                title: "Comprehensive AEO Reports",
                description: "Receive detailed Answer Engine Optimization (AEO) reports, focusing on how your site can become the definitive answer for user queries on AI platforms.",
                color: "cyan"
              },
              {
                icon: "🔍",
                title: "Semantic Content Insights",
                description: "Understand how AI interprets your content's meaning and context. Get actionable advice to enhance semantic relevance and authority.",
                color: "lime"
              },
              {
                icon: "🎯",
                title: "Competitor AI Visibility",
                description: "Analyze how your competitors are positioned for AI search. Uncover their strategies and find opportunities to outperform them.",
                color: "cyan"
              },
              {
                icon: "🚀",
                title: "Future-Proof Strategy",
                description: "Stay ahead of the curve with strategies designed for the evolving landscape of search, ensuring long-term visibility and traffic growth.",
                color: "lime"
              }
            ].map((feature, index) => (
              <div key={index} className="bg-gray-800/50 p-6 rounded-xl border border-gray-700">
                <div className={`w-12 h-12 mb-4 rounded-lg bg-gradient-to-r ${
                  feature.color === 'cyan' ? 'from-cyan-500 to-blue-500' : 'from-lime-500 to-green-500'
                } flex items-center justify-center text-xl`}>
                  {feature.icon}
                </div>
                <h3 className={`text-lg font-bold mb-3 ${
                  feature.color === 'cyan' ? 'text-cyan-400' : 'text-lime-400'
                }`}>
                  {feature.title}
                </h3>
                <p className="text-gray-300 text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-4">
            Flexible Pricing for Every Ambition
          </h2>
          <p className="text-gray-300 text-center mb-12 max-w-3xl mx-auto">
            Choose the plan that best fits your needs and start optimizing for the future of search today. 
            No hidden fees, transparent value.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {[
              {
                name: "Starter Domain",
                price: "$29",
                period: "/year",
                description: "Perfect for individual sites and getting started with AI optimization.",
                features: [
                  "Full SEO + AEO Report",
                  "LLMs.txt Generator",
                  "Basic Competitor Analysis",
                  "Monthly Progress Tracking"
                ],
                buttonText: "Get Started Free",
                buttonClass: "bg-gradient-to-r from-cyan-500 to-blue-500 text-white",
                borderClass: "border-cyan-500/30"
              },
              {
                name: "Pro Business",
                price: "$79",
                period: "/year",
                description: "For businesses serious about dominating AI search and maximizing traffic.",
                features: [
                  "Everything in Starter, plus:",
                  "Advanced AEO Strategies",
                  "In-depth Competitor AI Visibility",
                  "Priority Support",
                  "Content Semantic Insights"
                ],
                buttonText: "Choose Pro",
                buttonClass: "bg-gradient-to-r from-lime-500 to-green-500 text-black",
                borderClass: "border-lime-500/50",
                popular: true
              },
              {
                name: "Agency Scale",
                price: "$199",
                period: "/year",
                description: "Comprehensive tools for agencies managing multiple client websites.",
                features: [
                  "Everything in Pro, plus:",
                  "Multi-domain Management",
                  "White-label Reporting",
                  "API Access",
                  "Dedicated Account Manager"
                ],
                buttonText: "Contact Sales",
                buttonClass: "bg-gradient-to-r from-cyan-500 to-blue-500 text-white",
                borderClass: "border-cyan-500/30"
              }
            ].map((plan, index) => (
              <div key={index} className={`pricing-card ${plan.borderClass} relative`}>
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-gradient-to-r from-lime-500 to-green-500 text-black px-4 py-1 rounded-full text-sm font-bold">
                      MOST POPULAR
                    </span>
                  </div>
                )}
                <div className="text-center mb-6">
                  <h3 className={`text-xl font-bold mb-2 ${
                    plan.name === 'Pro Business' ? 'text-lime-400' : 'text-cyan-400'
                  }`}>
                    {plan.name}
                  </h3>
                  <div className="mb-2">
                    <span className={`text-4xl font-bold ${
                      plan.name === 'Pro Business' ? 'text-lime-400' : 'text-cyan-400'
                    }`}>
                      {plan.price}
                    </span>
                    <span className="text-gray-400">{plan.period}</span>
                  </div>
                  <p className="text-gray-400 text-sm">{plan.description}</p>
                </div>
                
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-start">
                      <span className="text-green-400 mr-3 mt-0.5">✓</span>
                      <span className="text-gray-300 text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
                
                <button className={`w-full py-3 rounded-lg font-medium transition-all duration-300 hover:transform hover:-translate-y-1 ${plan.buttonClass}`}>
                  {plan.buttonText}
                </button>
              </div>
            ))}
          </div>
          
          <div className="text-center mt-8">
            <p className="text-gray-400">
              Need something custom?{' '}
              <a href="#contact" className="text-lime-400 hover:text-lime-300 transition-colors">
                Contact our sales team
              </a>{' '}
              for enterprise solutions.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="w-64 h-48 bg-gradient-to-r from-lime-500 to-green-500 rounded-xl mb-6 flex items-center justify-center">
                <img src="/src/assets/traffictuner-logo.jpg" alt="TrafficTuner" className="w-32 h-auto" />
              </div>
              <h2 className="text-3xl font-bold mb-6">
                You're Not Just Improving Your Site—You're Becoming the Answer.
              </h2>
              <p className="text-gray-300 mb-8">
                Stop guessing and start growing. Our AI-powered analysis gives you a personalized roadmap to more traffic, authority, and success.
              </p>
              <button
                onClick={() => setShowSignupModal(true)}
                className="bg-gradient-to-r from-cyan-500 to-lime-500 text-black px-8 py-4 rounded-lg font-medium text-lg hover:opacity-90 transition-opacity"
              >
                Start Your Free Analysis Now
              </button>
            </div>
            
            <div className="bg-gray-800/50 p-8 rounded-xl border border-cyan-500/30">
              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-cyan-400 mb-2">Starter Domain</h3>
                <div className="mb-4">
                  <span className="text-4xl font-bold text-cyan-400">$29</span>
                  <span className="text-gray-400">/year</span>
                </div>
              </div>
              
              <ul className="space-y-3 mb-6">
                <li className="flex items-center">
                  <span className="text-green-400 mr-3">✓</span>
                  <span className="text-gray-300">Full SEO + AEO Report</span>
                </li>
                <li className="flex items-center">
                  <span className="text-green-400 mr-3">✓</span>
                  <span className="text-gray-300">LLMs.txt Generator</span>
                </li>
                <li className="flex items-center">
                  <span className="text-green-400 mr-3">✓</span>
                  <span className="text-gray-300">Monthly Progress Tracking</span>
                </li>
              </ul>
              
              <a
                href="#pricing"
                className="block w-full text-center bg-cyan-500 text-black py-3 rounded-lg font-medium hover:bg-cyan-400 transition-colors"
              >
                View All Pricing →
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-800 border-t border-gray-700 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center mb-4">
                <img src="/src/assets/traffictuner-logo.jpg" alt="TrafficTuner" className="h-8 w-auto mr-3" />
                <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-lime-400 bg-clip-text text-transparent">
                  TrafficTuner
                </span>
              </div>
              <p className="text-gray-400 text-sm">
                Making website optimization for both Google and AI simple and powerful.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#api" className="hover:text-white transition-colors">API</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#about" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#contact" className="hover:text-white transition-colors">Contact</a></li>
                <li><a href="#privacy" className="hover:text-white transition-colors">Privacy</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Resources</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#blog" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="#help" className="hover:text-white transition-colors">Help Center</a></li>
                <li><a href="#docs" className="hover:text-white transition-colors">Documentation</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-700 mt-8 pt-8 text-center text-gray-400 text-sm">
            © 2025 TrafficTuner. All rights reserved.
          </div>
        </div>
      </footer>

      {/* Login Modal */}
      {showLoginModal && (
        <LoginModal
          onClose={() => setShowLoginModal(false)}
          onSwitchToSignup={() => {
            setShowLoginModal(false);
            setShowSignupModal(true);
          }}
        />
      )}

      {/* Signup Modal */}
      {showSignupModal && (
        <SignupModal
          onClose={() => setShowSignupModal(false)}
          onSwitchToLogin={() => {
            setShowSignupModal(false);
            setShowLoginModal(true);
          }}
        />
      )}
    </div>
  );
};

// Login Modal Component
const LoginModal = ({ onClose, onSwitchToSignup }) => {
  const { login } = useAuth();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(formData.email, formData.password);
      onClose();
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl p-8 w-full max-w-md border border-gray-700">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Login</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-400"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-400"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-cyan-500 to-lime-500 text-black py-3 rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-400">
            Don't have an account?{' '}
            <button
              onClick={onSwitchToSignup}
              className="text-cyan-400 hover:text-cyan-300 transition-colors"
            >
              Sign up
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

// Signup Modal Component
const SignupModal = ({ onClose, onSwitchToLogin }) => {
  const { register } = useAuth();
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await register(formData.name, formData.email, formData.password);
      onClose();
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl p-8 w-full max-w-md border border-gray-700">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Sign Up</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Name</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-400"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-400"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-400"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-cyan-500 to-lime-500 text-black py-3 rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-400">
            Already have an account?{' '}
            <button
              onClick={onSwitchToLogin}
              className="text-cyan-400 hover:text-cyan-300 transition-colors"
            >
              Login
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  );
}

export default App;

