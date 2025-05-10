"""
Module for analyzing learning curves from BoardGameGeek game data without Streamlit dependencies
Optimized for daily_update.py
"""

import datetime
import math
import os
import yaml

# Configuration file paths
CONFIG_DIR = "config"
MECHANICS_DATA_FILE = os.path.join(CONFIG_DIR, "mechanics_data.yaml")
CATEGORIES_DATA_FILE = os.path.join(CONFIG_DIR, "categories_data.yaml")
RANK_COMPLEXITY_FILE = os.path.join(CONFIG_DIR, "rank_complexity.yaml")

# YAML configuration file loading function
def load_yaml_config(file_path, default_value=None):
    """Generic function to load YAML files"""
    if not os.path.exists(file_path):
        return default_value or {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        
        # Return empty dictionary if None
        if data is None:
            return {}
            
        return data
    except Exception as e:
        print(f"Error loading configuration file ({file_path}): {str(e)}")
        return default_value or {}

# Function to get mechanic complexity
def get_mechanic_complexity(mechanic_name, default_value=2.5):
    """Get complexity from mechanic name"""
    mechanics_data = load_yaml_config(MECHANICS_DATA_FILE)
    
    # Check if mechanic exists
    if mechanic_name in mechanics_data:
        # New structure: complexity_data[mechanic_name] is a dictionary,
        # which contains a 'complexity' key
        if isinstance(mechanics_data[mechanic_name], dict) and 'complexity' in mechanics_data[mechanic_name]:
            return mechanics_data[mechanic_name]['complexity']
        # Support backward compatibility if value is stored directly
        elif isinstance(mechanics_data[mechanic_name], (int, float)):
            return mechanics_data[mechanic_name]
    
    return default_value

# Function to get category complexity
def get_category_complexity(category_name, default_value=2.5):
    """Get complexity from category name"""
    categories_data = load_yaml_config(CATEGORIES_DATA_FILE)
    
    # Check if category exists
    if category_name in categories_data:
        # New structure: categories_data[category_name] is a dictionary
        if isinstance(categories_data[category_name], dict) and 'complexity' in categories_data[category_name]:
            return categories_data[category_name]['complexity']
        # Support backward compatibility if value is stored directly
        elif isinstance(categories_data[category_name], (int, float)):
            return categories_data[category_name]
    
    return default_value

def calculate_category_complexity(categories):
    """Calculate overall complexity score from category list"""
    if not categories:
        return 2.5  # Default value
    
    # Get complexity for each category
    complexity_scores = [get_category_complexity(cat['name']) for cat in categories]
    
    # Calculate average complexity
    avg_complexity = sum(complexity_scores) / len(complexity_scores)
    
    # Adjustment based on number of categories (games with diverse categories are more complex)
    category_count_factor = min(1.3, 1.0 + (len(categories) - 1) * 0.05)
    adjusted_complexity = avg_complexity * category_count_factor
    
    # Limit to range 1.0-5.0
    return min(5.0, max(1.0, adjusted_complexity))

# Function to get ranking complexity
def get_rank_complexity_value(rank_type, default_value=3.0):
    """Get complexity from rank type"""
    complexity_data = load_yaml_config(RANK_COMPLEXITY_FILE)
    
    # Check if rank type exists
    if rank_type in complexity_data:
        # New structure: complexity_data[rank_type] is a dictionary
        if isinstance(complexity_data[rank_type], dict) and 'complexity' in complexity_data[rank_type]:
            return complexity_data[rank_type]['complexity']
        # Support backward compatibility if value is stored directly
        elif isinstance(complexity_data[rank_type], (int, float)):
            return complexity_data[rank_type]
    
    return default_value

def calculate_rank_position_score(rank_value):
    """Calculate game popularity/quality score from ranking position"""
    try:
        # Convert rank to integer
        rank = int(rank_value)
        
        # Calculate score on logarithmic scale (higher rank = higher score)
        if rank <= 10:
            # Top 10 gets highest rating
            score = 5.0
        elif rank <= 100:
            # Top 100 gets very high rating
            score = 4.5 - (rank - 10) / 90 * 0.5  # 4.5~4.0
        elif rank <= 1000:
            # Top 1000 gets high rating
            score = 4.0 - (rank - 100) / 900 * 1.0  # 4.0~3.0
        elif rank <= 5000:
            # Top 5000 gets medium rating
            score = 3.0 - (rank - 1000) / 4000 * 1.0  # 3.0~2.0
        else:
            # Below 5000 gets low rating
            score = max(1.0, 2.0 - math.log10(rank / 5000))  # 2.0~1.0
        
        return score
    except (ValueError, TypeError):
        # Return default value if cannot convert to number
        return 2.5

def calculate_rank_complexity(ranks):
    """Calculate complexity score from ranking information"""
    if not ranks:
        return 3.0  # Default value
    
    # Calculate score for each ranking type
    rank_scores = []
    for rank_info in ranks:
        rank_type = rank_info.get('type', 'boardgame')
        rank_value = rank_info.get('rank')
        
        if rank_value and rank_value != "Not Ranked":
            # Popularity/quality score from rank position
            popularity_score = calculate_rank_position_score(rank_value)
            
            # Ranking type complexity (base value)
            type_complexity = get_rank_complexity_value(rank_type)
            
            # Complexity evaluation is mainly based on ranking type
            # Rank position has smaller influence (20%)
            adjusted_score = (type_complexity * 0.8 + (popularity_score - 3.0) * 0.2)
            
            # Weighting is based on importance of ranking type
            weight = 1.0
            if rank_type == "boardgame":
                weight = 1.0  # Overall ranking has standard weight
            elif rank_type in ["strategygames", "wargames"]:
                weight = 1.2  # Strategy games get higher weight
            elif rank_type in ["familygames", "partygames", "childrensgames"]:
                weight = 0.8  # Casual games get lower weight
            
            # Add weighted score
            rank_scores.append((adjusted_score, weight))
    
    # Return default value if no scores
    if not rank_scores:
        return 3.0
        
    # Calculate weighted average
    total_weighted_score = sum(score * weight for score, weight in rank_scores)
    total_weight = sum(weight for _, weight in rank_scores)
    
    avg_score = total_weighted_score / total_weight
    
    # Limit to range 1.0-5.0
    return min(5.0, max(1.0, avg_score))

def get_mechanic_strategic_value(mechanic_name, default_value=3.0):
    """Get strategic value of specified mechanic"""
    mechanics_data = load_yaml_config(MECHANICS_DATA_FILE)
    
    # Check if mechanic exists
    if mechanic_name in mechanics_data:
        # If strategic_value is stored in dictionary format
        if isinstance(mechanics_data[mechanic_name], dict) and "strategic_value" in mechanics_data[mechanic_name]:
            return mechanics_data[mechanic_name]["strategic_value"]
        else:
            # Estimate strategic value based on complexity value
            complexity = mechanics_data[mechanic_name] if isinstance(mechanics_data[mechanic_name], (int, float)) else 3.0
            # Estimate strategic value based on complexity (more complex = higher strategy)
            estimated_value = min(5.0, complexity * 0.9)
            return max(1.0, estimated_value)
    
    return default_value

def get_mechanic_interaction_value(mechanic_name, default_value=3.0):
    """Get player interaction value of specified mechanic"""
    mechanics_data = load_yaml_config(MECHANICS_DATA_FILE)
    
    # Check if mechanic exists
    if mechanic_name in mechanics_data:
        # If interaction_value is stored in dictionary format
        if isinstance(mechanics_data[mechanic_name], dict) and "interaction_value" in mechanics_data[mechanic_name]:
            return mechanics_data[mechanic_name]["interaction_value"]
        else:
            # Certain mechanics tend to have high interaction
            high_interaction_mechanics = [
                'Trading', 'Negotiation', 'Auction/Bidding', 'Take That', 
                'Betting and Bluffing', 'Player Elimination'
            ]
            if mechanic_name in high_interaction_mechanics:
                return 4.5
            
            medium_interaction_mechanics = [
                'Area Control', 'Team-Based Game', 'Cooperative Game', 
                'Simultaneous Action Selection'
            ]
            if mechanic_name in medium_interaction_mechanics:
                return 3.8
            
            # Others have medium interaction
            return default_value
    
    return default_value

def evaluate_playtime_complexity(game_data):
    """Evaluate complexity bonus based on playing time"""
    playtime_info = {
        "strategic_bonus": 0.0,     # Bonus for strategic depth
        "interaction_modifier": 0.0, # Modifier for interaction
        "decision_density": 0.0,    # Decision density per unit time
        "complexity_factor": 1.0    # Overall complexity modifier factor
    }
    
    # Return default values if playing time is not set
    if 'playing_time' not in game_data:
        return playtime_info
    
    try:
        play_time = int(game_data['playing_time'])
        
        # Bonus to strategic depth (longer games tend to be more strategic)
        if play_time > 180:  # Over 3 hours
            playtime_info["strategic_bonus"] = 0.3
        elif play_time > 120:  # Over 2 hours
            playtime_info["strategic_bonus"] = 0.2
        elif play_time > 60:  # Over 1 hour
            playtime_info["strategic_bonus"] = 0.1
        
        # Modifier for interaction (short games have dense interaction, long games have strategic opposition)
        if play_time <= 30:  # 30 minutes or less
            playtime_info["interaction_modifier"] = 0.2  # High interaction in short time
        elif play_time >= 180:  # 3 hours or more
            playtime_info["interaction_modifier"] = 0.1  # Strategic opposition in long time
        
        # Decision density per unit time
        # Decisions in short games tend to have more weight, in long games they tend to be more distributed
        mechanics_count = len(game_data.get('mechanics', []))
        if play_time <= 30 and mechanics_count >= 3:  # Short time with many mechanics
            playtime_info["decision_density"] = 0.2
        elif 30 < play_time <= 60 and mechanics_count >= 4:
            playtime_info["decision_density"] = 0.15
        elif 60 < play_time <= 120 and mechanics_count >= 5:
            playtime_info["decision_density"] = 0.1
        
        # Overall complexity modifier factor
        # Games that are too short tend to have limited complexity
        if play_time < 20:  # Less than 20 minutes
            playtime_info["complexity_factor"] = 0.85  # 15% complexity reduction
        elif play_time < 45:  # Less than 45 minutes
            playtime_info["complexity_factor"] = 0.95  # 5% complexity reduction
        elif play_time > 180:  # More than 3 hours
            playtime_info["complexity_factor"] = 1.1   # 10% complexity increase
        
    except (ValueError, TypeError):
        # Use default values if playing time cannot be parsed
        pass
        
    return playtime_info

def estimate_decision_points(mechanics, game_data=None):
    """Estimate decision points (with readjusted weights)"""
    if not mechanics:
        return 2.5  # Default value
    
    # Get strategic value for each mechanic
    strategic_values = [get_mechanic_strategic_value(m['name']) for m in mechanics]
    
    if strategic_values:
        # Sort by strategic value in descending order
        strategic_values.sort(reverse=True)
        
        # Readjust weight coefficients
        if len(strategic_values) == 1:
            weights = [1.0]
        elif len(strategic_values) == 2:
            weights = [0.65, 0.35]
        elif len(strategic_values) == 3:
            weights = [0.55, 0.30, 0.15]
        else:
            # Gradually decreasing weights, but make distribution smaller
            weights = []
            for i in range(len(strategic_values)):
                if i == 0:
                    weights.append(0.5)  # Highest element: 50%
                elif i == 1:
                    weights.append(0.25)  # Second element: 25%
                else:
                    # Remaining elements: gradually decreasing but minimum 0.5/(n-2)%
                    remaining_weight = 0.25  # Distribute remaining 25%
                    remaining_count = len(strategic_values) - 2
                    min_weight = 0.5 / max(1, remaining_count)
                    weights.append(max(min_weight, remaining_weight / remaining_count))
        
        # Normalize weight sum to 1.0
        weights_sum = sum(weights)
        weights = [w / weights_sum for w in weights]
        
        # Calculate weighted average
        weighted_sum = sum(v * w for v, w in zip(strategic_values, weights))
        
        # Bonus based on mechanic diversity
        unique_values = set(strategic_values)
        value_range = max(strategic_values) - min(strategic_values) if len(strategic_values) > 1 else 0
        
        # Bonus based on diversity and range (limited to maximum 0.4)
        diversity_bonus = min(0.4, len(unique_values) * 0.07 + value_range * 0.1)
        
        # Basic decision points
        decision_points = weighted_sum + diversity_bonus
        
        # Modification by playing time (if exists)
        if game_data:
            playtime_info = evaluate_playtime_complexity(game_data)
            # Adjust decision density impact (suppress to 80%)
            decision_points += playtime_info["decision_density"] * 0.8
            # Adjust complexity factor impact (suppress to 90%)
            complexity_factor = 1.0 + (playtime_info["complexity_factor"] - 1.0) * 0.9
            decision_points *= complexity_factor
    else:
        decision_points = 2.5
    
    # Limit to range 1.0-5.0
    return min(5.0, max(1.0, decision_points))

def estimate_interaction_complexity(categories, mechanics=None, game_data=None):
    """Estimate interaction complexity (with readjusted weights)"""
    if not categories and not mechanics:
        return 2.5  # Default value
    
    # Combine interaction values from categories and mechanics
    category_values = []
    for c in categories:
        category_name = c.get('name', '')
        categories_data = load_yaml_config(CATEGORIES_DATA_FILE)
        if category_name in categories_data:
            if isinstance(categories_data[category_name], dict) and 'interaction_value' in categories_data[category_name]:
                category_values.append(categories_data[category_name]['interaction_value'])
            else:
                # Known high interaction categories
                high_interaction_categories = [
                    'Negotiation', 'Political', 'Bluffing', 'Party Game', 'Fighting'
                ]
                if category_name in high_interaction_categories:
                    category_values.append(4.5)
                # Known low interaction categories
                elif category_name in ['Abstract Strategy', 'Puzzle', 'Solo / Solitaire Game']:
                    category_values.append(2.0)
                else:
                    category_values.append(3.0)
    
    mechanic_values = []
    if mechanics:
        for m in mechanics:
            mechanic_name = m.get('name', '')
            mechanic_values.append(get_mechanic_interaction_value(mechanic_name))
    
    # Adjust weighting of categories and mechanics (category:mechanics = 60:40)
    if category_values and mechanic_values:
        # Calculate weighted average if both exist
        all_values = []
        
        # Category values (60% weight)
        for value in category_values:
            all_values.append((value, 0.6 / len(category_values)))
            
        # Mechanic values (40% weight)
        for value in mechanic_values:
            all_values.append((value, 0.4 / len(mechanic_values)))
        
        # Sort by value in descending order
        all_values.sort(key=lambda x: x[0], reverse=True)
        values = [v[0] for v in all_values]
        weights = [v[1] for v in all_values]
    else:
        # If only one exists
        values = category_values or mechanic_values
        values.sort(reverse=True)
        
        # Readjust weight coefficients
        if len(values) <= 3:
            # Small number of elements: suppress influence of first element, increase influence of subsequent elements
            if len(values) == 1:
                weights = [1.0]
            elif len(values) == 2:
                weights = [0.65, 0.35]
            else:  # len(values) == 3
                weights = [0.55, 0.30, 0.15]
        else:
            # Many elements: emphasize top 3, but give certain influence to the rest
            weights = []
            top_n = min(3, len(values))
            for i in range(len(values)):
                if i < top_n:
                    # Top 3: 65% total influence
                    if i == 0:
                        weights.append(0.3)    # 1st: 30%
                    elif i == 1:
                        weights.append(0.2)    # 2nd: 20%
                    else:  # i == 2
                        weights.append(0.15)   # 3rd: 15%
                else:
                    # Remaining: distribute 35% equally
                    remaining_count = len(values) - top_n
                    weights.append(0.35 / remaining_count)
    
    # Normalize weight sum to 1.0
    weights_sum = sum(weights)
    weights = [w / weights_sum for w in weights]
    
    # Calculate weighted average
    interaction_complexity = sum(v * w for v, w in zip(values, weights))
    
    # Modification by playing time (if exists)
    if game_data:
        playtime_info = evaluate_playtime_complexity(game_data)
        # Adjust interaction modifier impact (suppress to 85%)
        interaction_complexity += playtime_info["interaction_modifier"] * 0.85
        # Adjust complexity factor impact (suppress to 90%)
        complexity_factor = 1.0 + (playtime_info["complexity_factor"] - 1.0) * 0.9
        interaction_complexity *= complexity_factor
    
    # Modification based on player count
    if game_data and 'publisher_max_players' in game_data:
        try:
            max_players = int(game_data['publisher_max_players'])
            # Adjust impact
            if max_players >= 5:
                interaction_complexity *= 1.10  # 10% increase
            elif max_players >= 4:
                interaction_complexity *= 1.07  # 7% increase
        except (ValueError, TypeError):
            pass
    
    # Limit to range 1.0-5.0
    return min(5.0, max(1.0, interaction_complexity))

def calculate_rules_complexity(game_data):
    """Calculate rules complexity"""
    # Calculate mechanic complexity
    mechanics = game_data.get('mechanics', [])
    mechanics_complexity_sum = sum(get_mechanic_complexity(m['name']) for m in mechanics)
    avg_mechanic_complexity = mechanics_complexity_sum / max(1, len(mechanics))
    
    # Adjustment by number of mechanics
    mechanics_count_factor = min(1.5, 1.0 + (len(mechanics) / 10))
    
    # Estimate complexity from recommended age
    min_age = float(game_data.get('publisher_min_age', 10))
    age_complexity = min(4.0, (min_age - 6) / 3)  # Age 6=0, Age 12=2.0, Age 18=4.0
    
    # BGG weight
    base_weight = float(game_data.get('weight', 3.0))
    
    # Calculate rules complexity (mechanics: 60%, age: 20%, BGG: 20%)
    rules_complexity = (
        (avg_mechanic_complexity * mechanics_count_factor) * 0.6 +
        age_complexity * 0.2 +
        base_weight * 0.2
    )
    
    # Limit to range 1.0-5.0
    return min(5.0, max(1.0, rules_complexity))

def calculate_strategic_depth_improved(game_data):
    """Improved strategic depth calculation function (with readjusted weights)"""
    # Adjust BGG weight to 20% (suppress influence of external evaluation)
    base_weight = float(game_data.get('weight', 3.0))
    
    # Estimate decision points
    decision_points = estimate_decision_points(
        game_data.get('mechanics', []), game_data)
    
    # Estimate player interaction complexity
    interaction_complexity = estimate_interaction_complexity(
        game_data.get('categories', []), game_data.get('mechanics', []), game_data)
    
    # Calculate rules complexity
    rules_complexity = calculate_rules_complexity(game_data)
    
    # Evaluate strategic value of mechanics
    mechanics = game_data.get('mechanics', [])
    mechanics_names = [m['name'] for m in mechanics]
    
    # Get list of mechanics with high strategic value
    high_strategy_values = [(name, get_mechanic_strategic_value(name)) for name in mechanics_names]
    high_strategy_values.sort(key=lambda x: x[1], reverse=True)
    
    # Calculate bonus based on strategic value
    strategy_bonus = 0
    mechanic_count = len(high_strategy_values)
    
    # Emphasize mechanics with top strategic values
    if mechanic_count > 0:
        # Consider maximum 3 strategic mechanics
        top_n = min(3, mechanic_count)
        
        # Influence distribution (1st: 50%, 2nd: 30%, 3rd: 20%)
        weights = [0.5, 0.3, 0.2][:top_n]
        
        # Normalize
        weights_sum = sum(weights)
        weights = [w / weights_sum for w in weights]
        
        # Sum of influence × strategic value for each mechanic
        for i in range(top_n):
            name, value = high_strategy_values[i]
            impact = 0.1 * (value - 2.5)  # Calculate bonus/penalty based on 2.5 as baseline
            strategy_bonus += impact * weights[i]
    
    # Apply decay if there are too many mechanics
    if mechanic_count > 0:
        decay_factor = 1.0 / (1.0 + math.log(mechanic_count, 10))
        # Bonus with decay applied (limited to maximum 0.8)
        strategy_bonus = min(0.8, strategy_bonus * decay_factor)
    
    # Strategic depth bonus from playing time
    playtime_info = evaluate_playtime_complexity(game_data)
    playtime_strategic_bonus = playtime_info["strategic_bonus"]
    
    # Calculate strategic depth (with readjusted weights)
    strategic_depth = (
        base_weight * 0.20 +                   # BGG evaluation (20%)
        decision_points * 0.35 +               # Decision points (35%)
        rules_complexity * 0.10 +              # Rules complexity (10%)
        interaction_complexity * 0.25 +        # Interaction complexity (25%)
        strategy_bonus * 0.8 +                 # Strategic mechanic bonus (max 0.8, 80% influence)
        playtime_strategic_bonus * 0.6         # Playing time bonus (60% influence)
    )
    
    # Apply overall complexity factor (suppress influence to 95%)
    complexity_factor = playtime_info["complexity_factor"]
    complexity_factor = 1.0 + (complexity_factor - 1.0) * 0.95
    strategic_depth *= complexity_factor
    
    # Final strategic depth (limited to range 1.0-5.0)
    strategic_depth = min(5.0, max(1.0, strategic_depth))
    
    return round(strategic_depth, 2)

def get_strategic_depth_description(strategic_depth):
    """Get description for strategic depth"""
    if strategic_depth >= 4.5:
        return "Very deep (takes long time to master)"
    elif strategic_depth >= 4.0:
        return "Deep (for experienced players)"
    elif strategic_depth >= 3.5:
        return "Medium-high (many strategies exist)"
    elif strategic_depth >= 3.0:
        return "Medium (some strategy options available)"
    elif strategic_depth >= 2.5:
        return "Medium-low (basic strategies exist)"
    elif strategic_depth >= 2.0:
        return "Low (limited strategy options)"
    else:
        return "Low (few strategic elements)"

def get_rank_value(game_data, rank_type="boardgame"):
    """Get rank value for specified rank type"""
    if 'ranks' not in game_data:
        return None
        
    for rank_info in game_data['ranks']:
        if rank_info.get('type') == rank_type:
            try:
                return int(rank_info.get('rank'))
            except (ValueError, TypeError):
                return None
    
    return None

def calculate_popularity_factor(rank):
    """Calculate popularity factor based on ranking"""
    if rank is None:
        return 1.0
        
    if rank <= 100:
        return 1.1  # Top 100 increases rating by 10%
    elif rank <= 500:
        return 1.07  # Top 500 increases rating by 6%
    elif rank <= 1000:
        return 1.02  # Top 1000 increases rating by 3%
    else:
        return 1.0  # Others remain as is

def get_year_published(game_data):
    """Get year of publication for the game"""
    if 'year_published' not in game_data:
        return None
        
    try:
        return int(game_data['year_published'])
    except (ValueError, TypeError):
        return None

def calculate_longevity_factor(year_published):
    """Calculate longevity factor based on year of publication"""
    if year_published is None:
        return 1.0
        
    current_year = datetime.datetime.now().year
    years_since_publication = current_year - year_published
    
    if years_since_publication >= 20:
        return 1.1   # 20+ years: 10% increase (classic games)
    elif years_since_publication >= 10:
        return 1.07  # 10+ years: 7% increase (long-term popularity)
    elif years_since_publication >= 5:
        return 1.05  # 5+ years: 5% increase (established games)
    else:
        return 1.0   # New games remain as is

def calculate_replayability(game_data):
    """Calculate game replayability"""
    # Base score
    base_score = 2.0
    
    # Score addition for element diversity
    diversity_score = 0.0
    
    # Mechanics diversity (max 0.7 points)
    mechanics_count = len(game_data.get('mechanics', []))
    diversity_score += min(0.7, mechanics_count * 0.1)
    
    # Evaluate mechanics that enhance replayability in detail
    high_replay_mechanics = [
        'Variable Set-up', 
        'Modular Board', 
        'Variable Player Powers',
        'Deck Building',
        'Campaign / Battle Card Driven',
        'Scenario / Mission / Campaign Game',
        'Deck Construction',
        'Engine Building',
        'Hidden Roles',
        'Asymmetric Gameplay'
    ]
    
    medium_replay_mechanics = [
        'Card Drafting',
        'Worker Placement',
        'Tech Trees / Tech Tracks',
        'Multi-Use Cards',
        'Area Control',
        'Route/Network Building',
        'Tile Placement',
        'Resource Management',
        'Drafting'
    ]
    
    # Count mechanics with high replayability
    high_replay_count = sum(
        1 for m in game_data.get('mechanics', [])
        if m.get('name') in high_replay_mechanics
    )
    
    medium_replay_count = sum(
        1 for m in game_data.get('mechanics', [])
        if m.get('name') in medium_replay_mechanics
    )
    
    # Evaluation of high replayability mechanics (max 0.8 points)
    replay_mechanics_score = min(
        0.8, (high_replay_count * 0.2) + (medium_replay_count * 0.1)
    )
    diversity_score += replay_mechanics_score
    
    # Category diversity (max 0.4 points)
    categories_count = len(game_data.get('categories', []))
    diversity_score += min(0.4, categories_count * 0.1)
    
    # Adjustment based on popularity ranking
    rank = get_rank_value(game_data)
    rank_bonus = 0.0
    
    if rank is not None:
        if rank <= 100:
            rank_bonus = 0.6  # Top 100: +0.6 points
        elif rank <= 500:
            rank_bonus = 0.4  # Top 500: +0.4 points
        elif rank <= 1000:
            rank_bonus = 0.2  # Top 1000: +0.2 points
    
    # Adjustment based on long-term popularity
    year_published = get_year_published(game_data)
    longevity_factor = calculate_longevity_factor(year_published)
    
    # Final score calculation
    # Apply longevity factor to diversity score and popularity bonus
    replayability = (base_score + diversity_score + rank_bonus) * longevity_factor
    
    # Set upper and lower limits
    replayability = max(1.0, min(5.0, replayability))
    
    return round(replayability, 2)

def calculate_learning_curve(game_data):
    """
    Calculate learning curve information from game data
    Improved version using category and ranking information
    
    Parameters:
    game_data (dict): Game details
    
    Returns:
    dict: Learning curve information
    """
    # Basic complexity (already retrieved from API)
    base_weight = float(game_data.get('weight', 3.0))
    
    # Estimate complexity from game mechanics
    mechanics_names = [m['name'] for m in game_data.get('mechanics', [])]
    mechanics_complexity = 0
    mechanic_count = 0
    
    for mechanic in mechanics_names:
        # Get complexity value
        mechanic_complexity = get_mechanic_complexity(mechanic)
        mechanics_complexity += mechanic_complexity
        mechanic_count += 1
    
    # Average mechanics complexity (default value if no mechanics)
    avg_mechanic_complexity = (
        mechanics_complexity / max(1, mechanic_count) if mechanic_count > 0 else 3.0
    )
    
    # Calculate complexity based on categories
    category_complexity = calculate_category_complexity(game_data.get('categories', []))
    
    # Calculate complexity based on rankings
    rank_complexity = calculate_rank_complexity(game_data.get('ranks', []))
    
    # Complexity evaluation from categories and rankings (60:40 weighting)
    complexity_factor = (category_complexity * 0.6 + rank_complexity * 0.4)
        
    # Update initial barrier calculation (rule complexity)
    initial_barrier = (
        avg_mechanic_complexity * 0.5 + 
        base_weight * 0.2 +
        complexity_factor * 0.2  # Use category and ranking evaluation instead of age recommendation
    )
    
    # Adjust initial barrier by number of mechanics (more mechanics = harder initial learning)
    mechanics_count_barrier_factor = min(1.25, max(1.0, len(mechanics_names) / 5))
    initial_barrier = initial_barrier * mechanics_count_barrier_factor
    
    # Set upper limit to 5.0
    initial_barrier = min(5.0, initial_barrier)
    initial_barrier = round(initial_barrier, 2)
    
    # Strategic depth (improved version)
    strategic_depth = calculate_strategic_depth_improved(game_data)
    
    # Calculate replayability (improved version)
    replayability = calculate_replayability(game_data)
    
    # Get rank info
    rank = get_rank_value(game_data)
    
    # Get year published
    year_published = get_year_published(game_data)
    
    # Build basic learning curve information
    learning_curve = {
        "initial_barrier": initial_barrier,  # Initial learning difficulty
        "strategic_depth": strategic_depth,  # Strategic depth
        "replayability": replayability,  # Replayability
        "mechanics_complexity": round(avg_mechanic_complexity, 2),  # Mechanics complexity
        "mechanics_count": len(mechanics_names),  # Number of mechanics
        "bgg_weight": base_weight,  # BGG complexity rating (original value)
        "bgg_rank": rank,  # BGG ranking
        "year_published": year_published,  # Year published
        # Newly added metrics
        "category_complexity": round(category_complexity, 2),  # Category-based complexity
        "rank_complexity": round(rank_complexity, 2)  # Ranking-based complexity
    }
    
    # Determine learning curve type
    if initial_barrier > 4.3:
        if strategic_depth > 4.3:
            learning_curve["learning_curve_type"] = "steep"  # Steep and deep
        elif strategic_depth > 3.5:
            learning_curve["learning_curve_type"] = "steep_then_moderate"  # Steep but moderate depth
        else:
            learning_curve["learning_curve_type"] = "steep_then_shallow"  # Steep but shallow
    elif initial_barrier > 3.5:
        if strategic_depth > 4.3:
            learning_curve["learning_curve_type"] = "moderate_then_deep"  # Moderate to deep
        elif strategic_depth > 3.5:
            learning_curve["learning_curve_type"] = "moderate"  # Moderate to moderate
        else:
            learning_curve["learning_curve_type"] = "moderate_then_shallow"  # Moderate to shallow
    else:
        if strategic_depth > 4.3:
            learning_curve["learning_curve_type"] = "gentle_then_deep"  # Gentle to deep
        elif strategic_depth > 3.5:
            learning_curve["learning_curve_type"] = "gentle_then_moderate"  # Gentle to moderate
        else:
            learning_curve["learning_curve_type"] = "gentle"  # Gentle to shallow
    
    # Add detailed analysis information
    learning_curve["decision_points"] = estimate_decision_points(game_data.get('mechanics', []), game_data)
    learning_curve["interaction_complexity"] = estimate_interaction_complexity(game_data.get('categories', []), game_data.get('mechanics', []), game_data)
    learning_curve["rules_complexity"] = calculate_rules_complexity(game_data)
    
    # Player type determination
    player_types = []
    
    # For beginners
    if initial_barrier < 3.0 and strategic_depth < 3.5:
        player_types.append("beginner")
    
    # For casual players
    if initial_barrier < 4.0 and strategic_depth < 4.5:
        player_types.append("casual")
    
    # For experienced players
    if strategic_depth >= 3.0:
        player_types.append("experienced")
    
    # For hardcore gamers
    if initial_barrier > 3.0 and strategic_depth > 3.5:
        player_types.append("hardcore")
    
    # For strategists
    if strategic_depth > 3.8:
        player_types.append("strategist")
    
    # For system masters
    if len(game_data.get('mechanics', [])) >= 5 and strategic_depth > 3.5:
        player_types.append("system_master")
    
    # For replayers (people who like highly replayable games)
    if replayability >= 3.8:
        player_types.append("replayer")
    
    # For trend followers (people who like popular games)
    if rank is not None and rank <= 1000:
        player_types.append("trend_follower")
    
    # For classic lovers (people who like time-tested traditional games)
    if year_published is not None and year_published <= 2000:
        player_types.append("classic_lover")
    
    learning_curve["player_types"] = player_types
    
    # Add playtime analysis data
    learning_curve["playtime_analysis"] = evaluate_playtime_complexity(game_data)
    
    # Estimate mastery time
    if strategic_depth > 4.3:
        if len(mechanics_names) >= 6:
            learning_curve["mastery_time"] = "medium_to_long"  # Many mechanics but easier to apply once basics understood
        else:
            learning_curve["mastery_time"] = "long"  # Takes long time to master
    elif strategic_depth > 3.2:
        learning_curve["mastery_time"] = "medium"  # Takes medium time to master
    else:
        learning_curve["mastery_time"] = "short"  # Can be mastered relatively quickly
    
    return learning_curve