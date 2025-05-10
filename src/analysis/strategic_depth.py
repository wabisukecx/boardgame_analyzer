"""
Strategic depth calculation module - utilizing existing YAML data
"""

import math
from src.analysis.mechanic_complexity import load_mechanics_data, get_complexity
from src.analysis.category_complexity import load_categories_data
from src.utils.language import t

def get_mechanic_strategic_value(mechanic_name, default_value=3.0):
    """
    Get strategic value for specified mechanic
    
    Parameters:
    mechanic_name (str): Mechanic name
    default_value (float): Default value if not exists
    
    Returns:
    float: Strategic value (range 1.0-5.0)
    """
    mechanics_data = load_mechanics_data()
    
    # Check if mechanic exists
    if mechanic_name in mechanics_data:
        # If strategic_value is stored in dictionary format
        if isinstance(mechanics_data[mechanic_name], dict) and "strategic_value" in mechanics_data[mechanic_name]:
            return mechanics_data[mechanic_name]["strategic_value"]
        else:
            # Estimate strategic value based on complexity value
            complexity = mechanics_data[mechanic_name] if isinstance(mechanics_data[mechanic_name], (int, float)) else 3.0
            # Estimate strategic value based on complexity (higher complexity tends to have higher strategy)
            estimated_value = min(5.0, complexity * 0.9)
            return max(1.0, estimated_value)
    
    return default_value

def get_mechanic_interaction_value(mechanic_name, default_value=3.0):
    """
    Get player interaction value for specified mechanic
    
    Parameters:
    mechanic_name (str): Mechanic name
    default_value (float): Default value if not exists
    
    Returns:
    float: Interaction value (range 1.0-5.0)
    """
    mechanics_data = load_mechanics_data()
    
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
            
            # Others have moderate interaction
            return default_value
    
    return default_value

def get_category_strategic_value(category_name, default_value=3.0):
    """
    Get strategic value for specified category
    
    Parameters:
    category_name (str): Category name
    default_value (float): Default value if not exists
    
    Returns:
    float: Strategic value (range 1.0-5.0)
    """
    categories_data = load_categories_data()
    
    # Check if category exists
    if category_name in categories_data:
        # If strategic_value is stored in dictionary format
        if isinstance(categories_data[category_name], dict) and "strategic_value" in categories_data[category_name]:
            return categories_data[category_name]["strategic_value"]
        else:
            # Estimate strategic value based on complexity value
            complexity = categories_data[category_name] if isinstance(categories_data[category_name], (int, float)) else 3.0
            # Estimate strategic value based on complexity (higher complexity tends to have higher strategy)
            estimated_value = min(5.0, complexity * 0.85 + 0.5)
            return max(1.0, estimated_value)
    
    # For known high strategy categories
    high_strategy_categories = [
        'Strategy', 'Economic', 'Civilization', 'Wargame', 'Abstract Strategy', 'Political'
    ]
    if category_name in high_strategy_categories:
        return 4.5
    
    # For known low strategy categories
    low_strategy_categories = [
        'Children\'s Game', 'Party Game', 'Dice', 'Memory'
    ]
    if category_name in low_strategy_categories:
        return 2.0
    
    return default_value

def get_category_interaction_value(category_name, default_value=3.0):
    """
    Get player interaction value for specified category
    
    Parameters:
    category_name (str): Category name
    default_value (float): Default value if not exists
    
    Returns:
    float: Interaction value (range 1.0-5.0)
    """
    categories_data = load_categories_data()
    
    # Check if category exists
    if category_name in categories_data:
        # If interaction_value is stored in dictionary format
        if isinstance(categories_data[category_name], dict) and "interaction_value" in categories_data[category_name]:
            return categories_data[category_name]["interaction_value"]
    
    # For known high interaction categories
    high_interaction_categories = [
        'Negotiation', 'Political', 'Bluffing', 'Party Game', 'Fighting'
    ]
    if category_name in high_interaction_categories:
        return 4.5
    
    # For known low interaction categories
    low_interaction_categories = [
        'Abstract Strategy', 'Puzzle', 'Solo / Solitaire Game'
    ]
    if category_name in low_interaction_categories:
        return 2.0
    
    return default_value

