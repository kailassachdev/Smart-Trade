const API_URL = "http://localhost:8000";

const getHeaders = () => {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
};

export const fetchPortfolio = async () => {
    try {
        const response = await fetch(`${API_URL}/portfolio`, {
            headers: getHeaders()
        });
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('token');
                window.location.reload();
            }
            throw new Error("Failed to fetch portfolio");
        }
        return await response.json();
    } catch (error) {
        console.error(error);
        return null;
    }
};

export const fetchTradeLogs = async () => {
    try {
        const response = await fetch(`${API_URL}/trade-logs`, {
            headers: getHeaders()
        });
        if (!response.ok) throw new Error("Failed to fetch trade logs");
        return await response.json();
    } catch (error) {
        console.error(error);
        return [];
    }
};

export const fetchAIAnalysis = async (marketData) => {
    try {
        const response = await fetch(`${API_URL}/api/analyze`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(marketData),
        });
        if (!response.ok) throw new Error("Failed to fetch AI analysis");
        return await response.json();
    } catch (error) {
        console.error(error);
        return { analysis: "Unable to generate analysis at this time." };
    }
};
export const startAgent = async () => {
    try {
        const response = await fetch(`${API_URL}/start-agent`, { 
            method: 'POST',
            headers: getHeaders()
        });
        if (!response.ok) throw new Error("Failed to start agent");
        return await response.json();
    } catch (error) {
        console.error(error);
        return { status: "Error starting agent" };
    }
};

export const stopAgent = async () => {
    try {
        const response = await fetch(`${API_URL}/stop-agent`, { 
            method: 'POST',
            headers: getHeaders()
        });
        if (!response.ok) throw new Error("Failed to stop agent");
        return await response.json();
    } catch (error) {
        console.error(error);
        return { status: "Error stopping agent" };
    }
};

export const depositWallet = async (amount) => {
    try {
        const response = await fetch(`${API_URL}/wallet/deposit`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ amount })
        });
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || "Failed to deposit");
        }
        return await response.json();
    } catch (error) {
        throw error;
    }
};

export const withdrawWallet = async (amount) => {
    try {
        const response = await fetch(`${API_URL}/wallet/withdraw`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ amount })
        });
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || "Failed to withdraw");
        }
        return await response.json();
    } catch (error) {
        throw error;
    }
};

export const executeTrade = async (action, symbol, quantity) => {
    try {
        const endpoint = action === 'BUY' ? '/trade/buy' : '/trade/sell';
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ symbol, quantity })
        });
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || `Failed to ${action}`);
        }
        return await response.json();
    } catch (error) {
        throw error;
    }
};

export const fetchWalletHistory = async () => {
    try {
        const response = await fetch(`${API_URL}/wallet/history`, {
            headers: getHeaders()
        });
        if (!response.ok) throw new Error("Failed to fetch wallet history");
        return await response.json();
    } catch (error) {
        console.error(error);
        return [];
    }
};

export const fetchStockHistory = async (symbol, period = '1mo', interval = '1d') => {
    try {
        const response = await fetch(`${API_URL}/stock/${symbol}/history?period=${period}&interval=${interval}`, {
            headers: getHeaders()
        });
        if (!response.ok) throw new Error(`Failed to fetch stock history for ${symbol}`);
        return await response.json();
    } catch (error) {
        console.error(error);
        return [];
    }
};
