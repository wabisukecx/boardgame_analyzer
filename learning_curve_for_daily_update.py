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
        if data is None:
            return {}
        return data
    except Exception as e:
        print(f"Error loading configuration file ({file_path}): {str(e)}")
        return default_value or {}

def get_mechanic_complexity(mechanic_name, default_value=2.5):
    """Get complexity from mechanic name"""
    mechanics_data = load_yaml_config(MECHANICS_DATA_FILE)
    if mechanic_name in mechanics_data:
        if isinstance(mechanics_data[mechanic_name], dict) and 'complexity' in mechanics_data[mechanic_name]:
            return mechanics_data[mechanic_name]['complexity']
        elif isinstance(mechanics_data[mechanic_name], (int, float)):
            return mechanics_data[mechanic_name]
    return default_value

def get_category_complexity(category_name, default_value=2.5):
    """Get complexity from category name"""
    categories_data = load_yaml_config(CATEGORIES_DATA_FILE)
    if category_name in categories_data:
        if isinstance(categories_data[category_name], dict) and 'complexity' in categories_data[category_name]:
            return categories_data[category_name]['complexity']
        elif isinstance(categories_data[category_name], (int, float)):
            return categories_data[category_name]
    return default_value

def calculate_category_complexity(categories):
    """Calculate overall complexity score from category list"""
    if not categories:
        return 2.5
    complexity_scores = [get_category_complexity(cat['name']) for cat in categories]
    avg_complexity = sum(complexity_scores) / len(complexity_scores)
    category_count_factor = min(1.3, 1.0 + (len(categories) - 1) * 0.05)
    adjusted_complexity = avg_complexity * category_count_factor
    return min(5.0, max(1.0, adjusted_complexity))

def get_rank_complexity_value(rank_type, default_value=3.0):
    """Get complexity from rank type"""
    complexity_data = load_yaml_config(RANK_COMPLEXITY_FILE)
    if rank_type in complexity_data:
        if isinstance(complexity_data[rank_type], dict) and 'complexity' in complexity_data[rank_type]:
            return complexity_data[rank_type]['complexity']
        elif isinstance(complexity_data[rank_type], (int, float)):
            return complexity_data[rank_type]
    return default_value

def calculate_rank_position_score(rank_value):
    """Calculate game popularity/quality score from ranking position"""
    try:
        rank = int(rank_value)
        if rank <= 10:
            score = 5.0
        elif rank <= 100:
            score = 4.5 - (rank - 10) / 90 * 0.5
        elif rank <= 1000:
            score = 4.0 - (rank - 100) / 900 * 1.0
        elif rank <= 5000:
            score = 3.0 - (rank - 1000) / 4000 * 1.0
        else:
            score = max(1.0, 2.0 - math.log10(rank / 5000))
        return score
    except (ValueError, TypeError):
        return 2.5

def calculate_rank_complexity(ranks):
    """Calculate complexity score from ranking information"""
    if not ranks:
        return 3.0
    rank_scores = []
    for rank_info in ranks:
        rank_type = rank_info.get('type', 'boardgame')
        rank_value = rank_info.get('rank')
        if rank_value and rank_value != "Not Ranked":
            popularity_score = calculate_rank_position_score(rank_value)
            type_complexity = get_rank_complexity_value(rank_type)
            adjusted_score = (type_complexity * 0.8 + (popularity_score - 3.0) * 0.2)
            weight = 1.0
            if rank_type == "boardgame":
                weight = 1.0
            elif rank_type in ["strategygames", "wargames"]:
                weight = 1.2
            elif rank_type in ["familygames", "partygames", "childrensgames"]:
                weight = 0.8
            rank_scores.append((adjusted_score, weight))
    if not rank_scores:
        return 3.0
    total_weighted_score = sum(score * weight for score, weight in rank_scores)
    total_weight = sum(weight for _, weight in rank_scores)
    avg_score = total_weighted_score / total_weight
    return min(5.0, max(1.0, avg_score))

