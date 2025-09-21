import React, { useState, useRef, useEffect } from "react";
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
  const [isRecording, setIsRecording] = useState(false);
  const [selectedImages, setSelectedImages] = useState([]);
  const [autoRunEnabled, setAutoRunEnabled] = useState(false);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [projectIdea]);

  const handleVoiceRecording = async () => {
    if (!isRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        
        const audioChunks = [];
        mediaRecorder.addEventListener("dataavailable", (event) => {
          audioChunks.push(event.data);
        });
        
        mediaRecorder.addEventListener("stop", async () => {
          const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
          // Convert speech to text (would need speech recognition API)
          // For demo purposes, append "[Voice Input]" to the text
          setProjectIdea(prev => prev + (prev ? " " : "") + "[Voice Input - Speech recognition would convert this to text]");
          stream.getTracks().forEach(track => track.stop());
        });
        
        mediaRecorder.start();
        setIsRecording(true);
      } catch (error) {
        console.error("Error accessing microphone:", error);
        alert("Unable to access microphone. Please ensure microphone permissions are granted.");
      }
    } else {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
        setIsRecording(false);
      }
    }
  };

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

  const buildProject = async () => {
    if (!projectIdea.trim()) return;
    setIsBuilding(true);
    setBuildProgress([]);
    setGeneratedProject(null);

    const steps = [
      "[INFO] Analyzing project requirements...",
      "[INFO] Generating full-stack architecture...",
      "[INFO] Creating React frontend with TailwindCSS...",
      "[INFO] Setting up FastAPI backend...",
      "[INFO] Configuring database models...",
      "[INFO] Implementing API endpoints...",
      "[INFO] Adding authentication logic...",
      "[INFO] Setting up deployment configurations...",
      "[INFO] Generating production-ready code...",
    ];
    let currentProgress = ["[INIT] Starting full-stack project generation..."];
    setBuildProgress(currentProgress);

    for (const step of steps) {
      await new Promise((res) => setTimeout(res, 800 + Math.random() * 400));
      currentProgress = [...currentProgress, step];
      setBuildProgress(currentProgress);
    }

    try {
      // Prepare the request payload
      const payload = {
        idea: projectIdea,
        project_type: "web-app",
        tech_stack: ["React", "TypeScript", "TailwindCSS", "FastAPI", "Python"],
        complexity: "medium"
      };

      // Add image context if images are selected
      if (selectedImages.length > 0) {
        payload.context = `Project includes ${selectedImages.length} reference image(s): ${selectedImages.map(img => img.name).join(", ")}`;
      }

      const response = await fetch("http://localhost:8000/generate-project", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!data.success) throw new Error(data.error || "Project generation failed");

      setGeneratedProject(data.project);
      setBuildProgress((prev) => [...prev, "[OK] Full-stack project generation complete!"]);
      setBuildProgress((prev) => [...prev, "[INFO] Frontend: React + TailwindCSS ready"]);
      setBuildProgress((prev) => [...prev, "[INFO] Backend: FastAPI + PostgreSQL configured"]);
      setBuildProgress((prev) => [...prev, "[INFO] Deployment: Ready for Vercel + Render"]);

      // Check if auto-run is enabled in response
      if (data.auto_run && data.auto_run.enabled) {
        setAutoRunEnabled(true);
        setBuildProgress((prev) => [...prev, "[INFO] Auto-run enabled - Opening Monaco Editor..."]);
        setBuildProgress((prev) => [...prev, "[INFO] Loading project file tree..."]);
        
        // Auto-open Monaco Editor
        setTimeout(() => {
          setShowMonacoEditor(true);
        }, 1000);

        // Auto-start project after a delay
        if (data.auto_run.auto_start_project) {
          setTimeout(async () => {
            setBuildProgress((prev) => [...prev, "[INFO] Auto-starting project..."]);
            try {
              const runResponse = await fetch("http://localhost:8001/api/run-project", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ project_name: data.project.name }),
              });
              const runData = await runResponse.json();
              if (runData.success) {
                setBuildProgress((prev) => [...prev, "[SUCCESS] Project started automatically!"]);
                setBuildProgress((prev) => [...prev, "[INFO] Live preview available"]);
              }
            } catch (error) {
              setBuildProgress((prev) => [...prev, `[WARNING] Auto-start failed: ${error.message}`]);
            }
          }, 3000);
        }
      } else {
        setBuildProgress((prev) => [...prev, "[INFO] Opening Monaco Editor..."]);
        setTimeout(() => {
          setShowMonacoEditor(true);
        }, 1000);
      }

      const treeRes = await fetch(
        `http://localhost:8001/api/project-file-tree?project_name=${encodeURIComponent(
          data.project.name
        )}`
      );
      const treeData = await treeRes.json();
      if (treeData.success) setFileTree(treeData.tree || []);
    } catch (error) {
      setBuildProgress((prev) => [...prev, `[ERROR] ${error.message}`]);
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
  };

  const handleFileClick = async (file) => {
    if (file.type === "dir") return;
    setSelectedFile(file.path);
    setFileContent("Loading file content...");
    try {
      const res = await fetch(
        `http://localhost:8000/project-file-content?project_name=${encodeURIComponent(
          generatedProject.name
        )}&file_path=${encodeURIComponent(file.path)}`
      );
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
            
            <div className="features-info">
              <div className="feature-item">
                <span className="feature-icon">⚛️</span>
                <span>React + TailwindCSS Frontend</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🔗</span>
                <span>FastAPI Backend + Database</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🤖</span>
                <span>AI Integration Ready</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🚀</span>
                <span>Production Deployment</span>
              </div>
            </div>
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
              
              <div className="input-container">
                <div className="input-controls">
                  <button
                    onClick={handleVoiceRecording}
                    disabled={isBuilding}
                    className={`media-btn ${isRecording ? 'recording' : ''}`}
                    title={isRecording ? "Stop Recording" : "Voice Input"}
                  >
                    {isRecording ? (
                      <>🔴</>
                    ) : (
                      <>🎤</>
                    )}
                  </button>
                  
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
