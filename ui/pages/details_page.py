import streamlit as st
import os
from src.api.bgg_api import get_game_details
from src.data.data_handler import (
    load_game_data_from_yaml, save_game_data_to_yaml,
    get_yaml_game_list, compare_game_data
)
from src.analysis.learning_curve import calculate_learning_curve
from ui.ui_components import (
    display_game_basic_info, display_game_players_info, display_game_age_time_info,
    display_learning_curve, display_data_tabs,
    display_game_analysis_summary, display_custom_metric
)

# Import from YAML update functions
from src.analysis.mechanic_complexity import (
    add_missing_mechanic, 
    flush_pending_mechanics
)
from src.analysis.category_complexity import add_missing_category
from src.analysis.rank_complexity import add_missing_rank_type

# Import language utilities
from src.utils.language import t, get_game_display_name, format_language_caption

def update_yaml_from_game_data(game_data):
    """
    Update YAML settings from game data
    
    Parameters:
    game_data (dict): Game data
    """
    # Process mechanics
    if 'mechanics' in game_data and isinstance(game_data['mechanics'], list):
        for mechanic in game_data['mechanics']:
            if isinstance(mechanic, dict) and 'name' in mechanic:
                mechanic_name = mechanic['name']
                # Add mechanic
                add_missing_mechanic(mechanic_name)
    
    # Process categories
    if 'categories' in game_data and isinstance(game_data['categories'], list):
        for category in game_data['categories']:
            if isinstance(category, dict) and 'name' in category:
                category_name = category['name']
                # Add category
                add_missing_category(category_name)
    
    # Process rankings
    if 'ranks' in game_data and isinstance(game_data['ranks'], list):
        for rank in game_data['ranks']:
            if isinstance(rank, dict) and 'type' in rank:
                rank_type = rank['type']
                # Add ranking type
                add_missing_rank_type(rank_type)
    
    # Save pending mechanics
    flush_pending_mechanics()
    
    st.session_state['yaml_updated'] = True

def details_page():
    """Display the page to get game details by ID"""
    st.header(t("details.title"))
    
    # Manage YAML update state
    if 'yaml_updated' not in st.session_state:
        st.session_state['yaml_updated'] = False
    
    # Allow selection from existing YAML files
    yaml_games = get_yaml_game_list()
    
    # Select input method
    input_method = st.radio(
        t("details.input_method"),
        [t("details.manual_input"), t("details.select_from_saved")],
        horizontal=True
    )
    
    yaml_data = None
    yaml_file_path = None
    
    if input_method == t("details.manual_input"):
        game_id = st.text_input(t("details.input_placeholder"))
    else:
        if yaml_games:
            # Create display names with language support
            yaml_games_display = []
            for game_info in yaml_games:
                game_id, filename, _ = game_info
                # Load game data to get display name
                yaml_file_path_temp = os.path.join("game_data", filename)
                game_data_temp = load_game_data_from_yaml(yaml_file_path_temp)
                if game_data_temp:
                    display_name = get_game_display_name(game_data_temp)
                    yaml_games_display.append((game_id, filename, f"{game_id} - {display_name}"))
                else:
                    yaml_games_display.append(game_info)
            
            selected_game = st.selectbox(
                t("details.select_game"),
                options=yaml_games_display,
                format_func=lambda x: x[2]  # Use display name
            )
            game_id = selected_game[0] if selected_game else ""
            
            # Load data from selected YAML file
            if selected_game:
                yaml_file_path = os.path.join("game_data", selected_game[1])
                yaml_data = load_game_data_from_yaml(yaml_file_path)
        else:
            st.warning(t("details.no_yaml_files"))
            game_id = ""
    
    if st.button(t("details.get_details_button"), type="primary"):
        if game_id:
            game_details = get_game_details(game_id)
            
            if game_details:
                # Update YAML data
                update_yaml_from_game_data(game_details)
                
                # Display update notification
                if st.session_state['yaml_updated']:
                    st.success(t("details.yaml_updated"))
                    st.session_state['yaml_updated'] = False
                
                # Add anchor tag (for sidebar links)
                st.markdown(f"<div id='{game_id}'></div>", unsafe_allow_html=True)
                
                # Display basic information
                display_game_basic_info(game_details)
                
                # Display additional basic information
                col1, col2 = st.columns(2)
                
                with col1:
                    display_game_players_info(game_details)
                
                with col2:
                    display_game_age_time_info(game_details)
                
                # Display complexity (BGG complexity rating only)
                col1, col2 = st.columns(2)
                with col1:
                    # BGG complexity rating
                    weight = game_details.get('weight', t("common.unknown"))
                    if weight != t("common.unknown"):
                        # Round to 2 decimal places
                        weight = f"{float(weight):.2f}/5.00"
                    display_custom_metric(t("metrics.bgg_complexity"), weight)
                
                # Calculate learning curve information
                learning_curve = None
                if ('description' in game_details and 'mechanics' in game_details
                        and 'weight' in game_details):
                    learning_curve = calculate_learning_curve(game_details)
                
                # Display learning curve information
                if learning_curve:
                    display_learning_curve(learning_curve)
                    
                    # Display evaluation summary
                    display_game_analysis_summary(game_details, learning_curve)
                
                # Display game description
                if 'description' in game_details and game_details['description']:
                    with st.expander(t("details.game_description")):
                        st.markdown(game_details['description'])
                
                # Organize detailed information with tabs
                display_data_tabs(game_details)
                
                # Link to BGG
                st.markdown(
                    f"[{t('details.view_on_bgg')}](https://boardgamegeek.com/boardgame/{game_id.lstrip('0')})"
                )
                
                # Save details to session
                if 'game_data' not in st.session_state:
                    st.session_state.game_data = {}
                
                st.session_state.game_data[game_id] = game_details
                
                # Compare with YAML data and auto-save if changed
                if yaml_data and yaml_file_path:
                    has_changes, change_description = compare_game_data(yaml_data, game_details)
                    
                    if has_changes:
                        # Show changes and ask to update
                        st.warning(t("details.data_changed"))
                        
                        with st.expander(t("details.change_details")):
                            st.markdown(change_description)
                        
                        if st.button(t("details.update_yaml"), key="update_yaml"):
                            # Maintain original filename
                            original_filename = os.path.basename(yaml_file_path)
                            
                            success, file_path, error_msg = save_game_data_to_yaml(
                                game_details, original_filename
                            )
                            
                            if success:
                                st.success(t("details.update_success"))
                            else:
                                st.error(t("details.update_error", error=error_msg))
                    else:
                        st.info(t("details.no_changes"))
            else:
                st.warning(t("details.not_found"))
        else:
            st.error(t("details.error_no_id"))