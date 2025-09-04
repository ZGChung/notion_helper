#!/usr/bin/env python3
"""Test script to isolate email generation with DeepSeek."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config
from src.todo_parser import TodoParser
from src.email_generator import EmailGenerator

def test_email_with_deepseek():
    """Test email generation with DeepSeek step by step."""
    try:
        print("🔧 Testing DeepSeek integration...")
        
        # Test config
        config = get_config()
        print(f"✅ DeepSeek API key configured: {config.deepseek_api_key[:10]}...")
        
        # Test email generator initialization
        print("\n📧 Initializing EmailGenerator...")
        email_gen = EmailGenerator()
        
        if email_gen.deepseek_client:
            print("✅ DeepSeek client initialized successfully")
        else:
            print("⚠️  DeepSeek client not initialized")
        
        # Test with minimal data to avoid Notion timeout
        print("\n📝 Testing with minimal data...")
        
        # Create mock completed tasks
        from src.todo_parser import TodoItem
        from datetime import datetime
        
        mock_todos = {
            "adr": [
                TodoItem("Test task 1", True, datetime.now(), "adr"),
                TodoItem("Test task 2", True, datetime.now(), "adr"),
            ]
        }
        
        week_start = datetime.now()
        week_end = datetime.now()
        
        print("🎯 Generating email with mock data...")
        email_content = email_gen.generate_weekly_email(
            mock_todos, week_start, week_end
        )
        
        print("✅ Email generated successfully!")
        print(f"Subject: {email_content['subject']}")
        print(f"Body length: {len(email_content['body'])} characters")
        
        # Test AI polishing directly
        print("\n🤖 Testing AI polishing directly...")
        test_content = "This is a test email content for polishing."
        polished = email_gen._polish_email_with_ai(test_content)
        
        if polished:
            print("✅ AI polishing successful!")
            print(f"Original length: {len(test_content)}")
            print(f"Polished length: {len(polished)}")
        else:
            print("⚠️  AI polishing failed or not available")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email_with_deepseek()
