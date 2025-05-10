import yaml
import numpy as np
import os
import glob
import pickle
import voyageai
from sklearn.metrics.pairwise import cosine_similarity
import argparse
from tqdm import tqdm
from typing import Dict, List, Any, Tuple
import asyncio
from dotenv import load_dotenv
import hashlib
import time
import random

# Load environment variables
load_dotenv()

def parse_args() -> argparse.Namespace:
    """Function to parse command line arguments"""
    parser = argparse.ArgumentParser(description='Calculate and save embeddings for board game data')
    parser.add_argument('--model', default='voyage-3-large', 
                      help='Embedding model name (default: voyage-3-large)')
    parser.add_argument('--data_path', default='game_data/*.yaml', 
                      help='Game data path (glob format)')
    parser.add_argument('--output', default='game_embeddings.pkl', 
                      help='Output filename')
    parser.add_argument('--batch_size', type=int, default=128, 
                      help='API request batch size (default: 128)')
    parser.add_argument('--max_retries', type=int, default=5,
                      help='Number of retries on API request failure (default: 5)')
    parser.add_argument('--request_interval', type=float, default=0.5,
                      help='Wait time between requests (seconds, default: 0.5)')
    parser.add_argument('--timeout', type=int, default=15,
                      help='API request timeout (seconds, default: 15)')
    parser.add_argument('--limit', type=int, default=0,
                      help='Maximum number of files to process (0=process all)')
    parser.add_argument('--skip', type=int, default=0,
                      help='Number of files to skip processing')
    parser.add_argument('--resume', action='store_true',
                      help='Resume previous processing from where it stopped (if intermediate files exist)')
    parser.add_argument('--force', action='store_true',
                      help='Force processing even if YAML files have not changed')
    parser.add_argument('--max_tokens_per_item', type=int, default=3000,
                      help='Maximum tokens per item (default: 3000)')
    parser.add_argument('--max_tokens_per_batch', type=int, default=100000,
                      help='Maximum tokens per batch (default: 100000)')
    parser.add_argument('--api_key', 
                      help='Voyage AI API key (direct specification instead of .env file)')
    return parser.parse_args()

