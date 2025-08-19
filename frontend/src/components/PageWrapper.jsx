import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import * as THREE from 'three';
import { BarChart3, Rocket, Shield, Menu, X, ChevronDown } from 'lucide-react';

// --- Sidebar Component (Updated) ---
const Sidebar = ({ isOpen, toggleSidebar }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const currentPath = location.pathname;
    const menuItems = [
        { icon: <BarChart3 size={20} />, title: 'Dashboard', path: '/home' },
        { icon: <Rocket size={20} />, title: 'Deploy Project', path: '/deploy' },
        { icon: <Shield size={20} />, title: 'Security Scan', path: '/security' },
        { icon: <BarChart3 size={20} />, title: 'Repo Analysis', path: '/repo-analysis' },
        { icon: <BarChart3 size={20} />, title: 'Reports', path: '/report' },
        { icon: <Rocket size={20} />, title: 'Build Apps', path: '/build' },
    ];
    return (
        <>
            <style>{`
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
                .sidebar {
                    width: 260px;
                    background: rgba(16, 16, 16, 0.6);
                    border-right: 1px solid rgba(255,255,255,0.15);
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
                }
                .sidebar-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 1.5rem;
                    border-bottom: 1px solid rgba(255,255,255,0.15);
                }
                .close-button {
                    background: none; border: none; color: #A0A0A0; cursor: pointer;
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
                    color: #A0A0A0;
                    text-decoration: none;
                    font-weight: 500;
                    transition: all 0.2s ease;
                    position: relative;
                }
                .nav-item:hover {
                    background-color: rgba(255,255,255,0.05);
                    color: #FFFFFF;
                }
                .nav-item.active {
                    color: #FFFFFF;
                    font-weight: 600;
                }
                .nav-item.active::before {
                    content: '';
                    position: absolute;
                    left: 0;
                    top: 0;
                    height: 100%;
                    width: 3px;
                    background: #FFFFFF;
                    box-shadow: 0 0 8px #FFFFFF;
                }
                .sidebar-footer { padding: 1.5rem; border-top: 1px solid rgba(255,255,255,0.15); }
                .user-profile { display: flex; align-items: center; gap: 0.75rem; cursor: pointer; }
                .user-profile img { border-radius: 50%; border: 1px solid rgba(255,255,255,0.15); }
                .user-info { flex-grow: 1; }
                .user-info span { display: block; font-weight: 600; color: #FFFFFF; }
                .user-info small { color: #A0A0A0; }
            `}</style>
            {isOpen && (
                <div className={`sidebar open`} style={{position: 'fixed', top: 0, left: 0, height: '100vh', width: 240, background: 'rgba(10,10,10,0.95)', zIndex: 100, boxShadow: '2px 0 16px rgba(0,0,0,0.12)'}}>
                    <div className="sidebar-header" style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem 1.2rem'}}>
                        <div className="logo-text">xVERTA</div>
                        <button className="close-button" onClick={toggleSidebar} style={{background: 'none', border: 'none', color: '#fff', cursor: 'pointer'}}>
                            <X size={24} />
                        </button>
                    </div>
                    <nav className="sidebar-nav" style={{display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '2rem'}}>
                        {menuItems.map(item => (
                            <a 
                                key={item.path}
                                href={item.path}
                                onClick={e => {
                                    e.preventDefault();
                                    navigate(item.path);
                                    toggleSidebar(); // Close sidebar on navigation
                                }}
                                style={{
                                    display: 'flex', alignItems: 'center', gap: 12, padding: '0.75rem 1.5rem', color: currentPath === item.path ? '#ffffffff' : '#fff', fontWeight: 600, textDecoration: 'none', borderRadius: 8, margin: '0 0.5rem', background: currentPath === item.path ? 'rgba(0,245,195,0.08)' : 'none', cursor: 'pointer', transition: 'background 0.2s',
                                }}
                            >
                                {item.icon}
                                <span>{item.title}</span>
                            </a>
                        ))}
                    </nav>
                    <div className="sidebar-footer" style={{ padding: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.15)' }}>
                        <div className="user-profile" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
                            <img src="https://placehold.co/40x40/000000/ffffff?text=A" alt="User Avatar" style={{ borderRadius: '50%', border: '1px solid rgba(255,255,255,0.15)' }} />
                            <div className="user-info" style={{ flexGrow: 1 }}>
                                <span style={{ display: 'block', fontWeight: 600, color: '#FFFFFF' }}>Admin User</span>
                                <small style={{ color: '#A0A0A0' }}>admin@securai.com</small>
                            </div>
                            <ChevronDown size={16} />
                        </div>
                    </div>
                </div>
            )}
            {!isOpen && (
                <button
                    className="menu-button"
                    style={{position: 'fixed', top: 20, left: 20, zIndex: 101, background: 'rgba(16,16,16,0.6)', border: '1px solid #A0A0A0', borderRadius: 8, padding: 8, color: '#fff', boxShadow: '0 2px 8px rgba(0,0,0,0.2)', cursor: 'pointer', display: 'flex', alignItems: 'center', backdropFilter: 'blur(5px)'}}
                    onClick={toggleSidebar}
                >
                    <Menu size={28} />
                </button>
            )}
        </>
    );
};

// --- ✨ UPDATED Vortex Three.js Background ---
const ThreeBackground = () => {
    const mountRef = useRef(null);

    useEffect(() => {
        if (!mountRef.current) return;

        let animationFrameId;
        const currentMount = mountRef.current;

        try {
            // --- Basic Scene Setup ---
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, currentMount.clientWidth / currentMount.clientHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            const clock = new THREE.Clock();
            renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            currentMount.appendChild(renderer.domElement);
            camera.position.z = 100;

            // --- Vortex Particles ---
            const particleCount = 50000; // Reduced particle count for subtlety and performance
            const positions = new Float32Array(particleCount * 3);
            const particleData = [];
            const maxRadius = 80;

            for (let i = 0; i < particleCount; i++) {
                const radius = Math.random() * maxRadius;
                const angle = Math.random() * Math.PI * 2;
                particleData.push({
                    radius: radius,
                    angle: angle,
                    // Drastically reduced the speed for a slower rotation
                    speed: (0.5 / (radius + 1)) * 0.1 + 0.0005,
                });
            }

            const particleGeometry = new THREE.BufferGeometry();
            particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

            const particleMaterial = new THREE.PointsMaterial({
                color: 0xffffff,
                size: 0.25, // Slightly smaller particle size
                blending: THREE.AdditiveBlending,
                transparent: true,
                opacity: 0.7, // Reduced opacity for a fainter look
                sizeAttenuation: true,
            });

            const vortex = new THREE.Points(particleGeometry, particleMaterial);
            scene.add(vortex);

            // --- Animation Loop ---
            const animate = () => {
                animationFrameId = requestAnimationFrame(animate);
                const elapsedTime = clock.getElapsedTime();
                const positions = vortex.geometry.attributes.position.array;

                for (let i = 0; i < particleCount; i++) {
                    const i3 = i * 3;
                    const data = particleData[i];

                    // Update angle for rotation
                    data.angle += data.speed;

                    // Greatly reduced the inward pull for a very slow drift
                    data.radius -= 0.01;

                    if (data.radius < 0.1) {
                        data.radius = maxRadius;
                        data.angle = Math.random() * Math.PI * 2;
                    }

                    // --- ✨ SUBTLE 3D PATTERN LOGIC ---
                    const spiralArms = 5;
                    const ringDensity = 0.5;
                    const waveSpeed = 0.2; // Significantly slowed down the wave evolution

                    // Reduced the amplitude (height) of the waves
                    const armWave = Math.sin(data.angle * spiralArms + elapsedTime * waveSpeed) * 1.5;
                    const ringWave = Math.sin(data.radius * ringDensity - elapsedTime * waveSpeed) * 2;
                    const finalY = armWave + ringWave;

                    // Update the particle's X, Y, and Z position
                    positions[i3] = Math.cos(data.angle) * data.radius;
                    positions[i3 + 1] = finalY;
                    positions[i3 + 2] = Math.sin(data.angle) * data.radius;
                }

                vortex.geometry.attributes.position.needsUpdate = true;
                renderer.render(scene, camera);
            };

            animate();

            // --- Handle Window Resizing ---
            const handleResize = () => {
                if (currentMount) {
                    camera.aspect = currentMount.clientWidth / currentMount.clientHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
                }
            };
            window.addEventListener('resize', handleResize);

            // --- Cleanup on Unmount ---
            return () => {
                window.removeEventListener('resize', handleResize);
                cancelAnimationFrame(animationFrameId);
                if (currentMount && renderer.domElement) {
                    try {
                        currentMount.removeChild(renderer.domElement);
                    } catch (e) {
                        // ignore error
                    }
                }
            };
        } catch (error) {
            console.error("Failed to initialize 3D background:", error);
        }
    }, []);

    return <div ref={mountRef} style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', zIndex: -1, background: '#000', pointerEvents: 'none' }} />;
};

// --- Shared Page Wrapper Component (Unchanged) ---
const PageWrapper = ({ children }) => {
    const [isSidebarOpen, setSidebarOpen] = useState(false);
    const location = useLocation();
    const toggleSidebar = () => setSidebarOpen(!isSidebarOpen);

    // Hide sidebar on /login and /signup
    const hideSidebar = location.pathname === '/login' || location.pathname === '/signup';

    return (
        <>
            <style>
                {`
                    /* --- Global Styles & Variables --- */
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
                    @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@700&display=swap');
                    :root {
                        --primary-green: #00f5c3;
                        --text-light: #f8fafc;
                        --text-dark: #94a3b8;
                        --bg-dark: #000000;
                        --card-bg: rgba(0, 0, 0, 0.3);
                        --card-bg-hover: rgba(0, 0, 0, 0.5);
                        --card-border: rgba(0, 245, 195, 0.2);
                        --card-border-hover: rgba(0, 245, 195, 0.5);
                    }
                    /* ... (rest of your CSS) ... */
                `}
            </style>
            <main className="main-app">
                <ThreeBackground />
                {!hideSidebar && <Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />}
                <div className="relative" style={{position: 'relative', zIndex: 1}}>
                    {children}
                </div>
            </main>
        </>
    );
};

export default PageWrapper;