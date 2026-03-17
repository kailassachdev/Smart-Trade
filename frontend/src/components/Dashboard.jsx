import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, DollarSign, TrendingUp, Wallet } from 'lucide-react';
import StatCard from './StatCard';
import TradeList from './TradeList';
import WalletCard from './WalletCard';
import { fetchPortfolio, fetchTradeLogs, startAgent, stopAgent, fetchStockHistory } from '../api';
import AIInsights from './AIInsights';
import TradeModal from './TradeModal';

const Dashboard = ({ onLogout }) => {
    const [portfolio, setPortfolio] = useState(null);
    const [trades, setTrades] = useState([]);
    const [loading, setLoading] = useState(true);
    const [agentStatus, setAgentStatus] = useState('stopped');
    const [isTradeModalOpen, setIsTradeModalOpen] = useState(false);
    const [selectedStock, setSelectedStock] = useState('AAPL');
    const [searchInput, setSearchInput] = useState('');
    const [stockChartData, setStockChartData] = useState([]);
    const [chartLoading, setChartLoading] = useState(false);

    const handleSearchSubmit = (e) => {
        e.preventDefault();
        if (searchInput.trim()) {
            setSelectedStock(searchInput.trim().toUpperCase());
            setSearchInput('');
        }
    };

    useEffect(() => {
        const loadData = async () => {
            try {
                const [portfolioData, logs] = await Promise.all([
                    fetchPortfolio(),
                    fetchTradeLogs()
                ]);
                setPortfolio(portfolioData);
                setTrades(logs);
                
                // If there's a portfolio position, maybe set default selected stock to the first one if we want
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

    useEffect(() => {
        const loadChart = async () => {
            setChartLoading(true);
            const data = await fetchStockHistory(selectedStock, '1mo', '1d');
            setStockChartData(data);
            setChartLoading(false);
        };
        loadChart();
    }, [selectedStock]);

    const handleStartAgent = async () => {
        const res = await startAgent();
        if (res.status?.includes("started") || res.status?.includes("running")) {
            setAgentStatus('running');
        }
    };

    const handleStopAgent = async () => {
        const res = await stopAgent();
        setAgentStatus('stopped');
    };

    const handleRefresh = async () => {
        try {
            const [portfolioData, logs] = await Promise.all([
                fetchPortfolio(),
                fetchTradeLogs()
            ]);
            setPortfolio(portfolioData);
            setTrades(logs);
        } catch (err) {
            console.error("Refresh failed", err);
        }
    };

    if (loading) {
        return <div className="flex items-center justify-center h-screen text-accent">Loading Smart Trade...</div>;
    }

    return (
        <div className="min-h-screen bg-primary p-8">
            <TradeModal 
                isOpen={isTradeModalOpen} 
                onClose={() => setIsTradeModalOpen(false)} 
                onUpdate={handleRefresh} 
            />
            <header className="mb-8 flex justify-between items-center bg-secondary p-6 rounded-2xl">
                <div>
                    <h1 className="text-3xl font-extrabold text-white tracking-tight mb-1">Smart Trade</h1>
                    <p className="text-gray-400 text-sm font-medium">AI-Powered Autonomous Trading</p>
                </div>
                <div className="flex gap-4">
                    <button
                        onClick={() => setIsTradeModalOpen(true)}
                        className="px-5 py-2.5 rounded-xl font-bold transition-all bg-white text-black hover:bg-gray-200 shadow-md"
                    >
                        Trade Stocks
                    </button>
                    <div className="w-px bg-gray-700 mx-2"></div>
                    <button
                        onClick={handleStartAgent}
                        className={`px-5 py-2.5 rounded-xl font-bold transition-all ${agentStatus === 'running' ? 'bg-primary border border-gray-700 text-gray-400 cursor-not-allowed' : 'bg-accent hover:bg-success text-black'}`}
                        disabled={agentStatus === 'running'}
                    >
                        {agentStatus === 'running' ? 'Agent Active' : 'Start Agent'}
                    </button>
                    <button
                        onClick={handleStopAgent}
                        className="bg-transparent border border-danger text-danger hover:bg-danger/10 px-5 py-2.5 rounded-xl font-bold transition-all"
                    >
                        Stop Agent
                    </button>
                    <div className="w-px bg-gray-700 mx-2"></div>
                    <button
                        onClick={onLogout}
                        className="bg-primary border border-gray-700 text-gray-400 hover:text-white hover:border-white px-5 py-2.5 rounded-xl font-bold transition-all"
                    >
                        Logout
                    </button>
                </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-6">
                    <StatCard
                        title="Total Portfolio Value"
                        value={`$${portfolio?.portfolio_value?.toFixed(2) || '0.00'}`}
                        icon={DollarSign}
                        trend={2.5}
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
                <div className="md:col-span-1">
                    <WalletCard balance={portfolio?.cash || 0} onUpdate={handleRefresh} />
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-8">
                    <div className="bg-secondary p-6 rounded-2xl">
                        <div className="flex justify-between items-start mb-8">
                            <div>
                                <h3 className="text-lg font-bold text-white flex items-center gap-3">
                                    {selectedStock} Performance
                                </h3>
                                <p className="text-gray-400 text-sm mt-1">Past 1 Month</p>
                                <form onSubmit={handleSearchSubmit} className="mt-4 flex gap-2">
                                    <input 
                                        type="text" 
                                        placeholder="Search any symbol (e.g. TSLA)" 
                                        value={searchInput}
                                        onChange={(e) => setSearchInput(e.target.value.toUpperCase())}
                                        className="bg-primary border border-gray-700 text-white text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-accent"
                                    />
                                    <button type="submit" className="bg-accent text-black font-bold text-sm px-3 py-1.5 rounded-lg hover:bg-success transition-colors">
                                        Graph
                                    </button>
                                </form>
                            </div>
                            <div className="text-right">
                                {stockChartData.length > 0 && (
                                    <>
                                        <p className="text-3xl font-bold text-white tracking-tight">
                                            ${stockChartData[stockChartData.length - 1].value.toFixed(2)}
                                        </p>
                                        {/* Simple calculation for display */}
                                        <p className={`${stockChartData[stockChartData.length - 1].value >= stockChartData[0].value ? 'text-success' : 'text-danger'} font-medium`}>
                                            {stockChartData[stockChartData.length - 1].value >= stockChartData[0].value ? '+' : ''}
                                            {((stockChartData[stockChartData.length - 1].value - stockChartData[0].value) / stockChartData[0].value * 100).toFixed(2)}%
                                        </p>
                                    </>
                                )}
                            </div>
                        </div>
                        <div className="h-[350px] w-full mt-4 flex items-center justify-center">
                            {chartLoading ? (
                                <div className="text-accent animate-pulse">Loading Chart Data...</div>
                            ) : (
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={stockChartData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1f1f1f" vertical={false} />
                                        <XAxis dataKey="time" stroke="#555" tick={{ fill: '#888', fontSize: 12 }} axisLine={false} tickLine={false} dy={10} minTickGap={30} />
                                        <YAxis stroke="#555" domain={['auto', 'auto']} tick={{ fill: '#888', fontSize: 12 }} axisLine={false} tickLine={false} dx={-10} hide />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#000', border: '1px solid #333', borderRadius: '12px' }}
                                            itemStyle={{ color: '#00C805', fontWeight: 'bold' }}
                                            labelStyle={{ color: '#888', marginBottom: '4px' }}
                                        />
                                        <Line
                                            type="monotone"
                                            dataKey="value"
                                            stroke="#00C805"
                                            strokeWidth={3}
                                            dot={false}
                                            activeDot={{ r: 6, fill: '#00C805', stroke: '#000', strokeWidth: 2 }}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            )}
                        </div>
                    </div>

                    <TradeList trades={trades} />
                </div>

                <div className="space-y-8">
                    <AIInsights />

                    <div className="bg-secondary p-6 rounded-2xl">
                        <h3 className="text-lg font-bold text-white mb-6">Agent Status</h3>
                        <div className="flex items-center gap-3 mb-6 p-4 bg-primary rounded-xl">
                            <div className="w-3 h-3 rounded-full bg-success animate-pulse shadow-[0_0_8px_#00C805]"></div>
                            <span className="text-white font-medium">System Operational</span>
                        </div>
                        <div className="space-y-4">
                            <div className="p-4 rounded-xl border border-primary hover:border-success/30 transition-colors">
                                <p className="text-xs text-gray-500 mb-1 uppercase tracking-wider font-semibold">Last RAG Decision</p>
                                <p className="text-sm text-gray-300">Analyzed "Moving Average Crossover" strategy. Market condition favorable for long positions.</p>
                            </div>
                            <div className="p-4 rounded-xl border border-primary hover:border-success/30 transition-colors">
                                <p className="text-xs text-gray-500 mb-1 uppercase tracking-wider font-semibold">Active Strategy</p>
                                <p className="text-sm text-accent font-bold">Momentum + RSI (RAG Enhanced)</p>
                            </div>
                        </div>
                    </div>

                    <div className="bg-secondary p-6 rounded-2xl">
                        <h3 className="text-lg font-bold text-white mb-6">Open Positions</h3>
                        <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                            {portfolio?.positions?.map((pos, idx) => {
                                const isSelected = selectedStock === pos.symbol;
                                return (
                                <div 
                                    key={idx} 
                                    onClick={() => setSelectedStock(pos.symbol)}
                                    className={`flex justify-between items-center p-4 bg-primary rounded-xl hover:bg-primary/80 transition-colors cursor-pointer group border ${isSelected ? 'border-accent' : 'border-transparent'}`}
                                >
                                    <div>
                                        <p className="font-bold text-white text-lg group-hover:text-accent transition-colors">{pos.symbol}</p>
                                        <p className="text-xs text-gray-500 font-medium">{pos.qty} shares</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-white font-bold text-lg">${pos.current_price?.toFixed(2) || pos.avg_entry_price.toFixed(2)}</p>
                                        <p className="text-xs text-gray-500 font-medium">Avg: ${pos.avg_entry_price.toFixed(2)}</p>
                                    </div>
                                </div>
                            )})}
                            {(!portfolio?.positions || portfolio.positions.length === 0) && (
                                <div className="p-8 text-center bg-primary rounded-xl">
                                    <p className="text-gray-500 font-medium pb-2">No open positions</p>
                                    <p className="text-gray-600 text-sm">Ready to buy</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
