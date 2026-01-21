import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { Shield, Database, Globe, Key, Lock, Zap, Filter, Users, Clock, AlertTriangle, Play, X, ChevronDown, Check } from 'lucide-react';

// Neon color palette for OLED theme
const NEON_COLORS = {
  cyan: '#00ffff',
  purple: '#bf00ff',
  green: '#00ff41',
  red: '#ff0033',
  orange: '#ff6600',
  yellow: '#ffff00',
  blue: '#0066ff'
};

// Security Node Types with their code injection templates
const SECURITY_NODE_TYPES = {
  sanitizer: {
    id: 'sanitizer',
    label: 'Sanitizer',
    description: 'Filters input data before DB',
    icon: Filter,
    color: NEON_COLORS.cyan,
    borderColor: '#00cccc',
    codeTemplate: `// Input Sanitization Middleware
const sanitizeInput = (req, res, next) => {
  Object.keys(req.body).forEach(key => {
    if (typeof req.body[key] === 'string') {
      req.body[key] = DOMPurify.sanitize(req.body[key]);
    }
  });
  next();
};`
  },
  gatekeeper: {
    id: 'gatekeeper',
    label: 'Gatekeeper',
    description: 'RBAC role verification',
    icon: Users,
    color: NEON_COLORS.purple,
    borderColor: '#9900cc',
    codeTemplate: `// Role-Based Access Control
const requireRole = (role) => (req, res, next) => {
  if (!req.user || req.user.role !== role) {
    return res.status(403).json({ error: 'Forbidden' });
  }
  next();
};`
  },
  encryptor: {
    id: 'encryptor',
    label: 'Encryptor',
    description: 'Field-level encryption',
    icon: Lock,
    color: NEON_COLORS.blue,
    borderColor: '#0055cc',
    codeTemplate: `// Field Encryption Middleware
const encryptFields = (fields) => (req, res, next) => {
  fields.forEach(field => {
    if (req.body[field]) {
      req.body[field] = crypto.createHash('sha256')
        .update(req.body[field]).digest('hex');
    }
  });
  next();
};`
  },
  throttle: {
    id: 'throttle',
    label: 'Throttle',
    description: 'Rate limiting / DDoS prevention',
    icon: Clock,
    color: NEON_COLORS.orange,
    borderColor: '#cc5500',
    codeTemplate: `// Rate Limiter
const rateLimit = require('express-rate-limit');
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per window
  message: { error: 'Too many requests' }
});`
  },
  jwtAuth: {
    id: 'jwtAuth',
    label: 'JWT Auth',
    description: 'Token verification',
    icon: Key,
    color: NEON_COLORS.yellow,
    borderColor: '#cccc00',
    codeTemplate: `// JWT Authentication Middleware
const verifyToken = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token' });
  try {
    req.user = jwt.verify(token, process.env.JWT_SECRET);
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Invalid token' });
  }
};`
  },
  validator: {
    id: 'validator',
    label: 'Validator',
    description: 'Schema validation',
    icon: Shield,
    color: NEON_COLORS.green,
    borderColor: '#00cc33',
    codeTemplate: `// Input Validation
const validateSchema = (schema) => (req, res, next) => {
  const { error } = schema.validate(req.body);
  if (error) {
    return res.status(400).json({ error: error.details[0].message });
  }
  next();
};`
  }
};

