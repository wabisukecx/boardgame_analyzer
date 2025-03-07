import streamlit as st
import os
import re
import json
import deepdiff
import yaml

# 既存のインポート
from bgg_api import search_games, get_game_details
from ui_components import (
    load_css, display_game_basic_info,
    display_game_players_info, display_game_age_time_info,
    display_game_complexity, display_learning_curve, display_data_tabs
)
from data_handler import save_game_data_to_yaml, search_results_to_dataframe, load_game_data_from_yaml
from learning_curve import calculate_learning_curve

# YAMLファイルからゲームIDとタイトルを抽出する関数
def get_yaml_game_list():
    """
    game_dataフォルダ内のYAMLファイルを走査し、ゲームIDとタイトルのリストを返す
    
    Returns:
    list: (ゲームID, ファイル名, 表示名)のタプルのリスト
    """
    game_list = []
    # game_dataフォルダが存在するか確認
    if not os.path.exists("game_data"):
        return game_list
        
    # YAMLファイルを検索
    for filename in os.listdir("game_data"):
        if filename.endswith(".yaml"):
            # ファイル名からゲームIDを抽出 (例: "167791_テラフォーミング・マーズ.yaml")
            match = re.match(r"(\d+)_(.*?)\.yaml", filename)
            if match:
                game_id = match.group(1)
                game_name = match.group(2)
                display_name = f"{game_id} - {game_name}"
                game_list.append((game_id, filename, display_name))
    
    # IDでソート
    game_list.sort(key=lambda x: int(x[0]))
    return game_list

# データの内容を比較する関数
def compare_game_data(old_data, new_data):
    """
    2つのゲームデータを比較し、重要な変更があるかどうかと変更内容を返す
    
    Parameters:
    old_data (dict): 既存のゲームデータ
    new_data (dict): 新しく取得したゲームデータ
    
    Returns:
    tuple: (変更があるかどうか, 変更の説明)
    """
    if not old_data or not new_data:
        return True, "データが不完全なため、更新が必要です。"
    
    # 重要なキーを定義
    important_keys = {
        'name': '英語名',
        'japanese_name': '日本語名',
        'year_published': '発行年',
        'average_rating': '平均評価',
        'weight': '複雑さ',
        # メカニクスやカテゴリは複雑な構造なので別途処理
    }
    
    changes = []
    has_changes = False
    
    # 基本的なフィールドの比較
    for key, display_name in important_keys.items():
        old_value = old_data.get(key)
        new_value = new_data.get(key)
        
        # データ型の違いを考慮して比較（文字列と数値の場合）
        if isinstance(old_value, (int, float)) and isinstance(new_value, str):
            try:
                new_value = float(new_value) if '.' in new_value else int(new_value)
            except ValueError:
                pass
        elif isinstance(new_value, (int, float)) and isinstance(old_value, str):
            try:
                old_value = float(old_value) if '.' in old_value else int(old_value)
            except ValueError:
                pass
        
        if old_value != new_value:
            has_changes = True
            if key in ['average_rating', 'weight'] and isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
                # 数値の場合は小数点2桁で丸める
                old_str = f"{old_value:.2f}" if isinstance(old_value, float) else str(old_value)
                new_str = f"{new_value:.2f}" if isinstance(new_value, float) else str(new_value)
                changes.append(f"- {display_name}: {old_str} → {new_str}")
            else:
                changes.append(f"- {display_name}: {old_value} → {new_value}")
    
    # メカニクスの比較
    old_mechanics = set(m.get('name', '') for m in old_data.get('mechanics', []))
    new_mechanics = set(m.get('name', '') for m in new_data.get('mechanics', []))
    
    if old_mechanics != new_mechanics:
        has_changes = True
        added = new_mechanics - old_mechanics
        removed = old_mechanics - new_mechanics
        
        if added:
            changes.append(f"- 追加されたメカニクス: {', '.join(added)}")
        if removed:
            changes.append(f"- 削除されたメカニクス: {', '.join(removed)}")
    
    # カテゴリの比較
    old_categories = set(c.get('name', '') for c in old_data.get('categories', []))
    new_categories = set(c.get('name', '') for c in new_data.get('categories', []))
    
    if old_categories != new_categories:
        has_changes = True
        added = new_categories - old_categories
        removed = old_categories - new_categories
        
        if added:
            changes.append(f"- 追加されたカテゴリ: {', '.join(added)}")
        if removed:
            changes.append(f"- 削除されたカテゴリ: {', '.join(removed)}")
    
    # 変更の説明を結合
    change_description = '\n'.join(changes) if changes else "変更はありませんでした。"
    
    return has_changes, change_description

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
                
                # 複雑さを表示
                col1, col2 = st.columns(2)
                with col1:
                    display_game_complexity(game_details)
                
                # ラーニングカーブ情報を計算して表示
                if ('description' in game_details and 'mechanics' in game_details
                        and 'weight' in game_details):
                    learning_curve = calculate_learning_curve(game_details)
                    
                    # ラーニングカーブの情報を表示
                    display_learning_curve(learning_curve)
                
                # ゲームの説明文を表示
                if 'description' in game_details and game_details['description']:
                    with st.expander("ゲーム説明"):
                        st.markdown(game_details['description'])
                
                # タブを使って詳細情報を整理
                display_data_tabs(game_details)
                
                # BGGへのリンク
                st.markdown(
                    f"[BoardGameGeekで詳細を見る](https://boardgamegeek.com/boardgame/{game_id})"
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
                                st.success(f"ゲームデータが更新されました。YAMLファイルを最新情報で上書き保存しました。")
                            else:
                                st.error(f"ファイル更新エラー: {error_msg}")
                    else:
                        st.info("保存されているデータと新しく取得したデータに違いはありません。")
                
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
            placeholder_filename = placeholder_filename.replace(" ", "_").replace(
                "/", "_").replace("\\", "_").replace(":", "_").replace(";", "_")
            
            custom_filename = st.text_input(
                "保存するファイル名 (空白の場合はplaceholderの名前を使用)", 
                value="", 
                placeholder=placeholder_filename
            )
            
            # 保存ボタン
            if st.button("選択したゲームデータをYAMLに保存", type="primary"):
                success, file_path, error_msg = save_game_data_to_yaml(
                    game_data, custom_filename
                )
                
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