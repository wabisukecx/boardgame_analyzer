#!/usr/bin/env python3
"""
Daily update script for BoardGame Analyzer to be executed at midnight
- Saves YAML data to backup folder with YYMMDD format
- Gets list of game IDs from local YAML files
- Re-retrieves detailed information for each game using BGG API
- If config files are updated, outputs changes to log
"""

import os
import shutil
import yaml
import requests
import time
import datetime
import logging
import difflib
import random
import xml.etree.ElementTree as ET
import re
from pathlib import Path

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/daily_update.log',
    filemode='a'
)
logger = logging.getLogger('daily_update')

# Constants
BASE_DIR = Path('.')
GAME_DATA_DIR = BASE_DIR / 'game_data'
CONFIG_DIR = BASE_DIR / 'config'
BACKUP_DIR = BASE_DIR / 'backup'
LOGS_DIR = BASE_DIR / 'logs'

# Cache and rate limiting for API calls
_cache = {}
_cache_ttl = {}
_request_history = []

# Simple cache implementation
def simple_cache(ttl_hours=24):
    """Decorator providing simple cache functionality"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = str(args) + str(sorted(kwargs.items()))
            key_hash = hash(key)
            cache_key = f"{func.__name__}_{key_hash}"
            
            # Return from cache if valid
            current_time = time.time()
            if cache_key in _cache and _cache_ttl.get(cache_key, 0) > current_time:
                logger.debug(f"Returning data from cache: {cache_key}")
                return _cache[cache_key]
            
            # Execute function if cache miss or expired
            result = func(*args, **kwargs)
            
            # Save result to cache
            _cache[cache_key] = result
            # Set expiration time (in seconds)
            _cache_ttl[cache_key] = current_time + (ttl_hours * 3600)
            
            return result
        return wrapper
    return decorator

# Rate limiting implementation
def rate_limited_request(max_per_minute=15, max_retries=3):
    """Decorator to rate limit BGG API requests"""
    # Calculate minimum interval between requests
    min_interval = 60.0 / max_per_minute
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            global _request_history
            
            # Remove request history older than 1 minute
            current_time = time.time()
            one_minute_ago = current_time - 60
            _request_history = [t for t in _request_history if t > one_minute_ago]
            
            # Check number of requests in past minute
            if len(_request_history) >= max_per_minute:
                # Use min_interval to evenly distribute requests
                oldest_request = min(_request_history) if _request_history else current_time - 60
                time_since_oldest = current_time - oldest_request
                # Calculate wait time based on elapsed time
                wait_time = max(0, min_interval - (time_since_oldest / max(1, len(_request_history)))) + random.uniform(0.1, 1.0)
                
                if wait_time > 0:
                    logger.info(f"BGG API rate limit reached. Waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
            
            # Add jitter to avoid simultaneous requests
            jitter = random.uniform(0.2, 1.0)
            time.sleep(jitter)
            
            # Execute request with retry logic
            retries = 0
            while retries <= max_retries:
                try:
                    # Record request history
                    _request_history.append(time.time())
                    
                    # Actual function call
                    result = func(*args, **kwargs)
                    return result
                    
                except requests.exceptions.HTTPError as e:
                    retries += 1
                    if e.response.status_code == 429:  # Too Many Requests
                        # Rate limit error
                        retry_after = int(e.response.headers.get('Retry-After', 30))
                        wait_time = retry_after + random.uniform(1, 5)
                        
                        logger.warning(f"BGG API rate limit reached. Waiting {wait_time:.1f} seconds... (attempt {retries}/{max_retries})")
                        time.sleep(wait_time)
                    
                    elif e.response.status_code >= 500:
                        # Server error - backoff and retry
                        wait_time = (2 ** retries) + random.uniform(0, 1)
                        
                        logger.warning(f"BGG API server error (status {e.response.status_code}). Retrying in {wait_time:.1f} seconds... (attempt {retries}/{max_retries})")
                        time.sleep(wait_time)
                    
                    else:
                        # Other HTTP errors
                        logger.error(f"API call error: {e.response.status_code} - {e.response.reason}")
                        raise
                
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    # Connection error or timeout
                    retries += 1
                    wait_time = (2 ** retries) + random.uniform(0, 1)
                    
                    # Adjust error message based on exception type
                    error_type = "Timeout" if isinstance(e, requests.exceptions.Timeout) else "Connection error"
                    logger.warning(f"{error_type} occurred. Retrying in {wait_time:.2f} seconds (attempt {retries}/{max_retries})")
                    time.sleep(wait_time)
                    
                # Maximum retries reached
                if retries > max_retries:
                    logger.error(f"Maximum retries ({max_retries}) reached. Please try again later.")
                    raise Exception("Maximum API request retries reached")
        
        return wrapper
    return decorator

@simple_cache(ttl_hours=48)
@rate_limited_request(max_per_minute=15)
def get_game_details(game_id):
    """Get detailed game information"""
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={game_id}&stats=1"
    logger.info(f"Retrieving details for game ID {game_id}...")
    
    response = requests.get(url)
    
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        game = {}
        
        item = root.find(".//item")
        if item is not None:
            game["id"] = item.get("id")
            game["type"] = item.get("type")
            
            # Get primary name
            name_element = item.find(".//name[@type='primary']")
            if name_element is not None:
                game["name"] = name_element.get("value")
            
            # Get alternate names (including Japanese names)
            alternate_names = []
            for name_elem in item.findall(".//name"):
                name_value = name_elem.get("value")
                name_type = name_elem.get("type")
                
                # Skip primary name as already retrieved
                if name_type == "primary":
                    continue
                
                alternate_names.append(name_value)
                
                # Check if language attribute exists
                if "language" in name_elem.attrib:
                    lang = name_elem.get("language")
                    if lang == "ja" or lang == "jp" or lang == "jpn":
                        game["japanese_name"] = name_value
            
            if alternate_names:
                game["alternate_names"] = alternate_names
                
                # If Japanese title not found yet
                if "japanese_name" not in game:
                    # Look for strings containing Japanese characters
                    for alt_name in alternate_names:
                        # Check if contains hiragana or katakana (more reliable Japanese detection)
                        has_japanese = any(
                            '\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF'
                            for c in alt_name
                        )
                        if has_japanese:
                            game["japanese_name"] = alt_name
                            break
            
            # Get year published
            year_element = item.find(".//yearpublished")
            if year_element is not None:
                game["year_published"] = year_element.get("value")
            
            # Get thumbnail URL
            thumbnail_element = item.find(".//thumbnail")
            if thumbnail_element is not None and thumbnail_element.text:
                game["thumbnail_url"] = thumbnail_element.text
            
            # Get publisher settings for player count
            minplayers_element = item.find(".//minplayers")
            if minplayers_element is not None:
                game["publisher_min_players"] = minplayers_element.get("value")
                
            maxplayers_element = item.find(".//maxplayers")
            if maxplayers_element is not None:
                game["publisher_max_players"] = maxplayers_element.get("value")
                
            # Get publisher playing time
            playtime_element = item.find(".//playingtime")
            if playtime_element is not None:
                game["playing_time"] = playtime_element.get("value")
                
            # Get publisher recommended age
            age_element = item.find(".//minage")
            if age_element is not None:
                game["publisher_min_age"] = age_element.get("value")
                
            # Get BGG community recommended player count
            poll = item.findall(".//poll[@name='suggested_numplayers']/results")
            community_players = {"best": [], "recommended": [], "not_recommended": []}
            
            for numplayer_result in poll:
                num_players = numplayer_result.get("numplayers")
                
                # Find most voted recommendation
                best_votes = 0
                best_recommendation = "not_recommended"
                
                for result in numplayer_result.findall("./result"):
                    vote_count = int(result.get("numvotes", "0"))
                    value = result.get("value")
                    
                    if vote_count > best_votes:
                        best_votes = vote_count
                        best_recommendation = value
                
                # Classify player count based on recommendation
                if best_recommendation == "Best":
                    community_players["best"].append(num_players)
                elif best_recommendation == "Recommended":
                    community_players["recommended"].append(num_players)
                elif best_recommendation == "Not Recommended":
                    community_players["not_recommended"].append(num_players)
            
            # Set best player count
            if community_players["best"]:
                # Sort if can be interpreted as numbers
                try:
                    community_players["best"] = sorted(
                        community_players["best"],
                        key=lambda x: float(x.replace("+", ""))
                    )
                except ValueError:
                    pass
                game["community_best_players"] = ", ".join(community_players["best"])
            
            if community_players["recommended"]:
                try:
                    community_players["recommended"] = sorted(
                        community_players["recommended"],
                        key=lambda x: float(x.replace("+", ""))
                    )
                except ValueError:
                    pass
                game["community_recommended_players"] = ", ".join(
                    community_players["recommended"]
                )
            
            # Get BGG community recommended age
            suggested_age_poll = item.find(".//poll[@name='suggested_playerage']")
            if suggested_age_poll is not None:
                age_results = suggested_age_poll.findall("./results/result")
                best_age_votes = 0
                community_age = None
                
                for age_result in age_results:
                    vote_count = int(age_result.get("numvotes", "0"))
                    age_value = age_result.get("value")
                    
                    if vote_count > best_age_votes:
                        best_age_votes = vote_count
                        community_age = age_value
                
                if community_age:
                    game["community_min_age"] = community_age
            
            # Get description
            description_element = item.find(".//description")
            if description_element is not None and description_element.text:
                game["description"] = description_element.text
            
            # Get mechanics (game types)
            mechanics = []
            for mechanic in item.findall(".//link[@type='boardgamemechanic']"):
                mechanics.append({
                    "id": mechanic.get("id"),
                    "name": mechanic.get("value")
                })
            game["mechanics"] = mechanics
            
            # Get categories
            categories = []
            for category in item.findall(".//link[@type='boardgamecategory']"):
                categories.append({
                    "id": category.get("id"),
                    "name": category.get("value")
                })
            game["categories"] = categories
            
            # Get designer information
            designers = []
            for designer in item.findall(".//link[@type='boardgamedesigner']"):
                designers.append({
                    "id": designer.get("id"),
                    "name": designer.get("value")
                })
            game["designers"] = designers
            
            # Get publisher information
            publishers = []
            for publisher in item.findall(".//link[@type='boardgamepublisher']"):
                publishers.append({
                    "id": publisher.get("id"),
                    "name": publisher.get("value")
                })
            game["publishers"] = publishers
            
            # Get rating information
            ratings = item.find(".//ratings")
            if ratings is not None:
                avg_rating = ratings.find(".//average")
                if avg_rating is not None:
                    game["average_rating"] = avg_rating.get("value")
                
                # Get weight (complexity)
                weight_element = ratings.find(".//averageweight")
                if weight_element is not None:
                    game["weight"] = weight_element.get("value")
                
                # Ranking information
                ranks = []
                for rank in ratings.findall(".//rank"):
                    if rank.get("value") != "Not Ranked":
                        ranks.append({
                            "type": rank.get("name"),
                            "id": rank.get("id"),
                            "rank": rank.get("value")
                        })
                game["ranks"] = ranks
        
        return game
    else:
        logger.error(f"Error: Status code {response.status_code}")
        return None

def save_game_data_to_yaml(game_data, custom_filename=None):
    """Save game data to YAML file"""
    # Generate filename
    game_id = game_data.get('id', 'unknown')
    
    # Pad game ID to 6 digits
    if game_id != 'unknown' and game_id.isdigit():
        game_id = game_id.zfill(6)  # Left-pad with zeros to 6 digits
    
    # Use Japanese name if available
    game_name = game_data.get('japanese_name', game_data.get('name', '名称不明'))
    
    # Convert full-width spaces to half-width spaces
    game_name = game_name.replace('　', ' ')
    
    # Placeholder filename
    placeholder_filename = f"{game_id}_{game_name}.yaml"
    # Replace special characters
    placeholder_filename = placeholder_filename.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace(";", "_")
    
    # Process custom filename
    if not custom_filename:
        filename = placeholder_filename
    else:
        # Convert full-width spaces to half-width in custom filename
        custom_filename = custom_filename.replace('　', ' ')
        filename = custom_filename
        if not filename.endswith('.yaml'):
            filename += '.yaml'
    
    # Create data directory
    os.makedirs("game_data", exist_ok=True)
    file_path = os.path.join("game_data", filename)
    
    try:
        # Handle special characters in game name before converting to YAML
        game_data_safe = game_data.copy()

        # Remove top-level ID
        if 'id' in game_data_safe:
            del game_data_safe['id']

        # Remove IDs from nested elements
        for category in ['mechanics', 'categories', 'designers', 'publishers', 'ranks']:
            if (category in game_data_safe and isinstance(game_data_safe[category], list)):
                for item in game_data_safe[category]:
                    if 'id' in item:
                        del item['id']

        # Add learning curve analysis (implemented without Streamlit dependencies)
        if ('learning_analysis' not in game_data_safe and 
            'description' in game_data_safe and 
            'mechanics' in game_data_safe and 
            'weight' in game_data_safe):
            try:
                # Use independent module for learning curve analysis
                from learning_curve_for_daily_update import calculate_learning_curve
                game_data_safe['learning_analysis'] = calculate_learning_curve(game_data_safe)
                logger.info(f"Added learning curve analysis for game ID {game_id}")
            except Exception as e:
                logger.warning(f"Error calculating learning curve: {str(e)}")
        
        # Convert full-width spaces to half-width before saving to YAML
        def replace_fullwidth_spaces(obj):
            if isinstance(obj, str):
                return obj.replace('　', ' ')
            elif isinstance(obj, dict):
                return {k: replace_fullwidth_spaces(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_fullwidth_spaces(item) for item in obj]
            else:
                return obj
        
        game_data_safe = replace_fullwidth_spaces(game_data_safe)
        
        # Convert to YAML and save
        with open(file_path, 'w', encoding='utf-8') as file:
            yaml.dump(game_data_safe, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return True, file_path, None
    except Exception as e:
        logger.error(f"File save error: {str(e)}")
        return False, None, str(e)

def setup_directories():
    """Create necessary directories"""
    GAME_DATA_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)

def backup_game_data():
    """
    Backup game_data folder
    
    Returns:
    tuple: (success flag, backup directory path)
    """
    today = datetime.datetime.now()
    backup_folder_name = today.strftime('%y%m%d')
    
    backup_dir = BACKUP_DIR / backup_folder_name
    
    # Check if game_data folder exists
    if not GAME_DATA_DIR.exists():
        logger.warning(f"Game data folder not found: {GAME_DATA_DIR}")
        return False, None
    
    # Create backup folder
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup game_data contents
    file_count = 0
    for file in GAME_DATA_DIR.glob('*.yaml'):
        shutil.copy2(file, backup_dir)
        file_count += 1
    
    logger.info(f"Backed up {file_count} YAML files to: {backup_dir}")
    
    return True, backup_dir

def get_game_ids_from_local():
    """Extract game IDs from local YAML files and return them"""
    game_ids = []
    
    # Find YAML files in game_data folder
    yaml_files = list(GAME_DATA_DIR.glob('*.yaml'))
    
    if not yaml_files:
        logger.warning(f"No YAML files found: {GAME_DATA_DIR}")
        return []
    
    for yaml_file in yaml_files:
        # Extract game ID from filename (e.g. "000013_カタンの開拓者.yaml")
        match = re.match(r"(\d+)_(.*?)\.yaml", yaml_file.name)
        if match:
            game_id = match.group(1)
            if game_id:
                game_ids.append(game_id)
    
    logger.info(f"Retrieved {len(game_ids)} game IDs from local files")
    return game_ids

def get_file_content(file_path):
    """Get file content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"File read error: {str(e)}")
        return ""

