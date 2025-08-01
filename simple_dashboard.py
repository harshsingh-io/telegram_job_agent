#!/usr/bin/env python3
"""
Simple analytics dashboard for job collection (No AI required)
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from collections import Counter
import re

load_dotenv()

class SimpleJobDashboard:
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
        except Exception as e:
            print(f"Error connecting to sheets: {e}")
            exit(1)
    
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
            
            return relevant_data, uncat_data
            
        except Exception as e:
            print(f"Error getting data: {e}")
            return [], []
    
    def show_summary(self):
        """Show overall summary"""
        relevant_data, uncat_data = self.get_all_data()
        
        print("\n" + "="*60)
        print("📊 JOB COLLECTION SUMMARY")
        print("="*60)
        
        total = len(relevant_data) + len(uncat_data)
        print(f"\nTotal Messages Collected: {total:,}")
        
        if total > 0:
            print(f"Relevant Jobs: {len(relevant_data):,} ({len(relevant_data)/total*100:.1f}%)")
            print(f"Uncategorized: {len(uncat_data):,} ({len(uncat_data)/total*100:.1f}%)")
        else:
            print("Relevant Jobs: 0")
            print("Uncategorized: 0")
            print("\n⚠️  No data found! Make sure to run the job agent first.")
        
        # Date range
        if relevant_data or uncat_data:
            all_data = relevant_data + uncat_data
            dates = [r.get('Message Date', '') for r in all_data if r.get('Message Date')]
            if dates:
                dates.sort()
                print(f"\nDate Range: {dates[0]} to {dates[-1]}")
        
        return relevant_data, uncat_data
    
    def analyze_by_source(self, data, title="Messages"):
        """Analyze messages by source group"""
        if not data:
            return
        
        print(f"\n📡 {title} BY SOURCE")
        print("-"*40)
        
        source_counts = Counter()
        for item in data:
            source = item.get('Source Group', 'Unknown')
            if source:
                source_counts[source] += 1
        
        for source, count in source_counts.most_common():
            percentage = count / len(data) * 100
            print(f"{source:.<30} {count:>5} ({percentage:>5.1f}%)")
    
    def analyze_by_date(self, data, title="Messages"):
        """Analyze messages by date"""
        if not data:
            return
        
        print(f"\n📅 {title} BY DATE (Last 7 days)")
        print("-"*40)
        
        date_counts = Counter()
        for item in data:
            date = item.get('Message Date', '')
            if date:
                date_counts[date] += 1
        
        # Show last 7 days
        for date in sorted(date_counts.keys(), reverse=True)[:7]:
            count = date_counts[date]
            print(f"{date}: {'█' * (count // 10)}{'▌' * ((count % 10) // 5)} {count}")
    
    def find_top_domains(self, data):
        """Find most common domains in links"""
        if not data:
            return
        
        print("\n🌐 TOP DOMAINS IN LINKS")
        print("-"*40)
        
        domain_counts = Counter()
        
        for item in data:
            links = item.get('Extracted Links', '')
            if links:
                # Extract domains from URLs
                urls = links.split('\n')
                for url in urls:
                    match = re.search(r'(?:https?://)?(?:www\.)?([^/\s]+)', url)
                    if match:
                        domain = match.group(1).lower()
                        # Clean up domain
                        domain = domain.split('?')[0].split('#')[0]
                        domain_counts[domain] += 1
        
        for domain, count in domain_counts.most_common(15):
            print(f"{domain:.<35} {count:>5}")
    
    def search_messages(self, keyword):
        """Search for specific keyword in messages"""
        relevant_data, uncat_data = self.get_all_data()
        all_data = relevant_data + uncat_data
        
        results = []
        keyword_lower = keyword.lower()
        
        for item in all_data:
            message = item.get('Full Message', '').lower()
            if keyword_lower in message:
                results.append(item)
        
        print(f"\n🔍 SEARCH RESULTS FOR '{keyword}'")
        print("="*60)
        print(f"Found {len(results)} messages containing '{keyword}'")
        
        # Show first 5 results
        for i, result in enumerate(results[:5], 1):
            print(f"\n{i}. {result.get('Source Group', 'Unknown')} - {result.get('Message Date', 'Unknown')}")
            message = result.get('Full Message', '')[:200]
            # Highlight keyword
            message = re.sub(f'({keyword})', r'**\1**', message, flags=re.IGNORECASE)
            print(f"   {message}...")
    
    def show_recent_jobs(self, limit=10):
        """Show most recent relevant jobs"""
        relevant_data, _ = self.get_all_data()
        
        if not relevant_data:
            print("\nNo relevant jobs found yet!")
            return
        
        # Sort by date and time
        sorted_data = sorted(relevant_data, 
                           key=lambda x: (x.get('Message Date', ''), x.get('Message Time', '')), 
                           reverse=True)
        
        print(f"\n📋 LATEST {limit} RELEVANT JOBS")
        print("="*60)
        
        for i, job in enumerate(sorted_data[:limit], 1):
            print(f"\n{i}. {job.get('Source Group', 'Unknown')} | {job.get('Message Date', '')} {job.get('Message Time', '')}")
            
            # Show message preview
            message = job.get('Full Message', '')[:300]
            print(f"   {message}...")
            
            # Show links if any
            links = job.get('Extracted Links', '')
            if links:
                print(f"   🔗 Links: {links.split()[0]}")
    
    def export_today_jobs(self):
        """Export today's jobs to a text file"""
        relevant_data, _ = self.get_all_data()
        today = datetime.now().strftime('%Y-%m-%d')
        
        today_jobs = [job for job in relevant_data if job.get('Date Added') == today]
        
        if not today_jobs:
            print(f"\nNo jobs added today ({today})")
            return
        
        filename = f"jobs_{today}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"RELEVANT JOBS - {today}\n")
            f.write("="*60 + "\n\n")
            
            for i, job in enumerate(today_jobs, 1):
                f.write(f"{i}. SOURCE: {job.get('Source Group', 'Unknown')}\n")
                f.write(f"   TIME: {job.get('Message Date')} {job.get('Message Time')}\n")
                f.write(f"   MESSAGE:\n{job.get('Full Message', '')}\n")
                if job.get('Extracted Links'):
                    f.write(f"   LINKS: {job.get('Extracted Links')}\n")
                f.write("\n" + "-"*60 + "\n\n")
        
        print(f"\n✅ Exported {len(today_jobs)} jobs to {filename}")
    
    def run_dashboard(self):
        """Main dashboard interface"""
        print("""
    ╔══════════════════════════════════════╗
    ║    SIMPLE JOB COLLECTION DASHBOARD   ║
    ╚══════════════════════════════════════╝
        """)
        
        while True:
            relevant_data, uncat_data = self.show_summary()
            
            print("\n\nOPTIONS:")
            print("1. View source analysis")
            print("2. View date analysis")
            print("3. View top domains")
            print("4. Show recent jobs")
            print("5. Search messages")
            print("6. Export today's jobs")
            print("0. Exit")
            
            choice = input("\nEnter choice (0-6): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.analyze_by_source(relevant_data, "Relevant Jobs")
                self.analyze_by_source(uncat_data, "Uncategorized")
            elif choice == '2':
                self.analyze_by_date(relevant_data, "Relevant Jobs")
            elif choice == '3':
                self.find_top_domains(relevant_data)
            elif choice == '4':
                limit = input("How many recent jobs to show? (default 10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                self.show_recent_jobs(limit)
            elif choice == '5':
                keyword = input("Enter search keyword: ").strip()
                if keyword:
                    self.search_messages(keyword)
            elif choice == '6':
                self.export_today_jobs()
            
            input("\nPress Enter to continue...")

def main():
    dashboard = SimpleJobDashboard()
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()
