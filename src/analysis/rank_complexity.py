import os
import yaml
import math

# Path to YAML file
RANK_COMPLEXITY_FILE = "config/rank_complexity.yaml"

def load_rank_complexity_data():
    """
    Load ranking type complexity data from YAML file
    
    Returns:
    dict: Dictionary with ranking type as key and complexity as value
    """
    try:
        # Return empty dictionary if file doesn't exist
        if not os.path.exists(RANK_COMPLEXITY_FILE):
            return {}
        
        with open(RANK_COMPLEXITY_FILE, 'r', encoding='utf-8') as file:
            complexity_data = yaml.safe_load(file)
            
        # Return empty dictionary if None
        if complexity_data is None:
            return {}
            
        return complexity_data
    except Exception as e:
        # Return error info without directly displaying error message
        print(f"Error loading ranking complexity data: {str(e)}")
        return {}

def save_rank_complexity_data(complexity_data):
    """
    Save ranking type complexity data to YAML file
    
    Parameters:
    complexity_data (dict): Dictionary with ranking type as key and complexity as value
    
    Returns:
    bool: Whether save was successful
    """
    try:
        with open(RANK_COMPLEXITY_FILE, 'w', encoding='utf-8') as file:
            yaml.dump(complexity_data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        print(f"Error saving ranking complexity data: {str(e)}")
        return False

def add_missing_rank_type(rank_type, default_complexity=3.0):
    """
    Add non-existent ranking type to YAML file
    
    Parameters:
    rank_type (str): Ranking type to add
    default_complexity (float): Default complexity value
    
    Returns:
    bool: Whether addition was successful
    """
    try:
        # Load current data
        complexity_data = load_rank_complexity_data()
        
        # Do nothing if already exists
        if rank_type in complexity_data:
            return True
        
        # Add if doesn't exist - Add in dictionary format to match new structure
        complexity_data[rank_type] = {
            'complexity': default_complexity,
            'strategic_value': 3.5,  # Default value
            'interaction_value': 3.2,  # Default value
            'description': f"Auto-added ranking type (default values)"
        }
        
        # Save
        return save_rank_complexity_data(complexity_data)
    except Exception as e:
        print(f"Error adding ranking type: {str(e)}")
        return False

def get_rank_complexity_value(rank_type, default_value=3.0):
    """
    Get complexity for specified ranking type
    Automatically adds to database and returns default value if not exists
    
    Parameters:
    rank_type (str): Ranking type to get complexity for
    default_value (float): Default value if not exists
    
    Returns:
    float: Ranking type complexity
    """
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