def check_config_updated():
    """
    Check if config files have been updated
    Output changes to log if updates are found
    
    Returns:
    tuple: (update flag, update description)
    """
    updated = False
    update_details = []
    
    # Find previous backup (most recent)
    previous_backups = sorted([d for d in BACKUP_DIR.glob('*') if d.is_dir()], reverse=True)
    if not previous_backups:
        logger.info("No previous backup found. Considering this as first run.")
        return False, "First run"
    
    # Get most recent backup directory
    last_backup = previous_backups[0]
    last_config_backup = last_backup / 'config'
    
    # If previous backup doesn't have config folder
    if not last_config_backup.exists():
        logger.info("No config folder in previous backup")
        return False, "No previous config backup"
    
    # Compare each config file
    for file in CONFIG_DIR.glob('*.yaml'):
        old_file = last_config_backup / file.name
        
        if not old_file.exists():
            # New file added
            updated = True
            update_details.append(f"New file added: {file.name}")
            continue
        
        # Compare file contents
        old_content = get_file_content(old_file)
        new_content = get_file_content(file)
        
        if old_content != new_content:
            updated = True
            
            # Get diff to record changes in detail
            diff = list(difflib.unified_diff(
                old_content.splitlines(),
                new_content.splitlines(),
                fromfile=str(old_file),
                tofile=str(file),
                lineterm=''
            ))
            
            update_details.append(f"File changed: {file.name}")
            for line in diff[:20]:  # Show only first 20 lines of diff (prevent too long output)
                update_details.append(f"  {line}")
            
            if len(diff) > 20:
                update_details.append(f"  ... {len(diff) - 20} more lines changed")
    
    # Find files that exist in CONFIG_DIR but not in last_config_backup (newly added)
    for old_file in last_config_backup.glob('*.yaml'):
        new_file = CONFIG_DIR / old_file.name
        if not new_file.exists():
            updated = True
            update_details.append(f"File deleted: {old_file.name}")
    
    return updated, "\n".join(update_details)

