import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.analysis.game_analyzer import generate_game_summary
from src.analysis.learning_curve import get_curve_type_display
from src.utils.language import t, get_game_display_name, get_game_secondary_name, format_language_caption, get_metric_names

def load_css():
    """Load custom CSS used in the application"""
    st.markdown("""
    <style>
        /* Adjust font size for metric values */
        .metric-value {
            font-size: 0.9rem !important;
        }
        
        /* Style for custom metrics - expanded width */
        .custom-metric {
            padding: 12px;
            border-radius: 5px;
            background-color: #f8f9fa;
            margin-bottom: 10px;
            width: 100%;
            box-sizing: border-box;
        }
        .custom-metric-label {
            font-size: 0.85rem;
            color: #6c757d;
            font-weight: bold;
            margin-bottom: 4px;
        }
        .custom-metric-value {
            font-size: 1.0rem;
            font-weight: 400;
        }
        
        /* Style for thumbnail images */
        .game-thumbnail {
            width: 100%;
            border-radius: 5px;
            margin-bottom: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        /* Basic info heading style */
        .info-heading {
            font-size: 0.85rem;
            font-weight: bold;
            margin-bottom: 4px;
        }
        
        /* Basic info value style */
        .info-value {
            font-size: 0.9rem;
        }
    </style>
    """, unsafe_allow_html=True)


