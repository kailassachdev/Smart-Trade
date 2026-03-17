import React, { useState, useEffect } from 'react';
import { Wallet, ArrowDownToLine, ArrowUpFromLine, Clock } from 'lucide-react';
import { depositWallet, withdrawWallet, fetchWalletHistory } from '../api';

const WalletCard = ({ balance = 0, onUpdate }) => {
    const [isHoveredDep, setIsHoveredDep] = useState(false);
    const [isHoveredWith, setIsHoveredWith] = useState(false);
    const [loading, setLoading] = useState(false);

    const [history, setHistory] = useState([]);

    useEffect(() => {
        const loadHistory = async () => {
            const data = await fetchWalletHistory();
            setHistory(data.slice(0, 5)); // show latest 5
        };
        loadHistory();
    }, [balance]); // Reload history when balance changes

    const handleTransaction = async (type) => {
        const amountStr = window.prompt(`Enter amount to ${type}:`);
        if (!amountStr) return;
        const amount = parseFloat(amountStr);
        if (isNaN(amount) || amount <= 0) {
            alert('Invalid amount');
            return;
        }

        setLoading(true);
        try {
            if (type === 'deposit') {
                await depositWallet(amount);
            } else {
                await withdrawWallet(amount);
            }
            if (onUpdate) onUpdate();
        } catch (error) {
            alert(error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={`bg-secondary p-6 rounded-2xl flex flex-col h-full ${loading ? 'opacity-50' : ''}`}>
            <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-primary rounded-full">
                    <Wallet className="text-white w-6 h-6" />
                </div>
                <h2 className="text-xl font-semibold text-white">Digital Wallet</h2>
            </div>

            <div className="mb-8">
                <p className="text-gray-400 text-sm mb-1 font-medium">Buying Power</p>
                <h1 className="text-5xl font-bold text-white tracking-tight">${balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}</h1>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-8">
                <button 
                    className="flex flex-col items-center justify-center p-4 bg-primary rounded-xl transition-all duration-200 border border-transparent hover:border-success/50 group disabled:opacity-50"
                    onMouseEnter={() => setIsHoveredDep(true)}
                    onMouseLeave={() => setIsHoveredDep(false)}
                    onClick={() => handleTransaction('deposit')}
                    disabled={loading}
                >
                    <div className="w-10 h-10 rounded-full bg-success/10 flex items-center justify-center mb-2 group-hover:bg-success transition-colors">
                        <ArrowDownToLine className={`w-5 h-5 ${isHoveredDep ? 'text-black' : 'text-success'}`} />
                    </div>
                    <span className="font-semibold text-sm">Deposit</span>
                </button>
                <button 
                    className="flex flex-col items-center justify-center p-4 bg-primary rounded-xl transition-all duration-200 border border-transparent hover:border-white/20 group disabled:opacity-50"
                    onMouseEnter={() => setIsHoveredWith(true)}
                    onMouseLeave={() => setIsHoveredWith(false)}
                    onClick={() => handleTransaction('withdraw')}
                    disabled={loading}
                >
                    <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center mb-2 group-hover:bg-white transition-colors">
                        <ArrowUpFromLine className={`w-5 h-5 ${isHoveredWith ? 'text-black' : 'text-white'}`} />
                    </div>
                    <span className="font-semibold text-sm">Withdraw</span>
                </button>
            </div>

            <div className="mt-auto">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Recent Transfers</h3>
                    <Clock className="w-4 h-4 text-gray-500" />
                </div>
                <div className="space-y-3">
                    {history.map((tx, idx) => (
                        <div key={idx} className="flex justify-between items-center py-2 border-b border-primary last:border-0">
                            <div>
                                <p className="font-medium text-white">{tx.action === 'DEPOSIT' ? 'Deposit' : 'Withdrawal'}</p>
                                <p className="text-xs text-gray-500">{new Date(tx.timestamp).toLocaleString()}</p>
                            </div>
                            <div className="text-right">
                                <p className={`font-medium ${tx.action === 'DEPOSIT' ? 'text-success' : 'text-white'}`}>
                                    {tx.action === 'DEPOSIT' ? '+' : '-'}${tx.amount.toLocaleString()}
                                </p>
                                <p className="text-xs text-success">Completed</p>
                            </div>
                        </div>
                    ))}
                    {history.length === 0 && (
                        <p className="text-xs text-gray-500 text-center py-4">No recent transfers</p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default WalletCard;
