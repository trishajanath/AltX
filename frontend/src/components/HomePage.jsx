import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Rocket, Shield, GitBranch, BrainCircuit, BarChart3, Menu, ChevronDown, X } from 'lucide-react';
import * as THREE from 'three';

// --- 3D Background Component (Unchanged) ---
const ThreeBackground = () => {
    const mountRef = useRef(null);

    useEffect(() => {
        if (!mountRef.current) return;

        let animationFrameId;
        const currentMount = mountRef.current;

        try {
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, currentMount.clientWidth / currentMount.clientHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
            const clock = new THREE.Clock();

            renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
            renderer.setClearColor(0x000000, 0); 
            currentMount.appendChild(renderer.domElement);

            camera.position.set(0, 40, 130);
            camera.lookAt(scene.position);

            const particleCount = 50000;
            const particleData = [];
            const positions = new Float32Array(particleCount * 3);
            const colors = new Float32Array(particleCount * 3);
            
            const maxRadius = 80;

            for (let i = 0; i < particleCount; i++) {
                const i3 = i * 3;
                const radius = Math.random() * maxRadius;
                const angle = Math.random() * Math.PI * 2;

                particleData.push({
                    radius: radius,
                    angle: angle,
                    speed: (0.5 / (radius + 1)) * 0.15 + 0.002,
                });

                colors[i3] = 1.0;
                colors[i3 + 1] = 1.0;
                colors[i3 + 2] = 1.0;
            }

            const particleGeometry = new THREE.BufferGeometry();
            particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            particleGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

            const particleMaterial = new THREE.PointsMaterial({
                size: 0.5,
                vertexColors: true,
                blending: THREE.AdditiveBlending,
                transparent: true,
                depthWrite: false,
                sizeAttenuation: true,
            });

            const vortex = new THREE.Points(particleGeometry, particleMaterial);
            scene.add(vortex);

            const animate = () => {
                animationFrameId = requestAnimationFrame(animate);
                const elapsedTime = clock.getElapsedTime();
                const positions = vortex.geometry.attributes.position.array;

                for (let i = 0; i < particleCount; i++) {
                    const i3 = i * 3;
                    const data = particleData[i];

                    data.angle += data.speed;
                    data.radius -= 0.08;

                    if (data.radius < 0.1) {
                        data.radius = maxRadius;
                        data.angle = Math.random() * Math.PI * 2;
                    }

                    const spiralArms = 5;
                    const ringDensity = 0.4;
                    const waveSpeed = 1.0;

                    const armWave = Math.sin(data.angle * spiralArms + elapsedTime * waveSpeed) * 4;
                    const ringWave = Math.sin(data.radius * ringDensity - elapsedTime * waveSpeed) * 5;
                    const finalY = armWave + ringWave;
                    
                    positions[i3] = Math.cos(data.angle) * data.radius;
                    positions[i3 + 1] = finalY;
                    positions[i3 + 2] = Math.sin(data.angle) * data.radius;
                }

                vortex.geometry.attributes.position.needsUpdate = true;
                vortex.rotation.y += 0.0001;

                renderer.render(scene, camera);
            };
            animate();

            const handleResize = () => {
                if (currentMount) {
                    camera.aspect = currentMount.clientWidth / currentMount.clientHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
                }
            };
            window.addEventListener('resize', handleResize);

            return () => {
                window.removeEventListener('resize', handleResize);
                cancelAnimationFrame(animationFrameId);
                if (currentMount && renderer.domElement) {
                   try { currentMount.removeChild(renderer.domElement); } catch (e) {}
                }
            };

        } catch (error) {
            console.error("Failed to initialize 3D background:", error);
        }
    }, []);

    return <div ref={mountRef} style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', zIndex: 0, backgroundColor: '#000' }} />;
};