def display_custom_metric(label, value):
    """Display a custom styled metric"""
    st.markdown(f"""
    <div class="custom-metric">
        <div class="custom-metric-label">{label}</div>
        <div class="custom-metric-value" style="font-size: 0.9rem;">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def display_game_thumbnail(thumbnail_url, game_name):
    """Display game thumbnail image"""
    if thumbnail_url:
        st.markdown(f"""
        <div style="text-align: center;">
            <img src="{thumbnail_url}" alt="{game_name}" class="game-thumbnail">
            <p style="font-size: 0.9rem; margin-top: 0px;">{game_name}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Placeholder for no image
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background-color: #f8f9fa; 
        border-radius: 5px; margin-bottom: 10px;">
            <p style="color: #6c757d;">{t("common.no_image")}</p>
            <p style="font-size: 0.9rem; margin-top: 5px;">{game_name}</p>
        </div>
        """, unsafe_allow_html=True)


def display_game_basic_info(game_details):
    """Display basic game information"""
    # Get display name
    display_name = get_game_display_name(game_details)
    secondary_name = get_game_secondary_name(game_details)
    
    # Add heading
    st.markdown(f"### {t('details.basic_info')}")
    
    # Display with custom HTML for font size adjustment
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**{t('common.game_name')}**")
        st.markdown(
            f"<div style='font-size: 0.9rem;'>{display_name}</div>",
            unsafe_allow_html=True
        )
        if secondary_name:
            st.caption(format_language_caption(secondary_name))
    with col2:
        st.markdown(f"**{t('common.year_published')}**")
        year = game_details.get('year_published', t('common.unknown'))
        st.markdown(
            f"<div style='font-size: 0.9rem;'>{year}</div>",
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(f"**{t('common.average_rating')}**")
        rating = game_details.get('average_rating', t('common.unknown'))
        if rating != t('common.unknown'):
            rating = round(float(rating), 2)
        st.markdown(
            f"<div style='font-size: 0.9rem;'>{rating}</div>",
            unsafe_allow_html=True
        )
    
    # Display game thumbnail (if available)
    if 'thumbnail_url' in game_details:
        st.image(
            game_details['thumbnail_url'],
            caption=display_name,
            use_container_width=False
        )


def display_game_players_info(game_details):
    """Display game player count information"""
    st.markdown(f"#### {t('details.player_count')}")
    # Prioritize community recommended player count
    if 'community_best_players' in game_details:
        display_custom_metric(
            t("details.best_players_community"),
            game_details['community_best_players']
        )
    
    # Also display publisher-specified player count
    publisher_players = t('common.unknown')
    if ('publisher_min_players' in game_details and
            'publisher_max_players' in game_details):
        publisher_players = f"{game_details['publisher_min_players']}～" \
                            f"{game_details['publisher_max_players']}{t('common.players_unit')}"
    display_custom_metric(t("details.publisher_players"), publisher_players)


def display_game_age_time_info(game_details):
    """Display game age and play time information"""
    st.markdown(f"#### {t('details.age_time')}")
    # Prioritize community recommended age
    if 'community_min_age' in game_details:
        display_custom_metric(
            t("details.recommended_age_community"),
            f"{game_details['community_min_age']}{t('common.age_and_up')}"
        )
    
    # Play time
    playtime = game_details.get('playing_time', t('common.unknown'))
    if playtime != t('common.unknown'):
        playtime = f"{playtime}{t('common.minutes')}"
    display_custom_metric(t("details.play_time"), playtime)


def display_game_complexity(game_details, learning_curve=None):
    """Display game complexity"""
    st.markdown(f"#### {t('details.complexity')}")
    
    # 2-column layout with equal width
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # BGG complexity rating
        weight = game_details.get('weight', t('common.unknown'))
        if weight != t('common.unknown'):
            # Round to 2 decimal places
            weight = f"{float(weight):.2f}/5.00"
        display_custom_metric(t("details.bgg_complexity"), weight)
    
    with col2:
        # System analysis (if learning curve data is available)
        if learning_curve and 'rules_complexity' in learning_curve:
            # Round to 2 decimal places
            system_analysis = f"{float(learning_curve['rules_complexity']):.2f}/5.00"
            display_custom_metric(t("details.system_analysis"), system_analysis)
        else:
            # Keep space to maintain layout even without learning curve data
            display_custom_metric(t("details.system_analysis"), t("common.calculating"))


def display_system_complexity(col, learning_curve):
    """Display system analysis (rules complexity)"""
    if learning_curve and 'rules_complexity' in learning_curve:
        # Round to 2 decimal places
        system_analysis = f"{float(learning_curve['rules_complexity']):.2f}/5.00"
        with col:
            display_custom_metric(t("details.system_analysis"), system_analysis)


def display_learning_curve(learning_curve, game_details=None):
    """
    Display learning curve information (improved version using category and ranking info)
    
    Parameters:
        learning_curve (dict): Learning curve information
        game_details (dict, optional): Game details (to get BGG complexity)
    """
    st.markdown(f"### {t('details.learning_curve_analysis')}")
    
    col1, col2 = st.columns(2)
    with col1:
        # Round to 2 decimal places
        initial_barrier = f"{float(learning_curve['initial_barrier']):.2f}/5.00"
        display_custom_metric(
            t("metrics.initial_barrier"),
            initial_barrier
        )
    with col2:
        # Display learning curve type
        if 'learning_curve_type' in learning_curve:
            curve_type = learning_curve['learning_curve_type']
            curve_type_display = get_curve_type_display(curve_type)
            display_custom_metric(t("metrics.learning_curve_type"), curve_type_display)
        else:
            display_custom_metric(t("metrics.learning_curve_type"), t("common.calculating"))


def display_data_tabs(game_details):
    """Display detailed information using tabs"""
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        t("tabs.mechanics"),
        t("tabs.categories"),
        t("tabs.rankings"),
        t("tabs.designers"),
        t("tabs.publishers")
    ])
    
    with tab1:
        if 'mechanics' in game_details and game_details['mechanics']:
            # Convert to DataFrame and display
            df = pd.DataFrame(game_details['mechanics'])
            df = df.rename(columns={
                "id": t("common.mechanic_id"),
                "name": t("common.mechanic_name")
            })
            st.dataframe(df, use_container_width=True)
        else:
            st.info(t("info.no_mechanics"))
    
    with tab2:
        if 'categories' in game_details and game_details['categories']:
            # Convert to DataFrame and display
            df = pd.DataFrame(game_details['categories'])
            df = df.rename(columns={
                "id": t("common.category_id"),
                "name": t("common.category_name")
            })
            st.dataframe(df, use_container_width=True)
        else:
            st.info(t("info.no_categories"))
    
    with tab3:
        if 'ranks' in game_details and game_details['ranks']:
            # Convert to DataFrame and display
            df = pd.DataFrame(game_details['ranks'])
            df = df.rename(columns={
                "type": t("common.ranking_type"),
                "id": t("common.ranking_id"),
                "rank": t("common.rank")
            })
            st.dataframe(df, use_container_width=True)
        else:
            st.info(t("info.no_rankings"))
    
    with tab4:
        if 'designers' in game_details and game_details['designers']:
            # Convert to DataFrame and display
            df = pd.DataFrame(game_details['designers'])
            df = df.rename(columns={
                "id": t("common.designer_id"),
                "name": t("common.designer_name")
            })
            st.dataframe(df, use_container_width=True)
        else:
            st.info(t("info.no_designers"))
    
    with tab5:
        if 'publishers' in game_details and game_details['publishers']:
            # Convert to DataFrame and display
            df = pd.DataFrame(game_details['publishers'])
            df = df.rename(columns={
                "id": t("common.publisher_id"),
                "name": t("common.publisher_name")
            })
            st.dataframe(df, use_container_width=True)
        else:
            st.info(t("info.no_publishers"))


def display_game_analysis_summary(game_data, learning_curve):
    """
    Display concise evaluation summary from game data and learning curve
    
    Parameters:
        game_data (dict): Game details
        learning_curve (dict): Learning curve information
    """
    st.markdown(f"### {t('details.evaluation_summary')}")
    
    # Display auto-generated summary
    summary = generate_game_summary(game_data, learning_curve)
    st.markdown(summary)
    
    # Visualization of complexity and strategy
    with st.expander(t("details.complexity_strategy_viz"), expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # BGG weight vs analyzed complexity
            bgg_weight = float(game_data.get('weight', 0))
            rules_complexity = learning_curve.get('rules_complexity', 0)
            
            st.markdown(f"#### {t('details.complexity_comparison')}")
            st.markdown(f"- {t('details.bgg_user_rating')}: **{bgg_weight:.2f}**/5.00")
            st.markdown(f"- {t('details.system_analysis')}: **{rules_complexity:.2f}**/5.00")
            
            # Calculate and color-code the difference
            diff = rules_complexity - bgg_weight
            if abs(diff) > 0.8:
                color = "red" if diff > 0 else "blue"
                st.markdown(f"<span style='color:{color};'>{t('details.difference')}: {diff:.2f}</span>", unsafe_allow_html=True)
        
        with col2:
            # Strategic depth and replayability
            strategic_depth = learning_curve.get('strategic_depth', 0)
            replayability = learning_curve.get('replayability', 0)
            
            st.markdown(f"#### {t('details.strategy_replayability')}")
            st.markdown(f"- {t('metrics.strategic_depth')}: **{strategic_depth:.2f}**/5.00")
            st.markdown(f"- {t('metrics.replayability')}: **{replayability:.2f}**/5.00")

def compare_games_radar_chart(games_data):
    """
    Create radar chart to compare multiple games
    
    Parameters:
    games_data (list): List of (game data, learning curve data) tuples
    
    Returns:
    fig: plotly Figure object
    """
    fig = go.Figure()
    
    # Categories to compare (using translated names)
    metric_names = get_metric_names()
    categories = [
        metric_names.get('initial_barrier', 'Initial Learning Barrier'),
        metric_names.get('strategic_depth', 'Strategic Depth'),
        metric_names.get('replayability', 'Replayability'),
        metric_names.get('decision_points', 'Decision Points'),
        metric_names.get('interaction_complexity', 'Player Interaction'),
        metric_names.get('rules_complexity', 'Rules Complexity')
    ]
    
    # Generate colors for each game in pastel tones
    colors = ['rgba(178, 34, 34, 0.7)', 'rgba(31, 119, 180, 0.7)', 
              'rgba(44, 160, 44, 0.7)', 'rgba(255, 127, 14, 0.7)',
              'rgba(148, 103, 189, 0.7)', 'rgba(140, 86, 75, 0.7)']
    
    for i, (game_data, learning_curve) in enumerate(games_data):
        if i >= len(colors):  # Color limit
            break
            
        game_name = get_game_display_name(game_data)
        
        values = [
            learning_curve.get('initial_barrier', 0),
            learning_curve.get('strategic_depth', 0),
            learning_curve.get('replayability', 0),
            learning_curve.get('decision_points', 0),
            learning_curve.get('interaction_complexity', 0),
            learning_curve.get('rules_complexity', 0)
        ]
        
        # Close the circle
        cat = categories + [categories[0]]
        val = values + [values[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=val,
            theta=cat,
            fill='toself',
            name=game_name,
            line_color=colors[i],
            fillcolor=colors[i].replace('0.7', '0.2')
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5]
            )
        ),
        showlegend=True,
        title={
            'text': t("compare.chart_title"),
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        margin=dict(l=80, r=80, t=50, b=50),
        height=600
    )
    
    return fig