def backup_config_files(backup_dir):
    """
    Backup current config files
    
    Parameters:
    backup_dir (Path): Backup directory
    """
    config_backup_dir = backup_dir / 'config'
    config_backup_dir.mkdir(exist_ok=True)
    
    for file in CONFIG_DIR.glob('*.yaml'):
        shutil.copy2(file, config_backup_dir)
    
    logger.info(f"Config files backed up to: {config_backup_dir}")

def update_game_data(game_ids):
    """Update game data"""
    success_count = 0
    error_count = 0
    
    for i, game_id in enumerate(game_ids):
        try:
            logger.info(f"Retrieving game data ({i+1}/{len(game_ids)}): {game_id}")
            
            # Get game details from BGG API
            game_details = get_game_details(game_id)
            
            if not game_details:
                logger.warning(f"Could not retrieve details for game ID {game_id}")
                error_count += 1
                continue
            
            # Save to YAML file
            success, file_path, error_msg = save_game_data_to_yaml(game_details)
            
            if success:
                logger.info(f"Saved information for game ID {game_id}: {file_path}")
                success_count += 1
            else:
                logger.error(f"Failed to save game ID {game_id}: {error_msg}")
                error_count += 1
            
            # Additional wait time for safety (although rate_limiter should be implemented)
            time.sleep(1)
        
        except Exception as e:
            logger.error(f"Error processing game ID {game_id}: {e}")
            error_count += 1
    
    return success_count, error_count