# Function to evaluate the relationship between playtime and complexity
def evaluate_playtime_complexity(game_data):
    """
    Evaluate complexity bonus based on playtime
    
    Parameters:
    game_data (dict): Game detail information
    
    Returns:
    dict: Playtime analysis information
    """
    playtime_info = {
        "strategic_bonus": 0.0,     # Bonus for strategic depth
        "interaction_modifier": 0.0, # Modifier for interaction
        "decision_density": 0.0,    # Decision density per unit time
        "complexity_factor": 1.0    # Overall modifier factor for complexity
    }
    
    # Return default values if playtime is not set
    if 'playing_time' not in game_data:
        return playtime_info
    
    try:
        play_time = int(game_data['playing_time'])
        
        # Bonus for strategic depth (longer games tend to be more strategic)
        if play_time > 180:  # Over 3 hours
            playtime_info["strategic_bonus"] = 0.3
        elif play_time > 120:  # Over 2 hours
            playtime_info["strategic_bonus"] = 0.2
        elif play_time > 60:  # Over 1 hour
            playtime_info["strategic_bonus"] = 0.1
        
        # Modifier for interaction (short games have intense interaction, long games have strategic confrontation)
        if play_time <= 30:  # 30 minutes or less
            playtime_info["interaction_modifier"] = 0.2  # High interaction in short time
        elif play_time >= 180:  # 3 hours or more
            playtime_info["interaction_modifier"] = 0.1  # Strategic confrontation in long games
        
        # Decision density per unit time
        # Decisions in short games tend to have weight, while in long games they tend to be distributed
        mechanics_count = len(game_data.get('mechanics', []))
        if play_time <= 30 and mechanics_count >= 3:  # Short time with many mechanics
            playtime_info["decision_density"] = 0.2
        elif 30 < play_time <= 60 and mechanics_count >= 4:
            playtime_info["decision_density"] = 0.15
        elif 60 < play_time <= 120 and mechanics_count >= 5:
            playtime_info["decision_density"] = 0.1
        
        # Overall modifier factor for complexity
        # Too short games tend to have limited complexity
        if play_time < 20:  # Less than 20 minutes
            playtime_info["complexity_factor"] = 0.85  # 15% decrease in complexity
        elif play_time < 45:  # Less than 45 minutes
            playtime_info["complexity_factor"] = 0.95  # 5% decrease in complexity
        elif play_time > 180:  # Over 3 hours
            playtime_info["complexity_factor"] = 1.1   # 10% increase in complexity
        
    except (ValueError, TypeError):
        # Use default values if playtime cannot be parsed
        pass
        
    return playtime_info

