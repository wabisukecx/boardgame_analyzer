"""
src/analysis/similarity.py - ボードゲームの類似性検索機能を提供するモジュール
"""

import numpy as np
import streamlit as st
import pickle
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import pandas as pd
from collections import Counter
import io
from typing import Dict, List, Any, Tuple, Optional
import logging
import os
import platform

# 既存のモジュールからYAML関連の関数をインポート
from src.analysis.mechanic_complexity import (
    add_missing_mechanic, 
    get_complexity, 
    flush_pending_mechanics
)
from src.analysis.category_complexity import (
    add_missing_category,
    get_category_complexity
)
from src.analysis.rank_complexity import (
    add_missing_rank_type,
    get_rank_complexity_value
)

# ロギング設定
logger = logging.getLogger("similarity_module")

def setup_japanese_fonts():
    """
    日本語フォントの設定を行う
    プラットフォームに応じて適切なフォントを選択
    """
    try:
        # まず利用可能なフォントをリストアップ
        from matplotlib.font_manager import fontManager
        available_fonts = set([f.name for f in fontManager.ttflist])       
        system = platform.system()
        
        # プラットフォーム別のフォント候補
        if system == 'Windows':
            font_options = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'Arial Unicode MS']
        elif system == 'Darwin':  # macOS
            font_options = ['Hiragino Sans', 'Hiragino Maru Gothic Pro', 'Osaka', 'AppleGothic']
        elif system == 'Linux':
            font_options = ['Noto Sans CJK JP', 'IPAGothic', 'VL Gothic', 'Droid Sans Japanese']
        else:
            font_options = []
        
        # 候補に加えてどのプラットフォームでも使えそうなフォントを追加
        font_options.extend(['DejaVu Sans', 'Arial', 'Tahoma', 'Verdana'])
        
        # 利用可能なフォントを絞り込み
        available_options = [f for f in font_options if f in available_fonts]
        
        # 利用可能なフォントがあればそれを設定
        if available_options:
            font_family = available_options[0]
            matplotlib.rcParams['font.family'] = font_family
            return True
        
        # フォントが見つからない場合、フォールバックとしてsans-serifを設定
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Helvetica', 'sans-serif']
        logger.warning("日本語フォントが見つかりませんでした。デフォルトのフォントを使用します。")
        
        return False
    except Exception as e:
        logger.error(f"フォント設定エラー: {e}")
        return False

# データの読み込み
@st.cache_resource(show_spinner=True)
def load_data(data_file: str) -> Optional[Dict[str, Any]]:
    """エンベディングデータを読み込む関数
    
    Args:
        data_file (str): データファイルのパス
        
    Returns:
        Optional[Dict[str, Any]]: 読み込まれたデータ、エラー時はNone
    """
    try:
        if not os.path.exists(data_file):
            logger.error(f"データファイル {data_file} が存在しません。")
            return None
            
        with open(data_file, 'rb') as f:
            data = pickle.load(f)
            
        # データの検証
        required_keys = ['games', 'game_data_list', 'embeddings', 'similarity_matrix']
        for key in required_keys:
            if key not in data:
                logger.error(f"データファイルに必要なキー '{key}' が含まれていません。")
                return None
        
        # ゲームデータを処理してYAMLに未知のメカニクス/カテゴリ/ランキングを追加
        process_game_data_for_yaml(data['game_data_list'])
                
        return data
    except Exception as e:
        logger.error(f"データファイルの読み込みに失敗しました: {e}")
        return None

