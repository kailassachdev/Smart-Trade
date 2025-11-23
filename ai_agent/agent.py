import time
import random
import requests

# Configuration
BACKEND_URL = "http://localhost:8000"

class SmartTradeAgent:
    def __init__(self):
        self.running = False
        print("Smart Trade Agent Initialized")

    def run(self):
        self.running = True
        print("Agent loop started...")
        while self.running:
            try:
                # 1. Trigger Trade Simulation (Backend handles Gemini Analysis)
                print("Requesting trade simulation...")
                
                response = requests.post(f"{BACKEND_URL}/simulate-trade")
                if response.status_code == 200:
                    trade = response.json()
                    print(f"Executed Trade: {trade['action']} {trade['quantity']} {trade['symbol']} @ ${trade['price']}")
                    print(f"AI Reasoning: {trade['reason']}")
                
                time.sleep(10) # Trade every 10 seconds for demo
            except Exception as e:
                print(f"Error in agent loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    agent = SmartTradeAgent()
    agent.run()
