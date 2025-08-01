# Telegram Job Agent Setup Instructions

## Prerequisites Setup

### 1. Install Python Dependencies

Create a `requirements.txt` file:

```txt
telethon==1.34.0
google-generativeai==0.3.2
gspread==5.12.4
google-auth==2.25.2
google-auth-oauthlib==1.2.0
pandas==2.1.4
python-dotenv==1.0.0
```

Install with:
```bash
pip install -r requirements.txt
```

### 2. Get Telegram API Credentials

1. Go to https://my.telegram.org
2. Log in with your phone number
3. Go to "API Development Tools"
4. Create a new application
5. Save your `api_id` and `api_hash`

### 3. Get Google Gemini API Key (Free)

1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Save the API key

### 4. Setup Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Sheets API and Google Drive API
4. Create Service Account:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Download the JSON credentials file
5. Share your Google Sheet with the service account email

### 5. Environment Variables

Create a `.env` file:

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
PHONE_NUMBER=+91XXXXXXXXXX
GEMINI_API_KEY=your_gemini_key
GOOGLE_SHEETS_CREDS=credentials.json
```

## Running the Agent

### Manual Run (One-time)
```bash
python telegram_job_agent.py
```

### Automated Nightly Run

#### Option 1: Using Cron (Linux/Mac)
```bash
# Open crontab
crontab -e

# Add this line to run at 1 AM daily
0 1 * * * /usr/bin/python3 /path/to/telegram_job_agent.py >> /path/to/job_agent.log 2>&1
```

#### Option 2: Using Task Scheduler (Windows)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 1:00 AM
4. Set action: Start Program
   - Program: `python.exe`
   - Arguments: `C:\path\to\telegram_job_agent.py`

#### Option 3: Using Python Schedule
```python
import schedule
import time
import asyncio

def run_agent():
    asyncio.run(main())

# Schedule daily at 1 AM
schedule.every().day.at("01:00").do(run_agent)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## First Run Instructions

1. **Initial Authentication**: 
   - First run will ask for Telegram authentication
   - Enter the code sent to your phone
   - This creates a session file for future runs

2. **Test with One Group First**:
   - Comment out other groups in the code
   - Test with just one group to ensure everything works

3. **Monitor Logs**:
   - Check `job_agent.log` for any errors
   - Verify data appears in Google Sheets

## Google Sheets Structure

Your sheet will have two tabs:

### Relevant Jobs Tab
- Contains parsed job details
- AI-extracted information
- Only fresher/0-2 year positions

### Uncategorized Tab
- Messages that don't match criteria
- Review these periodically
- May contain relevant jobs with different formatting

## Performance Expectations

- **Processing Time**: 4-7 hours for all groups
- **Message Volume**: ~500-1000 messages per group
- **AI Processing**: 1-2 seconds per message
- **Rate Limits**: 
  - Telegram: Built-in delays
  - Gemini: 60 requests/minute (free tier)
  - Google Sheets: 100 requests/100 seconds

## Troubleshooting

### Common Issues

1. **"FloodWaitError" from Telegram**
   - Solution: Increase delays between requests
   - Already handled in code with sleep()

2. **Google Sheets "Quota exceeded"**
   - Solution: Batch updates (already implemented)
   - Reduce update frequency if needed

3. **Gemini API errors**
   - Check API key validity
   - Monitor free tier limits (60 RPM)

4. **Session expired**
   - Delete `job_agent_session.session` file
   - Re-authenticate on next run

## Optional Enhancements

1. **Add More AI Providers**:
   - Claude API (Anthropic)
   - OpenAI GPT-3.5
   - Local LLMs (Ollama)

2. **Advanced Filtering**:
   - Salary range extraction
   - Remote/Hybrid detection
   - Technology stack matching

3. **Notifications**:
   - Email for high-priority matches
   - Telegram bot for instant alerts
   - Discord webhook integration

4. **Data Analysis**:
   - Weekly trends report
   - Most hiring companies
   - Popular skills dashboard

## Security Best Practices

1. Never commit credentials to Git
2. Use environment variables
3. Rotate API keys periodically
4. Keep session files secure
5. Use read-only Google Sheets permissions where possible

## Support

For issues or questions:
- Check logs first (`job_agent.log`)
- Verify all API credentials
- Test with minimal configuration
- Add debug prints if needed