import React, { useState } from 'react';
import { TrendingUp, User, Lock, Mail } from 'lucide-react';

const Auth = ({ onLogin }) => {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            if (isLogin) {
                // Login
                const params = new URLSearchParams();
                params.append('username', username);
                params.append('password', password);

                const res = await fetch('http://localhost:8000/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: params
                });
                
                if (!res.ok) {
                    const data = await res.json();
                    throw new Error(data.detail || 'Login failed');
                }
                const data = await res.json();
                localStorage.setItem('token', data.access_token);
                onLogin();
            } else {
                // Register
                const res = await fetch('http://localhost:8000/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                if (!res.ok) {
                    const data = await res.json();
                    throw new Error(data.detail || 'Registration failed');
                }
                // Automatically login after register
                setIsLogin(true);
                setError("Registration successful! Please login.");
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-primary flex items-center justify-center p-4">
            <div className="w-full max-w-md bg-secondary rounded-2xl p-8 border border-gray-800 shadow-2xl">
                <div className="flex flex-col items-center mb-8">
                    <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center mb-4 border border-accent/20">
                        <TrendingUp className="w-8 h-8 text-accent" />
                    </div>
                    <h1 className="text-3xl font-extrabold text-white tracking-tight">Smart Trade</h1>
                    <p className="text-gray-400 font-medium mt-1">
                        {isLogin ? 'Welcome back to the markets' : 'Start your trading journey'}
                    </p>
                </div>

                {error && (
                    <div className={`p-4 rounded-xl mb-6 text-sm font-medium ${error.includes('successful') ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Username</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <User className="h-5 w-5 text-gray-600" />
                            </div>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full bg-primary border border-gray-700 text-white rounded-xl py-3 pl-11 pr-4 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-colors"
                                placeholder="Trader123"
                                required
                            />
                        </div>
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Password</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <Lock className="h-5 w-5 text-gray-600" />
                            </div>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-primary border border-gray-700 text-white rounded-xl py-3 pl-11 pr-4 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-colors"
                                placeholder="••••••••"
                                required
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-accent hover:bg-success text-black font-bold py-3.5 rounded-xl transition-colors disabled:opacity-50 mt-4"
                    >
                        {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
                    </button>
                </form>

                <div className="mt-8 text-center">
                    <button
                        onClick={() => { setIsLogin(!isLogin); setError(null); }}
                        className="text-gray-400 hover:text-white text-sm font-medium transition-colors"
                    >
                        {isLogin ? "Don't have an account? Sign up" : "Already have an account? Log in"}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Auth;
