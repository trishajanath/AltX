import React, { useEffect, useRef, useState } from 'react';
// Note: react-router-dom is used for navigation.
// Ensure this component is rendered within a <Router> from react-router-dom.
import { useNavigate } from 'react-router-dom';
import { ChevronRight, ChevronDown } from 'lucide-react';

// --- Main Landing Page Component ---
const VexelLandingPage = () => {
    const mountRef = useRef(null);
    const navigate = useNavigate();
    const [threeLoaded, setThreeLoaded] = useState(false);
    const [effectsActive, setEffectsActive] = useState(false);
    const [blastOff, setBlastOff] = useState(false);
    const [activeButton, setActiveButton] = useState(null);
    const [performanceWarning, setPerformanceWarning] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [activeDropdown, setActiveDropdown] = useState(null);

    // Navigation menu items
    const navigationItems = {
        platform: {
            title: 'Platform',
            items: [
                { title: 'Voice Development', description: 'Build applications using natural language and voice commands', action: () => handleNavClick('about') },
                { title: 'AI Code Generation', description: 'Intelligent code generation with modern frameworks', action: () => handleNavClick('features') },
                { title: 'Testing & Validation', description: 'Comprehensive validation and quality assurance', action: () => handleNavClick('features') },
                { title: 'Cloud Deployment', description: 'Seamless deployment to major cloud platforms', action: () => handleNavClick('features') }
            ]
        },
        solutions: {
            title: 'Solutions',
            items: [
                { title: 'E-Commerce Platforms', description: 'Complete online stores with payment processing', action: () => handleNavClick('use-cases') },
                { title: 'SaaS Applications', description: 'Project management and collaboration tools', action: () => handleNavClick('use-cases') },
                { title: 'Mobile Applications', description: 'Cross-platform mobile apps with offline capabilities', action: () => handleNavClick('use-cases') },
                { title: 'Data Analytics', description: 'Business intelligence dashboards and reporting', action: () => handleNavClick('use-cases') }
            ]
        }
    };

    // Handle OAuth callback if user lands on root with auth params
    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const authStatus = urlParams.get('auth');
        const userEmail = urlParams.get('user');
        
        if (authStatus === 'success' && userEmail) {
            // Store auth info and redirect to home
            const userName = urlParams.get('name');
            const userAvatar = urlParams.get('avatar');
            
            const userInfo = {
                email: userEmail,
                name: userName || 'User',
                avatar: userAvatar || '',
                authenticatedAt: new Date().toISOString()
            };
            
            localStorage.setItem('user', JSON.stringify(userInfo));
            localStorage.setItem('isAuthenticated', 'true');
            
            // Redirect to homepage
            navigate('/home');
        } else if (urlParams.get('error')) {
            console.error('Authentication error:', urlParams.get('error'));
            // Clean URL
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }, [navigate]);

    // Close dropdowns when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (!event.target.closest('.nav-item')) {
                setActiveDropdown(null);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    // Force logo and navbar to correct colors after component mounts
    useEffect(() => {
        const forceColors = () => {
            // Force logo to be white - specifically override App.css gradient
            const logoElement = document.querySelector('.logo');
            if (logoElement) {
                // Remove any gradient background completely
                logoElement.style.setProperty('background', 'none', 'important');
                logoElement.style.setProperty('background-image', 'none', 'important');
                logoElement.style.setProperty('background-clip', 'initial', 'important');
                logoElement.style.setProperty('-webkit-background-clip', 'initial', 'important');
                logoElement.style.setProperty('background-size', 'auto', 'important');
                logoElement.style.setProperty('-webkit-text-fill-color', '#ffffff', 'important');
                logoElement.style.setProperty('color', '#ffffff', 'important');
                logoElement.style.setProperty('text-shadow', 'none', 'important');
                logoElement.style.setProperty('filter', 'none', 'important');
            }

            // Force ALL navigation elements to gray - be extremely aggressive
            const allNavElements = document.querySelectorAll('.nav-link, .header button, .header a, button');
            allNavElements.forEach(element => {
                // Skip logo and active elements
                if (!element.classList.contains('logo') && !element.classList.contains('active')) {
                    // Remove any gradient styling
                    element.style.setProperty('background', 'transparent', 'important');
                    element.style.setProperty('background-image', 'none', 'important');
                    element.style.setProperty('background-clip', 'initial', 'important');
                    element.style.setProperty('-webkit-background-clip', 'initial', 'important');
                    element.style.setProperty('-webkit-text-fill-color', '#a3a3a3', 'important');
                    element.style.setProperty('color', '#a3a3a3', 'important');
                    element.style.setProperty('text-shadow', 'none', 'important');
                    element.style.setProperty('filter', 'none', 'important');
                    element.style.setProperty('text-decoration', 'none', 'important');
                    element.style.setProperty('transform', 'none', 'important');
                    element.style.setProperty('box-sizing', 'border-box', 'important');
                }
            });

            // Also target auth buttons specifically
            const authButtons = document.querySelectorAll('.btn-signin, .btn-signup');
            authButtons.forEach(button => {
                button.style.setProperty('background', 'transparent', 'important');
                button.style.setProperty('background-image', 'none', 'important');
                button.style.setProperty('background-clip', 'initial', 'important');
                button.style.setProperty('-webkit-background-clip', 'initial', 'important');
                button.style.setProperty('-webkit-text-fill-color', '#a3a3a3', 'important');
                button.style.setProperty('color', '#a3a3a3', 'important');
                button.style.setProperty('text-shadow', 'none', 'important');
                button.style.setProperty('filter', 'none', 'important');
            });
        };

        // Force colors immediately and on any changes
        forceColors();
        const interval = setInterval(forceColors, 50); // More frequent updates

        return () => clearInterval(interval);
    }, []);

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
                const colorGray = new window.THREE.Color(0xa3a3a3);
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

                    colors[i3] = colorGray.r;
                    colors[i3 + 1] = colorGray.g;
                    colors[i3 + 2] = colorGray.b;
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
                colArray[i3] = 0.64 * (1 - glow) + 1.0 * glow; // Interpolate from gray to white
                colArray[i3 + 1] = 0.64 * (1 - glow) + 1.0 * glow;
                colArray[i3 + 2] = 0.64 * (1 - glow) + 1.0 * glow;
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
        setTimeout(() => {
            const aboutSection = document.getElementById('about');
            if (aboutSection) {
                aboutSection.scrollIntoView({ behavior: 'smooth' });
            }
        }, 800);
    };

    const handleNavClick = (sectionId) => {
        const section = document.getElementById(sectionId);
        if (section) {
            section.scrollIntoView({ behavior: 'smooth' });
        }
        setMobileMenuOpen(false); // Close mobile menu after navigation
    };

    const toggleMobileMenu = () => {
        setMobileMenuOpen(!mobileMenuOpen);
    };

    const handleDropdownToggle = (dropdownName) => {
        setActiveDropdown(activeDropdown === dropdownName ? null : dropdownName);
    };

    const handleDropdownItemClick = (action) => {
        action();
        setActiveDropdown(null);
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
                
                /* Override any external CSS that might be coloring text */
                .vexel-container * {
                    -webkit-text-fill-color: initial !important;
                    background-clip: initial !important;
                    -webkit-background-clip: initial !important;
                }

                /* Nuclear override for ALL elements in header to prevent gradient */
                .vexel-container .header *,
                .header *,
                .nav *,
                .nav-item *,
                .auth-buttons * {
                    background: none !important;
                    background-image: none !important;
                    background-clip: initial !important;
                    -webkit-background-clip: initial !important;
                    -webkit-text-fill-color: inherit !important;
                    transform: none !important;
                    box-sizing: border-box !important;
                }
                
                /* Force logo to be white - nuclear option - override App.css gradient */
                .vexel-container .logo,
                .header .logo,
                .header-content .logo,
                div.logo,
                [class*="logo"] {
                    color: #ffffff !important;
                    -webkit-text-fill-color: #ffffff !important;
                    background: none !important;
                    background-image: none !important;
                    background-clip: border-box !important;
                    -webkit-background-clip: border-box !important;
                    text-shadow: none !important;
                    filter: none !important;
                    text-stroke: none !important;
                    -webkit-text-stroke: none !important;
                    /* Specifically override the gradient from App.css */
                    background-size: auto !important;
                    -webkit-text-fill-color: #ffffff !important;
                }

                /* Force navbar links to be gray - nuclear option - override index.css */
                .vexel-container .nav-link,
                .header .nav-link,
                .nav .nav-link,
                button.nav-link,
                [class*="nav-link"],
                .vexel-container a,
                .header a {
                    color: #a3a3a3 !important;
                    -webkit-text-fill-color: #a3a3a3 !important;
                    background: transparent !important;
                    background-image: none !important;
                    background-clip: border-box !important;
                    -webkit-background-clip: border-box !important;
                    text-shadow: none !important;
                    filter: none !important;
                    text-stroke: none !important;
                    -webkit-text-stroke: none !important;
                    text-decoration: none !important;
                }

                /* Force auth buttons to be gray - nuclear option */
                .vexel-container .btn-signin,
                .vexel-container .btn-signup,
                .header .btn-signin,
                .header .btn-signup,
                button.btn-signin,
                button.btn-signup,
                [class*="btn-signin"],
                [class*="btn-signup"] {
                    color: #a3a3a3 !important;
                    -webkit-text-fill-color: #a3a3a3 !important;
                    background: transparent !important;
                    background-image: none !important;
                    background-clip: initial !important;
                    -webkit-background-clip: initial !important;
                    text-shadow: none !important;
                    filter: none !important;
                    text-stroke: none !important;
                    -webkit-text-stroke: none !important;
                }
                
                /* Override any potential gradient text effects */
                .logo::before,
                .logo::after {
                    display: none !important;
                    content: none !important;
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
                    padding: 1rem 0;
                    background: rgba(0, 0, 0, 0.8);
                    backdrop-filter: blur(10px);
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }

                .header-content {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 0 2rem;
                }


                .logo {
                    font-family: 'Inter', sans-serif !important;
                    font-size: 1.5rem !important;
                    font-weight: 700 !important;
                    letter-spacing: 1px !important;
                    cursor: pointer !important;
                    color: #ffffff !important;
                    transition: color 0.3s ease !important;
                    text-decoration: none !important;
                    background: transparent !important;
                    background-image: none !important;
                    background-clip: initial !important;
                    -webkit-background-clip: initial !important;
                    -webkit-text-fill-color: #ffffff !important;
                    -webkit-text-stroke: none !important;
                    text-shadow: none !important;
                    filter: none !important;
                }

                .logo:hover,
                .logo:focus,
                .logo:active,
                .logo:visited {
                    color: #ffffff !important;
                    -webkit-text-fill-color: #ffffff !important;
                    background: transparent !important;
                    background-image: none !important;
                    text-shadow: none !important;
                    filter: none !important;
                }

                .logo-text::before,
                .logo-text::after {
                    display: none !important;
                }

                .nav {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                }
                
                .nav-item {
                    position: relative;
                }
                
                .nav-link {
                    background: transparent !important;
                    background-image: none !important;
                    background-clip: initial !important;
                    -webkit-background-clip: initial !important;
                    border: none;
                    color: #a3a3a3 !important;
                    -webkit-text-fill-color: #a3a3a3 !important;
                    text-decoration: none;
                    font-weight: 500;
                    transition: color 0.3s ease, background-color 0.3s ease;
                    font-size: 0.9rem;
                    padding: 0.5rem 1rem;
                    border-radius: 6px;
                    cursor: pointer;
                    font-family: inherit;
                    position: relative;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    box-sizing: border-box !important;
                    min-height: 36px;
                    text-shadow: none !important;
                    filter: none !important;
                }
                .nav-link:hover {
                    color: #ffffff !important;
                    background: rgba(255, 255, 255, 0.05) !important;
                    -webkit-text-fill-color: #ffffff !important;
                    background-image: none !important;
                    background-clip: border-box !important;
                    -webkit-background-clip: border-box !important;
                    transform: none !important;
                    box-sizing: border-box !important;
                }

                .nav-link:active {
                    transform: translateY(1px);
                }

                .nav-link.active {
                    color: #ffffff !important;
                    background: rgba(255, 255, 255, 0.05) !important;
                }

                .dropdown-menu {
                    position: absolute;
                    top: 100%;
                    left: 0;
                    min-width: 320px;
                    background: rgba(0, 0, 0, 0.95);
                    backdrop-filter: blur(20px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    padding: 1rem;
                    margin-top: 0.5rem;
                    opacity: 0;
                    visibility: hidden;
                    transform: translateY(-10px);
                    transition: all 0.3s ease;
                    z-index: 100;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                }

                .dropdown-menu.open {
                    opacity: 1;
                    visibility: visible;
                    transform: translateY(0);
                }

                .dropdown-grid {
                    display: grid;
                    gap: 0.5rem;
                }

                .dropdown-item {
                    padding: 0.75rem;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    border: 1px solid transparent;
                }

                .dropdown-item:hover {
                    background: rgba(255, 255, 255, 0.05) !important;
                    border-color: rgba(255, 255, 255, 0.1) !important;
                }
                
                .dropdown-item:hover .dropdown-item-title {
                    color: #ffffff !important;
                }

                .dropdown-item-title {
                    font-size: 0.9rem;
                    font-weight: 600;
                    color: #ffffff !important;
                    margin-bottom: 0.25rem;
                }

                .dropdown-item-description {
                    font-size: 0.8rem;
                    color: #a3a3a3;
                    line-height: 1.4;
                }

                .chevron-icon {
                    width: 16px;
                    height: 16px;
                    transition: transform 0.3s ease;
                }

                .nav-link.active .chevron-icon {
                    transform: rotate(180deg);
                }

                .mobile-menu-toggle {
                    display: none;
                    background: transparent;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: #a3a3a3;
                    padding: 0.5rem;
                    border-radius: 6px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }

                .mobile-menu-toggle:hover {
                    color: #ffffff !important;
                    border-color: rgba(255, 255, 255, 0.5) !important;
                }

                .mobile-menu {
                    display: none;
                    position: fixed;
                    top: 70px;
                    left: 0;
                    right: 0;
                    background: rgba(0, 0, 0, 0.95);
                    backdrop-filter: blur(10px);
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                    padding: 1rem;
                    z-index: 49;
                }

                .mobile-menu.open {
                    display: block;
                }

                .mobile-nav {
                    display: flex;
                    flex-direction: column;
                    gap: 1rem;
                    margin-bottom: 1rem;
                }

                .mobile-nav .nav-link {
                    text-align: left;
                    padding: 0.8rem 1rem;
                    border-radius: 8px;
                }

                .mobile-auth-buttons {
                    display: flex;
                    flex-direction: column;
                    gap: 0.8rem;
                    padding-top: 1rem;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                }

                .mobile-auth-buttons .btn-signin,
                .mobile-auth-buttons .btn-signup {
                    width: 100%;
                    text-align: center;
                    padding: 0.8rem 1rem;
                }

                .mobile-nav-section {
                    margin-bottom: 1.5rem;
                }

                .mobile-nav-section-title {
                    font-size: 0.8rem;
                    font-weight: 600;
                    color: #fff;
                    margin-bottom: 0.8rem;
                    padding: 0 1rem;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }

                .mobile-nav-item {
                    width: 100%;
                    background: transparent;
                    border: none;
                    color: #a3a3a3;
                    padding: 0.8rem 1rem;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    text-align: left;
                    margin-bottom: 0.5rem;
                    border: 1px solid transparent;
                }

                .mobile-nav-item:hover {
                    background: rgba(255, 255, 255, 0.05);
                    border-color: rgba(255, 255, 255, 0.1);
                }

                .mobile-nav-item-title {
                    font-size: 0.9rem;
                    font-weight: 600;
                    color: #fff;
                    margin-bottom: 0.25rem;
                }

                .mobile-nav-item-description {
                    font-size: 0.8rem;
                    color: #a3a3a3;
                    line-height: 1.3;
                }
                .auth-buttons {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                }

                .btn-signin {
                    background: transparent;
                    border: 1px solid transparent;
                    color: #a3a3a3;
                    cursor: pointer;
                    font-size: 0.9rem;
                    font-weight: 500;
                    padding: 0.5rem 1rem;
                    border-radius: 6px;
                    transition: all 0.3s ease;
                    font-family: inherit;
                }
                .btn-signin:hover {
                    color: #ffffff !important;
                    background: rgba(255, 255, 255, 0.05) !important;
                }

                .btn-signup {
                    background: transparent;
                    color: #a3a3a3;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    padding: 0.5rem 1rem;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    font-size: 0.9rem;
                    font-family: inherit;
                }
                .btn-signup:hover {
                    color: #ffffff !important;
                    border-color: rgba(255, 255, 255, 0.5) !important;
                    background: rgba(255, 255, 255, 0.05) !important;
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
                    background: transparent;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: #a3a3a3;
                    padding: 0.8rem 1.5rem;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                    transition: all 0.3s ease;
                }

                .btn-explore:hover {
                    color: #ffffff !important;
                    border-color: rgba(255, 255, 255, 0.5) !important;
                }
                
                .btn-active {
                   color: #ffffff !important;
                   border-color: rgba(255, 255, 255, 0.5) !important;
                }

                /* Responsive Design */


                /* Sections */
                .section {
                    position: relative;
                    z-index: 10;
                    padding: 6rem 0;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                }

                .section-content {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 0 2rem;
                }

                .section-header {
                    text-align: center;
                    margin-bottom: 4rem;
                }

                .section-title {
                    font-size: clamp(2.5rem, 5vw, 4rem);
                    font-weight: 700;
                    line-height: 1.2;
                    margin-bottom: 1.5rem;
                    letter-spacing: -1px;
                }

                .section-subtitle {
                    font-size: 1.1rem;
                    color: #a3a3a3;
                    line-height: 1.6;
                    max-width: 600px;
                    margin: 0 auto;
                }

                /* Features Grid */
                .features-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 2.5rem;
                    margin-top: 4rem;
                }

                .feature-card {
                    padding: 2.5rem;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 12px;
                    transition: all 0.3s ease;
                }

                .feature-card:hover {
                    background: rgba(255, 255, 255, 0.05);
                    border-color: rgba(255, 255, 255, 0.15);
                    transform: translateY(-2px);
                }

                .feature-icon {
                    color: #a3a3a3;
                    margin-bottom: 1.5rem;
                }

                .feature-title {
                    font-size: 1.3rem;
                    font-weight: 600;
                    margin-bottom: 1rem;
                    color: #fff;
                }

                .feature-description {
                    color: #a3a3a3;
                    line-height: 1.6;
                }

                /* Capabilities List */
                .capabilities-list {
                    display: flex;
                    flex-direction: column;
                    gap: 3rem;
                    margin-top: 4rem;
                }

                .capability-item {
                    display: flex;
                    align-items: flex-start;
                    gap: 2rem;
                    padding: 2rem 0;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }

                .capability-item:last-child {
                    border-bottom: none;
                }

                .capability-number {
                    font-size: 3rem;
                    font-weight: 700;
                    color: #a3a3a3;
                    line-height: 1;
                    min-width: 80px;
                }

                .capability-content {
                    flex: 1;
                }

                .capability-title {
                    font-size: 1.5rem;
                    font-weight: 600;
                    margin-bottom: 1rem;
                    color: #fff;
                }

                .capability-description {
                    color: #a3a3a3;
                    line-height: 1.6;
                    font-size: 1rem;
                }

                /* Use Cases Grid */
                .use-cases-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: 2rem;
                    margin-top: 4rem;
                }

                .use-case-card {
                    padding: 2rem;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 12px;
                    transition: all 0.3s ease;
                }

                .use-case-card:hover {
                    background: rgba(255, 255, 255, 0.05);
                    border-color: rgba(255, 255, 255, 0.15);
                }

                .use-case-title {
                    font-size: 1.2rem;
                    font-weight: 600;
                    margin-bottom: 1rem;
                    color: #fff;
                }

                .use-case-description {
                    color: #a3a3a3;
                    line-height: 1.6;
                    margin-bottom: 1.5rem;
                    font-style: italic;
                }

                .use-case-tech {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                }

                .tech-tag {
                    background: rgba(255, 255, 255, 0.05);
                    color: #a3a3a3;
                    padding: 0.3rem 0.8rem;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    font-weight: 500;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }

                /* CTA Section */
                .cta-section {
                    background: rgba(255, 255, 255, 0.02);
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }

                .cta-content {
                    text-align: center;
                    max-width: 600px;
                    margin: 0 auto;
                }

                .cta-title {
                    font-size: clamp(2rem, 4vw, 3rem);
                    font-weight: 700;
                    margin-bottom: 1.5rem;
                    color: #fff;
                }

                .cta-description {
                    font-size: 1.1rem;
                    color: #a3a3a3;
                    line-height: 1.6;
                    margin-bottom: 2.5rem;
                }

                .btn-cta {
                    background: transparent;
                    color: #a3a3a3;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    padding: 1rem 2.5rem;
                    border-radius: 8px;
                    font-size: 1rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    display: inline-flex;
                    align-items: center;
                    gap: 0.5rem;
                }

                .btn-cta:hover {
                    color: #ffffff !important;
                    border-color: rgba(255, 255, 255, 0.5) !important;
                }

                .btn-icon {
                    width: 20px;
                    height: 20px;
                }

                /* Footer */
                .footer {
                    background: rgba(255, 255, 255, 0.02);
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                    position: relative;
                    z-index: 10;
                }

                .footer-content {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 4rem 2rem 2rem;
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 3rem;
                }

                .footer-section {
                    display: flex;
                    flex-direction: column;
                }

                .footer-title {
                    font-size: 1rem;
                    font-weight: 600;
                    margin-bottom: 1.5rem;
                    color: #fff;
                }

                .footer-description {
                    color: #a3a3a3;
                    line-height: 1.6;
                    margin-top: 1rem;
                }

                .footer-links {
                    display: flex;
                    flex-direction: column;
                    gap: 0.8rem;
                }

                .footer-link {
                    color: #a3a3a3;
                    text-decoration: none;
                    transition: color 0.3s ease;
                    font-size: 0.9rem;
                }

                .footer-link:hover {
                    color: #fff;
                }

                .footer-bottom {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 2rem;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    color: #a3a3a3;
                    font-size: 0.9rem;
                }

                .footer-bottom-links {
                    display: flex;
                    gap: 2rem;
                }

                .footer-bottom-link {
                    color: #a3a3a3;
                    text-decoration: none;
                    transition: color 0.3s ease;
                }

                .footer-bottom-link:hover {
                    color: #fff;
                }

                /* Performance Warning */
                .performance-warning {
                    position: fixed;
                    top: 1rem;
                    right: 1rem;
                    background: rgba(255, 255, 255, 0.1);
                    color: #a3a3a3;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    padding: 0.5rem 1rem;
                    border-radius: 6px;
                    font-size: 0.8rem;
                    z-index: 100;
                    backdrop-filter: blur(5px);
                }

                /* Responsive Design */
                @media (max-width: 1024px) {
                    .main-content {
                        grid-template-columns: 1fr;
                        text-align: center;
                        padding: 6rem 2rem 2rem;
                    }
                    
                    .hero-description {
                        position: static;
                        max-width: none;
                        text-align: center;
                        margin: 2rem 0;
                    }
                    
                    .action-buttons {
                        position: static;
                        align-items: center;
                        margin: 2rem 0;
                    }
                }

                @media (max-width: 768px) {
                    .header {
                        padding: 0.8rem 0;
                    }
                    
                    .header-content {
                        padding: 0 1rem;
                    }
                    
                    .nav {
                        display: none;
                    }
                    
                    .mobile-menu-toggle {
                        display: block;
                    }
                    
                    .logo {
                        font-size: 1.3rem;
                    }
                    
                    .auth-buttons {
                        gap: 0.5rem;
                    }
                    
                    .btn-signin, .btn-signup {
                        padding: 0.4rem 0.8rem;
                        font-size: 0.8rem;
                    }
                    
                    .hero-title {
                        font-size: 2.5rem;
                    }
                    
                    .section {
                        padding: 4rem 0;
                    }
                    
                    .section-content {
                        padding: 0 1rem;
                    }
                    
                    .features-grid {
                        grid-template-columns: 1fr;
                        gap: 2rem;
                    }
                    
                    .capability-item {
                        flex-direction: column;
                        gap: 1rem;
                        text-align: center;
                    }
                    
                    .capability-number {
                        min-width: auto;
                    }
                    
                    .use-cases-grid {
                        grid-template-columns: 1fr;
                    }
                    
                    .footer-content {
                        grid-template-columns: 1fr;
                        gap: 2rem;
                        text-align: center;
                    }
                    
                    .footer-bottom {
                        flex-direction: column;
                        gap: 1rem;
                        text-align: center;
                    }
                }
            `}</style>

            <div ref={mountRef} className="background-canvas"></div>
            
            {performanceWarning && (
                <div className="performance-warning">
                    Performance mode activated - reduced effects for better performance
                </div>
            )}
            
            <header className="header">
                <div className="header-content">
                    <div className="logo" style={{ color: '#ffffff !important', WebkitTextFillColor: '#ffffff !important', background: 'transparent !important' }}>XVERTA</div>
                    <nav className="nav">
                        {/* Platform Dropdown */}
                        <div className="nav-item">
                            <button 
                                className={`nav-link ${activeDropdown === 'platform' ? 'active' : ''}`}
                                onClick={() => handleDropdownToggle('platform')}
                            >
                                Platform
                                <ChevronDown className="chevron-icon" />
                            </button>
                            <div className={`dropdown-menu ${activeDropdown === 'platform' ? 'open' : ''}`}>
                                <div className="dropdown-grid">
                                    {navigationItems.platform.items.map((item, index) => (
                                        <div 
                                            key={index}
                                            className="dropdown-item"
                                            onClick={() => handleDropdownItemClick(item.action)}
                                        >
                                            <div className="dropdown-item-title">{item.title}</div>
                                            <div className="dropdown-item-description">{item.description}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Solutions Dropdown */}
                        <div className="nav-item">
                            <button 
                                className={`nav-link ${activeDropdown === 'solutions' ? 'active' : ''}`}
                                onClick={() => handleDropdownToggle('solutions')}
                            >
                                Solutions
                                <ChevronDown className="chevron-icon" />
                            </button>
                            <div className={`dropdown-menu ${activeDropdown === 'solutions' ? 'open' : ''}`}>
                                <div className="dropdown-grid">
                                    {navigationItems.solutions.items.map((item, index) => (
                                        <div 
                                            key={index}
                                            className="dropdown-item"
                                            onClick={() => handleDropdownItemClick(item.action)}
                                        >
                                            <div className="dropdown-item-title">{item.title}</div>
                                            <div className="dropdown-item-description">{item.description}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Direct Links */}
                        <button className="nav-link" onClick={() => handleNavClick('about')}>About</button>
                        <button className="nav-link" onClick={() => handleNavClick('features')}>Documentation</button>
                    </nav>
                    <div className="auth-buttons">
                        <button className="btn-signin" onClick={() => navigate('/login')}>Login</button>
                        <button className="btn-signup" onClick={() => navigate('/signup')}>Sign Up</button>
                    </div>
                    <button className="mobile-menu-toggle" onClick={toggleMobileMenu}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="3" y1="6" x2="21" y2="6"></line>
                            <line x1="3" y1="12" x2="21" y2="12"></line>
                            <line x1="3" y1="18" x2="21" y2="18"></line>
                        </svg>
                    </button>
                </div>
            </header>

            {/* Mobile Menu */}
            <div className={`mobile-menu ${mobileMenuOpen ? 'open' : ''}`}>
                <nav className="mobile-nav">
                    {/* Platform Section */}
                    <div className="mobile-nav-section">
                        <div className="mobile-nav-section-title">Platform</div>
                        {navigationItems.platform.items.map((item, index) => (
                            <button 
                                key={index}
                                className="mobile-nav-item"
                                onClick={() => {
                                    item.action();
                                    setMobileMenuOpen(false);
                                }}
                            >
                                <div className="mobile-nav-item-title">{item.title}</div>
                                <div className="mobile-nav-item-description">{item.description}</div>
                            </button>
                        ))}
                    </div>

                    {/* Solutions Section */}
                    <div className="mobile-nav-section">
                        <div className="mobile-nav-section-title">Solutions</div>
                        {navigationItems.solutions.items.map((item, index) => (
                            <button 
                                key={index}
                                className="mobile-nav-item"
                                onClick={() => {
                                    item.action();
                                    setMobileMenuOpen(false);
                                }}
                            >
                                <div className="mobile-nav-item-title">{item.title}</div>
                                <div className="mobile-nav-item-description">{item.description}</div>
                            </button>
                        ))}
                    </div>

                    {/* Direct Links */}
                    <div className="mobile-nav-section">
                        <button className="nav-link" onClick={() => handleNavClick('about')}>About</button>
                        <button className="nav-link" onClick={() => handleNavClick('features')}>Documentation</button>
                    </div>
                </nav>
                <div className="mobile-auth-buttons">
                    <button className="btn-signin" onClick={() => navigate('/login')}>Login</button>
                    <button className="btn-signup" onClick={() => navigate('/signup')}>Sign Up</button>
                </div>
            </div>
            
            <main className="main-content">
                <div className="hero-text">
                    <div className="hero-subtitle">AI-POWERED DEVELOPMENT</div>
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

            <div className="action-buttons">
                <div className="scroll-down">Scroll to explore</div>
                <button 
                    className={`btn-explore ${activeButton === 'explore' ? 'btn-active' : ''}`}
                    onClick={handleExplore}
                >
                    Explore Platform
                </button>
            </div>

            {/* About Section */}
            <section id="about" className="section about-section">
                <div className="section-content">
                    <div className="section-header">
                        <h2 className="section-title">Revolutionary Voice-Powered Development</h2>
                        <p className="section-subtitle">
                            Transform your ideas into fully functional applications using natural language and voice commands.
                        </p>
                    </div>
                    
                    <div className="features-grid">
                        <div className="feature-card">
                            <div className="feature-icon">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M12 1L21.5 7v10L12 23 2.5 17V7L12 1z"/>
                                    <path d="M12 8v8"/>
                                    <path d="M8 12h8"/>
                                </svg>
                            </div>
                            <h3 className="feature-title">Voice-First Development</h3>
                            <p className="feature-description">
                                Describe your application requirements using natural speech. Our AI understands context, 
                                requirements, and technical specifications from conversational input.
                            </p>
                        </div>
                        
                        <div className="feature-card">
                            <div className="feature-icon">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                    <circle cx="8.5" cy="8.5" r="1.5"/>
                                    <path d="M21 15l-5-5L5 21"/>
                                </svg>
                            </div>
                            <h3 className="feature-title">Intelligent Code Generation</h3>
                            <p className="feature-description">
                                Generate complete, production-ready applications with modern frameworks, 
                                best practices, and comprehensive validation systems.
                            </p>
                        </div>
                        
                        <div className="feature-card">
                            <div className="feature-icon">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                    <polyline points="14,2 14,8 20,8"/>
                                    <line x1="16" y1="13" x2="8" y2="13"/>
                                    <line x1="16" y1="17" x2="8" y2="17"/>
                                    <polyline points="10,9 9,9 8,9"/>
                                </svg>
                            </div>
                            <h3 className="feature-title">Real-Time Collaboration</h3>
                            <p className="feature-description">
                                Collaborate with your team using voice commands, share project updates, 
                                and maintain synchronized development environments.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section id="features" className="section features-section">
                <div className="section-content">
                    <div className="section-header">
                        <h2 className="section-title">Platform Capabilities</h2>
                        <p className="section-subtitle">
                            Comprehensive development tools powered by advanced AI and voice recognition technology.
                        </p>
                    </div>
                    
                    <div className="capabilities-list">
                        <div className="capability-item">
                            <div className="capability-number">01</div>
                            <div className="capability-content">
                                <h3 className="capability-title">Multi-Language Voice Recognition</h3>
                                <p className="capability-description">
                                    Support for multiple languages and technical terminology. Our AI understands programming 
                                    concepts, framework names, and development patterns across different spoken languages.
                                </p>
                            </div>
                        </div>
                        
                        <div className="capability-item">
                            <div className="capability-number">02</div>
                            <div className="capability-content">
                                <h3 className="capability-title">Automated Testing and Validation</h3>
                                <p className="capability-description">
                                    Every generated application undergoes rigorous testing and validation. Code is verified 
                                    for syntax, security vulnerabilities, and performance optimization before deployment.
                                </p>
                            </div>
                        </div>
                        
                        <div className="capability-item">
                            <div className="capability-number">03</div>
                            <div className="capability-content">
                                <h3 className="capability-title">Cloud-Native Deployment</h3>
                                <p className="capability-description">
                                    Seamless deployment to major cloud platforms with automated CI/CD pipelines, 
                                    monitoring, and scaling capabilities built into every project.
                                </p>
                            </div>
                        </div>
                        
                        <div className="capability-item">
                            <div className="capability-number">04</div>
                            <div className="capability-content">
                                <h3 className="capability-title">Enterprise Security</h3>
                                <p className="capability-description">
                                    Built-in security best practices, encryption, authentication systems, 
                                    and compliance with industry standards for data protection and privacy.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Use Cases Section */}
            <section id="use-cases" className="section use-cases-section">
                <div className="section-content">
                    <div className="section-header">
                        <h2 className="section-title">Transform Ideas Into Applications</h2>
                        <p className="section-subtitle">
                            From concept to deployment, xVerta handles the complete development lifecycle.
                        </p>
                    </div>
                    
                    <div className="use-cases-grid">
                        <div className="use-case-card">
                            <h3 className="use-case-title">E-Commerce Platforms</h3>
                            <p className="use-case-description">
                                "Create an online store with payment processing, inventory management, 
                                and customer analytics dashboard."
                            </p>
                            <div className="use-case-tech">
                                <span className="tech-tag">React</span>
                                <span className="tech-tag">FastAPI</span>
                                <span className="tech-tag">PostgreSQL</span>
                            </div>
                        </div>
                        
                        <div className="use-case-card">
                            <h3 className="use-case-title">SaaS Applications</h3>
                            <p className="use-case-description">
                                "Build a project management tool with team collaboration, 
                                real-time updates, and subscription billing."
                            </p>
                            <div className="use-case-tech">
                                <span className="tech-tag">Vue.js</span>
                                <span className="tech-tag">Node.js</span>
                                <span className="tech-tag">MongoDB</span>
                            </div>
                        </div>
                        
                        <div className="use-case-card">
                            <h3 className="use-case-title">Mobile Applications</h3>
                            <p className="use-case-description">
                                "Develop a cross-platform mobile app with offline capabilities, 
                                push notifications, and social features."
                            </p>
                            <div className="use-case-tech">
                                <span className="tech-tag">React Native</span>
                                <span className="tech-tag">Express</span>
                                <span className="tech-tag">Firebase</span>
                            </div>
                        </div>
                        
                        <div className="use-case-card">
                            <h3 className="use-case-title">Data Analytics</h3>
                            <p className="use-case-description">
                                "Create a business intelligence dashboard with data visualization, 
                                reporting, and machine learning insights."
                            </p>
                            <div className="use-case-tech">
                                <span className="tech-tag">Python</span>
                                <span className="tech-tag">Django</span>
                                <span className="tech-tag">TensorFlow</span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="section cta-section">
                <div className="section-content">
                    <div className="cta-content">
                        <h2 className="cta-title">Ready to Build Your Next Application?</h2>
                        <p className="cta-description">
                            Join thousands of developers who are already using xVerta to accelerate their development process.
                        </p>
                        <button 
                            className={`btn-cta ${activeButton === 'getstarted' ? 'btn-active' : ''}`}
                            onClick={handleGetStarted}
                        >
                            Get Started Now
                            <ChevronRight className="btn-icon" />
                        </button>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="footer">
                <div className="footer-content">
                    <div className="footer-section">
                        <div className="logo">XVERTA</div>
                        <p className="footer-description">
                            Empowering developers with AI-powered tools for faster, safer application development.
                        </p>
                    </div>
                    
                    <div className="footer-section">
                        <h4 className="footer-title">Platform</h4>
                        <div className="footer-links">
                            <a href="#features" className="footer-link">Features</a>
                            <a href="#pricing" className="footer-link">Pricing</a>
                            <a href="#integrations" className="footer-link">Integrations</a>
                            <a href="#security" className="footer-link">Security</a>
                        </div>
                    </div>
                    
                    <div className="footer-section">
                        <h4 className="footer-title">Resources</h4>
                        <div className="footer-links">
                            <a href="#documentation" className="footer-link">Documentation</a>
                            <a href="#tutorials" className="footer-link">Tutorials</a>
                            <a href="#community" className="footer-link">Community</a>
                            <a href="#support" className="footer-link">Support</a>
                        </div>
                    </div>
                    
                    <div className="footer-section">
                        <h4 className="footer-title">Company</h4>
                        <div className="footer-links">
                            <a href="#about" className="footer-link">About</a>
                            <a href="#careers" className="footer-link">Careers</a>
                            <a href="#blog" className="footer-link">Blog</a>
                            <a href="#contact" className="footer-link">Contact</a>
                        </div>
                    </div>
                </div>
                
                <div className="footer-bottom">
                    <p>&copy; 2025 xVerta. All rights reserved.</p>
                    <div className="footer-bottom-links">
                        <a href="#privacy" className="footer-bottom-link">Privacy Policy</a>
                        <a href="#terms" className="footer-bottom-link">Terms of Service</a>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default VexelLandingPage;