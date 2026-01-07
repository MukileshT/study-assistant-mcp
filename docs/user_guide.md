# Study Assistant MCP - User Guide

Complete guide to using the Study Assistant MCP system for automated note processing and study planning.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Processing Notes](#processing-notes)
3. [Study Planning](#study-planning)
4. [Configuration](#configuration)
5. [Advanced Features](#advanced-features)
6. [Tips & Best Practices](#tips--best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

Before using Study Assistant MCP, ensure you have:

✅ Python 3.11+ installed  
✅ All dependencies installed (`pip install -r requirements.txt`)  
✅ API keys configured in `.env`  
✅ Notion workspace set up  

### Quick Validation

Run the validation script to check your setup:

```bash
python scripts/validate_setup.py
```

This will verify:
- Python version
- Dependencies
- API keys
- Database setup
- API connections

---

## Processing Notes

### Basic Usage

Process a single note:

```bash
python -m src.main process note.jpg
```

Process multiple notes:

```bash
python -m src.main process lecture1.jpg lecture2.jpg lecture3.jpg
```

Process all images in a folder:

```bash
python -m src.main process notes/*.jpg
```

### With Options

Specify subject:

```bash
python -m src.main process note.jpg --subject "Mathematics"
```

Combine multiple images into one note:

```bash
python -m src.main process page1.jpg page2.jpg page3.jpg --combine
```

### What Happens During Processing

1. **Image Preprocessing**
   - Auto-rotation correction
   - Contrast and brightness enhancement
   - Noise reduction
   - Optimal sizing

2. **Text Extraction (OCR)**
   - Handwriting recognition
   - Formula detection
   - Diagram identification
   - Structure preservation

3. **Content Analysis**
   - Topic extraction
   - Subject classification
   - Difficulty assessment
   - Key concept identification

4. **Text Formatting**
   - Markdown conversion
   - Style application
   - Summary generation
   - Metadata addition

5. **Notion Upload**
   - Page creation
   - Property setting
   - Content formatting
   - Database organization

6. **Local Database**
   - Record saving
   - Hash tracking
   - Metadata storage

### Expected Output

After processing, you'll see:

```
✓ Note 1: Mathematics - Calculus - 2026-01-05
  Subject: Mathematics
  Topics: Derivatives, Limits, Applications
  Notion: abc123...
```

The note is now in your Notion database with:
- Formatted content
- Extracted topics
- Subject classification
- Date and metadata

---

## Study Planning

### Generate Daily Plan

Generate plan for today:

```bash
python -m src.main plan
```

Generate plan for specific date:

```bash
python -m src.main plan --date 2026-01-10
```

### How Planning Works

The system analyzes:

1. **Recent Notes** (last 14 days)
   - What subjects you've studied
   - Which topics you've covered
   - Difficulty of content
   - Study patterns

2. **Learning Patterns**
   - Subject frequency
   - Days since last study
   - Topic coverage
   - Difficulty distribution

3. **User Preferences**
   - Learning style
   - Study session length
   - Daily hour limits
   - Subject priorities

4. **Optimization**
   - Spaced repetition
   - Priority calculation
   - Time distribution
   - Cognitive load balancing

### Plan Output

Your plan includes:

- **Priority Subjects**: What to focus on
- **Schedule**: Time-blocked sessions
- **Topics**: Specific areas to review
- **Study Methods**: Techniques for your learning style
- **Expected Outcomes**: What you should accomplish

---

## Configuration

### View Current Config

```bash
python -m src.main config --show
```

### Update Learning Style

```bash
python -m src.main config --learning-style visual
```

Options:
- `visual` - Diagrams, charts, mind maps
- `auditory` - Verbal explanations, discussions
- `kinesthetic` - Hands-on practice, problems
- `reading_writing` - Detailed text, outlines

### Update Detail Level

```bash
python -m src.main config --detail-level detailed
```

Options:
- `minimal` - Key points only
- `standard` - Balanced detail (default)
- `detailed` - Everything including examples

### Edit Preferences File

For advanced configuration, edit:

```
config/user_preferences.json
```

You can customize:
- Note formatting preferences
- Subject priorities
- Study session settings
- Planning parameters

---

## Advanced Features

### Statistics

View processing and API usage stats:

```bash
python -m src.main stats
```

Shows:
- API usage (last 30 days)
- Token consumption
- Storage usage
- Processing history

### Cleanup

Remove old files and cache:

```bash
python -m src.main cleanup --days 30
```

This removes:
- Upload files older than N days
- Cache files
- Temporary data

### Testing

Test API connections:

```bash
python -m src.main test
```

Run validation:

```bash
python scripts/validate_setup.py
```

Run unit tests:

```bash
./scripts/run_tests.sh unit
```

---

## Tips & Best Practices

### For Best OCR Results

📸 **Image Quality**
- Good lighting (natural or bright)
- Clear, focused photos
- Minimal shadows
- High resolution (but system will optimize)

✍️ **Handwriting**
- Write clearly and legibly
- Use dark pen on white paper
- Avoid very light pencil
- Keep consistent spacing

📐 **Composition**
- Center the content
- Avoid edges and margins
- Include full page
- Minimize background clutter

### For Better Study Plans

📝 **Regular Processing**
- Process notes daily
- Don't let notes pile up
- Maintain consistent subjects
- Review processed notes in Notion

🎯 **Subject Organization**
- Use consistent subject names
- Tag topics accurately
- Set subject priorities in config
- Update preferences regularly

⏰ **Timing**
- Generate plans in evening
- Review plan in morning
- Adjust as needed during day
- Track completion

### For Efficient Workflow

1. **Batch Processing**
   ```bash
   python -m src.main process today/*.jpg
   ```

2. **Subject-Specific**
   ```bash
   python -m src.main process math/*.jpg --subject "Mathematics"
   ```

3. **Weekly Routine**
   - Monday: Process weekend study
   - Daily: Process day's notes
   - Friday: Review week's progress
   - Sunday: Plan next week

---

## Troubleshooting

### "API Key Not Valid"

**Solution:**
1. Check `.env` file
2. Verify no extra spaces
3. Ensure quotes if needed
4. Test at API provider's website

### "Notion Database Not Found"

**Solution:**
1. Verify database ID in `.env`
2. Check integration permissions
3. Ensure page is shared with integration
4. Run `python scripts/setup_notion.py`

### "Image File Too Large"

**Solution:**
1. Compress image before upload
2. Use JPEG instead of PNG
3. Adjust `MAX_IMAGE_SIZE_MB` in `.env`
4. System will auto-resize anyway

### "OCR Quality Low"

**Causes & Solutions:**
- **Blurry image**: Retake with better focus
- **Poor lighting**: Use better light
- **Complex layout**: Break into multiple images
- **Handwriting unclear**: Write more clearly

### "No Recent Notes for Planning"

**Solution:**
- Process some notes first
- System needs data to plan
- Default plan will be generated
- Add notes and regenerate

### "Rate Limit Exceeded"

**Solution:**
- Wait a few minutes
- System has retry logic
- Spread processing over time
- Check free tier limits:
  - Gemini: 15/min, 1,500/day
  - Groq: 30/min, 14,400/day

---

## Getting Help

### Check Logs

Logs are in: `data/logs/`

Enable debug mode:
```bash
# In .env
LOG_LEVEL=DEBUG
```

### Common Commands Quick Reference

```bash
# Process notes
python -m src.main process IMAGE1 [IMAGE2 ...]

# Generate plan
python -m src.main plan [--date YYYY-MM-DD]

# View config
python -m src.main config --show

# Update config
python -m src.main config --learning-style STYLE

# View stats
python -m src.main stats

# Clean up
python -m src.main cleanup [--days N]

# Test system
python -m src.main test
python scripts/validate_setup.py
```

### Support Resources

- 📖 Documentation: `docs/` folder
- 🐛 Issues: GitHub Issues
- 💬 Questions: GitHub Discussions
- 📧 Email: support@example.com

---

## Next Steps

1. **Process your first note**
   ```bash
   python -m src.main process my_first_note.jpg
   ```

2. **Check it in Notion**
   - Open your Notion workspace
   - Find the "Study Notes" database
   - See your formatted note!

3. **Generate a study plan**
   ```bash
   python -m src.main plan
   ```

4. **Customize preferences**
   ```bash
   python -m src.main config --learning-style YOUR_STYLE
   ```

---

**Happy Studying! 📚✨**

*Study smarter, not harder with AI-powered note processing and personalized study planning.*