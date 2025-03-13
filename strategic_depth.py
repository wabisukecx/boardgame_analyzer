"""
改善された戦略深度計算モジュール
"""

import math
from mechanic_complexity import get_complexity

# メカニクスの戦略的重要性の分類（1〜5のスケール）
MECHANICS_STRATEGIC_VALUE = {
    # 非常に高い戦略価値（5）
    'Engine Building': 5,
    'Worker Placement': 5,
    'Tech Trees / Tech Tracks': 5,
    'Deck Building': 5,
    'Area Control / Area Influence': 5,
    
    # 高い戦略価値（4）
    'Multi-Use Cards': 4,
    'Resource Management': 4,
    'Variable Player Powers': 4,
    'Action Points': 4,
    'Auction / Bidding': 4,
    'Worker Placement, Different Worker Types': 4,
    'Action Selection': 4,
    'Roles with Asymmetric Information': 4,
    
    # 中〜高の戦略価値（3.5）
    'Card Drafting': 3.5,
    'Route/Network Building': 3.5,
    'Tile Placement': 3.5,
    'Hand Management': 3.5,
    'Simulation': 3.5,
    'Stock Holding': 3.5,
    
    # 中程度の戦略価値（3）
    'Set Collection': 3,
    'Force Commitment': 3,
    'Market': 3,
    'Contracts': 3,
    'Network and Route Building': 3,
    'Pattern Building': 3,
    'Modular Board': 3,
    'End Game Bonuses': 3,
    
    # 中〜低の戦略価値（2.5）
    'Push Your Luck': 2.5,
    'Grid Movement': 2.5,
    'Trading': 2.5,
    'Voting': 2.5,
    'Variable Phase Order': 2.5,
    'Pattern Movement': 2.5,
    
    # 低い戦略価値（2）
    'Take That': 2,
    'Memory': 2,
    'Dice Rolling': 2,
    'Pattern Recognition': 2,
    'Roll / Spin and Move': 2,
    'Re-rolling and Locking': 2,
    'Storytelling': 2,
    
    # 非常に低い戦略価値（1）
    'Player Elimination': 1,
    'Lose a Turn': 1,
    'Bingo': 1
}

# メカニクスのプレイヤー間相互作用の分類（1〜5のスケール）
MECHANICS_INTERACTION_VALUE = {
    # 非常に高い相互作用（5）
    'Negotiation': 5,
    'Trading': 5,
    'Auction / Bidding': 5,
    'Betting and Bluffing': 5,
    'Take That': 5,
    
    # 高い相互作用（4）
    'Area Control / Area Influence': 4,
    'Roles with Asymmetric Information': 4,
    'Card Play Conflict Resolution': 4,
    'Stock Holding': 4,
    'Communication Limits': 4,
    'Player Elimination': 4,
    
    # 中〜高の相互作用（3.5）
    'Worker Placement': 3.5,
    'Voting': 3.5,
    'Variable Player Powers': 3.5,
    'Action Retrieval': 3.5,
    'Advantage Token': 3.5,
    
    # 中程度の相互作用（3）
    'Card Drafting': 3,
    'Route/Network Building': 3,
    'Market': 3,
    'Selection Order Bid': 3,
    'End Game Bonuses': 3,
    'Catch the Leader': 3,
    
    # 中〜低の相互作用（2.5）
    'Multi-Use Cards': 2.5,
    'Resource Management': 2.5,
    'Tile Placement': 2.5,
    'Hand Management': 2.5,
    'Set Collection': 2.5,
    
    # 低い相互作用（2）
    'Engine Building': 2,
    'Tech Trees / Tech Tracks': 2,
    'Deck Building': 2,
    'Push Your Luck': 2,
    'Pattern Building': 2,
    
    # 非常に低い相互作用（1）
    'Solo / Solitaire Game': 1,
    'Paper-and-Pencil': 1
}

