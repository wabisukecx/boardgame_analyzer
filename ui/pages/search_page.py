import streamlit as st
from src.api.bgg_api import search_games
from src.data.data_handler import search_results_to_dataframe
from src.utils.language import t, get_game_display_name, get_dataframe_column_names

def search_page():
    """Display the game search page"""
    st.header(t("search.title"))
    
    # Search parameter input fields
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(t("search.input_placeholder"))
    with col2:
        exact = st.checkbox(t("search.exact_match"), value=False)
    
    # Search button
    if st.button(t("search.search_button"), type="primary"):
        if query:
            results = search_games(query, exact)
            
            if results:
                st.success(t("search.results_found", count=len(results)))
                
                # Convert to DataFrame and display
                df = search_results_to_dataframe(results)
                
                # Rename columns according to language
                column_names = get_dataframe_column_names()
                rename_mapping = {
                    "ゲームID": column_names.get("id", "Game ID"),
                    "ゲーム名": column_names.get("name", "Game Name"),
                    "発行年": column_names.get("year_published", "Year Published")
                }
                
                # Apply column renaming if columns exist
                for old_name, new_name in rename_mapping.items():
                    if old_name in df.columns:
                        df = df.rename(columns={old_name: new_name})
                
                st.dataframe(df, use_container_width=True)
                
                # Add link to details
                st.info(t("search.view_details_info"))
                
                # Save results to session state
                st.session_state.search_results = results
            else:
                st.warning(t("search.no_results"))
        else:
            st.error(t("search.input_error"))