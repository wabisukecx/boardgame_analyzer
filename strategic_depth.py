"""
改善された戦略深度計算モジュール
"""

from mechanic_complexity import get_complexity

# 戦略的意思決定ポイントが高いメカニクス
HIGH_DECISION_MECHANICS = [
    'Worker Placement',
    'Engine Building',
    'Deck Building',
    'Area Control',
    'Tech Trees / Tech Tracks',
    'Variable Player Powers',
    'Action Points',
    'Hand Management',
    'Card Drafting',
    'Resource Management',
    'Action Selection'
]

# 中程度の意思決定ポイントを持つメカニクス
MEDIUM_DECISION_MECHANICS = [
    'Set Collection',
    'Tile Placement',
    'Route/Network Building',
    'Auction / Bidding',
    'Grid Movement',
    'Push Your Luck',
    'Market',
    'Take That'
]

# 低い意思決定ポイントを持つメカニクス
LOW_DECISION_MECHANICS = [
    'Roll / Spin and Move',
    'Dice Rolling',
    'Memory',
    'Pattern Recognition',
    'Race',
    'Player Elimination'
]

# プレイヤー相互作用の高いカテゴリ
HIGH_INTERACTION_CATEGORIES = [
    'Negotiation Game',
    'Bluffing',
    'Player Versus Player',
    'Trading',
    'Wargame',
    'Fighting',
    'Political'
]

# 中程度の相互作用を持つカテゴリ
MEDIUM_INTERACTION_CATEGORIES = [
    'Area Control / Area Influence',
    'Territory Building',
    'Economic',
    'Auction/Bidding',
    'City Building'
]

# 低い相互作用のカテゴリ（並行プレイなど）
LOW_INTERACTION_CATEGORIES = [
    'Puzzle',
    'Abstract Strategy',
    'Solo / Solitaire Game',
    'Educational',
    'Party Game'
]

def estimate_decision_points(mechanics):
    """
    メカニクスに基づく意思決定ポイントを推定する
    
    Parameters:
    mechanics (list): メカニクスのリスト（辞書のリスト）
    
    Returns:
    float: 推定された意思決定ポイント（1.0〜5.0の範囲）
    """
    if not mechanics:
        return 2.5  # デフォルト値
    
    mechanics_names = [m['name'] for m in mechanics]
    
    # 各カテゴリのメカニクス数をカウント
    high_count = sum(1 for m in mechanics_names if m in HIGH_DECISION_MECHANICS)
    medium_count = sum(1 for m in mechanics_names if m in MEDIUM_DECISION_MECHANICS)
    low_count = sum(1 for m in mechanics_names if m in LOW_DECISION_MECHANICS)
    
    # 残りのメカニクスは中程度とみなす
    other_count = len(mechanics) - high_count - medium_count - low_count
    
    # 加重平均を計算（高:4.5, 中:3.0, 低:1.5, その他:2.5）
    total_points = (high_count * 4.5) + (medium_count * 3.0) + (low_count * 1.5) + (other_count * 2.5)
    
    # メカニクスの多様性に基づくボーナス（多くのメカニクスを組み合わせると意思決定が複雑になる）
    if len(mechanics) >= 8:
        diversity_bonus = 0.5
    elif len(mechanics) >= 5:
        diversity_bonus = 0.3
    elif len(mechanics) >= 3:
        diversity_bonus = 0.2
    else:
        diversity_bonus = 0.0
    
    # 意思決定ポイントの計算
    decision_points = (total_points / len(mechanics)) + diversity_bonus
    
    # 1.0〜5.0の範囲に制限
    return min(5.0, max(1.0, decision_points))

def estimate_interaction_complexity(categories):
    """
    カテゴリに基づくプレイヤー間相互作用の複雑性を推定する
    
    Parameters:
    categories (list): カテゴリのリスト（辞書のリスト）
    
    Returns:
    float: 推定された相互作用複雑性（1.0〜5.0の範囲）
    """
    if not categories:
        return 2.5  # デフォルト値
    
    category_names = [c['name'] for c in categories]
    
    # 各相互作用レベルのカテゴリ数をカウント
    high_count = sum(1 for c in category_names if c in HIGH_INTERACTION_CATEGORIES)
    medium_count = sum(1 for c in category_names if c in MEDIUM_INTERACTION_CATEGORIES)
    low_count = sum(1 for c in category_names if c in LOW_INTERACTION_CATEGORIES)
    
    # 残りのカテゴリは中程度の相互作用とみなす
    other_count = len(categories) - high_count - medium_count - low_count
    
    # 加重平均を計算（高:4.5, 中:3.0, 低:1.5, その他:2.5）
    total_points = (high_count * 4.5) + (medium_count * 3.0) + (low_count * 1.5) + (other_count * 2.5)
    
    # 相互作用複雑性の計算
    interaction_complexity = total_points / max(1, len(categories))
    
    # 1.0〜5.0の範囲に制限
    return min(5.0, max(1.0, interaction_complexity))

