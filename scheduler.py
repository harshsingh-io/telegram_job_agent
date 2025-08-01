#!/usr/bin/env python3
"""
Scheduler for Telegram Job Agent
Runs the job agent automatically at specified times
"""

import asyncio
import schedule
import time
import logging
from datetime import datetime
import subprocess
import sys
import os
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

class JobAgentScheduler:
    def __init__(self):
        self.script_path = Path(__file__).parent / "telegram_job_agent.py"
        self.last_run = None
        self.run_history = []
        
    def run_agent(self):
        """Execute the job agent script"""
        try:
            start_time = datetime.now()
            logging.info(f"Starting job agent at {start_time}")
            
            # Run the agent script
            result = subprocess.run(
                [sys.executable, str(self.script_path)],
                capture_output=True,
                text=True
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() / 60
            
            if result.returncode == 0:
                logging.info(f"Job agent completed successfully in {duration:.2f} minutes")
                self.last_run = {
                    'status': 'success',
                    'start': start_time,
                    'end': end_time,
                    'duration': duration
                }
            else:
                logging.error(f"Job agent failed with error: {result.stderr}")
                self.last_run = {
                    'status': 'failed',
                    'start': start_time,
                    'end': end_time,
                    'duration': duration,
                    'error': result.stderr
                }
            
            self.run_history.append(self.last_run)
            
        except Exception as e:
            logging.error(f"Failed to run job agent: {e}")
            self.last_run = {
                'status': 'error',
                'start': datetime.now(),
                'error': str(e)
            }
    
    def health_check(self):
        """Check if the scheduler is healthy"""
        if not self.last_run:
            logging.info("No runs yet")
            return
        
        if self.last_run['status'] == 'success':
            logging.info(f"Last successful run: {self.last_run['start']} (Duration: {self.last_run['duration']:.2f} min)")
        else:
            logging.warning(f"Last run failed at {self.last_run['start']}")
    
    def get_stats(self):
        """Get statistics about runs"""
        if not self.run_history:
            return "No runs recorded yet"
        
        total_runs = len(self.run_history)
        successful_runs = sum(1 for run in self.run_history if run['status'] == 'success')
        avg_duration = sum(run.get('duration', 0) for run in self.run_history if 'duration' in run) / len(self.run_history)
        
        return f"""
        Job Agent Statistics:
        Total Runs: {total_runs}
        Successful: {successful_runs}
        Success Rate: {(successful_runs/total_runs)*100:.1f}%
        Average Duration: {avg_duration:.2f} minutes
        Last Run: {self.last_run['start'] if self.last_run else 'Never'}
        """

def main():
    """Main scheduler function"""
    scheduler = JobAgentScheduler()
    
    # Schedule options - uncomment the one you prefer
    
    # Option 1: Run at specific time daily (1 AM)
    schedule.every().day.at("01:00").do(scheduler.run_agent)
    
    # Option 2: Run every night at 10 PM
    # schedule.every().day.at("22:00").do(scheduler.run_agent)
    
    # Option 3: Run every 12 hours
    # schedule.every(12).hours.do(scheduler.run_agent)
    
    # Option 4: Run every day at multiple times
    # schedule.every().day.at("01:00").do(scheduler.run_agent)
    # schedule.every().day.at("13:00").do(scheduler.run_agent)
    
    # Health check every hour
    schedule.every().hour.do(scheduler.health_check)
    
    logging.info("Scheduler started. Waiting for scheduled runs...")
    logging.info(f"Next run scheduled at: {schedule.next_run()}")
    
    # Optional: Run immediately on start (uncomment if needed)
    # logging.info("Running initial job collection...")
    # scheduler.run_agent()
    
    try:
        while True:
            schedule.run_pending()
            
            # Display next run time every 10 minutes
            current_time = datetime.now()
            if current_time.minute % 10 == 0 and current_time.second < 1:
                logging.info(f"Current time: {current_time}. Next run at: {schedule.next_run()}")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        logging.info("\nScheduler stopped by user")
        print(scheduler.get_stats())
    except Exception as e:
        logging.error(f"Scheduler error: {e}")
        raise

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════╗
    ║    Telegram Job Agent Scheduler      ║
    ╠══════════════════════════════════════╣
    ║  Press Ctrl+C to stop                ║
    ║  Logs: scheduler.log                 ║
    ║  Default Schedule: Daily at 1 AM     ║
    ╚══════════════════════════════════════╝
    """)
    main()
