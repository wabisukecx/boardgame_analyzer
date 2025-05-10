"""
Improved board game similarity analysis module
Advanced similarity evaluation based on learning curves and game characteristics
"""

from typing import Dict, List, Any, Tuple
from src.utils.language import t

def analyze_similarity_reasons_improved(
    game1: Dict[str, Any],
    game2: Dict[str, Any]
) -> List[Tuple[str, float, str]]:
    """Analyze similarity reasons between two games in detail
    
    Args:
        game1 (Dict[str, Any]): First game data
        game2 (Dict[str, Any]): Second game data
        
    Returns:
        List[Tuple[str, float, str]]: List of tuples containing reason, similarity, and description
    """
    reasons = []
    learning1 = game1.get('learning_analysis', {})
    learning2 = game2.get('learning_analysis', {})
    
    # List of common metrics (key, display_name, description, weight)
    learning_metrics = [
        ('initial_barrier', t('metrics.initial_barrier'), t('similarity.reasons.initial_barrier_desc'), 1.0),
        ('strategic_depth', t('metrics.strategic_depth'), t('similarity.reasons.strategic_depth_desc'), 1.2),
        ('replayability', t('metrics.replayability'), t('similarity.reasons.replayability_desc'), 1.0),
        ('decision_points', t('metrics.decision_points'), t('similarity.reasons.decision_points_desc'), 0.9),
        ('interaction_complexity', t('metrics.interaction_complexity'), t('similarity.reasons.interaction_desc'), 0.9),
        ('rules_complexity', t('metrics.rules_complexity'), t('similarity.reasons.rules_desc'), 0.8),
    ]
    
    # Compare learning curve metrics
    if learning1 and learning2:
        for key, display_name, description, weight in learning_metrics:
            if key in learning1 and key in learning2:
                value1 = float(learning1.get(key, 0))
                value2 = float(learning2.get(key, 0))
                diff = abs(value1 - value2)
                
                # Consider similar if difference is small (max 0.7 point difference)
                if diff <= 0.7:
                    # Calculate similarity score
                    similarity_score = (0.7 - diff) / 0.7 * weight
                    
                    # Generate description based on value range
                    level_description = get_level_description(value1, key)
                    
                    # Add only if score is high enough
                    if similarity_score > 0.5:
                        reasons.append((
                            t("similarity.reasons.similar_metric", metric=display_name),
                            similarity_score,
                            t("similarity.reasons.both_games_have", 
                              description=level_description, 
                              value1=f"{value1:.1f}", 
                              value2=f"{value2:.1f}")
                        ))
        
        # Compare learning curve types
        curve_type1 = learning1.get('learning_curve_type', '')
        curve_type2 = learning2.get('learning_curve_type', '')
        if curve_type1 and curve_type2 and curve_type1 == curve_type2:
            reasons.append((
                t("similarity.reasons.same_learning_curve"),
                1.1,  # High score for exact match
                t("similarity.reasons.same_learning_pattern", curve_type=curve_type1)
            ))
        elif curve_type1 and curve_type2:
            # Partial match (e.g., steep_then_moderate vs steep)
            if curve_type1.startswith(curve_type2) or curve_type2.startswith(curve_type1):
                reasons.append((
                    t("similarity.reasons.similar_learning_curve"),
                    0.7,
                    t("similarity.reasons.similar_learning_pattern", 
                      curve_type1=curve_type1, 
                      curve_type2=curve_type2)
                ))
        
        # Compare mastery time
        mastery1 = learning1.get('mastery_time', '')
        mastery2 = learning2.get('mastery_time', '')
        if mastery1 and mastery2 and mastery1 == mastery2:
            reasons.append((
                t("similarity.reasons.same_mastery_time"),
                0.9,
                t("similarity.reasons.both_mastery_time", mastery_time=mastery1)
            ))
    
    # Compare player types (high importance)
    player_types1 = set(learning1.get('player_types', []))
    player_types2 = set(learning2.get('player_types', []))
    common_player_types = player_types1.intersection(player_types2)
    
    if common_player_types:
        # Higher score for more common types
        overlap_ratio = len(common_player_types) / max(len(player_types1), len(player_types2))
        score = min(1.2, 0.6 + overlap_ratio * 0.6)  # Max 1.2, min 0.6
        
        reasons.append((
            t("similarity.reasons.common_player_types"),
            score,
            t("similarity.reasons.suitable_for_same_players", 
              player_types=t("common.list_separator").join(common_player_types))
        ))
    
    # Compare categories (basic similarity element)
    g1_categories = set(
        [cat.get('name', '') for cat in game1.get('categories', [])
         if isinstance(cat, dict) and 'name' in cat]
    )
    g2_categories = set(
        [cat.get('name', '') for cat in game2.get('categories', [])
         if isinstance(cat, dict) and 'name' in cat]
    )
    common_categories = g1_categories.intersection(g2_categories)
    
    if common_categories:
        # Consider importance of categories
        important_categories = {
            'Strategy', 'Economic', 'Civilization', 'Abstract Strategy',
            'City Building', 'Wargame', 'Card Game', 'Worker Placement'
        }
        important_matches = important_categories.intersection(common_categories)
        
        # High score for important category matches
        if important_matches:
            reasons.append((
                t("similarity.reasons.important_categories"),
                1.0,
                t("similarity.reasons.important_category_match", 
                  categories=t("common.list_separator").join(important_matches))
            ))
        
        # Other common categories
        other_matches = common_categories - important_categories
        if other_matches:
            reasons.append((
                t("similarity.common_categories"),
                0.8,
                t("similarity.reasons.common_categories_list", 
                  categories=t("common.list_separator").join(other_matches))
            ))
    
    # Compare mechanics (basic similarity element)
    g1_mechanics = set(
        [mech.get('name', '') for mech in game1.get('mechanics', [])
         if isinstance(mech, dict) and 'name' in mech]
    )
    g2_mechanics = set(
        [mech.get('name', '') for mech in game2.get('mechanics', [])
         if isinstance(mech, dict) and 'name' in mech]
    )
    common_mechanics = g1_mechanics.intersection(g2_mechanics)
    
    if common_mechanics:
        # Consider importance of mechanics
        strategic_mechanics = {
            'Worker Placement', 'Engine Building', 'Deck Building', 
            'Area Control', 'Resource Management', 'Tech Trees / Tech Tracks',
            'Variable Player Powers', 'Draft', 'Action Points'
        }
        strategic_matches = strategic_mechanics.intersection(common_mechanics)
        
        # High score for strategic mechanic matches
        if strategic_matches:
            reasons.append((
                t("similarity.reasons.important_mechanics"),
                1.1,
                t("similarity.reasons.important_mechanic_match", 
                  mechanics=t("common.list_separator").join(strategic_matches))
            ))
        
        # Other common mechanics
        other_matches = common_mechanics - strategic_mechanics
        if other_matches:
            reasons.append((
                t("similarity.common_mechanics"),
                0.9,
                t("similarity.reasons.common_mechanics_list", 
                  mechanics=t("common.list_separator").join(other_matches))
            ))
    
    # Compare play time
    try:
        time1 = int(game1.get('playing_time', 0))
        time2 = int(game2.get('playing_time', 0))
        if time1 > 0 and time2 > 0:
            # Calculate time difference ratio
            time_diff_ratio = abs(time1 - time2) / max(time1, time2)
            
            # Consider similar if difference is within 30%
            if time_diff_ratio <= 0.3:
                reasons.append((
                    t("similarity.reasons.similar_playtime"),
                    0.8,
                    t("similarity.reasons.playtime_close", 
                      time1=time1, 
                      time2=time2)
                ))
    except (ValueError, TypeError):
        pass
    
    # Compare publication year (low importance)
    try:
        year1 = int(game1.get('year_published', 0))
        year2 = int(game2.get('year_published', 0))
        if year1 > 0 and year2 > 0 and abs(year1 - year2) <= 5:
            reasons.append((
                t("similarity.close_publication_year"),
                0.4,  # Low score
                t("similarity.reasons.close_years", year1=year1, year2=year2)
            ))
    except (ValueError, TypeError):
        pass
    
    # If no reasons found (extract common keywords from descriptions)
    if not reasons:
        g1_desc = str(game1.get('description', '')).lower()
        g2_desc = str(game2.get('description', '')).lower()
        
        # Simple word splitting
        g1_words = set(g1_desc.split())
        g2_words = set(g2_desc.split())
        common_words = g1_words.intersection(g2_words)
        
        # Exclude common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'as', 'of', 'from'}
        meaningful_words = [word for word in common_words if word not in stop_words and len(word) > 3]
        
        if meaningful_words:
            reasons.append((
                t("similarity.common_keywords"),
                0.3,  # Very low score
                t("similarity.reasons.common_keywords_list", 
                  keywords=t("common.list_separator").join(meaningful_words[:5]))
            ))
        else:
            reasons.append((
                t("similarity.reasons.overall_similarity"),
                0.2,  # Minimum score
                t("similarity.overall_similarity")
            ))
    
    # Sort by score descending
    reasons.sort(key=lambda x: x[1], reverse=True)
    return reasons

