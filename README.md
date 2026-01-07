#  AI Study Assistant with MCP

An intelligent agent system that automatically processes handwritten class notes, organizes them in Notion, and generates personalized daily study plans based on your learning style.

##  Features

-  **Automated Note Digitization** - Upload photos of handwritten notes
-  **AI-Powered Analysis** - Extract key concepts, summaries, and structure
-  **Notion Integration** - Organized storage with rich formatting
-  **Personalized Planning** - Daily study plans adapted to your learning style
-  **Smart Prioritization** - Focus on what matters most
-  **100% Free** - Uses free-tier APIs (Gemini, Groq)

##  Architecture

```
Photo → Image Processing → OCR (Gemini Vision) → Text Analysis (Groq) → Formatting → Notion Storage → Study Analysis → Daily Plan Generation (Gemini Pro) → Notion
```

##  Quick Start

### Prerequisites

- Python 3.11 or higher
- Notion account
- API keys (all free):
  - Google AI Studio (Gemini)
  - Groq Cloud
  - Notion Integration

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/MukileshT/study-assistant-mcp.git
cd study-assistant-mcp
```

2. **Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Get API Keys**

   **Gemini (Google AI Studio):**
   - Visit: https://ai.google.dev
   - Click "Get API Key"
   - Copy to `.env` as `GOOGLE_API_KEY`

   **Groq:**
   - Visit: https://console.groq.com
   - Sign up and get API key
   - Copy to `.env` as `GROQ_API_KEY`

   **Notion:**
   - Visit: https://www.notion.so/my-integrations
   - Create new integration
   - Copy token to `.env` as `NOTION_API_KEY`
   - Create a database in Notion and share it with your integration
   - Copy database ID to `.env` as `NOTION_DATABASE_ID`

6. **Initialize Notion workspace**
```bash
python scripts/setup_notion.py
```

##  Usage

### Upload and Process Notes

```bash
# Process a single image
python -m src.main process image.jpg

# Process multiple images
python -m src.main process note1.jpg note2.jpg note3.jpg

# Process all images in a folder
python -m src.main process ./my-notes/
```

### Generate Daily Study Plan

```bash
# Generate plan for tomorrow
python -m src.main plan

# Generate plan for specific date
python -m src.main plan --date 2024-01-15
```

### Configure Preferences

```bash
# Set learning style
python -m src.main config --learning-style visual

# Set note detail level
python -m src.main config --detail-level detailed

# View current settings
python -m src.main config --show
```

## 🎨 Customization

### Learning Styles

Choose your learning style in `config/user_preferences.json`:
- **Visual** - Emphasis on diagrams, charts, mind maps
- **Auditory** - Focus on verbal explanations, summaries
- **Kinesthetic** - Practice problems, hands-on examples
- **Reading/Writing** - Detailed text, lists, definitions

### Note Templates

Customize Notion templates in `config/notion_templates.py`:
- Header styles
- Metadata fields
- Color schemes
- Organization structure

##  Development

### Project Structure

```
study-assistant-mcp/
├── config/          # Configuration files
├── src/
│   ├── core/       # Main agent & orchestration
│   ├── models/     # AI model clients
│   ├── processors/ # Image & text processing
│   ├── storage/    # Notion & database
│   ├── planning/   # Study planning logic
│   └── utils/      # Utilities
├── scripts/        # Setup & automation scripts
├── tests/          # Unit tests
└── data/           # Local cache & uploads
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_image_processing.py
```

### Code Quality

```bash
# Format code
black src/

# Lint
flake8 src/

# Type checking
mypy src/
```

##  Performance

- **Note Processing:** ~5-10 seconds per image
- **Daily Plan Generation:** ~3-5 seconds
- **API Costs:** $0.00 (free tier)
- **Daily Limits:** ~50 notes, 1 plan (well within free quotas)

##  Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

##  Acknowledgments

- **Gemini API** by Google
- **Groq** for fast inference
- **Notion** for amazing organization tools
- **MCP** (Model Context Protocol) by Anthropic

## upcomming

- [ ] Mobile app support
- [ ] Voice note processing
- [ ] Collaborative study groups
- [ ] Flashcard generation
- [ ] Quiz creation
- [ ] Progress tracking dashboard

---

**Made with 💖 for students who want to study smarter, not harder**