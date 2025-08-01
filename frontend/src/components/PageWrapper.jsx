import React, { useEffect, useRef } from 'react';

// --- Particle Background Component ---
const ParticleBackground = () => {
    const canvasRef = useRef(null);
    const mouse = useRef({ x: null, y: null, radius: 150 });

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        let particlesArray;

        const handleMouseMove = (event) => {
            mouse.current.x = event.clientX;
            mouse.current.y = event.clientY;
        };
        window.addEventListener('mousemove', handleMouseMove);

        const handleResize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            init();
        };
        window.addEventListener('resize', handleResize);

        class Particle {
            constructor(x, y, directionX, directionY, size, color) {
                this.x = x; this.y = y; this.directionX = directionX; this.directionY = directionY; this.size = size; this.color = color;
            }
            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2, false);
                ctx.fillStyle = 'rgba(0, 245, 195, 0.5)';
                ctx.fill();
            }
            update() {
                if (this.x > canvas.width || this.x < 0) this.directionX = -this.directionX;
                if (this.y > canvas.height || this.y < 0) this.directionY = -this.directionY;
                let dx = mouse.current.x - this.x;
                let dy = mouse.current.y - this.y;
                let distance = Math.sqrt(dx * dx + dy * dy);
                if (distance < mouse.current.radius + this.size) {
                    if (mouse.current.x < this.x && this.x < canvas.width - this.size * 10) this.x += 5;
                    if (mouse.current.x > this.x && this.x > this.size * 10) this.x -= 5;
                    if (mouse.current.y < this.y && this.y < canvas.height - this.size * 10) this.y += 5;
                    if (mouse.current.y > this.y && this.y > this.size * 10) this.y -= 5;
                }
                this.x += this.directionX;
                this.y += this.directionY;
                this.draw();
            }
        }

        function init() {
            particlesArray = [];
            let numberOfParticles = (canvas.height * canvas.width) / 9000;
            for (let i = 0; i < numberOfParticles; i++) {
                let size = (Math.random() * 2) + 1;
                let x = (Math.random() * ((innerWidth - size * 2) - (size * 2)) + size * 2);
                let y = (Math.random() * ((innerHeight - size * 2) - (size * 2)) + size * 2);
                let directionX = (Math.random() * 0.4) - 0.2;
                let directionY = (Math.random() * 0.4) - 0.2;
                particlesArray.push(new Particle(x, y, directionX, directionY, size, '#00f5c3'));
            }
        }

        function connect() {
            let opacityValue = 1;
            for (let a = 0; a < particlesArray.length; a++) {
                for (let b = a; b < particlesArray.length; b++) {
                    let distance = ((particlesArray[a].x - particlesArray[b].x) ** 2) + ((particlesArray[a].y - particlesArray[b].y) ** 2);
                    if (distance < (canvas.width / 7) * (canvas.height / 7)) {
                        opacityValue = 1 - (distance / 20000);
                        ctx.strokeStyle = `rgba(0, 245, 195, ${opacityValue})`;
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        ctx.moveTo(particlesArray[a].x, particlesArray[a].y);
                        ctx.lineTo(particlesArray[b].x, particlesArray[b].y);
                        ctx.stroke();
                    }
                }
            }
        }

        let animationFrameId;
        function animate() {
            ctx.fillStyle = '#000000';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            particlesArray.forEach(p => p.update());
            connect();
            animationFrameId = requestAnimationFrame(animate);
        }

        init();
        animate();

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('resize', handleResize);
            cancelAnimationFrame(animationFrameId);
        };
    }, []);

    return <canvas ref={canvasRef} className="particle-canvas"></canvas>;
};

