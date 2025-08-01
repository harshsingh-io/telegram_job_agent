#!/usr/bin/env python3
"""
Quick script to check which Gemini models are available with your API key
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def check_gemini_models():
    """List all available Gemini models"""
    api_key = os.getenv("GEMINI_API_KEY", "")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env file")
        return
    
    genai.configure(api_key=api_key)
    
    print("🤖 Available Gemini Models:\n")
    print("-" * 60)
    
    content_models = []
    
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            content_models.append(model.name)
            print(f"✅ {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description[:100]}...")
            print(f"   Input Token Limit: {model.input_token_limit}")
            print(f"   Output Token Limit: {model.output_token_limit}")
            print()
    
    print("\n📝 Recommended models for job parsing:")
    print("-" * 60)
    
    if 'models/gemini-1.5-flash' in content_models:
        print("1. gemini-1.5-flash (RECOMMENDED)")
        print("   - Fastest and most cost-effective")
        print("   - Good for high-volume processing")
        print("   - Perfect for job message parsing")
    
    if 'models/gemini-1.5-pro' in content_models:
        print("\n2. gemini-1.5-pro")
        print("   - More accurate but slower")
        print("   - Better for complex parsing")
        print("   - Use if flash model misses details")
    
    # Test the recommended model
    print("\n🧪 Testing gemini-1.5-flash...")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'Hello, Job Agent!'")
        print(f"✅ Test successful! Response: {response.text.strip()}")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    check_gemini_models()
