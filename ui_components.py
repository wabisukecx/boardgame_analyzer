import streamlit as st
import pandas as pd
from learning_curve import (
    get_player_type_display, 
    get_mastery_time_display, get_replayability_display
)


# カスタムスタイル用のCSSを定義
def load_css():
    """アプリケーションで使用するカスタムCSSをロードする"""
    st.markdown("""
    <style>
        /* メトリック値のフォントサイズを調整 */
        .metric-value {
            font-size: 0.9rem !important;
        }
        
        /* カスタム指標用のスタイル */
        .custom-metric {
            padding: 8px;
            border-radius: 5px;
            background-color: #f8f9fa;
            margin-bottom: 8px;
        }
        .custom-metric-label {
            font-size: 0.85rem;
            color: #6c757d;
            font-weight: bold;
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


# カスタムメトリック表示関数
def display_custom_metric(label, value):
    """カスタムスタイルのメトリックを表示する"""
    st.markdown(f"""
    <div class="custom-metric">
        <div class="custom-metric-label">{label}</div>
        <div class="custom-metric-value" style="font-size: 0.9rem;">{value}</div>
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
        <div style="text-align: center; padding: 15px; background-color: #f8f9fa; 
        border-radius: 5px; margin-bottom: 10px;">
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
    
    # 見出し追加
    st.markdown("### ゲーム基本情報")
    
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


def display_game_complexity(game_details):
    """ゲームの複雑さを表示する"""
    st.markdown("#### ゲームの複雑さ")
    weight = game_details.get('weight', '不明')
    if weight != '不明':
        # 小数点第二位までに丸める
        weight = f"{float(weight):.2f}/5.00"
    display_custom_metric("BGG複雑さ評価", weight)

def display_learning_curve(learning_curve):
    """
    ラーニングカーブの情報を表示する（カテゴリとランキング情報を活用した改善版）
    
    Parameters:
    learning_curve (dict): ラーニングカーブの情報
    """
    st.markdown("### ラーニングカーブ分析")
    
    # 基本情報を2列に変更（3列から2列に変更して列幅を広くする）
    col1, col2 = st.columns(2)
    with col1:
        # 小数点第二位までに丸める
        initial_barrier = f"{float(learning_curve['initial_barrier']):.2f}/5.00"
        display_custom_metric(
            "初期学習の障壁",
            initial_barrier
        )
    with col2:
        # 戦略深度に説明文を追加
        strategic_depth = learning_curve['strategic_depth']
        strategic_depth_desc = learning_curve.get('strategic_depth_description', '')
        if not strategic_depth_desc:
            # 説明がない場合は簡易的な説明を生成
            if strategic_depth >= 4.5:
                strategic_depth_desc = "非常に深い"
            elif strategic_depth >= 4.0:
                strategic_depth_desc = "深い"
            elif strategic_depth >= 3.5:
                strategic_depth_desc = "中〜高"
            elif strategic_depth >= 3.0:
                strategic_depth_desc = "中程度"
            elif strategic_depth >= 2.5:
                strategic_depth_desc = "中〜低"
            else:
                strategic_depth_desc = "浅い"
        
        # 小数点第二位までに丸める
        strategic_depth_value = f"{float(strategic_depth):.2f}/5.00"
        display_custom_metric(
            "戦略の深さ",
            f"{strategic_depth_value} ({strategic_depth_desc})"
        )
    
    # メカニクスの複雑度とリプレイ性を表示
    col1, col2 = st.columns(2)
    with col1:
        if 'mechanics_complexity' in learning_curve:
            # 小数点第二位までに丸める
            mechanics_complexity = f"{float(learning_curve['mechanics_complexity']):.2f}/5.00"
            display_custom_metric(
                "メカニクスの複雑度",
                mechanics_complexity
            )
        
        # マスター時間を表示（あれば）
        if 'mastery_time' in learning_curve:
            mastery_time_ja = get_mastery_time_display(learning_curve['mastery_time'])
            display_custom_metric("マスターにかかる時間", mastery_time_ja)
    with col2:
        if 'replayability' in learning_curve:
            replay_score = learning_curve['replayability']
            replay_display = get_replayability_display(replay_score)
            # 小数点第二位までに丸める
            replay_score_formatted = f"{float(replay_score):.2f}/5.00"
            display_custom_metric(
                "リプレイ性",
                f"{replay_score_formatted} ({replay_display})"
            )
    
    # 推奨プレイヤータイプを表示
    if 'player_types' in learning_curve and learning_curve['player_types']:
        player_types_text = ", ".join(
            [get_player_type_display(pt) for pt in learning_curve['player_types']]
        )
        st.info(f"推奨プレイヤータイプ: {player_types_text}")
    
    # 詳細分析の表示（改善版で追加された指標を含む）
    with st.expander("詳細分析", expanded=False):
        st.markdown("#### メカニクスとカテゴリの詳細指標")
        
        # 詳細指標を2列で表示
        col1, col2 = st.columns(2)
        with col1:
            if 'decision_points' in learning_curve:
                decision_points = learning_curve['decision_points']
                decision_desc = ""
                if decision_points >= 4.5:
                    decision_desc = "（非常に多様な選択肢）"
                elif decision_points >= 4.0:
                    decision_desc = "（多くの重要な決断）"
                elif decision_points >= 3.0:
                    decision_desc = "（バランスの取れた選択肢）"
                else:
                    decision_desc = "（限られた選択肢）"
                
                # 小数点第二位までに丸める
                decision_points_formatted = f"{float(decision_points):.2f}/5.00"
                display_custom_metric(
                    "意思決定ポイント",
                    f"{decision_points_formatted} {decision_desc}"
                )
            
            if 'rules_complexity' in learning_curve:
                # 小数点第二位までに丸める
                rules_complexity = f"{float(learning_curve['rules_complexity']):.2f}/5.00"
                display_custom_metric(
                    "ルールの複雑さ",
                    rules_complexity
                )
                
            # 新しく追加したカテゴリ複雑さの表示
            if 'category_complexity' in learning_curve:
                category_complexity = f"{float(learning_curve['category_complexity']):.2f}/5.00"
                display_custom_metric(
                    "カテゴリに基づく複雑さ",
                    category_complexity
                )
        
        with col2:
            if 'interaction_complexity' in learning_curve:
                interaction = learning_curve['interaction_complexity']
                interaction_desc = ""
                if interaction >= 4.5:
                    interaction_desc = "（高度な対人戦略）"
                elif interaction >= 3.5:
                    interaction_desc = "（中〜高レベルの相互作用）"
                elif interaction >= 2.5:
                    interaction_desc = "（中程度の相互作用）"
                else:
                    interaction_desc = "（低い相互作用）"
                
                # 小数点第二位までに丸める
                interaction_formatted = f"{float(interaction):.2f}/5.00"
                display_custom_metric(
                    "プレイヤー相互作用",
                    f"{interaction_formatted} {interaction_desc}"
                )
            
            if 'mechanics_count' in learning_curve:
                display_custom_metric(
                    "メカニクスの数",
                    f"{learning_curve['mechanics_count']}"
                )
                
            # 新しく追加したランキング複雑さの表示
            if 'rank_complexity' in learning_curve:
                rank_complexity = f"{float(learning_curve['rank_complexity']):.2f}/5.00"
                display_custom_metric(
                    "ゲーム種別に基づく複雑さ",
                    rank_complexity
                )
        
        # 原データ表示
        if 'bgg_weight' in learning_curve:
            st.markdown("#### BGGデータ（参考）")
            bgg_row1, bgg_row2 = st.columns(2)
            with bgg_row1:
                # 小数点第二位までに丸める
                bgg_weight = f"{float(learning_curve['bgg_weight']):.2f}/5.00"
                display_custom_metric(
                    "BGG複雑さ評価（原データ）",
                    bgg_weight
                )
            
            with bgg_row2:
                if 'bgg_rank' in learning_curve and learning_curve['bgg_rank']:
                    display_custom_metric(
                        "BGGランキング",
                        f"{learning_curve['bgg_rank']}"
                    )

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
    from game_analyzer import generate_game_summary
    
    st.markdown("### ゲーム評価サマリー")
    
    # 自動生成されたサマリーを表示
    summary = generate_game_summary(game_data, learning_curve)
    st.markdown(summary)
    
    # 複雑さと戦略性の視覚化（オプション）
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