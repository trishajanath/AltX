import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { motion } from 'framer-motion';
import { User, Mail, Calendar, CheckCircle, XCircle, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const UserProfile = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  if (!user) {
    return null;
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/10 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/20 p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">User Profile</h2>
        <motion.button
          onClick={handleLogout}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="flex items-center gap-2 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg transition-all"
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </motion.button>
      </div>

      <div className="space-y-4">
        {/* Username */}
        <div className="flex items-center gap-3 p-4 bg-white/5 rounded-lg">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <User className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <p className="text-sm text-gray-400">Username</p>
            <p className="text-white font-semibold">{user.username}</p>
          </div>
        </div>

        {/* Email */}
        <div className="flex items-center gap-3 p-4 bg-white/5 rounded-lg">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <Mail className="w-5 h-5 text-blue-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm text-gray-400">Email</p>
            <p className="text-white font-semibold">{user.email}</p>
          </div>
          <div className="flex items-center gap-1">
            {user.is_verified ? (
              <>
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-xs text-green-400">Verified</span>
              </>
            ) : (
              <>
                <XCircle className="w-4 h-4 text-yellow-400" />
                <span className="text-xs text-yellow-400">Not Verified</span>
              </>
            )}
          </div>
        </div>

        {/* Account Created */}
        <div className="flex items-center gap-3 p-4 bg-white/5 rounded-lg">
          <div className="p-2 bg-indigo-500/20 rounded-lg">
            <Calendar className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <p className="text-sm text-gray-400">Member Since</p>
            <p className="text-white font-semibold">{formatDate(user.created_at)}</p>
          </div>
        </div>

        {/* Account Status */}
        <div className="flex items-center gap-3 p-4 bg-white/5 rounded-lg">
          <div className={`p-2 ${user.is_active ? 'bg-green-500/20' : 'bg-red-500/20'} rounded-lg`}>
            {user.is_active ? (
              <CheckCircle className="w-5 h-5 text-green-400" />
            ) : (
              <XCircle className="w-5 h-5 text-red-400" />
            )}
          </div>
          <div>
            <p className="text-sm text-gray-400">Account Status</p>
            <p className={`font-semibold ${user.is_active ? 'text-green-400' : 'text-red-400'}`}>
              {user.is_active ? 'Active' : 'Inactive'}
            </p>
          </div>
        </div>
      </div>

      {/* User ID (for developers) */}
      <div className="mt-6 p-3 bg-black/20 rounded-lg">
        <p className="text-xs text-gray-400 mb-1">User ID</p>
        <code className="text-xs text-gray-300 font-mono break-all">{user.id}</code>
      </div>
    </motion.div>
  );
};

export default UserProfile;
