import os
import yaml
import math
from datetime import datetime, timedelta

# Path to YAML file
RANK_COMPLEXITY_FILE = "config/rank_complexity.yaml"

# Global variables for caching
_rank_cache = None
_rank_cache_timestamp = None
_rank_cache_ttl = timedelta(minutes=10)  # Cache validity period (10 minutes)

def load_rank_complexity_data(force_reload=False):
    """
    Load ranking type complexity data from YAML file
    Utilize cache to reduce number of reads

    Parameters:
    force_reload (bool): Force reload ignoring cache

    Returns:
    dict: Dictionary with ranking type as key and complexity as value
    """
    global _rank_cache, _rank_cache_timestamp

    current_time = datetime.now()

    # Return from cache if cache is valid
    if not force_reload and _rank_cache is not None and _rank_cache_timestamp is not None:
        if current_time - _rank_cache_timestamp < _rank_cache_ttl:
            return _rank_cache

    try:
        # Return empty dictionary if file doesn't exist
        if not os.path.exists(RANK_COMPLEXITY_FILE):
            _rank_cache = {}
            _rank_cache_timestamp = current_time
            return _rank_cache

        with open(RANK_COMPLEXITY_FILE, 'r', encoding='utf-8') as file:
            complexity_data = yaml.safe_load(file)

        # Return empty dictionary if None
        if complexity_data is None:
            complexity_data = {}

        # Update cache
        _rank_cache = complexity_data
        _rank_cache_timestamp = current_time

        return complexity_data
    except Exception as e:
        # Return error info without directly displaying error message
        print(f"Error loading ranking complexity data: {str(e)}")
        return {}

def save_rank_complexity_data(complexity_data):
    """
    Save ranking type complexity data to YAML file
    Update cache after save

    Parameters:
    complexity_data (dict): Dictionary with ranking type as key and complexity as value

    Returns:
    bool: Whether save was successful
    """
    global _rank_cache, _rank_cache_timestamp

    try:
        with open(RANK_COMPLEXITY_FILE, 'w', encoding='utf-8') as file:
            yaml.dump(complexity_data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)

        # Update cache
        _rank_cache = complexity_data
        _rank_cache_timestamp = datetime.now()

        return True
    except Exception as e:
        print(f"Error saving ranking complexity data: {str(e)}")
        return False


# Buffer for temporarily storing new rank type additions
_pending_rank_types = {}
_pending_rank_types_count = 0
_max_pending_rank_types = 10  # Batch save when this number is reached


def add_missing_rank_type(rank_type, default_complexity=3.0):
    """
    Add non-existent ranking type to buffer and batch save when buffer is full

    Parameters:
    rank_type (str): Ranking type to add
    default_complexity (float): Default complexity value

    Returns:
    bool: Whether addition was successful
    """
    global _pending_rank_types, _pending_rank_types_count

    try:
        # Load current data (from cache)
        complexity_data = load_rank_complexity_data()

        # Do nothing if already exists
        if rank_type in complexity_data:
            return True

        # Do nothing if already in buffer
        if rank_type in _pending_rank_types:
            return True

        # Add to buffer
        _pending_rank_types[rank_type] = {
            'complexity': default_complexity,
            'strategic_value': 3.5,
            'interaction_value': 3.2,
            'description': f"Auto-added ranking type (default values)"
        }

        _pending_rank_types_count += 1

        # Batch save when buffer is full
        if _pending_rank_types_count >= _max_pending_rank_types:
            return _save_pending_rank_types()

        return True
    except Exception as e:
        print(f"Error adding ranking type: {str(e)}")
        return False


def _save_pending_rank_types():
    """Batch save all pending rank types in buffer"""
    global _pending_rank_types, _pending_rank_types_count

    if _pending_rank_types_count == 0:
        return True

    try:
        # Load current data (force reload)
        complexity_data = load_rank_complexity_data(force_reload=True)

        # Add buffer contents
        for rank_type, rank_data in _pending_rank_types.items():
            if rank_type not in complexity_data:
                complexity_data[rank_type] = rank_data

        # Save
        success = save_rank_complexity_data(complexity_data)

        if success:
            # Clear buffer
            _pending_rank_types = {}
            _pending_rank_types_count = 0

        return success
    except Exception as e:
        print(f"Error saving pending rank types: {str(e)}")
        return False


def flush_pending_rank_types():
    """Save all pending rank types"""
    return _save_pending_rank_types()

