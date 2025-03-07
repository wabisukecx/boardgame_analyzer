import streamlit as st

# 自作モジュールをインポート
from bgg_api import search_games, get_game_details
from ui_components import (
    load_css, display_game_basic_info,
    display_game_players_info, display_game_age_time_info,
    display_game_complexity, display_learning_curve, display_data_tabs
)
from data_handler import save_game_data_to_yaml, search_results_to_dataframe
from learning_curve import calculate_learning_curve

# ページ設定
st.set_page_config(
    page_title="BoardGameGeek API ツール",
    page_icon="🎲",
    layout="wide"
)

# カスタムCSSをロード
load_css()

# サイドバーでアプリの機能を選択
st.sidebar.title("機能")
option = st.sidebar.radio(
    "操作を選んでください",
    ["ゲーム名で検索", "ゲームIDで詳細情報を取得", "YAMLでデータを保存"]
)

# 選択された機能に基づいてUIを表示
if option == "ゲーム名で検索":
    st.header("ゲーム名で検索")
    
    # 検索パラメータ入力欄
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("検索するゲーム名を入力してください")
    with col2:
        exact = st.checkbox("完全一致検索", value=False)
    
    # 検索ボタン
    if st.button("検索", type="primary"):
        if query:
            results = search_games(query, exact)
            
            if results:
                st.success(f"検索結果: {len(results)}件見つかりました")
                
                # DataFrameに変換して表示
                df = search_results_to_dataframe(results)
                st.dataframe(df, use_container_width=True)
                
                # 詳細情報へのリンクを追加
                st.info("詳細情報を表示するには「ゲームIDで詳細情報を取得」機能を使用してください。")
                
                # セッションステートに結果を保存
                st.session_state.search_results = results
            else:
                st.warning("検索結果がありません")
        else:
            st.error("検索するゲーム名を入力してください")

elif option == "ゲームIDで詳細情報を取得":
    st.header("ゲームIDで詳細情報を取得")
    
    game_id = st.text_input("詳細情報を取得するゲームIDを入力してください")
    
    if st.button("詳細情報を取得", type="primary"):
        if game_id:
            game_details = get_game_details(game_id)
            
            if game_details:
                # アンカータグを追加（サイドバーからのリンク用）
                st.markdown(f"<div id='{game_id}'></div>", unsafe_allow_html=True)
                
                # 基本情報を表示
                display_game_basic_info(game_details)
                
                # 追加の基本情報を表示
                st.subheader("ゲーム情報")
                col1, col2 = st.columns(2)
                
                with col1:
                    display_game_players_info(game_details)
                
                with col2:
                    display_game_age_time_info(game_details)
                
                # 複雑さを表示
                col1, col2 = st.columns(2)
                with col1:
                    display_game_complexity(game_details)
                
                # ラーニングカーブ情報を計算して表示
                if 'description' in game_details and 'mechanics' in game_details and 'weight' in game_details:
                    learning_curve = calculate_learning_curve(game_details)
                    
                    # ラーニングカーブの情報を表示
                    st.subheader("ラーニングカーブ分析")
                    display_learning_curve(learning_curve)
                
                # ゲームの説明文を表示
                if 'description' in game_details and game_details['description']:
                    with st.expander("ゲーム説明"):
                        st.markdown(game_details['description'])
                
                # タブを使って詳細情報を整理
                display_data_tabs(game_details)
                
                # BGGへのリンク
                st.markdown(f"[BoardGameGeekで詳細を見る](https://boardgamegeek.com/boardgame/{game_id})")
                
                # 詳細情報をセッションに保存
                if 'game_data' not in st.session_state:
                    st.session_state.game_data = {}
                
                st.session_state.game_data[game_id] = game_details
                
            else:
                st.warning("ゲーム詳細情報が見つかりませんでした")
        else:
            st.error("ゲームIDを入力してください")

elif option == "YAMLでデータを保存":
    st.header("ゲームデータをYAML形式で保存")
    
    # 保存するゲームIDの選択
    game_ids = []
    if 'game_data' in st.session_state and st.session_state.game_data:
        game_ids = list(st.session_state.game_data.keys())
        selected_game_id = st.selectbox(
            "保存するゲームデータを選択してください", 
            game_ids,
            format_func=lambda x: f"{x}_{st.session_state.game_data[x].get('japanese_name', st.session_state.game_data[x].get('name', '名称不明'))}"
        )
        
        # 選択したゲームのデータを表示
        if selected_game_id:
            game_data = st.session_state.game_data[selected_game_id]
            
            # ゲーム名と基本情報を表示（日本語名があれば表示）
            game_name = game_data.get('name', '名称不明')
            japanese_name = game_data.get('japanese_name', '')
            
            if japanese_name:
                st.markdown(f"## {japanese_name}")
                st.markdown(f"**英語名:** {game_name}")
            else:
                st.markdown(f"## {game_name}")
            
            st.markdown(f"**ゲームID:** {selected_game_id}")
            
            # ゲームサムネイルを表示（ある場合）
            if 'thumbnail_url' in game_data:
                st.image(game_data['thumbnail_url'], caption=japanese_name or game_name)
            
            if 'year_published' in game_data:
                st.markdown(f"**発行年:** {game_data['year_published']}")
            
            # ファイル名の指定欄をボタンの前に配置
            display_name = japanese_name or game_name
            placeholder_filename = f"{selected_game_id}_{display_name}.yaml"
            # 特殊文字を置換（セミコロンも追加）
            placeholder_filename = placeholder_filename.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace(";", "_")
            
            custom_filename = st.text_input(
                "保存するファイル名 (空白の場合はplaceholderの名前を使用)", 
                value="", 
                placeholder=placeholder_filename
            )
            
            # 保存ボタン
            if st.button("選択したゲームデータをYAMLに保存", type="primary"):
                success, file_path, error_msg = save_game_data_to_yaml(game_data, custom_filename)
                
                if success:
                    st.success(f"ゲームデータをYAMLファイルに保存しました: {file_path}")
                else:
                    st.error(f"ファイル保存エラー: {error_msg}")
                    st.error("特殊文字（:;など）を含むゲーム名があると保存に失敗する場合があります。")
    else:
        st.info("保存可能なゲームデータがありません。まずゲームを検索して詳細情報を取得してください。")

# フッター
st.sidebar.markdown("---")
st.sidebar.caption("BoardGameGeek API を使用したデータ収集ツール")