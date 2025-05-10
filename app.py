import streamlit as st
import os
import logging
from typing import Tuple

# Import from the original BoardGame Analyzer
from ui.ui_components import load_css
from ui.pages.search_page import search_page
from ui.pages.details_page import details_page
from ui.pages.save_page import save_page
from ui.pages.compare_page import compare_page

# Import functions from the similarity search app individually
from src.analysis.similarity import (
    load_data, 
    extract_categories_and_mechanics,
    display_filter_ui,
    filter_games,
    display_game_card,
    get_similar_indices,
    display_similar_game_card,
    generate_heatmap,
    analyze_distribution_data,
    plot_category_pie_chart,
    plot_mechanics_bar_chart,
    plot_similar_games_bar_chart,
)

# Import from improved similarity analysis module
from src.analysis.improved_similarity_analyzer import (
    get_formatted_similarity_reasons,
    calculate_overall_similarity
)

# Import language utilities
from src.utils.language import language_manager, t, get_game_display_name, get_game_secondary_name

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("boardgame_app")

# Function for sidebar settings
def setup_similarity_sidebar() -> Tuple[str, int, float]:
    """Set up the sidebar and return user settings
    
    Returns:
        Tuple[str, int, float]: Data file name, number of games to display, similarity threshold
    """
    with st.sidebar:
        st.header(t("similarity.settings"))
        data_file = st.text_input(
            t("similarity.embedding_file"),
            value="game_embeddings.pkl"
        )
        
        st.header(t("similarity.search_settings"))
        top_n = st.slider(
            t("similarity.num_games"),
            min_value=1,
            max_value=20,
            value=5
        )
        similarity_threshold = st.slider(
            t("similarity.threshold"),
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05
        )
        
        # Category and mechanics filtering (used later)
        if 'category_filter' not in st.session_state:
            st.session_state.category_filter = []
        
        if 'mechanics_filter' not in st.session_state:
            st.session_state.mechanics_filter = []
        
    return data_file, top_n, similarity_threshold

