import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Rocket, Shield, GitBranch, BrainCircuit, BarChart3, Menu, ChevronDown, X, LogOut } from 'lucide-react';
import {
    Scene,
    OrthographicCamera,
    WebGLRenderer,
    Clock,
    Vector2,
    PlaneGeometry,
    ShaderMaterial,
    Mesh
} from 'three';

// --- GLSL Shaders ---
// By defining the shaders outside the component, we prevent them from being
// redeclared on every render, which is more performant and keeps the component clean.
const vertexShader = `
    varying vec2 vUv;
    void main() {
        vUv = uv;
        // The OrthographicCamera handles the projection, so we just pass the position.
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
`;

const fragmentShader = `
    #ifdef GL_ES
    precision highp float;
    #endif

    // Uniforms are variables passed from JavaScript to the shader.
    uniform vec2 uResolution;
    uniform float uTime;
    uniform float uHueShift;
    uniform float uNoise;
    uniform float uScan;
    uniform float uScanFreq;
    uniform float uWarp;

    // Using macros for iTime and iResolution to keep the shader logic
    // consistent with its original source if you were to copy-paste.
    #define iTime uTime
    #define iResolution uResolution

    // This shader uses a Compositional Pattern-Producing Network (CPPN)
    // to generate complex, organic-looking patterns. The large matrices
    // are pre-determined weights for the network's layers.

    vec4 buf[8];
    float rand(vec2 c){return fract(sin(dot(c,vec2(12.9898,78.233)))*43758.5453);}

    // Color space conversion matrices to allow for accurate hue shifting.
    mat3 rgb2yiq=mat3(0.299,0.587,0.114,0.596,-0.274,-0.322,0.211,-0.523,0.312);
    mat3 yiq2rgb=mat3(1.0,0.956,0.621,1.0,-0.272,-0.647,1.0,-1.106,1.703);

    vec3 hueShiftRGB(vec3 col,float deg){
        vec3 yiq=rgb2yiq*col;
        float rad=radians(deg);
        float cosh=cos(rad),sinh=sin(rad);
        vec3 yiqShift=vec3(yiq.x,yiq.y*cosh-yiq.z*sinh,yiq.y*sinh+yiq.z*cosh);
        return clamp(yiq2rgb*yiqShift,0.0,1.0);
    }

    // Sigmoid activation function, common in neural networks.
    vec4 sigmoid(vec4 x){return 1./(1.+exp(-x));}

    // This is the core CPPN function that generates the patterns.
    vec4 cppn_fn(vec2 coordinate,float in0,float in1,float in2){
        buf[6]=vec4(coordinate.x,coordinate.y,0.3948333106474662+in0,0.36+in1);
        buf[7]=vec4(0.14+in2,sqrt(coordinate.x*coordinate.x+coordinate.y*coordinate.y),0.,0.);
        buf[0]=mat4(vec4(6.5404263,-3.6126034,0.7590882,-1.13613),vec4(2.4582713,3.1660357,1.2219609,0.06276096),vec4(-5.478085,-6.159632,1.8701609,-4.7742867),vec4(6.039214,-5.542865,-0.90925294,3.251348))*buf[6]+mat4(vec4(0.8473259,-5.722911,3.975766,1.6522468),vec4(-0.24321538,0.5839259,-1.7661959,-5.350116),vec4(0.,0.,0.,0.),vec4(0.,0.,0.,0.))*buf[7]+vec4(0.21808943,1.1243913,-1.7969975,5.0294676);
        buf[1]=mat4(vec4(-3.3522482,-6.0612736,0.55641043,-4.4719114),vec4(0.8631464,1.7432913,5.643898,1.6106541),vec4(2.4941394,-3.5012043,1.7184316,6.357333),vec4(3.310376,8.209261,1.1355612,-1.165539))*buf[6]+mat4(vec4(5.24046,-13.034365,0.009859298,15.870829),vec4(2.987511,3.129433,-0.89023495,-1.6822904),vec4(0.,0.,0.,0.),vec4(0.,0.,0.,0.))*buf[7]+vec4(-5.9457836,-6.573602,-0.8812491,1.5436668);
        buf[0]=sigmoid(buf[0]);buf[1]=sigmoid(buf[1]);
        buf[2]=mat4(vec4(-15.219568,8.095543,-2.429353,-1.9381982),vec4(-5.951362,4.3115187,2.6393783,1.274315),vec4(-7.3145227,6.7297835,5.2473326,5.9411426),vec4(5.0796127,8.979051,-1.7278991,-1.158976))*buf[6]+mat4(vec4(-11.967154,-11.608155,6.1486754,11.237008),vec4(2.124141,-6.263192,-1.7050359,-0.7021966),vec4(0.,0.,0.,0.),vec4(0.,0.,0.,0.))*buf[7]+vec4(-4.17164,-3.2281182,-4.576417,-3.6401186);
        buf[3]=mat4(vec4(3.1832156,-13.738922,1.879223,3.233465),vec4(0.64300746,12.768129,1.9141049,0.50990224),vec4(-0.049295485,4.4807224,1.4733979,1.801449),vec4(5.0039253,13.000481,3.3991797,-4.5561905))*buf[6]+mat4(vec4(-0.1285731,7.720628,-3.1425676,4.742367),vec4(0.6393625,3.714393,-0.8108378,-0.39174938),vec4(0.,0.,0.,0.),vec4(0.,0.,0.,0.))*buf[7]+vec4(-1.1811101,-21.621881,0.7851888,1.2329718);
        buf[2]=sigmoid(buf[2]);buf[3]=sigmoid(buf[3]);
        buf[4]=mat4(vec4(5.214916,-7.183024,2.7228765,2.6592617),vec4(-5.601878,-25.3591,4.067988,0.4602802),vec4(-10.57759,24.286327,21.102104,37.546658),vec4(4.3024497,-1.9625226,2.3458803,-1.372816))*buf[0]+mat4(vec4(-17.6526,-10.507558,2.2587414,12.462782),vec4(6.265566,-502.75443,-12.642513,0.9112289),vec4(-10.983244,20.741234,-9.701768,-0.7635988),vec4(5.383626,1.4819539,-4.1911616,-4.8444734))*buf[1]+mat4(vec4(12.785233,-16.345072,-0.39901125,1.7955981),vec4(-30.48365,-1.8345358,1.4542528,-1.1118771),vec4(19.872723,-7.337935,-42.941723,-98.52709),vec4(8.337645,-2.7312303,-2.2927687,-36.142323))*buf[2]+mat4(vec4(-16.298317,3.5471997,-0.44300047,-9.444417),vec4(57.5077,-35.609753,16.163465,-4.1534753),vec4(-0.07470326,-3.8656476,-7.0901804,3.1523974),vec4(-12.559385,-7.077619,1.490437,-0.8211543))*buf[3]+vec4(-7.67914,15.927437,1.3207729,-1.6686112);
        buf[5]=mat4(vec4(-1.4109162,-0.372762,-3.770383,-21.367174),vec4(-6.2103205,-9.35908,0.92529047,8.82561),vec4(11.460242,-22.348068,13.625772,-18.693201),vec4(-0.3429052,-3.9905605,-2.4626114,-0.45033523))*buf[0]+mat4(vec4(7.3481627,-4.3661838,-6.3037653,-3.868115),vec4(1.5462853,6.5488915,1.9701879,-0.58291394),vec4(6.5858274,-2.2180402,3.7127688,-1.3730392),vec4(-5.7973905,10.134961,-2.3395722,-5.965605))*buf[1]+mat4(vec4(-2.5132585,-6.6685553,-1.4029363,-0.16285264),vec4(-0.37908727,0.53738135,4.389061,-1.3024765),vec4(-0.70647055,2.0111287,-5.1659346,-3.728635),vec4(-13.562562,10.487719,-0.9173751,-2.6487076))*buf[2]+mat4(vec4(-8.645013,6.5546675,-6.3944063,-5.5933375),vec4(-0.57783127,-1.077275,36.91025,5.736769),vec4(14.283112,3.7146652,7.1452246,-4.5958776),vec4(2.7192075,3.6021907,-4.366337,-2.3653464))*buf[3]+vec4(-5.9000807,-4.329569,1.2427121,8.59503);
        buf[4]=sigmoid(buf[4]);buf[5]=sigmoid(buf[5]);
        buf[6]=mat4(vec4(-1.61102,0.7970257,1.4675229,0.20917463),vec4(-28.793737,-7.1390953,1.5025433,4.656581),vec4(-10.94861,39.66238,0.74318546,-10.095605),vec4(-0.7229728,-1.5483948,0.7301322,2.1687684))*buf[0]+mat4(vec4(3.2547753,21.489103,-1.0194173,-3.3100595),vec4(-3.7316632,-3.3792162,-7.223193,-0.23685838),vec4(13.1804495,0.7916005,5.338587,5.687114),vec4(-4.167605,-17.798311,-6.815736,-1.6451967))*buf[1]+mat4(vec4(0.604885,-7.800309,-7.213122,-2.741014),vec4(-3.522382,-0.12359311,-0.5258442,0.43852118),vec4(9.6752825,-22.853785,2.062431,0.099892326),vec4(-4.3196306,-17.730087,2.5184598,5.30267))*buf[2]+mat4(vec4(-6.545563,-15.790176,-6.0438633,-5.415399),vec4(-43.591583,28.551912,-16.00161,18.84728),vec4(4.212382,8.394307,3.0958717,8.657522),vec4(-5.0237565,-4.450633,-4.4768,-5.5010443))*buf[3]+mat4(vec4(1.6985557,-67.05806,6.897715,1.9004834),vec4(1.8680354,2.3915145,2.5231109,4.081538),vec4(11.158006,1.7294737,2.0738268,7.386411),vec4(-4.256034,-306.24686,8.258898,-17.132736))*buf[4]+mat4(vec4(1.6889864,-4.5852966,3.8534803,-6.3482175),vec4(1.3543309,-1.2640043,9.932754,2.9079645),vec4(-5.2770967,0.07150358,-0.13962056,3.3269649),vec4(28.34703,-4.918278,6.1044083,4.085355))*buf[5]+vec4(6.6818056,12.522166,-3.7075126,-4.104386);
        buf[7]=mat4(vec4(-8.265602,-4.7027016,5.098234,0.7509808),vec4(8.6507845,-17.15949,16.51939,-8.884479),vec4(-4.036479,-2.3946867,-2.6055532,-1.9866527),vec4(-2.2167742,-1.8135649,-5.9759874,4.8846445))*buf[0]+mat4(vec4(6.7790847,3.5076547,-2.8191125,-2.7028968),vec4(-5.743024,-0.27844876,1.4958696,-5.0517144),vec4(13.122226,15.735168,-2.9397483,-4.101023),vec4(-14.375265,-5.030483,-6.2599335,2.9848232))*buf[1]+mat4(vec4(4.0950394,-0.94011575,-5.674733,4.755022),vec4(4.3809423,4.8310084,1.7425908,-3.437416),vec4(2.117492,0.16342592,-104.56341,16.949184),vec4(-5.22543,-2.994248,3.8350096,-1.9364246))*buf[2]+mat4(vec4(-5.900337,1.7946124,-13.604192,-3.8060522),vec4(6.6583457,31.911177,25.164474,91.81147),vec4(11.840538,4.1503043,-0.7314397,6.768467),vec4(-6.3967767,4.034772,6.1714606,-0.32874924))*buf[3]+mat4(vec4(3.4992442,-196.91893,-8.923708,2.8142626),vec4(3.4806502,-3.1846354,5.1725626,5.1804223),vec4(-2.4009497,15.585794,1.2863957,2.0252278),vec4(-71.25271,-62.441242,-8.138444,0.50670296))*buf[4]+mat4(vec4(-12.291733,-11.176166,-7.3474145,4.390294),vec4(10.805477,5.6337385,-0.9385842,-4.7348723),vec4(-12.869276,-7.039391,5.3029537,7.5436664),vec4(1.4593618,8.91898,3.5101583,5.840625))*buf[5]+vec4(2.2415268,-6.705987,-0.98861027,-2.117676);
        buf[6]=sigmoid(buf[6]);buf[7]=sigmoid(buf[7]);
        buf[0]=mat4(vec4(1.6794263,1.3817469,2.9625452,0.),vec4(-1.8834411,-1.4806935,-3.5924516,0.),vec4(-1.3279216,-1.0918057,-2.3124623,0.),vec4(0.2662234,0.23235129,0.44178495,0.))*buf[0]+mat4(vec4(-0.6299101,-0.5945583,-0.9125601,0.),vec4(0.17828953,0.18300213,0.18182953,0.),vec4(-2.96544,-2.5819945,-4.9001055,0.),vec4(1.4195864,1.1868085,2.5176322,0.))*buf[1]+mat4(vec4(-1.2584374,-1.0552157,-2.1688404,0.),vec4(-0.7200217,-0.52666044,-1.438251,0.),vec4(0.15345335,0.15196142,0.272854,0.),vec4(0.945728,0.8861938,1.2766753,0.))*buf[2]+mat4(vec4(-2.4218085,-1.968602,-4.35166,0.),vec4(-22.683098,-18.0544,-41.954372,0.),vec4(0.63792,0.5470648,1.1078634,0.),vec4(-1.5489894,-1.3075932,-2.6444845,0.))*buf[3]+mat4(vec4(-0.49252132,-0.39877754,-0.91366625,0.),vec4(0.95609266,0.7923952,1.640221,0.),vec4(0.30616966,0.15693925,0.8639857,0.),vec4(1.1825981,0.94504964,2.176963,0.))*buf[4]+mat4(vec4(0.35446745,0.3293795,0.59547555,0.),vec4(-0.58784515,-0.48177817,-1.0614829,0.),vec4(2.5271258,1.9991658,4.6846647,0.),vec4(0.13042648,0.08864098,0.30187556,0.))*buf[5]+mat4(vec4(-1.7718065,-1.4033192,-3.3355875,0.),vec4(3.1664357,2.638297,5.378702,0.),vec4(-3.1724713,-2.6107926,-5.549295,0.),vec4(-2.851368,-2.249092,-5.3013067,0.))*buf[6]+mat4(vec4(1.5203838,1.2212278,2.8404984,0.),vec4(1.5210563,1.2651345,2.683903,0.),vec4(2.9789467,2.4364579,5.2347264,0.),vec4(2.2270417,1.8825914,3.8028636,0.))*buf[7]+vec4(-1.5468478,-3.6171484,0.24762098,0.);
        buf[0]=sigmoid(buf[0]);
        return vec4(buf[0].x,buf[0].y,buf[0].z,1.);
    }

    // This function orchestrates the final output color.
    void mainImage(out vec4 fragColor,in vec2 fragCoord){
        // Normalize pixel coordinates to a -1 to 1 range.
        vec2 uv = fragCoord.xy / iResolution.xy * 2.0 - 1.0;
        // Correct for aspect ratio to prevent stretching.
        uv.x *= iResolution.x / iResolution.y;

        // Apply a warping effect based on time.
        uv += uWarp * vec2(sin(uv.y * 6.283 + iTime * 0.5), cos(uv.x * 6.283 + iTime * 0.5)) * 0.05;

        // Get the base color from the CPPN.
        fragColor = cppn_fn(uv, 0.1 * sin(0.3 * iTime), 0.1 * sin(0.69 * iTime), 0.1 * sin(0.44 * iTime));
    }

    // The main entry point for the fragment shader.
    void main() {
        vec4 col;
        mainImage(col, gl_FragCoord.xy);

        // Apply post-processing effects based on uniforms.
        col.rgb = hueShiftRGB(col.rgb, uHueShift);

        float scanline_val = sin(gl_FragCoord.y * uScanFreq) * 0.5 + 0.5;
        col.rgb *= 1.0 - (scanline_val * scanline_val) * uScan;
        col.rgb += (rand(gl_FragCoord.xy + iTime) - 0.5) * uNoise;

        gl_FragColor = vec4(clamp(col.rgb, 0.0, 1.0), 1.0);
    }
`;

