"""
src/analysis/similarity.py - Module providing board game similarity search functionality
"""

import numpy as np
import streamlit as st
import pickle
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import pandas as pd
from collections import Counter
import io
from typing import Dict, List, Any, Tuple, Optional
import logging
import os
import platform

# Import from existing modules
from src.analysis.mechanic_complexity import (
    add_missing_mechanic, 
    get_complexity, 
    flush_pending_mechanics
)
from src.analysis.category_complexity import (
    add_missing_category,
    get_category_complexity
)
from src.analysis.rank_complexity import (
    add_missing_rank_type,
    get_rank_complexity_value
)

# Import language utilities
from src.utils.language import t, get_game_display_name, get_game_secondary_name, format_language_caption

# Logging configuration
logger = logging.getLogger("similarity_module")

def setup_japanese_fonts():
    """
    Set up Japanese fonts
    Select appropriate fonts based on platform
    """
    try:
        # First list available fonts
        from matplotlib.font_manager import fontManager
        available_fonts = set([f.name for f in fontManager.ttflist])       
        system = platform.system()
        
        # Font candidates by platform
        if system == 'Windows':
            font_options = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'Arial Unicode MS']
        elif system == 'Darwin':  # macOS
            font_options = ['Hiragino Sans', 'Hiragino Maru Gothic Pro', 'Osaka', 'AppleGothic']
        elif system == 'Linux':
            font_options = ['Noto Sans CJK JP', 'IPAGothic', 'VL Gothic', 'Droid Sans Japanese']
        else:
            font_options = []
        
        # Add fonts that might work on any platform
        font_options.extend(['DejaVu Sans', 'Arial', 'Tahoma', 'Verdana'])
        
        # Filter available fonts
        available_options = [f for f in font_options if f in available_fonts]
        
        # Set available font if found
        if available_options:
            font_family = available_options[0]
            matplotlib.rcParams['font.family'] = font_family
            return True
        
        # Set sans-serif as fallback when font not found
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Helvetica', 'sans-serif']
        logger.warning(t("warnings.font_not_found"))
        
        return False
    except Exception as e:
        logger.error(f"Font setup error: {e}")
        return False

# Data loading
@st.cache_resource(show_spinner=True)
def load_data(data_file: str) -> Optional[Dict[str, Any]]:
    """Function to load embedding data
    
    Args:
        data_file (str): Data file path
        
    Returns:
        Optional[Dict[str, Any]]: Loaded data, None on error
    """
    try:
        if not os.path.exists(data_file):
            logger.error(t("errors.file_not_found", filename=data_file))
            return None
            
        with open(data_file, 'rb') as f:
            data = pickle.load(f)
            
        # Validate data
        required_keys = ['games', 'game_data_list', 'embeddings', 'similarity_matrix']
        for key in required_keys:
            if key not in data:
                logger.error(t("errors.missing_data_key", key=key))
                return None
        
        # Process game data to add unknown mechanics/categories/rankings to YAML
        process_game_data_for_yaml(data['game_data_list'])
                
        return data
    except Exception as e:
        logger.error(t("errors.file_load_failed", error=str(e)))
        return None