def get_mechanic_strategic_value(mechanic_name, default_value=3.0):
    """Get strategic value of specified mechanic"""
    mechanics_data = load_yaml_config(MECHANICS_DATA_FILE)
    if mechanic_name in mechanics_data:
        if isinstance(mechanics_data[mechanic_name], dict) and "strategic_value" in mechanics_data[mechanic_name]:
            return mechanics_data[mechanic_name]["strategic_value"]
        else:
            complexity = mechanics_data[mechanic_name] if isinstance(mechanics_data[mechanic_name], (int, float)) else 3.0
            estimated_value = min(5.0, complexity * 0.9)
            return max(1.0, estimated_value)
    return default_value

def get_mechanic_interaction_value(mechanic_name, default_value=3.0):
    """Get player interaction value of specified mechanic"""
    mechanics_data = load_yaml_config(MECHANICS_DATA_FILE)
    if mechanic_name in mechanics_data:
        if isinstance(mechanics_data[mechanic_name], dict) and "interaction_value" in mechanics_data[mechanic_name]:
            return mechanics_data[mechanic_name]["interaction_value"]
        else:
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
            return default_value
    return default_value

def evaluate_playtime_complexity(game_data):
    """Evaluate complexity bonus based on playing time"""
    playtime_info = {
        "strategic_bonus": 0.0,
        "interaction_modifier": 0.0,
        "decision_density": 0.0,
        "complexity_factor": 1.0
    }
    if 'playing_time' not in game_data:
        return playtime_info
    try:
        play_time = int(game_data['playing_time'])
        if play_time > 180:
            playtime_info["strategic_bonus"] = 0.3
        elif play_time > 120:
            playtime_info["strategic_bonus"] = 0.2
        elif play_time > 60:
            playtime_info["strategic_bonus"] = 0.1
        if play_time <= 30:
            playtime_info["interaction_modifier"] = 0.2
        elif play_time >= 180:
            playtime_info["interaction_modifier"] = 0.1
        mechanics_count = len(game_data.get('mechanics', []))
        if play_time <= 30 and mechanics_count >= 3:
            playtime_info["decision_density"] = 0.2
        elif 30 < play_time <= 60 and mechanics_count >= 4:
            playtime_info["decision_density"] = 0.15
        elif 60 < play_time <= 120 and mechanics_count >= 5:
            playtime_info["decision_density"] = 0.1
        if play_time < 20:
            playtime_info["complexity_factor"] = 0.85
        elif play_time < 45:
            playtime_info["complexity_factor"] = 0.95
        elif play_time > 180:
            playtime_info["complexity_factor"] = 1.1
    except (ValueError, TypeError):
        pass
    return playtime_info

def estimate_decision_points(mechanics, game_data=None):
    """Estimate decision points (with readjusted weights)"""
    if not mechanics:
        return 2.5
    strategic_values = [get_mechanic_strategic_value(m['name']) for m in mechanics]
    if strategic_values:
        strategic_values.sort(reverse=True)
        if len(strategic_values) == 1:
            weights = [1.0]
        elif len(strategic_values) == 2:
            weights = [0.65, 0.35]
        elif len(strategic_values) == 3:
            weights = [0.55, 0.30, 0.15]
        else:
            weights = []
            for i in range(len(strategic_values)):
                if i == 0:
                    weights.append(0.5)
                elif i == 1:
                    weights.append(0.25)
                else:
                    remaining_weight = 0.25
                    remaining_count = len(strategic_values) - 2
                    min_weight = 0.5 / max(1, remaining_count)
                    weights.append(max(min_weight, remaining_weight / remaining_count))
        weights_sum = sum(weights)
        weights = [w / weights_sum for w in weights]
        weighted_sum = sum(v * w for v, w in zip(strategic_values, weights))
        unique_values = set(strategic_values)
        value_range = max(strategic_values) - min(strategic_values) if len(strategic_values) > 1 else 0
        diversity_bonus = min(0.4, len(unique_values) * 0.07 + value_range * 0.1)
        decision_points = weighted_sum + diversity_bonus
        if game_data:
            playtime_info = evaluate_playtime_complexity(game_data)
            decision_points += playtime_info["decision_density"] * 0.8
            complexity_factor = 1.0 + (playtime_info["complexity_factor"] - 1.0) * 0.9
            decision_points *= complexity_factor
    else:
        decision_points = 2.5
    return min(5.0, max(1.0, decision_points))

