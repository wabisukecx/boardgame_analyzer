import streamlit as st
import pandas as pd
from src.data.data_handler import load_all_game_data
from src.analysis.learning_curve import calculate_learning_curve
from ui.ui_components import compare_games_radar_chart
from src.utils.language import t, get_game_display_name, get_metric_names

def compare_page():
    """Display the page to compare multiple games"""
    st.header(t("compare.title"))
    
    # Load saved game data
    all_game_data = load_all_game_data()
    
    if not all_game_data:
        st.warning(t("compare.no_data"))
    else:
        # Create game selection options
        game_options = []
        for game_id, game_data in all_game_data.items():
            # Use language-aware game name
            display_name = get_game_display_name(game_data)
            game_options.append({"id": game_id, "name": display_name})
        
        # Sort by ID
        game_options.sort(key=lambda x: x["id"])
        
        # Create display dictionary
        game_display_dict = {f"{g['id']} - {g['name']}": g["id"] for g in game_options}
        
        # Multi-select
        st.subheader(t("compare.select_games"))
        selected_game_keys = st.multiselect(
            t("compare.select_prompt"), 
            options=list(game_display_dict.keys()),
            default=[]
        )
        
        if selected_game_keys:
            selected_game_ids = [game_display_dict[key] for key in selected_game_keys]
            
            # Limit to maximum 6 games
            if len(selected_game_ids) > 6:
                st.warning(t("compare.limit_warning"))
                selected_game_ids = selected_game_ids[:6]
            
            # Get data and learning curve info for each game
            games_data = []
            for game_id in selected_game_ids:
                game_data = all_game_data[game_id]
                
                # Use learning curve info if available
                if 'learning_analysis' in game_data:
                    learning_curve = game_data['learning_analysis']
                # Otherwise calculate it
                elif ('description' in game_data and 'mechanics' in game_data and 
                      'weight' in game_data):
                    learning_curve = calculate_learning_curve(game_data)
                else:
                    display_name = get_game_display_name(game_data)
                    st.warning(t("compare.no_learning_curve", game_name=display_name))
                    continue
                
                games_data.append((game_data, learning_curve))
            
            # Display comparison radar chart
            if games_data:
                st.subheader(t("compare.chart_title"))
                fig = compare_games_radar_chart(games_data)
                st.plotly_chart(fig, use_container_width=True)
                
                # Also display values in table format
                st.subheader(t("compare.table_title"))
                comparison_data = []
                metric_names = get_metric_names()
                
                for game_data, learning_curve in games_data:
                    game_name = get_game_display_name(game_data)
                    comparison_data.append({
                        metric_names.get("game_name", "Game Name"): game_name,
                        metric_names.get("initial_barrier", "Initial Learning Barrier"): f"{learning_curve.get('initial_barrier', 0):.2f}",
                        metric_names.get("strategic_depth", "Strategic Depth"): f"{learning_curve.get('strategic_depth', 0):.2f}",
                        metric_names.get("replayability", "Replayability"): f"{learning_curve.get('replayability', 0):.2f}",
                        metric_names.get("decision_points", "Decision Points"): f"{learning_curve.get('decision_points', 0):.2f}",
                        metric_names.get("interaction_complexity", "Player Interaction"): f"{learning_curve.get('interaction_complexity', 0):.2f}",
                        metric_names.get("rules_complexity", "Rules Complexity"): f"{learning_curve.get('rules_complexity', 0):.2f}",
                        metric_names.get("bgg_weight", "BGG Weight"): f"{float(game_data.get('weight', 0)):.2f}"
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, use_container_width=True)