#!/usr/bin/env python3
"""Direct test of DeepSeek API."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_deepseek_direct():
    """Test DeepSeek API directly."""
    try:
        import openai
        from src.config import get_config
        
        config = get_config()
        api_key = config.deepseek_api_key
        
        print(f"Testing with API key: {api_key[:10]}...")
        
        # Try direct initialization
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        
        print("✅ Client initialized successfully")
        
        # Test simple completion
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": "Say hello in a professional way."}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ API call successful: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_deepseek_direct()
