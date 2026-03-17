import React, { useState } from 'react';
import { X, Search, ArrowRightLeft } from 'lucide-react';
import { executeTrade } from '../api';

const TradeModal = ({ isOpen, onClose, onUpdate }) => {
    const [symbol, setSymbol] = useState('');
    const [quantity, setQuantity] = useState(1);
    const [action, setAction] = useState('BUY'); // 'BUY' or 'SELL'
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [message, setMessage] = useState(null);

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setMessage(null);
        if (!symbol) {
            setError("Stock symbol is required");
            return;
        }
        if (quantity <= 0) {
            setError("Quantity must be greater than 0");
            return;
        }

        setLoading(true);
        try {
            const res = await executeTrade(action, symbol, parseInt(quantity));
            setMessage(res.message);
            if (onUpdate) onUpdate();
            // Clear form
            setSymbol('');
            setQuantity(1);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-secondary w-full max-w-md rounded-2xl border border-gray-800 shadow-2xl overflow-hidden flex flex-col relative">
                <button 
                    onClick={onClose}
                    className="absolute top-4 right-4 p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-full transition-colors"
                >
                    <X className="w-5 h-5" />
                </button>

                <div className="p-6 border-b border-gray-800">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center border border-accent/50">
                            <ArrowRightLeft className="w-5 h-5 text-accent" />
                        </div>
                        <h2 className="text-xl font-bold text-white tracking-tight">Trade Stocks</h2>
                    </div>
                </div>

                <div className="p-6">
                    {error && (
                        <div className="mb-4 p-3 rounded-xl bg-danger/10 border border-danger/30 text-danger text-sm font-medium">
                            {error}
                        </div>
                    )}
                    {message && (
                        <div className="mb-4 p-3 rounded-xl bg-success/10 border border-success/30 text-success text-sm font-medium">
                            {message}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div className="flex gap-2">
                            <button
                                type="button"
                                onClick={() => setAction('BUY')}
                                className={`flex-1 py-2 rounded-xl text-sm font-bold transition-colors ${action === 'BUY' ? 'bg-success text-black' : 'bg-primary text-gray-400 border border-gray-800 hover:border-success/50'}`}
                            >
                                BUY
                            </button>
                            <button
                                type="button"
                                onClick={() => setAction('SELL')}
                                className={`flex-1 py-2 rounded-xl text-sm font-bold transition-colors ${action === 'SELL' ? 'bg-danger text-white' : 'bg-primary text-gray-400 border border-gray-800 hover:border-danger/50'}`}
                            >
                                SELL
                            </button>
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Symbol</label>
                            <div className="relative">
                                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-600" />
                                <input
                                    type="text"
                                    value={symbol}
                                    onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                                    placeholder="e.g. AAPL"
                                    className="w-full bg-primary border border-gray-700 text-white rounded-xl py-3 pl-11 pr-4 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-colors font-mono uppercase"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Quantity</label>
                            <input
                                type="number"
                                min="1"
                                value={quantity}
                                onChange={(e) => setQuantity(e.target.value)}
                                className="w-full bg-primary border border-gray-700 text-white rounded-xl py-3 px-4 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-colors"
                            />
                        </div>

                        <button 
                            type="submit"
                            disabled={loading}
                            className={`w-full py-4 text-center font-bold text-lg rounded-xl transition-all shadow-lg mt-2 disabled:opacity-50 ${action === 'BUY' ? 'bg-success hover:bg-success/90 text-black shadow-success/20' : 'bg-danger hover:bg-danger/90 text-white shadow-danger/20'}`}
                        >
                            {loading ? 'Processing...' : `Review ${action} Order`}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default TradeModal;
