import asyncio
import os
from datetime import datetime, timedelta
import pandas as pd
from telethon import TelegramClient
from telethon.tl.types import Message
import gspread
from google.oauth2.service_account import Credentials
import re
from typing import List, Dict, Set
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_agent_simple.log'),
        logging.StreamHandler()
    ]
)

class SimpleTelegramJobAgent:
    def __init__(self):
        """Initialize the Simple Telegram Job Agent"""
        self.telegram_client = None
        self.sheets_client = None
        self.sheet = None
        self.processed_messages = set()  # For duplicate detection
        
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
        self.exclude_patterns = [
            r'\b[3-9]\+?\s*years?\b',
            r'\b[1-9]\d+\s*years?\b',
            r'\bsenior\b',
            r'\blead\b',
            r'\bmanager\b',
            r'\bexperienced\b',
            r'\bexpert\b',
            r'\b[3-9]-[0-9]+\s*years?\b',
            r'\bsr\.\b',
            r'\bprincipal\b',
            r'\barchitect\b',
        ]
        
        # Keywords to include (fresher positions)
        self.include_patterns = [
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
            r'\btrainee\b',
            r'\b0\s*year\b',
            r'\b0\s*to\s*[12]\s*years?\b',
        ]
        
        # Job indicators
        self.job_indicators = [
            'hiring', 'vacancy', 'opening', 'position', 'requirement', 
            'job', 'opportunity', 'recruitment', 'walk-in', 'walkin',
            'apply', 'career', 'placement', 'interview'
        ]
    
    async def setup(self):
        """Setup all necessary clients and connections"""
        # Setup Telegram client
        api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
        api_hash = os.getenv("TELEGRAM_API_HASH", "")
        phone = os.getenv("PHONE_NUMBER", "")
        
        self.telegram_client = TelegramClient(
            'job_agent_simple_session',
            api_id,
            api_hash
        )
        
        # Setup Google Sheets
        self._setup_sheets()
        
        # Connect to Telegram
        await self.telegram_client.start(phone=phone)
        logging.info("Successfully connected to Telegram")
        
        # Load previously processed message IDs
        self._load_processed_messages()
    
    def _setup_sheets(self):
        """Setup Google Sheets connection"""
        try:
            creds_file = os.getenv("GOOGLE_SHEETS_CREDS", "credentials.json")
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            creds = Credentials.from_service_account_file(creds_file, scopes=scope)
            
            self.sheets_client = gspread.authorize(creds)
            self.sheet = self.sheets_client.open_by_url(
                'https://docs.google.com/spreadsheets/d/1shH8hGgA5HSGIZF6eQl0k00MCobBsPqVtjaUVp8XY9E'
            )
            
            # Ensure both worksheets exist with simple headers
            worksheets = [ws.title for ws in self.sheet.worksheets()]
            
            headers = [
                'Date Added',
                'Message Date',
                'Message Time',
                'Message ID',
                'Source Group',
                'Full Message',
                'Extracted Links',
                'Category'
            ]
            
            if 'Relevant Jobs' not in worksheets:
                ws = self.sheet.add_worksheet(title='Relevant Jobs', rows=10000, cols=10)
                ws.append_row(headers)
            
            if 'Uncategorized' not in worksheets:
                ws = self.sheet.add_worksheet(title='Uncategorized', rows=10000, cols=10)
                ws.append_row(headers)
                
            logging.info("Google Sheets setup complete")
            
        except Exception as e:
            logging.error(f"Error setting up Google Sheets: {e}")
            raise
    
    def _load_processed_messages(self):
        """Load already processed message IDs to avoid duplicates"""
        try:
            # Get all message IDs from both sheets
            for sheet_name in ['Relevant Jobs', 'Uncategorized']:
                try:
                    ws = self.sheet.worksheet(sheet_name)
                    # Get all values from the Message ID column (column D, index 3)
                    all_values = ws.get_all_values()
                    
                    # Skip header and extract message IDs
                    for row in all_values[1:]:  # Skip header
                        if len(row) > 3 and row[3]:  # Message ID is in column 4 (index 3)
                            self.processed_messages.add(row[3])
                            
                except Exception as e:
                    logging.warning(f"Could not load from {sheet_name}: {e}")
            
            logging.info(f"Loaded {len(self.processed_messages)} previously processed messages")
            
        except Exception as e:
            logging.warning(f"Could not load processed messages: {e}")
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract all URLs from text"""
        # Improved URL regex pattern
        url_patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            r'www\.[^\s<>"{}|\\^`\[\]]+',
            r'bit\.ly/[^\s]+',
            r't\.me/[^\s]+',
            r'linkedin\.com/[^\s]+',
            r'forms\.gle/[^\s]+',
        ]
        
        urls = []
        for pattern in url_patterns:
            found_urls = re.findall(pattern, text, re.IGNORECASE)
            urls.extend(found_urls)
        
        # Clean up URLs
        cleaned_urls = []
        for url in urls:
            # Remove trailing punctuation
            url = re.sub(r'[.,;:!?\)]+$', '', url)
            if url:
                cleaned_urls.append(url)
        
        return list(set(cleaned_urls))  # Remove duplicates
    
    def is_relevant_job(self, text: str) -> bool:
        """Check if a message is relevant based on keywords"""
        text_lower = text.lower()
        
        # First check if it's even job-related
        has_job_indicator = any(indicator in text_lower for indicator in self.job_indicators)
        if not has_job_indicator:
            return False
        
        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return False
        
        # Check include patterns
        for pattern in self.include_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        # If it has job indicators but no specific patterns, consider it uncategorized
        return False
    
    def create_unique_message_id(self, group: str, message_id: int, date: str) -> str:
        """Create a unique identifier for a message"""
        # Combine group name, message ID, and date for uniqueness
        group_short = group.split('/')[-1]  # Get group username
        return f"{group_short}_{message_id}_{date}"
    
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
            message_count = 0
            async for message in self.telegram_client.iter_messages(
                group,
                limit=1000,  # Increased limit
                offset_date=datetime.now()
            ):
                if isinstance(message, Message) and message.date.replace(tzinfo=None) < date_limit:
                    break
                
                if message.text and len(message.text) > 20:  # Skip very short messages
                    # Create unique ID
                    unique_id = self.create_unique_message_id(
                        group_url, 
                        message.id,
                        message.date.strftime('%Y%m%d')
                    )
                    
                    # Skip if already processed
                    if unique_id in self.processed_messages:
                        continue
                    
                    messages.append({
                        'unique_id': unique_id,
                        'message_id': message.id,
                        'date': message.date.strftime('%Y-%m-%d'),
                        'time': message.date.strftime('%H:%M:%S'),
                        'datetime': message.date,
                        'group': group_name,
                        'text': message.text,
                        'urls': self.extract_urls(message.text)
                    })
                    message_count += 1
            
            logging.info(f"Fetched {message_count} new messages from {group_name}")
            
        except Exception as e:
            logging.error(f"Error fetching from {group_url}: {e}")
        
        return messages
    
    async def fetch_all_messages(self) -> List[Dict]:
        """Fetch messages from all configured groups"""
        all_messages = []
        
        for i, group in enumerate(self.groups):
            logging.info(f"Processing group {i+1}/{len(self.groups)}: {group}")
            messages = await self.fetch_messages_from_group(group)
            all_messages.extend(messages)
            
            # Rate limiting
            if i < len(self.groups) - 1:
                await asyncio.sleep(3)
        
        logging.info(f"Total new messages fetched: {len(all_messages)}")
        return all_messages
    
    def categorize_messages(self, messages: List[Dict]) -> tuple:
        """Categorize messages into relevant and uncategorized"""
        relevant_jobs = []
        uncategorized = []
        
        for message in messages:
            is_relevant = self.is_relevant_job(message['text'])
            
            # Prepare row data
            row_data = {
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'message_date': message['date'],
                'message_time': message['time'],
                'message_id': message['unique_id'],
                'source_group': message['group'],
                'full_message': message['text'][:10000],  # Limit message length
                'extracted_links': '\n'.join(message['urls']) if message['urls'] else '',
                'category': 'Relevant' if is_relevant else 'Uncategorized'
            }
            
            if is_relevant:
                relevant_jobs.append(row_data)
            else:
                uncategorized.append(row_data)
        
        logging.info(f"Categorized: {len(relevant_jobs)} relevant, {len(uncategorized)} uncategorized")
        return relevant_jobs, uncategorized
    
    def update_google_sheet(self, relevant_jobs: List[Dict], uncategorized: List[Dict]):
        """Update Google Sheets with processed data"""
        try:
            # Prepare batch update data
            def prepare_rows(data_list):
                rows = []
                for item in data_list:
                    rows.append([
                        item['date_added'],
                        item['message_date'],
                        item['message_time'],
                        item['message_id'],
                        item['source_group'],
                        item['full_message'],
                        item['extracted_links'],
                        item['category']
                    ])
                return rows
            
            # Update Relevant Jobs sheet
            if relevant_jobs:
                relevant_sheet = self.sheet.worksheet('Relevant Jobs')
                rows = prepare_rows(relevant_jobs)
                relevant_sheet.append_rows(rows, value_input_option='USER_ENTERED')
                logging.info(f"Added {len(rows)} relevant jobs to sheet")
            
            # Update Uncategorized sheet  
            if uncategorized:
                uncat_sheet = self.sheet.worksheet('Uncategorized')
                rows = prepare_rows(uncategorized)
                uncat_sheet.append_rows(rows, value_input_option='USER_ENTERED')
                logging.info(f"Added {len(rows)} uncategorized messages to sheet")
            
            # Update processed messages set
            for job in relevant_jobs + uncategorized:
                self.processed_messages.add(job['message_id'])
                
        except Exception as e:
            logging.error(f"Error updating Google Sheets: {e}")
    
    def generate_summary(self, relevant_jobs: List[Dict], uncategorized: List[Dict]):
        """Generate a summary of the processing"""
        summary = f"""
        ========================================
        JOB COLLECTION SUMMARY
        ========================================
        
        Total New Messages Processed: {len(relevant_jobs) + len(uncategorized)}
        Relevant Jobs Found: {len(relevant_jobs)}
        Uncategorized Messages: {len(uncategorized)}
        
        Success Rate: {(len(relevant_jobs) / (len(relevant_jobs) + len(uncategorized)) * 100):.1f}%
        
        Previously Processed Messages (Skipped): {len(self.processed_messages)}
        
        Top Sources for Relevant Jobs:
        """
        
        if relevant_jobs:
            from collections import Counter
            sources = Counter([job['source_group'] for job in relevant_jobs])
            for source, count in sources.most_common(5):
                summary += f"\n  - {source}: {count} jobs"
        
        logging.info(summary)
        print(summary)
    
    async def run(self):
        """Main execution method"""
        try:
            start_time = datetime.now()
            logging.info("Starting Simple Telegram Job Agent...")
            
            # Setup connections
            await self.setup()
            
            # Fetch messages
            logging.info("Fetching messages from all groups...")
            messages = await self.fetch_all_messages()
            
            if not messages:
                logging.info("No new messages to process!")
                return
            
            # Categorize messages
            logging.info("Categorizing messages...")
            relevant_jobs, uncategorized = self.categorize_messages(messages)
            
            # Update Google Sheets
            logging.info("Updating Google Sheets...")
            self.update_google_sheet(relevant_jobs, uncategorized)
            
            # Generate summary
            self.generate_summary(relevant_jobs, uncategorized)
            
            # Calculate runtime
            end_time = datetime.now()
            runtime = (end_time - start_time).total_seconds() / 60
            logging.info(f"Job Agent completed successfully in {runtime:.2f} minutes!")
            
        except Exception as e:
            logging.error(f"Error in main execution: {e}")
            raise
        finally:
            if self.telegram_client:
                await self.telegram_client.disconnect()

async def main():
    """Main entry point"""
    agent = SimpleTelegramJobAgent()
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
