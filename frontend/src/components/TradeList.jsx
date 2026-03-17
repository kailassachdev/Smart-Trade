import React from 'react';

const TradeList = ({ trades }) => {
    const [expandedId, setExpandedId] = React.useState(null);

    return (
        <div className="bg-secondary rounded-2xl overflow-hidden">
            <div className="p-6 border-b border-primary">
                <h3 className="text-lg font-bold text-white">Recent Activity</h3>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead className="bg-primary/50 text-gray-500 text-xs uppercase tracking-wider font-semibold">
                        <tr>
                            <th className="px-6 py-3">Time</th>
                            <th className="px-6 py-3">Symbol</th>
                            <th className="px-6 py-3">Action</th>
                            <th className="px-6 py-3">Qty</th>
                            <th className="px-6 py-3">Price</th>
                            <th className="px-6 py-3">AI Analysis</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-primary">
                        {trades.map((trade) => (
                            <tr key={trade.id} className="hover:bg-primary/30 transition-colors group">
                                <td className="px-6 py-4 text-sm text-gray-300">
                                    {new Date(trade.timestamp).toLocaleTimeString()}
                                </td>
                                <td className="px-6 py-4 text-sm font-medium text-white group-hover:text-accent transition-colors">{trade.symbol}</td>
                                <td className="px-6 py-4 text-sm">
                                    <span className={`px-2 py-1 rounded-md text-xs font-bold uppercase tracking-wider ${trade.action === 'BUY'
                                        ? 'bg-success/10 text-success'
                                        : 'bg-danger/10 text-danger'
                                        }`}>
                                        {trade.action}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-sm font-medium text-gray-300">{trade.quantity}</td>
                                <td className="px-6 py-4 text-sm font-bold text-white">${trade.price.toFixed(2)}</td>
                                <td
                                    className="px-6 py-4 text-sm text-gray-400 max-w-xs cursor-pointer group/cell relative"
                                    onClick={() => setExpandedId(expandedId === trade.id ? null : trade.id)}
                                >
                                    <div className={`transition-all duration-200 ${expandedId === trade.id ? "whitespace-normal text-gray-300" : "truncate"}`}>
                                        {trade.reason}
                                    </div>
                                    {expandedId !== trade.id && (
                                        <span className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover/cell:opacity-100 text-xs font-bold text-accent bg-secondary pl-2">
                                            READ
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
