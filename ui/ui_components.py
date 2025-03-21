import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.analysis.game_analyzer import generate_game_summary
from src.analysis.learning_curve import (
    get_player_type_display,
    get_mastery_time_display, get_replayability_display,
    get_curve_type_display
)


def load_css():
    """アプリケーションで使用するカスタムCSSをロードする"""
    st.markdown("""
    <style>
        /* メトリック値のフォントサイズを調整 */
        .metric-value {
            font-size: 0.9rem !important;
        }
        
        /* カスタム指標用のスタイル - 幅を拡張 */
        .custom-metric {
            padding: 12px;
            border-radius: 5px;
            background-color: #f8f9fa;
            margin-bottom: 10px;
            width: 100%; /* 幅を100%に設定 */
            box-sizing: border-box; /* パディングを含めた幅計算 */
        }
        .custom-metric-label {
            font-size: 0.85rem;
            color: #6c757d;
            font-weight: bold;
            margin-bottom: 4px; /* ラベルと値の間隔を調整 */
        }
        .custom-metric-value {
            font-size: 1.0rem;
            font-weight: 400;
        }
        
        /* サムネイル画像用のスタイル */
        .game-thumbnail {
            width: 100%;
            border-radius: 5px;
            margin-bottom: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        /* 基本情報の見出しスタイル */
        .info-heading {
            font-size: 0.85rem;
            font-weight: bold;
            margin-bottom: 4px;
        }
        
        /* 基本情報の値スタイル */
        .info-value {
            font-size: 0.9rem;
        }
    </style>
    """, unsafe_allow_html=True)