def estimate_interaction_complexity(categories, mechanics=None, game_data=None):
    """Estimate interaction complexity (with readjusted weights)"""
    if not categories and not mechanics:
        return 2.5
    category_values = []
    for c in categories:
        category_name = c.get('name', '')
        categories_data = load_yaml_config(CATEGORIES_DATA_FILE)
        if category_name in categories_data:
            if isinstance(categories_data[category_name], dict) and 'interaction_value' in categories_data[category_name]:
                category_values.append(categories_data[category_name]['interaction_value'])
            else:
                high_interaction_categories = ['Negotiation', 'Political', 'Bluffing', 'Party Game', 'Fighting']
                if category_name in high_interaction_categories:
                    category_values.append(4.5)
                elif category_name in ['Abstract Strategy', 'Puzzle', 'Solo / Solitaire Game']:
                    category_values.append(2.0)
                else:
                    category_values.append(3.0)
    mechanic_values = []
    if mechanics:
        for m in mechanics:
            mechanic_values.append(get_mechanic_interaction_value(m.get('name', '')))
    if category_values and mechanic_values:
        all_values = []
        for value in category_values:
            all_values.append((value, 0.6 / len(category_values)))
        for value in mechanic_values:
            all_values.append((value, 0.4 / len(mechanic_values)))
        all_values.sort(key=lambda x: x[0], reverse=True)
        values = [v[0] for v in all_values]
        weights = [v[1] for v in all_values]
    else:
        values = category_values or mechanic_values
        values.sort(reverse=True)
        if len(values) <= 3:
            if len(values) == 1:
                weights = [1.0]
            elif len(values) == 2:
                weights = [0.65, 0.35]
            else:
                weights = [0.55, 0.30, 0.15]
        else:
            weights = []
            top_n = min(3, len(values))
            for i in range(len(values)):
                if i < top_n:
                    if i == 0:
                        weights.append(0.3)
                    elif i == 1:
                        weights.append(0.2)
                    else:
                        weights.append(0.15)
                else:
                    remaining_count = len(values) - top_n
                    weights.append(0.35 / remaining_count)
    weights_sum = sum(weights)
    weights = [w / weights_sum for w in weights]
    interaction_complexity = sum(v * w for v, w in zip(values, weights))
    if game_data:
        playtime_info = evaluate_playtime_complexity(game_data)
        interaction_complexity += playtime_info["interaction_modifier"] * 0.85
        complexity_factor = 1.0 + (playtime_info["complexity_factor"] - 1.0) * 0.9
        interaction_complexity *= complexity_factor
    if game_data and 'publisher_max_players' in game_data:
        try:
            max_players = int(game_data['publisher_max_players'])
            if max_players >= 5:
                interaction_complexity *= 1.10
            elif max_players >= 4:
                interaction_complexity *= 1.07
        except (ValueError, TypeError):
            pass
    return min(5.0, max(1.0, interaction_complexity))

def calculate_rules_complexity(game_data):
    """Calculate rules complexity"""
    mechanics = game_data.get('mechanics', [])
    mechanics_complexity_sum = sum(get_mechanic_complexity(m['name']) for m in mechanics)
    avg_mechanic_complexity = mechanics_complexity_sum / max(1, len(mechanics))
    mechanics_count_factor = min(1.5, 1.0 + (len(mechanics) / 10))
    min_age = float(game_data.get('publisher_min_age', 10))
    age_complexity = min(4.0, (min_age - 6) / 3)
    base_weight = float(game_data.get('weight', 3.0))
    rules_complexity = (
        (avg_mechanic_complexity * mechanics_count_factor) * 0.6 +
        age_complexity * 0.2 +
        base_weight * 0.2
    )
    return min(5.0, max(1.0, rules_complexity))

