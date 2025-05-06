import streamlit as st
import os
import logging
from typing import Tuple

# 元のBoardGame Analyzerからのインポート
from ui.ui_components import load_css
from ui.pages.search_page import search_page
from ui.pages.details_page import details_page
from ui.pages.save_page import save_page
from ui.pages.compare_page import compare_page

# 類似性検索アプリの関数を個別にインポート
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

# 改善された類似性分析モジュールからインポート
from src.analysis.improved_similarity_analyzer import (
    get_formatted_similarity_reasons,
    calculate_overall_similarity
)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("boardgame_app")

# サイドバー設定を担当する関数
def setup_similarity_sidebar() -> Tuple[str, int, float]:
    """サイドバーの設定を行い、ユーザー設定を返す関数
    
    Returns:
        Tuple[str, int, float]: データファイル名、表示するゲーム数、類似度閾値
    """
    with st.sidebar:
        st.header("類似性検索設定")
        data_file = st.text_input(
            "エンベディングデータファイル",
            value="game_embeddings.pkl"
        )
        
        st.header("検索設定")
        top_n = st.slider(
            "表示する類似ゲーム数",
            min_value=1,
            max_value=20,
            value=5
        )
        similarity_threshold = st.slider(
            "類似度閾値",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05
        )
        
        # カテゴリとメカニクスのフィルタリング（後で使用）
        if 'category_filter' not in st.session_state:
            st.session_state.category_filter = []
        
        if 'mechanics_filter' not in st.session_state:
            st.session_state.mechanics_filter = []
        
    return data_file, top_n, similarity_threshold

# カスタムCSS
def load_custom_similarity_css() -> None:
    """類似性検索用のカスタムCSSを読み込む関数"""
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

