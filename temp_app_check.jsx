// motion is provided globally by the sandbox environment
// motion is provided globally by the sandbox environment
// NO IMPORTS - everything is global!

// --- MOCK DATA & API SIMULATION ---
const MOCK_STOCKS = {
  'AAPL': { name: 'Apple Inc.', price: 175.25, change: 2.51, changePercent: 1.45, marketCap: '2.85T', peRatio: 29.5, dividendYield: 0.52, logo: 'https://logo.clearbit.com/apple.com', summary: 'Designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.' },
  'GOOGL': { name: 'Alphabet Inc.', price: 140.80, change: -1.12, changePercent: -0.79, marketCap: '1.77T', peRatio: 26.8, dividendYield: 0.00, logo: 'https://logo.clearbit.com/abc.xyz', summary: 'Provides online advertising services in the United States, Europe, the Middle East, Africa, the Asia-Pacific, Canada, and Latin America.' },
  'MSFT': { name: 'Microsoft Corp.', price: 370.95, change: 3.45, changePercent: 0.94, marketCap: '2.75T', peRatio: 35.1, dividendYield: 0.75, logo: 'https://logo.clearbit.com/microsoft.com', summary: 'Develops, licenses, and supports software, services, devices, and solutions worldwide.' },
  'AMZN': { name: 'Amazon.com, Inc.', price: 155.20, change: -2.30, changePercent: -1.46, marketCap: '1.60T', peRatio: 65.2, dividendYield: 0.00, logo: 'https://logo.clearbit.com/amazon.com', summary: 'Engages in the retail sale of consumer products and subscriptions in North America and internationally.' },
  'TSLA': { name: 'Tesla, Inc.', price: 245.01, change: 5.67, changePercent: 2.37, marketCap: '780B', peRatio: 78.3, dividendYield: 0.00, logo: 'https://logo.clearbit.com/tesla.com', summary: 'Designs, develops, manufactures, leases, and sells electric vehicles, and energy generation and storage systems.' },
  'NVDA': { name: 'NVIDIA Corp.', price: 475.69, change: 10.11, changePercent: 2.17, marketCap: '1.17T', peRatio: 60.5, dividendYield: 0.03, logo: 'https://logo.clearbit.com/nvidia.com', summary: 'Provides graphics, and compute and networking solutions in the United States, Taiwan, China, and internationally.' },
};

const MOCK_PORTFOLIO = [
  { ticker: 'AAPL', quantity: 50, avgCost: 150.00, transactions: [{ type: 'buy', date: '2023-01-15', quantity: 50, price: 150.00 }] },
  { ticker: 'MSFT', quantity: 30, avgCost: 300.00, transactions: [{ type: 'buy', date: '2023-03-20', quantity: 30, price: 300.00 }] },
  { ticker: 'GOOGL', quantity: 25, avgCost: 120.00, transactions: [{ type: 'buy', date: '2023-05-10', quantity: 25, price: 120.00 }] },
];

const MOCK_WATCHLIST = ['TSLA', 'NVDA'];

const MOCK_NEWS = [
  { id: 1, ticker: 'AAPL', source: 'Bloomberg', title: 'Apple Unveils New M3 Chip Lineup, Boosting Mac Performance', sentiment: 'positive', timestamp: '2 hours ago', url: '#' },
  { id: 2, ticker: 'MSFT', source: 'Reuters', title: 'Microsoft\'s AI Investments Begin to Pay Off in Cloud Growth', sentiment: 'positive', timestamp: '5 hours ago', url: '#' },
  { id: 3, ticker: 'GOOGL', source: 'Wall Street Journal', title: 'Alphabet Faces Increased Scrutiny Over Ad Dominance', sentiment: 'negative', timestamp: '1 day ago', url: '#' },
  { id: 4, ticker: 'TSLA', source: 'TechCrunch', title: 'Tesla Cybertruck Deliveries to Start, But Production Challenges Remain', sentiment: 'neutral', timestamp: '2 days ago', url: '#' },
];

