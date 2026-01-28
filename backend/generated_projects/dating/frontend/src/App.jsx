import ChatOption from './components/ChatOption';
// NO IMPORTS - everything is global!

// --- MOCK DATA ---
const MOCK_USERS = [
  {
    id: 1,
    name: 'Sophia',
    age: 26,
    distance: 2,
    bio: "Lover of art, hiking, and spontaneous road trips. Looking for someone to share adventures and quiet moments with. Let's find the best coffee shop in town!",
    photos: [
      'https://images.unsplash.com/photo-1520466809213-7b9a56adcd45?w=500&h=700&q=80&auto=format&fit=crop',
      'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=500&h=700&q=80&auto=format&fit=crop',
      'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=500&h=700&q=80&auto=format&fit=crop'
    ],
    interests: ['Hiking', 'Art Galleries', 'Photography', 'Live Music'],
    isVerified: true,
  },
  {
    id: 2,
    name: 'Liam',
    age: 29,
    distance: 5,
    bio: "Software engineer by day, aspiring chef by night. My dog is my best friend. If you can beat me at Mario Kart, I'll make you dinner.",
    photos: [
      'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500&h=700&q=80&auto=format&fit=crop',
      'https://images.unsplash.com/photo-1581803118522-7b72a50f7e9f?w=500&h=700&q=80&auto=format&fit=crop'
    ],
    interests: ['Cooking', 'Video Games', 'Dogs', 'Sci-Fi Movies'],
    isVerified: false,
  },
  {
    id: 3,
    name: 'Chloe',
    age: 24,
    distance: 8,
    bio: "Just a girl who loves books, plants, and rainy days. My ideal date is exploring a bookstore or trying a new recipe together. Fluent in sarcasm.",
    photos: [
      'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=500&h=700&q=80&auto=format&fit=crop',
      'https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=500&h=700&q=80&auto=format&fit=crop'
    ],
    interests: ['Reading', 'Gardening', 'Baking', 'Yoga'],
    isVerified: true,
  },
  {
    id: 4,
    name: 'Ethan',
    age: 31,
    distance: 3,
    bio: "Fitness enthusiast and travel addict. I've been to 15 countries and counting. Looking for a gym partner and a travel buddy. What's your next destination?",
    photos: [
      'https://images.unsplash.com/photo-1564564321837-a57b7070ac4f?w=500&h=700&q=80&auto=format&fit=crop'
    ],
    interests: ['Weightlifting', 'Traveling', 'Beach Days', 'Podcasts'],
    isVerified: false,
  },
  {
    id: 5,
    name: 'Isabella',
    age: 27,
    distance: 12,
    bio: "Musician and animal lover. I spend my weekends volunteering at the local shelter or playing guitar. Let's talk about our favorite bands.",
    photos: [
      'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=500&h=700&q=80&auto=format&fit=crop'
    ],
    interests: ['Guitar', 'Animal Rescue', 'Concerts', 'Vintage Shopping'],
    isVerified: true,
  }
];

// --- ICONS ---

// --- CONTEXTS ---
const AppContext = React.createContext(null);
const useApp = () => React.useContext(AppContext);

// --- COMPONENTS ---

