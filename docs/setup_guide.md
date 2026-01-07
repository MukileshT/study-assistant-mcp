# Study Assistant MCP - Setup Guide

Complete guide to setting up and configuring the Study Assistant MCP system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [API Keys Setup](#api-keys-setup)
4. [Notion Configuration](#notion-configuration)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Git** (optional) - [Download](https://git-scm.com/downloads/)

### Required Accounts (All Free)

1. **Google AI Studio** - For Gemini API
2. **Groq** - For Groq API
3. **Notion** - For note storage

---

## Installation

### Quick Setup (Recommended)

**On macOS/Linux:**
```bash
chmod +x scripts/quick_setup.sh
./scripts/quick_setup.sh
```

**On Windows:**
```batch
scripts\quick_setup.bat
```

### Manual Setup

1. **Clone or download the repository**
```bash
git clone <repository-url>
cd study-assistant-mcp
```

2. **Create virtual environment**
```bash
python -m venv venv
```

3. **Activate virtual environment**

   macOS/Linux:
   ```bash
   source venv/bin/activate
   ```
   
   Windows:
   ```batch
   venv\Scripts\activate
   ```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Create .env file**
```bash
cp .env.example .env
```

---

## API Keys Setup

### 1. Google Gemini API Key

1. Visit [Google AI Studio](https://ai.google.dev)
2. Click **"Get API Key"**
3. Create a new API key or use existing
4. Copy the API key
5. Add to `.env`:
   ```
   GOOGLE_API_KEY=your_key_here
   ```

**Free Tier Limits:**
- 15 requests per minute
- 1,500 requests per day
- More than enough for personal use!

---

### 2. Groq API Key

1. Visit [Groq Console](https://console.groq.com)
2. Sign up for free account
3. Navigate to **API Keys** section
4. Click **"Create API Key"**
5. Copy the API key
6. Add to `.env`:
   ```
   GROQ_API_KEY=your_key_here
   ```

**Free Tier Limits:**
- 30 requests per minute
- 14,400 requests per day
- Ultra-fast inference!

---

### 3. Notion Integration

#### Step 1: Create Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Fill in details:
   - **Name**: Study Assistant MCP
   - **Logo**: (optional)
   - **Associated workspace**: Select your workspace
4. Under **Capabilities**, ensure these are enabled:
   - ✅ Read content
   - ✅ Update content
   - ✅ Insert content
5. Click **"Submit"**
6. Copy the **Internal Integration Token**
7. Add to `.env`:
   ```
   NOTION_API_KEY=secret_xxx...
   ```

#### Step 2: Create Workspace Page

1. Create a new page in Notion (this will be the parent for databases)
2. Name it something like "Study Notes" or "Study Assistant"

#### Step 3: Share Page with Integration

1. Open the page you created
2. Click **"..."** (three dots) in top right
3. Click **"Add connections"**
4. Select **"Study Assistant MCP"** (your integration name)
5. Click **"Confirm"**

#### Step 4: Get Page ID

1. With the page open, click **"Share"** → **"Copy link"**
2. The link looks like: `https://notion.so/Page-Title-abc123def456...`
3. The page ID is everything after the last `-`: `abc123def456...`
4. Keep this handy for the setup script

---

## Notion Configuration

### Automated Setup (Recommended)

Run the Notion setup script:
```bash
python scripts/setup_notion.py
```

The script will:
1. Test your Notion connection
2. Create required databases
3. Set up proper schemas
4. Create a sample note

**Follow the prompts** and provide your parent page ID when asked.

### Manual Setup

If you prefer to create databases manually:

1. **Create Notes Database**
   - In your parent page, type `/database` and create a new database
   - Name it "Study Notes"
   - Add these properties:
     - Title (title)
     - Subject (select)
     - Date (date)
     - Topics (multi-select)
     - Status (select)
     - Difficulty (select)
     - Source (select)
     - Word Count (number)

2. **Create Study Plans Database**
   - Create another database
   - Name it "Study Plans"
   - Add these properties:
     - Title (title)
     - Date (date)
     - Status (select)
     - Priority Subjects (multi-select)
     - Total Hours (number)
     - Completion (number)

3. **Get Database IDs**
   - Open each database as a full page
   - Copy the link
   - Extract the database ID (before the `?v=` part)
   - Add to `.env`:
     ```
     NOTION_DATABASE_ID=your_notes_db_id
     NOTION_PLANS_DATABASE_ID=your_plans_db_id
     ```

---

## Configuration

### Environment Variables

Edit `.env` file with your preferences:

```bash
# Core API Keys (Required)
GOOGLE_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
NOTION_API_KEY=your_notion_key
NOTION_DATABASE_ID=your_database_id

# Optional Settings
APP_ENV=development
LOG_LEVEL=INFO
MAX_IMAGE_SIZE_MB=10

# Model Selection
VISION_MODEL=gemini-1.5-flash
TEXT_MODEL=llama-3.1-70b-versatile
PLANNING_MODEL=gemini-1.5-pro

# User Preferences
LEARNING_STYLE=visual
NOTE_DETAIL_LEVEL=standard
TIMEZONE=America/New_York
```

### User Preferences

Edit `config/user_preferences.json` to customize:

- **Learning style**: visual, auditory, kinesthetic, reading_writing
- **Note formatting**: emojis, highlights, summaries
- **Subject priorities**: subjects and focus areas
- **Study schedule**: session duration, max hours, breaks

---

## Testing

### 1. Test API Connections

```bash
python scripts/test_apis.py
```

Expected output:
```
✓ Gemini API working!
✓ Groq API working!
✓ ModelManager working!
All tests passed!
```

### 2. Test Notion Connection

```bash
python scripts/setup_notion.py
```

Should confirm connection and show your databases.

### 3. Run Unit Tests

```bash
pytest tests/ -v
```

---

## Troubleshooting

### Common Issues

#### "Module not found" errors

**Solution:** Make sure virtual environment is activated
```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

Then reinstall dependencies:
```bash
pip install -r requirements.txt
```

---

#### Gemini API errors

**Issue:** "API key not valid"

**Solution:**
1. Check your API key in `.env`
2. Ensure no extra spaces or quotes
3. Verify key is active at [Google AI Studio](https://ai.google.dev)

**Issue:** "Quota exceeded"

**Solution:** Free tier limits reached. Wait for reset or:
- Gemini resets: Daily at midnight UTC
- Try using Groq fallback (automatic)

---

#### Groq API errors

**Issue:** "Rate limit exceeded"

**Solution:**
- Free tier: 30 requests/minute
- System has automatic retry with backoff
- Consider spacing out requests

---

#### Notion API errors

**Issue:** "Unauthorized" or "Invalid token"

**Solution:**
1. Regenerate integration token
2. Update `.env` with new token
3. Ensure integration is added to your workspace

**Issue:** "Object not found"

**Solution:**
1. Verify database IDs in `.env`
2. Ensure databases are shared with your integration
3. Check page permissions

**Issue:** "Validation error"

**Solution:**
- Database properties may not match expected schema
- Run `setup_notion.py` to recreate databases
- Or manually add missing properties

---

#### Image Processing errors

**Issue:** "File too large"

**Solution:**
- Default limit: 10MB per image
- Compress image before uploading
- Or increase `MAX_IMAGE_SIZE_MB` in `.env`

**Issue:** "Unsupported format"

**Solution:**
- Supported: JPG, PNG, HEIC, WEBP
- Convert other formats to supported types

---

### Getting Help

If you encounter issues:

1. Check the logs in `data/logs/`
2. Enable debug mode: `LOG_LEVEL=DEBUG` in `.env`
3. Review error messages carefully
4. Check API status pages:
   - [Google AI Status](https://status.cloud.google.com/)
   - [Groq Status](https://status.groq.com/)
   - [Notion Status](https://status.notion.so/)

---

## Next Steps

Once setup is complete:

1. **Process your first note:**
   ```bash
   python -m src.main process path/to/note.jpg
   ```

2. **Generate a study plan:**
   ```bash
   python -m src.main plan
   ```

3. **Configure your preferences:**
   ```bash
   python -m src.main config --learning-style visual
   ```

4. **Read the user manual:**
   See `docs/user_manual.md` for detailed usage instructions

---

**Setup Complete! Happy Studying! 📚✨**