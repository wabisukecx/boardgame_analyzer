# BoardGame Analyzer

A Streamlit application for searching, analyzing, and saving board game information using the BoardGameGeek (BGG) API.

**Demo:** [Streamlit Community Cloud](https://boardgameanalyzer-gsmlbaspmgvf3arxttip4f.streamlit.app/)

## Latest Updates

**Enhanced Similarity Analysis Feature**

The similarity search feature has been enhanced. The new `improved_similarity_analyzer` module enables more precise similarity analysis. Key improvements:

- More detailed similarity reason analysis (with weighted scores)
- Advanced comparison utilizing learning curve data
- Analysis based on strategic depth and interaction similarity
- Formatted similarity reasons

This feature allows for a deeper understanding of similarities between games.

## Table of Contents

- [BoardGame Analyzer](#boardgame-analyzer)
  - [Latest Updates](#latest-updates)
  - [Table of Contents](#table-of-contents)
  - [Main Features](#main-features)
  - [Installation](#installation)
  - [How to Use](#how-to-use)
    - [Basic Features](#basic-features)
      - [Search by Game Name](#search-by-game-name)
      - [Get Details by Game ID](#get-details-by-game-id)
      - [Save Data to YAML](#save-data-to-yaml)
      - [Game Comparison](#game-comparison)
    - [Similarity Search](#similarity-search)
  - [Automatic Updates and Data Sync](#automatic-updates-and-data-sync)
    - [Daily Update Script (daily\_update.py)](#daily-update-script-daily_updatepy)
    - [Remote Data Sync Script (fetch\_boardgame\_data.py)](#remote-data-sync-script-fetch_boardgame_datapy)
  - [Embedding Data File (game\_embeddings.pkl)](#embedding-data-file-game_embeddingspkl)
    - [Creation and Acquisition](#creation-and-acquisition)
    - [Usage](#usage)
    - [Notes](#notes)
  - [Technical Details](#technical-details)
    - [Learning Curve Analysis System](#learning-curve-analysis-system)
      - [Elements Used in Analysis](#elements-used-in-analysis)
      - [Analysis Result Metrics](#analysis-result-metrics)
    - [Customizing Complexity Data](#customizing-complexity-data)
      - [Editing Notes](#editing-notes)
    - [Strategic Value and Interaction Analysis](#strategic-value-and-interaction-analysis)
    - [Embedding Model and Similarity Search Technology](#embedding-model-and-similarity-search-technology)
      - [Embedding Model Generation Technology](#embedding-model-generation-technology)
      - [Similarity Calculation Algorithm](#similarity-calculation-algorithm)
      - [Technical File Structure](#technical-file-structure)
      - [Similarity Reason Analysis Algorithm](#similarity-reason-analysis-algorithm)
  - [Project Structure](#project-structure)
  - [Notes](#notes-1)
  - [Acknowledgments](#acknowledgments)

## Main Features

- **Search and Information Retrieval**
  - Search by game name: Search for board games from BGG using names
  - Get detailed information by game ID: Retrieve detailed game information using game ID
  - Select saved games: Easily select saved game data from dropdown menus

- **Data Analysis and Storage**
  - Data analysis: Automatically analyze game complexity, learning curves, replayability, etc.
  - YAML data storage: Save retrieved game information locally in YAML format
  - Data comparison: Automatic comparison between existing and newly retrieved data

- **Game Characteristic Analysis**
  - Learning curve analysis: Estimate game learning ease and time required for mastery
  - Category analysis: Evaluate complexity based on game categories
  - Ranking analysis: Evaluation based on BGG ranking type and position
  - Strategic depth evaluation: Analysis of strategic based on decision quality and weight
  - Player interaction analysis: Evaluation of player-to-player interaction in games

- **Comparison and Similarity Analysis**
  - Game comparison: Select multiple games and analyze with radar charts and numerical comparisons
  - **Enhanced similarity search**: Search and analyze similar games using embedding data, providing detailed similarity reasons

- **Data Management and Automation**
  - Daily data updates: Automatic daily game data updates and backups
  - Remote data retrieval: Sync data from remote servers like Raspberry Pi

## Installation

1. Clone or download this repository

```bash
git clone https://github.com/wabisukecx/boardgame_analyzer.git
cd boardgame-analyzer
```

2. Install required libraries

```bash
pip install -r requirements.txt
```

3. Run the application

```bash
streamlit run app.py
```

## How to Use

### Basic Features

#### Search by Game Name
1. Select "Search by Game Name" from the sidebar
2. Enter the game name you want to search for
3. Check the checkbox for exact match search if desired
4. Click the "Search" button

#### Get Details by Game ID
1. Select "Get Details by Game ID" from the sidebar
2. Enter manually or select from saved YAML files
3. Click the "Get Details" button
4. Detailed information will be displayed including:
   - Basic information (game name, year published, average rating)
   - Player count information (optimal players, supported players)
   - Recommended age and play time
   - Game complexity and learning curve analysis
   - Game description
   - Mechanics, categories, rankings, designers, publishers information

#### Save Data to YAML
1. Select "Save Data to YAML" from the sidebar
2. Select the game you want to save from the dropdown list
3. Enter a filename (automatic generation if left blank)
4. Click the "Save Selected Game Data to YAML" button

#### Game Comparison
1. Select "Game Comparison" from the sidebar
2. Select multiple games to compare (up to 6)
3. Selected game characteristics are visualized with radar charts and detailed numerical comparison tables

### Similarity Search

1. Select "Similarity Search" from the sidebar
2. Adjust search settings (number of similar games to display, similarity threshold)
3. Expand "Set Search Filters" to filter by category or mechanics
4. Select a game as the search reference from filtered results
5. Click the "Search Similar Games" button
6. Results are displayed in tabs:
   - Similar Games List: Game information with similarity scores and reasons
   - Similarity Heatmap: Visualization of similarity relationships between games
   - Data Analysis: List of most similar games, category and mechanics distribution analysis

## Automatic Updates and Data Sync
By setting up a Linux-based remote server like Raspberry Pi, you can always analyze with the latest game data. As of April 2025, we recommend the Raspberry Pi Zero 2 W.

### Daily Update Script (daily_update.py)

Running this script periodically on a remote server like Raspberry Pi provides the following features:

- Backup saved data in YYMMDD format
- Automatically update existing game data (retrieve latest information from BGG API)
- Detect and record configuration file changes

Configuration example (using crontab):
```
0 1 * * * cd /path/to/boardgame-analyzer && python daily_update.py >> logs/daily_update.log 2>&1
```

### Remote Data Sync Script (fetch_boardgame_data.py)

Script for retrieving BoardGame Analyzer data updated on remote servers like Raspberry Pi:

- Retrieve game data and configuration files via SSH
- Customize connection settings (host, port, authentication method)
- Automatic cleanup of existing files

Usage example:
```bash
python fetch_boardgame_data.py --host 192.168.50.192 --username pi
```

## Embedding Data File (game_embeddings.pkl)

`game_embeddings.pkl` is an embedding data file required for the similarity search feature.

### Creation and Acquisition

1. **Use the distributed file**:
   - Available from the application repository
   - Place this file in the root of the `boardgame-analyzer` directory to immediately enable similarity search
   - Created from the author's board game collection for testing purposes

2. **Generate your own**:
   - Can be generated using the `generate_embedding_model.py` script
   - Uses the Voyage AI API
   - Requirements:
     - Voyage AI user registration (https://www.voyageai.com/)
     - Voyage AI API token issuance (handle with care)
     - Payment setup for API usage
     - Set `VOYAGE_API_KEY` environment variable
     - Create .env file and add VOYAGE_API_KEY = "your_voyage_api_key"
   - Generation command example:
     ```bash
     python generate_embedding_model.py --data_path "game_data/*.yaml" --output "game_embeddings.pkl"
     ```
   - Important optional parameters:
     - `--batch_size` - Batch size for API requests (default: 128). If too large, it may fail; if processing fails, set to a smaller value (e.g., 64 or 32)
     - `--max_retries` - Number of retries on API request failure (default: 5)
     - `--request_interval` - Wait time between requests (seconds, default: 0.5)
     - `--timeout` - API request timeout (seconds, default: 15)
     - `--limit` - Upper limit of files to process (0=process all, default: 0)

### Usage

1. Place the file in the application root directory
2. Select the "Similarity Search" feature in the application
3. By default, `game_embeddings.pkl` is loaded, but you can specify another file path in the sidebar's "Embedding Data File"

### Notes

- Without this file, the similarity search feature cannot be used (other features work normally)
- File size varies depending on the number of saved games and can be relatively large with many game data entries
- When generating yourself, API calls incur costs (based on Voyage AI's pricing structure)
- Regular updates allow inclusion of new game data in similarity searches

Creating your own embedding data enables similarity searches tailored to specific game genres or preferences.

## Technical Details

### Learning Curve Analysis System

This app uses a proprietary algorithm to analyze board game learning curves:

#### Elements Used in Analysis
- Mechanics complexity and count
- BGG weight rating
- Category complexity
- Ranking information
- Replayability
- Mechanics strategic value
- Player interaction value
- Play time

#### Analysis Result Metrics
- Initial learning barrier (1-5)
- Strategic depth (1-5)
- Decision points (1-5)
- Player interaction (1-5)
- Rules complexity (1-5)
- Category-based complexity (1-5)
- Ranking-based complexity (1-5)
- Learning curve type
- Replayability (1-5)
- Mastery time
- Target player types

### Customizing Complexity Data

This app uses three YAML files to evaluate complexity:

- `mechanics_data.yaml`: Complexity, strategic value, and interaction value per mechanics
- `categories_data.yaml`: Complexity, strategic value, and interaction value per category
- `rank_complexity.yaml`: Complexity, strategic value, and interaction value per ranking type

These files can be manually edited, enabling more accurate analysis by customizing based on actual game experience. Basic data is automatically generated on first startup, and new mechanics or categories are automatically added when found.

#### Editing Notes

- All YAML files must be saved in UTF-8 encoding
- Saving in other encodings (like Shift-JIS) will cause read errors
- Keep numerical values between 1.0-5.0 (to one decimal place)

### Strategic Value and Interaction Analysis

Each mechanics and category has the following defined values:

- Complexity: Rule or concept complexity (1.0-5.0)
- Strategic value: Contribution to strategic depth (1.0-5.0)
- Interaction value: Degree of player-to-player interaction (1.0-5.0)

For example, in mechanics_data.yaml:

```yaml
Engine Building:
  complexity: 4.7
  strategic_value: 5.0
  interaction_value: 2.0
  description: Very strategically deep but relatively low interaction
```

These values are used to more precisely calculate game strategic depth and interaction complexity.

### Embedding Model and Similarity Search Technology

`game_embeddings.pkl` is a core file for the application's similarity search functionality.

#### Embedding Model Generation Technology

- **Vectorization Process**: 
  - Convert each game's text data (name, description, categories, mechanics, etc.) into semantically enriched text
  - Encode text into 1024-dimensional vector space using Voyage AI API (voyage-3-large model)
  - These mathematically represent game characteristics and properties

- **Technical Specifications**:
  - Vector dimensions: 1024 dimensions (by voyage-3-large model)
  - Embedding type: Dense vector representation

#### Similarity Calculation Algorithm

- **Cosine Similarity**:
  - Measures the cosine of the angle between two vectors, calculating similarity score from 0-1
  - Values closer to 1 indicate higher similarity, closer to 0 indicate lower similarity
  - Formula: cos(θ) = (A·B) / (||A|| ||B||)
  
- **Pre-computed Similarity Matrix**:
  - Pre-computes pairwise similarities between all games
  - Stores N×N matrix (N is number of games)
  - This eliminates runtime similarity calculations, speeding up searches

#### Technical File Structure

`game_embeddings.pkl` is a Python pickle file with the following structure:

```python
{
    'games': [  # List of game information
        {'id': '123456', 'name': 'Game Name', 'japanese_name': 'Japanese Name', 'file': 'path/to/yaml'},
        # ... other game information
    ],
    'game_data_list': [  # List of detailed game data
        {'name': 'Game Name', 'mechanics': [...], 'categories': [...], ...},
        # ... other game data
    ],
    'embeddings': numpy.ndarray,  # Shape: [N, 1024] - 1024-dimensional vector for each of N games
    'similarity_matrix': numpy.ndarray,  # Shape: [N, N] - Stores similarity between all games
    'metadata': {  # File update metadata
        'file_path1': 'hash1',  # File path and its hash value
        # ... other file metadata
    }
}
```

#### Similarity Reason Analysis Algorithm

Includes automatic analysis of similarity reasons, comparing the following elements:

- Common categories
- Common mechanics
- Strategic depth similarity
- Common target player types
- Complexity score proximity
- Year published proximity
- Common keywords from descriptions

These analysis results are displayed as "Similarity Reasons" and help understand relationships between games more deeply.

## Project Structure

```
boardgame-analyzer/
├── app.py                         # Main application
├── requirements.txt               # Required packages list
├── generate_embedding_model.py    # Embedding model generation script
├── daily_update.py                # Daily data update script
├── fetch_boardgame_data.py        # Remote data retrieval script
├── game_embeddings.pkl            # Embedding data file (for similarity search)
├── learning_curve_for_daily_update.py # Learning curve analysis module
├── config/                        # Configuration files
│   ├── mechanics_data.yaml        # Mechanics complexity data
│   ├── categories_data.yaml       # Category complexity data
│   └── rank_complexity.yaml       # Ranking type complexity data
├── game_data/                     # Saved game data
├── backup/                        # Backup data
├── logs/                          # Log files
│   └── daily_update.log           # Daily update log
├── src/                           # Source code
│   ├── api/                       # API related
│   │   ├── bgg_api.py             # BoardGameGeek API
│   │   └── rate_limiter.py        # Rate limiting and cache
│   ├── data/                      # Data processing
│   │   └── data_handler.py        # Data processing
│   └── analysis/                  # Analysis related
│       ├── similarity.py          # Similarity search
│       ├── improved_similarity_analyzer.py # Improved similarity analysis
│       ├── game_analyzer.py       # Game analysis
│       ├── learning_curve.py      # Learning curve
│       ├── mechanic_complexity.py # Mechanics complexity
│       ├── category_complexity.py # Category complexity
│       ├── rank_complexity.py     # Ranking complexity
│       └── strategic_depth.py     # Strategic depth
└── ui/                            # UI related
    ├── ui_components.py           # UI component functions
    └── pages/                     # Page components
        ├── search_page.py         # Search page
        ├── details_page.py        # Details page
        ├── save_page.py           # Save page
        └── compare_page.py        # Compare page
```

## Notes

- Game names containing special characters (:; etc.) may fail to save as files
- This tool's learning curve analysis algorithm contains subjective elements and is not an absolute evaluation
- Embedding generation requires a Voyage AI API key and incurs charges based on usage
- Daily update scripts require scheduler setup like crontab for periodic execution

## Acknowledgments

This application uses the BoardGameGeek API. Thanks to BoardGameGeek.
The similarity search feature uses Voyage AI's embedding API for creating embedding data.