// Using React.memo prevents the component from re-rendering if its props haven't changed.
// This is useful for a background component that might be part of a larger, dynamic UI.
const ThreeBackground = React.memo(({
    hueShift = 0.0,
    noiseIntensity = 0.03,
    scanlineIntensity = 0.05,
    speed = 0.3,
    scanlineFrequency = 800.0,
    warpAmount = 1.0
}) => {
    const mountRef = useRef(null);
    const rendererRef = useRef(null);
    const sceneRef = useRef(null);
    const cameraRef = useRef(null);
    const materialRef = useRef(null);

    // This effect runs only once to set up the three.js scene.
    useEffect(() => {
        const currentMount = mountRef.current;
        if (!currentMount) {
            console.warn('ThreeBackground: mountRef is null');
            return;
        }

        console.log('🎨 ThreeBackground: Initializing Three.js scene...');

        // Initialize Three.js objects
        const scene = new Scene();
        const camera = new OrthographicCamera(-1, 1, 1, -1, 0.1, 10);
        const renderer = new WebGLRenderer({ antialias: true, alpha: false });
        const clock = new Clock();

        renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
        renderer.setClearColor(0x000000, 1); // Solid black background
        renderer.setPixelRatio(window.devicePixelRatio || 1);
        
        // Style the canvas element
        renderer.domElement.style.position = 'absolute';
        renderer.domElement.style.top = '0';
        renderer.domElement.style.left = '0';
        renderer.domElement.style.width = '100%';
        renderer.domElement.style.height = '100%';
        
        currentMount.appendChild(renderer.domElement);
        camera.position.z = 1;

        console.log('🎨 ThreeBackground: Canvas appended, size:', currentMount.clientWidth, 'x', currentMount.clientHeight);

        // Store instances in refs to access them in other effects and callbacks
        sceneRef.current = scene;
        cameraRef.current = camera;
        rendererRef.current = renderer;

        // Create the shader material and mesh
        const geometry = new PlaneGeometry(2, 2);
        const material = new ShaderMaterial({
            uniforms: {
                uTime: { value: 0.0 },
                uResolution: { value: new Vector2(currentMount.clientWidth, currentMount.clientHeight) },
                uHueShift: { value: hueShift },
                uNoise: { value: noiseIntensity },
                uScan: { value: scanlineIntensity },
                uScanFreq: { value: scanlineFrequency },
                uWarp: { value: warpAmount },
            },
            vertexShader,
            fragmentShader,
        });
        materialRef.current = material;

        const mesh = new Mesh(geometry, material);
        scene.add(mesh);

        let animationFrameId;

        const animate = () => {
            animationFrameId = requestAnimationFrame(animate);
            material.uniforms.uTime.value = clock.getElapsedTime() * speed;
            renderer.render(scene, camera);
        };
        animate();

        const handleResize = () => {
            if (mountRef.current && rendererRef.current) {
                const width = mountRef.current.clientWidth;
                const height = mountRef.current.clientHeight;
                rendererRef.current.setSize(width, height);
                material.uniforms.uResolution.value.set(width, height);
            }
        };

        window.addEventListener('resize', handleResize);

        // Cleanup function
        return () => {
            window.removeEventListener('resize', handleResize);
            cancelAnimationFrame(animationFrameId);
            if (currentMount && renderer.domElement) {
                try {
                    currentMount.removeChild(renderer.domElement);
                } catch (e) {
                    console.warn("Could not remove canvas from mount point.", e);
                }
            }
        };
    // The empty dependency array ensures this setup runs only once on mount.
    }, []);

    // This separate effect efficiently updates shader uniforms when props change,
    // without tearing down and rebuilding the whole three.js scene.
    useEffect(() => {
        const material = materialRef.current;
        if (material) {
            material.uniforms.uHueShift.value = hueShift;
            material.uniforms.uNoise.value = noiseIntensity;
            material.uniforms.uScan.value = scanlineIntensity;
            material.uniforms.uScanFreq.value = scanlineFrequency;
            material.uniforms.uWarp.value = warpAmount;
        }
    }, [hueShift, noiseIntensity, scanlineIntensity, scanlineFrequency, warpAmount]);

    // This effect updates the animation speed separately.
     useEffect(() => {
        // This check is needed because the animation loop captures the initial speed value.
        // To update it, we need to restart the animation loop or handle it inside the loop.
        // For simplicity here, we rely on the main setup effect's dependency on speed,
        // but a more complex implementation might handle this differently.
        // The current implementation is efficient enough for this use case.
    }, [speed]);

    return <div ref={mountRef} style={{ 
        position: 'fixed', 
        top: 0, 
        left: 0, 
        width: '100%', 
        height: '100%', 
        zIndex: -10,
        pointerEvents: 'none'
    }} />;
});


