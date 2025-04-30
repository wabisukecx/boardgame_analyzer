"""
Streamlit依存なしでBoardGameGeekのゲームデータからラーニングカーブを分析するモジュール
daily_update.py用に最適化
"""

import datetime
import math
import os
import yaml

# 設定ファイルのパス
CONFIG_DIR = "config"
MECHANICS_DATA_FILE = os.path.join(CONFIG_DIR, "mechanics_data.yaml")
CATEGORIES_DATA_FILE = os.path.join(CONFIG_DIR, "categories_data.yaml")
RANK_COMPLEXITY_FILE = os.path.join(CONFIG_DIR, "rank_complexity.yaml")

# YAML設定ファイル読み込み関数
def load_yaml_config(file_path, default_value=None):
    """YAMLファイルを読み込む汎用関数"""
    if not os.path.exists(file_path):
        return default_value or {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        
        # Noneの場合は空の辞書を返す
        if data is None:
            return {}
            
        return data
    except Exception as e:
        print(f"設定ファイル読み込みエラー ({file_path}): {str(e)}")
        return default_value or {}

# メカニクスの複雑さ処理関数
def get_mechanic_complexity(mechanic_name, default_value=2.5):
    """メカニクス名から複雑さを取得"""
    mechanics_data = load_yaml_config(MECHANICS_DATA_FILE)
    
    # メカニクスが存在するか確認
    if mechanic_name in mechanics_data:
        # 新しい構造: complexity_data[mechanic_name] はディクショナリで、
        # その中に 'complexity' キーがある
        if isinstance(mechanics_data[mechanic_name], dict) and 'complexity' in mechanics_data[mechanic_name]:
            return mechanics_data[mechanic_name]['complexity']
        # 後方互換性のため、直接値が格納されている場合もサポート
        elif isinstance(mechanics_data[mechanic_name], (int, float)):
            return mechanics_data[mechanic_name]
    
    return default_value

# カテゴリの複雑さ処理関数
def get_category_complexity(category_name, default_value=2.5):
    """カテゴリ名から複雑さを取得"""
    categories_data = load_yaml_config(CATEGORIES_DATA_FILE)
    
    # カテゴリが存在するか確認
    if category_name in categories_data:
        # 新しい構造: categories_data[category_name] はディクショナリ
        if isinstance(categories_data[category_name], dict) and 'complexity' in categories_data[category_name]:
            return categories_data[category_name]['complexity']
        # 後方互換性のため、直接値が格納されている場合もサポート
        elif isinstance(categories_data[category_name], (int, float)):
            return categories_data[category_name]
    
    return default_value

def calculate_category_complexity(categories):
    """カテゴリリストから全体の複雑さスコアを計算"""
    if not categories:
        return 2.5  # デフォルト値
    
    # 各カテゴリの複雑さを取得
    complexity_scores = [get_category_complexity(cat['name']) for cat in categories]
    
    # 複雑さの平均を計算
    avg_complexity = sum(complexity_scores) / len(complexity_scores)
    
    # カテゴリ数による補正（多様なカテゴリがあるゲームはより複雑）
    category_count_factor = min(1.3, 1.0 + (len(categories) - 1) * 0.05)
    adjusted_complexity = avg_complexity * category_count_factor
    
    # 1.0〜5.0の範囲に制限
    return min(5.0, max(1.0, adjusted_complexity))

# ランキングの複雑さ処理関数
def get_rank_complexity_value(rank_type, default_value=3.0):
    """ランク種別から複雑さを取得"""
    complexity_data = load_yaml_config(RANK_COMPLEXITY_FILE)
    
    # ランク種別が存在するか確認
    if rank_type in complexity_data:
        # 新しい構造: complexity_data[rank_type] はディクショナリ
        if isinstance(complexity_data[rank_type], dict) and 'complexity' in complexity_data[rank_type]:
            return complexity_data[rank_type]['complexity']
        # 後方互換性のため、直接値が格納されている場合もサポート
        elif isinstance(complexity_data[rank_type], (int, float)):
            return complexity_data[rank_type]
    
    return default_value

def calculate_rank_position_score(rank_value):
    """ランキングの順位からゲームの人気/品質スコアを計算"""
    try:
        # 順位を整数に変換
        rank = int(rank_value)
        
        # 対数スケールでスコアを計算（上位ほどスコアが高い）
        if rank <= 10:
            # トップ10は最高評価
            score = 5.0
        elif rank <= 100:
            # トップ100はとても高い評価
            score = 4.5 - (rank - 10) / 90 * 0.5  # 4.5～4.0
        elif rank <= 1000:
            # トップ1000は高い評価
            score = 4.0 - (rank - 100) / 900 * 1.0  # 4.0～3.0
        elif rank <= 5000:
            # トップ5000は中程度の評価
            score = 3.0 - (rank - 1000) / 4000 * 1.0  # 3.0～2.0
        else:
            # 5000位より下は低い評価
            score = max(1.0, 2.0 - math.log10(rank / 5000))  # 2.0～1.0
        
        return score
    except (ValueError, TypeError):
        # 数値に変換できない場合はデフォルト値を返す
        return 2.5

def calculate_rank_complexity(ranks):
    """ランキング情報から複雑さスコアを計算"""
    if not ranks:
        return 3.0  # デフォルト値
    
    # 各ランキング種別ごとのスコアを計算
    rank_scores = []
    for rank_info in ranks:
        rank_type = rank_info.get('type', 'boardgame')
        rank_value = rank_info.get('rank')
        
        if rank_value and rank_value != "Not Ranked":
            # 順位からの人気/品質スコア
            popularity_score = calculate_rank_position_score(rank_value)
            
            # ランキング種別の複雑さ（基準値）
            type_complexity = get_rank_complexity_value(rank_type)
            
            # 複雑さ評価は主にランキング種別に基づく
            # 順位の影響は小さくする（20%）
            adjusted_score = (type_complexity * 0.8 + (popularity_score - 3.0) * 0.2)
            
            # 重み付けはランキング種別の重要度
            weight = 1.0
            if rank_type == "boardgame":
                weight = 1.0  # 総合ランキングは標準の重み
            elif rank_type in ["strategygames", "wargames"]:
                weight = 1.2  # 戦略ゲーム系は重み増加
            elif rank_type in ["familygames", "partygames", "childrensgames"]:
                weight = 0.8  # カジュアルゲーム系は重み減少
            
            # 重み付けスコアを追加
            rank_scores.append((adjusted_score, weight))
    
    # スコアがない場合はデフォルト値を返す
    if not rank_scores:
        return 3.0
        
    # 重み付け平均を計算
    total_weighted_score = sum(score * weight for score, weight in rank_scores)
    total_weight = sum(weight for _, weight in rank_scores)
    
    avg_score = total_weighted_score / total_weight
    
    # 1.0〜5.0の範囲に制限
    return min(5.0, max(1.0, avg_score))

def get_mechanic_strategic_value(mechanic_name, default_value=3.0):
    """指定されたメカニクスの戦略的価値を取得"""
    mechanics_data = load_yaml_config(MECHANICS_DATA_FILE)
    
    # メカニクスが存在するか確認
    if mechanic_name in mechanics_data:
        # 辞書形式でstrategic_valueを格納している場合
        if isinstance(mechanics_data[mechanic_name], dict) and "strategic_value" in mechanics_data[mechanic_name]:
            return mechanics_data[mechanic_name]["strategic_value"]
        else:
            # 複雑さの値に基づいて戦略的価値を推定
            complexity = mechanics_data[mechanic_name] if isinstance(mechanics_data[mechanic_name], (int, float)) else 3.0
            # 複雑さに基づく戦略的価値の推定（複雑なほど高い戦略性）
            estimated_value = min(5.0, complexity * 0.9)
            return max(1.0, estimated_value)
    
    return default_value

def get_mechanic_interaction_value(mechanic_name, default_value=3.0):
    """指定されたメカニクスのプレイヤー間相互作用の値を取得"""
    mechanics_data = load_yaml_config(MECHANICS_DATA_FILE)
    
    # メカニクスが存在するか確認
    if mechanic_name in mechanics_data:
        # 辞書形式でinteraction_valueを格納している場合
        if isinstance(mechanics_data[mechanic_name], dict) and "interaction_value" in mechanics_data[mechanic_name]:
            return mechanics_data[mechanic_name]["interaction_value"]
        else:
            # 特定のメカニクスは相互作用が高い傾向がある
            high_interaction_mechanics = [
                'Trading', 'Negotiation', 'Auction/Bidding', 'Take That', 
                'Betting and Bluffing', 'Player Elimination'
            ]
            if mechanic_name in high_interaction_mechanics:
                return 4.5
            
            medium_interaction_mechanics = [
                'Area Control', 'Team-Based Game', 'Cooperative Game', 
                'Simultaneous Action Selection'
            ]
            if mechanic_name in medium_interaction_mechanics:
                return 3.8
            
            # それ以外は中程度の相互作用
            return default_value
    
    return default_value

def evaluate_playtime_complexity(game_data):
    """プレイ時間に基づく複雑さボーナスを評価する"""
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

def estimate_decision_points(mechanics, game_data=None):
    """意思決定ポイントの推定（重み付けを再調整）"""
    if not mechanics:
        return 2.5  # デフォルト値
    
    # 各メカニクスの戦略的価値を取得
    strategic_values = [get_mechanic_strategic_value(m['name']) for m in mechanics]
    
    if strategic_values:
        # 戦略的価値が高い順にソート
        strategic_values.sort(reverse=True)
        
        # 重み付け係数の再調整
        if len(strategic_values) == 1:
            weights = [1.0]
        elif len(strategic_values) == 2:
            weights = [0.65, 0.35]
        elif len(strategic_values) == 3:
            weights = [0.55, 0.30, 0.15]
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
        
        # メカニクスの多様性に基づくボーナス
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

def estimate_interaction_complexity(categories, mechanics=None, game_data=None):
    """相互作用複雑性の推定（重み付けを再調整）"""
    if not categories and not mechanics:
        return 2.5  # デフォルト値
    
    # カテゴリとメカニクスの相互作用値を結合
    category_values = []
    for c in categories:
        category_name = c.get('name', '')
        categories_data = load_yaml_config(CATEGORIES_DATA_FILE)
        if category_name in categories_data:
            if isinstance(categories_data[category_name], dict) and 'interaction_value' in categories_data[category_name]:
                category_values.append(categories_data[category_name]['interaction_value'])
            else:
                # 既知の高相互作用カテゴリの場合
                high_interaction_categories = [
                    'Negotiation', 'Political', 'Bluffing', 'Party Game', 'Fighting'
                ]
                if category_name in high_interaction_categories:
                    category_values.append(4.5)
                # 既知の低相互作用カテゴリの場合
                elif category_name in ['Abstract Strategy', 'Puzzle', 'Solo / Solitaire Game']:
                    category_values.append(2.0)
                else:
                    category_values.append(3.0)
    
    mechanic_values = []
    if mechanics:
        for m in mechanics:
            mechanic_name = m.get('name', '')
            mechanic_values.append(get_mechanic_interaction_value(mechanic_name))
    
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
            # 影響を調整
            if max_players >= 5:
                interaction_complexity *= 1.10  # 10%増加
            elif max_players >= 4:
                interaction_complexity *= 1.07  # 7%増加
        except (ValueError, TypeError):
            pass
    
    # 1.0〜5.0の範囲に制限
    return min(5.0, max(1.0, interaction_complexity))

def calculate_rules_complexity(game_data):
    """ルールの複雑さを計算する"""
    # メカニクスの複雑さ計算
    mechanics = game_data.get('mechanics', [])
    mechanics_complexity_sum = sum(get_mechanic_complexity(m['name']) for m in mechanics)
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
    """改善された戦略深度計算関数（重み付けを再調整）"""
    # BGG重み付けを20%に調整（外部評価の影響を抑える）
    base_weight = float(game_data.get('weight', 3.0))
    
    # 意思決定ポイントの推定
    decision_points = estimate_decision_points(
        game_data.get('mechanics', []), game_data)
    
    # プレイヤー相互作用の複雑性を推定
    interaction_complexity = estimate_interaction_complexity(
        game_data.get('categories', []), game_data.get('mechanics', []), game_data)
    
    # ルールの複雑さを計算
    rules_complexity = calculate_rules_complexity(game_data)
    
    # メカニクスの戦略的価値を評価
    mechanics = game_data.get('mechanics', [])
    mechanics_names = [m['name'] for m in mechanics]
    
    # 戦略的価値の高いメカニクスのリストを取得
    high_strategy_values = [(name, get_mechanic_strategic_value(name)) for name in mechanics_names]
    high_strategy_values.sort(key=lambda x: x[1], reverse=True)
    
    # 戦略的価値に基づくボーナス計算
    strategy_bonus = 0
    mechanic_count = len(high_strategy_values)
    
    # 上位の戦略的価値を持つメカニクスを重視
    if mechanic_count > 0:
        # 最大3つの戦略的メカニクスを考慮
        top_n = min(3, mechanic_count)
        
        # 影響度の配分（1位:50%, 2位:30%, 3位:20%）
        weights = [0.5, 0.3, 0.2][:top_n]
        
        # 正規化
        weights_sum = sum(weights)
        weights = [w / weights_sum for w in weights]
        
        # 各メカニクスの影響度×戦略的価値の合計
        for i in range(top_n):
            name, value = high_strategy_values[i]
            impact = 0.1 * (value - 2.5)  # 2.5を基準としてボーナス/ペナルティを計算
            strategy_bonus += impact * weights[i]
    
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
        base_weight * 0.20 +                   # BGG評価（20%）
        decision_points * 0.35 +               # 意思決定ポイント（35%）
        rules_complexity * 0.10 +              # ルールの複雑さ（10%）
        interaction_complexity * 0.25 +        # 相互作用複雑性（25%）
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
    """戦略的深さの説明を取得する"""
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

def get_rank_value(game_data, rank_type="boardgame"):
    """指定されたランク種別の順位を取得する"""
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
    """ランキングに基づく人気係数を計算する"""
    if rank is None:
        return 1.0
        
    if rank <= 100:
        return 1.1  # トップ100は評価を10%増加
    elif rank <= 500:
        return 1.07  # トップ500は評価を6%増加
    elif rank <= 1000:
        return 1.02  # トップ1000は評価を3%増加
    else:
        return 1.0  # その他はそのまま

def get_year_published(game_data):
    """ゲームの発行年を取得する"""
    if 'year_published' not in game_data:
        return None
        
    try:
        return int(game_data['year_published'])
    except (ValueError, TypeError):
        return None

def calculate_longevity_factor(year_published):
    """ゲームの発行年に基づく長寿命係数を計算する"""
    if year_published is None:
        return 1.0
        
    current_year = datetime.datetime.now().year
    years_since_publication = current_year - year_published
    
    if years_since_publication >= 20:
        return 1.1   # 20年以上は10%増加（クラシックゲーム）
    elif years_since_publication >= 10:
        return 1.07  # 10年以上は7%増加（長期的な人気）
    elif years_since_publication >= 5:
        return 1.05  # 5年以上は5%増加（定着したゲーム）
    else:
        return 1.0   # 新しいゲームはそのまま

def calculate_replayability(game_data):
    """ゲームのリプレイ性を計算する"""
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
        'Campaign / Battle Card Driven',
        'Scenario / Mission / Campaign Game',
        'Deck Construction',
        'Engine Building',
        'Hidden Roles',
        'Asymmetric Gameplay'
    ]
    
    medium_replay_mechanics = [
        'Card Drafting',
        'Worker Placement',
        'Tech Trees / Tech Tracks',
        'Multi-Use Cards',
        'Area Control',
        'Route/Network Building',
        'Tile Placement',
        'Resource Management',
        'Drafting'
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
        # メカニクスの複雑さを取得
        mechanic_complexity = get_mechanic_complexity(mechanic)
        mechanics_complexity += mechanic_complexity
        mechanic_count += 1
    
    # メカニクスの平均複雑さ（メカニクスがない場合はデフォルト値）
    avg_mechanic_complexity = (
        mechanics_complexity / max(1, mechanic_count) if mechanic_count > 0 else 3.0
    )
    
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
        "rank_complexity": round(rank_complexity, 2),  # ランキングに基づく複雑さ
        "strategic_depth_description": get_strategic_depth_description(strategic_depth)
    }
    
    # 学習曲線タイプの判定
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
    
    # 各種分析の詳細情報を追加
    learning_curve["decision_points"] = estimate_decision_points(game_data.get('mechanics', []), game_data)
    learning_curve["interaction_complexity"] = estimate_interaction_complexity(game_data.get('categories', []), game_data.get('mechanics', []), game_data)
    learning_curve["rules_complexity"] = calculate_rules_complexity(game_data)
    
    # プレイヤータイプの判定
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
    
    # システムマスター向け
    if len(game_data.get('mechanics', [])) >= 5 and strategic_depth > 3.5:
        player_types.append("system_master")
    
    # リプレイヤー（リプレイ性の高いゲームを好む人）
    if replayability >= 3.8:
        player_types.append("replayer")
    
    # トレンドフォロワー（人気のゲームを好む人）
    if rank is not None and rank <= 1000:
        player_types.append("trend_follower")
    
    # クラシック愛好家（長年遊ばれている定番ゲームを好む人）
    if year_published is not None and year_published <= 2000:
        player_types.append("classic_lover")
    
    learning_curve["player_types"] = player_types
    
    # プレイ時間分析データを追加
    learning_curve["playtime_analysis"] = evaluate_playtime_complexity(game_data)
    
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