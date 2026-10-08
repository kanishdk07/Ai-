import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, Lock, User, LogIn, Sparkles, CheckCircle2 } from 'lucide-react';
import { UserRole } from '../types';

interface LoginPageProps {
  onLoginSuccess: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const { login, switchRole } = useAuth();

  const [username, setUsername] = useState<string>('admin');
  const [password, setPassword] = useState<string>('password123');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await login(username, password);
      onLoginSuccess();
    } catch (err: any) {
      setError(err?.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickLogin = (role: UserRole) => {
    switchRole(role);
    onLoginSuccess();
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-gray-100 flex flex-col justify-center items-center p-4 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-red-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-80 h-80 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex p-3 bg-gradient-to-tr from-red-600 to-amber-500 rounded-2xl text-white shadow-2xl shadow-red-600/40 mb-3 animate-bounce">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-extrabold text-white font-['Outfit'] tracking-wider">
            SAFEWAY<span className="text-red-500">.AI</span>
          </h1>
          <p className="text-xs text-gray-400 font-mono mt-1">
            AI Highway Accident Detection & Emergency Response Network
          </p>
        </div>

        {/* Login Box */}
        <div className="p-8 rounded-3xl bg-gray-900/90 border border-gray-800 shadow-2xl backdrop-blur-xl">
          <h2 className="text-base font-bold text-white mb-1">Operator Authentication</h2>
          <p className="text-xs text-gray-400 mb-6">Enter authorized credentials to access command dashboard.</p>

          {error && (
            <div className="mb-4 p-3 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-300">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">
                Username / Call Sign
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin or operator"
                  className="w-full pl-10 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-red-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">
                Secure Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-red-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-red-600 hover:bg-red-500 text-white font-bold rounded-xl text-sm uppercase tracking-wider shadow-lg shadow-red-600/30 transition duration-200 disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
            >
              <LogIn className="w-4 h-4" />
              {isLoading ? 'Authenticating...' : 'Sign In To Control Center'}
            </button>
          </form>

          {/* Quick Demo Access Roles */}
          <div className="mt-6 pt-6 border-t border-gray-800 text-center">
            <p className="text-[11px] font-mono text-gray-400 uppercase tracking-wider mb-2.5 flex items-center justify-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              Quick Testing One-Click Access
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('admin')}
                className="px-3 py-2 bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-xl text-xs font-bold text-white transition hover:border-red-500"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('operator')}
                className="px-3 py-2 bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-xl text-xs font-bold text-white transition hover:border-blue-500"
              >
                Operator
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('viewer')}
                className="px-3 py-2 bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-xl text-xs font-bold text-white transition hover:border-purple-500"
              >
                Viewer
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