# ゲームデータを処理してYAMLに未知のメカニクス/カテゴリ/ランキングを追加する関数
def process_game_data_for_yaml(game_data_list: List[Dict[str, Any]]) -> None:
    """
    ゲームデータを処理し、YAMLに存在しないメカニクス/カテゴリ/ランキングを追加する
    
    Args:
        game_data_list (List[Dict[str, Any]]): ゲームデータのリスト
    """
    try:
        # 各ゲームからメカニクス、カテゴリ、ランキングを抽出
        for game_data in game_data_list:
            # メカニクスの処理
            if 'mechanics' in game_data and isinstance(game_data['mechanics'], list):
                for mechanic in game_data['mechanics']:
                    if isinstance(mechanic, dict) and 'name' in mechanic:
                        mechanic_name = mechanic['name']
                        # 既存のadd_missing_mechanic関数を使用
                        add_missing_mechanic(mechanic_name)
            
            # カテゴリの処理
            if 'categories' in game_data and isinstance(game_data['categories'], list):
                for category in game_data['categories']:
                    if isinstance(category, dict) and 'name' in category:
                        category_name = category['name']
                        # 既存のadd_missing_category関数を使用
                        add_missing_category(category_name)
            
            # ランキングの処理
            if 'ranks' in game_data and isinstance(game_data['ranks'], list):
                for rank in game_data['ranks']:
                    if isinstance(rank, dict) and 'type' in rank:
                        rank_type = rank['type']
                        # 既存のadd_missing_rank_type関数を使用
                        add_missing_rank_type(rank_type)
        
        # 保留中のメカニクスを保存
        flush_pending_mechanics()
        
        logger.info("ゲームデータからYAMLファイルの更新が完了しました")
    except Exception as e:
        logger.error(f"YAMLデータ処理中にエラーが発生しました: {e}")

