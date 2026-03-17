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
        <div className="bg-secondary p-6 rounded-2xl relative overflow-hidden group">
            <div className="flex items-center justify-between mb-4 relative z-10">
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-accent animate-pulse shadow-[0_0_8px_#00C805]"></div>
                    <h3 className="text-lg font-bold text-white tracking-tight">Gemini AI Insights</h3>
                </div>
                <button
                    onClick={generateInsight}
                    disabled={loading}
                    className="p-2 rounded-full bg-primary hover:bg-primary/80 transition-colors disabled:opacity-50 border border-transparent hover:border-accent/30 text-gray-400 hover:text-accent"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className={`h-5 w-5 ${loading ? 'animate-spin text-accent' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                </button>
            </div>

            <div className="relative z-10 min-h-[100px] mt-2">
                {loading ? (
                    <div className="space-y-3 animate-pulse">
                        <div className="h-4 bg-primary rounded w-3/4"></div>
                        <div className="h-4 bg-primary rounded w-full"></div>
                        <div className="h-4 bg-primary rounded w-5/6"></div>
                    </div>
                ) : (
                    <div className="prose prose-invert prose-sm max-w-none">
                        <p className="text-gray-300 leading-relaxed whitespace-pre-line font-medium">
                            {analysis}
                        </p>
                    </div>
                )}
            </div>

            <div className="mt-6 pt-4 border-t border-primary flex justify-between items-center text-xs text-gray-500 font-semibold uppercase tracking-wider">
                <span>Powered by Gemini</span>
                <span>Just Now</span>
            </div>
        </div>
    );
};

export default AIInsights;