// --- Sidebar Component (Unchanged) ---
const Sidebar = ({ isOpen, toggleSidebar, setView, currentView }) => {
    const navigate = useNavigate();
    const menuItems = [
        { icon: <BarChart3 size={20} />, title: 'Dashboard', view: 'dashboard', path: '/home' },
        { icon: <Rocket size={20} />, title: 'Deploy Project', view: 'deploy', path: '/deploy' },
        { icon: <Shield size={20} />, title: 'Security Scan', view: 'security', path: '/security' },
        { icon: <GitBranch size={20} />, title: 'Repo Analysis', view: 'repo-analysis', path: '/repo-analysis' },
        { icon: <BarChart3 size={20} />, title: 'Reports', view: 'reports', path: '/report' },
        { icon: <Rocket size={20} />, title: 'Build Apps', view: 'build', path: '/build' },
    ];

    return (
        <>
            {isOpen && (
                <div className={`sidebar open`}>
                    <div className="sidebar-header">
                        <div className="logo">
                            <span className="logo-text">xVERTA</span>
                        </div>
                    <button className="close-button" onClick={toggleSidebar}>
                        <X size={24} />
                    </button>
                </div>
                <nav className="sidebar-nav">
                    {menuItems.map(item => (
                        <a 
                            key={item.view} 
                            href="#" 
                            onClick={e => {
                                e.preventDefault();
                                navigate(item.path);
                                if (window.innerWidth < 768) toggleSidebar();
                            }} 
                            className={`nav-item ${currentView === item.view ? 'active' : ''}`}
                        >
                            {item.icon}
                            <span>{item.title}</span>
                        </a>
                    ))}
                </nav>
                <div className="sidebar-footer">
                    <div className="user-profile">
                        <img src="https://placehold.co/40x40/000000/ffffff?text=A" alt="User Avatar" />
                        <div className="user-info">
                            <span>Admin User</span>
                            <small>admin@securai.com</small>
                        </div>
                        <ChevronDown size={16} />
                    </div>
                </div>
                </div>
            )}
        </>
    );
};

