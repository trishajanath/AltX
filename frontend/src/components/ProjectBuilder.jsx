import React, { useState, useRef, useEffect } from 'react';
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom';

// Add CSS animations
const spinKeyframes = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  @keyframes typing {
    from { width: 0; }
    to { width: 100%; }
  }
`;

// Inject the keyframes into the document head
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.innerHTML = spinKeyframes;
  document.head.appendChild(style);
}

const ProjectBuilder = () => {
  usePreventZoom();
  const [projectIdea, setProjectIdea] = useState('');
  const [isBuilding, setIsBuilding] = useState(false);
  const [buildProgress, setBuildProgress] = useState([]);
  const [generatedProject, setGeneratedProject] = useState(null);
  const [techStack, setTechStack] = useState('auto');
  const [projectType, setProjectType] = useState('web-app');
  const [complexity, setComplexity] = useState('medium');
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [projectIdea]);

  const buildProject = async () => {
    if (!projectIdea.trim()) return;

    setIsBuilding(true);
    setBuildProgress(['🚀 Starting project generation...']);
    setGeneratedProject(null);

    try {
      // Simulate building process with realistic steps
      const steps = [
        '🚀 Starting project generation...',
        '🧠 Analyzing project requirements...',
        '🏗️ Selecting optimal tech stack...',
        '📁 Creating project structure...',
        '⚙️ Generating core components...',
        '🎨 Setting up UI framework...',
        '🔧 Configuring build tools...',
        '📦 Installing dependencies...',
        '🔗 Setting up API endpoints...',
        '✅ Project generation complete!'
      ];

      // Show progress steps
      for (let i = 1; i < steps.length - 1; i++) {
        setBuildProgress(prev => [...prev, steps[i]]);
        await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 400));
      }

      // Call the actual backend API
      const response = await fetch('http://localhost:8000/generate-project', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          idea: projectIdea,
          project_type: projectType,
          tech_stack: techStack,
          complexity: complexity
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setBuildProgress(prev => [...prev, steps[steps.length - 1]]);
        setGeneratedProject(data.project);
      } else {
        throw new Error(data.error || 'Project generation failed');
      }

    } catch (error) {
      console.error('Project generation error:', error);
      setBuildProgress(prev => [...prev, `❌ ${error.message || 'Project generation failed. Please try again.'}`]);
    } finally {
      setIsBuilding(false);
    }
  };

  const resetBuilder = () => {
    setProjectIdea('');
    setBuildProgress([]);
    setGeneratedProject(null);
    setIsBuilding(false);
  };

  return (
    <PageWrapper>
      <style>
        {`
          :root {
            --primary-green: #00f5c3;
            --primary-blue: #00d4ff;
            --background-dark: #0a0a0a;
            --card-bg: rgba(26, 26, 26, 0.8);
            --card-bg-hover: rgba(36, 36, 36, 0.9);
            --card-border: rgba(255, 255, 255, 0.1);
            --text-light: #f5f5f5;
            --text-dark: #a3a3a3;
            --success: #22c55e;
            --warning: #f59e0b;
            --error: #ef4444;
          }

          body {
            background: linear-gradient(135deg, var(--background-dark) 0%, #1a1a1a 100%);
            color: var(--text-light);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
          }
          
          .builder-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            min-height: 100vh;
          }
          
          .hero-section {
            text-align: center;
            margin-bottom: 3rem;
          }
          
          .hero-title {
            font-size: 3.5rem;
            font-weight: 900;
            background: linear-gradient(135deg, var(--primary-green), var(--primary-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
            line-height: 1.1;
          }
          
          .hero-subtitle {
            font-size: 1.25rem;
            color: var(--text-dark);
            max-width: 600px;
            margin: 0 auto 2rem;
            line-height: 1.6;
          }
          
          .build-card {
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--card-border);
            border-radius: 1rem;
            padding: 2rem;
            margin-bottom: 2rem;
            transition: all 0.3s ease;
          }
          
          .build-card:hover {
            background: var(--card-bg-hover);
            border-color: rgba(0, 245, 195, 0.3);
            transform: translateY(-2px);
          }
          
          .idea-input {
            width: 100%;
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1.5rem;
            color: var(--text-light);
            font-size: 1.1rem;
            line-height: 1.6;
            resize: none;
            min-height: 120px;
            transition: all 0.3s ease;
            font-family: inherit;
          }
          
          .idea-input:focus {
            outline: none;
            border-color: var(--primary-green);
            box-shadow: 0 0 0 3px rgba(0, 245, 195, 0.1);
            background: rgba(0, 0, 0, 0.5);
          }
          
          .idea-input::placeholder {
            color: var(--text-dark);
          }
          
          .options-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0;
          }
          
          .option-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
          }
          
          .option-label {
            font-weight: 600;
            color: var(--text-light);
            font-size: 0.9rem;
          }
          
          .option-select {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 0.75rem;
            color: var(--text-light);
            font-size: 0.9rem;
            transition: all 0.3s ease;
          }
          
          .option-select:focus {
            outline: none;
            border-color: var(--primary-green);
            box-shadow: 0 0 0 2px rgba(0, 245, 195, 0.1);
          }
          
          .build-button {
            width: 100%;
            background: linear-gradient(135deg, var(--primary-green) 0%, var(--primary-blue) 100%);
            color: #000;
            border: none;
            border-radius: 12px;
            padding: 1rem 2rem;
            font-size: 1.1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 1.5rem;
          }
          
          .build-button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 245, 195, 0.3);
          }
          
          .build-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
          }
          
          .progress-container {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1.5rem;
            margin-top: 1.5rem;
            max-height: 300px;
            overflow-y: auto;
          }
          
          .progress-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.75rem;
            animation: fadeIn 0.5s ease;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 0.9rem;
          }
          
          .progress-item:last-child {
            margin-bottom: 0;
          }
          
          .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(0, 245, 195, 0.2);
            border-top: 2px solid var(--primary-green);
            border-radius: 50%;
            animation: spin 1s linear infinite;
          }
          
          .project-result {
            background: linear-gradient(135deg, rgba(0, 245, 195, 0.1) 0%, rgba(0, 212, 255, 0.1) 100%);
            border: 1px solid rgba(0, 245, 195, 0.3);
            border-radius: 16px;
            padding: 2rem;
            margin-top: 2rem;
            animation: fadeIn 0.8s ease;
          }
          
          .project-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1.5rem;
          }
          
          .project-title {
            font-size: 1.8rem;
            font-weight: 800;
            color: var(--primary-green);
            margin-bottom: 0.5rem;
          }
          
          .project-description {
            color: var(--text-dark);
            font-size: 1rem;
            line-height: 1.5;
          }
          
          .project-actions {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
          }
          
          .action-button {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 0.5rem 1rem;
            color: var(--text-light);
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
          }
          
          .action-button:hover {
            background: rgba(0, 245, 195, 0.1);
            border-color: var(--primary-green);
            transform: translateY(-1px);
          }
          
          .project-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
          }
          
          .detail-section {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 12px;
            padding: 1.5rem;
          }
          
          .detail-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-light);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
          }
          
          .tech-stack {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
          }
          
          .tech-item {
            background: rgba(0, 245, 195, 0.1);
            border: 1px solid rgba(0, 245, 195, 0.3);
            border-radius: 20px;
            padding: 0.3rem 0.8rem;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--primary-green);
          }
          
          .feature-list, .structure-list {
            list-style: none;
            padding: 0;
            margin: 0;
          }
          
          .feature-item, .structure-item {
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            color: var(--text-dark);
            font-size: 0.9rem;
          }
          
          .feature-item:last-child, .structure-item:last-child {
            border-bottom: none;
          }
          
          .structure-item {
            font-family: 'SF Mono', Monaco, monospace;
          }
          
          .reset-button {
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            color: var(--text-light);
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 1rem;
          }
          
          .reset-button:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.3);
          }
          
          @media (max-width: 768px) {
            .builder-container {
              padding: 1rem;
            }
            
            .hero-title {
              font-size: 2.5rem;
            }
            
            .options-grid {
              grid-template-columns: 1fr;
            }
            
            .project-actions {
              flex-direction: column;
            }
            
            .project-details {
              grid-template-columns: 1fr;
            }
          }
        `}
      </style>

      <div className="builder-container">
        <div className="hero-section">
          <h1 className="hero-title">Let's build something new</h1>
          <p className="hero-subtitle">
            Describe the application you want to build, or start from a template. 
            Our AI will generate a complete project structure with code, dependencies, and deployment ready.
          </p>
        </div>

        {!generatedProject && (
          <div className="build-card">
            <textarea
              ref={textareaRef}
              value={projectIdea}
              onChange={(e) => setProjectIdea(e.target.value)}
              placeholder="e.g., 'A Python Flask app with a Postgres database for tracking user habits'"
              className="idea-input"
              disabled={isBuilding}
            />

            <div className="options-grid">
              <div className="option-group">
                <label className="option-label">Project Type</label>
                <select 
                  value={projectType} 
                  onChange={(e) => setProjectType(e.target.value)}
                  className="option-select"
                  disabled={isBuilding}
                >
                  <option value="web-app">Web Application</option>
                  <option value="mobile-app">Mobile App</option>
                  <option value="api">API Service</option>
                  <option value="desktop-app">Desktop App</option>
                  <option value="ai-ml">AI/ML Project</option>
                  <option value="blockchain">Blockchain App</option>
                </select>
              </div>

              <div className="option-group">
                <label className="option-label">Tech Stack</label>
                <select 
                  value={techStack} 
                  onChange={(e) => setTechStack(e.target.value)}
                  className="option-select"
                  disabled={isBuilding}
                >
                  <option value="auto">Auto-select</option>
                  <option value="react-node">React + Node.js</option>
                  <option value="python-fastapi">Python + FastAPI</option>
                  <option value="nextjs">Next.js Full-stack</option>
                  <option value="vue-express">Vue + Express</option>
                  <option value="django">Django</option>
                  <option value="rails">Ruby on Rails</option>
                </select>
              </div>

              <div className="option-group">
                <label className="option-label">Complexity</label>
                <select 
                  value={complexity} 
                  onChange={(e) => setComplexity(e.target.value)}
                  className="option-select"
                  disabled={isBuilding}
                >
                  <option value="simple">Simple (MVP)</option>
                  <option value="medium">Medium (Full-featured)</option>
                  <option value="complex">Complex (Enterprise)</option>
                </select>
              </div>
            </div>

            <button 
              onClick={buildProject}
              disabled={isBuilding || !projectIdea.trim()}
              className="build-button"
            >
              {isBuilding ? (
                <>
                  <div className="spinner"></div>
                  Building Project...
                </>
              ) : (
                <>
                  ✨ Build Project
                </>
              )}
            </button>

            {buildProgress.length > 0 && (
              <div className="progress-container">
                {buildProgress.map((step, index) => (
                  <div key={index} className="progress-item">
                    {index === buildProgress.length - 1 && isBuilding ? (
                      <div className="spinner"></div>
                    ) : (
                      <span>✓</span>
                    )}
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {generatedProject && (
          <div className="project-result">
            <div className="project-header">
              <div>
                <h2 className="project-title">{generatedProject.name}</h2>
                <p className="project-description">{generatedProject.description}</p>
              </div>
              <div className="project-actions">
                <a href={generatedProject.github_repo} className="action-button" target="_blank" rel="noopener noreferrer">
                  📁 View Code
                </a>
                <a href={generatedProject.deployment_url} className="action-button" target="_blank" rel="noopener noreferrer">
                  🚀 Live Demo
                </a>
                <button onClick={() => navigator.clipboard.writeText(generatedProject.github_repo)} className="action-button">
                  📋 Copy Repo
                </button>
              </div>
            </div>

            <div className="project-details">
              <div className="detail-section">
                <h3 className="detail-title">🛠️ Tech Stack</h3>
                <div className="tech-stack">
                  {generatedProject.tech_stack.map((tech, index) => (
                    <span key={index} className="tech-item">{tech}</span>
                  ))}
                </div>
                <div style={{ marginTop: '1rem', fontSize: '0.9rem', color: 'var(--text-dark)' }}>
                  <strong>Estimated Development Time:</strong> {generatedProject.estimated_time}
                </div>
              </div>

              <div className="detail-section">
                <h3 className="detail-title">⚡ Key Features</h3>
                <ul className="feature-list">
                  {generatedProject.features.map((feature, index) => (
                    <li key={index} className="feature-item">✓ {feature}</li>
                  ))}
                </ul>
              </div>

              <div className="detail-section">
                <h3 className="detail-title">📁 Project Structure</h3>
                <ul className="structure-list">
                  {generatedProject.structure.map((item, index) => (
                    <li key={index} className="structure-item">{item}</li>
                  ))}
                </ul>
              </div>
            </div>

            <button onClick={resetBuilder} className="reset-button">
              🔄 Build Another Project
            </button>
          </div>
        )}
      </div>
    </PageWrapper>
  );
};

export default ProjectBuilder;
