#!/usr/bin/env python3
"""
Interactive Web Dashboard for Telegram Job Agent
View all messages without opening Google Sheets
"""

from flask import Flask, render_template, request, jsonify
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re
from collections import Counter
import json
import markdown

load_dotenv()

app = Flask(__name__)

class WebDashboard:
    def __init__(self):
        self.sheet = None
        self.setup_sheets()
    
    def setup_sheets(self):
        """Connect to Google Sheets"""
        try:
            creds_file = os.getenv("GOOGLE_SHEETS_CREDS", "credentials.json")
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            creds = Credentials.from_service_account_file(creds_file, scopes=scope)
            client = gspread.authorize(creds)
            
            self.sheet = client.open_by_url(
                'https://docs.google.com/spreadsheets/d/1shH8hGgA5HSGIZF6eQl0k00MCobBsPqVtjaUVp8XY9E'
            )
            print("✅ Connected to Google Sheets")
        except Exception as e:
            print(f"❌ Error connecting to sheets: {e}")
            raise
    
    def format_message_as_markdown(self, message):
        """Format message text as markdown-friendly"""
        if not message:
            return ""
        
        # Convert to markdown-friendly format
        text = message
        
        # Make URLs clickable in markdown
        url_pattern = r'(https?://[^\s<>"{}|\\^`\[\]]+)'
        text = re.sub(url_pattern, r'[\1](\1)', text)
        
        # Bold company names (basic detection)
        company_pattern = r'\b([A-Z][a-z]+ (?:Company|Corp|Corporation|Ltd|Limited|Inc|Technologies|Tech|Solutions|Systems))\b'
        text = re.sub(company_pattern, r'**\1**', text)
        
        # Bold job titles (basic detection)
        job_pattern = r'\b(Software (?:Engineer|Developer|Programmer)|Data (?:Scientist|Analyst)|Full Stack Developer|Backend Developer|Frontend Developer|DevOps Engineer)\b'
        text = re.sub(job_pattern, r'**\1**', text, flags=re.IGNORECASE)
        
        # Format requirements/skills sections
        text = re.sub(r'\b(Requirements?|Skills?|Qualifications?):\s*', r'\n**\1:**\n', text, flags=re.IGNORECASE)
        
        return text
    
    def extract_links_from_message(self, message):
        """Extract all links from a message"""
        if not message:
            return []
        
        url_patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            r'www\.[^\s<>"{}|\\^`\[\]]+',
            r'bit\.ly/[^\s]+',
            r't\.me/[^\s]+',
            r'linkedin\.com/[^\s]+',
            r'forms\.gle/[^\s]+',
        ]
        
        links = []
        for pattern in url_patterns:
            found_links = re.findall(pattern, message, re.IGNORECASE)
            links.extend(found_links)
        
        # Clean up links
        cleaned_links = []
        for link in links:
            # Remove trailing punctuation
            link = re.sub(r'[.,;:!?\)]+$', '', link)
            if link and link not in cleaned_links:
                cleaned_links.append(link)
        
        return cleaned_links
    
    def get_all_data(self):
        """Get all data from both sheets"""
        try:
            relevant_sheet = self.sheet.worksheet('Relevant Jobs')
            uncat_sheet = self.sheet.worksheet('Uncategorized')
            
            relevant_data = relevant_sheet.get_all_records()
            uncat_data = uncat_sheet.get_all_records()
            
            # Filter out empty rows and header duplicates
            relevant_data = [r for r in relevant_data if r.get('Message ID') and r.get('Message ID') != 'Message ID']
            uncat_data = [r for r in uncat_data if r.get('Message ID') and r.get('Message ID') != 'Message ID']
            
            # Add Category field and process each message
            for item in relevant_data:
                item['Category'] = 'Relevant'
                item['extracted_links'] = self.extract_links_from_message(item.get('Full Message', ''))
                item['formatted_message'] = self.format_message_as_markdown(item.get('Full Message', ''))
                
            for item in uncat_data:
                item['Category'] = 'Uncategorized'
                item['extracted_links'] = self.extract_links_from_message(item.get('Full Message', ''))
                item['formatted_message'] = self.format_message_as_markdown(item.get('Full Message', ''))
            
            return relevant_data, uncat_data
            
        except Exception as e:
            print(f"Error getting data: {e}")
            return [], []
    
    def get_filtered_data(self, category='all', source='all', start_date='', end_date='', search=''):
        """Get filtered data based on user criteria"""
        relevant_data, uncat_data = self.get_all_data()
        
        if category == 'relevant':
            data = relevant_data
        elif category == 'uncategorized':
            data = uncat_data
        else:
            data = relevant_data + uncat_data
        
        # Apply filters
        if source != 'all' and source:
            # Handle multiple source selection (comma-separated values)
            if ',' in source:
                selected_sources = [s.strip() for s in source.split(',')]
                data = [item for item in data if item.get('Source Group', '') in selected_sources]
            else:
                data = [item for item in data if item.get('Source Group', '') == source]
        
        # Date filtering with custom range
        if start_date and end_date:
            data = [item for item in data 
                   if start_date <= item.get('Message Date', '') <= end_date]
        elif start_date:
            data = [item for item in data 
                   if item.get('Message Date', '') >= start_date]
        elif end_date:
            data = [item for item in data 
                   if item.get('Message Date', '') <= end_date]
        
        if search:
            search_lower = search.lower()
            data = [item for item in data 
                   if search_lower in item.get('Full Message', '').lower() 
                   or search_lower in item.get('Source Group', '').lower()]
        
        # Sort by date-time latest first
        def sort_key(item):
            date_str = item.get('Message Date', '')
            time_str = item.get('Message Time', '00:00:00')
            try:
                return datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M:%S')
            except:
                return datetime.min
        
        data.sort(key=sort_key, reverse=True)
        
        return data
    
    def get_stats(self):
        """Get dashboard statistics"""
        relevant_data, uncat_data = self.get_all_data()
        
        total = len(relevant_data) + len(uncat_data)
        
        # Source distribution
        all_data = relevant_data + uncat_data
        sources = Counter([item.get('Source Group', 'Unknown') for item in all_data])
        
        # Date distribution
        dates = Counter([item.get('Message Date', 'Unknown') for item in all_data])
        
        # Today's count
        today = datetime.now().strftime('%Y-%m-%d')
        today_count = sum(1 for item in all_data if item.get('Message Date', '') == today)
        
        return {
            'total_messages': total,
            'relevant_jobs': len(relevant_data),
            'uncategorized': len(uncat_data),
            'today_count': today_count,
            'top_sources': dict(sources.most_common(5)),
            'recent_dates': dict(sorted(dates.items(), reverse=True)[:7])
        }