def estimate_decision_points_improved(mechanics, game_data=None):
    """
    Estimate decision points (with readjusted weighting)
    
    Parameters:
    mechanics (list): List of mechanics
    game_data (dict, optional): Game detail information
    
    Returns:
    float: Estimated decision points (range 1.0-5.0)
    """
    if not mechanics:
        return 2.5  # Default value
    
    # Get strategic value for each mechanic
    strategic_values = [get_mechanic_strategic_value(m['name']) for m in mechanics]
    
    if strategic_values:
        # Sort by strategic value in descending order
        strategic_values.sort(reverse=True)
        
        # Readjusted weighting coefficients
        # Reduce influence of highest value element, increase influence of subsequent elements
        if len(strategic_values) == 1:
            weights = [1.0]
        elif len(strategic_values) == 2:
            weights = [0.65, 0.35]  # Previously: about [0.67, 0.33]
        elif len(strategic_values) == 3:
            weights = [0.55, 0.30, 0.15]  # Previously: about [0.6, 0.3, 0.1]
        else:
            # Gradually decreasing weights, but with smaller variance
            weights = []
            for i in range(len(strategic_values)):
                if i == 0:
                    weights.append(0.5)  # Highest element: 50%
                elif i == 1:
                    weights.append(0.25)  # Second element: 25%
                else:
                    # Remaining elements: gradually decreasing but guaranteed minimum 0.5/(n-2)%
                    remaining_weight = 0.25  # Distribute remaining 25%
                    remaining_count = len(strategic_values) - 2
                    min_weight = 0.5 / max(1, remaining_count)
                    weights.append(max(min_weight, remaining_weight / remaining_count))
        
        # Normalize weight sum to 1.0
        weights_sum = sum(weights)
        weights = [w / weights_sum for w in weights]
        
        # Calculate weighted average
        weighted_sum = sum(v * w for v, w in zip(strategic_values, weights))
        
        # Bonus based on mechanic diversity (adjusted influence)
        # Evaluate degree of diversity, not just simple count
        unique_values = set(strategic_values)
        value_range = max(strategic_values) - min(strategic_values) if len(strategic_values) > 1 else 0
        
        # Bonus based on diversity and range (limited to max 0.4)
        diversity_bonus = min(0.4, len(unique_values) * 0.07 + value_range * 0.1)
        
        # Basic decision points
        decision_points = weighted_sum + diversity_bonus
        
        # Modifier based on playtime (if exists)
        if game_data:
            playtime_info = evaluate_playtime_complexity(game_data)
            # Adjust decision density influence (suppress to 80%)
            decision_points += playtime_info["decision_density"] * 0.8
            # Adjust complexity factor influence (suppress to 90%)
            complexity_factor = 1.0 + (playtime_info["complexity_factor"] - 1.0) * 0.9
            decision_points *= complexity_factor
    else:
        decision_points = 2.5
    
    # Limit to 1.0-5.0 range
    return min(5.0, max(1.0, decision_points))

def estimate_interaction_complexity_improved(categories, mechanics=None, game_data=None):
    """
    Estimate interaction complexity (with readjusted weighting)
    
    Parameters:
    categories (list): List of categories
    mechanics (list, optional): List of mechanics
    game_data (dict, optional): Game detail information
    
    Returns:
    float: Estimated interaction complexity (range 1.0-5.0)
    """
    if not categories and not mechanics:
        return 2.5  # Default value
    
    # Combine interaction values for categories and mechanics
    category_values = [get_category_interaction_value(c['name']) for c in (categories or [])]
    mechanic_values = [get_mechanic_interaction_value(m['name']) for m in (mechanics or [])]
    
    # Adjust weighting for categories and mechanics (categories:mechanics = 60:40)
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
        
        # Readjusted weighting coefficients
        if len(values) <= 3:
            # Few elements: reduce influence of first element, increase influence of subsequent elements
            if len(values) == 1:
                weights = [1.0]
            elif len(values) == 2:
                weights = [0.65, 0.35]
            else:  # len(values) == 3
                weights = [0.55, 0.30, 0.15]
        else:
            # Many elements: emphasize top 3 but give certain influence to the rest
            weights = []
            top_n = min(3, len(values))
            for i in range(len(values)):
                if i < top_n:
                    # Top 3: total 65% influence
                    if i == 0:
                        weights.append(0.3)    # 1st: 30%
                    elif i == 1:
                        weights.append(0.2)    # 2nd: 20%
                    else:  # i == 2
                        weights.append(0.15)   # 3rd: 15%
                else:
                    # Rest: distribute remaining 35% equally
                    remaining_count = len(values) - top_n
                    weights.append(0.35 / remaining_count)
    
    # Normalize weight sum to 1.0
    weights_sum = sum(weights)
    weights = [w / weights_sum for w in weights]
    
    # Calculate weighted average
    interaction_complexity = sum(v * w for v, w in zip(values, weights))
    
    # Modifier based on playtime (if exists)
    if game_data:
        playtime_info = evaluate_playtime_complexity(game_data)
        # Adjust interaction modifier influence (suppress to 85%)
        interaction_complexity += playtime_info["interaction_modifier"] * 0.85
        # Adjust complexity factor influence (suppress to 90%)
        complexity_factor = 1.0 + (playtime_info["complexity_factor"] - 1.0) * 0.9
        interaction_complexity *= complexity_factor
    
    # Modifier based on number of players
    if game_data and 'publisher_max_players' in game_data:
        try:
            max_players = int(game_data['publisher_max_players'])
            # Adjust influence (previously: 15%→10%, 10%→7%)
            if max_players >= 5:
                interaction_complexity *= 1.10  # 10% increase
            elif max_players >= 4:
                interaction_complexity *= 1.07  # 7% increase
        except (ValueError, TypeError):
            pass
    
    # Limit to 1.0-5.0 range
    return min(5.0, max(1.0, interaction_complexity))

