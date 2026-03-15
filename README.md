# BoardGame Analyzer - AI-Powered Board Game Analysis Tool

A comprehensive Streamlit application for analyzing board games using BoardGameGeek API data and advanced similarity search. Features intelligent learning curve analysis, multi-language support, and automated data management with remote synchronization capabilities.

## Key Features

### Smart Game Analysis
- **Learning Curve Analysis**: AI-powered evaluation of game complexity and strategic depth
- **Similarity Search**: Find similar games using pre-computed embeddings and cosine similarity
- **Multi-dimensional Metrics**: Initial barrier, strategic depth, replayability, player interaction, solo friendliness, luck dependency, and more
- **Japanese Description Translation**: Automatically translates English BGG descriptions to Japanese via Gemini 2.0 Flash

### Data Management
- **YAML Storage**: Local game data persistence with structured format
- **Auto-sync**: Remote server synchronization for always-updated data
- **Backup System**: Daily automated backups with change detection

### User Experience
- **Multi-language**: Japanese/English interface with intelligent game name display
- **Interactive Visualizations**: Radar charts, heatmaps, and distribution analysis
- **Responsive Design**: Optimized for desktop and mobile use

---

## Core Functions

| Function | Description | Key Benefits |
|----------|-------------|--------------|
| **Search by Name** | Find games using BGG database | Quick discovery with exact match option |
| **Game Details** | Comprehensive game information | Learning curve, complexity analysis |
| **Similarity Search** | AI-powered game recommendations | Discover games with detailed similarity reasons |
| **Game Comparison** | Side-by-side analysis of multiple games | Visual radar charts and metric tables |
| **Data Export** | Save analysis results to YAML | Local storage and backup capabilities |

---

## Quick Start

### Prerequisites

**BGG API Token (required)**

As of July 2025, the BoardGameGeek XML API requires registration and an application token for all use. Before running this application locally, you must obtain a token:

1. Create a BGG account at [boardgamegeek.com](https://boardgamegeek.com) if you do not have one
2. Go to [https://boardgamegeek.com/applications](https://boardgamegeek.com/applications) and click **Create Application**
3. Select **Non-commercial** for personal use
4. Wait for approval — this may take **a week or more**
5. Once approved, go to **Tokens** under your application and generate a Bearer token

> **Note**: Registration may not be approved in all cases. Applications that BGG judges to compete with or harm their business may be denied.

### Installation

```bash
# Clone repository
git clone https://github.com/wabisukecx/boardgame_analyzer.git
cd boardgame_analyzer

# Install dependencies
pip install -r requirements.txt

# Copy the example env file and add your tokens
cp .env.example .env
```

Edit `.env` and set your tokens:

```
BGG_TOKEN=your-bearer-token-here
GEMINI_API_KEY=your-gemini-api-key-here   # Optional: enables Japanese description translation
```

**Gemini API Key (optional)**

If you want game descriptions to be automatically translated to Japanese when saving YAML files, set a Gemini API key:

1. Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Create an API key
3. Set it as `GEMINI_API_KEY` in your `.env` file

If `GEMINI_API_KEY` is not set, the app works normally — descriptions remain in English only.

```bash
# Run application
streamlit run app.py
```

### Basic Usage
1. **Search**: Enter game name to find BoardGameGeek entries
2. **Analyze**: Get detailed information with learning curve analysis
3. **Save**: Export game data to YAML format for future use
4. **Compare**: Select multiple games for side-by-side analysis
5. **Discover**: Use similarity search to find related games

---

## Similarity Search Setup

### Option 1: Use Provided Embeddings
- Download `game_embeddings.pkl` from repository
- Place in root directory
- Similarity search ready to use

### Option 2: Generate Custom Embeddings
```bash
# Set Voyage AI API key in .env
VOYAGE_API_KEY=your_api_key

# Generate embeddings from your game data
python generate_embedding_model.py --data_path "game_data/*.yaml" --output "game_embeddings.pkl"
```

### Embedding Generation Options
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--batch_size` | 128 | API request batch size |
| `--max_tokens_per_item` | 3000 | Token limit per game |
| `--max_tokens_per_batch` | 100000 | Token limit per API call |
| `--limit` | 0 | Max files to process (0=all) |

---

## Analysis Metrics

### Learning Curve Analysis
| Metric | Range | Description |
|--------|-------|-------------|
| **Initial Barrier** | 1.0–5.0 | Difficulty of first-time learning |
| **Strategic Depth** | 1.0–5.0 | Long-term strategic complexity |
| **Replayability** | 1.0–5.0 | Value of repeated plays |
| **Decision Points** | 1.0–5.0 | Frequency of meaningful choices |
| **Player Interaction** | 1.0–5.0 | Degree of player-to-player engagement |
| **Rules Complexity** | 1.0–5.0 | Mechanical and rule system difficulty |
| **Solo Friendliness** | 1.0–5.0 | Suitability for solo play |
| **Player Scalability** | 1.0–5.0 | How well the game scales across player counts |
| **Luck Dependency** | 1.0–5.0 | Degree of random/luck elements vs. strategy |

### How Metrics Are Calculated

**Initial Barrier**
Weighted sum of average mechanic complexity (40%), rules complexity (25%), BGG weight (20%), and category/rank factor (15%), scaled by the number of mechanics.

**Strategic Depth**
Combines BGG weight (30% total), decision points (35%), rules complexity (10%), player interaction (25%), plus additive bonuses for high-value strategic mechanics, hidden information mechanics (asymmetric info, bluffing, deduction, etc.), and play time. All additive bonuses are individually capped to prevent score inflation.

**Replayability**
Based on mechanic diversity, replayability-enhancing mechanics (modular board, deck building, variable setup, etc.), category breadth, popularity rank (continuous logarithmic scale), play time adjustment (short games get a bonus; games over 3 hours get a small penalty), and a longevity factor for games with long publication history.

**Solo Friendliness**
Derived from the presence of Solo/Solitaire, Cooperative, or Campaign mechanics, and the publisher's minimum player count.

**Player Scalability**
Calculated from the difference between the publisher's maximum and minimum player counts.

**Luck Dependency**
Net score from luck-heavy mechanics (Dice Rolling, Push Your Luck, Random Production, etc.) minus strategy-heavy mechanics (Worker Placement, Engine Building, Tech Trees, etc.).

### Evaluation Summary
The summary text includes cross-metric relationship comments that describe how the metrics interact:
- High barrier + deep strategy → rewards long-term investment
- High barrier + shallow strategy → complex rules, limited strategic range
- Low barrier + deep strategy → easy to learn, hard to master
- Low barrier + shallow strategy → casual, accessible game
- Deep strategy + high replayability → long-term engagement
- Deep strategy + low replayability → patterns become familiar over time
- Shallow strategy + high replayability → light but highly variable

### Player Type Classification
| Type | Condition |
|------|-----------|
| **Beginner** | Initial barrier < 3.0 and strategic depth < 3.5 |
| **Casual** | Initial barrier < 4.0 and strategic depth < 4.5 |
| **Experienced** | Strategic depth ≥ 3.0 |
| **Hardcore** | Initial barrier > 3.0 and strategic depth > 3.5 |
| **Strategist** | Strategic depth > 3.8 |
| **System Master** | 5+ mechanics and strategic depth > 3.5 |
| **Replayer** | Replayability ≥ 3.8 |
| **Trend Follower** | BGG rank ≤ 1000 |
| **Classic Lover** | Published in 2000 or earlier |

---

## Automation Features

### Daily Data Updates
Automated system for keeping game data current:

```bash
# Set up cron job (Linux/macOS)
0 1 * * * cd /path/to/boardgame-analyzer && python daily_update.py >> logs/daily_update.log 2>&1
```

**Features:**
- Automatic BGG API data refresh
- YYMMDD backup creation
- Configuration change detection
- Error logging and retry logic

### Remote Synchronization
Sync data with remote servers (e.g., Raspberry Pi):

```bash
# Fetch latest data from remote server
python fetch_boardgame_data.py --host 192.168.1.100 --username pi
```

| Parameter | Description |
|-----------|-------------|
| `--host` | Remote server IP address |
| `--username` | SSH username |
| `--key-file` | SSH private key path |
| `--no-upload` | Skip upload phase |

---

## Configuration Files

### Complexity Data (YAML)
The application uses three configuration files for intelligent analysis:

| File | Purpose | Customizable |
|------|---------|--------------|
| `mechanics_data.yaml` | Mechanic complexity, strategic value, interaction value | ✅ Manual editing supported |
| `categories_data.yaml` | Category complexity, strategic value, interaction value | ✅ Manual editing supported |
| `rank_complexity.yaml` | Ranking type complexity | ✅ Manual editing supported |

Each entry stores four fields:

```yaml
Engine Building:
  complexity: 4.7
  strategic_value: 5.0
  interaction_value: 2.0
  description: Very strategically deep but relatively low interaction
```

Unknown mechanics and categories encountered during analysis are automatically added to these files with default values and batch-written to avoid excessive disk I/O.

---

## Language Support

### Supported Languages
- **Japanese (ja)**: Native support with kanji/hiragana/katakana
- **English (en)**: Full interface translation

### Game Name Handling
| Context | Japanese Mode | English Mode |
|---------|---------------|--------------|
| **Primary Display** | Japanese name → English fallback | English name → Japanese fallback |
| **Secondary Info** | English as caption | Japanese as caption |
| **File Naming** | English for consistency | English for consistency |

---

## Technical Architecture

### Core Technologies
- **Frontend**: Streamlit with Plotly visualizations
- **API**: BoardGameGeek XML API with rate limiting and Bearer token authentication
- **Translation**: Google Gemini 2.0 Flash for Japanese description translation (optional)
- **AI/ML**: Voyage AI embeddings, scikit-learn similarity
- **Storage**: YAML files with UTF-8 encoding
- **Networking**: SSH/SFTP for remote sync

### Performance Optimizations
- **Caching**: Multi-level cache (10-minute TTL for YAML data, 48-hour TTL for API responses)
- **Batch Writing**: Unknown mechanics/categories are buffered and written in batches of 10 to reduce disk I/O
- **Single-pass Calculation**: `calculate_strategic_depth_improved()` returns a tuple of sub-metrics so that decision points, interaction complexity, and rules complexity are each computed only once per analysis
- **Rate Limiting**: Intelligent BGG API throttling (max 15 requests/minute) with exponential backoff
- **Lazy Loading**: On-demand data processing

### File Structure
```
boardgame-analyzer/
├── app.py                          # Main Streamlit application
├── generate_embedding_model.py     # Embedding generation script
├── daily_update.py                 # Automated data update script
├── fetch_boardgame_data.py         # Remote sync script
├── learning_curve_for_daily_update.py
├── game_embeddings.pkl             # Similarity search data
├── .env.example                    # Environment variable template
├── config/
│   ├── mechanics_data.yaml         # Mechanic complexity data
│   ├── categories_data.yaml        # Category complexity data
│   ├── rank_complexity.yaml        # Ranking type complexity data
│   └── languages/                  # Translation files (ja.json, en.json)
├── game_data/                      # Saved game analysis (YAML per game)
├── logs/                           # Application logs
├── src/
│   ├── analysis/
│   │   ├── learning_curve.py       # Core learning curve calculation
│   │   ├── strategic_depth.py      # Strategic depth + sub-metrics
│   │   ├── game_analyzer.py        # Evaluation summary generation
│   │   ├── mechanic_complexity.py  # Mechanic YAML loader with cache
│   │   ├── category_complexity.py  # Category YAML loader with cache
│   │   ├── rank_complexity.py      # Rank YAML loader with cache
│   │   ├── similarity.py
│   │   └── improved_similarity_analyzer.py
│   ├── api/
│   │   ├── bgg_api.py              # BGG XML API client
│   │   ├── gemini_translator.py    # Gemini 2.0 Flash description translator
│   │   └── rate_limiter.py
│   ├── data/
│   └── utils/
└── ui/                             # Streamlit UI components
```

---

## Advanced Features

### Similarity Analysis Algorithm
1. **Text Processing**: Game data → enriched text representation
2. **Vectorization**: Voyage AI → 1024-dimensional embeddings
3. **Similarity Matrix**: Pre-computed cosine similarity (N×N)
4. **Reasoning Engine**: Multi-factor similarity explanation

### Learning Curve Calculation Pipeline
```
game_data
    │
    ├─► calculate_strategic_depth_improved()
    │       ├─ estimate_decision_points_improved()
    │       ├─ estimate_interaction_complexity_improved()
    │       ├─ calculate_rules_complexity()
    │       ├─ strategy_bonus (top mechanic strategic values)
    │       ├─ hidden_info_bonus (asymmetric info mechanics)
    │       └─ playtime_bonus
    │       └── returns tuple (depth, decision_pts, interaction, rules)
    │
    ├─► initial_barrier  (uses rules_complexity from above tuple)
    ├─► calculate_replayability()  (rank continuous scale + playtime)
    ├─► solo_friendliness, player_scalability, luck_dependency
    │
    └─► update_learning_curve_with_improved_strategic_depth()
            ├─ learning_curve_type (9 types)
            ├─ player_types
            └─ playtime_analysis
```

---

## Production Deployment

### Raspberry Pi Setup
Recommended for 24/7 data updates:

```bash
# Install dependencies
sudo apt update && sudo apt install python3-pip
pip3 install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add BGG_TOKEN

# Set up daily updates
crontab -e
# Add: 0 1 * * * cd /home/pi/boardgame-analyzer && python3 daily_update.py
```

### Resource Requirements
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 1GB | 2GB+ |
| **Storage** | 500MB | 2GB+ |
| **Network** | Stable internet | Broadband |
| **Python** | 3.8+ | 3.9+ |

---

## API Costs & Usage

### Gemini API (Description Translation)
- **Model**: gemini-2.0-flash
- **Cost**: Free tier available (generous daily quota for personal use)
- **Trigger**: Called once per game when saving to YAML, only if `description_ja` is absent
- **Caching**: Results cached in-process via `lru_cache`; no redundant API calls within a session
- **Fallback**: If the key is absent or the call fails, saving proceeds normally with English-only description
- **Pricing details**: [https://ai.google.dev/pricing](https://ai.google.dev/pricing)

### Voyage AI Embeddings
- **Current model**: voyage-4-large (replaces voyage-3-large)
- **Cost**: $0.12 per 1M tokens
- **Free tier**: First 200 million tokens free per account
- **Typical Game**: 500–1000 tokens
- **1000 Games**: ~$0.50–1.00 (well within the free tier at this scale)

### BoardGameGeek API
- **Authentication**: Bearer token required (as of July 2025)
- **Rate limiting**: Built-in throttle at 15 requests/minute with exponential backoff
- **Caching**: 48-hour TTL to minimize requests
- **Usage monitoring**: [https://boardgamegeek.com/applications](https://boardgamegeek.com/applications) → "Usage"

---

## Contributing

### Development Setup
```bash
# Clone with development branch
git clone -b develop https://github.com/wabisukecx/boardgame_analyzer.git

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Format code
black src/ ui/ *.py
```

### Adding New Languages
1. Create `config/languages/{code}.json`
2. Follow existing key structure (refer to `ja.json` or `en.json`)
3. Test with `language_manager.switch_language(code)`
4. Submit pull request

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Japanese translation not working** | Set `GEMINI_API_KEY` in `.env`; check that `google-genai` is installed (`pip install google-genai`) |
| **Translation skipped silently** | Check logs for `Gemini translation failed`; description may already be in Japanese (auto-detected) |
| **BGG API 401 / unauthorized** | Set `BGG_TOKEN` in `.env`; ensure the header format is `Bearer <token>` with no `www.` in the domain |
| **BGG token not yet approved** | Registration can take a week or more; check [boardgamegeek.com/applications](https://boardgamegeek.com/applications) |
| **BGG API rate limit** | Wait 60 seconds; the built-in rate limiter will auto-retry |
| **Embeddings not found** | Download `game_embeddings.pkl` or generate with Voyage AI |
| **YAML encoding errors** | Ensure UTF-8 encoding; avoid Shift-JIS |
| **Font rendering (Japanese)** | Install system Japanese fonts |
| **Memory issues** | Reduce batch size in embedding generation |

### Debug Mode
```bash
# Enable detailed logging
STREAMLIT_LOGGER_LEVEL=debug streamlit run app.py

# Check language configuration
python -c "from src.utils.language import debug_language_info; debug_language_info()"
```

---

## License & Acknowledgments

**License**: MIT License — Free for personal, educational, and commercial use

**Data Sources**:
- BoardGameGeek XML API for game information (token required)
- Google Gemini 2.0 Flash for Japanese description translation (optional)
- Voyage AI for similarity embeddings
- Community contributions for complexity data

**Special Thanks**:
- BoardGameGeek community for comprehensive game database
- Streamlit team for excellent web app framework
- Contributors to mechanics and category complexity data

---

**Version**: 2.2.0 | **Last Updated**: March 2026 | **Maintainer**: [@wabisukecx](https://github.com/wabisukecx)