def get_level_description(value: float, metric_key: str) -> str:
    """Get description text based on metric value
    
    Args:
        value (float): Metric value
        metric_key (str): Metric key name
        
    Returns:
        str: Description text
    """
    # Initial learning barrier
    if metric_key == 'initial_barrier':
        if value >= 4.5:
            return t("similarity.levels.initial_barrier.very_high")
        elif value >= 4.0:
            return t("similarity.levels.initial_barrier.high")
        elif value >= 3.0:
            return t("similarity.levels.initial_barrier.medium")
        else:
            return t("similarity.levels.initial_barrier.low")
    
    # Strategic depth
    elif metric_key == 'strategic_depth':
        if value >= 4.5:
            return t("similarity.levels.strategic_depth.very_deep")
        elif value >= 4.0:
            return t("similarity.levels.strategic_depth.deep")
        elif value >= 3.0:
            return t("similarity.levels.strategic_depth.medium")
        else:
            return t("similarity.levels.strategic_depth.shallow")
    
    # Replayability
    elif metric_key == 'replayability':
        if value >= 4.5:
            return t("similarity.levels.replayability.very_high")
        elif value >= 4.0:
            return t("similarity.levels.replayability.high")
        elif value >= 3.0:
            return t("similarity.levels.replayability.medium")
        else:
            return t("similarity.levels.replayability.low")
    
    # Decision points
    elif metric_key == 'decision_points':
        if value >= 4.5:
            return t("similarity.levels.decision_points.very_many")
        elif value >= 4.0:
            return t("similarity.levels.decision_points.many")
        elif value >= 3.0:
            return t("similarity.levels.decision_points.medium")
        else:
            return t("similarity.levels.decision_points.few")
    
    # Player interaction
    elif metric_key == 'interaction_complexity':
        if value >= 4.5:
            return t("similarity.levels.interaction.very_high")
        elif value >= 4.0:
            return t("similarity.levels.interaction.high")
        elif value >= 3.0:
            return t("similarity.levels.interaction.medium")
        else:
            return t("similarity.levels.interaction.low")
    
    # Rules complexity
    elif metric_key == 'rules_complexity':
        if value >= 4.5:
            return t("similarity.levels.rules.very_complex")
        elif value >= 4.0:
            return t("similarity.levels.rules.complex")
        elif value >= 3.0:
            return t("similarity.levels.rules.medium")
        else:
            return t("similarity.levels.rules.simple")
    
    # Default
    else:
        if value >= 4.0:
            return t("similarity.levels.default.high")
        elif value >= 3.0:
            return t("similarity.levels.default.medium")
        else:
            return t("similarity.levels.default.low")