# Initialize dashboard
dashboard = WebDashboard()

@app.route('/')
def index():
    """Main dashboard page"""
    stats = dashboard.get_stats()
    return render_template('index.html', stats=stats)

@app.route('/api/data')
def get_data():
    """API endpoint to get filtered data"""
    category = request.args.get('category', 'all')
    source = request.args.get('source', 'all')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    data = dashboard.get_filtered_data(category, source, start_date, end_date, search)
    
    # Pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_data = data[start_idx:end_idx]
    
    return jsonify({
        'data': paginated_data,
        'total': len(data),
        'page': page,
        'per_page': per_page,
        'total_pages': (len(data) + per_page - 1) // per_page
    })

@app.route('/api/sources')
def get_sources():
    """Get all unique sources with message counts"""
    relevant_data, uncat_data = dashboard.get_all_data()
    all_data = relevant_data + uncat_data
    
    # Count messages per source
    source_counts = Counter([item.get('Source Group', 'Unknown') for item in all_data])
    
    # Return sources with counts
    sources_with_counts = [
        {
            'name': source,
            'count': count
        }
        for source, count in sorted(source_counts.items())
    ]
    
    return jsonify(sources_with_counts)

@app.route('/api/stats')
def get_stats():
    """Get current statistics"""
    return jsonify(dashboard.get_stats())

@app.route('/message/<message_id>')
def view_message(message_id):
    """View individual message details"""
    relevant_data, uncat_data = dashboard.get_all_data()
    all_data = relevant_data + uncat_data
    
    message = next((item for item in all_data if item.get('Message ID') == message_id), None)
    if not message:
        return "Message not found", 404
    
    return render_template('message_detail.html', message=message)

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════╗
    ║     Job Dashboard Web Interface      ║
    ╠══════════════════════════════════════╣
    ║  Starting Flask server...            ║
    ║  Open: http://localhost:8080         ║
    ╚══════════════════════════════════════╝
    """)
    
    app.run(debug=True, host='0.0.0.0', port=8080)