import os
try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None

class StrategyRAG:
    def __init__(self):
        self.collection = None
        if chromadb:
            self.client = chromadb.Client()
            self.collection = self.client.create_collection(name="trading_strategies")
        else:
            print("ChromaDB not found. RAG will be mocked.")

    def add_documents(self, documents, ids):
        if self.collection:
            self.collection.add(documents=documents, ids=ids)
            print(f"Added {len(documents)} documents to RAG.")

    def query(self, query_text, n_results=1):
        if self.collection:
            results = self.collection.query(query_texts=[query_text], n_results=n_results)
            return results['documents'][0] if results['documents'] else []
        else:
            # Mock response
            return ["Strategy: Buy when price is above 50-day moving average and RSI < 30."]

# Example usage
if __name__ == "__main__":
    rag = StrategyRAG()
    rag.add_documents(
        ["Momentum Strategy: Buy when RSI < 30 and Trend is UP.", "Mean Reversion: Sell when Price > 200 SMA."],
        ["doc1", "doc2"]
    )
    print(rag.query("RSI strategy"))
