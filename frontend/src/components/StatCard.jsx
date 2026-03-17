import React from 'react';

const StatCard = ({ title, value, icon: Icon, trend }) => {
    return (
        <div className="bg-secondary p-6 rounded-2xl">
            <div className="flex items-center justify-between mb-2">
                <h3 className="text-gray-400 text-sm font-medium">{title}</h3>
                {Icon && <Icon className="text-gray-500 w-5 h-5" />}
            </div>
            <div className="flex items-end justify-between mt-4">
                <span className="text-3xl font-semibold text-white tracking-tight">{value}</span>
                {trend && (
                    <span className={`text-sm font-medium ${trend >= 0 ? 'text-success' : 'text-danger'}`}>
                        {trend > 0 ? '+' : ''}{trend}%
                    </span>
                )}
            </div>
        </div>
    );
};

export default StatCard;