# カテゴリの戦略的重要性の分類（1〜5のスケール）
CATEGORIES_STRATEGIC_VALUE = {
    # 非常に高い戦略価値（5）
    'Strategy': 5,
    'Civilization': 5,
    'Economic': 5,
    'Wargame': 5,
    'Political': 5,
    
    # 高い戦略価値（4）
    'City Building': 4,
    'Territory Building': 4,
    'Science Fiction': 4,
    'Industry / Manufacturing': 4,
    'Medieval': 4,
    'Renaissance': 4,
    
    # 中〜高の戦略価値（3.5）
    'Exploration': 3.5,
    'Farming': 3.5,
    'Fantasy': 3.5,
    'Abstract Strategy': 3.5,
    'Space Exploration': 3.5,
    'Trains': 3.5,
    
    # 中程度の戦略価値（3）
    'Adventure': 3,
    'Fighting': 3,
    'Nautical': 3,
    'Prehistoric': 3,
    'Transportation': 3,
    'Puzzle': 3,
    
    # 中〜低の戦略価値（2.5）
    'Sports': 2.5,
    'Movies / TV / Radio theme': 2.5,
    'Card Game': 2.5,
    'Travel': 2.5,
    'Racing': 2.5,
    
    # 低い戦略価値（2）
    'Word Game': 2,
    'Party Game': 2,
    'Educational': 2,
    'Humor': 2,
    'Dice': 2,
    
    # 非常に低い戦略価値（1）
    'Children\'s Game': 1
}

# カテゴリのプレイヤー間相互作用の分類（1〜5のスケール）
CATEGORIES_INTERACTION_VALUE = {
    # 非常に高い相互作用（5）
    'Negotiation': 5,
    'Political': 5,
    'Bluffing': 5,
    'Trading': 5,
    'Fighting': 5,
    
    # 高い相互作用（4）
    'Wargame': 4,
    'Party Game': 4,
    'Sports': 4,
    'Civilization': 4,
    'Economic': 4,
    
    # 中〜高の相互作用（3.5）
    'Area Control / Area Influence': 3.5,
    'Territory Building': 3.5,
    'City Building': 3.5,
    'Adventure': 3.5,
    
    # 中程度の相互作用（3）
    'Racing': 3,
    'Fantasy': 3,
    'Science Fiction': 3,
    'Medieval': 3,
    'Card Game': 3,
    
    # 中〜低の相互作用（2.5）
    'Trains': 2.5,
    'Transportation': 2.5,
    'Industry / Manufacturing': 2.5,
    'Word Game': 2.5,
    
    # 低い相互作用（2）
    'Puzzle': 2,
    'Abstract Strategy': 2,
    'Educational': 2,
    
    # 非常に低い相互作用（1）
    'Solo / Solitaire Game': 1
}

def get_mechanic_strategic_value(mechanic_name):
    """
    指定されたメカニクスの戦略的価値を取得する
    
    Parameters:
    mechanic_name (str): メカニクス名
    
    Returns:
    float: 戦略的価値（1.0〜5.0の範囲）
    """
    return MECHANICS_STRATEGIC_VALUE.get(mechanic_name, 3.0)  # デフォルト値: 3.0

def get_mechanic_interaction_value(mechanic_name):
    """
    指定されたメカニクスのプレイヤー間相互作用の値を取得する
    
    Parameters:
    mechanic_name (str): メカニクス名
    
    Returns:
    float: 相互作用の値（1.0〜5.0の範囲）
    """
    return MECHANICS_INTERACTION_VALUE.get(mechanic_name, 3.0)  # デフォルト値: 3.0

def get_category_strategic_value(category_name):
    """
    指定されたカテゴリの戦略的価値を取得する
    
    Parameters:
    category_name (str): カテゴリ名
    
    Returns:
    float: 戦略的価値（1.0〜5.0の範囲）
    """
    return CATEGORIES_STRATEGIC_VALUE.get(category_name, 3.0)  # デフォルト値: 3.0

def get_category_interaction_value(category_name):
    """
    指定されたカテゴリのプレイヤー間相互作用の値を取得する
    
    Parameters:
    category_name (str): カテゴリ名
    
    Returns:
    float: 相互作用の値（1.0〜5.0の範囲）
    """
    return CATEGORIES_INTERACTION_VALUE.get(category_name, 3.0)  # デフォルト値: 3.0