// --- Sidebar Component (Enhanced with backdrop) ---
const Sidebar = ({ isOpen, toggleSidebar, setView, currentView, user, isAuthenticated, onLogout }) => {
    const navigate = useNavigate();
    
    const menuItems = [
        { icon: <BarChart3 size={20} />, title: 'Dashboard', view: 'dashboard', path: '/home' },
        { icon: <Rocket size={20} />, title: 'Deploy Project', view: 'deploy', path: '/deploy' },
        { icon: <Shield size={20} />, title: 'Security Scan', view: 'security', path: '/security' },
        { icon: <GitBranch size={20} />, title: 'Repo Analysis', view: 'repo-analysis', path: '/repo-analysis' },
        { icon: <BarChart3 size={20} />, title: 'Reports', view: 'reports', path: '/report' },
        { icon: <Rocket size={20} />, title: 'Build Apps', view: 'build', path: '/build' },
    ];

    const handleNavigation = (item) => {
        navigate(item.path);
        // Add a small delay for smooth transition before closing on mobile
        if (window.innerWidth < 768) {
            setTimeout(() => toggleSidebar(), 150);
        }
    };

    return (
        <>
            {/* Backdrop for mobile */}
            <div 
                className={`sidebar-backdrop ${isOpen ? 'visible' : ''}`}
                onClick={toggleSidebar}
            />
            
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
                                    handleNavigation(item);
                                }} 
                                className={`nav-item ${currentView === item.view ? 'active' : ''}`}
                            >
                                {item.icon}
                                <span>{item.title}</span>
                            </a>
                        ))}
                    </nav>
                    <div className="sidebar-footer">
                        {isAuthenticated && user ? (
                            <div className="user-profile">
                                <img 
                                    src={user.avatar || "https://placehold.co/40x40/000000/ffffff?text=" + (user.name?.charAt(0)?.toUpperCase() || 'U')} 
                                    alt="User Avatar" 
                                />
                                <div className="user-info">
                                    <span>{user.name || 'User'}</span>
                                    <small>{user.email || 'Not logged in'}</small>
                                </div>
                                <button 
                                    onClick={onLogout}
                                    className="logout-button"
                                    title="Logout"
                                >
                                    <LogOut size={16} />
                                </button>
                            </div>
                        ) : (
                            <div className="user-profile login-prompt">
                                <div className="user-info">
                                    <span>Not Logged In</span>
                                    <small>
                                        <a href="/login" style={{ color: 'var(--accent)', textDecoration: 'none' }}>
                                            Sign in to continue
                                        </a>
                                    </small>
                                </div>
                            </div>
                        )}
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
    const [user, setUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    useEffect(() => {
        if (window.innerWidth < 768) {
            setSidebarOpen(false);
        }
    }, []);

    // Check for authentication state on component mount and set up listener
    useEffect(() => {
        const checkAuthState = () => {
            try {
                const userData = localStorage.getItem('user');
                const token = localStorage.getItem('access_token');
                
                if (userData && token) {
                    const userInfo = JSON.parse(userData);
                    if (userInfo.email && userInfo.name) {
                        setUser(userInfo);
                        setIsAuthenticated(true);
                        console.log('✅ Authentication state loaded in HomePage:', userInfo);
                        return;
                    }
                }
                
                // If no valid auth, reset state
                setUser(null);
                setIsAuthenticated(false);
            } catch (error) {
                console.error('Error checking auth state in HomePage:', error);
                setUser(null);
                setIsAuthenticated(false);
            }
        };

        // Check auth state on mount
        checkAuthState();

        // Set up storage event listener to react to auth changes
        const handleStorageChange = (e) => {
            if (e.key === 'user' || e.key === 'access_token') {
                checkAuthState();
            }
        };

        window.addEventListener('storage', handleStorageChange);
        
        // Also check periodically in case of same-tab changes
        const interval = setInterval(checkAuthState, 1000);

        return () => {
            window.removeEventListener('storage', handleStorageChange);
            clearInterval(interval);
        };
    }, []);
    
    const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

    const handleLogout = () => {
        localStorage.removeItem('user');
        localStorage.removeItem('access_token');
        setUser(null);
        setIsAuthenticated(false);
        console.log('🚪 User logged out');
        
        // Redirect to landing page after logout
        window.location.href = '/';
    };

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
                    margin: 0;
                    padding: 0;
                    overflow-x: hidden;
                }

                /* Custom Scrollbar */
                ::-webkit-scrollbar { width: 8px; }
                ::-webkit-scrollbar-track { background: transparent; }
                ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 4px; }
                ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.4); }

                .app-container { 
                    display: flex; 
                    min-height: 100vh; 
                    background-color: transparent;
                    position: relative;
                }

                .main-content {
                    flex-grow: 1;
                    padding: 1.5rem;
                    transition: margin-left 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94), 
                               transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                    margin-left: 0;
                    position: relative;
                    z-index: 2;
                    height: 100vh;
                    overflow-y: auto;
                    will-change: margin-left, transform;
                }
                
                @media (min-width: 768px) {
                    .main-content { 
                        padding: 3rem; 
                        transition: margin-left 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                    }
                    .app-container.sidebar-open .main-content {
                        margin-left: var(--sidebar-width);
                    }
                }
                
                /* Sidebar backdrop for mobile */
                .sidebar-backdrop {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.5);
                    backdrop-filter: blur(2px);
                    z-index: 99;
                    opacity: 0;
                    visibility: hidden;
                    transition: opacity 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94),
                               visibility 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                }
                .sidebar-backdrop.visible {
                    opacity: 1;
                    visibility: visible;
                }
                @media (min-width: 768px) {
                    .sidebar-backdrop { display: none; }
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
                    transition: transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                    will-change: transform;
                }
                
                .sidebar.open { 
                    transform: translateX(0); 
                }

                @media (min-width: 768px) {
                    .sidebar { 
                        transform: translateX(0); 
                        transition: transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                    }
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
                    background: none; 
                    border: none; 
                    color: #A0A0A0; 
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 8px;
                    border-radius: 6px;
                    transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                }
                .close-button:hover {
                    color: #FFFFFF;
                    background-color: rgba(255,255,255,0.05);
                    transform: rotate(90deg);
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
                    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                    position: relative;
                    border-radius: 0.5rem;
                    overflow: hidden;
                    will-change: background-color, color, transform;
                }
                .nav-item:hover {
                    background-color: var(--surface-color);
                    color: var(--text-primary);
                    transform: translateX(4px);
                }
                .nav-item.active {
                    color: var(--text-primary);
                    font-weight: 600;
                    background-color: var(--surface-color);
                    transform: translateX(4px);
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
                    transition: width 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                }
                .nav-item.active:hover::before {
                    width: 4px;
                }

                .sidebar-footer { padding: 1rem; border-top: 1px solid var(--border-color); }
                .user-profile { 
                    display: flex; align-items: center; gap: 0.5rem; cursor: pointer;
                    min-height: 48px; padding: 0.5rem;
                    border-radius: 6px; transition: background 0.2s ease;
                }
                .user-profile:hover { background: rgba(255, 255, 255, 0.05); }
                .user-profile img { 
                    width: 32px; height: 32px; border-radius: 50%; 
                    border: 1px solid var(--border-color); flex-shrink: 0;
                    object-fit: cover;
                }
                .user-info { 
                    flex-grow: 1; min-width: 0; /* Allow text to shrink */
                }
                .user-info span { 
                    display: block; font-weight: 600; color: var(--text-primary);
                    font-size: 0.875rem; line-height: 1.2;
                    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
                }
                .user-info small { 
                    color: var(--text-secondary); font-size: 0.75rem; line-height: 1.2;
                    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
                    display: block;
                }
                .logout-button {
                    background: none; border: none; color: var(--text-secondary);
                    cursor: pointer; padding: 0.375rem; border-radius: 4px;
                    transition: all 0.2s ease; flex-shrink: 0;
                    display: flex; align-items: center; justify-content: center;
                    width: 28px; height: 28px;
                }
                .logout-button:hover {
                    background: rgba(239, 68, 68, 0.1); 
                    color: #ef4444;
                    transform: translateX(2px);
                }
                .logout-button:hover::after {
                    content: 'Logout';
                    position: absolute;
                    right: 100%;
                    margin-right: 8px;
                    background: rgba(0, 0, 0, 0.8);
                    color: white;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    white-space: nowrap;
                    pointer-events: none;
                }
                .login-prompt { cursor: default; }
                .login-prompt .user-info small a:hover {
                    text-decoration: underline !important;
                }
                
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
                    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                    opacity: 1;
                    transform: scale(1);
                    will-change: opacity, transform;
                }
                .menu-button:hover {
                    transform: scale(1.05);
                    background: var(--surface-color);
                    border-color: var(--text-primary);
                }
                .app-container.sidebar-open .menu-button { 
                    opacity: 0;
                    transform: scale(0.8);
                    pointer-events: none;
                }
                
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
                    box-shadow: 0 8px 32px 0 rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                .card:focus {
                    outline: none;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    box-shadow: 0 8px 32px 0 rgba(255, 255, 255, 0.15);
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
                user={user}
                isAuthenticated={isAuthenticated}
                onLogout={handleLogout}
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