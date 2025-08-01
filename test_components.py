#!/usr/bin/env python3
"""
Test script to verify all components are working
Run this before the main agent to ensure setup is correct
"""

import asyncio
import os
from datetime import datetime, timedelta
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
from telethon import TelegramClient
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class ComponentTester:
    def __init__(self):
        self.results = {}
        
    async def test_telegram_connection(self):
        """Test Telegram API connection"""
        print("\n1. Testing Telegram Connection...")
        try:
            api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
            api_hash = os.getenv("TELEGRAM_API_HASH", "")
            phone = os.getenv("PHONE_NUMBER", "")
            
            if not all([api_id, api_hash, phone]):
                raise ValueError("Missing Telegram credentials in .env file")
            
            client = TelegramClient('test_session', api_id, api_hash)
            await client.connect()
            
            if not await client.is_user_authorized():
                print(f"📱 Sending code to {phone}...")
                await client.send_code_request(phone)
                code = input("Enter the code you received: ")
                await client.sign_in(phone, code)
            
            me = await client.get_me()
            print(f"✅ Telegram connected! Logged in as: {me.first_name} {me.last_name or ''}")
            
            # Test fetching from a small public channel
            print("\nTesting message fetch...")
            test_channel = "https://t.me/telegram"
            messages = []
            async for message in client.iter_messages(test_channel, limit=5):
                if message.text:
                    messages.append(message.text[:50] + "...")
            
            print(f"✅ Successfully fetched {len(messages)} test messages")
            
            await client.disconnect()
            self.results['telegram'] = 'PASSED'
            
        except Exception as e:
            print(f"❌ Telegram test failed: {e}")
            self.results['telegram'] = f'FAILED: {str(e)}'
    
    def test_gemini_ai(self):
        """Test Gemini AI connection"""
        print("\n2. Testing Gemini AI...")
        try:
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                raise ValueError("Missing GEMINI_API_KEY in .env file")
            
            genai.configure(api_key=api_key)
            
            # List available models first
            print("Available models:")
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    print(f"  - {model.name}")
            
            # Use gemini-1.5-flash (or gemini-1.5-pro for better accuracy)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Test with a sample job message
            test_message = """
            Urgent Hiring! Software Developer - Fresher
            Company: TechCorp India
            Location: Bangalore
            Experience: 0-1 years
            Skills: Python, JavaScript, SQL
            Apply at: careers@techcorp.com
            """
            
            prompt = f"Extract company name from this job posting: {test_message}. Reply with just the company name."
            
            response = model.generate_content(prompt)
            result = response.text.strip()
            
            print(f"✅ Gemini AI working! Test response: {result}")
            self.results['gemini'] = 'PASSED'
            
        except Exception as e:
            print(f"❌ Gemini AI test failed: {e}")
            self.results['gemini'] = f'FAILED: {str(e)}'
    
    def test_google_sheets(self):
        """Test Google Sheets connection"""
        print("\n3. Testing Google Sheets...")
        try:
            creds_file = os.getenv("GOOGLE_SHEETS_CREDS", "credentials.json")
            
            if not os.path.exists(creds_file):
                raise ValueError(f"Credentials file not found: {creds_file}")
            
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            creds = Credentials.from_service_account_file(creds_file, scopes=scope)
            client = gspread.authorize(creds)
            
            # Try to open the sheet
            sheet = client.open_by_url(
                'https://docs.google.com/spreadsheets/d/1shH8hGgA5HSGIZF6eQl0k00MCobBsPqVtjaUVp8XY9E'
            )
            
            print(f"✅ Connected to Google Sheet: {sheet.title}")
            
            # List worksheets
            worksheets = [ws.title for ws in sheet.worksheets()]
            print(f"   Found worksheets: {', '.join(worksheets)}")
            
            # Test write (add a test row)
            test_sheet = sheet.worksheet(worksheets[0])
            test_row = [f"Test at {datetime.now()}", "This is a test", "Will be deleted"]
            test_sheet.append_row(test_row)
            print("✅ Successfully wrote test data to sheet")
            
            self.results['sheets'] = 'PASSED'
            
        except Exception as e:
            print(f"❌ Google Sheets test failed: {e}")
            self.results['sheets'] = f'FAILED: {str(e)}'
    
    def test_keyword_matching(self):
        """Test keyword matching logic"""
        print("\n4. Testing Keyword Matching...")
        
        test_cases = [
            ("Hiring freshers 2025 batch for SDE role", True, "Should match: fresher + 2025 batch"),
            ("Senior Developer with 5+ years experience", False, "Should reject: 5+ years"),
            ("Entry level position, 0-1 year experience welcome", True, "Should match: entry level + 0-1 year"),
            ("Experienced Java Developer needed urgently", False, "Should reject: experienced"),
            ("Campus placement drive for 2025 graduates", True, "Should match: campus + 2025"),
            ("Team Lead position, 8 years required", False, "Should reject: 8 years + lead"),
        ]
        
        import re
        
        exclude_keywords = [
            r'\b[3-9]\+?\s*years?\b',
            r'\b[1-9]\d+\s*years?\b',
            r'\bsenior\b',
            r'\blead\b',
            r'\bexperienced\b',
        ]
        
        include_keywords = [
            r'\bfresher\b',
            r'\b2025\s*batch\b',
            r'\b0-[12]\s*years?\b',
            r'\bentry\s*level\b',
            r'\bcampus\b',
        ]
        
        all_correct = True
        
        for text, expected, reason in test_cases:
            text_lower = text.lower()
            
            # Check exclude first
            excluded = any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in exclude_keywords)
            
            # Then check include
            included = any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in include_keywords)
            
            result = not excluded and included
            
            if result == expected:
                print(f"✅ {reason}")
            else:
                print(f"❌ {reason} - Got {result}, expected {expected}")
                all_correct = False
        
        self.results['keywords'] = 'PASSED' if all_correct else 'FAILED'
    
    def show_summary(self):
        """Show test summary"""
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        
        for component, status in self.results.items():
            emoji = "✅" if status == "PASSED" else "❌"
            print(f"{emoji} {component.upper()}: {status}")
        
        all_passed = all(status == "PASSED" for status in self.results.values())
        
        if all_passed:
            print("\n🎉 All tests passed! You're ready to run the job agent.")
        else:
            print("\n⚠️  Some tests failed. Please fix the issues before running the agent.")
            print("\nTroubleshooting tips:")
            if 'telegram' in self.results and 'FAILED' in self.results['telegram']:
                print("- Check your Telegram API credentials")
                print("- Ensure your phone number is in international format (+91...)")
            if 'gemini' in self.results and 'FAILED' in self.results['gemini']:
                print("- Verify your Gemini API key at https://makersuite.google.com/app/apikey")
            if 'sheets' in self.results and 'FAILED' in self.results['sheets']:
                print("- Check if credentials.json exists")
                print("- Ensure the service account has access to your Google Sheet")

async def main():
    print("""
    ╔══════════════════════════════════════╗
    ║   Telegram Job Agent Test Suite      ║
    ╠══════════════════════════════════════╣
    ║  This will test all components       ║
    ║  Make sure .env file is configured   ║
    ╚══════════════════════════════════════╝
    """)
    
    tester = ComponentTester()
    
    # Run tests
    await tester.test_telegram_connection()
    tester.test_gemini_ai()
    tester.test_google_sheets()
    tester.test_keyword_matching()
    
    # Show summary
    tester.show_summary()

if __name__ == "__main__":
    asyncio.run(main())