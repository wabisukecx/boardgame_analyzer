import streamlit as st
import os
import re
import pandas as pd

from src.api.bgg_api import search_games, get_game_details
from ui.ui_components import (
    load_css, display_game_basic_info,
    display_game_players_info, display_game_age_time_info,
    display_game_complexity, display_learning_curve, display_data_tabs,
    display_game_analysis_summary, display_custom_metric
)
from src.data.data_handler import (
    save_game_data_to_yaml, search_results_to_dataframe, load_game_data_from_yaml
)
from src.analysis.learning_curve import calculate_learning_curve
from ui.ui_components import compare_games_radar_chart
from src.data.data_handler import load_all_game_data

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
    ["ゲーム名で検索", "ゲームIDで詳細情報を取得", "YAMLでデータを保存", "ゲーム比較"]
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
                                st.success("ゲームデータが更新されました。YAMLファイルを最新情報で上書き保存しました。")
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

elif option == "ゲーム比較":
    st.header("複数ゲームの比較")
    
    # 保存済みのゲームデータを読み込む
    all_game_data = load_all_game_data()
    
    if not all_game_data:
        st.warning("保存済みのゲームデータがありません。まずはゲームを検索して保存してください。")
    else:
        # ゲームの選択オプションを作成
        game_options = []
        for game_id, game_data in all_game_data.items():
            # 日本語名を優先
            display_name = game_data.get('japanese_name', game_data.get('name', '名称不明'))
            game_options.append({"id": game_id, "name": display_name})
        
        # IDで並び替え
        game_options.sort(key=lambda x: x["id"])
        
        # 表示用の辞書を作成
        game_display_dict = {f"{g['id']} - {g['name']}": g["id"] for g in game_options}
        
        # マルチセレクト
        st.subheader("比較するゲームを選択してください")
        selected_game_keys = st.multiselect(
            "比較するゲーム (最大6つまで選択可能)", 
            options=list(game_display_dict.keys()),
            default=[]
        )
        
        if selected_game_keys:
            selected_game_ids = [game_display_dict[key] for key in selected_game_keys]
            
            # 選択されたゲームを最大6つまでに制限
            if len(selected_game_ids) > 6:
                st.warning("表示は最大6ゲームまでに制限されます。最初の6つを表示します。")
                selected_game_ids = selected_game_ids[:6]
            
            # 各ゲームのデータと学習曲線情報を取得
            games_data = []
            for game_id in selected_game_ids:
                game_data = all_game_data[game_id]
                
                # 学習曲線情報がある場合はそれを使用
                if 'learning_analysis' in game_data:
                    learning_curve = game_data['learning_analysis']
                # なければ計算する
                elif ('description' in game_data and 'mechanics' in game_data and 
                      'weight' in game_data):
                    learning_curve = calculate_learning_curve(game_data)
                else:
                    st.warning(f"{game_data.get('name', 'ID: '+game_id)} の学習曲線情報を取得できません。")
                    continue
                
                games_data.append((game_data, learning_curve))
            
            # 比較レーダーチャートを表示
            if games_data:
                st.subheader("ゲーム特性比較チャート")
                fig = compare_games_radar_chart(games_data)
                st.plotly_chart(fig, use_container_width=True)
                
                # テーブル形式でも数値を表示
                st.subheader("数値比較")
                comparison_data = []
                for game_data, learning_curve in games_data:
                    game_name = game_data.get('japanese_name', game_data.get('name', '不明'))
                    comparison_data.append({
                        "ゲーム名": game_name,
                        "初期学習障壁": f"{learning_curve.get('initial_barrier', 0):.2f}",
                        "戦略的深さ": f"{learning_curve.get('strategic_depth', 0):.2f}",
                        "リプレイ性": f"{learning_curve.get('replayability', 0):.2f}",
                        "意思決定の深さ": f"{learning_curve.get('decision_points', 0):.2f}",
                        "プレイヤー相互作用": f"{learning_curve.get('interaction_complexity', 0):.2f}",
                        "ルールの複雑さ": f"{learning_curve.get('rules_complexity', 0):.2f}",
                        "BGG重み": f"{float(game_data.get('weight', 0)):.2f}"
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, use_container_width=True)

# フッター
st.sidebar.markdown("---")
st.sidebar.caption("BoardGameGeek API を使用したデータ収集ツール")
