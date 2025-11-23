import os
from dotenv import load_dotenv
import google.generativeai as genai

def test_gemini():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env file or environment variables.")
        print("Please create a .env file in the backend directory with: GEMINI_API_KEY=your_key_here")
        return

    print(f"✅ Found API Key: {api_key[:5]}...{api_key[-5:]}")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("🤖 Sending test prompt to Gemini...")
        response = model.generate_content("Say 'Hello from Gemini!' if you can hear me.")
        print(f"✅ Gemini Response: {response.text}")
        print("\n🎉 Integration Successful! You can now run the backend.")
    except Exception as e:
        print(f"❌ Error connecting to Gemini: {e}")

if __name__ == "__main__":
    test_gemini()