# Function to process game data and add unknown mechanics/categories/rankings to YAML
def process_game_data_for_yaml(game_data_list: List[Dict[str, Any]]) -> None:
    """
    Process game data and add mechanics/categories/rankings not in YAML
    
    Args:
        game_data_list (List[Dict[str, Any]]): List of game data
    """
    try:
        # Extract mechanics, categories, and rankings from each game
        for game_data in game_data_list:
            # Process mechanics
            if 'mechanics' in game_data and isinstance(game_data['mechanics'], list):
                for mechanic in game_data['mechanics']:
                    if isinstance(mechanic, dict) and 'name' in mechanic:
                        mechanic_name = mechanic['name']
                        # Use existing add_missing_mechanic function
                        add_missing_mechanic(mechanic_name)
            
            # Process categories
            if 'categories' in game_data and isinstance(game_data['categories'], list):
                for category in game_data['categories']:
                    if isinstance(category, dict) and 'name' in category:
                        category_name = category['name']
                        # Use existing add_missing_category function
                        add_missing_category(category_name)
            
            # Process rankings
            if 'ranks' in game_data and isinstance(game_data['ranks'], list):
                for rank in game_data['ranks']:
                    if isinstance(rank, dict) and 'type' in rank:
                        rank_type = rank['type']
                        # Use existing add_missing_rank_type function
                        add_missing_rank_type(rank_type)
        
        # Save pending mechanics
        flush_pending_mechanics()
        
        logger.info(t("info.yaml_update_complete"))
    except Exception as e:
        logger.error(t("errors.yaml_processing_error", error=str(e)))

