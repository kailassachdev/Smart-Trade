import React from 'react';

const TradeList = ({ trades }) => {
    const [expandedId, setExpandedId] = React.useState(null);

    return (
        <div className="bg-secondary rounded-xl shadow-lg border border-gray-700 overflow-hidden">
            <div className="p-6 border-b border-gray-700">
                <h3 className="text-lg font-semibold text-white">Recent Activity</h3>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead className="bg-gray-800 text-gray-400 text-xs uppercase">
                        <tr>
                            <th className="px-6 py-3">Time</th>
                            <th className="px-6 py-3">Symbol</th>
                            <th className="px-6 py-3">Action</th>
                            <th className="px-6 py-3">Qty</th>
                            <th className="px-6 py-3">Price</th>
                            <th className="px-6 py-3">AI Analysis</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                        {trades.map((trade) => (
                            <tr key={trade.id} className="hover:bg-gray-800/50 transition-colors">
                                <td className="px-6 py-4 text-sm text-gray-300">
                                    {new Date(trade.timestamp).toLocaleTimeString()}
                                </td>
                                <td className="px-6 py-4 text-sm font-medium text-white">{trade.symbol}</td>
                                <td className="px-6 py-4 text-sm">
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${trade.action === 'BUY'
                                        ? 'bg-success/20 text-success'
                                        : 'bg-danger/20 text-danger'
                                        }`}>
                                        {trade.action}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-300">{trade.quantity}</td>
                                <td className="px-6 py-4 text-sm text-gray-300">${trade.price.toFixed(2)}</td>
                                <td
                                    className="px-6 py-4 text-sm text-gray-400 max-w-xs cursor-pointer group relative"
                                    onClick={() => setExpandedId(expandedId === trade.id ? null : trade.id)}
                                >
                                    <div className={`transition-all duration-200 ${expandedId === trade.id ? "whitespace-normal" : "truncate"}`}>
                                        {trade.reason}
                                    </div>
                                    {expandedId !== trade.id && (
                                        <span className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 text-xs text-primary">
                                            Read
                                        </span>
                                    )}
                                </td>
                            </tr>
                        ))}
                        {trades.length === 0 && (
                            <tr>
                                <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                                    No trades executed yet.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default TradeList;