const ProfileCard = ({ user, onSwipe, isTop }) => {
  const [currentPhoto, setCurrentPhoto] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState(0);
  const [dragOffset, setDragOffset] = useState(0);
  const cardRef = useRef(null);

  const nextPhoto = (e) => {
    e.stopPropagation();
    setCurrentPhoto((p) => (p + 1) % user.photos.length);
  };

  const prevPhoto = (e) => {
    e.stopPropagation();
    setCurrentPhoto((p) => (p - 1 + user.photos.length) % user.photos.length);
  };

  const handlePointerDown = (e) => {
    if (!isTop) return;
    setIsDragging(true);
    setDragStart(e.clientX);
    cardRef.current.style.transition = 'none';
  };

  const handlePointerMove = (e) => {
    if (!isDragging || !isTop) return;
    const offset = e.clientX - dragStart;
    setDragOffset(offset);
  };

  const handlePointerUp = () => {
    if (!isDragging || !isTop) return;
    setIsDragging(false);
    cardRef.current.style.transition = 'transform 0.3s ease-out, opacity 0.3s ease-out';
    if (dragOffset > 100) {
      onSwipe('right', user.id);
    } else if (dragOffset < -100) {
      onSwipe('left', user.id);
    } else {
      setDragOffset(0);
    }
  };

  const rotation = dragOffset / 20;
  const cardStyle = {
    transform: `translateX(${dragOffset}px) rotate(${rotation}deg)`,
    opacity: 1 - Math.abs(dragOffset) / 200,
  };

  return (
    <div
      ref={cardRef}
      className="absolute w-full h-full transition-transform duration-300"
      style={cardStyle}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
    >
      <div className="relative w-full h-full bg-white rounded-2xl shadow-2xl overflow-hidden cursor-grab active:cursor-grabbing">
        <img src={user.photos[currentPhoto]} alt={user.name} className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent"></div>
        
        {user.photos.length > 1 && (
          <div className="absolute top-2 left-2 right-2 flex gap-1">
            {user.photos.map((_, index) => (
              <div key={index} className={`h-1 flex-1 rounded-full ${index === currentPhoto ? 'bg-white' : 'bg-white/50'}`}></div>
            ))}
          </div>
        )}

        <div className="absolute top-0 left-0 w-1/2 h-full" onClick={prevPhoto}></div>
        <div className="absolute top-0 right-0 w-1/2 h-full" onClick={nextPhoto}></div>

        <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-bold">{user.name}, {user.age}</h2>
            {user.isVerified && <CheckCircle className="w-7 h-7 text-blue-400 fill-current" />}
          </div>
          <p className="text-lg">{user.distance} miles away</p>
          <p className="mt-2 text-white/90">{user.bio}</p>
          <div className="flex flex-wrap gap-2 mt-4">
            {user.interests.map(interest => (
              <span key={interest} className="bg-white/20 text-white text-sm font-medium px-3 py-1 rounded-full bg-[#b04a4a]">{interest}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const DiscoverPage = () => {
  const { users, setUsers, handleMatch } = useApp();
  const [superLikes, setSuperLikes] = useState(1);

  const handleSwipe = (direction, userId) => {
    if (direction === 'right') {
      // Simulate a 50% chance of matching
      if (Math.random() > 0.5) {
        const matchedUser = users.find(u => u.id === userId);
        handleMatch(matchedUser);
      }
    }
    // Remove the swiped user from the queue
    setUsers(prevUsers => prevUsers.filter(user => user.id !== userId));
  };
  
  const handleSuperLike = () => {
    if (superLikes > 0 && users.length > 0) {
      const userToSuperLike = users[users.length - 1];
      handleMatch(userToSuperLike); // Super like is an instant match in this simulation
      setUsers(prevUsers => prevUsers.filter(user => user.id !== userToSuperLike.id));
      setSuperLikes(prev => prev - 1);
    }
  };

  return (
    <div className="flex-1 flex flex-col p-4 bg-rose-50 overflow-hidden">
      <div className="relative flex-1 mb-4">
        {users.length > 0 ? (
          users.map((user, index) => (
            <ProfileCard 
              key={user.id} 
              user={user} 
              onSwipe={handleSwipe} 
              isTop={index === users.length - 1}
            />
          )).reverse()
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
            <Sparkles className="w-16 h-16 mb-4 text-rose-300" />
            <h3 className="text-xl font-semibold">That's everyone for now!</h3>
            <p>Come back later to see new people.</p>
          </div>
        )}
      </div>
      <div className="flex justify-around items-center h-24">
        <button onClick={() => users.length > 0 && handleSwipe('left', users[users.length - 1].id)} className="w-16 h-16 rounded-full bg-white shadow-lg flex items-center justify-center text-gray-400 hover:bg-gray-100 transition-colors">
          <X className="w-8 h-8" />
        </button>
        <button onClick={handleSuperLike} disabled={superLikes === 0 || users.length === 0} className="w-20 h-20 rounded-full bg-white shadow-lg flex items-center justify-center text-blue-400 hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
          <Star className="w-10 h-10 fill-current" />
        </button>
        <button onClick={() => users.length > 0 && handleSwipe('right', users[users.length - 1].id)} className="w-16 h-16 rounded-full bg-white shadow-lg flex items-center justify-center text-rose-500 hover:bg-rose-100 transition-colors">
          <Heart className="w-8 h-8 fill-current" />
        </button>
      </div>
    </div>
  );
};

const MatchesPage = () => {
  const { matches } = useApp();
  const navigate = useNavigate();

  return (
    <div className="flex-1 flex flex-col bg-rose-50">
      <div className="p-4 border-b bg-white">
        <h1 className="text-2xl font-bold text-rose-900">Matches</h1>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {matches.length > 0 ? (
          matches.map(match => (
            <div key={match.id} onClick={() => navigate(`/chat/${match.id}`)} className="flex items-center gap-4 p-3 bg-white rounded-xl shadow-sm cursor-pointer hover:shadow-md transition-shadow">
              <img src={match.photos[0]} alt={match.name} className="w-16 h-16 rounded-full object-cover" />
              <div className="flex-1">
                <h3 className="font-semibold text-gray-800">{match.name}</h3>
                <p className="text-sm text-gray-500">You matched! Say hello.</p>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center text-gray-500 pt-20">
            <MessageCircle className="w-12 h-12 mx-auto mb-4 text-rose-300" />
            <h3 className="font-semibold">No matches yet</h3>
            <p>Keep swiping to find your connection!</p>
          </div>
        )}
      </div>
    </div>
  );
};

const ChatPage = () => {
  const { matches, unmatchUser } = useApp();
  const { matchId } = useParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [showOptions, setShowOptions] = useState(false);

  const match = useMemo(() => matches.find(m => m.id.toString() === matchId), [matches, matchId]);

  useEffect(() => {
    if (match) {
      setMessages([
        { id: 1, text: `Hey! I saw you like ${match.interests[0]}. Me too!`, sender: match.id },
        { id: 2, text: 'Oh cool! We should totally go sometime.', sender: 'me' },
      ]);
    }
  }, [match]);

  const handleSend = (e) => {
    e.preventDefault();
    if (newMessage.trim() === '') return;
    setMessages([...messages, { id: Date.now(), text: newMessage, sender: 'me' }]);
    setNewMessage('');
  };
  
  const handleUnmatch = () => {
    if (window.confirm(`Are you sure you want to unmatch ${match.name}?`)) {
      unmatchUser(match.id);
      navigate('/matches');
    }
  };
  
  const handleReport = () => {
    alert(`Thank you for reporting ${match.name}. Our team will review this profile.`);
    setShowOptions(false);
  };

  if (!match) {
    return <Navigate to="/matches" />;
  }

  return (
    <div className="flex-1 flex flex-col bg-rose-50 h-full">
      <div className="flex items-center justify-between p-3 bg-white border-b shadow-sm">
        <button onClick={() => navigate('/matches')} className="p-2 rounded-full hover:bg-gray-100">
          <ChevronLeft className="w-6 h-6 text-gray-600" />
        </button>
        <div className="flex items-center gap-3">
          <img src={match.photos[0]} alt={match.name} className="w-10 h-10 rounded-full object-cover" />
          <span className="font-semibold text-gray-800">{match.name}</span>
        </div>
        <div className="relative">
          <button onClick={() => setShowOptions(prev => !prev)} className="p-2 rounded-full hover:bg-gray-100">
            <MoreVertical className="w-6 h-6 text-gray-600" />
          </button>
          {showOptions && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10">
              <button onClick={handleUnmatch} className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100">Unmatch</button>
              <button onClick={handleReport} className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Report</button>
            </div>
          )}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.sender === 'me' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${msg.sender === 'me' ? 'bg-rose-500 text-white rounded-br-lg' : 'bg-white text-gray-800 rounded-bl-lg'}`}>
              {msg.text}
            </div>
          </div>
        ))}
      </div>
      <form onSubmit={handleSend} className="p-4 bg-white border-t">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 bg-gray-100 border-transparent rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-rose-400"
          />
          <button type="submit" className="bg-rose-500 text-white p-3 rounded-full hover:bg-rose-600 transition-colors">
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
};

const ProfilePage = () => {
  const { currentUser, setCurrentUser } = useApp();
  const [isEditing, setIsEditing] = useState(false);
  const [editedUser, setEditedUser] = useState(currentUser);

  const handleSave = () => {
    setCurrentUser(editedUser);
    setIsEditing(false);
  };

  const handleVerify = () => {
    alert("Verification request submitted! This may take up to 24 hours.");
    // Simulate verification after a delay
    setTimeout(() => {
      setCurrentUser(prev => ({...prev, isVerified: true}));
      setEditedUser(prev => ({...prev, isVerified: true}));
    }, 2000);
  };

  return (
    <div className="flex-1 flex flex-col bg-rose-50">
      <div className="p-4 border-b bg-white flex justify-between items-center">
        <h1 className="text-2xl font-bold text-rose-900">My Profile</h1>
        {isEditing ? (
          <button onClick={handleSave} className="bg-rose-500 text-white px-4 py-2 rounded-lg font-semibold hover:bg-rose-600 transition-colors">Save</button>
        ) : (
          <button onClick={() => setIsEditing(true)} className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg font-semibold hover:bg-gray-300 transition-colors">Edit</button>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        <div className="relative w-32 h-32 mx-auto">
          <img src={currentUser.photos[0]} alt={currentUser.name} className="w-full h-full rounded-full object-cover shadow-md" />
          {currentUser.isVerified && <CheckCircle className="absolute bottom-0 right-0 w-8 h-8 text-blue-400 bg-white rounded-full p-1 fill-current" />}
        </div>
        <div className="text-center">
          <h2 className="text-2xl font-bold">{currentUser.name}, {currentUser.age}</h2>
        </div>
        
        <div className="bg-white p-4 rounded-xl shadow-sm">
          <h3 className="font-semibold mb-2">Bio</h3>
          {isEditing ? (
            <textarea value={editedUser.bio} onChange={(e) => setEditedUser({...editedUser, bio: e.target.value})} className="w-full p-2 border rounded-md" rows="4"></textarea>
          ) : (
            <p className="text-gray-600">{currentUser.bio}</p>
          )}
        </div>

        <div className="bg-white p-4 rounded-xl shadow-sm">
          <h3 className="font-semibold mb-2">Interests</h3>
          <div className="flex flex-wrap gap-2">
            {currentUser.interests.map(interest => (
              <span key={interest} className="bg-rose-100 text-rose-800 text-sm font-medium px-3 py-1 rounded-full">{interest}</span>
            ))}
          </div>
        </div>

        {!currentUser.isVerified && (
          <div className="bg-white p-4 rounded-xl shadow-sm text-center">
            <h3 className="font-semibold mb-2">Get Verified!</h3>
            <p className="text-gray-600 mb-4">A verified badge helps build trust.</p>
            <button onClick={handleVerify} className="bg-blue-500 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-600 transition-colors">Start Verification</button>
          </div>
        )}
      </div>
    </div>
  );
};

const MainLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const navItems = [
    { path: '/discover', icon: Star, label: 'Discover' },
    { path: '/matches', icon: MessageCircle, label: 'Matches' },
    { path: '/profile', icon: User, label: 'Profile' },
  ];

  return (
    <div className="h-screen w-screen flex flex-col max-w-md mx-auto bg-white shadow-2xl">
      <Routes>
        <Route path="/discover" element={<DiscoverPage />} />
        <Route path="/matches" element={<MatchesPage />} />
        <Route path="/chat/:matchId" element={<ChatPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="*" element={<Navigate to="/discover" />} />
        <Route path="/chat-option" element={<ChatOption />} />

      </Routes>
      
      {/* Bottom Navigation - only show on main pages */}
      {['/discover', '/matches', '/profile'].includes(location.pathname) && (
        <div className="flex justify-around items-center h-16 bg-white border-t">
          {navItems.map(item => (
            <button key={item.path} onClick={() => navigate(item.path)} className="flex flex-col items-center justify-center w-1/3 h-full">
              <item.icon className={`w-7 h-7 transition-colors ${location.pathname === item.path ? 'text-rose-500' : 'text-gray-400'}`} />
              <span className={`text-xs mt-1 ${location.pathname === item.path ? 'text-rose-500 font-semibold' : 'text-gray-500'}`}>{item.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

const LandingPage = () => {
  const { setIsLoginOpen } = useApp();
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-red-200 via-pink-200 to-rose-200 p-6 text-center">
      <h1 className="text-5xl font-bold text-rose-800 mb-4">Serendipity</h1>
      <p className="text-xl text-rose-700 max-w-md mb-8">Find meaningful connections in a world of endless swipes. Your next great story starts here.</p>
      <button 
        onClick={() => setIsLoginOpen(true)}
        className="bg-rose-500 text-white px-10 py-4 rounded-full font-bold text-lg shadow-lg hover:bg-rose-600 transform hover:scale-105 transition-all"
      >
        Join Now
      </button>
    </div>
  );
};

const LoginModal = ({ isOpen, onClose }) => {
  const { login } = useApp();
  
  const handleLogin = (e) => {
    e.preventDefault();
    login();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white p-8 rounded-2xl max-w-sm w-full mx-4" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-2xl font-bold text-center text-rose-900 mb-6">Welcome Back</h2>
        <form onSubmit={handleLogin}>
          <input type="email" placeholder="Email" defaultValue="my.profile@serendipity.com" className="w-full p-3 mb-4 bg-gray-100 rounded-lg text-gray-800 border-transparent focus:ring-2 focus:ring-rose-400" />
          <input type="password" placeholder="Password" defaultValue="password" className="w-full p-3 mb-6 bg-gray-100 rounded-lg text-gray-800 border-transparent focus:ring-2 focus:ring-rose-400" />
          <button type="submit" className="w-full py-3 bg-rose-500 text-white rounded-lg font-semibold hover:bg-rose-600 transition-colors">Sign In</button>
        </form>
        <button onClick={onClose} className="mt-4 w-full text-center text-gray-500 hover:text-gray-700">Cancel</button>
      </div>
    </div>
  );
};

const MatchNotification = ({ match, onClose }) => {
  if (!match) return null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-gradient-to-br from-red-400 via-pink-400 to-rose-400 p-8 rounded-2xl text-center text-white max-w-sm w-full relative" onClick={e => e.stopPropagation()}>
        <h2 className="text-3xl font-bold mb-4">It's a Match!</h2>
        <p className="mb-6">You and {match.name} have liked each other.</p>
        <div className="flex justify-center items-center gap-4 mb-8">
          <img src={match.photos[0]} alt={match.name} className="w-24 h-24 rounded-full object-cover border-4 border-white" />
          <Heart className="w-10 h-10 text-white" />
          <img src="https://images.unsplash.com/photo-1580489944761-15a19d654956?w=500&h=500&q=80&auto=format&fit=crop" alt="You" className="w-24 h-24 rounded-full object-cover border-4 border-white" />
        </div>
        <button onClick={onClose} className="w-full py-3 bg-white text-rose-500 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
          Keep Swiping
        </button>
      </div>
    </div>
  );
};

const App = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [users, setUsers] = useState(MOCK_USERS);
  const [matches, setMatches] = useState([]);
  const [newMatch, setNewMatch] = useState(null);
  const [currentUser, setCurrentUser] = useState({
    id: 99,
    name: 'Alex',
    age: 28,
    bio: "Trying to find someone who will share their fries with me. I love exploring new places, trying new foods, and a good laugh.",
    photos: ['https://images.unsplash.com/photo-1580489944761-15a19d654956?w=500&h=500&q=80&auto=format&fit=crop'],
    interests: ['Foodie', 'Travel', 'Comedy', 'Dogs'],
    isVerified: false,
  });

  const login = () => setIsLoggedIn(true);
  const logout = () => setIsLoggedIn(false);

  const handleMatch = (matchedUser) => {
    setMatches(prev => [...prev, matchedUser]);
    setNewMatch(matchedUser);
  };
  
  const unmatchUser = (userId) => {
    setMatches(prev => prev.filter(match => match.id !== userId));
  };

  const appContextValue = {
    isLoggedIn,
    login,
    logout,
    isLoginOpen,
    setIsLoginOpen,
    users,
    setUsers,
    matches,
    setMatches,
    handleMatch,
    unmatchUser,
    currentUser,
    setCurrentUser
  };

  return (
    <AppContext.Provider value={appContextValue}>
      <div className="font-sans">
        {isLoggedIn ? <MainLayout /> : <LandingPage />}
        <LoginModal isOpen={isLoginOpen} onClose={() => setIsLoginOpen(false)} />
        <MatchNotification match={newMatch} onClose={() => setNewMatch(null)} />
      </div>
    </AppContext.Provider>
  );
};

const AppWrapper = () => (
  <Router>
    <App />
  </Router>
);

App;

App;

export default App;