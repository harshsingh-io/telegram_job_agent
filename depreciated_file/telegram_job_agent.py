import asyncio
import os
from datetime import datetime, timedelta
import pandas as pd
from telethon import TelegramClient
from telethon.tl.types import Message
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
import json
import re
from typing import List, Dict, Tuple
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_agent.log'),
        logging.StreamHandler()
    ]
)

class TelegramJobAgent:
    def __init__(self, config):
        """Initialize the Telegram Job Agent with configuration"""
        self.config = config
        self.telegram_client = None
        self.sheets_client = None
        self.sheet = None
        self.genai_model = None
        
        # Telegram groups to monitor
        self.groups = [
            'https://t.me/os_Community',
            'https://t.me/infytq_2022',
            'https://t.me/internfreak',
            'https://t.me/OceanOfJobs',
            'https://t.me/jobs_and_internships_updates',
            'https://t.me/gocareers',
            'https://t.me/vijaykushal',
            'https://t.me/dot_aware',
            'https://t.me/CodingBugs',
            'https://t.me/goyalarsh',
            'https://t.me/findITJobsLink',
            'https://t.me/arunchauhanofficial',
            'https://t.me/TorchBearerr',
            'https://t.me/offcampus_phodenge'
        ]
        
        # Keywords to exclude (experienced positions)
        self.exclude_keywords = [
            r'\b[3-9]\+?\s*years?\b',
            r'\b[1-9]\d+\s*years?\b',
            r'\bsenior\b',
            r'\blead\b',
            r'\bmanager\b',
            r'\bexperienced\b',
            r'\bexpert\b',
            r'\b[3-9]-[0-9]+\s*years?\b',
            r'\bsr\.\b',
            r'\bprincipal\b'
        ]
        
        # Keywords to include (fresher positions)
        self.include_keywords = [
            r'\bfresher\b',
            r'\bfreshman\b',
            r'\b2025\s*batch\b',
            r'\b2024\s*batch\b',
            r'\b0-[12]\s*years?\b',
            r'\b1-2\s*years?\b',
            r'\bentry\s*level\b',
            r'\bcampus\b',
            r'\bgraduate\b',
            r'\bnew\s*grad\b',
            r'\bintern\b',
            r'\btrainee\b'
        ]
    
    async def setup(self):
        """Setup all necessary clients and connections"""
        # Setup Telegram client
        self.telegram_client = TelegramClient(
            'job_agent_session',
            self.config['telegram_api_id'],
            self.config['telegram_api_hash']
        )
        
        # Setup Google Sheets
        self._setup_sheets()
        
        # Setup Gemini AI
        self._setup_gemini()
        
        # Connect to Telegram
        await self.telegram_client.start(phone=self.config['phone_number'])
        logging.info("Successfully connected to Telegram")
    
    def _setup_sheets(self):
        """Setup Google Sheets connection"""
        try:
            # Use service account credentials
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            creds = Credentials.from_service_account_file(
                self.config['google_sheets_credentials'],
                scopes=scope
            )
            
            self.sheets_client = gspread.authorize(creds)
            self.sheet = self.sheets_client.open_by_url(
                'https://docs.google.com/spreadsheets/d/1shH8hGgA5HSGIZF6eQl0k00MCobBsPqVtjaUVp8XY9E'
            )
            
            # Ensure both worksheets exist
            worksheets = [ws.title for ws in self.sheet.worksheets()]
            
            if 'Relevant Jobs' not in worksheets:
                self.sheet.add_worksheet(title='Relevant Jobs', rows=1000, cols=10)
                self._setup_sheet_headers('Relevant Jobs')
            
            if 'Uncategorized' not in worksheets:
                self.sheet.add_worksheet(title='Uncategorized', rows=1000, cols=10)
                self._setup_sheet_headers('Uncategorized')
                
            logging.info("Google Sheets setup complete")
            
        except Exception as e:
            logging.error(f"Error setting up Google Sheets: {e}")
            raise
    
    def _setup_sheet_headers(self, sheet_name):
        """Setup headers for a worksheet"""
        worksheet = self.sheet.worksheet(sheet_name)
        headers = [
            'Date Added',
            'Message Date',
            'Source Group',
            'Full Message',
            'Company',
            'Position',
            'Experience',
            'Location',
            'Skills',
            'Apply Link'
        ]
        worksheet.append_row(headers)
    
    def _setup_gemini(self):
        """Setup Gemini AI for message analysis"""
        genai.configure(api_key=self.config['gemini_api_key'])
        # Use gemini-1.5-flash for faster, cheaper processing
        # Alternative: 'gemini-1.5-pro' for more accuracy
        self.genai_model = genai.GenerativeModel('gemini-1.5-flash')
        logging.info("Gemini AI setup complete")
    
    async def fetch_messages_from_group(self, group_url: str) -> List[Dict]:
        """Fetch messages from a single Telegram group"""
        messages = []
        try:
            # Get the group entity
            group = await self.telegram_client.get_entity(group_url)
            group_name = getattr(group, 'title', group_url)
            
            # Calculate date 7 days ago
            date_limit = datetime.now() - timedelta(days=7)
            
            # Fetch messages
            async for message in self.telegram_client.iter_messages(
                group,
                limit=500,  # Adjust based on group activity
                offset_date=datetime.now()
            ):
                if isinstance(message, Message) and message.date.replace(tzinfo=None) < date_limit:
                    break
                
                if message.text:
                    messages.append({
                        'date': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                        'group': group_name,
                        'text': message.text,
                        'id': message.id
                    })
            
            logging.info(f"Fetched {len(messages)} messages from {group_name}")
            
        except Exception as e:
            logging.error(f"Error fetching from {group_url}: {e}")
        
        return messages
    
    async def fetch_all_messages(self) -> List[Dict]:
        """Fetch messages from all configured groups"""
        all_messages = []
        
        for group in self.groups:
            messages = await self.fetch_messages_from_group(group)
            all_messages.extend(messages)
            await asyncio.sleep(2)  # Rate limiting
        
        logging.info(f"Total messages fetched: {len(all_messages)}")
        return all_messages
    
    def is_relevant_job(self, text: str) -> bool:
        """Check if a message is relevant based on keywords"""
        text_lower = text.lower()
        
        # Check exclude keywords first
        for pattern in self.exclude_keywords:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return False
        
        # Check include keywords
        for pattern in self.include_keywords:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        # Additional check for job-related content
        job_indicators = ['hiring', 'vacancy', 'opening', 'position', 'requirement', 'job', 'opportunity']
        return any(indicator in text_lower for indicator in job_indicators)
    
    async def analyze_job_with_ai(self, message: Dict) -> Dict:
        """Use Gemini AI to extract job details from message"""
        prompt = f"""
        Analyze this job posting and extract the following information.
        If any information is not found, return 'Not specified'.
        
        Message: {message['text']}
        
        Extract:
        1. Company Name:
        2. Position/Role:
        3. Experience Required:
        4. Location:
        5. Key Skills (comma separated):
        6. Application Link/Email:
        
        Return in JSON format.
        """
        
        try:
            response = await asyncio.to_thread(
                self.genai_model.generate_content, prompt
            )
            
            # Parse the response
            result_text = response.text
            
            # Try to extract JSON from response
            try:
                # Find JSON in response
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    job_details = json.loads(json_match.group())
                else:
                    # Fallback parsing
                    job_details = self._parse_structured_response(result_text)
            except:
                job_details = self._parse_structured_response(result_text)
            
            return {
                'company': job_details.get('company', 'Not specified'),
                'position': job_details.get('position', 'Not specified'),
                'experience': job_details.get('experience', 'Not specified'),
                'location': job_details.get('location', 'Not specified'),
                'skills': job_details.get('skills', 'Not specified'),
                'apply_link': job_details.get('apply_link', 'Not specified')
            }
            
        except Exception as e:
            logging.error(f"Error analyzing with AI: {e}")
            return {
                'company': 'Error parsing',
                'position': 'Error parsing',
                'experience': 'Error parsing',
                'location': 'Error parsing',
                'skills': 'Error parsing',
                'apply_link': 'Error parsing'
            }
    
    def _parse_structured_response(self, text: str) -> Dict:
        """Fallback parser for structured text response"""
        result = {}
        
        patterns = {
            'company': r'Company\s*(?:Name)?:\s*(.+?)(?:\n|$)',
            'position': r'Position(?:/Role)?:\s*(.+?)(?:\n|$)',
            'experience': r'Experience\s*(?:Required)?:\s*(.+?)(?:\n|$)',
            'location': r'Location:\s*(.+?)(?:\n|$)',
            'skills': r'(?:Key\s*)?Skills.*?:\s*(.+?)(?:\n|$)',
            'apply_link': r'Application\s*(?:Link|Email).*?:\s*(.+?)(?:\n|$)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            result[key] = match.group(1).strip() if match else 'Not specified'
        
        return result
    
    async def process_messages(self, messages: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Process messages and categorize them"""
        relevant_jobs = []
        uncategorized = []
        
        for message in messages:
            if self.is_relevant_job(message['text']):
                # Analyze with AI
                job_details = await self.analyze_job_with_ai(message)
                
                relevant_jobs.append({
                    'date_added': datetime.now().strftime('%Y-%m-%d'),
                    'message_date': message['date'],
                    'source_group': message['group'],
                    'full_message': message['text'],
                    **job_details
                })
            else:
                uncategorized.append({
                    'date_added': datetime.now().strftime('%Y-%m-%d'),
                    'message_date': message['date'],
                    'source_group': message['group'],
                    'full_message': message['text'],
                    'company': '',
                    'position': '',
                    'experience': '',
                    'location': '',
                    'skills': '',
                    'apply_link': ''
                })
            
            # Rate limiting for AI calls
            await asyncio.sleep(1)
        
        logging.info(f"Processed: {len(relevant_jobs)} relevant, {len(uncategorized)} uncategorized")
        return relevant_jobs, uncategorized
    
    def update_google_sheet(self, relevant_jobs: List[Dict], uncategorized: List[Dict]):
        """Update Google Sheets with processed data"""
        try:
            # Update Relevant Jobs sheet
            if relevant_jobs:
                relevant_sheet = self.sheet.worksheet('Relevant Jobs')
                
                # Prepare rows
                rows = []
                for job in relevant_jobs:
                    rows.append([
                        job['date_added'],
                        job['message_date'],
                        job['source_group'],
                        job['full_message'][:5000],  # Limit message length
                        job['company'],
                        job['position'],
                        job['experience'],
                        job['location'],
                        job['skills'],
                        job['apply_link']
                    ])
                
                # Append all rows at once
                relevant_sheet.append_rows(rows)
                logging.info(f"Added {len(rows)} relevant jobs to sheet")
            
            # Update Uncategorized sheet
            if uncategorized:
                uncat_sheet = self.sheet.worksheet('Uncategorized')
                
                # Prepare rows
                rows = []
                for msg in uncategorized:
                    rows.append([
                        msg['date_added'],
                        msg['message_date'],
                        msg['source_group'],
                        msg['full_message'][:5000],  # Limit message length
                        '', '', '', '', '', ''  # Empty job details
                    ])
                
                # Append all rows at once
                uncat_sheet.append_rows(rows)
                logging.info(f"Added {len(rows)} uncategorized messages to sheet")
                
        except Exception as e:
            logging.error(f"Error updating Google Sheets: {e}")
    
    async def run(self):
        """Main execution method"""
        try:
            logging.info("Starting Telegram Job Agent...")
            
            # Setup connections
            await self.setup()
            
            # Fetch messages
            logging.info("Fetching messages from all groups...")
            messages = await self.fetch_all_messages()
            
            # Process messages
            logging.info("Processing messages with AI...")
            relevant_jobs, uncategorized = await self.process_messages(messages)
            
            # Update Google Sheets
            logging.info("Updating Google Sheets...")
            self.update_google_sheet(relevant_jobs, uncategorized)
            
            logging.info("Job Agent completed successfully!")
            
        except Exception as e:
            logging.error(f"Error in main execution: {e}")
            raise
        finally:
            if self.telegram_client:
                await self.telegram_client.disconnect()

# Configuration template
config_template = {
    "telegram_api_id": "YOUR_API_ID",
    "telegram_api_hash": "YOUR_API_HASH",
    "phone_number": "+91XXXXXXXXXX",
    "gemini_api_key": "YOUR_GEMINI_API_KEY",
    "google_sheets_credentials": "path/to/credentials.json"
}

async def main():
    """Main entry point"""
    # Load configuration
    # For production, load from environment variables or config file
    config = {
        "telegram_api_id": int(os.getenv("TELEGRAM_API_ID", "0")),
        "telegram_api_hash": os.getenv("TELEGRAM_API_HASH", ""),
        "phone_number": os.getenv("PHONE_NUMBER", ""),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
        "google_sheets_credentials": os.getenv("GOOGLE_SHEETS_CREDS", "credentials.json")
    }
    
    # Create and run agent
    agent = TelegramJobAgent(config)
    await agent.run()

if __name__ == "__main__":
    # Save config template for reference
    with open('config_template.json', 'w') as f:
        json.dump(config_template, f, indent=2)
    
    # Run the agent
    asyncio.run(main())