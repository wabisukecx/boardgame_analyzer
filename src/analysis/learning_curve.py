"""
BoardGameGeekのゲームデータからラーニングカーブを分析するモジュール
カテゴリとランキング情報を活用した分析
"""

import datetime

# メカニクスの複雑さデータを取得する関数をインポート
from src.analysis.mechanic_complexity import get_complexity
# カテゴリの複雑さデータを取得する関数をインポート
from src.analysis.category_complexity import calculate_category_complexity
# ランキングに基づく評価を取得する関数をインポート
from src.analysis.rank_complexity import calculate_rank_complexity
# 戦略深度計算の改善版をインポート
from src.analysis.strategic_depth import (
    calculate_strategic_depth_improved,
    update_learning_curve_with_improved_strategic_depth,
    estimate_decision_points_improved as estimate_decision_points,
    estimate_interaction_complexity_improved as estimate_interaction_complexity,
    calculate_rules_complexity
)

def get_rank_value(game_data, rank_type="boardgame"):
    """
    指定されたランク種別の順位を取得する
    
    Parameters:
    game_data (dict): ゲームの詳細情報
    rank_type (str): ランク種別（デフォルトは総合ランキング "boardgame"）
    
    Returns:
    int or None: ランク順位（見つからない場合はNone）
    """
    if 'ranks' not in game_data:
        return None
        
    for rank_info in game_data['ranks']:
        if rank_info.get('type') == rank_type:
            try:
                return int(rank_info.get('rank'))
            except (ValueError, TypeError):
                return None
    
    return None


def calculate_popularity_factor(rank):
    """
    ランキングに基づく人気係数を計算する
    
    Parameters:
    rank (int or None): BGGのランキング順位
    
    Returns:
    float: 人気係数（1.0〜1.3の範囲）
    """
    if rank is None:
        return 1.0
        
    if rank <= 100:
        return 1.3  # トップ100は評価を30%増加
    elif rank <= 500:
        return 1.2  # トップ500は評価を20%増加
    elif rank <= 1000:
        return 1.1  # トップ1000は評価を10%増加
    else:
        return 1.0  # その他はそのまま


def get_year_published(game_data):
    """
    ゲームの発行年を取得する
    
    Parameters:
    game_data (dict): ゲームの詳細情報
    
    Returns:
    int or None: 発行年（見つからない場合はNone）
    """
    if 'year_published' not in game_data:
        return None
        
    try:
        return int(game_data['year_published'])
    except (ValueError, TypeError):
        return None


def calculate_longevity_factor(year_published):
    """
    ゲームの発行年に基づく長寿命係数を計算する
    発行から長い期間が経過しているゲームは、長期間人気を保っている証拠であり、
    より高いリプレイ性を持つと考えられる
    
    Parameters:
    year_published (int or None): ゲームの発行年
    
    Returns:
    float: 長寿命係数（1.0〜1.25の範囲）
    """
    if year_published is None:
        return 1.0
        
    current_year = datetime.datetime.now().year
    years_since_publication = current_year - year_published
    
    if years_since_publication >= 20:
        return 1.25  # 20年以上は25%増加（クラシックゲーム）
    elif years_since_publication >= 10:
        return 1.2   # 10年以上は20%増加（長期的な人気）
    elif years_since_publication >= 5:
        return 1.1   # 5年以上は10%増加（定着したゲーム）
    else:
        return 1.0   # 新しいゲームはそのまま