def calculate_strategic_depth_improved(game_data):
    """
    Improved strategic depth calculation.
    Returns a tuple to avoid recomputing sub-metrics later:
    (strategic_depth, decision_points, interaction_complexity, rules_complexity)
    """
    base_weight = float(game_data.get('weight', 3.0))
    decision_points = estimate_decision_points(game_data.get('mechanics', []), game_data)
    interaction_complexity = estimate_interaction_complexity(
        game_data.get('categories', []), game_data.get('mechanics', []), game_data)
    rules_complexity = calculate_rules_complexity(game_data)
    mechanics = game_data.get('mechanics', [])
    mechanics_names = [m['name'] for m in mechanics]
    high_strategy_values = [(name, get_mechanic_strategic_value(name)) for name in mechanics_names]
    high_strategy_values.sort(key=lambda x: x[1], reverse=True)
    strategy_bonus = 0
    mechanic_count = len(high_strategy_values)
    if mechanic_count > 0:
        top_n = min(3, mechanic_count)
        weights = [0.5, 0.3, 0.2][:top_n]
        weights_sum = sum(weights)
        weights = [w / weights_sum for w in weights]
        for i in range(top_n):
            name, value = high_strategy_values[i]
            impact = 0.1 * (value - 2.5)
            strategy_bonus += impact * weights[i]
    if mechanic_count > 0:
        decay_factor = 1.0 / (1.0 + math.log(mechanic_count, 10))
        strategy_bonus = min(0.8, strategy_bonus * decay_factor)
    # Hidden information bonus
    hidden_info_mechanics = {
        'Roles with Asymmetric Information', 'Secret Unit Deployment',
        'Betting and Bluffing', 'Hidden Victory Points', 'Closed Drafting',
        'Communication Limits', 'Deduction', 'Predictive Bid',
    }
    hidden_info_count = sum(1 for m in mechanics_names if m in hidden_info_mechanics)
    hidden_info_bonus = min(0.3, hidden_info_count * 0.1)
    playtime_info = evaluate_playtime_complexity(game_data)
    playtime_strategic_bonus = playtime_info["strategic_bonus"]
    # Normalized weighted sum -- additive bonuses are individually capped
    strategy_bonus_capped    = min(0.4, strategy_bonus)
    playtime_bonus_capped    = min(0.1, playtime_strategic_bonus * 0.6)
    hidden_info_bonus_capped = min(0.3, hidden_info_bonus)
    strategic_depth = (
        base_weight * 0.20 +
        decision_points * 0.35 +
        rules_complexity * 0.10 +
        interaction_complexity * 0.25 +
        base_weight * 0.10 +
        strategy_bonus_capped +
        playtime_bonus_capped +
        hidden_info_bonus_capped
    )
    complexity_factor = playtime_info["complexity_factor"]
    complexity_factor = 1.0 + (complexity_factor - 1.0) * 0.95
    strategic_depth *= complexity_factor
    strategic_depth = min(5.0, max(1.0, strategic_depth))
    return round(strategic_depth, 2), decision_points, interaction_complexity, rules_complexity

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
        return 1.1
    elif rank <= 500:
        return 1.07
    elif rank <= 1000:
        return 1.02
    else:
        return 1.0

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
        return 1.1
    elif years_since_publication >= 10:
        return 1.07
    elif years_since_publication >= 5:
        return 1.05
    else:
        return 1.0