def calculate_rules_complexity(game_data):
    """
    Calculate rules complexity
    
    Parameters:
    game_data (dict): Game detail information
    
    Returns:
    float: Rules complexity score (range 1.0-5.0)
    """
    # Calculate mechanic complexity
    mechanics = game_data.get('mechanics', [])
    mechanics_complexity_sum = sum(get_complexity(m['name']) for m in mechanics)
    avg_mechanic_complexity = mechanics_complexity_sum / max(1, len(mechanics))
    
    # Adjustment based on number of mechanics
    mechanics_count_factor = min(1.5, 1.0 + (len(mechanics) / 10))
    
    # Estimate complexity from recommended age
    min_age = float(game_data.get('publisher_min_age', 10))
    age_complexity = min(4.0, (min_age - 6) / 3)  # age 6=0, age 12=2.0, age 18=4.0
    
    # BGG weight
    base_weight = float(game_data.get('weight', 3.0))
    
    # Calculate rules complexity (mechanics:60%, age:20%, BGG:20%)
    rules_complexity = (
        (avg_mechanic_complexity * mechanics_count_factor) * 0.6 +
        age_complexity * 0.2 +
        base_weight * 0.2
    )
    
    # Limit to 1.0-5.0 range
    return min(5.0, max(1.0, rules_complexity))