def main():
    """Main process"""
    logger.info("Starting daily update process")
    
    try:
        # Create necessary directories
        setup_directories()
        
        # Backup data
        backup_success, backup_dir = backup_game_data()
        if not backup_success:
            logger.error("Backup process failed")
            return
        
        # Check if config files have been updated
        config_updated, update_details = check_config_updated()
        
        # Backup config files (always perform)
        backup_config_files(backup_dir)
        
        # Record details to log if config was updated
        if config_updated:
            logger.info("Config files have been updated:")
            logger.info(update_details)
            
            # Create marker file in backup folder
            config_update_marker = backup_dir / 'CONFIG_UPDATED.txt'
            with open(config_update_marker, 'w', encoding='utf-8') as f:
                f.write(f"Config files updated on {datetime.datetime.now()}\n\n")
                f.write(update_details)
            
            logger.info(f"Created config update marker file: {config_update_marker}")
        
        # Get game IDs from local YAML files
        game_ids = get_game_ids_from_local()
        if not game_ids:
            logger.error("Could not retrieve game IDs from local files")
            return
        
        # Update game data
        success_count, error_count = update_game_data(game_ids)
        logger.info(f"Data update complete - Success: {success_count}, Failed: {error_count}")
        
        logger.info("Daily update process completed")
    
    except Exception as e:
        logger.error(f"Unexpected error occurred during processing: {e}")

if __name__ == "__main__":
    main()