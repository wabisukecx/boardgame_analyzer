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
    display_game_complexity, display_learning_curve, display_data_tabs,
    display_game_analysis_summary, display_custom_metric
)

# YAML更新用の関数をインポート
from src.analysis.mechanic_complexity import (
    add_missing_mechanic, 
    flush_pending_mechanics
)
from src.analysis.category_complexity import add_missing_category
from src.analysis.rank_complexity import add_missing_rank_type

def update_yaml_from_game_data(game_data):
    """
    ゲームデータからYAML設定を更新する
    
    Parameters:
    game_data (dict): ゲームデータ
    """
    # メカニクスの処理
    if 'mechanics' in game_data and isinstance(game_data['mechanics'], list):
        for mechanic in game_data['mechanics']:
            if isinstance(mechanic, dict) and 'name' in mechanic:
                mechanic_name = mechanic['name']
                # メカニクスを追加
                add_missing_mechanic(mechanic_name)
    
    # カテゴリの処理
    if 'categories' in game_data and isinstance(game_data['categories'], list):
        for category in game_data['categories']:
            if isinstance(category, dict) and 'name' in category:
                category_name = category['name']
                # カテゴリを追加
                add_missing_category(category_name)
    
    # ランキングの処理
    if 'ranks' in game_data and isinstance(game_data['ranks'], list):
        for rank in game_data['ranks']:
            if isinstance(rank, dict) and 'type' in rank:
                rank_type = rank['type']
                # ランキング種別を追加
                add_missing_rank_type(rank_type)
    
    # 保留中のメカニクスを保存
    flush_pending_mechanics()
    
    st.session_state['yaml_updated'] = True

def details_page():
    """ゲームIDで詳細情報を取得するページを表示"""
    st.header("ゲームIDで詳細情報を取得")
    
    # YAML更新状態を管理
    if 'yaml_updated' not in st.session_state:
        st.session_state['yaml_updated'] = False
    
    # 既存のYAMLファイルから選択できるようにする
    yaml_games = get_yaml_game_list()
    
    # 入力方法を選択
    input_method = st.radio(
        "入力方法を選択",
        ["手動入力", "保存済みYAMLファイルから選択"],
        horizontal=True
    )
    
    yaml_data = None
    yaml_file_path = None
    
    if input_method == "手動入力":
        game_id = st.text_input("詳細情報を取得するゲームIDを入力してください")
    else:
        if yaml_games:
            selected_game = st.selectbox(
                "保存済みゲームから選択",
                options=yaml_games,
                format_func=lambda x: x[2]  # 表示名を使用
            )
            game_id = selected_game[0] if selected_game else ""
            
            # 選択されたYAMLファイルからデータをロード
            if selected_game:
                yaml_file_path = os.path.join("game_data", selected_game[1])
                yaml_data = load_game_data_from_yaml(yaml_file_path)
        else:
            st.warning("保存済みのYAMLファイルが見つかりません")
            game_id = ""
    
    if st.button("詳細情報を取得", type="primary"):
        if game_id:
            game_details = get_game_details(game_id)
            
            if game_details:
                # *** 新機能: YAMLデータを更新 ***
                update_yaml_from_game_data(game_details)
                
                # 更新通知を表示
                if st.session_state['yaml_updated']:
                    st.success("メカニクス、カテゴリ、ランキング設定が更新されました")
                    st.session_state['yaml_updated'] = False
                
                # アンカータグを追加（サイドバーからのリンク用）
                st.markdown(f"<div id='{game_id}'></div>", unsafe_allow_html=True)
                
                # 基本情報を表示
                display_game_basic_info(game_details)
                
                # 追加の基本情報を表示
                col1, col2 = st.columns(2)
                
                with col1:
                    display_game_players_info(game_details)
                
                with col2:
                    display_game_age_time_info(game_details)
                
                # 複雑さを表示 (BGG複雑さ評価のみ)
                col1, col2 = st.columns(2)
                with col1:
                    # BGG複雑さ評価
                    weight = game_details.get('weight', '不明')
                    if weight != '不明':
                        # 小数点第二位までに丸める
                        weight = f"{float(weight):.2f}/5.00"
                    display_custom_metric("BGG複雑さ評価", weight)
                
                # ラーニングカーブ情報を計算
                learning_curve = None
                if ('description' in game_details and 'mechanics' in game_details
                        and 'weight' in game_details):
                    learning_curve = calculate_learning_curve(game_details)
                
                # ラーニングカーブの情報を表示
                if learning_curve:
                    display_learning_curve(learning_curve)
                    
                    # 評価サマリーを表示
                    display_game_analysis_summary(game_details, learning_curve)
                
                # ゲームの説明文を表示
                if 'description' in game_details and game_details['description']:
                    with st.expander("ゲーム説明"):
                        st.markdown(game_details['description'])
                
                # タブを使って詳細情報を整理
                display_data_tabs(game_details)
                
                # BGGへのリンク
                st.markdown(
                    f"[BoardGameGeekで詳細を見る](https://boardgamegeek.com/boardgame/{game_id.lstrip('0')})"
                )
                
                # 詳細情報をセッションに保存
                if 'game_data' not in st.session_state:
                    st.session_state.game_data = {}
                
                st.session_state.game_data[game_id] = game_details
                
                # YAMLファイルから読み込んだデータと比較して、変更があれば自動保存
                if yaml_data and yaml_file_path:
                    has_changes, change_description = compare_game_data(yaml_data, game_details)
                    
                    if has_changes:
                        # 変更がある場合は、変更内容を表示して更新するか尋ねる
                        st.warning("保存されているデータと新しく取得したデータに違いがあります。")
                        
                        with st.expander("変更内容の詳細"):
                            st.markdown(change_description)
                        
                        if st.button("YAMLファイルを更新する", key="update_yaml"):
                            # 元のファイル名を維持
                            original_filename = os.path.basename(yaml_file_path)
                            
                            success, file_path, error_msg = save_game_data_to_yaml(
                                game_details, original_filename
                            )
                            
                            if success:
                                st.success("ゲームデータが更新されました。YAMLファイルを最新情報で上書き保存しました。")
                            else:
                                st.error(f"ファイル更新エラー: {error_msg}")
                    else:
                        st.info("保存されているデータと新しく取得したデータに違いはありません。")
            else:
                st.warning("ゲーム詳細情報が見つかりませんでした")
        else:
            st.error("ゲームIDを入力してください")