def calculate_replayability(game_data):
    """Calculate game replayability"""
    base_score = 2.0
    diversity_score = 0.0
    mechanics_count = len(game_data.get('mechanics', []))
    diversity_score += min(0.7, mechanics_count * 0.1)
    high_replay_mechanics = [
        'Variable Set-up', 'Modular Board', 'Variable Player Powers',
        'Deck Building', 'Campaign / Battle Card Driven',
        'Scenario / Mission / Campaign Game', 'Deck Construction',
        'Engine Building', 'Hidden Roles', 'Asymmetric Gameplay'
    ]
    medium_replay_mechanics = [
        'Card Drafting', 'Worker Placement', 'Tech Trees / Tech Tracks',
        'Multi-Use Cards', 'Area Control', 'Route/Network Building',
        'Tile Placement', 'Resource Management', 'Drafting'
    ]
    high_replay_count = sum(
        1 for m in game_data.get('mechanics', []) if m.get('name') in high_replay_mechanics
    )
    medium_replay_count = sum(
        1 for m in game_data.get('mechanics', []) if m.get('name') in medium_replay_mechanics
    )
    diversity_score += min(0.8, (high_replay_count * 0.2) + (medium_replay_count * 0.1))
    categories_count = len(game_data.get('categories', []))
    diversity_score += min(0.4, categories_count * 0.1)
    # Rank bonus: continuous logarithmic scale (0.0-0.6)
    rank = get_rank_value(game_data)
    rank_bonus = 0.0
    if rank is not None:
        rank_bonus = min(0.6, max(0.0, (calculate_rank_position_score(rank) - 1.0) / 4.0 * 0.6))
    # Playtime adjustment (short games replayed more easily)
    try:
        play_time = int(game_data.get('playing_time', 60))
        if play_time <= 30:
            playtime_replay_bonus = 0.3
        elif play_time <= 60:
            playtime_replay_bonus = 0.15
        elif play_time >= 180:
            playtime_replay_bonus = -0.2
        else:
            playtime_replay_bonus = 0.0
    except (ValueError, TypeError):
        playtime_replay_bonus = 0.0
    year_published = get_year_published(game_data)
    longevity_factor = calculate_longevity_factor(year_published)
    replayability = (base_score + diversity_score + rank_bonus) * longevity_factor + playtime_replay_bonus
    return round(max(1.0, min(5.0, replayability)), 2)