# プレイ時間と複雑さの関係を評価する関数
def evaluate_playtime_complexity(game_data):
    """
    プレイ時間に基づく複雑さボーナスを評価する
    
    Parameters:
    game_data (dict): ゲームの詳細情報
    
    Returns:
    dict: プレイ時間に関する分析情報
    """
    playtime_info = {
        "strategic_bonus": 0.0,     # 戦略的深度に対するボーナス
        "interaction_modifier": 0.0, # 相互作用に対する修正値
        "decision_density": 0.0,    # 単位時間あたりの意思決定密度
        "complexity_factor": 1.0    # 複雑さに対する全体的な修正係数
    }
    
    # プレイ時間が設定されていない場合はデフォルト値を返す
    if 'playing_time' not in game_data:
        return playtime_info
    
    try:
        play_time = int(game_data['playing_time'])
        
        # 戦略的深度へのボーナス（長時間ゲームは通常より戦略的）
        if play_time > 180:  # 3時間以上
            playtime_info["strategic_bonus"] = 0.3
        elif play_time > 120:  # 2時間以上
            playtime_info["strategic_bonus"] = 0.2
        elif play_time > 60:  # 1時間以上
            playtime_info["strategic_bonus"] = 0.1
        
        # 相互作用への修正（短時間ゲームは濃密な相互作用、長時間ゲームは戦略的対立）
        if play_time <= 30:  # 30分以下
            playtime_info["interaction_modifier"] = 0.2  # 短時間での高い相互作用
        elif play_time >= 180:  # 3時間以上
            playtime_info["interaction_modifier"] = 0.1  # 長時間での戦略的対立
        
        # 単位時間あたりの意思決定密度
        # 短いゲームでの決断は重みがある傾向、長いゲームでは分散する傾向
        mechanics_count = len(game_data.get('mechanics', []))
        if play_time <= 30 and mechanics_count >= 3:  # 短時間で多くのメカニクス
            playtime_info["decision_density"] = 0.2
        elif 30 < play_time <= 60 and mechanics_count >= 4:
            playtime_info["decision_density"] = 0.15
        elif 60 < play_time <= 120 and mechanics_count >= 5:
            playtime_info["decision_density"] = 0.1
        
        # 全体的な複雑さに対する修正係数
        # 短すぎるゲームは複雑さが制限される傾向がある
        if play_time < 20:  # 20分未満
            playtime_info["complexity_factor"] = 0.85  # 複雑さ15%減少
        elif play_time < 45:  # 45分未満
            playtime_info["complexity_factor"] = 0.95  # 複雑さ5%減少
        elif play_time > 180:  # 3時間以上
            playtime_info["complexity_factor"] = 1.1   # 複雑さ10%増加
        
    except (ValueError, TypeError):
        # プレイ時間をパースできない場合はデフォルト値を使用
        pass
        
    return playtime_info

def estimate_decision_points_improved(mechanics, game_data=None):
    """
    意思決定ポイントの推定（重み付けを再調整）
    
    Parameters:
    mechanics (list): メカニクスのリスト
    game_data (dict, optional): ゲームの詳細情報
    
    Returns:
    float: 推定された意思決定ポイント（1.0〜5.0の範囲）
    """
    if not mechanics:
        return 2.5  # デフォルト値
    
    # 各メカニクスの戦略的価値を取得
    strategic_values = [get_mechanic_strategic_value(m['name']) for m in mechanics]
    
    if strategic_values:
        # 戦略的価値が高い順にソート
        strategic_values.sort(reverse=True)
        
        # 重み付け係数の再調整
        # 最も価値の高い要素の影響力を抑え、2番目以降の要素の影響力を増加
        if len(strategic_values) == 1:
            weights = [1.0]
        elif len(strategic_values) == 2:
            weights = [0.65, 0.35]  # 以前: 約[0.67, 0.33]
        elif len(strategic_values) == 3:
            weights = [0.55, 0.30, 0.15]  # 以前: 約[0.6, 0.3, 0.1]
        else:
            # 徐々に減少する重み付け、但し分散を小さくする
            weights = []
            for i in range(len(strategic_values)):
                if i == 0:
                    weights.append(0.5)  # 最も高い要素: 50%
                elif i == 1:
                    weights.append(0.25)  # 2番目の要素: 25%
                else:
                    # 残りの要素: 徐々に減少するが最低0.5/(n-2)%を保証
                    remaining_weight = 0.25  # 残り25%を分配
                    remaining_count = len(strategic_values) - 2
                    min_weight = 0.5 / max(1, remaining_count)
                    weights.append(max(min_weight, remaining_weight / remaining_count))
        
        # 重み付け合計を1.0に正規化
        weights_sum = sum(weights)
        weights = [w / weights_sum for w in weights]
        
        # 重み付け平均を計算
        weighted_sum = sum(v * w for v, w in zip(strategic_values, weights))
        
        # メカニクスの多様性に基づくボーナス（影響を調整）
        # 単純なカウントではなく、多様性の度合いを評価
        unique_values = set(strategic_values)
        value_range = max(strategic_values) - min(strategic_values) if len(strategic_values) > 1 else 0
        
        # 多様性と範囲に基づくボーナス（最大0.4に制限）
        diversity_bonus = min(0.4, len(unique_values) * 0.07 + value_range * 0.1)
        
        # 基本的な意思決定ポイント
        decision_points = weighted_sum + diversity_bonus
        
        # プレイ時間による修正（存在する場合）
        if game_data:
            playtime_info = evaluate_playtime_complexity(game_data)
            # 決断密度の影響を調整（80%に抑制）
            decision_points += playtime_info["decision_density"] * 0.8
            # 複雑さ係数の影響を調整（90%に抑制）
            complexity_factor = 1.0 + (playtime_info["complexity_factor"] - 1.0) * 0.9
            decision_points *= complexity_factor
    else:
        decision_points = 2.5
    
    # 1.0〜5.0の範囲に制限
    return min(5.0, max(1.0, decision_points))