// Analyze project files to generate security pipeline with detailed business logic
const analyzeProjectFiles = (files) => {
  const nodes = [];
  const edges = [];
  const securityStatus = [
    { id: 'ssl', label: 'SSL/TLS Enabled', status: false },
    { id: 'db_encrypt', label: 'Database Encrypted', status: false },
    { id: 'csrf', label: 'CSRF Protection', status: false },
    { id: 'headers', label: 'Security Headers', status: false },
    { id: 'cors', label: 'CORS Configured', status: false }
  ];
  
  // Details about the data flow
  const dataFlowDetails = {
    clientToApi: [],
    apiToDb: [],
    businessLogic: [],
    dataTransformations: []
  };
  
  if (!files || Object.keys(files).length === 0) {
    // Return default structure if no files - will show loading state
    return {
      nodes: [
        { 
          id: 'client', 
          type: 'source', 
          label: 'Client / Browser', 
          x: 80, 
          y: 200, 
          icon: Globe, 
          color: '#ffffff', 
          borderColor: '#444444',
          description: 'Waiting for project files to load...',
          dataFlow: 'Loading analysis...'
        },
        { 
          id: 'api', 
          type: 'logic', 
          label: 'API Endpoint', 
          x: 400, 
          y: 200, 
          icon: Zap, 
          color: NEON_COLORS.orange, 
          borderColor: '#cc5500', 
          route: 'Loading...',
          description: 'Loading project analysis...',
          dataFlow: 'Analyzing routes...'
        },
        { 
          id: 'database', 
          type: 'destination', 
          label: 'Database', 
          x: 720, 
          y: 200, 
          icon: Database, 
          color: NEON_COLORS.green, 
          borderColor: '#00cc33',
          description: 'Loading database configuration...',
          dataFlow: 'Analyzing storage...'
        }
      ],
      edges: [
        { id: 'e1', source: 'client', target: 'api', encrypted: false, dataFlow: 'Loading...' },
        { id: 'e2', source: 'api', target: 'database', encrypted: false, dataFlow: 'Loading...' }
      ],
      securityStatus,
      dataFlowDetails
    };
  }
  
  // Extract code content from files (handle different file structures)
  const extractContent = (value) => {
    if (typeof value === 'string') return value;
    if (value && typeof value === 'object') {
      if (value.content) return value.content;
      if (value.code) return value.code;
      if (value.source) return value.source;
    }
    return '';
  };
  
  const allCode = Object.values(files).map(extractContent).join('\n');
  const fileNames = Object.keys(files);
  const fileEntries = Object.entries(files);
  
  // Debug: log what we found
  console.log('[SecurityCanvas] Analyzing files:', fileNames);
  console.log('[SecurityCanvas] Total code length:', allCode.length);
  
  // Enhanced patterns for detection
  const patterns = {
    // API/Routes detection
    expressRoutes: /app\.(get|post|put|delete|patch)\s*\(\s*['"`]([^'"`]+)['"`]/gi,
    routerRoutes: /router\.(get|post|put|delete|patch)\s*\(\s*['"`]([^'"`]+)['"`]/gi,
    fetchApi: /fetch\s*\(\s*['"`]([^'"`]+)['"`]/gi,
    axiosApi: /axios\.(get|post|put|delete|patch)\s*\(\s*['"`]([^'"`]+)['"`]/gi,
    nextApiRoute: /export\s+(default\s+)?(async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH)/gi,
    apiEndpoint: /['"`](\/api\/[^'"`]+)['"`]/gi,
    
    // Database detection
    mongodb: /mongoose|mongodb|MongoClient|\.findOne|\.find\(|\.insertOne|\.updateOne|\.deleteOne/gi,
    postgres: /pg|postgres|PostgreSQL|sequelize|\.query\(/gi,
    mysql: /mysql|mysql2/gi,
    prisma: /prisma|PrismaClient|prisma\.\w+\.(findMany|findUnique|create|update|delete)/gi,
    firebase: /firebase|firestore|\.collection\(|\.doc\(/gi,
    supabase: /supabase|createClient|\.from\(/gi,
    localStorage: /localStorage\.(getItem|setItem)|sessionStorage/gi,
    
    // State management
    useState: /useState\s*[<(]/gi,
    useEffect: /useEffect\s*\(/gi,
    redux: /useSelector|useDispatch|createSlice|configureStore/gi,
    zustand: /create\s*\(\s*\(set|useStore/gi,
    
    // Form handling
    formData: /FormData|new\s+FormData|formData\./gi,
    formSubmit: /onSubmit|handleSubmit|\.preventDefault/gi,
    inputHandling: /onChange|onInput|e\.target\.value/gi,
    
    // Auth detection
    jwt: /jwt|jsonwebtoken|JWT_SECRET|Bearer|token/gi,
    oauth: /oauth|passport|OAuth|google.*auth|facebook.*auth/gi,
    bcrypt: /bcrypt|bcryptjs|hash.*password|password.*hash|hashPassword/gi,
    authHeader: /authorization|authenticate|isAuthenticated|requireAuth|withAuth/gi,
    login: /login|signin|signIn|LoginForm|LoginPage/gi,
    register: /register|signup|signUp|RegisterForm|CreateAccount/gi,
    
    // Security patterns
    cors: /cors|CORS|Access-Control|crossorigin/gi,
    helmet: /helmet|security.*headers|X-Frame-Options|X-XSS/gi,
    csrf: /csrf|csurf|CSRF|_token/gi,
    rateLimit: /rate.*limit|express-rate-limit|throttle|limiter/gi,
    sanitize: /sanitize|DOMPurify|xss|escape|validator|encode/gi,
    https: /https:\/\/|SSL|TLS|secure.*cookie|httpOnly/gi,
    encryption: /crypto|encrypt|decrypt|AES|RSA|hash|cipher/gi,
    validation: /joi|yup|zod|validate|schema|\.required\(|\.string\(|\.email\(/gi
  };
  
  // Detect what's in the project
  const detected = {
    routes: [],
    database: null,
    hasJwt: patterns.jwt.test(allCode),
    hasOAuth: patterns.oauth.test(allCode),
    hasBcrypt: patterns.bcrypt.test(allCode),
    hasAuth: patterns.authHeader.test(allCode),
    hasCors: patterns.cors.test(allCode),
    hasHelmet: patterns.helmet.test(allCode),
    hasCsrf: patterns.csrf.test(allCode),
    hasRateLimit: patterns.rateLimit.test(allCode),
    hasSanitize: patterns.sanitize.test(allCode),
    hasHttps: patterns.https.test(allCode),
    hasEncryption: patterns.encryption.test(allCode),
    hasValidation: patterns.validation.test(allCode),
    hasLocalStorage: patterns.localStorage.test(allCode)
  };
  
  // Extract routes from multiple patterns
  let match;
  
  // Express app routes
  patterns.expressRoutes.lastIndex = 0;
  while ((match = patterns.expressRoutes.exec(allCode)) !== null) {
    detected.routes.push({ method: match[1].toUpperCase(), path: match[2] });
  }
  
  // Express router routes
  patterns.routerRoutes.lastIndex = 0;
  while ((match = patterns.routerRoutes.exec(allCode)) !== null) {
    detected.routes.push({ method: match[1].toUpperCase(), path: match[2] });
  }
  
  // Fetch API calls
  patterns.fetchApi.lastIndex = 0;
  while ((match = patterns.fetchApi.exec(allCode)) !== null) {
    if (match[1].startsWith('/') || match[1].includes('api')) {
      detected.routes.push({ method: 'FETCH', path: match[1] });
    }
  }
  
  // API endpoint strings
  patterns.apiEndpoint.lastIndex = 0;
  while ((match = patterns.apiEndpoint.exec(allCode)) !== null) {
    detected.routes.push({ method: 'API', path: match[1] });
  }
  
  // Next.js API routes
  patterns.nextApiRoute.lastIndex = 0;
  while ((match = patterns.nextApiRoute.exec(allCode)) !== null) {
    detected.routes.push({ method: match[3], path: '/api/[route]' });
  }
  
  // Log detection results
  console.log('[SecurityCanvas] Detected:', detected);
  
  // Detect database type (reset patterns before testing)
  patterns.mongodb.lastIndex = 0;
  patterns.postgres.lastIndex = 0;
  patterns.mysql.lastIndex = 0;
  patterns.prisma.lastIndex = 0;
  patterns.supabase.lastIndex = 0;
  patterns.firebase.lastIndex = 0;
  
  if (patterns.mongodb.test(allCode)) detected.database = 'MongoDB';
  else if (patterns.postgres.test(allCode)) detected.database = 'PostgreSQL';
  else if (patterns.mysql.test(allCode)) detected.database = 'MySQL';
  else if (patterns.prisma.test(allCode)) detected.database = 'Prisma DB';
  else if (patterns.supabase.test(allCode)) detected.database = 'Supabase';
  else if (patterns.firebase.test(allCode)) detected.database = 'Firebase';
  else if (detected.hasLocalStorage) detected.database = 'LocalStorage';
  else if (fileNames.some(f => f.toLowerCase().includes('db') || f.toLowerCase().includes('database') || f.toLowerCase().includes('model') || f.toLowerCase().includes('schema'))) {
    detected.database = 'Database';
  }
  
  // Update security status based on detection
  securityStatus[0].status = detected.hasHttps; // SSL/TLS
  securityStatus[1].status = detected.hasEncryption || detected.hasBcrypt; // Database Encrypted
  securityStatus[2].status = detected.hasCsrf; // CSRF Protection
  securityStatus[3].status = detected.hasHelmet; // Security Headers
  securityStatus[4].status = detected.hasCors; // CORS Configured
  
  // Detect additional features for detailed descriptions
  patterns.useState.lastIndex = 0;
  patterns.formSubmit.lastIndex = 0;
  patterns.login.lastIndex = 0;
  patterns.register.lastIndex = 0;
  const hasStateManagement = patterns.useState.test(allCode) || patterns.redux.test(allCode);
  const hasFormHandling = patterns.formSubmit.test(allCode);
  const hasLoginFlow = patterns.login.test(allCode);
  const hasRegisterFlow = patterns.register.test(allCode);
  
  // Build detailed data flow descriptions
  const buildClientDescription = () => {
    const features = [];
    if (hasStateManagement) features.push('Manages local state with React hooks');
    if (hasFormHandling) features.push('Handles form submissions');
    if (hasLoginFlow) features.push('User authentication interface');
    if (hasRegisterFlow) features.push('User registration flow');
    if (detected.routes.some(r => r.method === 'FETCH')) features.push('Makes API calls via fetch()');
    
    return features.length > 0 
      ? features.join('. ') + '.'
      : 'Frontend application renders UI and handles user interactions.';
  };
  
  const buildApiDescription = () => {
    const routeTypes = [...new Set(detected.routes.map(r => r.method))];
    const features = [];
    
    if (routeTypes.includes('GET')) features.push('GET requests to retrieve data');
    if (routeTypes.includes('POST')) features.push('POST requests to create resources');
    if (routeTypes.includes('PUT') || routeTypes.includes('PATCH')) features.push('PUT/PATCH requests to update data');
    if (routeTypes.includes('DELETE')) features.push('DELETE requests to remove resources');
    
    if (detected.hasValidation) features.push('Input validation before processing');
    if (detected.hasSanitize) features.push('Input sanitization to prevent XSS');
    
    return features.length > 0 
      ? 'Handles: ' + features.join(', ') + '.'
      : 'Processes API requests and returns responses.';
  };
  
  const buildDbDescription = () => {
    const features = [];
    if (detected.database === 'MongoDB') features.push('NoSQL document storage, stores data as JSON-like documents');
    else if (detected.database === 'PostgreSQL') features.push('Relational database with SQL queries, ACID compliant');
    else if (detected.database === 'MySQL') features.push('Relational database with SQL queries');
    else if (detected.database === 'Prisma DB') features.push('ORM layer with type-safe database access');
    else if (detected.database === 'Supabase') features.push('PostgreSQL database with real-time subscriptions');
    else if (detected.database === 'Firebase') features.push('Real-time NoSQL cloud database');
    else if (detected.database === 'LocalStorage') features.push('Browser-based key-value storage, persists locally');
    
    if (detected.hasEncryption) features.push('Data encrypted at rest');
    if (detected.hasBcrypt) features.push('Passwords hashed with bcrypt');
    
    return features.length > 0 
      ? features.join('. ') + '.'
      : 'Persistent data storage layer.';
  };
  
  // Build nodes with detailed descriptions - spread out horizontally
  const NODE_SPACING = 220; // Horizontal spacing between nodes (160px width + 60px gap)
  let currentX = 100;
  
  // Client node (always first)
  nodes.push({
    id: 'client',
    type: 'source',
    label: 'Client / Browser',
    x: currentX,
    y: 200,
    icon: Globe,
    color: '#ffffff',
    borderColor: '#444444',
    description: buildClientDescription(),
    dataFlow: hasFormHandling 
      ? 'Sends form data (JSON) to API endpoints' 
      : 'Sends HTTP requests with user actions'
  });
  currentX += NODE_SPACING;
  
  // Add security middleware nodes if detected
  let prevNodeId = 'client';
  let edgeCount = 0;
  
  if (detected.hasRateLimit) {
    const nodeId = 'detected_throttle';
    nodes.push({
      id: nodeId,
      type: 'security',
      label: 'Rate Limiter',
      x: currentX,
      y: 200,
      icon: Clock,
      color: NEON_COLORS.orange,
      borderColor: '#cc5500',
      securityType: 'throttle',
      detectedIn: 'Project files',
      description: 'Limits requests per IP to prevent DDoS and brute force attacks. Typically allows 100 requests per 15 minute window.',
      dataFlow: 'Counts requests per IP, blocks if threshold exceeded'
    });
    edges.push({ 
      id: `e${++edgeCount}`, 
      source: prevNodeId, 
      target: nodeId, 
      encrypted: detected.hasHttps,
      dataFlow: 'HTTP Request with IP address'
    });
    prevNodeId = nodeId;
    currentX += NODE_SPACING;
  }
  
  if (detected.hasJwt || detected.hasOAuth || detected.hasAuth) {
    const nodeId = 'detected_auth';
    const authLabel = detected.hasJwt ? 'JWT Auth' : (detected.hasOAuth ? 'OAuth' : 'Auth');
    const authDesc = detected.hasJwt 
      ? 'Validates JWT tokens from Authorization header. Decodes payload to extract user ID, roles, and permissions.'
      : detected.hasOAuth
        ? 'OAuth 2.0 authentication. Redirects to provider, exchanges code for access token.'
        : 'Authentication middleware verifies user identity before allowing access.';
    nodes.push({
      id: nodeId,
      type: 'security',
      label: authLabel,
      x: currentX,
      y: 200,
      icon: Key,
      color: NEON_COLORS.yellow,
      borderColor: '#cccc00',
      securityType: 'jwtAuth',
      detectedIn: 'Project files',
      description: authDesc,
      dataFlow: detected.hasJwt ? 'Extracts user from token: {id, email, role}' : 'Verifies user session'
    });
    edges.push({ 
      id: `e${++edgeCount}`, 
      source: prevNodeId, 
      target: nodeId, 
      encrypted: detected.hasHttps,
      dataFlow: detected.hasJwt ? 'Bearer token in Authorization header' : 'Session cookie'
    });
    prevNodeId = nodeId;
    currentX += NODE_SPACING;
  }
  
  if (detected.hasSanitize) {
    const nodeId = 'detected_sanitizer';
    nodes.push({
      id: nodeId,
      type: 'security',
      label: 'Input Sanitizer',
      x: currentX,
      y: 200,
      icon: Filter,
      color: NEON_COLORS.cyan,
      borderColor: '#00cccc',
      securityType: 'sanitizer',
      detectedIn: 'Project files',
      description: 'Sanitizes user input to prevent XSS attacks. Strips malicious HTML, JavaScript, and SQL injection attempts.',
      dataFlow: 'Cleans input: removes <script>, encodes special chars'
    });
    edges.push({ 
      id: `e${++edgeCount}`, 
      source: prevNodeId, 
      target: nodeId, 
      encrypted: detected.hasHttps,
      dataFlow: 'Raw user input data'
    });
    prevNodeId = nodeId;
    currentX += NODE_SPACING;
  }
  
  if (detected.hasValidation) {
    const nodeId = 'detected_validator';
    nodes.push({
      id: nodeId,
      type: 'security',
      label: 'Validator',
      x: currentX,
      y: 200,
      icon: Shield,
      color: NEON_COLORS.green,
      borderColor: '#00cc33',
      securityType: 'validator',
      detectedIn: 'Project files',
      description: 'Validates input against schema. Checks data types, required fields, formats (email, phone), and constraints.',
      dataFlow: 'Validates: types, required fields, formats'
    });
    edges.push({ 
      id: `e${++edgeCount}`, 
      source: prevNodeId, 
      target: nodeId, 
      encrypted: detected.hasHttps,
      dataFlow: 'Sanitized input for validation'
    });
    prevNodeId = nodeId;
    currentX += NODE_SPACING;
  }
  
  // API/Routes node
  const routeLabel = detected.routes.length > 0 
    ? `${detected.routes[0].method} ${detected.routes[0].path}${detected.routes.length > 1 ? ` (+${detected.routes.length - 1})` : ''}`
    : 'API Endpoints';
  
  nodes.push({
    id: 'api',
    type: 'logic',
    label: 'API Layer',
    x: currentX,
    y: 200,
    icon: Zap,
    color: NEON_COLORS.orange,
    borderColor: '#cc5500',
    route: routeLabel,
    routes: detected.routes,
    description: buildApiDescription(),
    dataFlow: detected.routes.length > 0 
      ? `Handles ${detected.routes.length} endpoint(s): ${detected.routes.slice(0, 3).map(r => r.path).join(', ')}${detected.routes.length > 3 ? '...' : ''}`
      : 'Processes incoming requests and routes to handlers'
  });
  edges.push({ 
    id: `e${++edgeCount}`, 
    source: prevNodeId, 
    target: 'api', 
    encrypted: detected.hasHttps,
    dataFlow: 'Validated request data'
  });
  currentX += NODE_SPACING;
  
  // Add encryption node if detected between API and DB
  if (detected.hasEncryption || detected.hasBcrypt) {
    const nodeId = 'detected_encryptor';
    nodes.push({
      id: nodeId,
      type: 'security',
      label: 'Encryptor',
      x: currentX,
      y: 200,
      icon: Lock,
      color: NEON_COLORS.blue,
      borderColor: '#0055cc',
      securityType: 'encryptor',
      detectedIn: 'Project files',
      description: detected.hasBcrypt 
        ? 'Hashes passwords using bcrypt with salt rounds. One-way encryption prevents password recovery.'
        : 'Encrypts sensitive data before storage. Uses industry-standard algorithms (AES, RSA).',
      dataFlow: detected.hasBcrypt ? 'password → bcrypt hash' : 'plaintext → ciphertext'
    });
    edges.push({ 
      id: `e${++edgeCount}`, 
      source: 'api', 
      target: nodeId, 
      encrypted: true,
      dataFlow: 'Sensitive data for encryption'
    });
    currentX += NODE_SPACING;
    
    // Database node
    if (detected.database) {
      nodes.push({
        id: 'database',
        type: 'destination',
        label: detected.database,
        x: currentX,
        y: 200,
        icon: Database,
        color: NEON_COLORS.green,
        borderColor: '#00cc33',
        description: buildDbDescription(),
        dataFlow: 'Persists: user data, sessions, app state'
      });
      edges.push({ 
        id: `e${++edgeCount}`, 
        source: nodeId, 
        target: 'database', 
        encrypted: true,
        dataFlow: 'Encrypted data for storage'
      });
    }
  } else if (detected.database) {
    // Database node without encryption
    nodes.push({
      id: 'database',
      type: 'destination',
      label: detected.database,
      x: currentX,
      y: 200,
      icon: Database,
      color: NEON_COLORS.green,
      borderColor: '#00cc33',
      description: buildDbDescription(),
      dataFlow: 'Persists: user data, sessions, app state'
    });
    edges.push({ 
      id: `e${++edgeCount}`, 
      source: 'api', 
      target: 'database', 
      encrypted: detected.hasEncryption,
      dataFlow: 'Query results and data mutations'
    });
  }
  
  return { nodes, edges, securityStatus, detected, dataFlowDetails };
};

const SecurityCanvas = ({ securityScore, securityIssues, onClose, onCodeInjection, onPipelineChange, projectFiles, isLoading, highlightedNodeId }) => {
  const canvasRef = useRef(null);
  
  // Analyze project files on mount or when files change
  const analysisResult = useMemo(() => analyzeProjectFiles(projectFiles), [projectFiles]);
  
  const [nodes, setNodes] = useState(analysisResult.nodes);
  const [edges, setEdges] = useState(analysisResult.edges);
  const [securityStatusItems, setSecurityStatusItems] = useState(analysisResult.securityStatus);
  const [pipelineVersion, setPipelineVersion] = useState(0); // Track changes
  
  // Re-analyze when project files change
  useEffect(() => {
    const result = analyzeProjectFiles(projectFiles);
    setNodes(result.nodes);
    setEdges(result.edges);
    setSecurityStatusItems(result.securityStatus);
  }, [projectFiles]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [draggedNodeType, setDraggedNodeType] = useState(null);
  const [hoveredEdge, setHoveredEdge] = useState(null);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [injectedMiddleware, setInjectedMiddleware] = useState([]);
  const [showShieldDropdown, setShowShieldDropdown] = useState(false);
  const [isSimulatingAttack, setIsSimulatingAttack] = useState(false);
  const [attackType, setAttackType] = useState(null);
  const [packetPositions, setPacketPositions] = useState({});
  const [highlightedNode, setHighlightedNode] = useState(null);
  const [draggingNode, setDraggingNode] = useState(null); // Node being dragged
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 }); // Offset from mouse to node corner
  const [customNodes, setCustomNodes] = useState([]); // User-created custom nodes
  const [showCustomNodeModal, setShowCustomNodeModal] = useState(false);
  const [newCustomNode, setNewCustomNode] = useState({ label: '', description: '', codeTemplate: '' });
  const [showAiNodeModal, setShowAiNodeModal] = useState(false);
  const [aiNodePrompt, setAiNodePrompt] = useState('');
  const [isAiGenerating, setIsAiGenerating] = useState(false);
  const [aiGeneratedNode, setAiGeneratedNode] = useState(null);

  // Handle highlighted node from issues deep-link
  useEffect(() => {
    if (highlightedNodeId) {
      // Find the node to highlight
      const targetNode = nodes.find(n => n.id === highlightedNodeId || n.id.includes(highlightedNodeId.replace('detected_', '')));
      if (targetNode) {
        setHighlightedNode(targetNode.id);
        setSelectedNode(targetNode);
        // Pan to center on the node
        setPan({
          x: -targetNode.x + 400,
          y: -targetNode.y + 200
        });
        setZoom(1.2);
        // Clear highlight after 5 seconds
        const timer = setTimeout(() => {
          setHighlightedNode(null);
        }, 5000);
        return () => clearTimeout(timer);
      }
    }
  }, [highlightedNodeId, nodes]);

  // Serialize pipeline to JSON for AI consumption
  const serializePipelineForAI = useCallback(() => {
    // Build ordered pipeline from edges
    const pipeline = [];
    const nodeMap = {};
    nodes.forEach(n => { nodeMap[n.id] = n; });
    
    // Find the starting node (source/client)
    const startNode = nodes.find(n => n.type === 'source');
    if (!startNode) return null;
    
    // Traverse the pipeline
    const visited = new Set();
    let currentId = startNode.id;
    
    while (currentId && !visited.has(currentId)) {
      visited.add(currentId);
      const node = nodeMap[currentId];
      if (!node) break;
      
      // Add to pipeline (skip icons since they can't be serialized)
      pipeline.push({
        id: node.id,
        type: node.type,
        label: node.label,
        securityType: node.securityType || null,
        config: node.config || {},
        codeTemplate: node.securityType ? SECURITY_NODE_TYPES[node.securityType]?.codeTemplate : null
      });
      
      // Find next node in chain
      const outEdge = edges.find(e => e.source === currentId);
      currentId = outEdge?.target;
    }
    
    return {
      version: pipelineVersion,
      timestamp: new Date().toISOString(),
      pipeline: pipeline,
      summary: {
        totalNodes: nodes.length,
        securityNodes: nodes.filter(n => n.type === 'security').length,
        injectedNodes: injectedMiddleware.length,
        hasAuth: nodes.some(n => n.securityType === 'jwtAuth' || n.label?.includes('Auth')),
        hasSanitizer: nodes.some(n => n.securityType === 'sanitizer'),
        hasValidator: nodes.some(n => n.securityType === 'validator'),
        hasEncryption: nodes.some(n => n.securityType === 'encryptor'),
        hasRateLimiting: nodes.some(n => n.securityType === 'throttle')
      }
    };
  }, [nodes, edges, pipelineVersion, injectedMiddleware]);

  // Notify parent when pipeline changes
  useEffect(() => {
    if (pipelineVersion > 0 && onPipelineChange) {
      const pipelineData = serializePipelineForAI();
      if (pipelineData) {
        onPipelineChange(pipelineData);
      }
    }
  }, [pipelineVersion, onPipelineChange, serializePipelineForAI]);

  // Helper to trigger pipeline change notification
  const notifyPipelineChange = useCallback(() => {
    setPipelineVersion(v => v + 1);
  }, []);

  // Live traffic animation
  useEffect(() => {
    const interval = setInterval(() => {
      setPacketPositions(prev => {
        const newPositions = {};
        edges.forEach(edge => {
          const currentPos = prev[edge.id] || 0;
          newPositions[edge.id] = (currentPos + 2) % 100;
        });
        return newPositions;
      });
    }, 50);
    return () => clearInterval(interval);
  }, [edges]);

  // Attack simulation
  const simulateAttack = (type) => {
    setIsSimulatingAttack(true);
    setAttackType(type);
    setTimeout(() => {
      setIsSimulatingAttack(false);
      setAttackType(null);
    }, 3000);
  };

  // Check if attack is blocked by security nodes
  const hasSecurityNode = (type) => {
    return nodes.some(n => n.securityType === type);
  };

  // Get point on Bézier curve at t (0-1)
  const getPointOnBezier = (sourceX, sourceY, targetX, targetY, t) => {
    const midX = (sourceX + targetX) / 2;
    const x = Math.pow(1-t, 3) * sourceX + 3 * Math.pow(1-t, 2) * t * midX + 3 * (1-t) * Math.pow(t, 2) * midX + Math.pow(t, 3) * targetX;
    const y = Math.pow(1-t, 3) * sourceY + 3 * Math.pow(1-t, 2) * t * sourceY + 3 * (1-t) * Math.pow(t, 2) * targetY + Math.pow(t, 3) * targetY;
    return { x, y };
  };

  // Calculate Bézier curve path
  const getBezierPath = (sourceX, sourceY, targetX, targetY) => {
    const midX = (sourceX + targetX) / 2;
    return `M ${sourceX} ${sourceY} C ${midX} ${sourceY}, ${midX} ${targetY}, ${targetX} ${targetY}`;
  };

  // Get node position (center of node for edge connections)
  const getNodePosition = (nodeId) => {
    const node = nodes.find(n => n.id === nodeId);
    // Node width is 160px, so center is at x + 80
    // Node approximate height is ~50px, so vertical center is at y + 25
    return node ? { x: node.x + 80, y: node.y + 25 } : { x: 0, y: 0 };
  };

  // Handle wheel zoom
  const handleWheel = useCallback((e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom(z => Math.min(Math.max(z * delta, 0.5), 2));
  }, []);

  // Handle pan start
  const handleMouseDown = (e) => {
    if (e.target === canvasRef.current || e.target.classList.contains('canvas-grid')) {
      setIsPanning(true);
      setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
      setShowShieldDropdown(false);
    }
  };

  // Handle node drag start
  const handleNodeMouseDown = (e, node) => {
    e.stopPropagation();
    e.preventDefault();
    
    // Calculate the offset from mouse position to node's top-left corner
    const canvasRect = canvasRef.current.getBoundingClientRect();
    const mouseX = (e.clientX - canvasRect.left - pan.x) / zoom;
    const mouseY = (e.clientY - canvasRect.top - pan.y) / zoom;
    
    setDraggingNode(node.id);
    setDragOffset({
      x: mouseX - node.x,
      y: mouseY - node.y
    });
    setSelectedNode(node);
  };

  // Handle pan/node move
  const handleMouseMove = (e) => {
    if (draggingNode) {
      // Move the node being dragged
      const canvasRect = canvasRef.current.getBoundingClientRect();
      const mouseX = (e.clientX - canvasRect.left - pan.x) / zoom;
      const mouseY = (e.clientY - canvasRect.top - pan.y) / zoom;
      
      const newX = mouseX - dragOffset.x;
      const newY = mouseY - dragOffset.y;
      
      setNodes(prev => prev.map(n => 
        n.id === draggingNode 
          ? { ...n, x: newX, y: newY }
          : n
      ));
    } else if (isPanning) {
      setPan({ x: e.clientX - panStart.x, y: e.clientY - panStart.y });
    }
  };

  // Handle pan/node drag end
  const handleMouseUp = () => {
    setIsPanning(false);
    setDraggingNode(null);
  };

  // Handle drag start from sidebar
  const handleDragStart = (nodeType) => {
    setDraggedNodeType(nodeType);
  };

  // Handle drop on edge
  const handleDropOnEdge = (edgeId, e) => {
    if (!draggedNodeType) return;
    
    const edge = edges.find(ed => ed.id === edgeId);
    if (!edge) return;
    
    // Get node type from built-in or custom nodes
    const allNodeTypes = getAllNodeTypes();
    const nodeType = allNodeTypes[draggedNodeType];
    if (!nodeType) return;
    
    const sourcePos = getNodePosition(edge.source);
    const targetPos = getNodePosition(edge.target);
    
    // Create new node in the middle
    const newNodeId = `${draggedNodeType}_${Date.now()}`;
    const newNode = {
      id: newNodeId,
      type: 'security',
      label: nodeType.label,
      x: (sourcePos.x + targetPos.x) / 2 - 80,
      y: (sourcePos.y + targetPos.y) / 2 - 30,
      icon: nodeType.icon,
      color: nodeType.color,
      borderColor: nodeType.borderColor,
      securityType: draggedNodeType,
      config: getDefaultConfig(draggedNodeType)
    };
    
    // Split the edge
    const newEdges = edges.filter(ed => ed.id !== edgeId);
    newEdges.push({ id: `e_${Date.now()}_1`, source: edge.source, target: newNodeId, encrypted: edge.encrypted });
    newEdges.push({ id: `e_${Date.now()}_2`, source: newNodeId, target: edge.target, encrypted: true });
    
    setNodes([...nodes, newNode]);
    setEdges(newEdges);
    setDraggedNodeType(null);
    setHoveredEdge(null);
    
    // Track injected middleware
    setInjectedMiddleware([...injectedMiddleware, {
      id: newNodeId,
      type: draggedNodeType,
      code: nodeType.codeTemplate,
      timestamp: new Date().toISOString()
    }]);
    
    // Notify parent of code injection
    if (onCodeInjection) {
      onCodeInjection(nodeType.codeTemplate, draggedNodeType);
    }
    
    // Notify pipeline change for AI
    notifyPipelineChange();
  };

  // Get default config for node type
  const getDefaultConfig = (type) => {
    switch (type) {
      case 'jwtAuth':
        return { algorithm: 'HS256', expiration: '1h', secret: '***hidden***' };
      case 'throttle':
        return { windowMs: 900000, maxRequests: 100 };
      case 'gatekeeper':
        return { requiredRole: 'user', allowedRoles: ['user', 'admin'] };
      case 'encryptor':
        return { algorithm: 'sha256', fields: ['password', 'ssn'] };
      case 'sanitizer':
        return { allowedTags: [], stripScripts: true };
      case 'validator':
        return { strict: true, abortEarly: false };
      default:
        return {};
    }
  };

  // Update node config
  const updateNodeConfig = (nodeId, key, value) => {
    setNodes(nodes.map(n => 
      n.id === nodeId 
        ? { ...n, config: { ...n.config, [key]: value } }
        : n
    ));
    // Notify pipeline change when config updates
    notifyPipelineChange();
  };

  // Remove node
  const removeNode = (nodeId) => {
    const node = nodes.find(n => n.id === nodeId);
    if (node.type === 'source' || node.type === 'destination') return; // Can't remove source/destination
    
    // Find edges connected to this node
    const incomingEdge = edges.find(e => e.target === nodeId);
    const outgoingEdge = edges.find(e => e.source === nodeId);
    
    // Reconnect the flow
    const newEdges = edges.filter(e => e.source !== nodeId && e.target !== nodeId);
    if (incomingEdge && outgoingEdge) {
      newEdges.push({
        id: `e_${Date.now()}`,
        source: incomingEdge.source,
        target: outgoingEdge.target,
        encrypted: incomingEdge.encrypted && outgoingEdge.encrypted
      });
    }
    
    setNodes(nodes.filter(n => n.id !== nodeId));
    setEdges(newEdges);
    setSelectedNode(null);
    setInjectedMiddleware(injectedMiddleware.filter(m => m.id !== nodeId));
    
    // Notify pipeline change when node is removed
    notifyPipelineChange();
  };

  // Create custom node type
  const createCustomNode = () => {
    if (!newCustomNode.label.trim()) return;
    
    const customId = `custom_${Date.now()}`;
    const customNodeType = {
      id: customId,
      label: newCustomNode.label,
      description: newCustomNode.description || 'Custom middleware',
      icon: Shield, // Default icon
      color: NEON_COLORS.purple,
      borderColor: '#9900cc',
      codeTemplate: newCustomNode.codeTemplate || `// Custom Middleware: ${newCustomNode.label}\nconst ${newCustomNode.label.toLowerCase().replace(/\s+/g, '')}Middleware = (req, res, next) => {\n  // Add your custom logic here\n  next();\n};`,
      isCustom: true
    };
    
    setCustomNodes([...customNodes, customNodeType]);
    setNewCustomNode({ label: '', description: '', codeTemplate: '' });
    setShowCustomNodeModal(false);
  };

  // Ask AI to generate a security node
  const askAiToCreateNode = async () => {
    if (!aiNodePrompt.trim()) return;
    
    setIsAiGenerating(true);
    setAiGeneratedNode(null);
    
    try {
      const response = await fetch('/api/ai/generate-security-node', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: aiNodePrompt,
          existingNodes: nodes.map(n => ({ label: n.label, type: n.type })),
          projectContext: Object.keys(projectFiles || {}).slice(0, 10) // Send some file names for context
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate node');
      }
      
      const data = await response.json();
      
      // Structure expected from AI:
      // { label: string, description: string, codeTemplate: string, securityType: string }
      const generatedNode = {
        id: `ai_${Date.now()}`,
        label: data.label || 'AI Generated Node',
        description: data.description || 'AI-generated security middleware',
        icon: Shield,
        color: NEON_COLORS.cyan,
        borderColor: '#00cccc',
        codeTemplate: data.codeTemplate || `// AI Generated Middleware\nconst middleware = (req, res, next) => {\n  // ${data.description || 'AI logic'}\n  next();\n};`,
        isCustom: true,
        isAiGenerated: true
      };
      
      setAiGeneratedNode(generatedNode);
    } catch (error) {
      console.error('[SecurityCanvas] AI node generation error:', error);
      // Fallback: Generate a basic node based on the prompt
      const fallbackNode = {
        id: `ai_${Date.now()}`,
        label: aiNodePrompt.split(' ').slice(0, 3).join(' ').substring(0, 20) || 'AI Node',
        description: aiNodePrompt.substring(0, 100),
        icon: Shield,
        color: NEON_COLORS.cyan,
        borderColor: '#00cccc',
        codeTemplate: `// AI Generated: ${aiNodePrompt.substring(0, 50)}\nconst middleware = (req, res, next) => {\n  // TODO: Implement ${aiNodePrompt.substring(0, 30)}\n  next();\n};`,
        isCustom: true,
        isAiGenerated: true
      };
      setAiGeneratedNode(fallbackNode);
    } finally {
      setIsAiGenerating(false);
    }
  };

  // Add AI-generated node to custom nodes
  const confirmAiNode = () => {
    if (!aiGeneratedNode) return;
    
    setCustomNodes([...customNodes, aiGeneratedNode]);
    setAiGeneratedNode(null);
    setAiNodePrompt('');
    setShowAiNodeModal(false);
  };

  // Get all available node types (built-in + custom)
  const getAllNodeTypes = () => {
    return { ...SECURITY_NODE_TYPES, ...Object.fromEntries(customNodes.map(n => [n.id, n])) };
  };

  // Get security status color
  const getStatusColor = (score) => {
    if (score >= 80) return NEON_COLORS.green;
    if (score >= 60) return NEON_COLORS.yellow;
    if (score >= 40) return NEON_COLORS.orange;
    return NEON_COLORS.red;
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      canvas.addEventListener('wheel', handleWheel, { passive: false });
      return () => canvas.removeEventListener('wheel', handleWheel);
    }
  }, [handleWheel]);

  // Count files being analyzed
  const fileCount = projectFiles ? Object.keys(projectFiles).length : 0;

  return (
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: '#000000',
      zIndex: 20,
      display: 'flex',
      fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace"
    }}>
      {/* Loading Overlay */}
      {isLoading && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.8)',
          zIndex: 100,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '16px'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: `3px solid ${NEON_COLORS.cyan}`,
            borderTopColor: 'transparent',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
          <div style={{ color: NEON_COLORS.cyan, fontSize: '14px' }}>
            Analyzing project files...
          </div>
          <div style={{ color: '#666666', fontSize: '11px' }}>
            Loading security pipeline data
          </div>
        </div>
      )}
      
      {/* Left Sidebar - Security Nodes */}
      <div style={{
        width: '240px',
        background: '#0a0a0a',
        borderRight: '1px solid #1a1a1a',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        <div style={{
          padding: '16px',
          borderBottom: '1px solid #1a1a1a'
        }}>
          <div style={{ color: '#a3a3a3', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>
            Security Nodes
          </div>
          <div style={{ color: '#666666', fontSize: '10px' }}>
            Drag onto connections to inject
          </div>
        </div>
        
        <div style={{ flex: 1, overflow: 'auto', padding: '12px' }}>
          {/* Built-in Node Types */}
          {Object.values(SECURITY_NODE_TYPES).map((nodeType) => {
            const Icon = nodeType.icon;
            return (
              <div
                key={nodeType.id}
                draggable
                onDragStart={() => handleDragStart(nodeType.id)}
                onDragEnd={() => setDraggedNodeType(null)}
                style={{
                  padding: '12px',
                  marginBottom: '8px',
                  background: '#050505',
                  border: '1px solid #1a1a1a',
                  borderRadius: '6px',
                  cursor: 'grab',
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = nodeType.borderColor;
                  e.currentTarget.style.boxShadow = `0 0 8px ${nodeType.borderColor}40`;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#1a1a1a';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                  <Icon size={16} color={nodeType.color} />
                  <span style={{ color: '#ffffff', fontSize: '12px', fontWeight: 500 }}>
                    {nodeType.label}
                  </span>
                </div>
                <div style={{ color: '#a3a3a3', fontSize: '10px', lineHeight: 1.4 }}>
                  {nodeType.description}
                </div>
              </div>
            );
          })}
          
          {/* Custom Node Types */}
          {customNodes.length > 0 && (
            <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid #1a1a1a' }}>
              <div style={{ color: '#a3a3a3', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>
                Custom Nodes ({customNodes.length})
              </div>
              {customNodes.map((nodeType) => {
                const Icon = nodeType.icon;
                return (
                  <div
                    key={nodeType.id}
                    draggable
                    onDragStart={() => handleDragStart(nodeType.id)}
                    onDragEnd={() => setDraggedNodeType(null)}
                    style={{
                      padding: '12px',
                      marginBottom: '8px',
                      background: '#050505',
                      border: '1px solid #1a1a1a',
                      borderRadius: '6px',
                      cursor: 'grab',
                      transition: 'all 0.15s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = nodeType.borderColor;
                      e.currentTarget.style.boxShadow = `0 0 8px ${nodeType.borderColor}40`;
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = '#1a1a1a';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                      <Icon size={16} color={nodeType.color} />
                      <span style={{ color: '#ffffff', fontSize: '12px', fontWeight: 500 }}>
                        {nodeType.label}
                      </span>
                      <span style={{ 
                        fontSize: '8px', 
                        padding: '2px 4px', 
                        background: `${NEON_COLORS.purple}20`, 
                        color: NEON_COLORS.purple,
                        borderRadius: '3px',
                        marginLeft: 'auto'
                      }}>
                        CUSTOM
                      </span>
                    </div>
                    <div style={{ color: '#a3a3a3', fontSize: '10px', lineHeight: 1.4 }}>
                      {nodeType.description}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
          
          {/* Create Custom Node Button */}
          <button
            onClick={() => setShowCustomNodeModal(true)}
            style={{
              width: '100%',
              padding: '12px',
              marginTop: '16px',
              background: 'transparent',
              border: `1px dashed ${NEON_COLORS.purple}60`,
              borderRadius: '6px',
              color: NEON_COLORS.purple,
              fontSize: '11px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'all 0.15s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = `${NEON_COLORS.purple}10`;
              e.currentTarget.style.borderColor = NEON_COLORS.purple;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
              e.currentTarget.style.borderColor = `${NEON_COLORS.purple}60`;
            }}
          >
            <span style={{ fontSize: '16px' }}>+</span>
            Create Custom Node
          </button>
          
          {/* Ask AI to Create Node Button */}
          <button
            onClick={() => setShowAiNodeModal(true)}
            style={{
              width: '100%',
              padding: '12px',
              marginTop: '8px',
              background: `linear-gradient(135deg, ${NEON_COLORS.cyan}15, ${NEON_COLORS.purple}15)`,
              border: `1px solid ${NEON_COLORS.cyan}40`,
              borderRadius: '6px',
              color: NEON_COLORS.cyan,
              fontSize: '11px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'all 0.15s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = `linear-gradient(135deg, ${NEON_COLORS.cyan}25, ${NEON_COLORS.purple}25)`;
              e.currentTarget.style.borderColor = NEON_COLORS.cyan;
              e.currentTarget.style.boxShadow = `0 0 15px ${NEON_COLORS.cyan}40`;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = `linear-gradient(135deg, ${NEON_COLORS.cyan}15, ${NEON_COLORS.purple}15)`;
              e.currentTarget.style.borderColor = `${NEON_COLORS.cyan}40`;
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            <Zap size={14} />
            Ask AI to Create Node
          </button>
        </div>
        
        {/* Injected Middleware List */}
        {injectedMiddleware.length > 0 && (
          <div style={{
            borderTop: '1px solid #1a1a1a',
            padding: '12px'
          }}>
            <div style={{ color: '#a3a3a3', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>
              Active Middleware ({injectedMiddleware.length})
            </div>
            {injectedMiddleware.map((mw) => (
              <div key={mw.id} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 8px',
                background: '#050505',
                borderRadius: '4px',
                marginBottom: '4px'
              }}>
                <div style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: NEON_COLORS.green,
                  boxShadow: `0 0 6px ${NEON_COLORS.green}`
                }} />
                <span style={{ color: '#a3a3a3', fontSize: '10px' }}>
                  {SECURITY_NODE_TYPES[mw.type]?.label}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Main Canvas */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Top Bar - Matte Black */}
        <div style={{
          height: '48px',
          background: '#111111',
          borderBottom: '1px solid #222222',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ color: '#ffffff', fontSize: '13px', fontWeight: 500 }}>
              Security Pipeline
            </span>
            
            {/* Files analyzed count */}
            <div style={{
              padding: '4px 10px',
              background: '#050505',
              borderRadius: '4px',
              border: '1px solid #222222'
            }}>
              <span style={{ color: '#666666', fontSize: '10px' }}>
                {fileCount > 0 ? `${fileCount} files analyzed` : 'Loading files...'}
              </span>
            </div>
            
            {/* Shield Status - Clickable with Dropdown */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setShowShieldDropdown(!showShieldDropdown)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '6px 12px',
                  background: '#050505',
                  borderRadius: '4px',
                  border: `1px solid ${getStatusColor(securityScore)}40`,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: getStatusColor(securityScore),
                  boxShadow: `0 0 8px ${getStatusColor(securityScore)}`
                }} />
                <span style={{ color: '#ffffff', fontSize: '11px' }}>
                  Shield: {securityScore}%
                </span>
                <ChevronDown size={12} color="#666666" />
              </button>
              
              {/* Shield Dropdown */}
              {showShieldDropdown && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  marginTop: '4px',
                  background: '#0a0a0a',
                  border: '1px solid #222222',
                  borderRadius: '6px',
                  padding: '8px 0',
                  minWidth: '200px',
                  zIndex: 100,
                  boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
                }}>
                  {securityStatusItems.map(item => (
                    <div key={item.id} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '8px 12px'
                    }}>
                      <div style={{
                        width: '16px',
                        height: '16px',
                        borderRadius: '4px',
                        background: item.status ? `${NEON_COLORS.green}20` : `${NEON_COLORS.red}20`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}>
                        {item.status ? (
                          <Check size={10} color={NEON_COLORS.green} />
                        ) : (
                          <X size={10} color={NEON_COLORS.red} />
                        )}
                      </div>
                      <span style={{ 
                        color: item.status ? '#ffffff' : '#666666', 
                        fontSize: '11px' 
                      }}>
                        {item.label}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Simulate Attack Button */}
            <button
              onClick={() => simulateAttack('sql_injection')}
              disabled={isSimulatingAttack}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                background: isSimulatingAttack ? '#1a0000' : 'transparent',
                border: `1px solid ${isSimulatingAttack ? NEON_COLORS.red : '#333333'}`,
                borderRadius: '4px',
                color: isSimulatingAttack ? NEON_COLORS.red : '#a3a3a3',
                fontSize: '11px',
                cursor: isSimulatingAttack ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => {
                if (!isSimulatingAttack) {
                  e.currentTarget.style.borderColor = NEON_COLORS.red;
                  e.currentTarget.style.color = NEON_COLORS.red;
                }
              }}
              onMouseLeave={(e) => {
                if (!isSimulatingAttack) {
                  e.currentTarget.style.borderColor = '#333333';
                  e.currentTarget.style.color = '#a3a3a3';
                }
              }}
            >
              <Play size={12} />
              {isSimulatingAttack ? 'Simulating...' : 'Simulate Attack'}
            </button>
            
            <span style={{ color: '#666666', fontSize: '11px' }}>
              Zoom: {Math.round(zoom * 100)}%
            </span>
            {zoom < 0.6 && (
              <span style={{ 
                color: NEON_COLORS.cyan, 
                fontSize: '10px',
                padding: '2px 6px',
                background: `${NEON_COLORS.cyan}15`,
                borderRadius: '4px',
                border: `1px solid ${NEON_COLORS.cyan}30`
              }}>
                Compact View
              </span>
            )}
            <button
              onClick={onClose}
              style={{
                padding: '6px 12px',
                background: 'transparent',
                border: '1px solid #333333',
                borderRadius: '4px',
                color: '#a3a3a3',
                fontSize: '11px',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#ffffff';
                e.currentTarget.style.color = '#ffffff';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#333333';
                e.currentTarget.style.color = '#a3a3a3';
              }}
            >
              Close
            </button>
          </div>
        </div>

        {/* Canvas Area */}
        <div
          ref={canvasRef}
          className="canvas-grid"
          style={{
            flex: 1,
            position: 'relative',
            overflow: 'hidden',
            cursor: isPanning ? 'grabbing' : 'grab',
            background: '#000000',
            backgroundImage: `radial-gradient(circle, #222222 1px, transparent 1px)`,
            backgroundSize: `${20 * zoom}px ${20 * zoom}px`,
            backgroundPosition: `${pan.x}px ${pan.y}px`
          }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onClick={() => setShowShieldDropdown(false)}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            // Handle drop on canvas (will be caught by edge handlers)
          }}
        >
          <svg
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              pointerEvents: 'all',
              overflow: 'visible'
            }}
          >
            <defs>
              {/* Glow filters */}
              <filter id="glow-green" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
              <filter id="glow-red" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
              <filter id="glow-grey" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="1" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>
            
            <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
              {/* Render Edges - Bézier Curves */}
              {edges.map((edge) => {
                const sourcePos = getNodePosition(edge.source);
                const targetPos = getNodePosition(edge.target);
                const isHovered = hoveredEdge === edge.id;
                const isDragging = draggedNodeType !== null;
                const packetT = (packetPositions[edge.id] || 0) / 100;
                const packetPos = getPointOnBezier(sourcePos.x, sourcePos.y, targetPos.x, targetPos.y, packetT);
                
                // During attack simulation, packets turn red if no sanitizer
                const isAttackPacket = isSimulatingAttack && !hasSecurityNode('sanitizer');
                const packetColor = isAttackPacket ? NEON_COLORS.red : NEON_COLORS.green;
                
                // Default wire color is dim grey, glows green when data flows
                const wireBaseColor = '#333333';
                const wireActiveColor = NEON_COLORS.green;
                const wireColor = isHovered ? (isDragging ? '#ffffff' : '#555555') : wireBaseColor;
                
                return (
                  <g key={edge.id}>
                    {/* Invisible wider path for easier interaction - handles drag and drop */}
                    <path
                      d={getBezierPath(sourcePos.x, sourcePos.y, targetPos.x, targetPos.y)}
                      fill="none"
                      stroke={isHovered && isDragging ? 'rgba(0, 255, 65, 0.3)' : 'transparent'}
                      strokeWidth={30}
                      strokeLinecap="round"
                      style={{ 
                        pointerEvents: 'stroke', 
                        cursor: isDragging ? 'copy' : 'pointer',
                        transition: 'stroke 0.15s ease'
                      }}
                      onMouseEnter={() => setHoveredEdge(edge.id)}
                      onMouseLeave={() => setHoveredEdge(null)}
                      onMouseUp={(e) => handleDropOnEdge(edge.id, e)}
                      onDragOver={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setHoveredEdge(edge.id);
                      }}
                      onDragLeave={() => setHoveredEdge(null)}
                      onDrop={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleDropOnEdge(edge.id, e);
                      }}
                    />
                    
                    {/* Base wire - dim grey Bézier curve */}
                    <path
                      d={getBezierPath(sourcePos.x, sourcePos.y, targetPos.x, targetPos.y)}
                      fill="none"
                      stroke={wireColor}
                      strokeWidth={isHovered ? 3 : 2}
                      strokeLinecap="round"
                      filter="url(#glow-grey)"
                      style={{ transition: 'all 0.15s ease', pointerEvents: 'none' }}
                    />
                    
                    {/* Glowing overlay that follows the packet - neon green trail */}
                    <path
                      d={getBezierPath(sourcePos.x, sourcePos.y, targetPos.x, targetPos.y)}
                      fill="none"
                      stroke={isAttackPacket ? NEON_COLORS.red : wireActiveColor}
                      strokeWidth={3}
                      strokeLinecap="round"
                      strokeDasharray="20 180"
                      strokeDashoffset={-packetT * 200}
                      filter={isAttackPacket ? 'url(#glow-red)' : 'url(#glow-green)'}
                      style={{ transition: 'stroke 0.15s ease', pointerEvents: 'none' }}
                    />
                    
                    {/* Animated data packet */}
                    <circle
                      cx={packetPos.x}
                      cy={packetPos.y}
                      r={5}
                      fill={packetColor}
                      filter={isAttackPacket ? 'url(#glow-red)' : 'url(#glow-green)'}
                      style={{ pointerEvents: 'none' }}
                    />
                    
                    {/* Connection point at target - arrow indicator */}
                    <circle
                      cx={targetPos.x - 15}
                      cy={targetPos.y}
                      r={4}
                      fill={wireBaseColor}
                      style={{ pointerEvents: 'none' }}
                    />
                    {/* Arrow head */}
                    <polygon
                      points={`${targetPos.x - 5},${targetPos.y} ${targetPos.x - 12},${targetPos.y - 5} ${targetPos.x - 12},${targetPos.y + 5}`}
                      fill={wireBaseColor}
                      style={{ pointerEvents: 'none' }}
                    />
                    
                    {/* Data flow label on hover */}
                    {edge.dataFlow && isHovered && (
                      <g>
                        <rect
                          x={(sourcePos.x + targetPos.x) / 2 - 80}
                          y={(sourcePos.y + targetPos.y) / 2 - 28}
                          width="160"
                          height="20"
                          rx="4"
                          fill="#0a0a0a"
                          stroke={NEON_COLORS.green}
                          strokeWidth="1"
                        />
                        <text
                          x={(sourcePos.x + targetPos.x) / 2}
                          y={(sourcePos.y + targetPos.y) / 2 - 14}
                          fill={NEON_COLORS.green}
                          fontSize="10"
                          textAnchor="middle"
                          fontFamily="'JetBrains Mono', monospace"
                        >
                          {edge.dataFlow.length > 25 ? edge.dataFlow.substring(0, 25) + '...' : edge.dataFlow}
                        </text>
                      </g>
                    )}
                  </g>
                );
              })}
            </g>
          </svg>

          {/* Render Nodes */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: '0 0'
            }}
          >
            {nodes.map((node) => {
              const Icon = node.icon;
              const isSelected = selectedNode?.id === node.id;
              const isHighlighted = highlightedNode === node.id;
              const isDragging = draggingNode === node.id;
              const borderColor = node.borderColor || '#333333';
              const isCompactView = zoom < 0.6; // LOD: Extra compact when zoomed out
              
              // Generate 1-line summary from description
              const getOneLiner = () => {
                if (node.type === 'source') return 'Entry point';
                if (node.type === 'destination') return 'Data storage';
                if (node.securityType === 'jwtAuth') return 'Token verification';
                if (node.securityType === 'sanitizer') return 'Input filtering';
                if (node.securityType === 'validator') return 'Schema validation';
                if (node.securityType === 'encryptor') return 'Data encryption';
                if (node.securityType === 'throttle') return 'Rate limiting';
                if (node.securityType === 'gatekeeper') return 'Access control';
                if (node.label?.includes('API')) return 'Request routing';
                if (node.label?.includes('Auth')) return 'Authentication';
                if (node.label?.includes('Sanitizer')) return 'XSS protection';
                if (node.label?.includes('Validator')) return 'Input validation';
                if (node.label?.includes('Encryptor')) return 'Encryption layer';
                if (node.label?.includes('Rate')) return 'DDoS protection';
                return node.type || 'Processing';
              };
              
              return (
                <div
                  key={node.id}
                  onMouseDown={(e) => handleNodeMouseDown(e, node)}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (!draggingNode) {
                      setSelectedNode(node);
                      setShowShieldDropdown(false);
                    }
                  }}
                  style={{
                    position: 'absolute',
                    left: node.x,
                    top: node.y,
                    width: isCompactView ? '100px' : '160px',
                    padding: isCompactView ? '8px' : '10px 12px',
                    background: '#050505',
                    border: isHighlighted 
                      ? '2px solid #ff0033' 
                      : `1px solid ${isSelected ? node.color : borderColor}`,
                    borderRadius: '8px',
                    cursor: isDragging ? 'grabbing' : 'grab',
                    transition: isDragging || isHighlighted ? 'none' : 'all 0.2s ease',
                    boxShadow: isHighlighted 
                      ? '0 0 20px #ff0033, 0 0 40px #ff003380' 
                      : isDragging 
                        ? `0 0 20px ${node.color}60, 0 8px 32px rgba(0,0,0,0.5)`
                        : isSelected ? `0 0 15px ${node.color}50` : 'none',
                    animation: isHighlighted ? 'pulseRedBorder 1s ease-in-out infinite' : 'none',
                    zIndex: isDragging ? 200 : isHighlighted ? 100 : isSelected ? 50 : 1,
                    userSelect: 'none'
                  }}
                >
                  {/* Clean Header: Icon + Title + Status */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{
                      width: isCompactView ? '22px' : '26px',
                      height: isCompactView ? '22px' : '26px',
                      borderRadius: '6px',
                      background: `${node.color}20`,
                      border: `1px solid ${node.color}40`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}>
                      <Icon size={isCompactView ? 11 : 13} color={node.color} />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ 
                        color: '#ffffff', 
                        fontSize: isCompactView ? '9px' : '11px', 
                        fontWeight: 600,
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        lineHeight: 1.2
                      }}>
                        {node.label}
                      </div>
                      {/* 1-line summary - hidden in ultra compact */}
                      {!isCompactView && (
                        <div style={{ 
                          color: '#666666', 
                          fontSize: '9px',
                          marginTop: '2px',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis'
                        }}>
                          {getOneLiner()}
                        </div>
                      )}
                    </div>
                    {/* Status Dot */}
                    <div style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      background: node.type === 'security' || node.securityType ? NEON_COLORS.green : node.color,
                      boxShadow: `0 0 6px ${node.type === 'security' || node.securityType ? NEON_COLORS.green : node.color}`,
                      flexShrink: 0
                    }} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Attack Simulation Overlay */}
          {isSimulatingAttack && (
            <div style={{
              position: 'absolute',
              top: '20px',
              left: '50%',
              transform: 'translateX(-50%)',
              padding: '12px 20px',
              background: hasSecurityNode('sanitizer') ? `${NEON_COLORS.green}15` : `${NEON_COLORS.red}15`,
              border: `1px solid ${hasSecurityNode('sanitizer') ? NEON_COLORS.green : NEON_COLORS.red}`,
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: hasSecurityNode('sanitizer') ? NEON_COLORS.green : NEON_COLORS.red,
                animation: 'pulse 1s infinite'
              }} />
              <span style={{ 
                color: hasSecurityNode('sanitizer') ? NEON_COLORS.green : NEON_COLORS.red, 
                fontSize: '12px' 
              }}>
                {hasSecurityNode('sanitizer') 
                  ? 'SQL Injection BLOCKED by Sanitizer' 
                  : 'SQL Injection DETECTED - Add Sanitizer to block'}
              </span>
            </div>
          )}

          {/* Drop Indicator */}
          {draggedNodeType && (
            <div style={{
              position: 'absolute',
              bottom: '20px',
              left: '50%',
              transform: 'translateX(-50%)',
              padding: '8px 16px',
              background: '#0a0a0a',
              border: `1px solid ${SECURITY_NODE_TYPES[draggedNodeType]?.borderColor}`,
              borderRadius: '6px',
              color: '#ffffff',
              fontSize: '11px'
            }}>
              Drop on a connection to inject {SECURITY_NODE_TYPES[draggedNodeType]?.label}
            </div>
          )}
        </div>
      </div>

      {/* Right Panel - Inspector */}
      {selectedNode && (
        <div style={{
          width: '280px',
          background: '#0a0a0a',
          borderLeft: '1px solid #1a1a1a',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <div style={{
            padding: '16px',
            borderBottom: '1px solid #1a1a1a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <span style={{ color: '#ffffff', fontSize: '12px', fontWeight: 500 }}>
              Properties
            </span>
            <button
              onClick={() => setSelectedNode(null)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#666666',
                cursor: 'pointer',
                fontSize: '16px',
                lineHeight: 1,
                padding: '4px'
              }}
              onMouseEnter={(e) => e.currentTarget.style.color = '#ffffff'}
              onMouseLeave={(e) => e.currentTarget.style.color = '#666666'}
            >
              <X size={14} />
            </button>
          </div>
          
          <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
            {/* Node Info */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ color: '#666666', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>
                Node Details
              </div>
              <div style={{
                padding: '12px',
                background: '#050505',
                borderRadius: '6px',
                border: `1px solid ${selectedNode.borderColor || '#1a1a1a'}`
              }}>
                <div style={{ color: '#ffffff', fontSize: '12px', fontWeight: 500, marginBottom: '4px' }}>
                  {selectedNode.label}
                </div>
                <div style={{ color: '#666666', fontSize: '10px', marginBottom: '8px' }}>
                  Type: {selectedNode.type}
                </div>
                {selectedNode.detectedIn && (
                  <div style={{ 
                    color: NEON_COLORS.green, 
                    fontSize: '9px', 
                    marginTop: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    <div style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      background: NEON_COLORS.green,
                      boxShadow: `0 0 4px ${NEON_COLORS.green}`
                    }} />
                    Auto-detected in project
                  </div>
                )}
              </div>
            </div>
            
            {/* Business Logic Description */}
            {selectedNode.description && (
              <div style={{ marginBottom: '20px' }}>
                <div style={{ color: '#666666', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>
                  Business Logic
                </div>
                <div style={{
                  padding: '12px',
                  background: '#050505',
                  borderRadius: '6px',
                  border: '1px solid #1a1a1a'
                }}>
                  <div style={{ color: '#a3a3a3', fontSize: '11px', lineHeight: 1.5 }}>
                    {selectedNode.description}
                  </div>
                </div>
              </div>
            )}
            
            {/* Data Flow Details */}
            {selectedNode.dataFlow && (
              <div style={{ marginBottom: '20px' }}>
                <div style={{ color: '#666666', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>
                  Data Flow
                </div>
                <div style={{
                  padding: '12px',
                  background: `${NEON_COLORS.green}08`,
                  borderRadius: '6px',
                  border: `1px solid ${NEON_COLORS.green}30`
                }}>
                  <div style={{ color: NEON_COLORS.green, fontSize: '11px', fontFamily: 'monospace' }}>
                    {selectedNode.dataFlow}
                  </div>
                </div>
              </div>
            )}
            
            {/* Detected Routes */}
            {selectedNode.routes && selectedNode.routes.length > 0 && (
              <div style={{ marginBottom: '20px' }}>
                <div style={{ color: '#666666', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>
                  Detected Routes ({selectedNode.routes.length})
                </div>
                <div style={{
                  padding: '8px',
                  background: '#050505',
                  borderRadius: '6px',
                  border: '1px solid #1a1a1a',
                  maxHeight: '150px',
                  overflow: 'auto'
                }}>
                  {selectedNode.routes.map((r, i) => (
                    <div key={i} style={{
                      padding: '4px 8px',
                      background: '#0a0a0a',
                      borderRadius: '4px',
                      marginBottom: '4px',
                      display: 'flex',
                      gap: '8px',
                      alignItems: 'center'
                    }}>
                      <span style={{
                        padding: '2px 6px',
                        background: r.method === 'GET' ? `${NEON_COLORS.green}20` :
                                   r.method === 'POST' ? `${NEON_COLORS.blue}20` :
                                   r.method === 'PUT' || r.method === 'PATCH' ? `${NEON_COLORS.yellow}20` :
                                   r.method === 'DELETE' ? `${NEON_COLORS.red}20` :
                                   `${NEON_COLORS.cyan}20`,
                        color: r.method === 'GET' ? NEON_COLORS.green :
                               r.method === 'POST' ? NEON_COLORS.blue :
                               r.method === 'PUT' || r.method === 'PATCH' ? NEON_COLORS.yellow :
                               r.method === 'DELETE' ? NEON_COLORS.red :
                               NEON_COLORS.cyan,
                        borderRadius: '3px',
                        fontSize: '9px',
                        fontWeight: 600
                      }}>
                        {r.method}
                      </span>
                      <code style={{ color: '#a3a3a3', fontSize: '10px' }}>
                        {r.path}
                      </code>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Config Fields */}
            {selectedNode.config && (
              <div style={{ marginBottom: '20px' }}>
                <div style={{ color: '#666666', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>
                  Configuration
                </div>
                {Object.entries(selectedNode.config).map(([key, value]) => (
                  <div key={key} style={{ marginBottom: '12px' }}>
                    <label style={{
                      display: 'block',
                      color: '#a3a3a3',
                      fontSize: '10px',
                      marginBottom: '4px',
                      textTransform: 'capitalize'
                    }}>
                      {key.replace(/([A-Z])/g, ' $1').trim()}
                    </label>
                    <input
                      type={typeof value === 'number' ? 'number' : 'text'}
                      value={Array.isArray(value) ? value.join(', ') : value}
                      onChange={(e) => updateNodeConfig(selectedNode.id, key, e.target.value)}
                      style={{
                        width: '100%',
                        padding: '8px 10px',
                        background: '#050505',
                        border: '1px solid #222222',
                        borderRadius: '4px',
                        color: '#ffffff',
                        fontSize: '11px',
                        fontFamily: 'inherit',
                        outline: 'none',
                        transition: 'border-color 0.15s ease'
                      }}
                      onFocus={(e) => e.currentTarget.style.borderColor = selectedNode.borderColor || '#444444'}
                      onBlur={(e) => e.currentTarget.style.borderColor = '#222222'}
                    />
                  </div>
                ))}
              </div>
            )}

            {/* Code Preview */}
            {selectedNode.securityType && SECURITY_NODE_TYPES[selectedNode.securityType] && (
              <div style={{ marginBottom: '20px' }}>
                <div style={{ color: '#666666', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>
                  Generated Code
                </div>
                <pre style={{
                  padding: '12px',
                  background: '#050505',
                  borderRadius: '6px',
                  border: '1px solid #1a1a1a',
                  color: '#a3a3a3',
                  fontSize: '9px',
                  lineHeight: 1.5,
                  overflow: 'auto',
                  maxHeight: '200px',
                  margin: 0
                }}>
                  {SECURITY_NODE_TYPES[selectedNode.securityType].codeTemplate}
                </pre>
              </div>
            )}

            {/* Remove Button */}
            {selectedNode.type === 'security' && (
              <button
                onClick={() => removeNode(selectedNode.id)}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: 'transparent',
                  border: `1px solid ${NEON_COLORS.red}`,
                  borderRadius: '4px',
                  color: NEON_COLORS.red,
                  fontSize: '11px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = `${NEON_COLORS.red}15`;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent';
                }}
              >
                Remove Node
              </button>
            )}
          </div>

          {/* Security Issues */}
          {securityIssues && securityIssues.length > 0 && (
            <div style={{
              borderTop: '1px solid #1a1a1a',
              padding: '16px'
            }}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '6px',
                marginBottom: '12px'
              }}>
                <AlertTriangle size={12} color={NEON_COLORS.orange} />
                <span style={{ color: NEON_COLORS.orange, fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                  Issues ({securityIssues.length})
                </span>
              </div>
              {securityIssues.slice(0, 3).map((issue, index) => (
                <div key={index} style={{
                  padding: '8px 10px',
                  background: '#050505',
                  borderRadius: '4px',
                  marginBottom: '6px',
                  borderLeft: `2px solid ${
                    issue.severity === 'critical' ? NEON_COLORS.red 
                    : issue.severity === 'high' ? NEON_COLORS.orange 
                    : NEON_COLORS.yellow
                  }`
                }}>
                  <div style={{ color: '#ffffff', fontSize: '10px', marginBottom: '2px' }}>
                    {issue.issue}
                  </div>
                  <div style={{ color: '#666666', fontSize: '9px' }}>
                    {issue.file}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      {/* Custom Node Creation Modal */}
      {showCustomNodeModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}
        onClick={() => setShowCustomNodeModal(false)}
        >
          <div 
            style={{
              width: '500px',
              background: '#0a0a0a',
              border: `1px solid ${NEON_COLORS.purple}40`,
              borderRadius: '12px',
              padding: '24px',
              boxShadow: `0 0 40px ${NEON_COLORS.purple}20`
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between',
              marginBottom: '20px'
            }}>
              <h3 style={{ color: '#ffffff', fontSize: '16px', fontWeight: 600, margin: 0 }}>
                Create Custom Security Node
              </h3>
              <button
                onClick={() => setShowCustomNodeModal(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#666',
                  cursor: 'pointer',
                  fontSize: '20px'
                }}
              >
                ×
              </button>
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ color: '#888', fontSize: '11px', display: 'block', marginBottom: '6px' }}>
                Node Name *
              </label>
              <input
                type="text"
                value={newCustomNode.label}
                onChange={(e) => setNewCustomNode({ ...newCustomNode, label: e.target.value })}
                placeholder="e.g., API Logger, Cache Layer"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  background: '#050505',
                  border: '1px solid #222',
                  borderRadius: '6px',
                  color: '#fff',
                  fontSize: '13px',
                  outline: 'none'
                }}
              />
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ color: '#888', fontSize: '11px', display: 'block', marginBottom: '6px' }}>
                Description
              </label>
              <input
                type="text"
                value={newCustomNode.description}
                onChange={(e) => setNewCustomNode({ ...newCustomNode, description: e.target.value })}
                placeholder="Brief description of what this node does"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  background: '#050505',
                  border: '1px solid #222',
                  borderRadius: '6px',
                  color: '#fff',
                  fontSize: '13px',
                  outline: 'none'
                }}
              />
            </div>
            
            <div style={{ marginBottom: '20px' }}>
              <label style={{ color: '#888', fontSize: '11px', display: 'block', marginBottom: '6px' }}>
                Code Template (Express Middleware)
              </label>
              <textarea
                value={newCustomNode.codeTemplate}
                onChange={(e) => setNewCustomNode({ ...newCustomNode, codeTemplate: e.target.value })}
                placeholder={`// Your custom middleware code\nconst myMiddleware = (req, res, next) => {\n  // Add your logic here\n  next();\n};`}
                style={{
                  width: '100%',
                  height: '150px',
                  padding: '12px',
                  background: '#050505',
                  border: '1px solid #222',
                  borderRadius: '6px',
                  color: NEON_COLORS.green,
                  fontSize: '12px',
                  fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                  outline: 'none',
                  resize: 'vertical'
                }}
              />
            </div>
            
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowCustomNodeModal(false)}
                style={{
                  padding: '10px 20px',
                  background: 'transparent',
                  border: '1px solid #333',
                  borderRadius: '6px',
                  color: '#888',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={createCustomNode}
                disabled={!newCustomNode.label.trim()}
                style={{
                  padding: '10px 20px',
                  background: newCustomNode.label.trim() ? NEON_COLORS.purple : '#333',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#fff',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: newCustomNode.label.trim() ? 'pointer' : 'not-allowed',
                  opacity: newCustomNode.label.trim() ? 1 : 0.5
                }}
              >
                Create Node
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Ask AI Modal */}
      {showAiNodeModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.85)',
          zIndex: 200,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
        onClick={() => setShowAiNodeModal(false)}
        >
          <div 
            onClick={(e) => e.stopPropagation()}
            style={{
              background: '#0a0a0a',
              border: `1px solid ${NEON_COLORS.cyan}40`,
              borderRadius: '12px',
              padding: '24px',
              width: '520px',
              maxHeight: '80vh',
              overflow: 'auto',
              boxShadow: `0 0 40px ${NEON_COLORS.cyan}20`
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Zap size={20} color={NEON_COLORS.cyan} />
                <span style={{ color: '#fff', fontSize: '16px', fontWeight: 600 }}>Ask AI to Create Node</span>
              </div>
              <button
                onClick={() => setShowAiNodeModal(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#666',
                  cursor: 'pointer',
                  padding: '4px'
                }}
              >
                <X size={18} />
              </button>
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ color: '#888', fontSize: '11px', display: 'block', marginBottom: '8px' }}>
                Describe the security node you want to create
              </label>
              <textarea
                value={aiNodePrompt}
                onChange={(e) => setAiNodePrompt(e.target.value)}
                placeholder="e.g., Create a middleware that logs all API requests with timestamps and user IDs, or Create a GDPR compliance checker that validates data before storage..."
                style={{
                  width: '100%',
                  height: '100px',
                  padding: '12px',
                  background: '#050505',
                  border: `1px solid ${NEON_COLORS.cyan}30`,
                  borderRadius: '8px',
                  color: '#fff',
                  fontSize: '13px',
                  fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                  outline: 'none',
                  resize: 'vertical'
                }}
                onFocus={(e) => e.target.style.borderColor = NEON_COLORS.cyan}
                onBlur={(e) => e.target.style.borderColor = `${NEON_COLORS.cyan}30`}
              />
            </div>
            
            {/* Generate Button */}
            {!aiGeneratedNode && (
              <button
                onClick={askAiToCreateNode}
                disabled={!aiNodePrompt.trim() || isAiGenerating}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: aiNodePrompt.trim() && !isAiGenerating 
                    ? `linear-gradient(135deg, ${NEON_COLORS.cyan}, ${NEON_COLORS.purple})` 
                    : '#222',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: aiNodePrompt.trim() && !isAiGenerating ? 'pointer' : 'not-allowed',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  opacity: aiNodePrompt.trim() ? 1 : 0.5
                }}
              >
                {isAiGenerating ? (
                  <>
                    <div style={{
                      width: '14px',
                      height: '14px',
                      border: '2px solid #fff',
                      borderTopColor: 'transparent',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }} />
                    Generating...
                  </>
                ) : (
                  <>
                    <Zap size={14} />
                    Generate Node with AI
                  </>
                )}
              </button>
            )}
            
            {/* AI Generated Node Preview */}
            {aiGeneratedNode && (
              <div style={{ marginTop: '16px' }}>
                <div style={{ 
                  color: NEON_COLORS.green, 
                  fontSize: '11px', 
                  textTransform: 'uppercase', 
                  letterSpacing: '0.1em', 
                  marginBottom: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <Check size={14} />
                  Generated Node Preview
                </div>
                
                <div style={{
                  background: '#050505',
                  border: `1px solid ${NEON_COLORS.cyan}30`,
                  borderRadius: '8px',
                  padding: '16px'
                }}>
                  <div style={{ color: '#fff', fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>
                    {aiGeneratedNode.label}
                  </div>
                  <div style={{ color: '#888', fontSize: '12px', marginBottom: '12px' }}>
                    {aiGeneratedNode.description}
                  </div>
                  <div style={{
                    background: '#000',
                    border: '1px solid #222',
                    borderRadius: '6px',
                    padding: '12px',
                    maxHeight: '150px',
                    overflow: 'auto'
                  }}>
                    <pre style={{ 
                      color: NEON_COLORS.green, 
                      fontSize: '11px', 
                      fontFamily: "'JetBrains Mono', monospace",
                      margin: 0,
                      whiteSpace: 'pre-wrap'
                    }}>
                      {aiGeneratedNode.codeTemplate}
                    </pre>
                  </div>
                </div>
                
                <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                  <button
                    onClick={() => {
                      setAiGeneratedNode(null);
                    }}
                    style={{
                      flex: 1,
                      padding: '10px',
                      background: 'transparent',
                      border: '1px solid #333',
                      borderRadius: '6px',
                      color: '#888',
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    Regenerate
                  </button>
                  <button
                    onClick={confirmAiNode}
                    style={{
                      flex: 1,
                      padding: '10px',
                      background: NEON_COLORS.green,
                      border: 'none',
                      borderRadius: '6px',
                      color: '#000',
                      fontSize: '12px',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    Add to Toolbox
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* CSS for animations */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes pulseRedBorder {
          0%, 100% { 
            box-shadow: 0 0 10px #ff0033, 0 0 20px #ff003380;
            border-color: #ff0033;
          }
          50% { 
            box-shadow: 0 0 25px #ff0033, 0 0 50px #ff003380, 0 0 75px #ff003340;
            border-color: #ff6666;
          }
        }
      `}</style>
    </div>
  );
};

export default SecurityCanvas;