# カテゴリとメカニクスの一覧を抽出
def extract_categories_and_mechanics(game_data_list: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    """ゲームデータからカテゴリとメカニクスの一覧を抽出する関数
    
    Args:
        game_data_list (List[Dict[str, Any]]): ゲームデータのリスト
        
    Returns:
        Tuple[List[str], List[str]]: カテゴリとメカニクスのリスト
    """
    all_categories = set()
    all_mechanics = set()
    
    for game in game_data_list:
        # カテゴリの収集
        if 'categories' in game and isinstance(game['categories'], list):
            categories = [cat.get('name', '') for cat in game['categories'] 
                          if isinstance(cat, dict) and 'name' in cat]
            all_categories.update(categories)
        
        # メカニクスの収集
        if 'mechanics' in game and isinstance(game['mechanics'], list):
            mechanics = [mech.get('name', '') for mech in game['mechanics'] 
                         if isinstance(mech, dict) and 'name' in mech]
            all_mechanics.update(mechanics)
    
    return sorted(list(all_categories)), sorted(list(all_mechanics))

# フィルター設定UIを表示
def display_filter_ui(
    categories: List[str],
    mechanics: List[str]
) -> Tuple[List[str], List[str]]:
    """フィルター設定UIを表示する関数
    
    Args:
        categories (List[str]): カテゴリのリスト
        mechanics (List[str]): メカニクスのリスト
        
    Returns:
        Tuple[List[str], List[str]]: 選択されたカテゴリとメカニクスのリスト
    """
    with st.expander("検索フィルターを設定"):
        st.markdown("### 検索フィルター")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### カテゴリで絞り込み")
            selected_categories = st.multiselect(
                "カテゴリを選択",
                options=categories,
                default=st.session_state.category_filter
            )
        
        with col2:
            st.markdown("#### メカニクスで絞り込み")
            selected_mechanics = st.multiselect(
                "メカニクスを選択",
                options=mechanics,
                default=st.session_state.mechanics_filter
            )
        
        # 選択結果を保存
        st.session_state.category_filter = selected_categories
        st.session_state.mechanics_filter = selected_mechanics
    
    return selected_categories, selected_mechanics

# ゲームをフィルタリングする関数
def filter_games(
    games: List[Dict[str, Any]],
    game_data_list: List[Dict[str, Any]],
    categories: List[str],
    mechanics: List[str]
) -> List[int]:
    """ゲームをフィルタリングする関数
    
    Args:
        games (List[Dict[str, Any]]): ゲーム情報のリスト
        game_data_list (List[Dict[str, Any]]): ゲームデータのリスト
        categories (List[str]): フィルタリングするカテゴリのリスト
        mechanics (List[str]): フィルタリングするメカニクスのリスト
        
    Returns:
        List[int]: フィルタリング後のゲームのインデックスリスト
    """
    if not categories and not mechanics:
        return list(range(len(games)))
    
    filtered_indices = []
    
    for i, game_data in enumerate(game_data_list):
        match = True
        
        if categories:
            game_categories = set()
            if 'categories' in game_data:
                game_categories = set(cat.get('name', '') for cat in game_data['categories'] 
                                    if isinstance(cat, dict) and 'name' in cat)
            
            # いずれかのカテゴリが一致するか
            if not any(cat in game_categories for cat in categories):
                match = False
        
        if mechanics and match:
            game_mechanics = set()
            if 'mechanics' in game_data:
                game_mechanics = set(mech.get('name', '') for mech in game_data['mechanics'] 
                                   if isinstance(mech, dict) and 'name' in mech)
            
            # いずれかのメカニクスが一致するか
            if not any(mech in game_mechanics for mech in mechanics):
                match = False
        
        if match:
            filtered_indices.append(i)
    
    return filtered_indices

# ゲーム情報カードの表示
def display_game_card(
    game_data: Dict[str, Any],
    is_main: bool = False
) -> None:
    """ゲーム情報カードを表示する関数
    
    Args:
        game_data (Dict[str, Any]): ゲームデータ
        is_main (bool, optional): メインカードとして表示するか. デフォルトはFalse.
    """
    game_name = game_data.get('japanese_name', '') or game_data.get('name', '')
    
    with st.container():
        st.markdown(f"<div class='game-card'>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # サムネイル画像がある場合は表示
            thumbnail_url = game_data.get('thumbnail_url', '')
            if thumbnail_url:
                st.image(thumbnail_url, width=150)
            else:
                st.markdown("🎲")
        
        with col2:
            if is_main:
                st.markdown(f"### 📊 {game_name}")
            else:
                st.markdown(f"### {game_name}")
            
            # ゲーム基本情報
            cols = st.columns(3)
            with cols[0]:
                if 'year_published' in game_data:
                    st.markdown(f"**発売年**: {game_data['year_published']}")
            with cols[1]:
                if 'weight' in game_data:
                    st.markdown(f"**複雑さ**: {game_data['weight']}")
            with cols[2]:
                if 'playing_time' in game_data:
                    st.markdown(f"**プレイ時間**: {game_data['playing_time']}分")
            
            # カテゴリとメカニクス
            if 'categories' in game_data:
                categories = [cat.get('name', '') for cat in game_data['categories'] 
                             if isinstance(cat, dict) and 'name' in cat]
                if categories:
                    st.markdown(f"**カテゴリ**: {', '.join(categories)}")
            
            if 'mechanics' in game_data:
                mechanics = [mech.get('name', '') for mech in game_data['mechanics'] 
                            if isinstance(mech, dict) and 'name' in mech]
                if mechanics:
                    st.markdown(f"**メカニクス**: {', '.join(mechanics[:5])}")
                    if len(mechanics) > 5:
                        st.markdown(f"*および他 {len(mechanics)-5} 個*")
            
            if is_main and 'description' in game_data:
                with st.expander("ゲーム説明を表示"):
                    st.markdown(game_data['description'])
        
        st.markdown("</div>", unsafe_allow_html=True)

def display_similar_game_card(
    rank: int,
    idx: int,
    selected_index: int,
    games: List[Dict[str, Any]],
    game_data_list: List[Dict[str, Any]],
    similarity_matrix: np.ndarray
) -> None:
    """
    類似ゲームのカードを表示する関数
    
    Args:
        rank (int): 類似度ランク
        idx (int): ゲームのインデックス
        selected_index (int): 選択されたゲームのインデックス
        games (List[Dict[str, Any]]): ゲーム情報のリスト
        game_data_list (List[Dict[str, Any]]): ゲームデータのリスト
        similarity_matrix (np.ndarray): 類似度行列
    """
    # app.pyでの関数の実際の使用状況に応じて、実装を復元
    # もしくは互換性のために関数の枠を維持
    similarity = similarity_matrix[selected_index][idx]
    
    # 類似度スコア表示
    st.markdown(f"<div class='similarity-score'>類似度: {similarity:.4f}</div>", unsafe_allow_html=True)
    
    # ゲームカード表示
    display_game_card(game_data_list[idx])

# 類似ゲームの取得
def get_similar_indices(
    selected_index: int,
    similarity_matrix: np.ndarray,
    top_n: int,
    similarity_threshold: float = 0.0
) -> np.ndarray:
    """類似度が高いゲームのインデックスを取得する関数
    
    Args:
        selected_index (int): 選択されたゲームのインデックス
        similarity_matrix (np.ndarray): 類似度行列
        top_n (int): 取得するゲーム数
        similarity_threshold (float, optional): 類似度閾値. デフォルトは0.0.
        
    Returns:
        np.ndarray: 類似ゲームのインデックス配列
    """
    # 自分自身を除外した類似度
    similarities = similarity_matrix[selected_index]
    mask = (similarities >= similarity_threshold) & (np.arange(len(similarities)) != selected_index)
    
    # 閾値を超えるインデックスを抽出し、類似度順にソート
    filtered_indices = np.where(mask)[0]
    if filtered_indices.size == 0:
        return np.array([])
        
    sorted_indices = filtered_indices[np.argsort(similarities[filtered_indices])[::-1]]
    
    # top_n件に制限
    return sorted_indices[:min(top_n, len(sorted_indices))]

# 類似性の理由を分析する関数
def analyze_similarity_reasons(
    game1: Dict[str, Any],
    game2: Dict[str, Any]
) -> List[str]:
    """2つのゲーム間の類似理由を分析する関数
    
    Args:
        game1 (Dict[str, Any]): 1つ目のゲームデータ
        game2 (Dict[str, Any]): 2つ目のゲームデータ
        
    Returns:
        List[str]: 類似理由のリスト
    """
    reasons = []
    
    # カテゴリの比較
    g1_categories = set(
        [cat.get('name', '') for cat in game1.get('categories', [])
         if isinstance(cat, dict) and 'name' in cat]
    )
    g2_categories = set(
        [cat.get('name', '') for cat in game2.get('categories', [])
         if isinstance(cat, dict) and 'name' in cat]
    )
    common_categories = g1_categories.intersection(g2_categories)
    if common_categories:
        reasons.append(f"共通カテゴリ: {', '.join(common_categories)}")
    
    # メカニクスの比較
    g1_mechanics = set(
        [mech.get('name', '') for mech in game1.get('mechanics', [])
         if isinstance(mech, dict) and 'name' in mech]
    )
    g2_mechanics = set(
        [mech.get('name', '') for mech in game2.get('mechanics', [])
         if isinstance(mech, dict) and 'name' in mech]
    )
    common_mechanics = g1_mechanics.intersection(g2_mechanics)
    if common_mechanics:
        reasons.append(f"共通メカニクス: {', '.join(common_mechanics)}")
    
    # 戦略的深さの比較
    if 'learning_analysis' in game1 and 'learning_analysis' in game2:
        g1_depth = game1.get('learning_analysis', {}).get('strategic_depth_description', '')
        g2_depth = game2.get('learning_analysis', {}).get('strategic_depth_description', '')
        if g1_depth and g2_depth and g1_depth == g2_depth:
            reasons.append(f"同じ戦略的深さ: {g1_depth}")
    
    # プレイヤータイプの比較
    if 'learning_analysis' in game1 and 'learning_analysis' in game2:
        g1_player_types = set(game1.get('learning_analysis', {}).get('player_types', []))
        g2_player_types = set(game2.get('learning_analysis', {}).get('player_types', []))
        common_player_types = g1_player_types.intersection(g2_player_types)
        if common_player_types:
            reasons.append(f"共通プレイヤータイプ: {', '.join(common_player_types)}")
    
    # 重さ（複雑さ）の比較
    if 'weight' in game1 and 'weight' in game2:
        try:
            g1_weight = float(game1.get('weight', 0))
            g2_weight = float(game2.get('weight', 0))
            if abs(g1_weight - g2_weight) < 0.5:  # 重さの差が0.5未満なら似ている
                reasons.append(f"似た複雑さ: {g1_weight:.2f} vs {g2_weight:.2f}")
        except (ValueError, TypeError):
            pass
    
    # 出版年の比較
    if 'year_published' in game1 and 'year_published' in game2:
        try:
            g1_year = int(game1.get('year_published', 0))
            g2_year = int(game2.get('year_published', 0))
            if abs(g1_year - g2_year) <= 5:
                reasons.append(f"近い発売年: {g1_year} vs {g2_year}")
        except (ValueError, TypeError):
            pass
    
    # 理由がない場合
    if not reasons:
        # 説明文から共通のキーワードを抽出
        g1_desc = str(game1.get('description', '')).lower()
        g2_desc = str(game2.get('description', '')).lower()
        
        # 単語分割（簡易的）
        g1_words = set(g1_desc.split())
        g2_words = set(g2_desc.split())
        common_words = g1_words.intersection(g2_words)
        
        # 一般的な単語を除外
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'as', 'of', 'from'}
        meaningful_words = [word for word in common_words if word not in stop_words and len(word) > 3]
        
        if meaningful_words:
            reasons.append(f"説明文の共通キーワード: {', '.join(meaningful_words[:5])}")
        else:
            reasons.append("テキスト内容の全体的な類似性")
    
    return reasons

# 類似性ヒートマップの生成
def generate_heatmap(
    selected_index: int,
    games: List[Dict[str, Any]],
    similarity_matrix: np.ndarray,
    top_n: int = 10
) -> Optional[io.BytesIO]:
    """類似性ヒートマップを生成する関数
    
    Args:
        selected_index (int): 選択されたゲームのインデックス
        games (List[Dict[str, Any]]): ゲーム情報のリスト
        similarity_matrix (np.ndarray): 類似度行列
        top_n (int, optional): 表示するゲーム数. デフォルトは10.
        
    Returns:
        Optional[io.BytesIO]: ヒートマップ画像のバッファ、エラー時はNone
    """
    try:
        similar_indices = np.argsort(similarity_matrix[selected_index])[::-1][1:top_n+1]
        all_indices = [selected_index] + list(similar_indices)
        
        # 類似度行列のサブセットを作成
        sub_matrix = similarity_matrix[np.ix_(all_indices, all_indices)]
        
        # ラベルの作成
        labels = [games[i].get('japanese_name', '') or games[i].get('name', '') for i in all_indices]
        
        # 長いラベルを短縮
        shortened_labels = []
        for label in labels:
            if len(label) > 15:
                shortened_labels.append(label[:12] + "...")
            else:
                shortened_labels.append(label)
        
        # 日本語表示用にフォントを再確認
        setup_japanese_fonts()
        
        # ヒートマップの作成
        plt.figure(figsize=(10, 8))
        ax = sns.heatmap(
            sub_matrix,
            annot=True,
            fmt=".2f",
            cmap="YlGnBu", 
            xticklabels=shortened_labels,
            yticklabels=shortened_labels
        )
        
        # フォントサイズの調整
        plt.setp(ax.get_xticklabels(), fontsize=9, rotation=45, ha="right", rotation_mode="anchor")
        plt.setp(ax.get_yticklabels(), fontsize=9)
        
        plt.title("ゲーム間の類似度ヒートマップ", fontsize=12)
        plt.tight_layout()
        
        # プロットをStreamlitに表示するための変換
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150)
        plt.close()
        buf.seek(0)
        
        return buf
    except Exception as e:
        logger.error(f"ヒートマップ生成エラー: {e}")
        return None

