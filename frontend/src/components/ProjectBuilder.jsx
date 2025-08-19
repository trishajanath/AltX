import React, { useState, useRef, useEffect } from 'react';
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom';

// --- Sub-component: Custom Select Dropdown ---
const CustomSelect = ({ options, value, onChange, disabled }) => {
    const [isOpen, setIsOpen] = useState(false);
    const wrapperRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleSelect = (optionValue) => {
        onChange(optionValue);
        setIsOpen(false);
    };

    const selectedOption = options.find(opt => opt.value === value);

    return (
        <div className="custom-select-wrapper" ref={wrapperRef}>
            <button className={`select-trigger ${isOpen ? 'open' : ''}`} onClick={() => setIsOpen(!isOpen)} disabled={disabled}>
                <span>{selectedOption?.label || 'Select...'}</span>
                <svg className={`chevron ${isOpen ? 'open' : ''}`} width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M6 9L12 15L18 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
            </button>
            {isOpen && (
                <div className="select-options">
                    {options.map(option => (
                        <div key={option.value} className="select-option" onClick={() => handleSelect(option.value)}>
                            <strong>{option.label}</strong>
                            {option.description && <span className="option-description">{option.description}</span>}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};


// --- Main Page Component ---
const ProjectBuilder = () => {
    usePreventZoom();
    const [projectIdea, setProjectIdea] = useState('');
    const [isBuilding, setIsBuilding] = useState(false);
    const [buildProgress, setBuildProgress] = useState([]);
    const [generatedProject, setGeneratedProject] = useState(null);
    const [techStack, setTechStack] = useState('auto');
    const [projectType, setProjectType] = useState('web-app');
    const [complexity, setComplexity] = useState('medium');
    const [fileTree, setFileTree] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [fileContent, setFileContent] = useState('');
    const textareaRef = useRef(null);

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [projectIdea]);

    const buildProject = async () => {
        if (!projectIdea.trim()) return;
        setIsBuilding(true);
        setBuildProgress([]);
        setGeneratedProject(null);
        
        const steps = [
            '[INFO] Analyzing project requirements...',
            '[INFO] Selecting optimal tech stack...',
            '[INFO] Creating project structure...',
            '[INFO] Generating core components...',
            '[INFO] Configuring build tools...',
            '[INFO] Installing dependencies...',
        ];
        let currentProgress = ['[INIT] Starting project generation...'];
        setBuildProgress(currentProgress);

        for (const step of steps) {
            await new Promise(res => setTimeout(res, 800 + Math.random() * 400));
            currentProgress = [...currentProgress, step];
            setBuildProgress(currentProgress);
        }

        try {
            const response = await fetch('http://localhost:8000/generate-project', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ idea: projectIdea, project_type: projectType, tech_stack: techStack, complexity }),
            });
            const data = await response.json();
            if (!data.success) throw new Error(data.error || 'Project generation failed');
            
            setGeneratedProject(data.project);
            setBuildProgress(prev => [...prev, '[OK] Project generation complete!']);

            const treeRes = await fetch(`http://localhost:8000/project-file-tree?project_name=${encodeURIComponent(data.project.name)}`);
            const treeData = await treeRes.json();
            if (treeData.success) setFileTree(treeData.tree || []);

        } catch (error) {
            setBuildProgress(prev => [...prev, `[ERROR] ${error.message}`]);
        } finally {
            setIsBuilding(false);
        }
    };

    const resetBuilder = () => {
        setProjectIdea('');
        setBuildProgress([]);
        setGeneratedProject(null);
        setFileTree([]);
        setSelectedFile(null);
        setFileContent('');
        setIsBuilding(false);
    };

    const handleFileClick = async (file) => {
        if (file.type === 'dir') return;
        setSelectedFile(file.path);
        setFileContent('Loading file content...');
        try {
            const res = await fetch(`http://localhost:8000/project-file-content?project_name=${encodeURIComponent(generatedProject.name)}&file_path=${encodeURIComponent(file.path)}`);
            const data = await res.json();
            setFileContent(data.content || 'Error: Could not load file content.');
        } catch (error) {
            setFileContent('Error: Could not connect to the server.');
        }
    };

    const projectTypeOptions = [
        { value: "web-app", label: "Web Application", description: "Interactive sites and dashboards." },
        { value: "api", label: "API Service", description: "Backend for mobile or web clients." },
        { value: "mobile-app", label: "Mobile App", description: "iOS & Android applications." },
    ];
    const techStackOptions = [
        { value: "auto", label: "Auto-select", description: "Let the AI choose the best stack." },
        { value: "react-node", label: "React + Node.js", description: "Popular for modern web apps." },
        { value: "python-fastapi", label: "Python + FastAPI", description: "Ideal for data-intensive APIs." },
    ];
    const complexityOptions = [
        { value: "simple", label: "Simple", description: "A minimal viable product (MVP)." },
        { value: "medium", label: "Medium", description: "A well-featured standard application." },
        { value: "complex", label: "Complex", description: "Enterprise-grade with scaling." },
    ];
    
    return (
        <PageWrapper>
            <style>{`
                :root {
                    --bg-black: #000000; --card-bg: rgba(10, 10, 10, 0.5); --card-border: rgba(255, 255, 255, 0.1);
                    --card-border-hover: rgba(255, 255, 255, 0.3); --text-primary: #f5f5f5; --text-secondary: #bbbbbb;
                }
                .project-builder-page { background: transparent; color: var(--text-primary); min-height: 100vh; font-family: sans-serif; }
                .layout-container { max-width: 1200px; margin: 0 auto; padding: 0 2rem 4rem 2rem; }
                
                .hero-section { text-align: center; padding: 4rem 1rem 3rem 1rem; }
                .hero-title { font-size: 3.5rem; font-weight: 700; margin: 0; letter-spacing: -2px; color: var(--text-primary); }
                .hero-subtitle { color: var(--text-secondary); margin: 1rem auto 0 auto; font-size: 1.1rem; max-width: 650px; line-height: 1.6; }

                .card { width: 100%; box-sizing: border-box; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); transition: all 0.3s ease; }
                .card:hover { border-color: var(--card-border-hover); box-shadow: 0 0 25px rgba(255, 255, 255, 0.08); }
                .card h3 { font-size: 1rem; font-weight: 500; color: var(--text-secondary); margin: 0 0 1.5rem 0; text-transform: uppercase; letter-spacing: 1px; }

                .idea-input { width: 100%; box-sizing: border-box; background: rgba(0,0,0,0.2); border: 1px solid var(--card-border); color: var(--text-primary); border-radius: 0.75rem; padding: 1rem; font-size: 1.1rem; line-height: 1.6; resize: none; min-height: 80px; }
                .idea-input:focus { border-color: var(--text-primary); outline: none; }
                
                .options-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin: 1.5rem 0; }
                .form-label { display: block; font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.5rem; }
                
                .btn { width: 100%; background: var(--text-primary); border: 1px solid var(--text-primary); color: var(--bg-black); padding: 0.75rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; transition: all 0.3s; display: flex; align-items: center; justify-content: center; gap: 0.5rem; }
                .btn:disabled { opacity: 0.5; cursor: not-allowed; }
                .btn:hover:not(:disabled) { box-shadow: 0 0 20px rgba(255, 255, 255, 0.2); transform: translateY(-2px); }
                .btn-secondary { background: transparent; color: var(--text-secondary); border: 1px solid var(--card-border); }
                .btn-secondary:hover:not(:disabled) { border-color: var(--text-primary); color: var(--text-primary); }
                
                .terminal { background: #000; border: 1px solid var(--card-border); border-radius: 0.5rem; padding: 1.5rem; margin-top: 1.5rem; height: 250px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.9rem; }
                .terminal-line { line-height: 1.6; color: var(--text-secondary); }
                .terminal-line .log-prefix { display: inline-block; margin-right: 0.75rem; color: var(--text-primary); font-weight: 600; }
                
                .results-grid { display: grid; grid-template-columns: 300px 1fr; gap: 2rem; }
                @media (max-width: 1024px) { .results-grid { grid-template-columns: 1fr; } }
                
                .file-tree { max-height: 600px; overflow-y: auto; }
                .file-item { padding: 0.4rem 0.5rem; cursor: pointer; border-radius: 0.25rem; font-size: 0.9rem; word-break: break-all; }
                .file-item:hover { background: rgba(255,255,255,0.1); }
                .file-item.selected { background: rgba(255,255,255,0.15); color: var(--text-primary); font-weight: 500; }
                
                .code-editor { background: #000; border: 1px solid var(--card-border); border-radius: 0.5rem; padding: 1.5rem; height: 600px; overflow: auto; font-family: 'Courier New', monospace; font-size: 0.9rem; white-space: pre-wrap; }
                
                .tech-stack { display: flex; flex-wrap: wrap; gap: 0.5rem; }
                .tech-item { background: rgba(255,255,255,0.1); color: var(--text-secondary); padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 600; }
                
                /* Custom Select Styles */
                .custom-select-wrapper { position: relative; width: 100%; }
                .select-trigger { width: 100%; box-sizing: border-box; display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.2); border: 1px solid var(--card-border); color: var(--text-primary); border-radius: 0.5rem; padding: 0.75rem 1rem; font-size: 1rem; text-align: left; cursor: pointer; transition: border-color 0.2s; }
                .select-trigger.open, .select-trigger:hover { border-color: var(--card-border-hover); }
                .chevron { transition: transform 0.2s ease; color: var(--text-secondary); } .chevron.open { transform: rotate(180deg); }
                .select-options { position: absolute; top: calc(100% + 8px); left: 0; right: 0; background: var(--card-bg); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid var(--card-border-hover); border-radius: 0.75rem; z-index: 10; max-height: 220px; overflow-y: auto; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2); animation: dropdown-fade-in 0.2s ease-out; }
                .select-option { padding: 1rem; cursor: pointer; } .select-option:hover { background: rgba(255, 255, 255, 0.08); }
                .select-option:not(:last-child) { border-bottom: 1px solid var(--card-border); }
                .select-option strong { color: var(--text-primary); }
                .option-description { display: block; font-size: 0.8rem; color: var(--text-primary); opacity: 0.7; margin-top: 0.25rem; }
                @keyframes dropdown-fade-in { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
            `}</style>
            
            <div className="project-builder-page">
                <div className="layout-container">
                    <div className="hero-section">
                        <h1 className="hero-title">AI Project Builder</h1>
                        <p className="hero-subtitle">Describe the application you want to build. Our AI will generate a complete project structure, code, dependencies, and deployment configuration.</p>
                    </div>

                    {!generatedProject ? (
                        <div className="card">
                            <textarea
                                ref={textareaRef}
                                value={projectIdea}
                                onChange={(e) => setProjectIdea(e.target.value)}
                                placeholder="e.g., A minimalist blog built with Next.js and Tailwind CSS, deployed on Vercel..."
                                className="idea-input"
                                disabled={isBuilding}
                            />
                            <div className="options-grid">
                                <div className="option-group">
                                    <label className="form-label">Project Type</label>
                                    <CustomSelect options={projectTypeOptions} value={projectType} onChange={setProjectType} disabled={isBuilding} />
                                </div>
                                <div className="option-group">
                                    <label className="form-label">Tech Stack</label>
                                    <CustomSelect options={techStackOptions} value={techStack} onChange={setTechStack} disabled={isBuilding} />
                                </div>
                                <div className="option-group">
                                    <label className="form-label">Complexity</label>
                                    <CustomSelect options={complexityOptions} value={complexity} onChange={setComplexity} disabled={isBuilding} />
                                </div>
                            </div>
                            <button onClick={buildProject} disabled={isBuilding || !projectIdea.trim()} className="btn">
                                {isBuilding ? 'Building Project...' : 'Build with AI'}
                            </button>
                            {buildProgress.length > 0 && (
                                <div className="terminal">
                                    {buildProgress.map((log, index) => (
                                        <div key={index} className="terminal-line">
                                            <span className="log-prefix">[{log.match(/^\[(.*?)\]/)?.[1] || 'INFO'}]</span>
                                            {log.replace(/^\[.*?\]\s/, '')}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="card">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
                                <div>
                                    <h2 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)', fontSize: '1.8rem' }}>{generatedProject.name}</h2>
                                    <p style={{ margin: 0, color: 'var(--text-secondary)' }}>{generatedProject.description}</p>
                                </div>
                                <button onClick={resetBuilder} className="btn btn-secondary" style={{width: 'auto'}}>Build Another Project</button>
                            </div>
                            
                            <div className="results-grid">
                                <div className="file-tree-container">
                                    <h3>File Structure</h3>
                                    <div className="file-tree card" style={{padding: '1rem'}}>
                                        {fileTree.map((file, idx) => (
                                            <div key={idx} className={`file-item ${selectedFile === file.path ? 'selected' : ''}`} onClick={() => handleFileClick(file)}>
                                                {file.path}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                <div className="code-viewer-container">
                                    <h3>Code Viewer</h3>
                                    <div className="code-editor">
                                        {selectedFile ? fileContent : "Select a file to view its code."}
                                    </div>
                                </div>
                            </div>
                            
                            <div style={{ marginTop: '2rem' }}>
                                <h3>Tech Stack</h3>
                                <div className="tech-stack">
                                    {generatedProject.tech_stack.map((tech, index) => <span key={index} className="tech-item">{tech}</span>)}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </PageWrapper>
    );
};

export default ProjectBuilder;