def calculate_replayability(game_data):
    """
    ゲームのリプレイ性を計算する
    
    Parameters:
    game_data (dict): ゲームの詳細情報
    
    Returns:
    float: リプレイ性スコア（1.0〜5.0の範囲）
    """
    # 基本スコア
    base_score = 2.0
    
    # 要素の多様性によるスコア加算
    diversity_score = 0.0
    
    # メカニクスの多様性（最大0.7ポイント）
    mechanics_count = len(game_data.get('mechanics', []))
    diversity_score += min(0.7, mechanics_count * 0.1)
    
    # リプレイ性を高めるメカニクスをより詳細に評価
    high_replay_mechanics = [
        'Variable Set-up', 
        'Modular Board', 
        'Variable Player Powers',
        'Deck Building',
        'Legacy Game',
        'Campaign / Battle Card Driven',
        'Scenario / Mission / Campaign Game',
        'Deck Construction',
        'Engine Building'
    ]
    
    medium_replay_mechanics = [
        'Dice Rolling',
        'Card Drafting',
        'Worker Placement',
        'Tech Trees / Tech Tracks',
        'Multi-Use Cards',
        'Push Your Luck',
        'Area Control',
        'Route/Network Building'
    ]
    
    # リプレイ性の高いメカニクスの数をカウント
    high_replay_count = sum(
        1 for m in game_data.get('mechanics', [])
        if m.get('name') in high_replay_mechanics
    )
    
    medium_replay_count = sum(
        1 for m in game_data.get('mechanics', [])
        if m.get('name') in medium_replay_mechanics
    )
    
    # リプレイ性が高いメカニクスの評価（最大0.8ポイント）
    replay_mechanics_score = min(
        0.8, (high_replay_count * 0.2) + (medium_replay_count * 0.1)
    )
    diversity_score += replay_mechanics_score
    
    # カテゴリの多様性（最大0.4ポイント）
    categories_count = len(game_data.get('categories', []))
    diversity_score += min(0.4, categories_count * 0.1)
    
    # 人気ランキングからの補正
    rank = get_rank_value(game_data)
    rank_bonus = 0.0
    
    if rank is not None:
        if rank <= 100:
            rank_bonus = 0.6  # トップ100は+0.6ポイント
        elif rank <= 500:
            rank_bonus = 0.4  # トップ500は+0.4ポイント
        elif rank <= 1000:
            rank_bonus = 0.2  # トップ1000は+0.2ポイント
    
    # 長期的な人気による補正
    year_published = get_year_published(game_data)
    longevity_factor = calculate_longevity_factor(year_published)
    
    # 最終スコア計算
    # 多様性スコアと人気ボーナスを足したものに、長寿命係数を掛ける
    replayability = (base_score + diversity_score + rank_bonus) * longevity_factor
    
    # 上限と下限の設定
    replayability = max(1.0, min(5.0, replayability))
    
    return round(replayability, 2)


def calculate_learning_curve(game_data):
    """
    ゲームデータからラーニングカーブ情報を計算する
    カテゴリとランキング情報を活用した改善版
    
    Parameters:
    game_data (dict): ゲームの詳細情報
    
    Returns:
    dict: ラーニングカーブの情報
    """
    # 基本的な複雑さ（すでにAPIから取得）
    base_weight = float(game_data.get('weight', 3.0))
    
    # ゲームのメカニクスから複雑さを推定
    mechanics_names = [m['name'] for m in game_data.get('mechanics', [])]
    mechanics_complexity = 0
    mechanic_count = 0
    
    for mechanic in mechanics_names:
        # get_complexity関数で取得した値
        mechanic_complexity = get_complexity(mechanic)
        mechanics_complexity += mechanic_complexity
        mechanic_count += 1
    
    # メカニクスの平均複雑さ（メカニクスがない場合はデフォルト値）
    avg_mechanic_complexity = (
        mechanics_complexity / max(1, mechanic_count) if mechanic_count > 0 else 3.0
    )
    
    # 【変更点】推奨年齢からの複雑さ推定を、カテゴリとランキングによる評価に置き換え
    # カテゴリに基づく複雑さを計算
    category_complexity = calculate_category_complexity(game_data.get('categories', []))
    
    # ランキングに基づく複雑さを計算
    rank_complexity = calculate_rank_complexity(game_data.get('ranks', []))
    
    # カテゴリとランキングによる複雑さ評価（60:40の重み付け）
    complexity_factor = (category_complexity * 0.6 + rank_complexity * 0.4)
        
    # 初期障壁（ルールの複雑さ）の計算を更新
    initial_barrier = (
        avg_mechanic_complexity * 0.5 + 
        base_weight * 0.2 +
        complexity_factor * 0.2  # 推奨年齢の代わりにカテゴリとランキングによる評価
    )
    
    # メカニクス数による初期障壁の調整（多くのメカニクスがあるほど初期学習が難しくなる）
    mechanics_count_barrier_factor = min(1.25, max(1.0, len(mechanics_names) / 5))
    initial_barrier = initial_barrier * mechanics_count_barrier_factor
    
    # 上限を5.0に設定
    initial_barrier = min(5.0, initial_barrier)
    initial_barrier = round(initial_barrier, 2)
    
    # 戦略的深さ（改善版）
    strategic_depth = calculate_strategic_depth_improved(game_data)
    
    # リプレイ性を計算（改善版）
    replayability = calculate_replayability(game_data)
    
    # ランク情報を取得
    rank = get_rank_value(game_data)
    
    # 発行年を取得
    year_published = get_year_published(game_data)
    
    # 基本的な学習曲線情報を構築
    learning_curve = {
        "initial_barrier": initial_barrier,  # 初期学習の難しさ
        "strategic_depth": strategic_depth,  # 戦略の深さ
        "replayability": replayability,  # リプレイ性
        "mechanics_complexity": round(avg_mechanic_complexity, 2),  # メカニクスの複雑さ
        "mechanics_count": len(mechanics_names),  # メカニクスの数
        "bgg_weight": base_weight,  # BGGの複雑さ評価（元の値）
        "bgg_rank": rank,  # BGGのランキング
        "year_published": year_published,  # 発行年
        # 新しく追加した指標
        "category_complexity": round(category_complexity, 2),  # カテゴリに基づく複雑さ
        "rank_complexity": round(rank_complexity, 2)  # ランキングに基づく複雑さ
    }
    
    # 改善版の指標で学習曲線データを拡張
    learning_curve = update_learning_curve_with_improved_strategic_depth(
        game_data, learning_curve)
    
    # 各種分析の詳細情報を追加
    learning_curve["decision_points"] = estimate_decision_points(game_data.get('mechanics', []))
    learning_curve["interaction_complexity"] = estimate_interaction_complexity(game_data.get('categories', []))
    learning_curve["rules_complexity"] = calculate_rules_complexity(game_data)
    
    # マスター時間の推定
    if strategic_depth > 4.3:
        if len(mechanics_names) >= 6:
            learning_curve["mastery_time"] = "medium_to_long"  # メカニクスが多いが、一度基本を理解すれば応用が利く
        else:
            learning_curve["mastery_time"] = "long"  # マスターに長時間かかる
    elif strategic_depth > 3.2:
        learning_curve["mastery_time"] = "medium"  # マスターに中程度の時間がかかる
    else:
        learning_curve["mastery_time"] = "short"  # 比較的短時間でマスター可能
    
    return learning_curve

