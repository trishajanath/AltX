import React, { useEffect, useRef, useState } from 'react';
// Note: react-router-dom is used for navigation.
// Ensure this component is rendered within a <Router> from react-router-dom.
import { useNavigate } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

// --- Main Landing Page Component ---
const VexelLandingPage = () => {
    const mountRef = useRef(null);
    const navigate = useNavigate();
    const [threeLoaded, setThreeLoaded] = useState(false);
    const [effectsActive, setEffectsActive] = useState(false);
    const [blastOff, setBlastOff] = useState(false);
    const [activeButton, setActiveButton] = useState(null);
    const [performanceWarning, setPerformanceWarning] = useState(false);

    // Effect for the interactive 3D particle animation
    useEffect(() => {
        let scene, camera, renderer, particles, lines;
        let animationId;
        const mountNode = mountRef.current;
        let mouse, targetRotation;
        let performanceMode = false;

        // Adaptive particle count based on device capability
        const getOptimalParticleCount = () => {
            const isMobile = window.innerWidth < 768;
            if (isMobile) return 1500; // Lower count for mobile devices
            return 3000; // Higher count for desktops
        };

        const particleCount = getOptimalParticleCount();
        const positions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);
        const velocities = new Float32Array(particleCount * 3);

        const loadThreeJS = () => {
            return new Promise((resolve, reject) => {
                if (window.THREE) {
                    resolve();
                    return;
                }
                const script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
                script.onload = () => { setThreeLoaded(true); resolve(); };
                script.onerror = reject;
                document.head.appendChild(script);
            });
        };

        const init = async () => {
            if (!mountNode) return;

            try {
                await loadThreeJS();
                if (!window.THREE) { console.error("Three.js failed to load"); return; }

                mouse = new window.THREE.Vector2();
                targetRotation = new window.THREE.Vector2();

                scene = new window.THREE.Scene();

                camera = new window.THREE.PerspectiveCamera(75, mountNode.clientWidth / mountNode.clientHeight, 0.1, 1000);
                camera.position.z = 120; // Adjusted camera position for the visual effect

                renderer = new window.THREE.WebGLRenderer({
                    antialias: !window.innerWidth < 768,
                    alpha: true,
                    powerPreference: "high-performance",
                });
                renderer.setSize(mountNode.clientWidth, mountNode.clientHeight);
                renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
                renderer.setClearColor(0x000000, 0);
                mountNode.appendChild(renderer.domElement);

                // Particles shaped into the curved structure
                const colorAqua = new window.THREE.Color(0x00c0ff);
                const segments = 64;
                const rings = 128;
                let particleIndex = 0;

                for (let i = 0; i < particleCount; i++) {
                    const i3 = i * 3;
                    
                    // Create a large, curved, semi-toroidal shape
                    const ringRadius = 100;
                    const tubeRadius = 30;
                    const u = (i % segments / segments) * 2 * Math.PI;
                    const v = Math.floor(i / segments) / rings * Math.PI; // Only half a torus

                    const x = (ringRadius + tubeRadius * Math.cos(v)) * Math.cos(u);
                    const y = (ringRadius + tubeRadius * Math.cos(v)) * Math.sin(u);
                    const z = tubeRadius * Math.sin(v) - 50; // Offset to push it back

                    positions[i3] = x + (Math.random() - 0.5) * 5;
                    positions[i3 + 1] = y + (Math.random() - 0.5) * 5;
                    positions[i3 + 2] = z + (Math.random() - 0.5) * 5;

                    velocities[i3] = (Math.random() - 0.5) * 0.1;
                    velocities[i3 + 1] = (Math.random() - 0.5) * 0.1;
                    velocities[i3 + 2] = (Math.random() - 0.5) * 0.1;

                    colors[i3] = colorAqua.r;
                    colors[i3 + 1] = colorAqua.g;
                    colors[i3 + 2] = colorAqua.b;
                }

                const particleGeometry = new window.THREE.BufferGeometry();
                particleGeometry.setAttribute('position', new window.THREE.BufferAttribute(positions, 3));
                particleGeometry.setAttribute('color', new window.THREE.BufferAttribute(colors, 3));

                const particleMaterial = new window.THREE.PointsMaterial({
                    size: window.innerWidth < 768 ? 0.8 : 1.2,
                    vertexColors: true,
                    blending: window.THREE.AdditiveBlending,
                    transparent: true,
                    opacity: 0.9,
                    depthWrite: false,
                    sizeAttenuation: true
                });

                particles = new window.THREE.Points(particleGeometry, particleMaterial);
                particles.rotation.x = 0.5; // Tilt the structure
                scene.add(particles);

                window.addEventListener('resize', onWindowResize, false);
                window.addEventListener('mousemove', onMouseMove, false);
                setEffectsActive(true);
                animate();
            } catch (error) {
                console.error('Failed to initialize Three.js:', error);
                setEffectsActive(false);
            }
        };

        const onWindowResize = () => {
            if (!camera || !renderer || !mountNode) return;
            camera.aspect = mountNode.clientWidth / mountNode.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(mountNode.clientWidth, mountNode.clientHeight);
        };

        const onMouseMove = (event) => {
            if (mountNode) {
                mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
                mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
                targetRotation.x = mouse.y * 0.1;
                targetRotation.y = mouse.x * 0.1;
            }
        };

        let lastFrameTime = performance.now();
        const animate = () => {
            animationId = requestAnimationFrame(animate);

            const time = Date.now() * 0.0005;
            
            // Performance monitoring
            const frameTime = performance.now();
            const deltaTime = frameTime - lastFrameTime;
            lastFrameTime = frameTime;

            if (deltaTime > 33) { // Below 30 FPS
                if (!performanceMode) {
                    performanceMode = true;
                    setPerformanceWarning(true);
                }
            } else if (deltaTime < 20) { // Stable FPS
                if (performanceMode) {
                    performanceMode = false;
                    setPerformanceWarning(false);
                }
            }
            
            const posArray = particles.geometry.attributes.position.array;
            const colArray = particles.geometry.attributes.color.array;

            // Smooth rotation towards mouse target
            particles.rotation.y += (targetRotation.y - particles.rotation.y) * 0.05;
            particles.rotation.x += (targetRotation.x - particles.rotation.x) * 0.05;

            // Subtle wave motion
            for (let i = 0; i < particleCount; i++) {
                const i3 = i * 3;
                const x = posArray[i3];
                const y = posArray[i3 + 1];

                if (blastOff) {
                    posArray[i3] += velocities[i3] * 10.0;
                    posArray[i3 + 1] += velocities[i3 + 1] * 10.0;
                    posArray[i3 + 2] += velocities[i3 + 2] * 10.0;
                } else {
                     posArray[i3 + 2] += Math.sin(i * 0.1 + time * 3) * 0.05;
                }

                 // Glow effect
                const glow = Math.sin(i * 0.5 + time * 5) * 0.5 + 0.5;
                colArray[i3] = 0.0 * (1 - glow) + 1.0 * glow; // Interpolate from blue to white
                colArray[i3 + 1] = 0.75 * (1 - glow) + 1.0 * glow;
                colArray[i3 + 2] = 1.0 * (1 - glow) + 1.0 * glow;
            }

            particles.geometry.attributes.position.needsUpdate = true;
            particles.geometry.attributes.color.needsUpdate = true;
            
            particles.rotation.z += 0.0002; // Slow base rotation

            renderer.render(scene, camera);
        };

        init();

        return () => {
            cancelAnimationFrame(animationId);
            window.removeEventListener('resize', onWindowResize);
            window.removeEventListener('mousemove', onMouseMove);
            if (mountNode && renderer && renderer.domElement) {
                mountNode.removeChild(renderer.domElement);
            }
            if (renderer) renderer.dispose();
        };
    }, [blastOff]);

    const triggerBlastOff = (buttonId) => {
        setActiveButton(buttonId);
        setBlastOff(true);
        // Reset blast effect after animation
        setTimeout(() => {
            setBlastOff(false);
            setActiveButton(null);
        }, 1500);
    };
    
    const handleGetStarted = () => {
        triggerBlastOff('getstarted');
        setTimeout(() => navigate('/signup'), 800);
    };

    const handleExplore = () => {
        triggerBlastOff('explore');
        // Add scroll or navigation logic here
        setTimeout(() => {
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        }, 800);
    };


    return (
        <div className="vexel-container">
             <style>{`
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');

                .vexel-container {
                    font-family: 'Inter', sans-serif;
                    background: #000000;
                    color: #fff;
                    min-height: 100vh;
                    position: relative;
                    overflow: hidden;
                }

                .background-canvas {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: 0;
                }

                .page-content {
                    position: relative;
                    z-index: 10;
                    display: flex;
                    flex-direction: column;
                    min-height: 100vh;
                }


                .header {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    z-index: 50;
                    padding: 1.5rem 2.5rem;
                    display: grid;
                    grid-template-columns: 1fr auto 1fr; /* Three-column layout */
                    align-items: center;
                    width: 100%;
                    max-width: 1600px;
                    margin: 0 auto;
                    box-sizing: border-box;
                }


                .logo {
                    font-family: 'Chakra Petch', sans-serif;
                    font-size: 1.8rem;
                    font-weight: 700;
                    letter-spacing: 2px;
                    cursor: pointer;
                    color: #ffffffff !important;
                    text-shadow: none !important;
                    filter: none !important;
                    background: none !important;
                    background-color: transparent !important;
                    justify-self: start;
                    -webkit-text-fill-color: #ffffff !important;
                    -webkit-text-stroke: none !important;
                }

                .logo-text::before,
                .logo-text::after {
                    display: none !important;
                }

                .nav {
                    display: flex;
                    gap: 2.5rem;
                    justify-self: center;
                }
                
                .nav-link {
                    color: #a3a3a3;
                    text-decoration: none;
                    font-weight: 500;
                    transition: color 0.3s ease;
                    font-size: 0.9rem;
                }
                .nav-link:hover {
                    color: #fff;
                }
                .auth-buttons {
                    display: flex;
                    align-items: center;
                    gap: 1.5rem;
                    justify-self: end;
                }

                .btn-signin {
                    background: transparent;
                    border: none;
                    color: #a3a3a3;
                    cursor: pointer;
                    font-size: 0.9rem;
                    font-weight: 500;
                    transition: color 0.3s ease;
                }
                .btn-signin:hover {
                    color: #fff;
                }

                .btn-signup {
                    background: #fff;
                    color: #000;
                    border: 1px solid #fff;
                    padding: 0.6rem 1.2rem;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    font-size: 0.9rem;
                }
                .btn-signup:hover {
                    background: transparent;
                    color: #fff;
                }

                
                .main-content {
                    flex-grow: 1;
                    position: relative;
                    z-index: 2;
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    align-items: center;
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 8rem 2rem 2rem;
                    min-height: 100vh;
                }

                .hero-text {
                    text-align: left;
                }

                .hero-subtitle {
                    font-size: 0.9rem;
                    color: #a3a3a3;
                    font-weight: 500;
                    letter-spacing: 2px;
                    margin-bottom: 1rem;
                }

                .hero-title {
                    font-size: clamp(3rem, 7vw, 6rem);
                    font-weight: 700;
                    line-height: 1.1;
                    margin-bottom: 2rem;
                    letter-spacing: -2px;
                }
                
                .hero-description {
                    position: absolute;
                    bottom: 5rem;
                    right: 2rem;
                    max-width: 300px;
                    font-size: 0.9rem;
                    color: #a3a3a3;
                    line-height: 1.6;
                    text-align: right;
                }
                
                .action-buttons {
                    position: absolute;
                    bottom: 5rem;
                    left: 2rem;
                    display: flex;
                    flex-direction: column;
                    gap: 1rem;
                    align-items: flex-start;
                }

                .scroll-down {
                    font-size: 0.8rem;
                    color: #a3a3a3;
                    letter-spacing: 1px;
                    text-transform: uppercase;
                }

                .btn-explore {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    backdrop-filter: blur(5px);
                    color: #fff;
                    padding: 0.8rem 1.5rem;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                    transition: all 0.3s ease;
                }

                .btn-explore:hover {
                    background: #fff;
                    color: #000;
                }
                
                .btn-active {
                   border: 1px solid #00c0ff !important;
                   box-shadow: 0 0 20px rgba(0, 192, 255, 0.5) !important;
                }

                /* Responsive Design */


                @media (max-width: 768px) {
                    .header {
                        padding: 1.5rem 1rem;
                        grid-template-columns: 1fr 1fr;
                    }
                    .nav {
                        display: none;
                    }
                    .hero-title {
                        font-size: 2.5rem;
                    }
                }
            `}</style>

            <div ref={mountRef} className="background-canvas"></div>
            
            <header className="header">

                    <div className="logo">xVerta</div>
                    <nav className="nav">
                        <a href="#about" className="nav-link">ABOUT</a>
                        <a href="#features" className="nav-link">FEATURES</a>
                        <a href="#use-cases" className="nav-link">USE CASES</a>
                    </nav>
                    <div className="auth-buttons">
                        <button className="btn-signin" onClick={(e) => navigate('/login')}>Login</button>
                        <button className="btn-signup" onClick={(e) => navigate('/signup')}>Sign Up</button>
                    </div>
            </header>
            
            <main className="main-content">
                <div className="hero-text">
                    <div className="hero-subtitle">xVerta</div>
                    <h1 className="hero-title">Build safely with AI.</h1>
                </div>
            </main>

            <div className="hero-description">
                <p>
                    xVerta is an AI-powered platform that transforms your ideas into reality. 
                    Whether you're a developer, designer, or entrepreneur, xVerta helps you build 
                    and deploy projects with ease and confidence.
                </p>
            </div>
        </div>
    );
};

export default VexelLandingPage;