def calculate_overall_similarity(
    game1: Dict[str, Any],
    game2: Dict[str, Any]
) -> float:
    """Calculate overall similarity between two games
    
    Args:
        game1 (Dict[str, Any]): First game data
        game2 (Dict[str, Any]): Second game data
        
    Returns:
        float: Overall similarity score (0.0-1.0)
    """
    # Get similarity reasons
    similarity_reasons = analyze_similarity_reasons_improved(game1, game2)
    
    if not similarity_reasons:
        return 0.0
    
    # Sum scores from all reasons
    total_score = sum(reason[1] for reason in similarity_reasons)
    
    # Normalize score (assuming max score is 5.0)
    normalized_score = min(1.0, total_score / 5.0)
    
    return normalized_score

def get_formatted_similarity_reasons(
    game1: Dict[str, Any],
    game2: Dict[str, Any]
) -> List[str]:
    """Return formatted list of similarity reasons
    
    Args:
        game1 (Dict[str, Any]): First game data
        game2 (Dict[str, Any]): Second game data
        
    Returns:
        List[str]: List of formatted similarity reasons
    """
    reasons = analyze_similarity_reasons_improved(game1, game2)
    
    # Format for display (score is internal, so format without it)
    formatted_reasons = [f"{reason[0]}: {reason[2]}" for reason in reasons[:5]]
    
    # If no reasons
    if not formatted_reasons:
        return [t("similarity.overall_similarity")]
    
    return formatted_reasons