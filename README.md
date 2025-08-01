# 🤖 Telegram Job Agent

A powerful automated job scraping and analysis tool that monitors Telegram groups for fresher-friendly job opportunities. Features an interactive web dashboard, intelligent filtering, and automated data collection.

![Dashboard Preview](https://img.shields.io/badge/Dashboard-Interactive-blue) ![Python](https://img.shields.io/badge/Python-3.7%2B-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

## 🚀 Features

### 📊 **Interactive Web Dashboard**
- **Real-time filtering** by category, source groups, and date ranges
- **Multi-select source filtering** to view specific Telegram groups
- **Markdown-formatted messages** with syntax highlighting
- **Read more/less functionality** for long messages
- **Link extraction and pills** showing clickable application links
- **Message analysis** with keyword detection and sentiment analysis
- **Export capabilities** for individual messages and bulk data

### 🔍 **Smart Job Detection**
- **Keyword-based filtering** for fresher positions (0-2 years experience)
- **Automatic exclusion** of senior/experienced roles
- **Company and skill extraction** from job postings
- **Salary detection** and categorization
- **Link extraction** for application URLs

### 📱 **Telegram Integration**
- **Multi-group monitoring** of 14+ job-focused Telegram channels
- **Duplicate prevention** to avoid reprocessing messages
- **Rate limiting** to respect Telegram API limits
- **Session persistence** for uninterrupted operation

### 📈 **Data Management**
- **Google Sheets integration** for persistent storage
- **Automated categorization** (Relevant Jobs vs Uncategorized)
- **Batch processing** for efficient updates
- **Data export** capabilities (JSON, text files)

## 📋 Table of Contents

- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Usage](#-usage)
- [Web Dashboard](#-web-dashboard)
- [API Endpoints](#-api-endpoints)
- [Scheduling](#-scheduling)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## 🛠️ Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager
- Google account for Sheets API
- Telegram account for API access

### Quick Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd telegram_job
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Setup environment variables**
```bash
cp .env.example .env
# Edit .env with your actual API keys and credentials
```

4. **Test the setup**
```bash
python test_components.py
```

### Detailed Dependencies

Create a `requirements.txt` file:
```txt
telethon==1.34.0
google-generativeai==0.3.2
gspread==5.12.4
google-auth==2.25.2
google-auth-oauthlib==1.2.0
pandas==2.1.4
python-dotenv==1.0.0
flask==3.1.1
markdown==3.8.2
```

## ⚙️ Configuration

### 1. Telegram API Setup
1. Visit [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Go to "API Development Tools"
4. Create a new application
5. Note down your `api_id` and `api_hash`

### 2. Google Sheets API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Sheets API and Google Drive API
4. Create a Service Account and download the JSON credentials
5. Share your Google Sheet with the service account email

### 3. Gemini AI Setup (Optional but Recommended)
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key (free tier available)
3. Add to your `.env` file

### 4. Environment Configuration
Edit your `.env` file with the obtained credentials:
```bash
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
PHONE_NUMBER=+919876543210
GEMINI_API_KEY=your_gemini_key
GOOGLE_SHEETS_CREDS=credentials.json
```

## 🏃 Usage

### Command Line Usage

#### Run the Job Agent (One-time)
```bash
python telegram_job_agent_simple.py
```

#### Start the Web Dashboard
```bash
python web_dashboard.py
# Open http://localhost:8080 in your browser
```

#### Test Components
```bash
python test_components.py
```

#### Schedule Automated Runs
```bash
python scheduler.py
```

### First Run
On your first run, you'll need to authenticate with Telegram:
1. The script will send a verification code to your phone
2. Enter the code when prompted
3. A session file will be created for future automatic runs

## 🌐 Web Dashboard

The interactive web dashboard provides a comprehensive interface for viewing and analyzing collected job data.

### Main Features

#### 📊 **Statistics Dashboard**
- Total messages collected
- Relevant jobs count
- Today's new messages
- Source group activity

#### 🔍 **Advanced Filtering**
- **Category Filter**: Relevant Jobs, Uncategorized, or All
- **Multi-Select Sources**: Choose specific Telegram groups
- **Date Range Picker**: Custom start and end dates
- **Search**: Full-text search across messages

#### 📱 **Message Display**
- **Card-based layout** with expandable content
- **Read more/less** for long messages
- **Link pills** showing application URLs
- **Markdown formatting** for better readability
- **Keyword highlighting** for job-related terms

#### 📄 **Message Details Page**
- **Full message view** with formatting toggle
- **Extracted links** with platform detection
- **Quick analysis** with keyword extraction
- **Export capabilities** (JSON format)
- **Copy functions** for easy sharing

### Dashboard Navigation
- **Home**: Main message browser with filters
- **Message Details**: Click any message for detailed view
- **Real-time Updates**: Refresh button for latest data

## 🔌 API Endpoints

The web dashboard exposes several API endpoints:

```
GET /                          # Main dashboard
GET /api/data                  # Filtered message data
GET /api/sources              # Source groups with counts
GET /api/stats                # Dashboard statistics
GET /message/<message_id>     # Individual message details
```

### API Parameters
- `category`: 'all', 'relevant', 'uncategorized'
- `source`: comma-separated source group names
- `start_date`: YYYY-MM-DD format
- `end_date`: YYYY-MM-DD format
- `search`: search term
- `page`: page number for pagination
- `per_page`: items per page (20, 50, 100)

## ⏰ Scheduling

### Automated Daily Runs

#### Option 1: Using the Built-in Scheduler
```bash
python scheduler.py
```
Default: Runs daily at 1 AM

#### Option 2: Using Cron (Linux/Mac)
```bash
crontab -e
# Add this line for daily 1 AM execution:
0 1 * * * /usr/bin/python3 /path/to/telegram_job_agent_simple.py
```

#### Option 3: Using Task Scheduler (Windows)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 1:00 AM
4. Set action: Start Program
   - Program: `python.exe`
   - Arguments: `path\to\telegram_job_agent_simple.py`

### Performance Expectations
- **Processing Time**: 30-60 minutes for all groups
- **Message Volume**: ~500-1000 messages per group
- **Rate Limits**: Built-in delays respect API limits

## 🧪 Testing

### Component Testing
```bash
python test_components.py
```
This will test:
- Telegram API connection
- Google Sheets access
- Gemini AI functionality (if enabled)
- Keyword matching logic

### Manual Testing
```bash
# Test with one group first
python telegram_job_agent_simple.py
```

## 📊 Monitored Telegram Groups

The agent monitors these job-focused Telegram channels:
- os_Community
- infytq_2022
- internfreak
- OceanOfJobs
- jobs_and_internships_updates
- gocareers
- vijaykushal
- dot_aware
- CodingBugs
- goyalarsh
- findITJobsLink
- arunchauhanofficial
- TorchBearerr
- offcampus_phodenge

## 🛠️ Troubleshooting

### Common Issues

#### 1. "FloodWaitError" from Telegram
**Solution**: Increase delays in configuration
```bash
TELEGRAM_REQUEST_DELAY=5
```

#### 2. Google Sheets "Quota exceeded"
**Solution**: 
- Reduce batch size
- Check service account permissions
- Verify API limits

#### 3. Session Expired
**Solution**: Delete session files and re-authenticate
```bash
rm *.session*
python telegram_job_agent_simple.py
```

#### 4. Port 5000 Already in Use
**Solution**: The dashboard uses port 8080 by default. If needed, change it:
```bash
DASHBOARD_PORT=8081
```

### Debug Mode
Enable detailed logging:
```bash
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

## 🏗️ Project Structure

```
telegram_job/
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
├── setup-instructions.md    # Detailed setup guide
├── README.md               # This file
├── telegram_job_agent_simple.py  # Main job scraping script
├── web_dashboard.py        # Flask web dashboard
├── scheduler.py            # Automated scheduling
├── simple_dashboard.py     # CLI dashboard
├── test_components.py      # Component testing
├── templates/              # HTML templates
│   ├── index.html         # Main dashboard page
│   └── message_detail.html # Message details page
└── depreciated_file/       # Legacy scripts
    ├── telegram_job_agent.py
    ├── dashboard-script.py
    └── check_gemini_models.py
```

## 🔒 Security Considerations

- Never commit `.env` files or `credentials.json`
- Use environment variables for all sensitive data
- Regularly rotate API keys
- Keep session files secure
- Use read-only permissions where possible

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Format code
black .
flake8 .
```

## 📈 Future Enhancements

- [ ] AI-powered job matching based on user preferences
- [ ] Email/Discord notifications for high-priority matches
- [ ] Advanced analytics and trending insights
- [ ] Mobile app for iOS/Android
- [ ] Integration with LinkedIn and other job boards
- [ ] Resume matching against job requirements
- [ ] Salary trend analysis
- [ ] Company rating integration

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Telethon](https://github.com/LonamiWebs/Telethon) for Telegram API access
- [Google Sheets API](https://developers.google.com/sheets/api) for data storage
- [Flask](https://flask.palletsprojects.com/) for the web dashboard
- [Bootstrap](https://getbootstrap.com/) for UI components
- [Google Gemini](https://makersuite.google.com/) for AI analysis

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: Check `setup-instructions.md` for detailed setup
- **Testing**: Run `test_components.py` to verify your setup

---

**Made with ❤️ for the job-seeking community**

*Last updated: August 2025*