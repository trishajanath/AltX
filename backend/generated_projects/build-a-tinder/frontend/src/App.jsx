```javascript
import React, { useState, useEffect, useMemo, useRef } from 'react';
import TinderCard from 'react-tinder-card';
import { Flame, Heart, X, Star, Zap, User, MessageSquare } from 'lucide-react';

//  MOCK DATA 
// In a real application, this would be fetched from a secure API.
const initialProfiles = [
  { id: 1, name: 'Jessica', age: 26, bio: 'Lover of hiking, dogs, and spontaneous trips. Looking for a partner in crime.', imageUrl: 'https://images.unsplash.com/photo-1520466809213-7b9a56adcd45?q=80&w=800' },
  { id: 2, name: 'Mark', age: 29, bio: 'Software engineer by day, musician by night. Let\'s talk about code or chords.', imageUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=800' },
  { id: 3, name: 'Chloe', age: 24, bio: 'Art student who loves museums and coffee shops. Swipe right if you\'re a good conversationalist!', imageUrl: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=800' },
  { id: 4, name: 'Alex', age: 31, bio: 'Fitness enthusiast and personal trainer. I can probably lift more than you.', imageUrl: 'https://images.unsplash.com/photo-1521119989659-a83eee488004?q=80&w=800' },
  { id: 5, name: 'Sophia', age: 27, bio: 'Just a girl who loves books, cats, and rainy days. Tell me your favorite book!', imageUrl: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?q=80&w=800' },
];

//  Sub-Components 

const Header = ({ currentView, setCurrentView }) => (
  
     setCurrentView('profile')}>

     setCurrentView('swipe')}>

     setCurrentView('matches')}>

);

const SwipeDeck = ({ profiles, onSwipe, onCardLeftScreen }) => {
  if (profiles.length === 0) {
    return (
      
        That's everyone!
        You've seen all the profiles for now. Check back later for more.
      
    );
  }

  return (
    
      {profiles.map((profile, index) => (
         onSwipe(dir, profile.id, index)}
          onCardLeftScreen={() => onCardLeftScreen(profile.id)}
          preventSwipe={['up', 'down']}
        >

              {profile.name}, {profile.age}
              {profile.bio}

      ))}
    
  );
};

const MatchesList = ({ matches }) => (
  
    Your Matches ({matches.length})
    {matches.length === 0 ? (
      You haven't matched with anyone yet. Keep swiping!
    ) : (
      
        {matches.map(match => (

            {match.name}
          
        ))}
      
    )}
  
);

const UserProfile = () => (
    
        My Profile
        This is where your user profile settings and details would go.
        (Feature not implemented in this demo)
    
);

const LoadingSpinner = () => (

);

const ErrorDisplay = ({ message }) => (

            Oops! Something went wrong.
            {message}

);

//  Main App Component 
export default function App() {
  const [profiles, setProfiles] = useState([]);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentView, setCurrentView] = useState('swipe'); // 'swipe', 'matches', 'profile'
  
  // To keep track of the current swipable profiles
  const [currentIndex, setCurrentIndex] = useState(0);
  const currentIndexRef = useRef(currentIndex);

  const childRefs = useMemo(() =>
    Array(initialProfiles.length).fill(0).map(() => React.createRef()), 
  []);

  useEffect(() => {
    // Simulate fetching data from an API
    const fetchData = () => {
      setLoading(true);
      setError(null);
      setTimeout(() => {
        try {
          // In a real app, you'd fetch from an API
          // For now, we'll just use our mock data
          setProfiles(initialProfiles);
          setCurrentIndex(initialProfiles.length - 1);
        } catch (err) {
          setError("Failed to load profiles. Please try again later.");
        } finally {
          setLoading(false);
        }
      }, 1500); // 1.5 second delay to show loading state
    };
    fetchData();
  }, []);

  const updateCurrentIndex = (val) => {
    setCurrentIndex(val);
    currentIndexRef.current = val;
  }

  const canSwipe = currentIndex >= 0;

  const swiped = (direction, profile, index) => {
    console.log(`You swiped ${direction} on ${profile.name}`);
    updateCurrentIndex(index - 1);
    if (direction === 'right') {
        // Simulate a mutual match 50% of the time for demo purposes
        const isMutualMatch = Math.random()  [profile, ...prevMatches]);
        }
    }
  };

  const cardLeftScreen = (profileId) => {
    console.log(`${profileId} left the screen!`);
  };

  const swipe = async (dir) => {
    if (canSwipe && currentIndex  {
    if (loading) return ;
    if (error) return ;

    switch (currentView) {
      case 'swipe':
        return ;
      case 'matches':
        return ;
      case 'profile':
        return ;
      default:
        return ;
    }
  };

  return (

        {renderView()}
      
      {currentView === 'swipe' && !loading && !error && canSwipe && (
        
           swipe('left')} className="p-4 rounded-full bg-white shadow-lg text-yellow-500">

           swipe('right')} className="p-4 rounded-full bg-white shadow-lg text-green-500">

      )}
    
  );
}
```