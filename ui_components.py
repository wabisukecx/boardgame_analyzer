import streamlit as st
import pandas as pd
from learning_curve import get_curve_type_display, get_player_type_display

# カスタムスタイル用のCSSを定義
def load_css():
    """アプリケーションで使用するカスタムCSSをロードする"""
    st.markdown("""
    <style>
        /* メトリック値のフォントサイズを調整 */
        .metric-value {
            font-size: 1.5rem !important;
        }
        
        /* カスタム指標用のスタイル */
        .custom-metric {
            padding: 10px;
            border-radius: 5px;
            background-color: #f8f9fa;
            margin-bottom: 10px;
        }
        .custom-metric-label {
            font-size: 0.9rem;
            color: #6c757d;
        }
        .custom-metric-value {
            font-size: 1.2rem;
            font-weight: 500;
        }
        
        /* サムネイル画像用のスタイル */
        .game-thumbnail {
            width: 100%;
            border-radius: 5px;
            margin-bottom: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

# カスタムメトリック表示関数
def display_custom_metric(label, value):
    """カスタムスタイルのメトリックを表示する"""
    st.markdown(f"""
    <div class="custom-metric">
        <div class="custom-metric-label">{label}</div>
        <div class="custom-metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# サムネイル表示関数
def display_game_thumbnail(thumbnail_url, game_name):
    """ゲームのサムネイル画像を表示する"""
    if thumbnail_url:
        st.markdown(f"""
        <div style="text-align: center;">
            <img src="{thumbnail_url}" alt="{game_name}" class="game-thumbnail">
            <p style="font-size: 0.9rem; margin-top: 0px;">{game_name}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 画像がない場合のプレースホルダー
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 10px;">
            <p style="color: #6c757d;">画像なし</p>
            <p style="font-size: 0.9rem; margin-top: 5px;">{game_name}</p>
        </div>
        """, unsafe_allow_html=True)

# ゲーム詳細表示関数
def display_game_basic_info(game_details):
    """ゲームの基本情報を表示する"""
    # 日本語名を取得
    japanese_name = game_details.get('japanese_name', '')
    english_name = game_details.get('name', '不明')
    
    # 表示する名前（日本語名があれば優先）
    display_name = japanese_name or english_name
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("ゲーム名", display_name)
        if japanese_name and english_name != japanese_name:
            st.caption(f"英語名: {english_name}")
    with col2:
        st.metric("発行年", game_details.get('year_published', '不明'))
    with col3:
        rating = game_details.get('average_rating', '不明')
        if rating != '不明':
            rating = round(float(rating), 2)
        st.metric("平均評価", rating)
    
    # ゲームサムネイルを表示（ある場合）
    if 'thumbnail_url' in game_details:
        st.image(game_details['thumbnail_url'], caption=display_name, use_container_width=False)

def display_game_players_info(game_details):
    """ゲームのプレイ人数情報を表示する"""
    st.markdown("#### プレイ人数")
    # コミュニティの推奨人数を優先
    if 'community_best_players' in game_details:
        display_custom_metric("ベストプレイ人数（コミュニティ推奨）", game_details['community_best_players'])
    
    # パブリッシャー指定のプレイ人数も表示
    publisher_players = "不明"
    if 'publisher_min_players' in game_details and 'publisher_max_players' in game_details:
        publisher_players = f"{game_details['publisher_min_players']}～{game_details['publisher_max_players']}人"
    display_custom_metric("パブリッシャー指定プレイ人数", publisher_players)

def display_game_age_time_info(game_details):
    """ゲームの年齢・プレイ時間情報を表示する"""
    st.markdown("#### 推奨年齢・プレイ時間")
    # コミュニティの推奨年齢を優先
    if 'community_min_age' in game_details:
        display_custom_metric("推奨年齢（コミュニティ推奨）", f"{game_details['community_min_age']}歳以上")
    
    # プレイ時間
    playtime = game_details.get('playing_time', '不明')
    if playtime != '不明':
        playtime = f"{playtime}分"
    display_custom_metric("プレイ時間", playtime)

def display_game_complexity(game_details):
    """ゲームの複雑さを表示する"""
    st.markdown("#### ゲームの複雑さ")
    weight = game_details.get('weight', '不明')
    if weight != '不明':
        weight = f"{round(float(weight), 2)}/5.0"
    display_custom_metric("BGG複雑さ評価", weight)

def display_learning_curve(learning_curve):
    """ラーニングカーブの情報を表示する"""
    col1, col2, col3 = st.columns(3)
    with col1:
        display_custom_metric("初期学習の障壁", f"{learning_curve['initial_barrier']}/5.0")
    with col2:
        display_custom_metric("戦略の深さ", f"{learning_curve['strategic_depth']}/5.0")
    with col3:
        curve_type_ja = get_curve_type_display(learning_curve['learning_curve_type'])
        display_custom_metric("学習曲線タイプ", curve_type_ja)
    
    # 推奨プレイヤータイプを表示
    if 'player_types' in learning_curve and learning_curve['player_types']:
        player_types_text = ", ".join([get_player_type_display(pt) for pt in learning_curve['player_types']])
        st.info(f"推奨プレイヤータイプ: {player_types_text}")

def display_data_tabs(game_details):
    """タブを使って詳細情報を表示する"""
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["メカニクス", "カテゴリ", "ランキング", "デザイナー", "パブリッシャー"])
    
    with tab1:
        if 'mechanics' in game_details and game_details['mechanics']:
            # DataFrameに変換して表示
            df = pd.DataFrame(game_details['mechanics'])
            df = df.rename(columns={
                "id": "メカニクスID",
                "name": "メカニクス名"
            })
            st.dataframe(df, use_container_width=True)
        else:
            st.info("メカニクス情報がありません")
    
    with tab2:
        if 'categories' in game_details and game_details['categories']:
            # DataFrameに変換して表示
            df = pd.DataFrame(game_details['categories'])
            df = df.rename(columns={
                "id": "カテゴリID",
                "name": "カテゴリ名"
            })
            st.dataframe(df, use_container_width=True)
        else:
            st.info("カテゴリ情報がありません")
    
    with tab3:
        if 'ranks' in game_details and game_details['ranks']:
            # DataFrameに変換して表示
            df = pd.DataFrame(game_details['ranks'])
            df = df.rename(columns={
                "type": "ランキング種別",
                "id": "ランキングID",
                "rank": "順位"
            })
            st.dataframe(df, use_container_width=True)
        else:
            st.info("ランキング情報がありません")
    
    with tab4:
        if 'designers' in game_details and game_details['designers']:
            # DataFrameに変換して表示
            df = pd.DataFrame(game_details['designers'])
            df = df.rename(columns={
                "id": "デザイナーID",
                "name": "デザイナー名"
            })
            st.dataframe(df, use_container_width=True)
        else:
            st.info("デザイナー情報がありません")
    
    with tab5:
        if 'publishers' in game_details and game_details['publishers']:
            # DataFrameに変換して表示
            df = pd.DataFrame(game_details['publishers'])
            df = df.rename(columns={
                "id": "パブリッシャーID",
                "name": "パブリッシャー名"
            })
            st.dataframe(df, use_container_width=True)
        else:
            st.info("パブリッシャー情報がありません")