def load_game_data(file_path: str) -> Dict[str, Any]:
    """Function to load game data from YAML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return {}

def estimate_tokens(text: str) -> int:
    """Function to more accurately estimate token count (upwardly adjusted version)"""
    # Increase estimation coefficient from 1.3 to 1.8 for safety margin
    words = len(text.split())
    punctuation = sum(1 for char in text if char in ".,;:!?-()[]{}\"'")
    # Consider special characters, numbers, and spaces
    special_chars = sum(1 for char in text if not char.isalnum() and not char.isspace() and char not in ".,;:!?-()[]{}\"'")
    
    # Conservative estimation
    estimated_tokens = int(words * 1.8) + punctuation + special_chars
    
    # Add 20% additional safety margin
    return int(estimated_tokens * 1.2)

def truncate_text_to_token_limit(text: str, max_tokens: int = 3000) -> str:
    """Function to truncate text to below maximum token count"""
    if estimate_tokens(text) <= max_tokens:
        return text
    
    # Split into paragraphs
    paragraphs = text.split('\n')
    result = []
    current_tokens = 0
    
    # Prioritize important information (name, categories, mechanics, etc.)
    priority_keywords = [
        "Board Game Name:", 
        "Japanese Title:", 
        "Game Categories:", 
        "Game Mechanics:", 
        "Strategic Depth:", 
        "Game Complexity"
    ]
    
    # Add priority items first
    for para in paragraphs:
        for keyword in priority_keywords:
            if keyword in para:
                result.append(para)
                current_tokens += estimate_tokens(para)
                break
    
    # Add remaining items (within token limit)
    for para in paragraphs:
        # Skip priority items already added
        if any(keyword in para for keyword in priority_keywords):
            continue
            
        para_tokens = estimate_tokens(para)
        if current_tokens + para_tokens <= max_tokens:
            result.append(para)
            current_tokens += para_tokens
        elif "Game Description:" in para:
            # For long descriptions, get only part of it
            words = para.split()
            desc_prefix = " ".join(words[:30])  # First 30 words only
            desc_prefix += "... (description truncated)"
            desc_tokens = estimate_tokens(desc_prefix)
            
            if current_tokens + desc_tokens <= max_tokens:
                result.append(desc_prefix)
                current_tokens += desc_tokens
    
    return '\n'.join(result)

def create_game_text(game_data: Dict[str, Any]) -> str:
    """Function to create text for embedding from game data (complete version with all items)"""
    text = f"Board Game Name: {game_data.get('name', '')}\n"
    
    # Add alternate names
    if 'alternate_names' in game_data and game_data['alternate_names']:
        if isinstance(game_data['alternate_names'], list):
            alt_names = ', '.join([str(name) for name in game_data['alternate_names'] if name])
            text += f"Alternative Names: {alt_names}\n"
    
    # Add Japanese name
    if 'japanese_name' in game_data and game_data['japanese_name']:
        text += f"Japanese Title: {game_data.get('japanese_name', '')}\n"
    
    # Add game description
    text += f"Game Description: {game_data.get('description', '')}\n"
    
    # Add year published
    if 'year_published' in game_data:
        text += f"Year Published: {game_data.get('year_published', '')}\n"
    
    # Add thumbnail URL
    if 'thumbnail_url' in game_data and game_data['thumbnail_url']:
        text += f"Thumbnail URL: {game_data.get('thumbnail_url', '')}\n"
    
    # Player count information (publisher recommended)
    if 'publisher_min_players' in game_data and 'publisher_max_players' in game_data:
        text += f"Publisher Recommended Players: {game_data.get('publisher_min_players', '')} to {game_data.get('publisher_max_players', '')} players\n"
    
    # Add playing time
    if 'playing_time' in game_data:
        text += f"Average Playing Time: {game_data.get('playing_time', '')} minutes\n"
    
    # Add recommended age (publisher)
    if 'publisher_min_age' in game_data:
        text += f"Publisher Recommended Minimum Age: {game_data.get('publisher_min_age', '')} years\n"
    
    # Community best player count
    if 'community_best_players' in game_data and game_data['community_best_players']:
        text += f"Community Best Player Count: {game_data.get('community_best_players', '')}\n"
    
    # Community recommended player count
    if 'community_recommended_players' in game_data and game_data['community_recommended_players']:
        if isinstance(game_data['community_recommended_players'], list):
            rec_players = ', '.join([str(count) for count in game_data['community_recommended_players']])
        else:
            rec_players = str(game_data['community_recommended_players'])
        text += f"Community Recommended Player Counts: {rec_players}\n"
    
    # Community recommended minimum age
    if 'community_min_age' in game_data:
        text += f"Community Recommended Minimum Age: {game_data.get('community_min_age', '')} years\n"
    
    # Add categories
    if 'categories' in game_data and isinstance(game_data['categories'], list):
        categories = [cat.get('name', '') for cat in game_data['categories'] 
                     if isinstance(cat, dict) and 'name' in cat]
        text += f"Game Categories: {', '.join(categories)}\n"
    
    # Add mechanics
    if 'mechanics' in game_data and isinstance(game_data['mechanics'], list):
        mechanics = [mech.get('name', '') for mech in game_data['mechanics'] 
                    if isinstance(mech, dict) and 'name' in mech]
        text += f"Game Mechanics: {', '.join(mechanics)}\n"
    
    # Add designers
    if 'designers' in game_data and isinstance(game_data['designers'], list):
        designers = [des.get('name', '') for des in game_data['designers'] 
                    if isinstance(des, dict) and 'name' in des]
        text += f"Game Designers: {', '.join(designers)}\n"
    
    # Add publishers
    if 'publishers' in game_data and isinstance(game_data['publishers'], list):
        publishers = [pub.get('name', '') for pub in game_data['publishers'] 
                     if isinstance(pub, dict) and 'name' in pub]
        text += f"Publishers: {', '.join(publishers)}\n"
    
    # Add rating and weight
    if 'average_rating' in game_data:
        text += f"Average Rating: {game_data.get('average_rating', '')}\n"
    
    if 'weight' in game_data:
        text += f"Game Complexity (Weight): {game_data.get('weight', '')} on a scale of 1-5\n"
    
    # Add ranking information
    if 'ranks' in game_data and isinstance(game_data['ranks'], list):
        for rank_info in game_data['ranks']:
            if isinstance(rank_info, dict) and 'type' in rank_info and 'rank' in rank_info:
                text += f"Rank ({rank_info.get('type', '')}): {rank_info.get('rank', '')}\n"
    
    # Add learning analysis data
    if 'learning_analysis' in game_data and isinstance(game_data['learning_analysis'], dict):
        learning = game_data['learning_analysis']
        
        # Basic learning analysis data
        if 'initial_barrier' in learning:
            text += f"Learning Barrier: {learning.get('initial_barrier', '')} on a scale of 1-5\n"
        
        if 'strategic_depth' in learning:
            text += f"Strategic Depth: {learning.get('strategic_depth', '')} on a scale of 1-5\n"
        
        if 'strategic_depth_description' in learning:
            text += f"Strategic Depth Description: {learning.get('strategic_depth_description', '')}\n"
        
        if 'replayability' in learning:
            text += f"Replayability: {learning.get('replayability', '')} on a scale of 1-5\n"
        
        if 'mechanics_complexity' in learning:
            text += f"Mechanics Complexity: {learning.get('mechanics_complexity', '')} on a scale of 1-5\n"
        
        if 'learning_curve_type' in learning:
            text += f"Learning Curve Type: {learning.get('learning_curve_type', '')}\n"
        
        if 'decision_points' in learning:
            text += f"Decision Points: {learning.get('decision_points', '')}\n"
        
        if 'interaction_complexity' in learning:
            text += f"Interaction Complexity: {learning.get('interaction_complexity', '')}\n"
        
        if 'rules_complexity' in learning:
            text += f"Rules Complexity: {learning.get('rules_complexity', '')}\n"
        
        # Add player type information
        if 'player_types' in learning and isinstance(learning['player_types'], list):
            text += f"Suitable Player Types: {', '.join(learning['player_types'])}\n"
        
        # Add playtime analysis
        if 'playtime_analysis' in learning and isinstance(learning['playtime_analysis'], dict):
            pta = learning['playtime_analysis']
            for key, value in pta.items():
                text += f"Playtime Analysis - {key}: {value}\n"
        
        # Add mastery time
        if 'mastery_time' in learning:
            text += f"Time to Master: {learning.get('mastery_time', '')}\n"
    
    # Truncate text to fit within token limit
    return text

def save_temp_result(embeddings, last_index, filename="temp_embeddings.pkl"):
    """Function to save temporary results"""
    try:
        with open(filename, 'wb') as f:
            pickle.dump({
                'embeddings': embeddings,
                'last_index': last_index
            }, f)
        print(f"Saved temporary results to {filename} (index: {last_index})")
    except Exception as e:
        print(f"Failed to save temporary file: {e}")

def load_temp_result(filename="temp_embeddings.pkl"):
    """Function to load temporary results"""
    if os.path.exists(filename):
        try:
            with open(filename, 'rb') as f:
                data = pickle.load(f)
            print(f"Loaded temporary results from {filename} (index: {data.get('last_index', 0)})")
            return data.get('embeddings', []), data.get('last_index', 0)
        except Exception as e:
            print(f"Failed to load temporary file: {e}")
    return [], 0

def get_file_hash(file_path: str) -> str:
    """Function to calculate file hash"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        # If file cannot be read, hash current time
        return hashlib.md5(str(time.time()).encode()).hexdigest()