def calculate_learning_curve(game_data):
    """
    Calculate learning curve information from game data
    Improved version using category and ranking information

    Parameters:
    game_data (dict): Game details

    Returns:
    dict: Learning curve information
    """
    base_weight = float(game_data.get('weight', 3.0))
    mechanics_names = [m['name'] for m in game_data.get('mechanics', [])]
    mechanics_complexity = 0
    mechanic_count = 0
    for mechanic in mechanics_names:
        mechanic_complexity = get_mechanic_complexity(mechanic)
        mechanics_complexity += mechanic_complexity
        mechanic_count += 1
    avg_mechanic_complexity = (
        mechanics_complexity / max(1, mechanic_count) if mechanic_count > 0 else 3.0
    )
    category_complexity = calculate_category_complexity(game_data.get('categories', []))
    rank_complexity = calculate_rank_complexity(game_data.get('ranks', []))
    complexity_factor = (category_complexity * 0.6 + rank_complexity * 0.4)

    # Strategic depth and sub-metrics -- single pass, no re-computation
    strategic_depth_result = calculate_strategic_depth_improved(game_data)
    strategic_depth      = strategic_depth_result[0]
    rules_complexity_val = strategic_depth_result[3]

    # Initial barrier: coefficients sum to 1.0, incorporating rules_complexity
    initial_barrier = (
        avg_mechanic_complexity * 0.40 +
        rules_complexity_val    * 0.25 +
        base_weight             * 0.20 +
        complexity_factor       * 0.15
    )
    mechanics_count_barrier_factor = min(1.25, max(1.0, len(mechanics_names) / 5))
    initial_barrier = min(5.0, initial_barrier * mechanics_count_barrier_factor)
    initial_barrier = round(initial_barrier, 2)

    replayability  = calculate_replayability(game_data)
    rank           = get_rank_value(game_data)
    year_published = get_year_published(game_data)

    # --- Additional metrics ---
    solo_friendly_mechanics = {
        'Solo / Solitaire Game', 'Cooperative Game', 'Scenario / Mission / Campaign Game'
    }
    mechanics_names_set = set(mechanics_names)
    if 'Solo / Solitaire Game' in mechanics_names_set:
        solo_friendliness = 5.0
    elif 'Cooperative Game' in mechanics_names_set:
        solo_friendliness = 4.0
    elif any(m in solo_friendly_mechanics for m in mechanics_names_set):
        solo_friendliness = 3.5
    else:
        try:
            solo_friendliness = 3.0 if int(game_data.get('publisher_min_players', 2)) == 1 else 1.0
        except (ValueError, TypeError):
            solo_friendliness = 1.0

    try:
        min_p = int(game_data.get('publisher_min_players', 2))
        max_p = int(game_data.get('publisher_max_players', 4))
        player_scalability = min(5.0, 2.0 + max(0, max_p - min_p) * 0.5)
    except (ValueError, TypeError):
        player_scalability = 3.0

    high_luck_mechanics = {
        'Dice Rolling', 'Random Production', 'Push Your Luck',
        'Roll / Spin and Move', 'Chit-Pull System', 'Critical Hits and Failures'
    }
    low_luck_mechanics = {
        'Worker Placement', 'Engine Building', 'Tech Trees / Tech Tracks',
        'Deck Construction', 'Action Points'
    }
    luck_count     = sum(1 for m in mechanics_names if m in high_luck_mechanics)
    strategy_count = sum(1 for m in mechanics_names if m in low_luck_mechanics)
    luck_dependency = min(5.0, max(1.0, 3.0 + luck_count * 0.5 - strategy_count * 0.4))

    # Build learning curve dict
    learning_curve = {
        "initial_barrier":      initial_barrier,
        "strategic_depth":      strategic_depth,
        "replayability":        replayability,
        "mechanics_complexity": round(avg_mechanic_complexity, 2),
        "mechanics_count":      len(mechanics_names),
        "bgg_weight":           base_weight,
        "bgg_rank":             rank,
        "year_published":       year_published,
        "category_complexity":  round(category_complexity, 2),
        "rank_complexity":      round(rank_complexity, 2),
        # Sub-metrics from single-pass calculation
        "decision_points":        strategic_depth_result[1],
        "interaction_complexity": strategic_depth_result[2],
        "rules_complexity":       strategic_depth_result[3],
        # Additional metrics
        "solo_friendliness":  round(solo_friendliness, 2),
        "player_scalability": round(player_scalability, 2),
        "luck_dependency":    round(luck_dependency, 2),
    }

    # Learning curve type
    if initial_barrier > 4.3:
        if strategic_depth > 4.3:
            learning_curve["learning_curve_type"] = "steep"
        elif strategic_depth > 3.5:
            learning_curve["learning_curve_type"] = "steep_then_moderate"
        else:
            learning_curve["learning_curve_type"] = "steep_then_shallow"
    elif initial_barrier > 3.5:
        if strategic_depth > 4.3:
            learning_curve["learning_curve_type"] = "moderate_then_deep"
        elif strategic_depth > 3.5:
            learning_curve["learning_curve_type"] = "moderate"
        else:
            learning_curve["learning_curve_type"] = "moderate_then_shallow"
    else:
        if strategic_depth > 4.3:
            learning_curve["learning_curve_type"] = "gentle_then_deep"
        elif strategic_depth > 3.5:
            learning_curve["learning_curve_type"] = "gentle_then_moderate"
        else:
            learning_curve["learning_curve_type"] = "gentle"

    # Player types
    player_types = []
    if initial_barrier < 3.0 and strategic_depth < 3.5:
        player_types.append("beginner")
    if initial_barrier < 4.0 and strategic_depth < 4.5:
        player_types.append("casual")
    if strategic_depth >= 3.0:
        player_types.append("experienced")
    if initial_barrier > 3.0 and strategic_depth > 3.5:
        player_types.append("hardcore")
    if strategic_depth > 3.8:
        player_types.append("strategist")
    if len(game_data.get('mechanics', [])) >= 5 and strategic_depth > 3.5:
        player_types.append("system_master")
    if replayability >= 3.8:
        player_types.append("replayer")
    if rank is not None and rank <= 1000:
        player_types.append("trend_follower")
    if year_published is not None and year_published <= 2000:
        player_types.append("classic_lover")
    if not player_types:
        if strategic_depth >= 3.5:
            player_types.append("experienced")
        elif initial_barrier >= 3.5:
            player_types.append("hardcore")
        else:
            player_types.append("casual")
    learning_curve["player_types"] = player_types

    learning_curve["playtime_analysis"] = evaluate_playtime_complexity(game_data)

    # Mastery time: consider both strategic_depth AND initial_barrier
    if strategic_depth > 4.3:
        learning_curve["mastery_time"] = "medium_to_long" if len(mechanics_names) >= 6 else "long"
    elif strategic_depth > 3.2:
        learning_curve["mastery_time"] = "medium_to_long" if initial_barrier > 4.0 else "medium"
    else:
        learning_curve["mastery_time"] = "medium" if initial_barrier > 4.0 else "short"

    return learning_curve
