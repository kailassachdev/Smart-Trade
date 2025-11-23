import ollama

class OllamaService:
    def __init__(self, model="deepseek-v3.1:671b-cloud"):
        self.model = model
        try:
            # Check if model exists, if not, warn user
            ollama.show(self.model)
        except Exception as e:
            print(f"Warning: Model '{self.model}' not found. Please run 'ollama pull {self.model}'")

    def analyze_market(self, market_data: dict) -> str:
        prompt = f"""
        You are an expert financial analyst AI. Analyze the following market data and provide a concise trading insight and recommendation.
        
        Market Data:
        {market_data}
        
        Provide your response in a clear, professional tone. Focus on key trends and potential risks/opportunities.
        Keep it under 3 sentences.
        """
        
        try:
            response = ollama.chat(model=self.model, messages=[
                {
                    'role': 'user',
                    'content': prompt,
                },
            ])
            return response['message']['content']
        except Exception as e:
            return f"Error generating analysis: {str(e)}. Ensure Ollama is running."
