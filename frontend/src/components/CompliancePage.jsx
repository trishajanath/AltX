import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Lock, 
  FileCheck, 
  Eye, 
  Database, 
  Key, 
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Code,
  Copy,
  Check,
  Info,
  Globe,
  Server,
  Users,
  FileText,
  Trash2,
  Download,
  Bell,
  ClipboardList
} from 'lucide-react';
import PageWrapper from './PageWrapper';
import { apiUrl } from '../config/api';

const CompliancePage = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [expandedSections, setExpandedSections] = useState({});
  const [documentation, setDocumentation] = useState(null);
  const [requirements, setRequirements] = useState(null);
  const [codePatterns, setCodePatterns] = useState(null);
  const [selectedPattern, setSelectedPattern] = useState(null);
  const [patternCode, setPatternCode] = useState(null);
  const [copiedPattern, setCopiedPattern] = useState(null);
  const [loading, setLoading] = useState(true);
  const [standards, setStandards] = useState(null);
  const [categories, setCategories] = useState(null);
  const [aiEnforcement, setAiEnforcement] = useState(null);

  useEffect(() => {
    loadComplianceData();
  }, []);

  const loadComplianceData = async () => {
    try {
      setLoading(true);
      const [docRes, reqRes, patRes, stdRes, catRes, aiRes] = await Promise.all([
        fetch(`${apiUrl}/api/compliance/documentation`),
        fetch(`${apiUrl}/api/compliance/requirements`),
        fetch(`${apiUrl}/api/compliance/code-patterns`),
        fetch(`${apiUrl}/api/compliance/standards`),
        fetch(`${apiUrl}/api/compliance/categories`),
        fetch(`${apiUrl}/api/compliance/ai-enforcement`)
      ]);

      const [docData, reqData, patData, stdData, catData, aiData] = await Promise.all([
        docRes.json(),
        reqRes.json(),
        patRes.json(),
        stdRes.json(),
        catRes.json(),
        aiRes.json()
      ]);

      setDocumentation(docData);
      setRequirements(reqData);
      setCodePatterns(patData);
      setStandards(stdData);
      setCategories(catData);
      setAiEnforcement(aiData);
    } catch (error) {
      console.error('Failed to load compliance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPatternCode = async (patternName) => {
    try {
      const res = await fetch(`${apiUrl}/api/compliance/code-patterns?pattern_name=${patternName}`);
      const data = await res.json();
      setPatternCode(data.code);
      setSelectedPattern(patternName);
    } catch (error) {
      console.error('Failed to load pattern:', error);
    }
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const copyToClipboard = async (text, patternName) => {
    await navigator.clipboard.writeText(text);
    setCopiedPattern(patternName);
    setTimeout(() => setCopiedPattern(null), 2000);
  };

  const getStandardIcon = (standard) => {
    switch(standard.toLowerCase()) {
      case 'gdpr': return <Globe className="w-6 h-6" />;
      case 'nist_800_53': case 'nist 800-53': case 'nist': return <Server className="w-6 h-6" />;
      case 'iso_27001': case 'iso 27001': return <Shield className="w-6 h-6" />;
      case 'soc2': case 'soc 2': return <FileCheck className="w-6 h-6" />;
      default: return <Lock className="w-6 h-6" />;
    }
  };

  const getCategoryIcon = (category) => {
    switch(category) {
      case 'data_protection': return <Database className="w-5 h-5" />;
      case 'access_control': return <Users className="w-5 h-5" />;
      case 'encryption': return <Key className="w-5 h-5" />;
      case 'audit_logging': return <ClipboardList className="w-5 h-5" />;
      case 'consent_management': return <CheckCircle2 className="w-5 h-5" />;
      case 'data_retention': return <Trash2 className="w-5 h-5" />;
      case 'incident_response': return <Bell className="w-5 h-5" />;
      case 'secure_development': return <Code className="w-5 h-5" />;
      case 'privacy_by_design': return <Eye className="w-5 h-5" />;
      case 'data_minimization': return <FileText className="w-5 h-5" />;
      default: return <Shield className="w-5 h-5" />;
    }
  };

  if (loading) {
    return (
      <PageWrapper>
        <div className="min-h-screen bg-black text-white flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper>
      <div className="min-h-screen bg-black text-white">
        {/* Header */}
        <div className="bg-gradient-to-r from-cyan-900/30 via-purple-900/30 to-blue-900/30 border-b border-gray-800">
          <div className="max-w-7xl mx-auto px-6 py-12">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 bg-cyan-500/20 rounded-xl">
                <Shield className="w-10 h-10 text-cyan-400" />
              </div>
              <div>
                <h1 className="text-4xl font-bold">Compliance Framework</h1>
                <p className="text-gray-400 mt-1">GDPR • SOC 2 • NIST SP 800-53</p>
              </div>
            </div>
            <p className="text-lg text-gray-300 max-w-3xl">
              AltX ensures all generated applications comply with major data protection and security 
              standards by design. Every line of code is generated with compliance requirements in mind.
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="border-b border-gray-800 sticky top-0 bg-black/95 backdrop-blur-sm z-10">
          <div className="max-w-7xl mx-auto px-6">
            <nav className="flex gap-1">
              {[
                { id: 'overview', label: 'Overview', icon: Info },
                { id: 'standards', label: 'Standards', icon: Shield },
                { id: 'requirements', label: 'Requirements', icon: FileCheck },
                { id: 'code-patterns', label: 'Code Patterns', icon: Code },
                { id: 'ai-enforcement', label: 'AI Enforcement', icon: Lock }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-cyan-500 text-cyan-400'
                      : 'border-transparent text-gray-400 hover:text-white'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* Overview Tab */}
          {activeTab === 'overview' && documentation && (
            <div className="space-y-8">
              {/* Quick Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-cyan-900/30 to-cyan-900/10 border border-cyan-800/50 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Globe className="w-8 h-8 text-cyan-400" />
                    <h3 className="text-xl font-semibold">GDPR</h3>
                  </div>
                  <p className="text-gray-400 text-sm mb-2">EU Regulation 2016/679</p>
                  <a href="https://gdpr-info.eu/" target="_blank" rel="noopener noreferrer" 
                     className="text-cyan-400 text-xs hover:underline flex items-center gap-1 mb-4">
                    gdpr-info.eu <ExternalLink className="w-3 h-3" />
                  </a>
                  <ul className="space-y-2">
                    {documentation.gdpr?.implementation_summary?.slice(0, 4).map((item, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm">
                        <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
                        <span className="text-gray-300">{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-gradient-to-br from-purple-900/30 to-purple-900/10 border border-purple-800/50 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <FileCheck className="w-8 h-8 text-purple-400" />
                    <h3 className="text-xl font-semibold">SOC 2</h3>
                  </div>
                  <p className="text-gray-400 text-sm mb-2">AICPA Trust Services Criteria</p>
                  <a href="https://sprinto.com/blog/soc-2-controls/" target="_blank" rel="noopener noreferrer" 
                     className="text-purple-400 text-xs hover:underline flex items-center gap-1 mb-4">
                    SOC 2 Controls Guide <ExternalLink className="w-3 h-3" />
                  </a>
                  <ul className="space-y-2">
                    {documentation.soc2?.implementation_summary?.slice(0, 4).map((item, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm">
                        <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
                        <span className="text-gray-300">{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-gradient-to-br from-blue-900/30 to-blue-900/10 border border-blue-800/50 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Server className="w-8 h-8 text-blue-400" />
                    <h3 className="text-xl font-semibold">NIST SP 800-53</h3>
                  </div>
                  <p className="text-gray-400 text-sm mb-2">Security & Privacy Controls</p>
                  <a href="https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf" target="_blank" rel="noopener noreferrer" 
                     className="text-blue-400 text-xs hover:underline flex items-center gap-1 mb-4">
                    NIST Publication <ExternalLink className="w-3 h-3" />
                  </a>
                  <ul className="space-y-2">
                    {documentation.nist_800_53?.implementation_summary?.slice(0, 4).map((item, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm">
                        <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
                        <span className="text-gray-300">{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* How It Works */}
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
                <h2 className="text-2xl font-bold mb-6">How AltX Enforces Compliance</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {documentation.overview?.enforcement_methods?.map((method, i) => (
                    <div key={i} className="flex flex-col items-center text-center p-4">
                      <div className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center mb-4">
                        <span className="text-cyan-400 font-bold text-lg">{i + 1}</span>
                      </div>
                      <p className="text-gray-300">{method}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Code Patterns Preview */}
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
                <h2 className="text-2xl font-bold mb-6">Compliant Code Patterns</h2>
                <p className="text-gray-400 mb-6">
                  Every generated application includes these pre-built, compliance-verified patterns:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {documentation.code_patterns?.patterns?.map((pattern, i) => (
                    <div 
                      key={i}
                      className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 hover:border-cyan-500/50 transition-colors cursor-pointer"
                      onClick={() => {
                        setActiveTab('code-patterns');
                        loadPatternCode(pattern.name);
                      }}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <Code className="w-4 h-4 text-cyan-400" />
                        <span className="font-mono text-sm text-cyan-400">{pattern.name}</span>
                      </div>
                      <p className="text-gray-400 text-sm">{pattern.purpose}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Standards Tab */}
          {activeTab === 'standards' && standards && (
            <div className="space-y-8">
              {standards.standards?.map((standard, i) => (
                <div 
                  key={i}
                  className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden"
                >
                  <div 
                    className="p-6 cursor-pointer hover:bg-gray-800/30 transition-colors"
                    onClick={() => toggleSection(`standard-${standard.id}`)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-xl ${
                          standard.id === 'gdpr' ? 'bg-cyan-500/20 text-cyan-400' :
                          standard.id === 'iso_27001' ? 'bg-purple-500/20 text-purple-400' :
                          'bg-blue-500/20 text-blue-400'
                        }`}>
                          {getStandardIcon(standard.id)}
                        </div>
                        <div>
                          <h3 className="text-xl font-bold">{standard.name}</h3>
                          <p className="text-gray-400">{standard.full_name}</p>
                        </div>
                      </div>
                      {expandedSections[`standard-${standard.id}`] 
                        ? <ChevronDown className="w-5 h-5 text-gray-400" />
                        : <ChevronRight className="w-5 h-5 text-gray-400" />
                      }
                    </div>
                  </div>
                  
                  {expandedSections[`standard-${standard.id}`] && (
                    <div className="px-6 pb-6 border-t border-gray-800 pt-6">
                      <p className="text-gray-300 mb-6">{standard.description}</p>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <h4 className="font-semibold mb-3 text-gray-200">
                            {standard.key_principles ? 'Key Principles' : 'Trust Principles'}
                          </h4>
                          <ul className="space-y-2">
                            {(standard.key_principles || standard.trust_principles)?.map((item, j) => (
                              <li key={j} className="flex items-start gap-2">
                                <CheckCircle2 className="w-4 h-4 text-green-400 mt-1 flex-shrink-0" />
                                <span className="text-gray-400">
                                  {typeof item === 'string' ? item : `${item.name}: ${item.description}`}
                                </span>
                              </li>
                            ))}
                          </ul>
                        </div>
                        
                        <div className="space-y-4">
                          {standard.jurisdiction && (
                            <div>
                              <h4 className="font-semibold mb-2 text-gray-200">Jurisdiction</h4>
                              <p className="text-gray-400">{standard.jurisdiction}</p>
                            </div>
                          )}
                          {standard.penalties && (
                            <div>
                              <h4 className="font-semibold mb-2 text-gray-200">Penalties</h4>
                              <p className="text-red-400">{standard.penalties}</p>
                            </div>
                          )}
                          {standard.effective_date && (
                            <div>
                              <h4 className="font-semibold mb-2 text-gray-200">Effective Date</h4>
                              <p className="text-gray-400">{standard.effective_date}</p>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {standard.domains && (
                        <div className="mt-6">
                          <h4 className="font-semibold mb-3 text-gray-200">Control Domains</h4>
                          <div className="flex flex-wrap gap-2">
                            {standard.domains.map((domain, j) => (
                              <span 
                                key={j}
                                className="px-3 py-1 bg-gray-800 rounded-full text-sm text-gray-300"
                              >
                                {domain}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Requirements Tab */}
          {activeTab === 'requirements' && requirements && (
            <div className="space-y-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold">
                  {requirements.total_count} Compliance Requirements
                </h2>
              </div>

              {Object.entries(requirements.requirements || {}).map(([standardName, reqs]) => (
                <div key={standardName} className="space-y-4">
                  <h3 className="text-xl font-semibold flex items-center gap-2">
                    {getStandardIcon(standardName)}
                    <span className="uppercase">{standardName.replace('_', ' ')}</span>
                    <span className="text-gray-500 text-sm font-normal">({reqs.length} requirements)</span>
                  </h3>
                  
                  <div className="space-y-3">
                    {reqs.map((req, i) => (
                      <div 
                        key={i}
                        className="bg-gray-900/50 border border-gray-800 rounded-lg overflow-hidden"
                      >
                        <div 
                          className="p-4 cursor-pointer hover:bg-gray-800/30 transition-colors"
                          onClick={() => toggleSection(`req-${req.id}`)}
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex items-start gap-3">
                              {getCategoryIcon(req.category)}
                              <div>
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-mono text-cyan-400 text-sm">{req.id}</span>
                                  <span className={`px-2 py-0.5 rounded text-xs ${
                                    req.severity === 'required' 
                                      ? 'bg-red-500/20 text-red-400' 
                                      : 'bg-yellow-500/20 text-yellow-400'
                                  }`}>
                                    {req.severity}
                                  </span>
                                </div>
                                <h4 className="font-semibold">{req.title}</h4>
                                <p className="text-gray-400 text-sm mt-1">{req.description}</p>
                              </div>
                            </div>
                            {expandedSections[`req-${req.id}`] 
                              ? <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                              : <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
                            }
                          </div>
                        </div>
                        
                        {expandedSections[`req-${req.id}`] && (
                          <div className="px-4 pb-4 border-t border-gray-800 pt-4">
                            <div className="bg-gray-800/50 rounded-lg p-4 mb-4">
                              <h5 className="font-semibold text-sm mb-2 text-gray-300">Implementation Guidance</h5>
                              <pre className="text-gray-400 text-sm whitespace-pre-wrap font-sans">
                                {req.implementation}
                              </pre>
                            </div>
                            
                            {req.references && req.references.length > 0 && (
                              <div>
                                <h5 className="font-semibold text-sm mb-2 text-gray-300">References</h5>
                                <div className="flex flex-wrap gap-2">
                                  {req.references.map((ref, j) => (
                                    <span 
                                      key={j}
                                      className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-400"
                                    >
                                      {ref}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Code Patterns Tab */}
          {activeTab === 'code-patterns' && codePatterns && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Pattern List */}
              <div className="space-y-3">
                <h3 className="text-lg font-semibold mb-4">Available Patterns</h3>
                {codePatterns.available_patterns?.map((pattern) => (
                  <button
                    key={pattern}
                    onClick={() => loadPatternCode(pattern)}
                    className={`w-full text-left p-4 rounded-lg border transition-colors ${
                      selectedPattern === pattern
                        ? 'bg-cyan-900/30 border-cyan-500'
                        : 'bg-gray-900/50 border-gray-800 hover:border-gray-700'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Code className="w-4 h-4 text-cyan-400" />
                      <span className="font-mono text-sm">{pattern}</span>
                    </div>
                    <p className="text-gray-400 text-xs">
                      {codePatterns.patterns?.[pattern]?.lines} lines
                    </p>
                  </button>
                ))}
              </div>

              {/* Code View */}
              <div className="lg:col-span-2">
                {selectedPattern && patternCode ? (
                  <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
                      <span className="font-mono text-cyan-400">{selectedPattern}</span>
                      <button
                        onClick={() => copyToClipboard(patternCode, selectedPattern)}
                        className="flex items-center gap-2 px-3 py-1 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors text-sm"
                      >
                        {copiedPattern === selectedPattern ? (
                          <>
                            <Check className="w-4 h-4 text-green-400" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4" />
                            Copy
                          </>
                        )}
                      </button>
                    </div>
                    <pre className="p-4 overflow-x-auto text-sm">
                      <code className="text-gray-300">{patternCode}</code>
                    </pre>
                  </div>
                ) : (
                  <div className="bg-gray-900/50 rounded-xl border border-gray-800 p-12 text-center">
                    <Code className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400">Select a pattern to view the code</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* AI Enforcement Tab */}
          {activeTab === 'ai-enforcement' && aiEnforcement && (
            <div className="space-y-8">
              {/* Method Overview */}
              <div className="bg-gradient-to-r from-cyan-900/30 to-purple-900/30 border border-cyan-800/50 rounded-xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Lock className="w-8 h-8 text-cyan-400" />
                  <div>
                    <h2 className="text-2xl font-bold">{aiEnforcement.enforcement_method}</h2>
                    <p className="text-gray-400">{aiEnforcement.description}</p>
                  </div>
                </div>
              </div>

              {/* Validation Checks */}
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
                <h3 className="text-xl font-bold mb-6">Automated Validation Checks</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {aiEnforcement.validation_checks?.map((check, i) => (
                    <div key={i} className="bg-gray-800/50 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <CheckCircle2 className="w-5 h-5 text-green-400 mt-0.5" />
                        <div>
                          <h4 className="font-semibold">{check.check}</h4>
                          <p className="text-gray-400 text-sm mt-1">{check.description}</p>
                          <div className="flex gap-2 mt-2">
                            {check.standards.map((std, j) => (
                              <span 
                                key={j}
                                className="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 rounded text-xs"
                              >
                                {std}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Prompt Injection */}
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
                  <h3 className="text-xl font-bold">Compliance Prompt Injection</h3>
                  <button
                    onClick={() => copyToClipboard(aiEnforcement.prompt_injection, 'prompt')}
                    className="flex items-center gap-2 px-3 py-1 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors text-sm"
                  >
                    {copiedPattern === 'prompt' ? (
                      <>
                        <Check className="w-4 h-4 text-green-400" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        Copy
                      </>
                    )}
                  </button>
                </div>
                <pre className="p-6 overflow-x-auto text-sm bg-gray-950">
                  <code className="text-gray-300 whitespace-pre-wrap">{aiEnforcement.prompt_injection}</code>
                </pre>
              </div>

              {/* Applied Patterns */}
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
                <h3 className="text-xl font-bold mb-4">Code Patterns Applied During Generation</h3>
                <div className="flex flex-wrap gap-2">
                  {aiEnforcement.code_patterns_applied?.map((pattern, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        setActiveTab('code-patterns');
                        loadPatternCode(pattern);
                      }}
                      className="px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm font-mono text-cyan-400 transition-colors"
                    >
                      {pattern}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </PageWrapper>
  );
};

export default CompliancePage;
