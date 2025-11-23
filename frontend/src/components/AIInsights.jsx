import React, { useState, useEffect } from 'react';
import { fetchAIAnalysis } from '../api';

const AIInsights = () => {
    const [analysis, setAnalysis] = useState("Initializing AI Agent...");
    const [loading, setLoading] = useState(false);

    const generateInsight = async () => {
        setLoading(true);
        // Mock market data for the prompt - in a real app this would come from the state
        const marketData = {
            symbol: "MARKET_OVERVIEW",
            price: 0,
            trends: {
                "volatility": "High",
                "sector": "Tech",
                "sentiment": "Mixed"
            }
        };

        const result = await fetchAIAnalysis(marketData);
        if (result && result.analysis) {
            setAnalysis(result.analysis);
        }
        setLoading(false);
    };

    useEffect(() => {
        generateInsight();
        const interval = setInterval(generateInsight, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="bg-gradient-to-br from-indigo-900/50 to-purple-900/50 p-6 rounded-xl shadow-lg border border-indigo-500/30 backdrop-blur-sm relative overflow-hidden group">
            {/* Animated background glow */}
            <div className="absolute -top-24 -right-24 w-48 h-48 bg-indigo-500/20 rounded-full blur-3xl group-hover:bg-indigo-500/30 transition-all duration-1000"></div>

            <div className="flex items-center justify-between mb-4 relative z-10">
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
                    <h3 className="text-lg font-semibold text-white tracking-wide">Gemini AI Insights</h3>
                </div>
                <button
                    onClick={generateInsight}
                    disabled={loading}
                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors disabled:opacity-50"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className={`h-5 w-5 text-indigo-300 ${loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                </button>
            </div>

            <div className="relative z-10 min-h-[100px]">
                {loading ? (
                    <div className="space-y-3 animate-pulse">
                        <div className="h-4 bg-indigo-400/20 rounded w-3/4"></div>
                        <div className="h-4 bg-indigo-400/20 rounded w-full"></div>
                        <div className="h-4 bg-indigo-400/20 rounded w-5/6"></div>
                    </div>
                ) : (
                    <div className="prose prose-invert prose-sm max-w-none">
                        <p className="text-indigo-100 leading-relaxed whitespace-pre-line">
                            {analysis}
                        </p>
                    </div>
                )}
            </div>

            <div className="mt-4 pt-4 border-t border-white/10 flex justify-between items-center text-xs text-indigo-300/70">
                <span>Powered by Google Gemini</span>
                <span>Updated just now</span>
            </div>
        </div>
    );
};

export default AIInsights;