# Custom CSS
def load_custom_similarity_css() -> None:
    """Load custom CSS for similarity search"""
    st.markdown("""
    <style>
        .game-card {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 10px;
            background-color: #f9f9f9;
        }
        .similarity-score {
            font-size: 18px;
            font-weight: bold;
            color: #1e88e5;
        }
        .reason-item {
            margin-left: 20px;
            color: #555;
        }
        .header-container {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        .app-header {
            color: #2e7d32;
            font-size: 2.5rem;
        }
        .stProgress > div > div > div > div {
            background-color: #4CAF50;
        }
        .tooltip {
            position: relative;
            display: inline-block;
            border-bottom: 1px dotted #ccc;
            cursor: help;
        }
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 200px;
            background-color: #555;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -100px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
        .filter-container {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)

# Similarity search page
def similarity_search_page():
    """Page to display similarity search functionality"""
    st.header(t("similarity.title"))
    st.markdown(t("similarity.description"))
    
    # Sidebar settings
    data_file, top_n, similarity_threshold = setup_similarity_sidebar()
    
    # Check data file existence
    if not os.path.exists(data_file):
        st.error(t("errors.file_not_found", filename=data_file))
        return
    
    # Load data
    with st.spinner(t("loading.data")):
        data = load_data(data_file)
    
    if data is None:
        st.error(t("errors.file_load_failed", filename=data_file))
        return
    
    games = data['games']
    game_data_list = data['game_data_list']
    embeddings = data['embeddings']
    similarity_matrix = data['similarity_matrix']
    
    st.success(t("loading.games_loaded", count=len(games)))
    
    # Extract list of categories and mechanics
    categories, mechanics = extract_categories_and_mechanics(game_data_list)
    
    # Filter settings
    selected_categories, selected_mechanics = display_filter_ui(categories, mechanics)
    
    # Filtering
    filtered_indices = filter_games(games, game_data_list, selected_categories, selected_mechanics)
    if not filtered_indices:
        st.warning(t("similarity.no_matching_games"))
        return
    
    # List of game names after filtering
    filtered_display_names = [
        get_game_display_name(game_data_list[i])
        for i in filtered_indices
    ]
    
    # Game selection by search
    selected_game = st.selectbox(
        t("similarity.select_game"),
        filtered_display_names,
        index=0
    )
    
    # Get the original index of the selected game
    selected_filtered_index = filtered_display_names.index(selected_game)
    selected_index = filtered_indices[selected_filtered_index]
    
    # Display information of the selected game
    st.markdown(f"## {t('similarity.selected_game')}")
    display_game_card(game_data_list[selected_index], is_main=True)
    
    if st.button(t("similarity.search_button")):
        # Show progress bar
        progress_bar = st.progress(0)
        
        st.markdown(f"## {t('similarity.similar_games')}")
        
        # Create tabs
        tab1, tab2, tab3 = st.tabs([
            t("similarity.tabs.game_list"),
            t("similarity.tabs.heatmap"),
            t("similarity.tabs.analysis")
        ])
        
        with tab1:
            # Get similar game indices
            similar_indices = get_similar_indices(selected_index, similarity_matrix, top_n, similarity_threshold)
            
            if not similar_indices.size:
                st.warning(t("similarity.no_similar_games", threshold=similarity_threshold))
            else:
                # Display each similar game
                for rank, idx in enumerate(similar_indices, 1):
                    similarity = similarity_matrix[selected_index][idx]
                    
                    # Display similarity score
                    st.markdown(f"<div class='similarity-score'>{t('similarity.similarity_score', score=f'{similarity:.4f}')}</div>", unsafe_allow_html=True)
                    
                    # Display game card
                    display_game_card(game_data_list[idx])
                    
                    # Use improved similarity analysis module
                    similarity_reasons = get_formatted_similarity_reasons(game_data_list[selected_index], game_data_list[idx])
                    st.markdown(f"**{t('similarity.similarity_reasons')}:**")
                    for reason in similarity_reasons:
                        st.markdown(f"<div class='reason-item'>• {reason}</div>", unsafe_allow_html=True)
                    
                    st.markdown("---")
            
            progress_bar.progress(33)
        
        with tab2:
            try:
                heatmap_buffer = generate_heatmap(selected_index, games, similarity_matrix)
                if heatmap_buffer:
                    st.image(heatmap_buffer)
                else:
                    st.info(t("errors.heatmap_failed"))
            except Exception as e:
                logger.error(f"Heatmap display error: {e}")
                st.error(t("errors.heatmap_error", error=str(e)))
            
            progress_bar.progress(66)
        
        with tab3:
            try:
                # Plot similarity to selected game with others
                df, category_counts, mechanics_counts = analyze_distribution_data(
                    selected_index, games, game_data_list, similarity_matrix
                )
                
                st.markdown(f"### {t('similarity.analysis.top_games')}")
                fig = plot_similar_games_bar_chart(df)
                st.pyplot(fig)
                
                st.markdown(f"### {t('analysis.category_mechanics')}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"#### {t('similarity.analysis.category_distribution')}")
                    if category_counts:
                        fig = plot_category_pie_chart(category_counts)
                        if fig:
                            st.pyplot(fig)
                        else:
                            st.info(t("errors.category_chart_failed"))
                    else:
                        st.info(t("similarity.analysis.no_categories"))
                
                with col2:
                    st.markdown(f"#### {t('similarity.analysis.mechanics_distribution')}")
                    if mechanics_counts:
                        fig = plot_mechanics_bar_chart(mechanics_counts)
                        if fig:
                            st.pyplot(fig)
                        else:
                            st.info(t("errors.mechanics_chart_failed"))
                    else:
                        st.info(t("similarity.analysis.no_mechanics"))
            except Exception as e:
                logger.error(f"Data analysis error: {e}")
                st.error(t("errors.analysis_error", error=str(e)))
        
        # Complete the progress bar
        progress_bar.progress(100)

def main():
    """Main entry point for the integrated board game application"""
    # Initialize language manager first
    if 'language' not in st.session_state:
        st.session_state.language = 'ja'
    
    # Initialize language resources
    language_manager.initialize()
    
    # Page configuration
    st.set_page_config(
        page_title=t("app.title"),
        page_icon="🎲",
        layout="wide"
    )

    # Load custom CSS
    load_css()  # CSS for BoardGame Analyzer
    load_custom_similarity_css()  # CSS for similarity search

    # Sidebar for language switching and app functions
    with st.sidebar:
        # Language switching
        st.markdown(f"### {t('sidebar.language')}")
        language = st.selectbox(
            t('sidebar.language'),  # ラベルを提供
            options=list(language_manager.supported_languages.keys()),
            format_func=lambda x: language_manager.supported_languages[x],
            index=list(language_manager.supported_languages.keys()).index(st.session_state.language),
            key="language_selector",
            label_visibility="collapsed"  # ラベルを非表示にする
        )
        
        if language != st.session_state.language:
            language_manager.switch_language(language)
        
        st.markdown("---")
        
        # Function selection
        st.title(t("sidebar.functions"))
        option = st.radio(
            t("sidebar.select_operation"),
            [
                t("sidebar.search_by_name"),
                t("sidebar.get_details_by_id"),
                t("sidebar.save_yaml"),
                t("sidebar.compare_games"),
                t("sidebar.similarity_search")
            ]
        )

    # Display page based on selected function
    if option == t("sidebar.search_by_name"):
        search_page()
    elif option == t("sidebar.get_details_by_id"):
        details_page()
    elif option == t("sidebar.save_yaml"):
        save_page()
    elif option == t("sidebar.compare_games"):
        compare_page()
    elif option == t("sidebar.similarity_search"):
        similarity_search_page()

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption(t("app.description"))

if __name__ == "__main__":
    main()