// --- Dashboard View Component (Unchanged) ---
const DashboardView = () => {
    const navigate = useNavigate();
    const deployedProjects = [
        { name: 'project-sentinel.securai.dev', status: 'Live', vulnerabilities: 0, lastScan: '2h ago' },
        { name: 'gamma-platform.securai.dev', status: 'Live', vulnerabilities: 2, lastScan: '8h ago' },
        { name: 'marketing-site.com', status: 'Error', vulnerabilities: 5, lastScan: '1d ago' },
    ];

    const recentScans = [
        { repo: 'acme-corp/frontend', status: 'Clean', issues: 0, timestamp: '15m ago' },
        { repo: 'acme-corp/api-gateway', status: 'Warnings', issues: 2, timestamp: '45m ago' },
        { repo: 'acme-corp/user-database', status: 'Failed', issues: 1, timestamp: '1h ago' },
    ];

    return (
        <div className="dashboard-view">
            <h1 className="page-title">Dashboard</h1>
            <p className="page-subtitle">Welcome back, here's a summary of your projects.</p>
            <div className="dashboard-grid">
                {/* Deployed Projects Card */}
                <div className="card" onClick={() => navigate('/deploy')}>
                    <div className="card-header">
                        <h2>Deployed Projects</h2>
                        <button onClick={e => { e.stopPropagation(); navigate('/deploy'); }} className="btn-secondary">Deploy New</button>
                    </div>
                    <div className="card-content">
                        <div className="table-wrapper">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Domain</th>
                                        <th>Status</th>
                                        <th>Vulnerabilities</th>
                                        <th>Last Scan</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {deployedProjects.map((proj, i) => (
                                        <tr key={i}>
                                            <td>{proj.name}</td>
                                            <td>
                                                <span className={`status-badge status-${proj.status.toLowerCase()}`}>
                                                    {proj.status}
                                                </span>
                                            </td>
                                            <td>
                                                <span className={`vulnerability-count ${proj.vulnerabilities > 0 ? 'has-issues' : ''}`}>
                                                    {proj.vulnerabilities}
                                                </span>
                                            </td>
                                            <td>{proj.lastScan}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* Recent Scans Card */}
                <div className="card" onClick={() => navigate('/security')}>
                    <div className="card-header">
                        <h2>Recent Scans</h2>
                        <button onClick={e => { e.stopPropagation(); navigate('/security'); }} className="btn-secondary">View All</button>
                    </div>
                    <div className="card-content">
                         <ul className="scan-list">
                            {recentScans.map((scan, i) => (
                                <li key={i} className="scan-item">
                                    <div className="scan-info">
                                        <span className="scan-repo">{scan.repo}</span>
                                        <span className="scan-time">{scan.timestamp}</span>
                                    </div>
                                    <div className={`scan-status status-${scan.status.toLowerCase()}`}>
                                        {scan.status} ({scan.issues} issues)
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Repo Analysis Card */}
                <div className="card" onClick={() => navigate('/repo-analysis')}>
                    <div className="card-header">
                        <h2>Repository Analysis</h2>
                        <button onClick={e => { e.stopPropagation(); navigate('/repo-analysis'); }} className="btn-secondary">Scan Repo</button>
                    </div>
                    <div className="card-content">
                        <p>Analyze your codebase for vulnerabilities, secrets, and dependency issues using AI-powered static analysis.</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

// --- Placeholder for other views (Unchanged) ---
const PlaceholderView = ({ title }) => (
    <div className="placeholder-view">
        <h1 className="page-title">{title}</h1>
        <p className="page-subtitle">This is a placeholder for the {title} page.</p>
        <div className="card">
            <div className="card-content">
                <p>Functionality for this section would be built out here.</p>
            </div>
        </div>
    </div>
);


// --- Main App Component ---
export default function App() {
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [currentView, setCurrentView] = useState('dashboard');

    useEffect(() => {
        if (window.innerWidth < 768) {
            setSidebarOpen(false);
        }
    }, []);
    
    const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

    const renderView = () => {
        // This logic would be handled by a router in a real app
        switch (currentView) {
            case 'dashboard':
                return <DashboardView setView={setCurrentView} />;
            case 'deploy':
                return <PlaceholderView title="Deploy Project" />;
            case 'security':
                return <PlaceholderView title="Security Scan" />;
            case 'repo-analysis':
                return <PlaceholderView title="Repository Analysis" />;
            case 'reports':
                return <PlaceholderView title="Reports" />;
            case 'build':
                 return <PlaceholderView title="Build Apps" />;
            default:
                return <DashboardView setView={setCurrentView} />;
        }
    };

    return (
        <div className={`app-container ${sidebarOpen ? 'sidebar-open' : ''}`}>
             <style>{`
                /* --- ✨ NEW & IMPROVED STYLES --- */
                @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@600;700&family=Inter:wght@400;500;600&display=swap');
                
                :root {
                    --bg-color: #000000;
                    --glass-bg: rgba(16, 16, 16, 0.6); /* For sidebar and cards */
                    --surface-color: rgba(255, 255, 255, 0.05); /* For hovers */
                    --border-color: rgba(255, 255, 255, 0.15);
                    --text-primary: #FFFFFF;
                    --text-secondary: #A0A0A0;
                    --accent-glow: #FFFFFF;
                    
                    /* Status Colors */
                    --status-ok: #2ECC71;
                    --status-warn: #F39C12;
                    --status-error: #E74C3C;

                    --sidebar-width: 260px;
                }

                * { box-sizing: border-box; margin: 0; padding: 0; }
                
                body {
                    font-family: 'Inter', sans-serif;
                    background-color: var(--bg-color);
                    color: var(--text-primary);
                    overflow: hidden;
                }

                /* Custom Scrollbar */
                ::-webkit-scrollbar { width: 8px; }
                ::-webkit-scrollbar-track { background: transparent; }
                ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 4px; }
                ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.4); }

                .app-container { display: flex; min-height: 100vh; background-color: var(--bg-color); }

                .main-content {
                    flex-grow: 1;
                    padding: 1.5rem;
                    transition: margin-left 0.3s ease-in-out;
                    margin-left: 0;
                    position: relative;
                    z-index: 2;
                    height: 100vh;
                    overflow-y: auto;
                }
                
                @media (min-width: 768px) {
                    .main-content { padding: 3rem; }
                    .app-container.sidebar-open .main-content {
                        margin-left: var(--sidebar-width);
                    }
                }
                
                /* --- Sidebar --- */
                .sidebar {
                    width: var(--sidebar-width);
                    background: var(--glass-bg);
                    border-right: 1px solid var(--border-color);
                    backdrop-filter: blur(10px);
                    -webkit-backdrop-filter: blur(10px);
                    display: flex;
                    flex-direction: column;
                    position: fixed;
                    top: 0;
                    left: 0;
                    height: 100%;
                    z-index: 100;
                    transform: translateX(-100%);
                    transition: transform 0.3s ease-in-out;
                }
                
                .sidebar.open { transform: translateX(0); }

                @media (min-width: 768px) {
                    .sidebar { transform: translateX(0); }
                    .app-container:not(.sidebar-open) .sidebar {
                        transform: translateX(-100%);
                    }
                }

                .sidebar-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 1.5rem;
                    border-bottom: 1px solid var(--border-color);
                }
                .logo-text {
                    font-family: 'Chakra Petch', sans-serif !important;
                    font-size: 1.8rem !important;
                    font-weight: 700 !important;
                    letter-spacing: 2px !important;
                    color: #ffffff !important;
                    text-shadow: none !important;
                    filter: none !important;
                    -webkit-text-fill-color: #ffffff !important;
                    -webkit-text-stroke: none !important;
                    background: none !important;
                    background-color: transparent !important;
                    justify-self: start;
                    align-self: start;
                }

                .logo-text::before,
                .logo-text::after {
                    display: none !important;
                }

                .close-button {
                    background: none; border: none; color: var(--text-secondary); cursor: pointer;
                    display: none;
                }
                 @media (max-width: 767px) {
                    .close-button { display: block; }
                }

                .sidebar-nav { flex-grow: 1; padding: 1rem 0; }
                .nav-item {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                    padding: 0.875rem 1.5rem;
                    margin: 0.25rem 0;
                    color: var(--text-secondary);
                    text-decoration: none;
                    font-weight: 500;
                    transition: all 0.2s ease;
                    position: relative;
                }
                .nav-item:hover {
                    background-color: var(--surface-color);
                    color: var(--text-primary);
                }
                .nav-item.active {
                    color: var(--text-primary);
                    font-weight: 600;
                }
                .nav-item.active::before {
                    content: '';
                    position: absolute;
                    left: 0;
                    top: 0;
                    height: 100%;
                    width: 3px;
                    background: var(--accent-glow);
                    box-shadow: 0 0 8px var(--accent-glow);
                }

                .sidebar-footer { padding: 1.5rem; border-top: 1px solid var(--border-color); }
                .user-profile { display: flex; align-items: center; gap: 0.75rem; cursor: pointer; }
                .user-profile img { border-radius: 50%; border: 1px solid var(--border-color); }
                .user-info { flex-grow: 1; }
                .user-info span { display: block; font-weight: 600; color: var(--text-primary); }
                .user-info small { color: var(--text-secondary); }
                
                .menu-button {
                    position: fixed; top: 20px; left: 20px; z-index: 101;
                    background: var(--glass-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    padding: 8px;
                    color: var(--text-primary);
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    backdrop-filter: blur(5px);
                }
                .app-container.sidebar-open .menu-button { display: none; }
                
                /* --- Content Styling --- */
                .page-title {
                    font-family: 'Chakra Petch', sans-serif;
                    font-size: 3rem;
                    font-weight: 700;
                    margin-bottom: 0.5rem;
                    color: var(--text-primary);
                }
                .page-subtitle { color: var(--text-secondary); margin-bottom: 2.5rem; font-size: 1.1rem; }
                
                .card {
                    background: var(--glass-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 1rem;
                    overflow: hidden;
                    backdrop-filter: blur(10px);
                    -webkit-backdrop-filter: blur(10px);
                    transition: transform 0.2s ease, box-shadow 0.2s ease;
                    cursor: pointer;
                }
                .card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
                }

                .card-header {
                    display: flex; justify-content: space-between; align-items: center;
                    padding: 1.5rem; border-bottom: 1px solid var(--border-color);
                }
                .card-header h2 { font-family: 'Chakra Petch', sans-serif; font-size: 1.25rem; font-weight: 600; }
                .card-content { padding: 1.5rem; }
                .card-content p { color: var(--text-secondary); line-height: 1.6; }

                /* --- Buttons --- */
                .btn-primary, .btn-secondary {
                    padding: 0.6rem 1.2rem; border-radius: 0.5rem; font-weight: 600;
                    cursor: pointer; transition: all 0.2s ease;
                    border: 1px solid var(--border-color); font-size: 0.875rem;
                    background: transparent;
                    color: var(--text-secondary);
                }
                .btn-primary { border-color: var(--text-primary); color: var(--text-primary); }
                .btn-primary:hover { background-color: var(--text-primary); color: var(--bg-color); }
                .btn-secondary:hover { color: var(--text-primary); border-color: var(--text-primary); }

                /* --- Dashboard Specific --- */
                .dashboard-grid {
                    display: grid; grid-template-columns: 1fr; gap: 1.5rem;
                }
                @media (min-width: 1024px) {
                    .dashboard-grid { grid-template-columns: 2fr 1fr; gap: 2rem; }
                }
                .table-wrapper { overflow-x: auto; }
                .data-table { width: 100%; border-collapse: collapse; min-width: 500px; }
                .data-table th, .data-table td {
                    padding: 1rem; text-align: left;
                    border-bottom: 1px solid var(--border-color);
                    font-size: 0.9rem;
                    color: var(--text-secondary);
                }
                .data-table td { color: var(--text-primary); }
                .data-table th { font-weight: 500; text-transform: uppercase; font-size: 0.75rem; }
                .data-table tr:last-child td { border-bottom: none; }
                
                .status-badge {
                    padding: 0.3rem 0.7rem; border-radius: 0.5rem;
                    font-weight: 600; font-size: 0.75rem;
                    display: inline-block;
                }
                .status-live { background-color: rgba(46, 204, 113, 0.1); color: var(--status-ok); }
                .status-error { background-color: rgba(231, 76, 60, 0.1); color: var(--status-error); }
                .vulnerability-count.has-issues { color: var(--status-warn); font-weight: 600; }

                .scan-list { list-style: none; display: flex; flex-direction: column; gap: 1.25rem; }
                .scan-item {
                    display: flex; justify-content: space-between; align-items: center;
                }
                .scan-info .scan-repo { font-weight: 500; color: var(--text-primary); }
                .scan-info .scan-time { font-size: 0.8rem; color: var(--text-secondary); display: block; margin-top: 0.25rem; }
                .scan-status { font-size: 0.85rem; font-weight: 500; }
                .scan-status.status-clean { color: var(--status-ok); }
                .scan-status.status-warnings { color: var(--status-warn); }
                .scan-status.status-failed { color: var(--status-error); }

                .placeholder-view { text-align: center; }
                .placeholder-view .card { margin-top: 2rem; text-align: left; max-width: 600px; margin-left: auto; margin-right: auto; }
            `}</style>
            
            <ThreeBackground />
            <Sidebar 
                isOpen={sidebarOpen} 
                toggleSidebar={toggleSidebar} 
                setView={setCurrentView} 
                currentView={currentView} 
            />
            
            {!sidebarOpen && (
                <button className="menu-button" onClick={toggleSidebar}>
                    <Menu size={24} />
                </button>
            )}

            <main className="main-content">
                {renderView()}
            </main>
        </div>
    );
}