# Extract list of categories and mechanics
def extract_categories_and_mechanics(game_data_list: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    """Function to extract list of categories and mechanics from game data
    
    Args:
        game_data_list (List[Dict[str, Any]]): List of game data
        
    Returns:
        Tuple[List[str], List[str]]: Lists of categories and mechanics
    """
    all_categories = set()
    all_mechanics = set()
    
    for game in game_data_list:
        # Collect categories
        if 'categories' in game and isinstance(game['categories'], list):
            categories = [cat.get('name', '') for cat in game['categories'] 
                          if isinstance(cat, dict) and 'name' in cat]
            all_categories.update(categories)
        
        # Collect mechanics
        if 'mechanics' in game and isinstance(game['mechanics'], list):
            mechanics = [mech.get('name', '') for mech in game['mechanics'] 
                         if isinstance(mech, dict) and 'name' in mech]
            all_mechanics.update(mechanics)
    
    return sorted(list(all_categories)), sorted(list(all_mechanics))

# Display filter settings UI
def display_filter_ui(
    categories: List[str],
    mechanics: List[str]
) -> Tuple[List[str], List[str]]:
    """Function to display filter settings UI
    
    Args:
        categories (List[str]): List of categories
        mechanics (List[str]): List of mechanics
        
    Returns:
        Tuple[List[str], List[str]]: Selected lists of categories and mechanics
    """
    with st.expander(t("similarity.search_filter")):
        st.markdown(f"### {t('similarity.filter_title')}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### {t('similarity.category_filter')}")
            selected_categories = st.multiselect(
                t("similarity.select_categories"),
                options=categories,
                default=st.session_state.category_filter
            )
        
        with col2:
            st.markdown(f"#### {t('similarity.mechanics_filter')}")
            selected_mechanics = st.multiselect(
                t("similarity.select_mechanics"),
                options=mechanics,
                default=st.session_state.mechanics_filter
            )
        
        # Save selections
        st.session_state.category_filter = selected_categories
        st.session_state.mechanics_filter = selected_mechanics
    
    return selected_categories, selected_mechanics

# Function to filter games
def filter_games(
    games: List[Dict[str, Any]],
    game_data_list: List[Dict[str, Any]],
    categories: List[str],
    mechanics: List[str]
) -> List[int]:
    """Function to filter games
    
    Args:
        games (List[Dict[str, Any]]): List of game information
        game_data_list (List[Dict[str, Any]]): List of game data
        categories (List[str]): List of categories to filter
        mechanics (List[str]): List of mechanics to filter
        
    Returns:
        List[int]: List of filtered game indices
    """
    if not categories and not mechanics:
        return list(range(len(games)))
    
    filtered_indices = []
    
    for i, game_data in enumerate(game_data_list):
        match = True
        
        if categories:
            game_categories = set()
            if 'categories' in game_data:
                game_categories = set(cat.get('name', '') for cat in game_data['categories'] 
                                    if isinstance(cat, dict) and 'name' in cat)
            
            # Check if any category matches
            if not any(cat in game_categories for cat in categories):
                match = False
        
        if mechanics and match:
            game_mechanics = set()
            if 'mechanics' in game_data:
                game_mechanics = set(mech.get('name', '') for mech in game_data['mechanics'] 
                                   if isinstance(mech, dict) and 'name' in mech)
            
            # Check if any mechanics matches
            if not any(mech in game_mechanics for mech in mechanics):
                match = False
        
        if match:
            filtered_indices.append(i)
    
    return filtered_indices

# Display game information card
def display_game_card(
    game_data: Dict[str, Any],
    is_main: bool = False
) -> None:
    """Function to display game information card
    
    Args:
        game_data (Dict[str, Any]): Game data
        is_main (bool, optional): Whether to display as main card. Default is False.
    """
    game_name = get_game_display_name(game_data)
    secondary_name = get_game_secondary_name(game_data)
    
    with st.container():
        st.markdown(f"<div class='game-card'>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Display thumbnail image if available
            thumbnail_url = game_data.get('thumbnail_url', '')
            if thumbnail_url:
                st.image(thumbnail_url, width=150)
            else:
                st.markdown("🎲")
        
        with col2:
            if is_main:
                st.markdown(f"### 📊 {game_name}")
            else:
                st.markdown(f"### {game_name}")
            
            # Secondary language name as caption
            if secondary_name:
                st.caption(format_language_caption(secondary_name))
            
            # Basic game information
            cols = st.columns(3)
            with cols[0]:
                if 'year_published' in game_data:
                    st.markdown(f"**{t('common.year_published')}**: {game_data['year_published']}")
            with cols[1]:
                if 'weight' in game_data:
                    st.markdown(f"**{t('common.complexity')}**: {game_data['weight']}")
            with cols[2]:
                if 'playing_time' in game_data:
                    st.markdown(f"**{t('common.playing_time')}**: {game_data['playing_time']}{t('common.minutes')}")
            
            # Categories and mechanics
            if 'categories' in game_data:
                categories = [cat.get('name', '') for cat in game_data['categories'] 
                             if isinstance(cat, dict) and 'name' in cat]
                if categories:
                    st.markdown(f"**{t('common.categories')}**: {', '.join(categories)}")
            
            if 'mechanics' in game_data:
                mechanics = [mech.get('name', '') for mech in game_data['mechanics'] 
                            if isinstance(mech, dict) and 'name' in mech]
                if mechanics:
                    st.markdown(f"**{t('common.mechanics')}**: {', '.join(mechanics[:5])}")
                    if len(mechanics) > 5:
                        st.markdown(f"*{t('common.and_more', count=len(mechanics)-5)}*")
            
            if is_main and 'description' in game_data:
                with st.expander(t("details.game_description")):
                    st.markdown(game_data['description'])
        
        st.markdown("</div>", unsafe_allow_html=True)

def display_similar_game_card(
    rank: int,
    idx: int,
    selected_index: int,
    games: List[Dict[str, Any]],
    game_data_list: List[Dict[str, Any]],
    similarity_matrix: np.ndarray
) -> None:
    """
    Function to display similar game card
    
    Args:
        rank (int): Similarity rank
        idx (int): Game index
        selected_index (int): Selected game index
        games (List[Dict[str, Any]]): List of game information
        game_data_list (List[Dict[str, Any]]): List of game data
        similarity_matrix (np.ndarray): Similarity matrix
    """
    # Implementation maintained for compatibility
    similarity = similarity_matrix[selected_index][idx]
    
    # Display similarity score
    st.markdown(f"<div class='similarity-score'>{t('similarity.similarity_score', score=f'{similarity:.4f}')}</div>", unsafe_allow_html=True)
    
    # Display game card
    display_game_card(game_data_list[idx])

# Get similar games
def get_similar_indices(
    selected_index: int,
    similarity_matrix: np.ndarray,
    top_n: int,
    similarity_threshold: float = 0.0
) -> np.ndarray:
    """Function to get indices of games with high similarity
    
    Args:
        selected_index (int): Selected game index
        similarity_matrix (np.ndarray): Similarity matrix
        top_n (int): Number of games to get
        similarity_threshold (float, optional): Similarity threshold. Default is 0.0.
        
    Returns:
        np.ndarray: Array of similar game indices
    """
    # Similarity excluding self
    similarities = similarity_matrix[selected_index]
    mask = (similarities >= similarity_threshold) & (np.arange(len(similarities)) != selected_index)
    
    # Extract indices that exceed threshold and sort by similarity
    filtered_indices = np.where(mask)[0]
    if filtered_indices.size == 0:
        return np.array([])
        
    sorted_indices = filtered_indices[np.argsort(similarities[filtered_indices])[::-1]]
    
    # Limit to top_n
    return sorted_indices[:min(top_n, len(sorted_indices))]

# Function to analyze similarity reasons
def analyze_similarity_reasons(
    game1: Dict[str, Any],
    game2: Dict[str, Any]
) -> List[str]:
    """Function to analyze similarity reasons between two games
    
    Args:
        game1 (Dict[str, Any]): First game data
        game2 (Dict[str, Any]): Second game data
        
    Returns:
        List[str]: List of similarity reasons
    """
    reasons = []
    
    # Compare categories
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
        reasons.append(f"{t('similarity.common_categories')}: {', '.join(common_categories)}")
    
    # Compare mechanics
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
        reasons.append(f"{t('similarity.common_mechanics')}: {', '.join(common_mechanics)}")
    
    # Compare strategic depth
    if 'learning_analysis' in game1 and 'learning_analysis' in game2:
        g1_depth = game1.get('learning_analysis', {}).get('strategic_depth_description', '')
        g2_depth = game2.get('learning_analysis', {}).get('strategic_depth_description', '')
        if g1_depth and g2_depth and g1_depth == g2_depth:
            reasons.append(f"{t('similarity.same_strategic_depth')}: {g1_depth}")
    
    # Compare player types
    if 'learning_analysis' in game1 and 'learning_analysis' in game2:
        g1_player_types = set(game1.get('learning_analysis', {}).get('player_types', []))
        g2_player_types = set(game2.get('learning_analysis', {}).get('player_types', []))
        common_player_types = g1_player_types.intersection(g2_player_types)
        if common_player_types:
            reasons.append(f"{t('similarity.common_player_types')}: {', '.join(common_player_types)}")
    
    # Compare weight (complexity)
    if 'weight' in game1 and 'weight' in game2:
        try:
            g1_weight = float(game1.get('weight', 0))
            g2_weight = float(game2.get('weight', 0))
            if abs(g1_weight - g2_weight) < 0.5:  # Similar if difference is less than 0.5
                reasons.append(f"{t('similarity.similar_complexity')}: {g1_weight:.2f} vs {g2_weight:.2f}")
        except (ValueError, TypeError):
            pass
    
    # Compare publication year
    if 'year_published' in game1 and 'year_published' in game2:
        try:
            g1_year = int(game1.get('year_published', 0))
            g2_year = int(game2.get('year_published', 0))
            if abs(g1_year - g2_year) <= 5:
                reasons.append(f"{t('similarity.close_publication_year')}: {g1_year} vs {g2_year}")
        except (ValueError, TypeError):
            pass
    
    # If no reasons found
    if not reasons:
        # Extract common keywords from descriptions
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
            reasons.append(f"{t('similarity.common_keywords')}: {', '.join(meaningful_words[:5])}")
        else:
            reasons.append(t("similarity.overall_similarity"))
    
    return reasons

# Generate similarity heatmap
def generate_heatmap(
    selected_index: int,
    games: List[Dict[str, Any]],
    similarity_matrix: np.ndarray,
    top_n: int = 10
) -> Optional[io.BytesIO]:
    """Function to generate similarity heatmap
    
    Args:
        selected_index (int): Selected game index
        games (List[Dict[str, Any]]): List of game information
        similarity_matrix (np.ndarray): Similarity matrix
        top_n (int, optional): Number of games to display. Default is 10.
        
    Returns:
        Optional[io.BytesIO]: Heatmap image buffer, None on error
    """
    try:
        similar_indices = np.argsort(similarity_matrix[selected_index])[::-1][1:top_n+1]
        all_indices = [selected_index] + list(similar_indices)
        
        # Create subset of similarity matrix
        sub_matrix = similarity_matrix[np.ix_(all_indices, all_indices)]
        
        # Create labels with language awareness
        labels = []
        for i in all_indices:
            # Load game data to get proper display name
            game_data = games[i] if isinstance(games[i], dict) else None
            if game_data:
                label = get_game_display_name(game_data)
            else:
                # Fallback if game data isn't properly structured
                label = games[i].get('japanese_name', '') or games[i].get('name', '')
            labels.append(label)
        
        # Shorten long labels
        shortened_labels = []
        for label in labels:
            if len(label) > 15:
                shortened_labels.append(label[:12] + "...")
            else:
                shortened_labels.append(label)
        
        # Reconfirm font for Japanese display
        setup_japanese_fonts()
        
        # Create heatmap
        plt.figure(figsize=(10, 8))
        ax = sns.heatmap(
            sub_matrix,
            annot=True,
            fmt=".2f",
            cmap="YlGnBu", 
            xticklabels=shortened_labels,
            yticklabels=shortened_labels
        )
        
        # Adjust font size
        plt.setp(ax.get_xticklabels(), fontsize=9, rotation=45, ha="right", rotation_mode="anchor")
        plt.setp(ax.get_yticklabels(), fontsize=9)
        
        plt.title(t("similarity.heatmap_title"), fontsize=12)
        plt.tight_layout()
        
        # Convert plot for Streamlit display
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150)
        plt.close()
        buf.seek(0)
        
        return buf
    except Exception as e:
        logger.error(f"Heatmap generation error: {e}")
        return None

# Function to analyze similar game distribution data
def analyze_distribution_data(
    selected_index: int,
    games: List[Dict[str, Any]],
    game_data_list: List[Dict[str, Any]],
    similarity_matrix: np.ndarray,
    top_n: int = 20
) -> Tuple[pd.DataFrame, Counter, Counter]:
    """Function to analyze similar game distribution data
    
    Args:
        selected_index (int): Selected game index
        games (List[Dict[str, Any]]): List of game information
        game_data_list (List[Dict[str, Any]]): List of game data
        similarity_matrix (np.ndarray): Similarity matrix
        top_n (int, optional): Number of games to analyze. Default is 20.
        
    Returns:
        Tuple[pd.DataFrame, Counter, Counter]: Similarity dataframe, category distribution, mechanics distribution
    """
    # Get high similarity games
    similarities = similarity_matrix[selected_index]
    indices = np.argsort(similarities)[::-1][1:top_n+1]
    
    # Create DataFrame with language-aware names
    display_names = []
    for i in indices:
        display_names.append(get_game_display_name(game_data_list[i]))
    
    df = pd.DataFrame({
        t('common.game_name'): display_names,
        t('common.similarity'): [similarities[i] for i in indices]
    })
    
    # Analyze category and mechanics distribution
    all_categories = []
    all_mechanics = []
    
    for i in indices[:10]:  # Top 10 games only
        game = game_data_list[i]
        
        # Collect categories
        if 'categories' in game:
            cats = [cat.get('name', '') for cat in game['categories'] 
                   if isinstance(cat, dict) and 'name' in cat]
            all_categories.extend(cats)
        
        # Collect mechanics
        if 'mechanics' in game:
            mechs = [mech.get('name', '') for mech in game['mechanics'] 
                    if isinstance(mech, dict) and 'name' in mech]
            all_mechanics.extend(mechs)
    
    # Count
    category_counts = Counter(all_categories)
    mechanics_counts = Counter(all_mechanics)
    
    return df, category_counts, mechanics_counts

# Draw category distribution pie chart
def plot_category_pie_chart(category_counts: Counter) -> Optional[plt.Figure]:
    """Function to draw category distribution pie chart
    
    Args:
        category_counts (Counter): Category counts
        
    Returns:
        Optional[plt.Figure]: Drawn figure, None if no data
    """
    if not category_counts:
        return None
    
    # Reconfirm font for Japanese display
    setup_japanese_fonts()
    
    # Extract top 8 categories (for graph readability)
    top_categories = dict(category_counts.most_common(8))
    others_count = sum(count for cat, count in category_counts.items() if cat not in top_categories)
    if others_count > 0:
        top_categories[t('common.others')] = others_count
    
    # Pie chart
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        top_categories.values(), 
        labels=list(top_categories.keys()), 
        autopct='%1.1f%%',
        textprops={'fontsize': 9}
    )
    
    # Adjust label font size
    plt.setp(autotexts, size=8)
    plt.setp(texts, size=9)
    
    ax.axis('equal')
    plt.title(t('similarity.category_distribution_title'), fontsize=12)
    
    return fig