def calculate_rules_complexity(game_data):
    """
    ルールの複雑さを計算する
    
    Parameters:
    game_data (dict): ゲームの詳細情報
    
    Returns:
    float: ルールの複雑さスコア（1.0〜5.0の範囲）
    """
    # メカニクスの複雑さ計算
    mechanics = game_data.get('mechanics', [])
    mechanics_complexity_sum = sum(get_complexity(m['name']) for m in mechanics)
    avg_mechanic_complexity = mechanics_complexity_sum / max(1, len(mechanics))
    
    # メカニクスの数による補正
    mechanics_count_factor = min(1.5, 1.0 + (len(mechanics) / 10))
    
    # 推奨年齢からの複雑さ推定
    min_age = float(game_data.get('publisher_min_age', 10))
    age_complexity = min(4.0, (min_age - 6) / 3)  # 6歳=0, 12歳=2.0, 18歳=4.0
    
    # BGGの重み付け
    base_weight = float(game_data.get('weight', 3.0))
    
    # ルールの複雑さ計算（メカニクス:60%, 年齢:20%, BGG:20%）
    rules_complexity = (
        (avg_mechanic_complexity * mechanics_count_factor) * 0.6 +
        age_complexity * 0.2 +
        base_weight * 0.2
    )
    
    # 1.0〜5.0の範囲に制限
    return min(5.0, max(1.0, rules_complexity))

def calculate_strategic_depth_improved(game_data):
    """
    改善された戦略深度計算関数
    
    Parameters:
    game_data (dict): ゲームの詳細情報
    
    Returns:
    float: 戦略的深さのスコア（1.0〜5.0の範囲）
    """
    # BGG重み付けの影響を50%に削減
    base_weight = float(game_data.get('weight', 3.0))
    
    # 意思決定ポイントの推定
    decision_points = estimate_decision_points(game_data.get('mechanics', []))
    
    # プレイヤー相互作用の複雑性を推定
    interaction_complexity = estimate_interaction_complexity(game_data.get('categories', []))
    
    # ルールの複雑さを計算
    rules_complexity = calculate_rules_complexity(game_data)
    
    # 戦略的深さの計算（BGGの影響を30%に削減）
    strategic_depth = (
        base_weight * 0.3 +                    # BGG評価（30%）
        decision_points * 0.3 +                # 意思決定ポイント（30%）
        rules_complexity * 0.2 +               # ルールの複雑さ（20%）
        interaction_complexity * 0.2           # 相互作用複雑性（20%）
    )
    
    # 継続的な戦略性評価（長期的な戦略の存在を評価）
    has_long_term_strategy = any(m['name'] in [
        'Engine Building', 'Tech Trees / Tech Tracks', 'Legacy Game', 
        'Campaign / Battle Card Driven', 'Deck Building'
    ] for m in game_data.get('mechanics', []))
    
    if has_long_term_strategy:
        strategic_depth += 0.3  # 長期的な戦略性へのボーナス
    
    # 最終的な戦略的深さの計算
    strategic_depth = min(5.0, strategic_depth)
    
    return round(strategic_depth, 2)

def get_strategic_depth_description(strategic_depth):
    """
    戦略的深さの説明を取得する
    
    Parameters:
    strategic_depth (float): 戦略的深さの値
    
    Returns:
    str: 戦略的深さの説明文
    """
    if strategic_depth >= 4.5:
        return "非常に深い（マスターに長い時間を要する）"
    elif strategic_depth >= 4.0:
        return "深い（熟練プレイヤー向け）"
    elif strategic_depth >= 3.5:
        return "中〜高（多くの戦略が存在）"
    elif strategic_depth >= 3.0:
        return "中程度（いくつかの戦略オプションあり）"
    elif strategic_depth >= 2.5:
        return "中〜低（基本的な戦略が存在）"
    elif strategic_depth >= 2.0:
        return "低め（限られた戦略オプション）"
    else:
        return "低い（戦略的要素が少ない）"

