import React, { useState, useRef, useEffect } from "react";
import { apiUrl, wsUrl } from '../config/api';
import PageWrapper from "./PageWrapper";
import usePreventZoom from "./usePreventZoom";
import MonacoProjectEditor from "./MonacoProjectEditor";

const ProjectBuilder = () => {
  usePreventZoom();
  const [projectIdea, setProjectIdea] = useState("");
  const [isBuilding, setIsBuilding] = useState(false);
  const [buildProgress, setBuildProgress] = useState([]);
  const [generatedProject, setGeneratedProject] = useState(null);
  const [showMonacoEditor, setShowMonacoEditor] = useState(false);
  const [fileTree, setFileTree] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState("");
  const [selectedImages, setSelectedImages] = useState([]);
  const [autoRunEnabled, setAutoRunEnabled] = useState(false);
  const [showProductInput, setShowProductInput] = useState(false);
  const [productDataText, setProductDataText] = useState("");
  const [productDataError, setProductDataError] = useState("");
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [projectIdea]);

  const handleImageUpload = (event) => {
    const files = Array.from(event.target.files);
    const imageFiles = files.filter(file => file.type.startsWith('image/'));
    
    setSelectedImages(prev => [...prev, ...imageFiles]);
    
    // For demo purposes, add image descriptions to the text
    const imageDescriptions = imageFiles.map(file => `[Image: ${file.name}]`).join(" ");
    setProjectIdea(prev => prev + (prev ? " " : "") + imageDescriptions);
  };

  const removeImage = (index) => {
    setSelectedImages(prev => prev.filter((_, i) => i !== index));
  };

  // Generate a meaningful, human-readable project name from the idea description
  // Note: The backend will ensure uniqueness by appending numbers if needed (e.g., todo-list, todo-list-2)
  const generateProjectName = (idea) => {
    if (!idea) return 'my-project';
    
    // Common words to filter out
    const stopWords = ['a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 
      'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall',
      'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
      'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once',
      'create', 'build', 'make', 'develop', 'design', 'implement', 'add', 'use', 'using', 'want',
      'need', 'like', 'help', 'please', 'can', 'you', 'i', 'we', 'they', 'it', 'this', 'that',
      'app', 'application', 'website', 'web', 'page', 'site', 'project', 'system', 'platform',
      'and', 'or', 'but', 'if', 'so', 'because', 'about', 'which', 'when', 'where', 'who', 'what', 'how'];
    
    // Extract meaningful words from the idea
    const words = idea.toLowerCase()
      .replace(/[^\w\s]/g, ' ') // Remove punctuation
      .split(/\s+/)
      .filter(word => word.length > 2 && !stopWords.includes(word));
    
    // Take the first 2-3 meaningful words
    const keyWords = words.slice(0, 3);
    
    if (keyWords.length === 0) {
      // Fallback: use first few words of original idea
      const fallbackWords = idea.toLowerCase()
        .replace(/[^\w\s]/g, ' ')
        .split(/\s+/)
        .filter(word => word.length > 1)
        .slice(0, 2);
      return fallbackWords.length > 0 ? fallbackWords.join('-') : 'my-project';
    }
    
    // Create a clean slug from keywords (no random numbers)
    return keyWords.join('-');
  };

  const loadFileTree = async (projectName) => {
    try {
      const treeRes = await fetch(
        apiUrl(`api/project-file-tree?project_name=${encodeURIComponent(projectName)}`)
      );
      const treeData = await treeRes.json();
      if (treeData.success) {
        setFileTree(treeData.file_tree || treeData.tree || []);
      }
    } catch (error) {
      console.error("Failed to load file tree:", error);
    }
  };

  const buildProject = async () => {
    if (!projectIdea.trim()) return;
    setIsBuilding(true);
    setBuildProgress([]);
    setGeneratedProject(null);

    // Generate a meaningful project name from the idea
    const projectName = generateProjectName(projectIdea);
    
    // Set initial project data and immediately show Monaco Editor
    const initialProject = {
      name: projectName,
      idea: projectIdea,
      tech_stack: ["React", "FastAPI", "Vite", "TailwindCSS"],
      preview_url: null,
      isBuilding: true
    };
    
    setGeneratedProject(initialProject);
    setShowMonacoEditor(true);
    
    // Setup WebSocket connection for real-time updates
    const ws = new WebSocket(wsUrl(`ws/project/${projectName}`));
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'status':
          setBuildProgress(prev => [...prev, `[${data.phase?.toUpperCase()}] ${data.message}`]);
          break;
        case 'terminal_output':
          setBuildProgress(prev => [...prev, `[${data.level?.toUpperCase()}] ${data.message}`]);
          break;
        case 'preview_ready':
          setBuildProgress(prev => [...prev, `[SUCCESS] 🌐 Live preview ready: ${data.url}`]);
          // Update project with preview URL
          setGeneratedProject(prev => ({
            ...prev,
            preview_url: data.url,
            isBuilding: false
          }));
          break;
        case 'file_created':
          setBuildProgress(prev => [...prev, `[FILE] ✓ Created ${data.file_path}`]);
          // Refresh file tree when new files are created
          loadFileTree(projectName);
          break;
      }
    };

    try {
      // Use the new AI-powered React + FastAPI generation
      const payload = {
        project_name: projectName,
        idea: projectIdea,
        tech_stack: ["React", "FastAPI", "Vite", "TailwindCSS"]
      };

      // Add image context if images are selected
      if (selectedImages.length > 0) {
        payload.context = `Project includes ${selectedImages.length} reference image(s): ${selectedImages.map(img => img.name).join(", ")}`;
      }

      // Add product data if provided (for e-commerce projects)
      if (showProductInput && productDataText.trim()) {
        try {
          const parsedProducts = JSON.parse(productDataText);
          payload.product_data = parsedProducts;
          setBuildProgress(prev => [...prev, `[PRODUCTS] 📦 Using ${parsedProducts.length || 'custom'} products from your catalog`]);
        } catch (e) {
          setBuildProgress(prev => [...prev, `[WARN] ⚠️ Could not parse product data, using AI-generated products`]);
        }
      }

      setBuildProgress(["[INIT] 🤖 Starting AI-powered React + FastAPI generation..."]);

      const response = await fetch(apiUrl("api/build-with-ai"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      
      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || "Build failed");
      }

      // Set the final generated project data
      setGeneratedProject(prev => ({
        ...prev,
        preview_url: data.preview_url,
        isBuilding: false
      }));

      // Load initial file tree
      await loadFileTree(projectName);

    } catch (error) {
      setBuildProgress((prev) => [...prev, `[ERROR] ${error.message}`]);
      setGeneratedProject(prev => prev ? {...prev, isBuilding: false} : null);
    } finally {
      setIsBuilding(false);
    }
  };

  const resetBuilder = () => {
    setProjectIdea("");
    setBuildProgress([]);
    setGeneratedProject(null);
    setFileTree([]);
    setSelectedFile(null);
    setFileContent("");
    setIsBuilding(false);
    setShowMonacoEditor(false);
    setSelectedImages([]);
    setShowProductInput(false);
    setProductDataText("");
    setProductDataError("");
  };

  const handleFileClick = async (file) => {
    if (file.type === "dir") return;
    setSelectedFile(file.path);
    setFileContent("Loading file content...");
    try {
      const res = await fetch(
        apiUrl(`api/project-file-content?project_name=${encodeURIComponent(
          generatedProject.name
        )}&file_path=${encodeURIComponent(file.path)}`
      ));
      const data = await res.json();
      setFileContent(data.content || "Error: Could not load file content.");
    } catch (error) {
      setFileContent("Error: Could not connect to the server.");
    }
  };

  return (
    <PageWrapper>
      <style>{`
        :root {
          --bg-black: #0a0a0a;
          --card-bg: rgba(255, 255, 255, 0.04);
          --card-border: rgba(255, 255, 255, 0.08);
          --text-primary: #ffffff;
          --text-secondary: #a1a1a1;
          --accent: #4ade80;
        }
        .project-builder-page {
          background: var(--bg-black);
          color: var(--text-primary);
          min-height: 100vh;
          font-family: "Inter", sans-serif;
        }
        .layout-container {
          max-width: 900px;
          margin: 0 auto;
          padding: 4rem 2rem;
        }
        .hero-section { text-align: center; margin-bottom: 4rem; }
        .hero-title { font-size: 3rem; font-weight: 700; margin: 0; }
                .hero-subtitle {
          font-size: 1.2rem;
          color: var(--text-secondary);
          margin-bottom: 2rem;
          line-height: 1.6;
        }

        .features-info {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
          margin-bottom: 2rem;
          padding: 1.5rem;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 1rem;
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .feature-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-size: 0.95rem;
          color: var(--text-primary);
        }

        .feature-icon {
          font-size: 1.2rem;
          opacity: 0.8;
        }

        .main-input-card {
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: 1.5rem;
          padding: 0;
          margin-bottom: 2rem;
          box-shadow: 0 8px 30px rgba(0,0,0,0.2);
          transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
          overflow: hidden;
        }
        .main-input-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 8px 32px 0 rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .main-input-card:focus-within {
          outline: none;
          border: 1px solid rgba(255, 255, 255, 0.3);
          box-shadow: 0 8px 32px 0 rgba(255, 255, 255, 0.15);
        }

        .card {
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: 1rem;
          padding: 2rem;
          margin-bottom: 2rem;
          box-shadow: 0 8px 30px rgba(0,0,0,0.2);
          transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        }
        .card:hover {
          transform: translateY(-5px);
          box-shadow: 0 8px 32px 0 rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .card:focus {
          outline: none;
          border: 1px solid rgba(255, 255, 255, 0.3);
          box-shadow: 0 8px 32px 0 rgba(255, 255, 255, 0.15);
        }

        .idea-input {
          width: 100%;
          background: transparent;
          border: none;
          color: var(--text-primary);
          font-size: 1.1rem;
          padding: 1.5rem 2rem;
          resize: none;
          min-height: 120px;
          line-height: 1.6;
        }
        .idea-input:focus { outline: none; }
        .idea-input::placeholder {
          color: var(--text-secondary);
          opacity: 0.7;
        }

        .btn {
          margin-top: 2rem;
          background: #ffffff;
          border: none;
          color: #000000;
          padding: 0.9rem 2rem;
          border-radius: 999px;
          font-weight: 600;
          cursor: pointer;
          font-size: 1rem;
          transition: all 0.3s;
        }
        .btn:hover:not(:disabled) { opacity: 0.9; transform: translateY(-2px); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }

        .terminal {
          margin-top: 2rem;
          background: #111;
          border-radius: 0.75rem;
          padding: 1.25rem;
          font-family: "JetBrains Mono", monospace;
          font-size: 0.9rem;
          max-height: 250px;
          overflow-y: auto;
        }
        .terminal-line { margin-bottom: 0.5rem; color: var(--text-secondary); }
        .terminal-line .log-prefix { color: var(--accent); margin-right: 0.5rem; }

        .results-grid {
          display: grid;
          grid-template-columns: 280px 1fr;
          gap: 1.5rem;
        }
        @media (max-width: 900px) { .results-grid { grid-template-columns: 1fr; } }

        .file-tree { max-height: 600px; overflow-y: auto; }
        .file-item { padding: 0.4rem; cursor: pointer; border-radius: 0.25rem; }
        .file-item:hover { background: rgba(255,255,255,0.08); }
        .file-item.selected { background: rgba(74, 222, 128, 0.15); color: var(--accent); }

        .code-editor {
          background: #111;
          border-radius: 0.75rem;
          padding: 1rem;
          height: 600px;
          overflow: auto;
          font-family: "JetBrains Mono", monospace;
          font-size: 0.9rem;
          white-space: pre-wrap;
        }

        .tech-stack {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          margin-top: 1rem;
        }
        .tech-item {
          background: rgba(74, 222, 128, 0.15);
          color: var(--accent);
          padding: 0.25rem 0.75rem;
          border-radius: 999px;
          font-size: 0.8rem;
          font-weight: 600;
        }

        .input-container {
          display: flex;
          align-items: flex-end;
          background: transparent;
          border-top: 1px solid var(--card-border);
          padding: 1rem 1.5rem;
          gap: 0.75rem;
        }
        
        .input-wrapper {
          flex: 1;
        }
        
        .input-controls {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .media-btn {
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid rgba(255, 255, 255, 0.15);
          color: var(--text-secondary);
          padding: 0.75rem;
          border-radius: 0.75rem;
          cursor: pointer;
          font-size: 1.1rem;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 44px;
          height: 44px;
          white-space: nowrap;
        }
        .media-btn:hover { 
          background: rgba(255, 255, 255, 0.12); 
          color: var(--text-primary);
          transform: translateY(-1px);
        }
        .media-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          transform: none;
        }
        .media-btn.recording { 
          background: rgba(220, 38, 38, 0.15); 
          border-color: rgba(220, 38, 38, 0.3);
          color: #dc2626; 
          border-color: #dc2626;
          animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.7; }
          100% { opacity: 1; }
        }

        @media (max-width: 768px) {
          .input-container {
            flex-direction: column;
            align-items: stretch;
            gap: 1rem;
          }
          
          .input-controls {
            justify-content: center;
          }
          
          .media-btn {
            font-size: 0.9rem;
            padding: 0.5rem 1rem;
          }
        }

        .image-preview {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          margin-top: 1rem;
        }
        .image-item {
          position: relative;
          background: rgba(255, 255, 255, 0.1);
          padding: 0.5rem;
          border-radius: 0.5rem;
          font-size: 0.85rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        .remove-image {
          background: #dc2626;
          border: none;
          color: white;
          border-radius: 50%;
          width: 20px;
          height: 20px;
          cursor: pointer;
          font-size: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .hidden { display: none; }
      `}</style>

      <div className="project-builder-page">
        <div className="layout-container">
          <div className="hero-section">
            <h1 className="hero-title">AI Project Builder</h1>
            <p className="hero-subtitle">
              Generate complete full-stack applications with React, FastAPI, and deployment-ready code.
            </p>
          </div>

          {!generatedProject ? (
            <div className="main-input-card">
              <textarea
                ref={textareaRef}
                value={projectIdea}
                onChange={(e) => setProjectIdea(e.target.value)}
                placeholder="Build a todo app with AI reminders, or create a blog with user auth..."
                className="idea-input"
                disabled={isBuilding}
              />
              
              {/* E-commerce Product Data Toggle */}
              <div style={{ 
                padding: '0.75rem 1.5rem', 
                borderTop: '1px solid var(--card-border)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem'
              }}>
                <label style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '0.5rem',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  color: 'var(--text-secondary)'
                }}>
                  <input
                    type="checkbox"
                    checked={showProductInput}
                    onChange={(e) => setShowProductInput(e.target.checked)}
                    style={{ 
                      width: '16px', 
                      height: '16px', 
                      accentColor: 'var(--accent)' 
                    }}
                    disabled={isBuilding}
                  />
                  <span>📦 Add my product catalog (for e-commerce)</span>
                </label>
              </div>

              {/* Product Data Input */}
              {showProductInput && (
                <div style={{ 
                  padding: '1rem 1.5rem', 
                  borderTop: '1px solid var(--card-border)',
                  background: 'rgba(74, 222, 128, 0.05)'
                }}>
                  <div style={{ marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      Paste your products as JSON array:
                    </label>
                    <button 
                      onClick={() => setProductDataText(`[
  {
    "name": "Product Name",
    "price": 29.99,
    "description": "Product description here",
    "category": "Category",
    "image_url": "https://images.unsplash.com/photo-..."
  }
]`)}
                      style={{
                        background: 'transparent',
                        border: '1px solid var(--card-border)',
                        color: 'var(--text-secondary)',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '0.25rem',
                        fontSize: '0.75rem',
                        cursor: 'pointer'
                      }}
                    >
                      📋 Show Example
                    </button>
                  </div>
                  <textarea
                    value={productDataText}
                    onChange={(e) => {
                      setProductDataText(e.target.value);
                      // Validate JSON
                      if (e.target.value.trim()) {
                        try {
                          JSON.parse(e.target.value);
                          setProductDataError("");
                        } catch (err) {
                          setProductDataError("Invalid JSON format");
                        }
                      } else {
                        setProductDataError("");
                      }
                    }}
                    placeholder='[{"name": "T-Shirt", "price": 29.99, "description": "Cotton t-shirt", "category": "Clothing"}, ...]'
                    style={{
                      width: '100%',
                      background: 'rgba(0, 0, 0, 0.3)',
                      border: productDataError ? '1px solid #dc2626' : '1px solid var(--card-border)',
                      borderRadius: '0.5rem',
                      color: 'var(--text-primary)',
                      fontSize: '0.85rem',
                      padding: '0.75rem',
                      minHeight: '100px',
                      resize: 'vertical',
                      fontFamily: '"JetBrains Mono", monospace'
                    }}
                    disabled={isBuilding}
                  />
                  {productDataError && (
                    <p style={{ color: '#dc2626', fontSize: '0.75rem', marginTop: '0.25rem' }}>
                      ⚠️ {productDataError}
                    </p>
                  )}
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                    💡 Your actual products will be used instead of AI-generated placeholder data
                  </p>
                </div>
              )}
              
              <div className="input-container">
                <div className="input-controls">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isBuilding}
                    className="media-btn"
                    title="Add Images"
                  >
                    📷
                  </button>
                  
                  <button
                    onClick={buildProject}
                    disabled={isBuilding || !projectIdea.trim()}
                    className="btn"
                  >
                    {isBuilding ? "Building..." : "Build with AI"}
                  </button>
                </div>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleImageUpload}
                  className="hidden"
                />
              </div>

              {selectedImages.length > 0 && (
                <div className="image-preview">
                  {selectedImages.map((image, index) => (
                    <div key={index} className="image-item">
                      📷 {image.name}
                      <button
                        onClick={() => removeImage(index)}
                        className="remove-image"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
              {buildProgress.length > 0 && (
                <div className="terminal">
                  {buildProgress.map((log, index) => (
                    <div key={index} className="terminal-line">
                      <span className="log-prefix">
                        [{log.match(/^\[(.*?)\]/)?.[1] || "INFO"}]
                      </span>
                      {log.replace(/^\[.*?\]\s/, "")}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="card">
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: "1rem",
                  flexWrap: "wrap",
                  gap: "1rem",
                }}
              >
                <div>
                  <h2 style={{ margin: 0 }}>{generatedProject.name}</h2>
                  <p style={{ color: "var(--text-secondary)" }}>
                    {generatedProject.description}
                  </p>
                </div>
                <div className="enhanced-actions">
                  <button
                    onClick={() => setShowMonacoEditor(true)}
                    className="btn monaco-btn"
                    style={{ background: "#007acc", color: "#fff", marginRight: "1rem" }}
                  >
                    🚀 Open in Monaco Editor
                  </button>
                  <button
                    onClick={resetBuilder}
                    className="btn"
                    style={{ background: "#222", color: "#fff" }}
                  >
                    Build Another
                  </button>
                </div>
              </div>

              <div className="results-grid">
                <div className="file-tree card" style={{ padding: "1rem" }}>
                  {fileTree.map((file, idx) => (
                    <div
                      key={idx}
                      className={`file-item ${
                        selectedFile === file.path ? "selected" : ""
                      }`}
                      onClick={() => handleFileClick(file)}
                    >
                      {file.path}
                    </div>
                  ))}
                </div>
                <div className="code-editor">
                  {selectedFile ? fileContent : "Select a file to view its code."}
                </div>
              </div>

              <div style={{ marginTop: "2rem" }}>
                <h3>Tech Stack</h3>
                <div className="tech-stack">
                  {generatedProject.tech_stack.map((tech, index) => (
                    <span key={index} className="tech-item">
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Monaco Editor Modal */}
      {showMonacoEditor && generatedProject && (
        <MonacoProjectEditor
          project={generatedProject}
          onClose={() => setShowMonacoEditor(false)}
        />
      )}
    </PageWrapper>
  );
};

export default ProjectBuilder;
