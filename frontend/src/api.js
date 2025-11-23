const API_URL = "http://localhost:8000";

export const fetchPortfolio = async () => {
    try {
        const response = await fetch(`${API_URL}/portfolio`);
        if (!response.ok) throw new Error("Failed to fetch portfolio");
        return await response.json();
    } catch (error) {
        console.error(error);
        return null;
    }
};

export const fetchTradeLogs = async () => {
    try {
        const response = await fetch(`${API_URL}/trade-logs`);
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
            headers: {
                'Content-Type': 'application/json',
            },
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
        const response = await fetch(`${API_URL}/start-agent`, { method: 'POST' });
        if (!response.ok) throw new Error("Failed to start agent");
        return await response.json();
    } catch (error) {
        console.error(error);
        return { status: "Error starting agent" };
    }
};

export const stopAgent = async () => {
    try {
        const response = await fetch(`${API_URL}/stop-agent`, { method: 'POST' });
        if (!response.ok) throw new Error("Failed to stop agent");
        return await response.json();
    } catch (error) {
        console.error(error);
        return { status: "Error stopping agent" };
    }
};