# 類似ゲームの分布データを分析する関数
def analyze_distribution_data(
    selected_index: int,
    games: List[Dict[str, Any]],
    game_data_list: List[Dict[str, Any]],
    similarity_matrix: np.ndarray,
    top_n: int = 20
) -> Tuple[pd.DataFrame, Counter, Counter]:
    """類似ゲームの分布データを分析する関数
    
    Args:
        selected_index (int): 選択されたゲームのインデックス
        games (List[Dict[str, Any]]): ゲーム情報のリスト
        game_data_list (List[Dict[str, Any]]): ゲームデータのリスト
        similarity_matrix (np.ndarray): 類似度行列
        top_n (int, optional): 分析するゲーム数. デフォルトは20.
        
    Returns:
        Tuple[pd.DataFrame, Counter, Counter]: 類似度データフレーム、カテゴリ分布、メカニクス分布
    """
    # 類似度の高いゲームを取得
    similarities = similarity_matrix[selected_index]
    indices = np.argsort(similarities)[::-1][1:top_n+1]
    
    # DataFrameの作成
    display_names = [games[i].get('japanese_name', '') or games[i].get('name', '') for i in indices]
    df = pd.DataFrame({
        'ゲーム名': display_names,
        '類似度': [similarities[i] for i in indices]
    })
    
    # カテゴリとメカニクスの分布を分析
    all_categories = []
    all_mechanics = []
    
    for i in indices[:10]:  # 上位10ゲームのみ
        game = game_data_list[i]
        
        # カテゴリの収集
        if 'categories' in game:
            cats = [cat.get('name', '') for cat in game['categories'] 
                   if isinstance(cat, dict) and 'name' in cat]
            all_categories.extend(cats)
        
        # メカニクスの収集
        if 'mechanics' in game:
            mechs = [mech.get('name', '') for mech in game['mechanics'] 
                    if isinstance(mech, dict) and 'name' in mech]
            all_mechanics.extend(mechs)
    
    # カウント
    category_counts = Counter(all_categories)
    mechanics_counts = Counter(all_mechanics)
    
    return df, category_counts, mechanics_counts