# 元のcalculate_learning_curve関数の戦略深度計算部分を置き換えるための関数
def update_learning_curve_with_improved_strategic_depth(game_data, learning_curve):
    """
    既存の学習曲線データを改善された戦略深度で更新する
    
    Parameters:
    game_data (dict): ゲームの詳細情報
    learning_curve (dict): 既存の学習曲線データ
    
    Returns:
    dict: 更新された学習曲線データ
    """
    # 改善された戦略深度を計算
    strategic_depth = calculate_strategic_depth_improved(game_data)
    
    # 学習曲線データを更新
    learning_curve["strategic_depth"] = strategic_depth
    learning_curve["strategic_depth_description"] = get_strategic_depth_description(strategic_depth)
    
    # 学習曲線タイプの更新（初期障壁と戦略深度の新しい組み合わせに基づく）
    initial_barrier = learning_curve["initial_barrier"]
    
    if initial_barrier > 4.3:
        if strategic_depth > 4.3:
            learning_curve["learning_curve_type"] = "steep"  # 急で深い
        elif strategic_depth > 3.5:
            learning_curve["learning_curve_type"] = "steep_then_moderate"  # 急だが中程度の深さ
        else:
            learning_curve["learning_curve_type"] = "steep_then_shallow"  # 急だが浅い
    elif initial_barrier > 3.5:
        if strategic_depth > 4.3:
            learning_curve["learning_curve_type"] = "moderate_then_deep"  # 中程度から深い
        elif strategic_depth > 3.5:
            learning_curve["learning_curve_type"] = "moderate"  # 中程度から中程度
        else:
            learning_curve["learning_curve_type"] = "moderate_then_shallow"  # 中程度から浅い
    else:
        if strategic_depth > 4.3:
            learning_curve["learning_curve_type"] = "gentle_then_deep"  # 緩やかから深い
        elif strategic_depth > 3.5:
            learning_curve["learning_curve_type"] = "gentle_then_moderate"  # 緩やかから中程度
        else:
            learning_curve["learning_curve_type"] = "gentle"  # 緩やかから浅い
    
    # プレイヤータイプの更新（より緩やかな条件に変更）
    player_types = []
    
    # 初心者向け
    if initial_barrier < 3.0 and strategic_depth < 3.5:
        player_types.append("beginner")
    
    # カジュアルプレイヤー向け
    if initial_barrier < 4.0 and strategic_depth < 4.5:
        player_types.append("casual")
    
    # 熟練プレイヤー向け
    if strategic_depth >= 3.0:
        player_types.append("experienced")
    
    # ハードコアゲーマー向け
    if initial_barrier > 3.0 and strategic_depth > 3.5:
        player_types.append("hardcore")
    
    # 戦略家向け
    if strategic_depth > 3.8:
        player_types.append("strategist")
    
    # システムマスター向け（mechanics_masterからsystem_masterに名称変更）
    if len(game_data.get('mechanics', [])) >= 5 and strategic_depth > 3.5:
        player_types.append("system_master")
    
    # リプレイヤー（リプレイ性の高いゲームを好む人）
    if learning_curve.get('replayability', 0) >= 3.8:
        player_types.append("replayer")
    
    # トレンドフォロワー（人気のゲームを好む人）
    if learning_curve.get('bgg_rank') is not None and learning_curve.get('bgg_rank') <= 1000:
        player_types.append("trend_follower")
    
    # クラシック愛好家（長年遊ばれている定番ゲームを好む人）
    year_published = learning_curve.get('year_published')
    if year_published is not None and isinstance(year_published, int) and year_published <= 2000:
        player_types.append("classic_lover")
        
    # 条件にマッチするものがない場合、初期障壁と戦略深度に基づいて基本的なプレイヤータイプを割り当て
    if not player_types:
        if strategic_depth >= 3.5:
            player_types.append("experienced")
        elif initial_barrier >= 3.5:
            player_types.append("hardcore")
        else:
            player_types.append("casual")
    
    # 学習曲線分析に追加の指標を含める
    learning_curve["decision_points"] = estimate_decision_points(game_data.get('mechanics', []))
    learning_curve["interaction_complexity"] = estimate_interaction_complexity(game_data.get('categories', []))
    learning_curve["rules_complexity"] = calculate_rules_complexity(game_data)
    learning_curve["player_types"] = player_types
    
    return learning_curve