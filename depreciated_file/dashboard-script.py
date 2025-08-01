#!/usr/bin/env python3
"""
Dashboard to view job collection statistics and recent entries
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from collections import Counter
import re

load_dotenv()

class JobDashboard:
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
    
    def get_stats(self):
        """Get overall statistics"""
        try:
            relevant_sheet = self.sheet.worksheet('Relevant Jobs')
            uncat_sheet = self.sheet.worksheet('Uncategorized')
            
            relevant_data = relevant_sheet.get_all_records()
            uncat_data = uncat_sheet.get_all_records()
            
            # Remove header if present
            relevant_data = [r for r in relevant_data if r.get('Date Added') != 'Date Added']
            uncat_data = [r for r in uncat_data if r.get('Date Added') != 'Date Added']
            
            print("\n📊 JOB COLLECTION STATISTICS")
            print("="*50)
            print(f"Total Relevant Jobs: {len(relevant_data)}")
            print(f"Total Uncategorized: {len(uncat_data)}")
            print(f"Total Messages Processed: {len(relevant_data) + len(uncat_data)}")
            
            return relevant_data, uncat_data
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return [], []
    
    def analyze_by_date(self, data):
        """Analyze jobs by date"""
        if not data:
            return
        
        date_counts = Counter()
        for job in data:
            date = job.get('Date Added', '')
            if date:
                date_counts[date] += 1
        
        print("\n📅 JOBS BY DATE (Last 7 days)")
        print("-"*30)
        
        for date in sorted(date_counts.keys(), reverse=True)[:7]:
            print(f"{date}: {date_counts[date]} jobs")
    
    def analyze_by_source(self, data):
        """Analyze jobs by source group"""
        if not data:
            return
        
        source_counts = Counter()
        for job in data:
            source = job.get('Source Group', 'Unknown')
            source_counts[source] += 1
        
        print("\n📡 TOP SOURCES")
        print("-"*30)
        
        for source, count in source_counts.most_common(10):
            print(f"{source}: {count} jobs")
    
    def analyze_companies(self, data):
        """Analyze top hiring companies"""
        if not data:
            return
        
        company_counts = Counter()
        for job in data:
            company = job.get('Company', '').strip()
            if company and company != 'Not specified' and company != 'Error parsing':
                company_counts[company] += 1
        
        print("\n🏢 TOP HIRING COMPANIES")
        print("-"*30)
        
        for company, count in company_counts.most_common(10):
            print(f"{company}: {count} positions")
    
    def analyze_skills(self, data):
        """Analyze most demanded skills"""
        if not data:
            return
        
        skill_counts = Counter()
        for job in data:
            skills = job.get('Skills', '')
            if skills and skills != 'Not specified':
                # Split by common delimiters
                skill_list = re.split(r'[,;/|]', skills)
                for skill in skill_list:
                    skill = skill.strip().lower()
                    if skill and len(skill) > 1:
                        skill_counts[skill] += 1
        
        print("\n💻 TOP SKILLS IN DEMAND")
        print("-"*30)
        
        for skill, count in skill_counts.most_common(15):
            print(f"{skill.title()}: {count} mentions")
    
    def show_recent_jobs(self, data, limit=5):
        """Show recent job postings"""
        if not data:
            return
        
        print(f"\n📋 RECENT JOB POSTINGS (Last {limit})")
        print("="*70)
        
        # Sort by date
        sorted_data = sorted(data, key=lambda x: x.get('Message Date', ''), reverse=True)
        
        for i, job in enumerate(sorted_data[:limit], 1):
            print(f"\n{i}. {job.get('Position', 'Unknown Position')}")
            print(f"   Company: {job.get('Company', 'Not specified')}")
            print(f"   Location: {job.get('Location', 'Not specified')}")
            print(f"   Experience: {job.get('Experience', 'Not specified')}")
            print(f"   Posted: {job.get('Message Date', 'Unknown')}")
            print(f"   Source: {job.get('Source Group', 'Unknown')}")
            
            # Show truncated message
            message = job.get('Full Message', '')
            if message:
                preview = message[:100] + "..." if len(message) > 100 else message
                print(f"   Preview: {preview}")
    
    def analyze_locations(self, data):
        """Analyze job locations"""
        if not data:
            return
        
        location_counts = Counter()
        for job in data:
            location = job.get('Location', '').strip()
            if location and location != 'Not specified':
                # Normalize common location names
                location = location.lower()
                if 'bangalore' in location or 'bengaluru' in location:
                    location = 'Bangalore'
                elif 'delhi' in location or 'ncr' in location:
                    location = 'Delhi/NCR'
                elif 'mumbai' in location:
                    location = 'Mumbai'
                elif 'remote' in location:
                    location = 'Remote'
                else:
                    location = location.title()
                
                location_counts[location] += 1
        
        print("\n📍 JOB LOCATIONS")
        print("-"*30)
        
        for location, count in location_counts.most_common(10):
            print(f"{location}: {count} jobs")
    
    def run_dashboard(self):
        """Run the complete dashboard"""
        print("""
    ╔══════════════════════════════════════╗
    ║     JOB COLLECTION DASHBOARD         ║
    ╚══════════════════════════════════════╝
        """)
        
        # Get data
        relevant_data, uncat_data = self.get_stats()
        
        if not relevant_data:
            print("\n⚠️  No relevant jobs found yet. Run the agent first!")
            return
        
        # Run analyses
        self.analyze_by_date(relevant_data)
        self.analyze_by_source(relevant_data)
        self.analyze_companies(relevant_data)
        self.analyze_locations(relevant_data)
        self.analyze_skills(relevant_data)
        self.show_recent_jobs(relevant_data, limit=5)
        
        # Summary
        print("\n" + "="*70)
        print("💡 INSIGHTS")
        print("-"*70)
        
        # Calculate some insights
        today_count = sum(1 for job in relevant_data 
                         if job.get('Date Added') == datetime.now().strftime('%Y-%m-%d'))
        
        print(f"• Jobs added today: {today_count}")
        print(f"• Average jobs per day: {len(relevant_data) / 7:.1f}")
        print(f"• Categorization rate: {len(relevant_data) / (len(relevant_data) + len(uncat_data)) * 100:.1f}%")
        
        # Suggest review if many uncategorized
        if len(uncat_data) > len(relevant_data) * 0.5:
            print(f"\n⚠️  High uncategorized count ({len(uncat_data)}). Consider reviewing keywords!")

def main():
    dashboard = JobDashboard()
    dashboard.run_dashboard()
    
    print("\n\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    main()