def calculate_strategic_depth_improved(game_data):
    """
    Improved strategic depth calculation function (with readjusted weighting)
    
    Parameters:
    game_data (dict): Game detail information
    
    Returns:
    float: Strategic depth score (range 1.0-5.0)
    """
    # Adjust BGG weight to 20% (reduce influence of external evaluation)
    base_weight = float(game_data.get('weight', 3.0))
    
    # Estimate decision points
    decision_points = estimate_decision_points_improved(
        game_data.get('mechanics', []), game_data)
    
    # Estimate player interaction complexity
    interaction_complexity = estimate_interaction_complexity_improved(
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
        # Consider up to 3 strategic mechanics
        top_n = min(3, mechanic_count)
        
        # Distribution of influence (1st:50%, 2nd:30%, 3rd:20%)
        weights = [0.5, 0.3, 0.2][:top_n]
        
        # Normalize
        weights_sum = sum(weights)
        weights = [w / weights_sum for w in weights]
        
        # Sum of influence × strategic value for each mechanic
        for i in range(top_n):
            name, value = high_strategy_values[i]
            impact = 0.1 * (value - 2.5)  # Calculate bonus/penalty based on 2.5 as baseline
            strategy_bonus += impact * weights[i]
    
    # Apply decay for too many mechanics
    if mechanic_count > 0:
        decay_factor = 1.0 / (1.0 + math.log(mechanic_count, 10))
        # Apply decay to bonus (limit to max 0.8)
        strategy_bonus = min(0.8, strategy_bonus * decay_factor)
    
    # Strategic depth bonus based on playtime
    playtime_info = evaluate_playtime_complexity(game_data)
    playtime_strategic_bonus = playtime_info["strategic_bonus"]
    
    # Calculate strategic depth (with readjusted weighting)
    strategic_depth = (
        base_weight * 0.20 +                   # BGG evaluation (20%→reduce predictive power)
        decision_points * 0.35 +               # Decision points (30%→increase to 35%)
        rules_complexity * 0.10 +              # Rules complexity (15%→decrease to 10%)
        interaction_complexity * 0.25 +        # Interaction complexity (20%→increase to 25%)
        strategy_bonus * 0.8 +                 # Strategic mechanic bonus (limited to max 0.8, 80% influence)
        playtime_strategic_bonus * 0.6         # Playtime bonus (60% influence)
    )
    
    # Apply overall complexity factor (suppress influence to 95%)
    complexity_factor = playtime_info["complexity_factor"]
    complexity_factor = 1.0 + (complexity_factor - 1.0) * 0.95
    strategic_depth *= complexity_factor
    
    # Final strategic depth (limit to 1.0-5.0)
    strategic_depth = min(5.0, max(1.0, strategic_depth))
    
    return round(strategic_depth, 2)

def get_strategic_depth_description(strategic_depth):
    """
    Get description for strategic depth
    
    Parameters:
    strategic_depth (float): Strategic depth value
    
    Returns:
    str: Strategic depth description text
    """
    if strategic_depth >= 4.5:
        return t("analysis.depth.very_deep")
    elif strategic_depth >= 4.0:
        return t("analysis.depth.deep")
    elif strategic_depth >= 3.5:
        return t("analysis.depth.medium_high")
    elif strategic_depth >= 3.0:
        return t("analysis.depth.medium")
    elif strategic_depth >= 2.5:
        return t("analysis.depth.medium_low")
    elif strategic_depth >= 2.0:
        return t("analysis.depth.shallow")
    else:
        return t("analysis.depth.very_shallow")

def update_learning_curve_with_improved_strategic_depth(game_data, learning_curve):
    """
    Update existing learning curve data with improved strategic depth
    
    Parameters:
    game_data (dict): Game detail information
    learning_curve (dict): Existing learning curve data
    
    Returns:
    dict: Updated learning curve data
    """
    # Calculate improved strategic depth
    strategic_depth = calculate_strategic_depth_improved(game_data)
    
    # Update learning curve data
    learning_curve["strategic_depth"] = strategic_depth
    learning_curve["strategic_depth_description"] = get_strategic_depth_description(strategic_depth)
    
    # Update learning curve type (based on new combination of initial barrier and strategic depth)
    initial_barrier = learning_curve["initial_barrier"]
    
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
    
    # Update player types (changed to more lenient conditions)
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
    
    # For system masters (name changed from mechanics_master to system_master)
    if len(game_data.get('mechanics', [])) >= 5 and strategic_depth > 3.5:
        player_types.append("system_master")
    
    # For replayers (those who prefer highly replayable games)
    if learning_curve.get('replayability', 0) >= 3.8:
        player_types.append("replayer")
    
    # For trend followers (those who prefer popular games)
    if learning_curve.get('bgg_rank') is not None and learning_curve.get('bgg_rank') <= 1000:
        player_types.append("trend_follower")
    
    # For classic lovers (those who prefer long-standing classic games)
    year_published = learning_curve.get('year_published')
    if year_published is not None and isinstance(year_published, int) and year_published <= 2000:
        player_types.append("classic_lover")
        
    # If no matching conditions, assign basic player types based on initial barrier and strategic depth
    if not player_types:
        if strategic_depth >= 3.5:
            player_types.append("experienced")
        elif initial_barrier >= 3.5:
            player_types.append("hardcore")
        else:
            player_types.append("casual")
    
    # Include additional metrics in learning curve analysis
    learning_curve["decision_points"] = estimate_decision_points_improved(game_data.get('mechanics', []), game_data)
    learning_curve["interaction_complexity"] = estimate_interaction_complexity_improved(
        game_data.get('categories', []), game_data.get('mechanics', []), game_data)
    learning_curve["rules_complexity"] = calculate_rules_complexity(game_data)
    learning_curve["player_types"] = player_types
    
    # Add playtime analysis data
    learning_curve["playtime_analysis"] = evaluate_playtime_complexity(game_data)
    
    return learning_curve