def display_custom_metric(label, value):
    """カスタムスタイルのメトリックを表示する"""
    st.markdown(f"""
    <div class="custom-metric">
        <div class="custom-metric-label">{label}</div>
        <div class="custom-metric-value" style="font-size: 0.9rem;">{value}</div>
    </div>
    """, unsafe_allow_html=True)


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
        <div style="text-align: center; padding: 15px; background-color: #f8f9fa; 
        border-radius: 5px; margin-bottom: 10px;">
            <p style="color: #6c757d;">画像なし</p>
            <p style="font-size: 0.9rem; margin-top: 5px;">{game_name}</p>
        </div>
        """, unsafe_allow_html=True)


def display_game_basic_info(game_details):
    """ゲームの基本情報を表示する"""
    # 日本語名を取得
    japanese_name = game_details.get('japanese_name', '')
    english_name = game_details.get('name', '不明')
    
    # 表示する名前（日本語名があれば優先）
    display_name = japanese_name or english_name
    
    # 見出し追加
    st.markdown("### 基本情報")
    
    # カスタムHTMLでフォントサイズを調整して表示
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**ゲーム名**")
        st.markdown(
            f"<div style='font-size: 0.9rem;'>{display_name}</div>",
            unsafe_allow_html=True
        )
        if japanese_name and english_name != japanese_name:
            st.caption(f"英語名: {english_name}")
    with col2:
        st.markdown("**発行年**")
        year = game_details.get('year_published', '不明')
        st.markdown(
            f"<div style='font-size: 0.9rem;'>{year}</div>",
            unsafe_allow_html=True
        )
    with col3:
        st.markdown("**平均評価**")
        rating = game_details.get('average_rating', '不明')
        if rating != '不明':
            rating = round(float(rating), 2)
        st.markdown(
            f"<div style='font-size: 0.9rem;'>{rating}</div>",
            unsafe_allow_html=True
        )
    
    # ゲームサムネイルを表示（ある場合）
    if 'thumbnail_url' in game_details:
        st.image(
            game_details['thumbnail_url'],
            caption=display_name,
            use_container_width=False
        )


def display_game_players_info(game_details):
    """ゲームのプレイ人数情報を表示する"""
    st.markdown("#### プレイ人数")
    # コミュニティの推奨人数を優先
    if 'community_best_players' in game_details:
        display_custom_metric(
            "ベストプレイ人数（コミュニティ推奨）",
            game_details['community_best_players']
        )
    
    # パブリッシャー指定のプレイ人数も表示
    publisher_players = "不明"
    if ('publisher_min_players' in game_details and
            'publisher_max_players' in game_details):
        publisher_players = f"{game_details['publisher_min_players']}～" \
                            f"{game_details['publisher_max_players']}人"
    display_custom_metric("パブリッシャー指定プレイ人数", publisher_players)


def display_game_age_time_info(game_details):
    """ゲームの年齢・プレイ時間情報を表示する"""
    st.markdown("#### 推奨年齢・プレイ時間")
    # コミュニティの推奨年齢を優先
    if 'community_min_age' in game_details:
        display_custom_metric(
            "推奨年齢（コミュニティ推奨）",
            f"{game_details['community_min_age']}歳以上"
        )
    
    # プレイ時間
    playtime = game_details.get('playing_time', '不明')
    if playtime != '不明':
        playtime = f"{playtime}分"
    display_custom_metric("プレイ時間", playtime)


def display_game_complexity(game_details, learning_curve=None):
    """ゲームの複雑さを表示する"""
    st.markdown("#### 複雑さ")
    
    # 2列のレイアウトで、等幅に設定
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # BGG複雑さ評価
        weight = game_details.get('weight', '不明')
        if weight != '不明':
            # 小数点第二位までに丸める
            weight = f"{float(weight):.2f}/5.00"
        display_custom_metric("BGG複雑さ評価", weight)
    
    with col2:
        # システム分析（学習曲線データがある場合）
        if learning_curve and 'rules_complexity' in learning_curve:
            # 小数点第二位までに丸める
            system_analysis = f"{float(learning_curve['rules_complexity']):.2f}/5.00"
            display_custom_metric("システム分析", system_analysis)
        else:
            # 学習曲線データがない場合でも空のスペースを確保（レイアウト維持のため）
            display_custom_metric("システム分析", "計算中...")


def display_system_complexity(col, learning_curve):
    """システム分析（ルールの複雑さ）を表示する"""
    if learning_curve and 'rules_complexity' in learning_curve:
        # 小数点第二位までに丸める
        system_analysis = f"{float(learning_curve['rules_complexity']):.2f}/5.00"
        with col:
            display_custom_metric("システム分析", system_analysis)


def display_learning_curve(learning_curve, game_details=None):
    """
    ラーニングカーブの情報を表示する（カテゴリとランキング情報を活用した改善版）
    
    Parameters:
        learning_curve (dict): ラーニングカーブの情報
        game_details (dict, optional): ゲームの詳細情報（BGG複雑さを取得するため）
    """
    st.markdown("### ラーニングカーブ分析")
    
    col1, col2 = st.columns(2)
    with col1:
        # 小数点第二位までに丸める
        initial_barrier = f"{float(learning_curve['initial_barrier']):.2f}/5.00"
        display_custom_metric(
            "初期学習の障壁",
            initial_barrier
        )
    with col2:
        # 学習曲線タイプを表示
        if 'learning_curve_type' in learning_curve:
            curve_type = learning_curve['learning_curve_type']
            curve_type_display = get_curve_type_display(curve_type)
            display_custom_metric("学習曲線タイプ", curve_type_display)
        else:
            display_custom_metric("学習曲線タイプ", "計算中...")


def display_data_tabs(game_details):
    """タブを使って詳細情報を表示する"""
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "メカニクス", "カテゴリ", "ランキング", "デザイナー", "パブリッシャー"
    ])
    
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


def display_game_analysis_summary(game_data, learning_curve):
    """
    ゲームデータとラーニングカーブから簡潔な評価サマリーを表示する
    
    Parameters:
        game_data (dict): ゲームの詳細情報
        learning_curve (dict): ラーニングカーブの情報
    """
    st.markdown("### 評価サマリー")
    
    # 自動生成されたサマリーを表示
    summary = generate_game_summary(game_data, learning_curve)
    st.markdown(summary)
    
    # 複雑さと戦略性の視覚化
    with st.expander("複雑さと戦略性の視覚化", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # BGG重み vs 分析した複雑さ
            bgg_weight = float(game_data.get('weight', 0))
            rules_complexity = learning_curve.get('rules_complexity', 0)
            
            st.markdown("#### 複雑さ比較")
            st.markdown(f"- BGGユーザー評価: **{bgg_weight:.2f}**/5.00")
            st.markdown(f"- システム分析: **{rules_complexity:.2f}**/5.00")
            
            # 差異の計算と色分け
            diff = rules_complexity - bgg_weight
            if abs(diff) > 0.8:
                color = "red" if diff > 0 else "blue"
                st.markdown(f"<span style='color:{color};'>差異: {diff:.2f}</span>", unsafe_allow_html=True)
        
        with col2:
            # 戦略深度とリプレイ性
            strategic_depth = learning_curve.get('strategic_depth', 0)
            replayability = learning_curve.get('replayability', 0)
            
            st.markdown("#### 戦略性とリプレイ性")
            st.markdown(f"- 戦略的深さ: **{strategic_depth:.2f}**/5.00")
            st.markdown(f"- リプレイ性: **{replayability:.2f}**/5.00")

def compare_games_radar_chart(games_data):
    """
    複数ゲームを比較するレーダーチャートを作成
    
    Parameters:
    games_data (list): (ゲームデータ, 学習曲線データ)のタプルリスト
    
    Returns:
    fig: plotlyのFigureオブジェクト
    """
    fig = go.Figure()
    
    # 比較するカテゴリ
    categories = ['初期学習障壁', '戦略的深さ', 'リプレイ性', 
                  '意思決定の深さ', 'プレイヤー相互作用', 'ルールの複雑さ']
    
    # 各ゲームの色をパステルカラーで生成
    colors = ['rgba(178, 34, 34, 0.7)', 'rgba(31, 119, 180, 0.7)', 
              'rgba(44, 160, 44, 0.7)', 'rgba(255, 127, 14, 0.7)',
              'rgba(148, 103, 189, 0.7)', 'rgba(140, 86, 75, 0.7)']
    
    for i, (game_data, learning_curve) in enumerate(games_data):
        if i >= len(colors):  # 色数の上限
            break
            
        game_name = game_data.get('japanese_name', game_data.get('name', '不明'))
        
        values = [
            learning_curve.get('initial_barrier', 0),
            learning_curve.get('strategic_depth', 0),
            learning_curve.get('replayability', 0),
            learning_curve.get('decision_points', 0),
            learning_curve.get('interaction_complexity', 0),
            learning_curve.get('rules_complexity', 0)
        ]
        
        # 円環状に閉じる
        cat = categories + [categories[0]]
        val = values + [values[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=val,
            theta=cat,
            fill='toself',
            name=game_name,
            line_color=colors[i],
            fillcolor=colors[i].replace('0.7', '0.2')
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5]
            )
        ),
        showlegend=True,
        title={
            'text': "ゲーム特性比較",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        margin=dict(l=80, r=80, t=50, b=50),
        height=600
    )
    
    return fig