def create_file_metadata(file_paths: List[str]) -> Dict[str, str]:
    """Function to create file metadata (hash values)"""
    metadata = {}
    for file_path in file_paths:
        metadata[file_path] = get_file_hash(file_path)
    return metadata

def load_previous_metadata(output_file: str) -> Dict[str, Any]:
    """Function to load metadata from previous processing results"""
    if not os.path.exists(output_file):
        return {}
        
    try:
        with open(output_file, 'rb') as f:
            data = pickle.load(f)
            return data.get('metadata', {})
    except Exception as e:
        print(f"Error loading previous processing results: {e}")
        return {}

def check_files_changed(new_metadata: Dict[str, str], old_metadata: Dict[str, str]) -> bool:
    """Function to check if files have changed"""
    # True if number of files changed
    if len(new_metadata) != len(old_metadata):
        return True
    
    # Compare hash values
    for file_path, hash_value in new_metadata.items():
        if file_path not in old_metadata or old_metadata[file_path] != hash_value:
            return True
    
    return False

async def get_embeddings_with_backoff(
    client,
    batch_texts: List[str],
    model: str,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.1
) -> List[List[float]]:
    """Function to get embeddings asynchronously using exponential backoff"""
    delay = initial_delay
    
    for retry in range(max_retries):
        try:
            # Get embeddings
            response = await client.embed(batch_texts, model=model)
            
            # Handle new API response format
            if hasattr(response, 'embeddings'):
                return response.embeddings
            else:
                # Old response format (just in case)
                return [item for item in response]
                
        except Exception as e:
            # Raise exception on last retry
            if retry == max_retries - 1:
                print(f"Maximum retries reached: {e}")
                # Propagate error up
                raise e
            
            # Calculate wait time with jitter
            jitter_amount = random.uniform(-jitter, jitter) * delay
            wait_time = delay + jitter_amount
            
            print(f"Error occurred: {e}. Retrying in {wait_time:.2f} seconds (retry {retry+1}/{max_retries})")
            await asyncio.sleep(wait_time)
            
            # Increase wait time for next retry
            delay *= backoff_factor