# カテゴリ分布の円グラフを描画
def plot_category_pie_chart(category_counts: Counter) -> Optional[plt.Figure]:
    """カテゴリ分布の円グラフを描画する関数
    
    Args:
        category_counts (Counter): カテゴリのカウント
        
    Returns:
        Optional[plt.Figure]: 描画した図、データがない場合はNone
    """
    if not category_counts:
        return None
    
    # 日本語表示用にフォントを再確認
    setup_japanese_fonts()
    
    # トップ8カテゴリを抽出（グラフを見やすくするため）
    top_categories = dict(category_counts.most_common(8))
    others_count = sum(count for cat, count in category_counts.items() if cat not in top_categories)
    if others_count > 0:
        top_categories['その他'] = others_count
    
    # 円グラフ
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        top_categories.values(), 
        labels=list(top_categories.keys()), 
        autopct='%1.1f%%',
        textprops={'fontsize': 9}
    )
    
    # ラベルのフォントサイズを調整
    plt.setp(autotexts, size=8)
    plt.setp(texts, size=9)
    
    ax.axis('equal')
    plt.title('類似ゲームのカテゴリ分布', fontsize=12)
    
    return fig

# メカニクス分布の棒グラフを描画
def plot_mechanics_bar_chart(mechanics_counts: Counter) -> Optional[plt.Figure]:
    """メカニクス分布の棒グラフを描画する関数
    
    Args:
        mechanics_counts (Counter): メカニクスのカウント
        
    Returns:
        Optional[plt.Figure]: 描画した図、データがない場合はNone
    """
    if not mechanics_counts:
        return None
    
    # 日本語表示用にフォントを再確認
    setup_japanese_fonts()
    
    # 上位10個のみ表示
    top_mechanics = dict(mechanics_counts.most_common(10))
    
    # 長いメカニクス名を短縮
    shortened_mechs = {}
    for mech, count in top_mechanics.items():
        if len(mech) > 25:
            shortened_mechs[mech[:22] + "..."] = count
        else:
            shortened_mechs[mech] = count
    
    # 横棒グラフ
    fig, ax = plt.subplots(figsize=(8, 8))
    bars = ax.barh(list(shortened_mechs.keys()), list(shortened_mechs.values()), color='lightgreen')
    ax.set_xlabel('出現回数', fontsize=12)
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    # 値を表示
    for i, bar in enumerate(bars):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                str(list(shortened_mechs.values())[i]), 
                va='center')
    
    plt.title('類似ゲームのメカニクス分布', fontsize=12)
    plt.tight_layout()
    
    return fig

# 類似ゲームの棒グラフを描画
def plot_similar_games_bar_chart(df: pd.DataFrame) -> plt.Figure:
    """類似ゲームの棒グラフを描画する関数
    
    Args:
        df (pd.DataFrame): 類似ゲームのデータフレーム
        
    Returns:
        plt.Figure: 描画した図
    """
    # 日本語表示用にフォントを再確認
    setup_japanese_fonts()
    
    # 長いゲーム名を短縮
    shortened_names = []
    for name in df['ゲーム名']:
        if len(name) > 20:
            shortened_names.append(name[:17] + "...")
        else:
            shortened_names.append(name)
    
    df_plot = df.copy()
    df_plot['短縮名'] = shortened_names
    
    # プロットの作成
    fig, ax = plt.subplots(figsize=(10, 8))
    bars = ax.barh(df_plot['短縮名'], df['類似度'], color='skyblue')
    ax.set_xlabel('類似度', fontsize=12)
    ax.set_xlim(0, 1)
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    # 値を表示
    for i, bar in enumerate(bars):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2, 
                f'{df.iloc[i]["類似度"]:.2f}', 
                va='center')
    
    plt.tight_layout()
    
    return fig