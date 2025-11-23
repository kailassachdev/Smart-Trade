import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def analyze_market(self, market_data: dict) -> str:
        if not self.model:
            return "Error: Gemini API key not configured. Please set GEMINI_API_KEY in .env file."

        prompt = f"""
        You are an expert financial analyst AI. Analyze the following market data and provide a concise trading insight and recommendation.
        
        Market Data:
        {market_data}
        
        Provide your response in a clear, professional tone. Focus on key trends and potential risks/opportunities.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating analysis: {str(e)}"