async def get_embeddings(
    texts: List[str],
    model: str,
    batch_size: int,
    max_retries: int,
    request_interval: float,
    timeout: int,
    resume: bool,
    max_tokens_per_item: int = 3000,
    max_tokens_per_batch: int = 100000,
    api_key: str = None
) -> List[List[float]]:
    """Function to get embeddings asynchronously (with token limit support)"""
    # Get API key from environment variable
    if api_key is None:
        api_key = os.getenv("VOYAGE_API_KEY")
    
    if not api_key:
        print("VOYAGE_API_KEY is not set")
        raise ValueError("API key is not set")
        
    client = voyageai.AsyncClient(api_key=api_key, max_retries=max_retries, timeout=timeout)
    
    all_embeddings = []
    start_idx = 0
    
    # Load intermediate results if resuming
    if resume:
        all_embeddings, start_idx = load_temp_result()
    
    # Truncate texts to fit within token limit
    truncated_texts = [truncate_text_to_token_limit(text, max_tokens_per_item) for text in texts]
    
    # Reduce default batch size by half (for safety)
    initial_batch_size = max(1, batch_size // 2)
    
    i = start_idx
    while i < len(truncated_texts):
        # Start with small batch size
        current_batch_size = initial_batch_size
        batch_end = min(i + current_batch_size, len(truncated_texts))
        batch_texts = truncated_texts[i:batch_end]
        
        # Estimate batch token count
        batch_tokens = sum(estimate_tokens(text) for text in batch_texts)
        
        # Adjust batch size if tokens exceed limit
        while batch_tokens > max_tokens_per_batch * 0.8 and current_batch_size > 1:  # Use 80% threshold
            current_batch_size = max(1, current_batch_size // 2)
            batch_end = min(i + current_batch_size, len(truncated_texts))
            batch_texts = truncated_texts[i:batch_end]
            batch_tokens = sum(estimate_tokens(text) for text in batch_texts)
        
        print(f"Batch {i//initial_batch_size + 1}: Size {len(batch_texts)}, Estimated tokens {batch_tokens}")
        
        # Get embeddings with exponential backoff
        try:
            batch_embeddings = await get_embeddings_with_backoff(
                client,
                batch_texts,
                model,
                max_retries
            )
            
            all_embeddings.extend(batch_embeddings)
            
            # Save intermediate results
            save_temp_result(all_embeddings, i + len(batch_texts))
            
        except Exception as e:
            print(f"Error occurred during batch processing: {e}")
            # Reduce batch size further and retry on error
            if current_batch_size > 1:
                print(f"Retrying with reduced batch size from {current_batch_size} to {max(1, current_batch_size // 2)}")
                continue
            else:
                # Process texts individually if batch size is 1
                print("Processing texts individually")
                for single_text in batch_texts:
                    try:
                        single_embedding = await get_embeddings_with_backoff(
                            client,
                            [single_text],
                            model,
                            max_retries
                        )
                        all_embeddings.extend(single_embedding)
                        save_temp_result(all_embeddings, i + 1)
                        i += 1
                    except Exception as single_error:
                        print(f"Error processing individual text: {single_error}")
                        # Add zero vector on error
                        all_embeddings.append([0.0] * 1024)  # voyage-3-large has 1024 dimensions
                        save_temp_result(all_embeddings, i + 1)
                        i += 1
                continue
        
        # Wait before next request (rate limiting)
        if i + len(batch_texts) < len(truncated_texts):
            print(f"Waiting {request_interval} seconds before next request...")
            await asyncio.sleep(request_interval)
        
        i += len(batch_texts)
    
    return all_embeddings

def calculate_similarity_matrix(embeddings_array: np.ndarray) -> np.ndarray:
    """Function to calculate similarity matrix from embeddings"""
    print("Calculating similarity matrix...")
    return cosine_similarity(embeddings_array)

def save_results(
    output_file: str,
    games: List[Dict[str, Any]],
    game_data_list: List[Dict[str, Any]],
    embeddings_array: np.ndarray,
    similarity_matrix: np.ndarray,
    file_metadata: Dict[str, str]
) -> None:
    """Function to save results to file"""
    print(f"Saving results to {output_file}...")
    try:
        with open(output_file, 'wb') as f:
            pickle.dump({
                'games': games,
                'game_data_list': game_data_list,
                'embeddings': embeddings_array,
                'similarity_matrix': similarity_matrix,
                'metadata': file_metadata  # Save file metadata
            }, f)
        print("Saving completed")
        
        # Delete temporary file
        if os.path.exists("temp_embeddings.pkl"):
            os.remove("temp_embeddings.pkl")
            print("Deleted temporary file")
    except Exception as e:
        print(f"Error during saving: {e}")

def process_game_files(file_paths: List[str], limit: int = 0, skip: int = 0) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """Function to process game files and extract data"""
    games = []
    game_data_list = []
    game_texts = []
    
    # Select target files (apply skip and limit)
    if skip > 0:
        print(f"Skipping first {skip} files")
        file_paths = file_paths[skip:]
    
    if limit > 0 and limit < len(file_paths):
        print(f"Limiting number of files to process to {limit}")
        file_paths = file_paths[:limit]
    
    print("Loading game data...")
    for file_path in tqdm(file_paths):
        game_data = load_game_data(file_path)
        if not game_data:
            continue
            
        game_name = game_data.get('name', os.path.basename(file_path))
        game_text = create_game_text(game_data)
        
        games.append({
            "name": game_name,
            "file": file_path,
            "japanese_name": game_data.get('japanese_name', '')
        })
        game_data_list.append(game_data)
        game_texts.append(game_text)
    
    print(f"Processed {len(games)} game data")
    return games, game_data_list, game_texts

def load_previous_results(output_file: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], np.ndarray, np.ndarray]:
    """Function to load previous processing results"""
    try:
        with open(output_file, 'rb') as f:
            data = pickle.load(f)
            return (
                data.get('games', []),
                data.get('game_data_list', []),
                data.get('embeddings', np.array([])),
                data.get('similarity_matrix', np.array([]))
            )
    except Exception as e:
        print(f"Error loading previous processing results: {e}")
        return [], [], np.array([]), np.array([])

async def main_async():
    """Main function (async version)"""
    try:
        args = parse_args()
        
        # Search for game files
        print(f"Searching for game data: {args.data_path}")
        game_files = glob.glob(args.data_path)
        print(f"Found {len(game_files)} files")
        
        if not game_files:
            print("No game files found. Please check data_path.")
            return
        
        # Create metadata for files
        current_metadata = create_file_metadata(game_files)
        
        # Load previous metadata
        previous_metadata = load_previous_metadata(args.output)
        
        # Check if files have changed
        files_changed = check_files_changed(current_metadata, previous_metadata)
        
        # Skip processing if no changes and force flag is off
        if not files_changed and not args.force and os.path.exists(args.output):
            print("No changes in YAML files, skipping processing.")
            print("Use --force option to force processing.")
            return
        
        # Continue processing if there are changes or force execution
        if files_changed:
            print("Changes detected in YAML files. Continuing processing.")
        elif args.force:
            print("Force execution with --force option.")
        
        # Process game data
        games, game_data_list, game_texts = process_game_files(game_files, args.limit, args.skip)
        
        if not games:
            print("No valid game data.")
            return
        
        # Display API key information (only first and last few characters for security)
        if args.api_key:
            masked_key = f"{args.api_key[:5]}...{args.api_key[-5:]}"
            print(f"API key: {masked_key}")
        
        # Get embeddings
        print(f"Calculating embeddings... Model: {args.model}, Batch size: {args.batch_size}")
        print(f"Max tokens per item: {args.max_tokens_per_item}, Max tokens per batch: {args.max_tokens_per_batch}")

        embeddings = await get_embeddings(
            game_texts, 
            args.model,
            args.batch_size,
            args.max_retries,
            args.request_interval,
            args.timeout,
            args.resume,
            args.max_tokens_per_item,
            args.max_tokens_per_batch,
            args.api_key
        )
        
        # Convert embeddings array to NumPy array
        embeddings_array = np.array(embeddings)
        
        # Calculate similarity matrix
        similarity_matrix = calculate_similarity_matrix(embeddings_array)
        
        # Save results (including metadata)
        save_results(args.output, games, game_data_list, embeddings_array, similarity_matrix, current_metadata)
        
        print(f"Processing completed. Generated {len(embeddings)} embeddings.")
        
    except Exception as e:
        print(f"Error occurred during program execution: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

def main() -> None:
    """Main function"""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()