def get_rank_complexity_value(rank_type, default_value=3.0):
    """
    Get complexity for specified ranking type
    Get from cache and add to buffer if doesn't exist

    Parameters:
    rank_type (str): Ranking type to get complexity for
    default_value (float): Default value if not exists

    Returns:
    float: Ranking type complexity
    """
    # Check buffer first
    global _pending_rank_types

    if rank_type in _pending_rank_types:
        pending_data = _pending_rank_types[rank_type]
        if isinstance(pending_data, dict) and 'complexity' in pending_data:
            return pending_data['complexity']
        elif isinstance(pending_data, (int, float)):
            return pending_data
        else:
            return default_value

    complexity_data = load_rank_complexity_data()
    
    # Check if ranking type exists
    if rank_type in complexity_data:
        # New structure: complexity_data[rank_type] is a dictionary
        # with a 'complexity' key inside
        if isinstance(complexity_data[rank_type], dict) and 'complexity' in complexity_data[rank_type]:
            return complexity_data[rank_type]['complexity']
        # Support backward compatibility if value is stored directly
        elif isinstance(complexity_data[rank_type], (int, float)):
            return complexity_data[rank_type]
        # Return default value if neither case
        else:
            return default_value
    
    # Add and save if doesn't exist
    add_missing_rank_type(rank_type, default_value)
    
    return default_value

def calculate_rank_position_score(rank_value):
    """
    Calculate game popularity/quality score from ranking position
    Higher positions (smaller numbers) result in higher popularity/quality scores
    
    Parameters:
    rank_value (int or str): Ranking position
    
    Returns:
    float: Popularity/quality score based on ranking position (range 1.0-5.0)
    """
    try:
        # Convert position to integer
        rank = int(rank_value)
        
        # Calculate score on logarithmic scale (higher positions get higher scores)
        if rank <= 10:
            # Top 10 gets highest rating
            score = 5.0
        elif rank <= 100:
            # Top 100 gets very high rating
            score = 4.5 - (rank - 10) / 90 * 0.5  # 4.5 to 4.0
        elif rank <= 1000:
            # Top 1000 gets high rating
            score = 4.0 - (rank - 100) / 900 * 1.0  # 4.0 to 3.0
        elif rank <= 5000:
            # Top 5000 gets moderate rating
            score = 3.0 - (rank - 1000) / 4000 * 1.0  # 3.0 to 2.0
        else:
            # Below 5000 gets low rating
            score = max(1.0, 2.0 - math.log10(rank / 5000))  # 2.0 to 1.0
        
        return score
    except (ValueError, TypeError):
        # Return default value if cannot convert to number
        return 2.5

def calculate_rank_complexity(ranks):
    """
    Calculate complexity score from ranking information
    Primarily considers ranking type complexity, with position as secondary factor
    
    Parameters:
    ranks (list): List of ranking information
    
    Returns:
    float: Ranking-based complexity score (range 1.0-5.0)
    """
    if not ranks:
        return 3.0  # Default value
    
    # Calculate score for each ranking type
    rank_scores = []
    for rank_info in ranks:
        rank_type = rank_info.get('type', 'boardgame')
        rank_value = rank_info.get('rank')
        
        if rank_value and rank_value != "Not Ranked":
            # Popularity/quality score from position
            popularity_score = calculate_rank_position_score(rank_value)
            
            # Ranking type complexity (baseline value)
            type_complexity = get_rank_complexity_value(rank_type)
            
            # Complexity evaluation is mainly based on ranking type
            # Position influence is minimal (20%)
            # Reflects tendency that higher rankings slightly increase complexity, but not primary factor
            adjusted_score = (type_complexity * 0.8 + (popularity_score - 3.0) * 0.2)
            
            # Weight by ranking type importance (boardgame is 1.0, others are type-specific)
            weight = 1.0
            if rank_type == "boardgame":
                weight = 1.0  # Overall ranking has standard weight
            elif rank_type in ["strategygames", "wargames"]:
                weight = 1.2  # Strategy games get increased weight
            elif rank_type in ["familygames", "partygames", "childrensgames"]:
                weight = 0.8  # Casual games get decreased weight
            
            # Add weighted score
            rank_scores.append((adjusted_score, weight))
    
    # Return default value if no scores
    if not rank_scores:
        return 3.0
        
    # Calculate weighted average
    total_weighted_score = sum(score * weight for score, weight in rank_scores)
    total_weight = sum(weight for _, weight in rank_scores)
    
    avg_score = total_weighted_score / total_weight
    
    # Limit to 1.0-5.0 range
    return min(5.0, max(1.0, avg_score))