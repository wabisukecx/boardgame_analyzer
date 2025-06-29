# BoardGame Analyzer - AI-Powered Board Game Analysis Tool

A comprehensive Streamlit application for analyzing board games using BoardGameGeek API data and advanced similarity search. Features intelligent learning curve analysis, multi-language support, and automated data management with remote synchronization capabilities.

**Live Demo:** [Streamlit Community Cloud](https://boardgameanalyzer-gsmlbaspmgvf3arxttip4f.streamlit.app/)

## Key Features

### Smart Game Analysis
- **Learning Curve Analysis**: AI-powered evaluation of game complexity and strategic depth
- **Similarity Search**: Find similar games using pre-computed embeddings and cosine similarity
- **Multi-dimensional Metrics**: Initial barrier, strategic depth, replayability, player interaction

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

### Installation
```bash
# Clone repository
git clone https://github.com/wabisukecx/boardgame_analyzer.git
cd boardgame_analyzer

# Install dependencies
pip install -r requirements.txt

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
# Set up Voyage AI API key
echo "VOYAGE_API_KEY=your_api_key" > .env

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
| **Initial Barrier** | 1.0-5.0 | Difficulty of first-time learning |
| **Strategic Depth** | 1.0-5.0 | Long-term strategic complexity |
| **Replayability** | 1.0-5.0 | Value of repeated plays |
| **Decision Points** | 1.0-5.0 | Frequency of meaningful choices |
| **Player Interaction** | 1.0-5.0 | Degree of player-to-player engagement |
| **Rules Complexity** | 1.0-5.0 | Mechanical and rule system difficulty |

### Player Type Classification
- **Beginner**: Low barrier, accessible games
- **Casual**: Moderate complexity, broad appeal
- **Experienced**: High strategic depth
- **Hardcore**: Complex systems, high barriers
- **Strategist**: Deep tactical games
- **System Master**: Multi-layered mechanics

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
| `mechanics_data.yaml` | Mechanic complexity values | ✅ Manual editing supported |
| `categories_data.yaml` | Category complexity values | ✅ Manual editing supported |
| `rank_complexity.yaml` | Ranking type complexity | ✅ Manual editing supported |

**Example Configuration:**
```yaml
Engine Building:
  complexity: 4.7
  strategic_value: 5.0
  interaction_value: 2.0
  description: Very strategically deep but relatively low interaction
```

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
- **API**: BoardGameGeek XML API with rate limiting
- **AI/ML**: Voyage AI embeddings, scikit-learn similarity
- **Storage**: YAML files with UTF-8 encoding
- **Networking**: SSH/SFTP for remote sync

### Performance Optimizations
- **Caching**: Multi-level cache system (memory, session, file)
- **Rate Limiting**: Intelligent BGG API throttling
- **Batch Processing**: Efficient embedding generation
- **Lazy Loading**: On-demand data processing

### File Structure
```
boardgame-analyzer/
├── app.py                          # Main Streamlit application
├── generate_embedding_model.py     # Embedding generation script
├── daily_update.py                 # Automated data update script
├── fetch_boardgame_data.py         # Remote sync script
├── game_embeddings.pkl             # Similarity search data
├── config/                         # Configuration files
│   ├── mechanics_data.yaml
│   ├── categories_data.yaml
│   ├── rank_complexity.yaml
│   └── languages/                  # Multi-language support
├── game_data/                      # Saved game analysis
├── src/                            # Source code modules
│   ├── analysis/                   # Analysis algorithms
│   ├── api/                        # BGG API interface
│   ├── data/                       # Data handling
│   └── utils/                      # Utilities
└── ui/                             # User interface components
```

---

## Advanced Features

### Similarity Analysis Algorithm
1. **Text Processing**: Game data → enriched text representation
2. **Vectorization**: Voyage AI → 1024-dimensional embeddings
3. **Similarity Matrix**: Pre-computed cosine similarity (N×N)
4. **Reasoning Engine**: Multi-factor similarity explanation

### Learning Curve Calculation
- **Mechanic Analysis**: Complexity weighting from 1000+ mechanics
- **Category Evaluation**: Strategic depth assessment
- **BGG Integration**: Community ratings and rankings
- **Time Factors**: Play time impact on complexity
- **Player Count**: Interaction complexity scaling

---

## Production Deployment

### Raspberry Pi Setup
Recommended for 24/7 data updates:

```bash
# Install dependencies
sudo apt update && sudo apt install python3-pip
pip3 install -r requirements.txt

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

### Voyage AI Embeddings
- **Model**: voyage-3-large (1024 dimensions)
- **Cost**: ~$0.12 per 1M tokens
- **Typical Game**: 500-1000 tokens
- **1000 Games**: ~$0.50-1.00

### BoardGameGeek API
- **Free tier**: 15-20 requests/minute
- **Rate limiting**: Built-in exponential backoff
- **Caching**: 24-48 hour TTL to minimize requests

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
2. Follow existing key structure
3. Test with `language_manager.switch_language(code)`
4. Submit pull request

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Embeddings not found** | Download `game_embeddings.pkl` or generate with Voyage AI |
| **BGG API rate limit** | Wait 60 seconds, rate limiter will auto-retry |
| **YAML encoding errors** | Ensure UTF-8 encoding, avoid Shift-JIS |
| **Font rendering (Japanese)** | Install system Japanese fonts |
| **Memory issues** | Reduce batch size in embedding generation |

### Debug Mode
```bash
# Enable detailed logging
STREAMLIT_LOGGER_LEVEL=debug streamlit run app.py

# Check configuration
python -c "from src.utils.language import debug_language_info; debug_language_info()"
```

---

## License & Acknowledgments

**License**: MIT License - Free for personal, educational, and commercial use

**Data Sources**:
- BoardGameGeek API for game information
- Voyage AI for similarity embeddings
- Community contributions for complexity data

**Special Thanks**:
- BoardGameGeek community for comprehensive game database
- Streamlit team for excellent web app framework
- Contributors to mechanics and category complexity data

---

**Version**: 2.0.0 | **Last Updated**: December 2024 | **Maintainer**: [@wabisukecx](https://github.com/wabisukecx)
