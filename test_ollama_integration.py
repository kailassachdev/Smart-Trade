import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from ollama_service import OllamaService

def test_ollama():
    print("Initializing OllamaService...")
    try:
        service = OllamaService(model="deepseek-v3.1:671b-cloud")
        
        print("Testing analyze_market...")
        market_data = {
            "symbol": "AAPL",
            "price": 150.00,
            "trend": "upward",
            "news": "Positive earnings report expected"
        }
        
        analysis = service.analyze_market(market_data)
        print("\n--- AI Analysis ---")
        print(analysis)
        print("-------------------")
        
        if analysis and "Error" not in analysis:
            print("\nSUCCESS: Ollama responded correctly.")
        else:
            print("\nFAILURE: Ollama returned an error or empty response.")
            
    except Exception as e:
        print(f"\nEXCEPTION: {e}")

if __name__ == "__main__":
    test_ollama()