# 類似性検索ページ
def similarity_search_page():
    """類似性検索機能を表示するページ"""
    st.header("ボードゲーム類似性検索")
    st.markdown("事前計算されたエンベディングを使用してボードゲームの類似性を検索するアプリケーションです。")
    
    # サイドバーの設定
    data_file, top_n, similarity_threshold = setup_similarity_sidebar()
    
    # データファイルの存在確認
    if not os.path.exists(data_file):
        st.error(f"データファイル {data_file} が存在しません。正しいパスを指定してください。")
        return
    
    # データの読み込み
    with st.spinner("データを読み込んでいます..."):
        data = load_data(data_file)
    
    if data is None:
        st.error(f"データファイル {data_file} を読み込めませんでした。")
        return
    
    games = data['games']
    game_data_list = data['game_data_list']
    embeddings = data['embeddings']
    similarity_matrix = data['similarity_matrix']
    
    st.success(f"{len(games)}個のゲームデータが読み込まれました。")
    
    # カテゴリとメカニクスのリストを抽出
    categories, mechanics = extract_categories_and_mechanics(game_data_list)
    
    # フィルター設定
    selected_categories, selected_mechanics = display_filter_ui(categories, mechanics)
    
    # フィルタリング
    filtered_indices = filter_games(games, game_data_list, selected_categories, selected_mechanics)
    if not filtered_indices:
        st.warning("条件に合うゲームが見つかりませんでした。フィルター条件を変更してください。")
        return
    
    # フィルター適用後のゲーム名リスト
    filtered_display_names = [
        games[i].get('japanese_name', '') or games[i].get('name', '') 
        for i in filtered_indices
    ]
    
    # ゲーム選択による検索
    selected_game = st.selectbox(
        "検索するゲームを選択してください",
        filtered_display_names,
        index=0
    )
    
    # 選択されたゲームの元のインデックスを取得
    selected_filtered_index = filtered_display_names.index(selected_game)
    selected_index = filtered_indices[selected_filtered_index]
    
    # 選択されたゲームの情報を表示
    st.markdown("## 選択されたゲーム")
    display_game_card(game_data_list[selected_index], is_main=True)
    
    if st.button("類似ゲームを検索"):
        # プログレスバーを表示
        progress_bar = st.progress(0)
        
        st.markdown("## 類似ゲーム")
        
        # タブを作成
        tab1, tab2, tab3 = st.tabs(["類似ゲーム一覧", "類似度ヒートマップ", "データ分析"])
        
        with tab1:
            # 類似ゲームのインデックスを取得
            similar_indices = get_similar_indices(selected_index, similarity_matrix, top_n, similarity_threshold)
            
            if not similar_indices.size:
                st.warning(f"類似度が {similarity_threshold} を超えるゲームが見つかりませんでした。閾値を下げてみてください。")
            else:
                # 各類似ゲームを表示
                for rank, idx in enumerate(similar_indices, 1):
                    similarity = similarity_matrix[selected_index][idx]
                    
                    # 類似度スコア表示
                    st.markdown(f"<div class='similarity-score'>類似度: {similarity:.4f}</div>", unsafe_allow_html=True)
                    
                    # ゲームカード表示
                    display_game_card(game_data_list[idx])
                    
                    # *** 改善版類似性分析モジュールを使用 ***
                    # 類似性の理由を分析して表示
                    similarity_reasons = get_formatted_similarity_reasons(game_data_list[selected_index], game_data_list[idx])
                    st.markdown("**類似性の理由:**")
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
                    st.info("ヒートマップを生成できませんでした。")
            except Exception as e:
                logger.error(f"ヒートマップ表示エラー: {e}")
                st.error(f"ヒートマップ表示中にエラーが発生しました: {e}")
            
            progress_bar.progress(66)
        
        with tab3:
            try:
                # 選択したゲームと他のゲームとの類似度をプロット
                df, category_counts, mechanics_counts = analyze_distribution_data(
                    selected_index, games, game_data_list, similarity_matrix
                )
                
                st.markdown("### 最も類似度が高い20ゲーム")
                fig = plot_similar_games_bar_chart(df)
                st.pyplot(fig)
                
                st.markdown("### カテゴリとメカニクスの分析")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### カテゴリの分布")
                    if category_counts:
                        fig = plot_category_pie_chart(category_counts)
                        if fig:
                            st.pyplot(fig)
                        else:
                            st.info("カテゴリの円グラフを生成できませんでした。")
                    else:
                        st.info("類似ゲームのカテゴリ情報がありません")
                
                with col2:
                    st.markdown("#### メカニクスの分布")
                    if mechanics_counts:
                        fig = plot_mechanics_bar_chart(mechanics_counts)
                        if fig:
                            st.pyplot(fig)
                        else:
                            st.info("メカニクスの棒グラフを生成できませんでした。")
                    else:
                        st.info("類似ゲームのメカニクス情報がありません")
            except Exception as e:
                logger.error(f"データ分析エラー: {e}")
                st.error(f"データ分析中にエラーが発生しました: {e}")
        
        # プログレスバーを完了させる
        progress_bar.progress(100)

def main():
    """統合されたボードゲームアプリケーションのメインエントリポイント"""
    # ページ設定
    st.set_page_config(
        page_title="ボードゲームアプリ",
        page_icon="🎲",
        layout="wide"
    )

    # カスタムCSSをロード
    load_css()  # BoardGame Analyzer用のCSS
    load_custom_similarity_css()  # 類似性検索用のCSS

    # サイドバーでアプリの機能を選択
    st.sidebar.title("機能")
    option = st.sidebar.radio(
        "操作を選んでください",
        ["ゲーム名で検索", "ゲームIDで詳細情報を取得", 
         "YAMLでデータを保存", "ゲーム比較", "類似性検索"]
    )

    # 選択された機能に基づいてページを表示
    if option == "ゲーム名で検索":
        search_page()
    elif option == "ゲームIDで詳細情報を取得":
        details_page()
    elif option == "YAMLでデータを保存":
        save_page()
    elif option == "ゲーム比較":
        compare_page()
    elif option == "類似性検索":
        similarity_search_page()

    # フッター
    st.sidebar.markdown("---")
    st.sidebar.caption("BoardGameGeek API と事前計算されたエンベディングを使用したボードゲームデータツール")

if __name__ == "__main__":
    main()