def get_curve_type_display(curve_type):
    """
    学習曲線タイプの表示名を取得する
    
    Parameters:
    curve_type (str): 学習曲線タイプ
    
    Returns:
    str: 表示用の学習曲線タイプ
    """
    curve_type_ja = {
        # 基本タイプ
        "steep": "急な学習曲線",
        "moderate": "中程度の学習曲線",
        "gentle": "緩やかな学習曲線",
        
        # 旧バージョンの拡張タイプ
        "steep_then_flat": "初期は急だが習得後は上達しやすい学習曲線",
        "moderate_then_flat": "中程度で習得後は上達しやすい学習曲線",
        
        # 新バージョンの拡張タイプ
        "steep_then_moderate": "初期は急だが中程度の複雑さの学習曲線",
        "steep_then_shallow": "初期は急だが戦略は浅い学習曲線",
        "moderate_then_deep": "中程度の障壁で深い戦略性を持つ学習曲線",
        "moderate_then_shallow": "中程度の障壁で浅い戦略性の学習曲線",
        "gentle_then_deep": "習得は簡単だが深い戦略性を持つ学習曲線",
        "gentle_then_moderate": "習得は簡単で中程度の戦略性を持つ学習曲線"
    }
    return curve_type_ja.get(curve_type, '不明')

def get_player_type_display(player_type):
    """
    プレイヤータイプの表示名を取得する
    
    Parameters:
    player_type (str): プレイヤータイプ
    
    Returns:
    str: 表示用のプレイヤータイプ
    """
    player_types_ja = {
        "beginner": "初心者",
        "casual": "カジュアルプレイヤー",
        "experienced": "熟練プレイヤー",
        "hardcore": "ハードコアゲーマー",
        "system_master": "システムマスター（複雑なゲームシステムを好む）",
        "strategist": "戦略家（戦略的深さのあるゲームを好む）",
        "replayer": "リプレイヤー（遊び込めるゲームを好む）",
        "trend_follower": "トレンドフォロワー（人気ゲームを好む）",
        "classic_lover": "クラシック愛好家（長年遊ばれている定番ゲームを好む）"
    }
    return player_types_ja.get(player_type, player_type)

def get_mastery_time_display(mastery_time):
    """
    マスター時間の表示名を取得する
    
    Parameters:
    mastery_time (str): マスター時間
    
    Returns:
    str: 表示用のマスター時間
    """
    mastery_time_ja = {
        "short": "短い",
        "medium": "中程度",
        "long": "長い",
        "medium_to_long": "中〜長い（基本習得後は上達しやすい）"
    }
    return mastery_time_ja.get(mastery_time, '不明')


def get_replayability_display(replayability):
    """
    リプレイ性の表示名を取得する
    
    Parameters:
    replayability (float): リプレイ性スコア
    
    Returns:
    str: 表示用のリプレイ性評価
    """
    if replayability >= 4.5:
        return "非常に高い（何度でも遊べる定番ゲーム）"
    elif replayability >= 4.0:
        return "高い（長期間遊べる）"
    elif replayability >= 3.5:
        return "やや高い（何度か遊ぶ価値がある）"
    elif replayability >= 3.0:
        return "中程度（数回は楽しめる）"
    elif replayability >= 2.0:
        return "低め（数回プレイすれば十分）"
    else:
        return "低い（1〜2回プレイすれば十分）"