// --- CONTEXTS ---
const AuthContext = React.createContext(null);
const useAuth = () => React.useContext(AuthContext);
const DataContext = React.createContext(null);
const useData = () => React.useContext(DataContext);

// --- HELPER & UI COMPONENTS ---

const StatCard = ({ title, value, change, isCurrency = true, className }) => (
  <motion.div
    className={cn("backdrop-blur-md bg-gray-800/40 p-6 rounded-2xl border border-white/10 shadow-lg", className)}
    whileHover={{ y: -5, scale: 1.02 }}
    transition={{ type: 'spring', stiffness: 300 }}
  >
    <p className="text-sm text-gray-400 font-medium tracking-wider uppercase">{title}</p>
    <p className="text-3xl font-bold text-white mt-2">{isCurrency ? `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : value}</p>
    {change !== undefined && (
      <div className={`flex items-center mt-1 text-sm font-semibold ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
        {change >= 0 ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        <span className="ml-1">{isCurrency ? `$${Math.abs(change).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : `${change}%`}</span>
      </div>
    )}
  </motion.div>
);

const DonutChart = ({ data, size = 250 }) => {
  const [hoveredSegment, setHoveredSegment] = useState(null);
  const radius = size / 2 - 20;
  const circumference = 2 * Math.PI * radius;

  const totalValue = useMemo(() => data.reduce((sum, item) => sum + item.value, 0), [data]);
  if (totalValue === 0) {
    return <div className="flex items-center justify-center" style={{ width: size, height: size }}><p className="text-gray-400">No data to display</p></div>;
  }

  let accumulatedAngle = 0;
  const segments = data.map(item => {
    const percentage = item.value / totalValue;
    const angle = percentage * 360;
    const segmentData = { ...item, percentage, angle, startAngle: accumulatedAngle };
    accumulatedAngle += angle;
    return segmentData;
  });

  const activeSegment = hoveredSegment ? segments.find(s => s.ticker === hoveredSegment) : segments[0];

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <g transform={`translate(${size / 2}, ${size / 2})`}>
          {segments.map((segment, index) => (
            <motion.circle
              key={segment.ticker}
              r={radius}
              cx="0"
              cy="0"
              fill="transparent"
              stroke={segment.color}
              strokeWidth="30"
              strokeDasharray={`${circumference * segment.percentage} ${circumference * (1 - segment.percentage)}`}
              strokeDashoffset={-circumference * (segment.startAngle / 360)}
              transform={`rotate(-90)`}
              onMouseOver={() => setHoveredSegment(segment.ticker)}
              onMouseOut={() => setHoveredSegment(null)}
              className="cursor-pointer transition-opacity duration-300"
              style={{ opacity: hoveredSegment && hoveredSegment !== segment.ticker ? 0.5 : 1 }}
              initial={{ strokeDasharray: `0 ${circumference}` }}
              animate={{ strokeDasharray: `${circumference * segment.percentage} ${circumference * (1 - segment.percentage)}` }}
              transition={{ duration: 1, delay: index * 0.1 }}
            />
          ))}
        </g>
      </svg>
      <div className="absolute text-center">
        <p className="text-gray-400 text-sm">Total Value</p>
        <p className="text-white text-2xl font-bold">${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
        {activeSegment && (
          <div className="mt-2">
            <p className="text-white font-semibold">{activeSegment.ticker}</p>
            <p className="text-gray-300 text-sm">{(activeSegment.percentage * 100).toFixed(2)}%</p>
          </div>
        )}
      </div>
    </div>
  );
};

const DiagonalSection = ({ children, className, reverse = false }) => {
  const clipPath = reverse ? 'polygon(15% 0, 100% 0, 100% 100%, 0% 100%)' : 'polygon(0 0, 100% 0, 85% 100%, 0% 100%)';
  return (
    <section className={cn("relative", className)} style={{ clipPath }}>
      <div className="relative z-10">{children}</div>
    </section>
  );
};

const AuthModal = ({ isOpen, onClose }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    // Simulate login/signup
    login({ name: email.split('@')[0], email });
    onClose();
    navigate('/dashboard');
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/70 flex items-center justify-center z-50"
          onClick={onClose}
        >
          <motion.div
            initial={{ y: -50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 50, opacity: 0 }}
            className="bg-gray-900/50 backdrop-blur-xl border border-white/10 rounded-2xl w-full max-w-md p-8 shadow-2xl shadow-purple-500/20"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-3xl font-bold text-white">{isLogin ? 'Sign In' : 'Create Account'}</h2>
              <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors"><X /></button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                {!isLogin && (
                  <Input type="text" placeholder="Full Name" className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-500 focus:ring-purple-500 focus:border-purple-500" />
                )}
                <Input type="email" placeholder="Email Address" value={email} onChange={e => setEmail(e.target.value)} className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-500 focus:ring-purple-500 focus:border-purple-500" />
                <Input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-500 focus:ring-purple-500 focus:border-purple-500" />
              </div>
              <Button type="submit" className="w-full mt-6 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-bold py-3 rounded-lg shadow-lg hover:shadow-purple-500/40 transform hover:scale-105 transition-all duration-300">
                {isLogin ? 'Sign In' : 'Sign Up'}
              </Button>
              <p className="text-center text-gray-400 text-sm mt-4">
                {isLogin ? "Don't have an account?" : "Already have an account?"}
                <button type="button" onClick={() => setIsLogin(!isLogin)} className="font-semibold text-purple-400 hover:text-purple-300 ml-1">
                  {isLogin ? 'Sign Up' : 'Sign In'}
                </button>
              </p>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// --- PAGE COMPONENTS ---

const LandingPage = () => {
  const [isAuthModalOpen, setAuthModalOpen] = useState(false);
  const { user } = useAuth();
  const navigate = useNavigate();

  if (user) {
    return <Navigate to="/dashboard" />;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white overflow-hidden">
      <header className="absolute top-0 left-0 right-0 z-20 p-6 flex justify-between items-center">
        <div className="text-2xl font-bold tracking-tight">InvestorTrack</div>
        <Button onClick={() => setAuthModalOpen(true)} className="bg-white/10 backdrop-blur-md border border-white/20 text-white hover:bg-white/20 px-6 py-2 rounded-full font-semibold transition-all">
          Sign In
        </Button>
      </header>

      <main>
        <div className="relative h-screen flex items-center justify-center">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-900 via-gray-900 to-black opacity-50"></div>
          <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1600&h=900&q=80&auto=format&fit=crop')] bg-cover bg-center opacity-10"></div>
          
          <div className="relative z-10 text-center px-4">
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="text-5xl md:text-7xl font-extrabold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-500"
            >
              Your Portfolio, Perfected.
            </motion.h1>
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
              className="mt-4 max-w-2xl mx-auto text-lg md:text-xl text-gray-300"
            >
              Track stocks, visualize allocations, and stay ahead with curated news. The ultimate tool for the modern individual investor.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4, ease: "easeOut" }}
              className="mt-8"
            >
              <Button onClick={() => setAuthModalOpen(true)} className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold px-8 py-4 rounded-xl shadow-xl hover:shadow-2xl shadow-purple-500/30 transform hover:scale-105 transition-all duration-300">
                Get Started for Free
              </Button>
            </motion.div>
          </div>
        </div>
      </main>
      <AuthModal isOpen={isAuthModalOpen} onClose={() => setAuthModalOpen(false)} />
    </div>
  );
};

const DashboardPage = () => {
  const { portfolio, stocks, news, watchlist } = useData();
  const navigate = useNavigate();

  const portfolioValue = useMemo(() => portfolio.reduce((sum, holding) => sum + (stocks[holding.ticker]?.price * holding.quantity || 0), 0), [portfolio, stocks]);
  const totalCost = useMemo(() => portfolio.reduce((sum, holding) => sum + (holding.avgCost * holding.quantity), 0), [portfolio]);
  const totalGainLoss = portfolioValue - totalCost;
  
  const dailyChange = useMemo(() => portfolio.reduce((sum, holding) => sum + (stocks[holding.ticker]?.change * holding.quantity || 0), 0), [portfolio, stocks]);

  const chartData = useMemo(() => {
    const colors = ['#8B5CF6', '#EC4899', '#3B82F6', '#10B981', '#F59E0B'];
    return portfolio.map((holding, index) => ({
      ticker: holding.ticker,
      value: (stocks[holding.ticker]?.price || 0) * holding.quantity,
      color: colors[index % colors.length],
    }));
  }, [portfolio, stocks]);

  return (
    <div className="p-4 md:p-8 space-y-8">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        <h1 className="text-4xl font-bold tracking-tight text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">Welcome back, here's your portfolio snapshot.</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Portfolio Value" value={portfolioValue} change={dailyChange} />
        <StatCard title="Total Gain/Loss" value={totalGainLoss} change={(totalGainLoss / totalCost * 100).toFixed(2)} isCurrency={true} />
        <StatCard title="Holdings" value={portfolio.length} isCurrency={false} />
        <StatCard title="Watchlist" value={watchlist.length} isCurrency={false} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <motion.div 
          initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.2 }}
          className="lg:col-span-2 backdrop-blur-md bg-gray-800/40 p-6 rounded-2xl border border-white/10 shadow-lg"
        >
          <h2 className="text-xl font-bold text-white mb-4">Portfolio Allocation</h2>
          <div className="flex flex-col md:flex-row items-center justify-around">
            <DonutChart data={chartData} size={300} />
            <div className="mt-6 md:mt-0 md:ml-6 space-y-3">
              {chartData.map(item => (
                <div key={item.ticker} className="flex items-center">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
                  <span className="ml-3 text-white font-medium">{item.ticker}</span>
                  <span className="ml-auto text-gray-300">{((item.value / portfolioValue) * 100).toFixed(2)}%</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.3 }}
          className="backdrop-blur-md bg-gray-800/40 p-6 rounded-2xl border border-white/10 shadow-lg"
        >
          <h2 className="text-xl font-bold text-white mb-4">Watchlist</h2>
          <div className="space-y-4">
            {watchlist.map(ticker => {
              const stock = stocks[ticker];
              if (!stock) return null;
              const isUp = stock.change >= 0;
              return (
                <div key={ticker} className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg hover:bg-gray-700/50 transition-colors cursor-pointer" onClick={() => navigate(`/portfolio/${ticker}`)}>
                  <div>
                    <p className="font-bold text-white">{ticker}</p>
                    <p className="text-xs text-gray-400 truncate w-24">{stock.name}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-white">${stock.price.toFixed(2)}</p>
                    <p className={`text-sm ${isUp ? 'text-green-400' : 'text-red-400'}`}>{isUp ? '+' : ''}{stock.change.toFixed(2)} ({stock.changePercent.toFixed(2)}%)</p>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>
      
      <motion.div 
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.4 }}
        className="backdrop-blur-md bg-gray-800/40 p-6 rounded-2xl border border-white/10 shadow-lg"
      >
        <h2 className="text-xl font-bold text-white mb-4">Relevant News</h2>
        <div className="space-y-4">
          {news.slice(0, 3).map(item => (
            <div key={item.id} className="flex items-start space-x-4 p-3 rounded-lg hover:bg-gray-900/50 transition-colors">
              <div className={`w-2 h-2 rounded-full mt-1.5 ${item.sentiment === 'positive' ? 'bg-green-500' : item.sentiment === 'negative' ? 'bg-red-500' : 'bg-yellow-500'}`}></div>
              <div>
                <a href={item.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-white hover:text-purple-400 transition-colors">{item.title}</a>
                <p className="text-xs text-gray-400 mt-1">{item.source} &bull; {item.timestamp}</p>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

const PortfolioPage = () => {
  const { portfolio, stocks } = useData();
  const navigate = useNavigate();

  return (
    <div className="p-4 md:p-8">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        <h1 className="text-4xl font-bold tracking-tight text-white">My Portfolio</h1>
        <p className="text-gray-400 mt-1">Detailed view of your holdings.</p>
      </motion.div>
      <div className="mt-8 overflow-x-auto">
        <table className="w-full text-left">
          <thead className="border-b border-gray-700">
            <tr className="text-xs text-gray-400 uppercase tracking-wider">
              <th className="p-4">Asset</th>
              <th className="p-4">Holdings</th>
              <th className="p-4">Avg. Cost</th>
              <th className="p-4">Market Value</th>
              <th className="p-4">Total Gain/Loss</th>
            </tr>
          </thead>
          <motion.tbody>
            {portfolio.map((holding, index) => {
              const stock = stocks[holding.ticker];
              if (!stock) return null;
              const marketValue = stock.price * holding.quantity;
              const totalCost = holding.avgCost * holding.quantity;
              const gainLoss = marketValue - totalCost;
              const gainLossPercent = (gainLoss / totalCost) * 100;
              const isGain = gainLoss >= 0;

              return (
                <motion.tr 
                  key={holding.ticker} 
                  className="border-b border-gray-800 hover:bg-gray-800/50 cursor-pointer"
                  onClick={() => navigate(`/portfolio/${holding.ticker}`)}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  <td className="p-4">
                    <div className="flex items-center">
                      <img src={stock.logo} alt={stock.name} className="w-8 h-8 rounded-full mr-4" />
                      <div>
                        <p className="font-bold text-white">{holding.ticker}</p>
                        <p className="text-xs text-gray-400">{stock.name}</p>
                      </div>
                    </div>
                  </td>
                  <td className="p-4">
                    <p className="font-semibold text-white">{holding.quantity} shares</p>
                    <p className="text-xs text-gray-400">${stock.price.toFixed(2)}</p>
                  </td>
                  <td className="p-4 font-semibold text-white">${holding.avgCost.toFixed(2)}</td>
                  <td className="p-4 font-semibold text-white">${marketValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                  <td className="p-4">
                    <p className={`font-semibold ${isGain ? 'text-green-400' : 'text-red-400'}`}>
                      {isGain ? '+' : '-'}${Math.abs(gainLoss).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                    <p className={`text-xs ${isGain ? 'text-green-400' : 'text-red-400'}`}>
                      ({gainLossPercent.toFixed(2)}%)
                    </p>
                  </td>
                </motion.tr>
              );
            })}
          </motion.tbody>
        </table>
      </div>
    </div>
  );
};

const StockDetailPage = () => {
  const { ticker } = useParams();
  const { stocks, portfolio, addTransaction } = useData();
  const [isTxnModalOpen, setTxnModalOpen] = useState(false);
  const stock = stocks[ticker];
  const holding = portfolio.find(h => h.ticker === ticker);

  if (!stock) {
    return <div className="p-8 text-white">Stock not found.</div>;
  }

  return (
    <div className="p-4 md:p-8">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        <div className="flex items-center space-x-4">
          <img src={stock.logo} alt={stock.name} className="w-16 h-16 rounded-full" />
          <div>
            <h1 className="text-4xl font-bold tracking-tight text-white">{stock.name} ({ticker})</h1>
            <p className="text-2xl font-semibold text-white mt-1">${stock.price.toFixed(2)}</p>
          </div>
        </div>
      </motion.div>
      
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <motion.div 
            initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.2 }}
            className="backdrop-blur-md bg-gray-800/40 p-6 rounded-2xl border border-white/10"
          >
            <h2 className="text-xl font-bold text-white mb-4">Company Profile</h2>
            <p className="text-gray-300 leading-relaxed">{stock.summary}</p>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.3 }}
            className="backdrop-blur-md bg-gray-800/40 p-6 rounded-2xl border border-white/10"
          >
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-white">Transactions</h2>
              <Button onClick={() => setTxnModalOpen(true)} className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-semibold text-sm">
                <Plus className="w-4 h-4 mr-2 inline" />
                Log Transaction
              </Button>
            </div>
            {holding && holding.transactions.length > 0 ? (
              <div className="space-y-2">
                {holding.transactions.map((txn, i) => (
                  <div key={i} className="flex justify-between p-3 bg-gray-900/50 rounded-lg">
                    <span className={`font-semibold capitalize ${txn.type === 'buy' ? 'text-green-400' : 'text-red-400'}`}>{txn.type}</span>
                    <span>{txn.quantity} shares @ ${txn.price.toFixed(2)}</span>
                    <span className="text-gray-400">{txn.date}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400">No transactions logged for this asset.</p>
            )}
          </motion.div>
        </div>
        
        <motion.div 
          initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.4 }}
          className="backdrop-blur-md bg-gray-800/40 p-6 rounded-2xl border border-white/10 h-fit"
        >
          <h2 className="text-xl font-bold text-white mb-4">Key Financials</h2>
          <div className="space-y-3">
            <div className="flex justify-between text-sm"><span className="text-gray-400">Market Cap</span><span className="font-semibold text-white">{stock.marketCap}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-400">P/E Ratio</span><span className="font-semibold text-white">{stock.peRatio}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-400">Dividend Yield</span><span className="font-semibold text-white">{stock.dividendYield}%</span></div>
          </div>
        </motion.div>
      </div>
      
      <TransactionModal 
        isOpen={isTxnModalOpen} 
        onClose={() => setTxnModalOpen(false)} 
        ticker={ticker}
        onSubmit={addTransaction}
      />
    </div>
  );
};

const TransactionModal = ({ isOpen, onClose, ticker, onSubmit }) => {
  const [type, setType] = useState('buy');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      ticker,
      type,
      quantity: parseFloat(quantity),
      price: parseFloat(price),
      date
    });
    onClose();
    setQuantity('');
    setPrice('');
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={onClose}>
          <motion.div initial={{ y: -50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 50, opacity: 0 }} className="bg-gray-900/50 backdrop-blur-xl border border-white/10 rounded-2xl w-full max-w-md p-8" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-2xl font-bold text-white mb-6">Log Transaction for {ticker}</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-400">Type</label>
                <div className="flex mt-2 rounded-lg bg-gray-800 p-1">
                  <button type="button" onClick={() => setType('buy')} className={cn("w-1/2 py-2 rounded-md text-sm font-semibold transition-colors", type === 'buy' ? 'bg-green-600 text-white' : 'text-gray-300 hover:bg-gray-700')}>Buy</button>
                  <button type="button" onClick={() => setType('sell')} className={cn("w-1/2 py-2 rounded-md text-sm font-semibold transition-colors", type === 'sell' ? 'bg-red-600 text-white' : 'text-gray-300 hover:bg-gray-700')}>Sell</button>
                </div>
              </div>
              <Input type="number" placeholder="Quantity" value={quantity} onChange={e => setQuantity(e.target.value)} required className="bg-gray-800/50 border-gray-700 text-white" />
              <Input type="number" placeholder="Price per Share" value={price} onChange={e => setPrice(e.target.value)} required className="bg-gray-800/50 border-gray-700 text-white" />
              <Input type="date" value={date} onChange={e => setDate(e.target.value)} required className="bg-gray-800/50 border-gray-700 text-white" />
              <div className="flex justify-end space-x-4 pt-4">
                <Button type="button" onClick={onClose} className="bg-gray-700 hover:bg-gray-600 text-white px-6 py-2 rounded-lg font-semibold">Cancel</Button>
                <Button type="submit" className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg font-semibold">Save</Button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// --- MAIN APP LAYOUT & ROUTER ---

const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/" />;
  }
  return children;
};

const AppLayout = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/dashboard', icon: Home, label: 'Dashboard' },
    { path: '/portfolio', icon: User, label: 'Portfolio' },
    // Add more pages like News, Watchlist here if needed
  ];

  return (
    <div className="min-h-screen bg-black text-white flex">
      <aside className="w-20 lg:w-64 bg-gray-900/50 border-r border-white/10 p-4 flex flex-col">
        <div className="text-2xl font-bold tracking-tight text-white mb-12 hidden lg:block">InvestorTrack</div>
        <div className="text-2xl font-bold tracking-tight text-white mb-12 lg:hidden text-center">IT</div>
        <nav className="flex-grow space-y-2">
          {navItems.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  "flex items-center p-3 rounded-lg transition-colors",
                  "hover:bg-purple-600/30",
                  isActive ? "bg-purple-600 text-white" : "text-gray-300"
                )
              }
            >
              <item.icon className="w-6 h-6" />
              <span className="ml-4 hidden lg:inline">{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <Button onClick={() => { logout(); navigate('/'); }} className="w-full bg-red-600/20 hover:bg-red-600/40 text-red-300 border border-red-500/50 px-4 py-2 rounded-lg font-semibold">
          <span className="hidden lg:inline">Logout</span>
          <span className="lg:hidden">Exit</span>
        </Button>
      </aside>
      <main className="flex-1 bg-gray-900 overflow-y-auto">
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1600&h=900&q=80&auto=format&fit=crop')] bg-cover bg-center opacity-[0.03]"></div>
        <div className="relative z-10">
          <Routes>
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="portfolio" element={<PortfolioPage />} />
            <Route path="portfolio/:ticker" element={<StockDetailPage />} />
            <Route index element={<Navigate to="dashboard" />} />
          </Routes>
        </div>
      </main>
    </div>
  );
};

const App = () => {
  const [user, setUser] = useState(null);
  const [stocks, setStocks] = useState(MOCK_STOCKS);
  const [portfolio, setPortfolio] = useState(MOCK_PORTFOLIO);
  const [watchlist, setWatchlist] = useState(MOCK_WATCHLIST);
  const [news, setNews] = useState(MOCK_NEWS);

  useEffect(() => {
    // Simulate real-time price updates
    const interval = setInterval(() => {
      setStocks(prevStocks => {
        const newStocks = { ...prevStocks };
        for (const ticker in newStocks) {
          const change = (Math.random() - 0.5) * (newStocks[ticker].price * 0.02);
          newStocks[ticker].price += change;
          newStocks[ticker].change = change;
          newStocks[ticker].changePercent = (change / newStocks[ticker].price) * 100;
        }
        return newStocks;
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []);
  
  const login = (userData) => setUser(userData);
  const logout = () => setUser(null);

  const addTransaction = (txn) => {
    setPortfolio(prev => {
      const newPortfolio = [...prev];
      const holdingIndex = newPortfolio.findIndex(h => h.ticker === txn.ticker);
      if (holdingIndex > -1) {
        const holding = newPortfolio[holdingIndex];
        holding.transactions.push(txn);
        // Recalculate quantity and avgCost
        let totalQuantity = 0;
        let totalCost = 0;
        holding.transactions.forEach(t => {
          if (t.type === 'buy') {
            totalQuantity += t.quantity;
            totalCost += t.quantity * t.price;
          } else {
            totalQuantity -= t.quantity;
          }
        });
        holding.quantity = totalQuantity;
        holding.avgCost = totalCost / holding.transactions.filter(t => t.type === 'buy').reduce((sum, t) => sum + t.quantity, 0);
      } else {
        // New holding
        newPortfolio.push({
          ticker: txn.ticker,
          quantity: txn.quantity,
          avgCost: txn.price,
          transactions: [txn]
        });
      }
      return newPortfolio;
    });
  };

  const authContextValue = { user, login, logout };
  const dataContextValue = { stocks, portfolio, watchlist, news, addTransaction };

  return (
    <AuthContext.Provider value={authContextValue}>
      <DataContext.Provider value={dataContextValue}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/*" element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          } />
        </Routes>
      </DataContext.Provider>
    </AuthContext.Provider>
  );
};

const AppWrapper = () => (
  <Router>
    <App />
  </Router>
);

export default App;
