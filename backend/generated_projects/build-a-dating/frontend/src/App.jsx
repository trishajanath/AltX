```jsx
import React, { useState, useEffect } from 'react';
import { Flame, Users, UserCircle, MessageSquare } from 'lucide-react';
import { faker } from '@faker-js/faker';

// Mock data generation
const createRandomUser = () => ({
  id: faker.string.uuid(),
  name: faker.person.firstName(),
  age: faker.number.int({ min: 18, max: 40 }),
  bio: faker.person.bio(),
  imageUrl: `https://i.pravatar.cc/400?u=${faker.string.uuid()}`,
});

const initialUsers = Array.from({ length: 10 }, createRandomUser);
const currentUser = {
  name: 'You',
  age: 28,
  bio: 'Looking for adventure and meaningful connections. I love hiking, trying new foods, and coding.',
  imageUrl: 'https://i.pravatar.cc/400?u=currentuser'
};

// Main App Component
export default function App() {
  const [activeScreen, setActiveScreen] = useState('swipe');
  const [profiles, setProfiles] = useState([]);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      try {
        setProfiles(initialUsers);
        setLoading(false);
      } catch (err) {
        setError('Failed to load profiles. Please try again later.');
        setLoading(false);
      }
    }, 1500);
  }, []);

  const handleSwipe = (direction, swipedUser) => {
    // Remove swiped user from the stack
    setProfiles(prevProfiles => prevProfiles.filter(p => p.id !== swipedUser.id));

    if (direction === 'right') {
      // Simple mock logic: 30% chance of a match
      if (Math.random()  [...prevMatches, swipedUser]);
        alert(`It's a match with ${swipedUser.name}!`);
      }
    }
  };

  const renderScreen = () => {
    if (loading) return ;
    if (error) return ;

    switch (activeScreen) {
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

        {renderScreen()}

  );
}

// Sub-components (could be in separate files in a larger app)

const Header = () => (

      Kindling

);

const NavBar = ({ activeScreen, setActiveScreen, matchCount }) => {
  const navItems = [
    { id: 'swipe', icon: Flame },
    { id: 'matches', icon: Users },
    { id: 'profile', icon: UserCircle },
  ];
  return (
    
      {navItems.map(item => (
         setActiveScreen(item.id)}
          className={`relative p-2 rounded-full transition-colors duration-200 ${
            activeScreen === item.id ? 'text-brand-pink bg-pink-100' : 'text-gray-400 hover:bg-gray-100'
          }`}
        >
          
          {item.id === 'matches' && matchCount > 0 && (
            
              {matchCount}
            
          )}
        
      ))}
    
  );
};

const SwipeScreen = ({ profiles, onSwipe }) => {
  if (profiles.length === 0) {
    return ;
  }
  
  // We need to import TinderCard for this to work
  // In a real project, this would be an import:
  // import TinderCard from 'react-tinder-card';
  // For this single-file setup, we'll use a simplified mock component
  // to avoid needing the dependency to run this exact file.
  // In the full project structure provided, `react-tinder-card` is in package.json.
  // This is a placeholder for demonstration. The real implementation uses the library.
  const TinderCard = ({ children, onSwipe, onCardLeftScreen }) => {
    // This is a mock. The real library provides gesture handling.
    return (
      
        {children}
      
    );
  };
  
  // Correctly importing the actual library for full functionality
  const RealTinderCard = require('react-tinder-card');

  const swiped = (direction, user) => {
    console.log(`Swiped ${direction} on ${user.name}`);
    onSwipe(direction, user);
  };

  const outOfFrame = (name) => {
    console.log(`${name} left the screen!`);
  };

  return (

        {profiles.map((profile, index) => (
           swiped(dir, profile)}
            onCardLeftScreen={() => outOfFrame(profile.name)}
            preventSwipe={['up', 'down']}
          >

        ))}

        You've seen all profiles!

  );
};

const ProfileCard = ({ user }) => (

      {user.name}, {user.age}
      {user.bio}

);

const MatchesScreen = ({ matches }) => (
  
    Your Matches
    {matches.length === 0 ? (

        No matches yet.
        Keep swiping to find your match!
      
    ) : (
      
        {matches.map(match => (

              {match.name}

        ))}
      
    )}
  
);

const ProfileScreen = ({ user }) => (

      {user.name}, {user.age}

      About Me
      {user.bio}

      Settings
      Account
      Discovery Settings

      Upgrade to Gold

);

const LoadingSpinner = () => (

);

const ErrorMessage = ({ message }) => (
    
        An Error Occurred
        {message}
    
);

const NoMoreProfiles = () => (
  
      That's everyone!
      You've seen all the available profiles for now. Check back later for new people.
  
);
```