def estimate_interaction_complexity_improved(categories, mechanics=None, game_data=None):
    """
    相互作用複雑性の推定（重み付けを再調整）
    
    Parameters:
    categories (list): カテゴリのリスト
    mechanics (list, optional): メカニクスのリスト
    game_data (dict, optional): ゲームの詳細情報
    
    Returns:
    float: 推定された相互作用複雑性（1.0〜5.0の範囲）
    """
    if not categories and not mechanics:
        return 2.5  # デフォルト値
    
    # カテゴリとメカニクスの相互作用値を結合
    category_values = [get_category_interaction_value(c['name']) for c in (categories or [])]
    mechanic_values = [get_mechanic_interaction_value(m['name']) for m in (mechanics or [])]
    
    # カテゴリとメカニクスの重み付けを調整（カテゴリ:メカニクス = 60:40）
    if category_values and mechanic_values:
        # 両方存在する場合は加重平均を計算
        all_values = []
        
        # カテゴリ値（60%の重み）
        for value in category_values:
            all_values.append((value, 0.6 / len(category_values)))
            
        # メカニクス値（40%の重み）
        for value in mechanic_values:
            all_values.append((value, 0.4 / len(mechanic_values)))
        
        # 値で降順ソート
        all_values.sort(key=lambda x: x[0], reverse=True)
        values = [v[0] for v in all_values]
        weights = [v[1] for v in all_values]
    else:
        # いずれか一方のみ存在する場合
        values = category_values or mechanic_values
        values.sort(reverse=True)
        
        # 重み付け係数の再調整
        if len(values) <= 3:
            # 少数の要素: 最初の要素の影響力を抑え、後続要素の影響力を増加
            if len(values) == 1:
                weights = [1.0]
            elif len(values) == 2:
                weights = [0.65, 0.35]
            else:  # len(values) == 3
                weights = [0.55, 0.30, 0.15]
        else:
            # 多数の要素: 上位3つを強調するが、残りにも一定の影響力を持たせる
            weights = []
            top_n = min(3, len(values))
            for i in range(len(values)):
                if i < top_n:
                    # 上位3つ: 合計で65%の影響力
                    if i == 0:
                        weights.append(0.3)    # 1位: 30%
                    elif i == 1:
                        weights.append(0.2)    # 2位: 20%
                    else:  # i == 2
                        weights.append(0.15)   # 3位: 15%
                else:
                    # 残り: 合計で35%を均等に分配
                    remaining_count = len(values) - top_n
                    weights.append(0.35 / remaining_count)
    
    # 重み付け合計を1.0に正規化
    weights_sum = sum(weights)
    weights = [w / weights_sum for w in weights]
    
    # 重み付け平均を計算
    interaction_complexity = sum(v * w for v, w in zip(values, weights))
    
    # プレイ時間による修正（存在する場合）
    if game_data:
        playtime_info = evaluate_playtime_complexity(game_data)
        # 相互作用修正値の影響を調整（85%に抑制）
        interaction_complexity += playtime_info["interaction_modifier"] * 0.85
        # 複雑さ係数の影響を調整（90%に抑制）
        complexity_factor = 1.0 + (playtime_info["complexity_factor"] - 1.0) * 0.9
        interaction_complexity *= complexity_factor
    
    # プレイ人数に基づく修正
    if game_data and 'publisher_max_players' in game_data:
        try:
            max_players = int(game_data['publisher_max_players'])
            # 影響を調整（以前: 15%→10%、10%→7%）
            if max_players >= 5:
                interaction_complexity *= 1.10  # 10%増加
            elif max_players >= 4:
                interaction_complexity *= 1.07  # 7%増加
        except (ValueError, TypeError):
            pass
    
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
    改善された戦略深度計算関数（重み付けを再調整）
    
    Parameters:
    game_data (dict): ゲームの詳細情報
    
    Returns:
    float: 戦略的深さのスコア（1.0〜5.0の範囲）
    """
    # BGG重み付けを20%に調整（外部評価の影響を抑える）
    base_weight = float(game_data.get('weight', 3.0))
    
    # 意思決定ポイントの推定
    decision_points = estimate_decision_points_improved(
        game_data.get('mechanics', []), game_data)
    
    # プレイヤー相互作用の複雑性を推定
    interaction_complexity = estimate_interaction_complexity_improved(
        game_data.get('categories', []), game_data.get('mechanics', []), game_data)
    
    # ルールの複雑さを計算
    rules_complexity = calculate_rules_complexity(game_data)
    
    # メカニクスの戦略的価値を評価
    mechanics = game_data.get('mechanics', [])
    mechanics_names = [m['name'] for m in mechanics]
    
    # 戦略的価値の高いメカニクスによるボーナス計算
    # 重み付けを再調整: 0.5 -> 0.4, 0.45 -> 0.35 など、全体的に20%減少
    high_strategy_mechanics = {
        'Engine Building': 0.4,
        'Tech Trees / Tech Tracks': 0.35,
        'Worker Placement': 0.32,
        'Deck Building': 0.28,
        'Area Control / Area Influence': 0.28,
        'Multi-Use Cards': 0.24,
        'Action Points': 0.2,
        'Resource Management': 0.2
    }
    
    medium_strategy_mechanics = {
        'Card Drafting': 0.16,
        'Variable Player Powers': 0.16,
        'Route/Network Building': 0.16,
        'Auction / Bidding': 0.12,
        'Hand Management': 0.12,
        'Tile Placement': 0.12,
        'Action Selection': 0.12
    }
    
    # 戦略的価値に基づくボーナス計算
    strategy_bonus = 0
    mechanic_count = 0
    
    for mechanic in mechanics_names:
        if mechanic in high_strategy_mechanics:
            strategy_bonus += high_strategy_mechanics[mechanic]
            mechanic_count += 1
        elif mechanic in medium_strategy_mechanics:
            strategy_bonus += medium_strategy_mechanics[mechanic]
            mechanic_count += 1
    
    # メカニクスが多すぎる場合の減衰を適用
    if mechanic_count > 0:
        decay_factor = 1.0 / (1.0 + math.log(mechanic_count, 10))
        # 減衰を適用したボーナス（最大0.8に制限）
        strategy_bonus = min(0.8, strategy_bonus * decay_factor)
    
    # プレイ時間による戦略的深さボーナス
    playtime_info = evaluate_playtime_complexity(game_data)
    playtime_strategic_bonus = playtime_info["strategic_bonus"]
    
    # 戦略的深さの計算（重み付けを再調整）
    strategic_depth = (
        base_weight * 0.20 +                   # BGG評価（20%→予測能力を抑える）
        decision_points * 0.35 +               # 意思決定ポイント（30%→35%に増加）
        rules_complexity * 0.10 +              # ルールの複雑さ（15%→10%に減少）
        interaction_complexity * 0.25 +        # 相互作用複雑性（20%→25%に増加）
        strategy_bonus * 0.8 +                 # 戦略的メカニクスボーナス（最大0.8に制限、80%の影響力）
        playtime_strategic_bonus * 0.6         # プレイ時間ボーナス（60%の影響力）
    )
    
    # 全体的な複雑さ係数を適用（影響を95%に抑制）
    complexity_factor = playtime_info["complexity_factor"]
    complexity_factor = 1.0 + (complexity_factor - 1.0) * 0.95
    strategic_depth *= complexity_factor
    
    # 最終的な戦略的深さ（1.0〜5.0に制限）
    strategic_depth = min(5.0, max(1.0, strategic_depth))
    
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
    learning_curve["decision_points"] = estimate_decision_points_improved(game_data.get('mechanics', []), game_data)
    learning_curve["interaction_complexity"] = estimate_interaction_complexity_improved(
        game_data.get('categories', []), game_data.get('mechanics', []), game_data)
    learning_curve["rules_complexity"] = calculate_rules_complexity(game_data)
    learning_curve["player_types"] = player_types
    
    # プレイ時間分析データを追加
    learning_curve["playtime_analysis"] = evaluate_playtime_complexity(game_data)
    
    return learning_curve