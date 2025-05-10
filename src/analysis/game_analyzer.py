"""
game_analyzer.py - Board game evaluation and analysis module
Contains only the functions actually used in the current application
"""

from src.utils.language import t, get_game_display_name

def get_complexity_level(weight):
    """Get complexity level description
    
    Parameters:
    weight (float): Game complexity value
    
    Returns:
    str: Complexity level description text
    """
    if weight >= 4.0:
        return t("analysis.complexity.very_high")
    elif weight >= 3.5:
        return t("analysis.complexity.high")
    elif weight >= 2.8:
        return t("analysis.complexity.medium_high")
    elif weight >= 2.0:
        return t("analysis.complexity.medium")
    elif weight >= 1.5:
        return t("analysis.complexity.medium_low")
    else:
        return t("analysis.complexity.low")

def get_depth_level(depth):
    """Get strategic depth description
    
    Parameters:
    depth (float): Game strategic depth value
    
    Returns:
    str: Strategic depth description text
    """
    if depth >= 4.5:
        return t("analysis.depth.very_deep")
    elif depth >= 4.0:
        return t("analysis.depth.deep")
    elif depth >= 3.5:
        return t("analysis.depth.medium_high")
    elif depth >= 3.0:
        return t("analysis.depth.medium")
    elif depth >= 2.5:
        return t("analysis.depth.medium_low")
    elif depth >= 2.0:
        return t("analysis.depth.shallow")
    else:
        return t("analysis.depth.very_shallow")

def get_popularity_level(rank):
    """Get popularity level description
    
    Parameters:
    rank (int or None): BGG ranking position
    
    Returns:
    str: Popularity level description text
    """
    if rank is None:
        return t("analysis.popularity.new_or_unrated")
    elif rank <= 100:
        return t("analysis.popularity.highest")
    elif rank <= 500:
        return t("analysis.popularity.very_high")
    elif rank <= 1000:
        return t("analysis.popularity.high")
    elif rank <= 2000:
        return t("analysis.popularity.moderate")
    else:
        return t("analysis.popularity.niche")

def generate_game_summary(game_data, learning_curve):
    """
    Generate comprehensive game summary text
    
    Parameters:
    game_data (dict): Game details
    learning_curve (dict): Learning curve information
    
    Returns:
    str: Generated summary text
    """
    # Game name and year - using language-aware function
    game_name = get_game_display_name(game_data)
    year = game_data.get('year_published', t('common.unknown'))
    
    # Categories and mechanics (max 3 each)
    categories = [cat.get('name', '') for cat in game_data.get('categories', [])][:3]  
    mechanics = [mech.get('name', '') for mech in game_data.get('mechanics', [])][:3]  
    
    # BGG ranking info
    bgg_rank = None
    for rank_info in game_data.get('ranks', []):
        if rank_info.get('type') == 'boardgame':
            try:
                bgg_rank = int(rank_info.get('rank'))
                break
            except (ValueError, TypeError):
                pass
    
    # Analysis data
    complexity = get_complexity_level(float(game_data.get('weight', 3.0)))
    depth = get_depth_level(learning_curve.get('strategic_depth', 3.0))
    popularity = get_popularity_level(bgg_rank)
    
    # Player types
    from src.analysis.learning_curve import get_player_type_display, get_replayability_display
    player_types_display = [get_player_type_display(pt) for pt in learning_curve.get('player_types', [])[:2]]
    
    # Initial learning barrier
    initial_barrier = learning_curve.get('initial_barrier', 3.0)
    
    # Initial learning barrier text representation
    if initial_barrier >= 4.5:
        barrier_text = t("analysis.barrier.very_high")
    elif initial_barrier >= 4.0:
        barrier_text = t("analysis.barrier.high")
    elif initial_barrier >= 3.5:
        barrier_text = t("analysis.barrier.medium_high")
    elif initial_barrier >= 3.0:
        barrier_text = t("analysis.barrier.medium")
    elif initial_barrier >= 2.0:
        barrier_text = t("analysis.barrier.low")
    else:
        barrier_text = t("analysis.barrier.very_low")
        
    # Replayability
    replayability = learning_curve.get('replayability', 3.0)
    replayability_text = get_replayability_display(replayability)
    
    # Basic summary
    categories_text = t("common.list_separator").join(categories) if categories else t("analysis.no_specific_theme")
    mechanics_text = t("common.list_separator").join(mechanics) if mechanics else t("analysis.no_characteristic_mechanics")
    
    # Build summary using translation keys
    summary = t("analysis.summary.intro", 
                game_name=game_name, 
                year=year, 
                categories=categories_text)
    
    summary += t("analysis.summary.complexity_and_depth", 
                 complexity=complexity, 
                 depth=depth)
    
    summary += t("analysis.summary.features", 
                 mechanics=mechanics_text)
    
    if popularity == t("analysis.popularity.new_or_unrated"):
        summary += t("analysis.summary.popularity_unrated", popularity=popularity)
    else:
        summary += t("analysis.summary.popularity_rated", popularity=popularity)
    
    summary += "\n\n"
    
    summary += t("analysis.summary.barrier_and_replay", 
                 barrier=barrier_text, 
                 replayability=replayability_text)
    
    if player_types_display:
        summary += t("analysis.summary.suitable_for", 
                     player_types=t("common.list_separator").join(player_types_display))
    
    return summary