import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, DollarSign, TrendingUp, Wallet } from 'lucide-react';
import StatCard from './StatCard';
import TradeList from './TradeList';
import { fetchPortfolio, fetchTradeLogs, startAgent, stopAgent } from '../api';
import AIInsights from './AIInsights';

const Dashboard = () => {
    const [portfolio, setPortfolio] = useState(null);
    const [trades, setTrades] = useState([]);
    const [loading, setLoading] = useState(true);
    const [agentStatus, setAgentStatus] = useState('stopped');

    // Mock chart data for visualization
    const chartData = [
        { time: '09:30', value: 100000 },
        { time: '10:00', value: 100200 },
        { time: '10:30', value: 100150 },
        { time: '11:00', value: 100400 },
        { time: '11:30', value: 100300 },
        { time: '12:00', value: 100600 },
        { time: '12:30', value: 100800 },
    ];

    useEffect(() => {
        const loadData = async () => {
            try {
                const [portfolioData, logs] = await Promise.all([
                    fetchPortfolio(),
                    fetchTradeLogs()
                ]);
                setPortfolio(portfolioData);
                setTrades(logs);
            } catch (err) {
                console.error("Error loading dashboard data:", err);
            } finally {
                setLoading(false);
            }
        };

        loadData();
        const interval = setInterval(loadData, 5000); // Refresh every 5s
        return () => clearInterval(interval);
    }, []);

    const handleStartAgent = async () => {
        const res = await startAgent();
        if (res.status === "Agent started" || res.status === "Agent already running") {
            setAgentStatus('running');
        }
    };

    const handleStopAgent = async () => {
        const res = await stopAgent();
        setAgentStatus('stopped');
    };

    if (loading) {
        return <div className="flex items-center justify-center h-screen text-accent">Loading Smart Trade...</div>;
    }

    return (
        <div className="min-h-screen bg-primary p-8">
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Smart Trade Dashboard</h1>
                    <p className="text-gray-400">AI-Powered Autonomous Trading Agent</p>
                </div>
                <div className="flex gap-4">
                    <button
                        onClick={handleStartAgent}
                        className={`px-4 py-2 rounded-lg font-semibold transition-colors ${agentStatus === 'running' ? 'bg-gray-600 text-gray-400 cursor-not-allowed' : 'bg-accent hover:bg-accent/90 text-primary'}`}
                        disabled={agentStatus === 'running'}
                    >
                        {agentStatus === 'running' ? 'Agent Running' : 'Start Agent'}
                    </button>
                    <button
                        onClick={handleStopAgent}
                        className="bg-danger hover:bg-danger/90 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
                    >
                        Stop Agent
                    </button>
                </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <StatCard
                    title="Total Portfolio Value"
                    value={`$${portfolio?.portfolio_value?.toFixed(2) || '0.00'}`}
                    icon={DollarSign}
                    trend={2.5}
                />
                <StatCard
                    title="Cash Balance"
                    value={`$${portfolio?.cash?.toFixed(2) || '0.00'}`}
                    icon={Wallet}
                />
                <StatCard
                    title="Day's Gain/Loss"
                    value={`$${(portfolio?.equity || 0).toFixed(2)}`}
                    icon={TrendingUp}
                    trend={1.2}
                />
                <StatCard
                    title="Active Positions"
                    value={portfolio?.positions?.length || 0}
                    icon={Activity}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-8">
                    <div className="bg-secondary p-6 rounded-xl shadow-lg border border-gray-700">
                        <h3 className="text-lg font-semibold text-white mb-6">Portfolio Performance</h3>
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                    <XAxis dataKey="time" stroke="#94a3b8" />
                                    <YAxis stroke="#94a3b8" domain={['auto', 'auto']} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                                        itemStyle={{ color: '#fff' }}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="value"
                                        stroke="#38bdf8"
                                        strokeWidth={2}
                                        dot={false}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    <TradeList trades={trades} />
                </div>

                <div className="space-y-8">
                    <AIInsights />

                    <div className="bg-secondary p-6 rounded-xl shadow-lg border border-gray-700">
                        <h3 className="text-lg font-semibold text-white mb-4">Agent Status</h3>
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-3 h-3 rounded-full bg-success animate-pulse"></div>
                            <span className="text-gray-300">System Operational</span>
                        </div>
                        <div className="space-y-4">
                            <div className="bg-primary/50 p-4 rounded-lg border border-gray-700">
                                <p className="text-xs text-gray-400 mb-1">Last RAG Decision</p>
                                <p className="text-sm text-white">Analyzed "Moving Average Crossover" strategy. Market condition favorable for long positions.</p>
                            </div>
                            <div className="bg-primary/50 p-4 rounded-lg border border-gray-700">
                                <p className="text-xs text-gray-400 mb-1">Active Strategy</p>
                                <p className="text-sm text-accent font-medium">Momentum + RSI (RAG Enhanced)</p>
                            </div>
                        </div>
                    </div>

                    <div className="bg-secondary p-6 rounded-xl shadow-lg border border-gray-700">
                        <h3 className="text-lg font-semibold text-white mb-4">Open Positions</h3>
                        <div className="space-y-3">
                            {portfolio?.positions?.map((pos, idx) => (
                                <div key={idx} className="flex justify-between items-center p-3 bg-primary/50 rounded-lg border border-gray-700">
                                    <div>
                                        <p className="font-bold text-white">{pos.symbol}</p>
                                        <p className="text-xs text-gray-400">{pos.qty} shares</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-success font-medium">+1.2%</p>
                                        <p className="text-xs text-gray-400">${pos.avg_entry_price}</p>
                                    </div>
                                </div>
                            ))}
                            {(!portfolio?.positions || portfolio.positions.length === 0) && (
                                <p className="text-gray-500 text-sm text-center py-4">No open positions</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