# Draw mechanics distribution bar chart
def plot_mechanics_bar_chart(mechanics_counts: Counter) -> Optional[plt.Figure]:
    """Function to draw mechanics distribution bar chart
    
    Args:
        mechanics_counts (Counter): Mechanics counts
        
    Returns:
        Optional[plt.Figure]: Drawn figure, None if no data
    """
    if not mechanics_counts:
        return None
    
    # Reconfirm font for Japanese display
    setup_japanese_fonts()
    
    # Display only top 10
    top_mechanics = dict(mechanics_counts.most_common(10))
    
    # Shorten long mechanics names
    shortened_mechs = {}
    for mech, count in top_mechanics.items():
        if len(mech) > 25:
            shortened_mechs[mech[:22] + "..."] = count
        else:
            shortened_mechs[mech] = count
    
    # Horizontal bar chart
    fig, ax = plt.subplots(figsize=(8, 8))
    bars = ax.barh(list(shortened_mechs.keys()), list(shortened_mechs.values()), color='lightgreen')
    ax.set_xlabel(t('common.occurrence_count'), fontsize=12)
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Display values
    for i, bar in enumerate(bars):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                str(list(shortened_mechs.values())[i]), 
                va='center')
    
    plt.title(t('similarity.mechanics_distribution_title'), fontsize=12)
    plt.tight_layout()
    
    return fig

# Draw similar games bar chart
def plot_similar_games_bar_chart(df: pd.DataFrame) -> plt.Figure:
    """Function to draw similar games bar chart
    
    Args:
        df (pd.DataFrame): Similar games dataframe
        
    Returns:
        plt.Figure: Drawn figure
    """
    # Reconfirm font for Japanese display
    setup_japanese_fonts()
    
    # Shorten long game names
    shortened_names = []
    for name in df[t('common.game_name')]:
        if len(name) > 20:
            shortened_names.append(name[:17] + "...")
        else:
            shortened_names.append(name)
    
    df_plot = df.copy()
    df_plot[t('common.shortened_name')] = shortened_names
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 8))
    bars = ax.barh(df_plot[t('common.shortened_name')], df[t('common.similarity')], color='skyblue')
    ax.set_xlabel(t('common.similarity'), fontsize=12)
    ax.set_xlim(0, 1)
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Display values
    for i, bar in enumerate(bars):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2, 
                f'{df.iloc[i][t("common.similarity")]:.2f}', 
                va='center')
    
    plt.tight_layout()
    
    return fig