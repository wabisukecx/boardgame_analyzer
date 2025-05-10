import streamlit as st
from src.data.data_handler import save_game_data_to_yaml
from src.utils.language import t, get_game_display_name, get_game_filename, format_language_caption

def save_page():
    """Display the page to save game data in YAML format"""
    st.header(t("save.title"))
    
    # Selection of game ID to save
    game_ids = []
    if 'game_data' in st.session_state and st.session_state.game_data:
        game_ids = list(st.session_state.game_data.keys())
        
        # Create display names for each game
        game_options = []
        for game_id in game_ids:
            game_data = st.session_state.game_data[game_id]
            display_name = get_game_display_name(game_data)
            game_options.append((game_id, f"{game_id}_{display_name}"))
        
        selected_game_id = st.selectbox(
            t("save.select_game"), 
            game_ids,
            format_func=lambda x: [opt[1] for opt in game_options if opt[0] == x][0]
        )
        
        # Display data of selected game
        if selected_game_id:
            game_data = st.session_state.game_data[selected_game_id]
            
            # Display game name and basic info (show Japanese name if available)
            display_name = get_game_display_name(game_data)
            secondary_name = format_language_caption(game_data.get('japanese_name') if st.session_state.language == 'en' else game_data.get('name'))
            
            st.markdown(f"## {display_name}")
            if secondary_name:
                st.markdown(f"**{secondary_name}**")
            
            st.markdown(f"**{t('save.game_id')}:** {selected_game_id}")
            
            # Display game thumbnail (if available)
            if 'thumbnail_url' in game_data:
                st.image(game_data['thumbnail_url'], caption=display_name)
            
            if 'year_published' in game_data:
                st.markdown(f"**{t('save.year_published')}:** {game_data['year_published']}")
            
            # Filename input field placed before the button
            placeholder_filename = get_game_filename(game_data, selected_game_id) + ".yaml"
            
            custom_filename = st.text_input(
                t("save.filename_input"), 
                value="", 
                placeholder=placeholder_filename
            )
            
            # Save button
            if st.button(t("save.save_button"), type="primary"):
                success, file_path, error_msg = save_game_data_to_yaml(
                    game_data, custom_filename
                )
                
                if success:
                    st.success(t("save.save_success", filepath=file_path))
                else:
                    st.error(t("save.save_error", error=error_msg))
                    st.error(t("save.special_char_error"))
    else:
        st.info(t("save.no_data"))