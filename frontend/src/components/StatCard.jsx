import React from 'react';

const StatCard = ({ title, value, icon: Icon, trend }) => {
    return (
        <div className="bg-secondary p-6 rounded-xl shadow-lg border border-gray-700">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-gray-400 text-sm font-medium">{title}</h3>
                {Icon && <Icon className="text-accent w-5 h-5" />}
            </div>
            <div className="flex items-end justify-between">
                <span className="text-2xl font-bold text-white">{value}</span>
                {trend && (
                    <span className={`text-sm ${trend >= 0 ? 'text-success' : 'text-danger'}`}>
                        {trend > 0 ? '+' : ''}{trend}%
                    </span>
                )}
            </div>
        </div>
    );
};

export default StatCard;