// --- Shared Page Wrapper Component ---
const PageWrapper = ({ children }) => {
    return (
        <>
            <style>
                {`
                    /* --- Global Styles & Variables --- */
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
                    
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

                    body {
                        background-color: var(--bg-dark);
                        color: var(--text-light);
                        font-family: 'Inter', sans-serif;
                        margin: 0;
                        overflow-x: hidden;
                    }

                    .main-app {
                        position: relative;
                        z-index: 1;
                        min-height: 100vh;
                        width: 100%;
                    }

                    .particle-canvas {
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        z-index: -1;
                    }

                    /* --- Layout Containers --- */
                    .page-container {
                        width: 100%;
                        padding: 0 1rem;
                    }

                    .content-wrapper {
                        max-width: 1280px;
                        margin: 0 auto;
                    }

                    /* --- Buttons --- */
                    .main-app .btn {
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        padding: 0.75rem 2rem;
                        font-size: 1.125rem;
                        font-weight: 700;
                        border-radius: 9999px;
                        border: none;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        width: 100%;
                    }

                    .main-app .btn-primary {
                        background-color: transparent !important;
                        color: var(--primary-green) !important;
                        border: 2px solid var(--card-border-hover) !important;
                        box-shadow: none !important;
                    }
                    .main-app .btn-primary:hover {
                        background-color: rgba(0, 245, 195, 0.1) !important;
                        border-color: var(--primary-green) !important;
                        transform: none !important;
                        box-shadow: none !important;
                    }

                    .main-app .btn-secondary {
                        background-color: transparent !important;
                        color: var(--primary-green) !important;
                        border: 2px solid var(--card-border-hover) !important;
                    }
                    .main-app .btn-secondary:hover {
                        background-color: rgba(0, 245, 195, 0.1) !important;
                        border-color: var(--primary-green) !important;
                        transform: none !important;
                    }

                    /* --- Cards and Layout --- */
                    .main-app .card {
                        background-color: var(--card-bg) !important;
                        backdrop-filter: blur(4px);
                        border: 1px solid var(--card-border) !important;
                        border-radius: 1rem;
                        padding: 2rem;
                        transition: all 0.3s ease;
                        color: var(--text-light);
                    }
                    .main-app .card:hover {
                        border-color: var(--card-border-hover) !important;
                        background-color: var(--card-bg-hover) !important;
                        transform: translateY(-0.5rem);
                    }

                    /* --- Text Styles --- */
                    .main-app h1, .main-app h2, .main-app h3, .main-app h4 {
                        color: var(--text-light);
                    }

                    .main-app p, .main-app span {
                        color: var(--text-dark);
                    }

                    /* --- Input Styles --- */
                    .main-app .input {
                        background-color: var(--card-bg) !important;
                        border: 1px solid var(--card-border) !important;
                        color: var(--text-light) !important;
                        border-radius: 0.5rem;
                        padding: 0.75rem 1rem;
                        transition: all 0.3s ease;
                    }
                    .main-app .input:focus {
                        border-color: var(--primary-green) !important;
                        box-shadow: 0 0 0 3px rgba(0, 245, 195, 0.1) !important;
                        outline: none;
                    }

                    /* --- Status Indicators --- */
                    .main-app .status-success {
                        background: rgba(0, 245, 195, 0.1) !important;
                        color: var(--primary-green) !important;
                        border: 1px solid rgba(0, 245, 195, 0.2) !important;
                    }

                    .main-app .status-warning {
                        background: rgba(251, 191, 36, 0.1) !important;
                        color: #fbbf24 !important;
                        border: 1px solid rgba(251, 191, 36, 0.2) !important;
                    }

                    .main-app .status-error {
                        background: rgba(239, 68, 68, 0.1) !important;
                        color: #ef4444 !important;
                        border: 1px solid rgba(239, 68, 68, 0.2) !important;
                    }

                    /* --- Terminal --- */
                    .main-app .terminal {
                        background: var(--card-bg) !important;
                        border: 1px solid var(--card-border) !important;
                        color: var(--primary-green);
                        border-radius: 0.5rem;
                    }

                    /* --- Responsive Design --- */
                    @media (min-width: 640px) {
                        .page-container {
                            padding: 0 1.5rem;
                        }
                        .main-app .btn {
                            width: auto;
                        }
                    }

                    @media (min-width: 1024px) {
                        .hero-title {
                            font-size: 6rem;
                        }
                    }
                `}
            </style>
            <main className="main-app">
                <ParticleBackground />
                <div className="relative z-10">
                    {children}
                </div>
            </main>
        </>
    );
};

export default PageWrapper;
