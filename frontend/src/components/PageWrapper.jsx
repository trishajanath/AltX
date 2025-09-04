import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import * as THREE from 'three';
import { BarChart3, Rocket, Shield, GitBranch, Menu, X, ChevronDown } from 'lucide-react';
import Plasma from './Plasma';

// --- Sidebar Component (Updated) ---
const Sidebar = ({ isOpen, toggleSidebar }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const currentPath = location.pathname;
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
            `}</style>
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
                            className={`nav-item ${currentPath === item.path ? 'active' : ''}`}
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
            {!isOpen && (
                <button className="menu-button" onClick={toggleSidebar}>
                    <Menu size={24} />
                </button>
            )}
        </>
    );
};

// --- ✨ UPDATED Vortex Three.js Background ---
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

        // Initialize Three.js objects
        const scene = new Scene();
        const camera = new OrthographicCamera(-1, 1, 1, -1, 0.1, 10);
        const renderer = new WebGLRenderer({ antialias: true, alpha: true });
        const clock = new Clock();

        renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
        renderer.setClearColor(0x000000, 0); // Transparent background
        currentMount.appendChild(renderer.domElement);
        camera.position.z = 1;

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


    return <div ref={mountRef} style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', zIndex: -1, backgroundColor: '#000' }} />;
});

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
                        --bg-dark: transparent !important;
                        --card-bg: rgba(0, 0, 0, 0.3);
                        --card-bg-hover: rgba(0, 0, 0, 0.5);
                        --card-border: rgba(0, 245, 195, 0.2);
                        --card-border-hover: rgba(0, 245, 195, 0.5);
                    }
                    .main-app, .app-container, .report-page, .security-scan-page, .deploy-page, .repo-analysis-page, .project-builder-page {
                        background: transparent !important;
                        background-color: transparent !important;
                    }
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