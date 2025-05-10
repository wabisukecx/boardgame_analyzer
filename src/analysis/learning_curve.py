"""
Board game learning curve analysis module
Contains functions for analyzing learning curves using categories and ranking information
"""

import datetime
from src.utils.language import t

# Import mechanic complexity data retrieval function
from src.analysis.mechanic_complexity import get_complexity
# Import category complexity calculation function
from src.analysis.category_complexity import calculate_category_complexity
# Import ranking-based evaluation function
from src.analysis.rank_complexity import calculate_rank_complexity
# Import improved strategic depth calculation
from src.analysis.strategic_depth import (
    calculate_strategic_depth_improved,
    update_learning_curve_with_improved_strategic_depth,
    estimate_decision_points_improved as estimate_decision_points,
    estimate_interaction_complexity_improved as estimate_interaction_complexity,
    calculate_rules_complexity
)

def get_rank_value(game_data, rank_type="boardgame"):
    """
    Get rank value for specified rank type
    
    Parameters:
    game_data (dict): Game details
    rank_type (str): Rank type (default is overall ranking "boardgame")
    
    Returns:
    int or None: Rank position (None if not found)
    """
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
    """
    Calculate popularity factor based on ranking
    
    Parameters:
    rank (int or None): BGG ranking position
    
    Returns:
    float: Popularity factor (1.0-1.1 range)
    """
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
    """
    Get year of publication for the game
    
    Parameters:
    game_data (dict): Game details
    
    Returns:
    int or None: Year of publication (None if not found)
    """
    if 'year_published' not in game_data:
        return None
        
    try:
        return int(game_data['year_published'])
    except (ValueError, TypeError):
        return None


def calculate_longevity_factor(year_published):
    """
    Calculate longevity factor based on year of publication
    Games that have been popular for a long time are considered
    to have higher replayability
    
    Parameters:
    year_published (int or None): Year of publication
    
    Returns:
    float: Longevity factor (1.0-1.1 range)
    """
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
    """
    Calculate game replayability
    
    Parameters:
    game_data (dict): Game details
    
    Returns:
    float: Replayability score (1.0-5.0 range)
    """
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
    # Multiply diversity score and popularity bonus by longevity factor
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
        mechanic_complexity = get_complexity(mechanic)
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
    
    # Expand learning curve data with improved metrics
    learning_curve = update_learning_curve_with_improved_strategic_depth(
        game_data, learning_curve)
    
    # Add detailed analysis information
    learning_curve["decision_points"] = estimate_decision_points(game_data.get('mechanics', []))
    learning_curve["interaction_complexity"] = estimate_interaction_complexity(game_data.get('categories', []))
    learning_curve["rules_complexity"] = calculate_rules_complexity(game_data)
    
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

def get_curve_type_display(curve_type):
    """
    Get display name for learning curve type
    
    Parameters:
    curve_type (str): Learning curve type
    
    Returns:
    str: Display learning curve type
    """
    return t(f"learning_curve.types.{curve_type}")

def get_player_type_display(player_type):
    """
    Get display name for player type
    
    Parameters:
    player_type (str): Player type
    
    Returns:
    str: Display player type
    """
    return t(f"player_types.{player_type}")

def get_mastery_time_display(mastery_time):
    """
    Get display name for mastery time
    
    Parameters:
    mastery_time (str): Mastery time
    
    Returns:
    str: Display mastery time
    """
    return t(f"mastery_time.{mastery_time}")

def get_replayability_display(replayability):
    """
    Get display name for replayability
    
    Parameters:
    replayability (float): Replayability score
    
    Returns:
    str: Display replayability evaluation
    """
    if replayability >= 4.5:
        return t("replayability.very_high")
    elif replayability >= 4.0:
        return t("replayability.high")
    elif replayability >= 3.5:
        return t("replayability.medium_high")
    elif replayability >= 3.0:
        return t("replayability.medium")
    elif replayability >= 2.0:
        return t("replayability.low")
    else:
        return t("replayability.very_low")