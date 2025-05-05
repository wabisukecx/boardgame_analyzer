"""
改良版ボードゲーム類似性分析モジュール
学習曲線とゲーム特性に基づく高度な類似性評価
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Set

def analyze_similarity_reasons_improved(
    game1: Dict[str, Any],
    game2: Dict[str, Any]
) -> List[Tuple[str, float, str]]:
    """2つのゲーム間の類似理由を詳細に分析する関数
    
    Args:
        game1 (Dict[str, Any]): 1つ目のゲームデータ
        game2 (Dict[str, Any]): 2つ目のゲームデータ
        
    Returns:
        List[Tuple[str, float, str]]: 類似理由と類似度と説明のタプルのリスト
    """
    reasons = []
    learning1 = game1.get('learning_analysis', {})
    learning2 = game2.get('learning_analysis', {})
    
    # 共通指標のリスト（key, display_name, description, weight）
    learning_metrics = [
        ('initial_barrier', '初期学習障壁', '初期の学習しやすさ', 1.0),
        ('strategic_depth', '戦略的深さ', '戦略の深度', 1.2),
        ('replayability', 'リプレイ性', '繰り返し遊ぶ価値', 1.0),
        ('decision_points', '意思決定ポイント', '重要な決断の頻度', 0.9),
        ('interaction_complexity', 'プレイヤー相互作用', 'プレイヤー間の相互作用の複雑さ', 0.9),
        ('rules_complexity', 'ルールの複雑さ', 'ルールシステムの複雑さ', 0.8),
    ]
    
    # 学習曲線指標の比較
    if learning1 and learning2:
        for key, display_name, description, weight in learning_metrics:
            if key in learning1 and key in learning2:
                value1 = float(learning1.get(key, 0))
                value2 = float(learning2.get(key, 0))
                diff = abs(value1 - value2)
                
                # 差が小さいほど類似性が高い（最大0.7ポイント差まで類似と判断）
                if diff <= 0.7:
                    # 類似度スコアを計算 (0.7-diff)/0.7 * weight で正規化
                    similarity_score = (0.7 - diff) / 0.7 * weight
                    
                    # 値の範囲に応じた説明を生成
                    level_description = get_level_description(value1, key)
                    
                    # スコアが十分高い場合のみ追加
                    if similarity_score > 0.5:
                        reasons.append((
                            f"類似した{display_name}",
                            similarity_score,
                            f"両方のゲームが{level_description}（{value1:.1f} vs {value2:.1f}）"
                        ))
        
        # 学習曲線タイプの比較
        curve_type1 = learning1.get('learning_curve_type', '')
        curve_type2 = learning2.get('learning_curve_type', '')
        if curve_type1 and curve_type2 and curve_type1 == curve_type2:
            reasons.append((
                "同じ学習曲線タイプ",
                1.1,  # 完全一致は高いスコア
                f"両方のゲームが同じ学習パターン ({curve_type1}) を持つ"
            ))
        elif curve_type1 and curve_type2:
            # 部分的に一致する場合（例: steep_then_moderate と steep）
            if curve_type1.startswith(curve_type2) or curve_type2.startswith(curve_type1):
                reasons.append((
                    "類似した学習曲線タイプ",
                    0.7,
                    f"類似した学習パターン ({curve_type1} と {curve_type2})"
                ))
        
        # マスタリー時間の比較
        mastery1 = learning1.get('mastery_time', '')
        mastery2 = learning2.get('mastery_time', '')
        if mastery1 and mastery2 and mastery1 == mastery2:
            reasons.append((
                "同じマスタリー時間",
                0.9,
                f"両方のゲームのマスター時間が同程度 ({mastery1})"
            ))
    
    # プレイヤータイプの比較（重要度高め）
    player_types1 = set(learning1.get('player_types', []))
    player_types2 = set(learning2.get('player_types', []))
    common_player_types = player_types1.intersection(player_types2)
    
    if common_player_types:
        # 共通タイプが多いほど高いスコア
        overlap_ratio = len(common_player_types) / max(len(player_types1), len(player_types2))
        score = min(1.2, 0.6 + overlap_ratio * 0.6)  # 最大1.2、最小0.6
        
        reasons.append((
            "共通プレイヤータイプ",
            score,
            f"両方のゲームが同じタイプのプレイヤーに適している: {', '.join(common_player_types)}"
        ))
    
    # カテゴリ比較（基本類似性要素）
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
        # 共通カテゴリの重要度を考慮
        important_categories = {
            'Strategy', 'Economic', 'Civilization', 'Abstract Strategy',
            'City Building', 'Wargame', 'Card Game', 'Worker Placement'
        }
        important_matches = important_categories.intersection(common_categories)
        
        # 重要カテゴリの一致があれば高スコア
        if important_matches:
            reasons.append((
                "重要な共通カテゴリ",
                1.0,
                f"重要なカテゴリの一致: {', '.join(important_matches)}"
            ))
        
        # それ以外の共通カテゴリ
        other_matches = common_categories - important_categories
        if other_matches:
            reasons.append((
                "共通カテゴリ",
                0.8,
                f"共通カテゴリ: {', '.join(other_matches)}"
            ))
    
    # メカニクス比較（基本類似性要素）
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
        # 共通メカニクスの重要度を考慮
        strategic_mechanics = {
            'Worker Placement', 'Engine Building', 'Deck Building', 
            'Area Control', 'Resource Management', 'Tech Trees / Tech Tracks',
            'Variable Player Powers', 'Draft', 'Action Points'
        }
        strategic_matches = strategic_mechanics.intersection(common_mechanics)
        
        # 戦略的メカニクスの一致があれば高スコア
        if strategic_matches:
            reasons.append((
                "重要な共通メカニクス",
                1.1,
                f"重要なメカニクスの一致: {', '.join(strategic_matches)}"
            ))
        
        # それ以外の共通メカニクス
        other_matches = common_mechanics - strategic_mechanics
        if other_matches:
            reasons.append((
                "共通メカニクス",
                0.9,
                f"共通メカニクス: {', '.join(other_matches)}"
            ))
    
    # プレイ時間の比較
    try:
        time1 = int(game1.get('playing_time', 0))
        time2 = int(game2.get('playing_time', 0))
        if time1 > 0 and time2 > 0:
            # プレイ時間の差の割合
            time_diff_ratio = abs(time1 - time2) / max(time1, time2)
            
            # 差が30%以内なら類似と判断
            if time_diff_ratio <= 0.3:
                reasons.append((
                    "類似したプレイ時間",
                    0.8,
                    f"両方のゲームのプレイ時間が近い ({time1}分 vs {time2}分)"
                ))
    except (ValueError, TypeError):
        pass
    
    # 出版年の比較（低重要度）
    try:
        year1 = int(game1.get('year_published', 0))
        year2 = int(game2.get('year_published', 0))
        if year1 > 0 and year2 > 0 and abs(year1 - year2) <= 5:
            reasons.append((
                "近い発売年",
                0.4,  # 低めのスコア
                f"発売時期が近い ({year1} vs {year2})"
            ))
    except (ValueError, TypeError):
        pass
    
    # 理由がない場合（説明文から共通のキーワードを抽出）
    if not reasons:
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
            reasons.append((
                "説明文の共通キーワード",
                0.3,  # かなり低めのスコア
                f"説明文の共通キーワード: {', '.join(meaningful_words[:5])}"
            ))
        else:
            reasons.append((
                "テキスト内容の全体的な類似性",
                0.2,  # 最低スコア
                "特定の要素は見つかりませんでしたが、全体的な傾向が類似しています"
            ))
    
    # スコアで降順ソート
    reasons.sort(key=lambda x: x[1], reverse=True)
    return reasons

def get_level_description(value: float, metric_key: str) -> str:
    """メトリック値に基づく説明文を取得
    
    Args:
        value (float): メトリック値
        metric_key (str): メトリックのキー名
        
    Returns:
        str: 説明文
    """
    # 初期学習障壁
    if metric_key == 'initial_barrier':
        if value >= 4.5:
            return "非常に高い初期障壁を持つ"
        elif value >= 4.0:
            return "高い初期障壁を持つ"
        elif value >= 3.0:
            return "中程度の初期障壁を持つ"
        else:
            return "低い初期障壁を持つ"
    
    # 戦略的深さ
    elif metric_key == 'strategic_depth':
        if value >= 4.5:
            return "非常に深い戦略性を持つ"
        elif value >= 4.0:
            return "深い戦略性を持つ"
        elif value >= 3.0:
            return "中程度の戦略性を持つ"
        else:
            return "浅い戦略性を持つ"
    
    # リプレイ性
    elif metric_key == 'replayability':
        if value >= 4.5:
            return "非常に高いリプレイ性を持つ"
        elif value >= 4.0:
            return "高いリプレイ性を持つ"
        elif value >= 3.0:
            return "中程度のリプレイ性を持つ"
        else:
            return "限定的なリプレイ性を持つ"
    
    # 意思決定ポイント
    elif metric_key == 'decision_points':
        if value >= 4.5:
            return "非常に多くの意思決定を要する"
        elif value >= 4.0:
            return "多くの意思決定を要する"
        elif value >= 3.0:
            return "中程度の意思決定を要する"
        else:
            return "少数の意思決定で済む"
    
    # プレイヤー相互作用
    elif metric_key == 'interaction_complexity':
        if value >= 4.5:
            return "非常に高い相互作用を持つ"
        elif value >= 4.0:
            return "高い相互作用を持つ"
        elif value >= 3.0:
            return "中程度の相互作用を持つ"
        else:
            return "低い相互作用を持つ"
    
    # ルールの複雑さ
    elif metric_key == 'rules_complexity':
        if value >= 4.5:
            return "非常に複雑なルールを持つ"
        elif value >= 4.0:
            return "複雑なルールを持つ"
        elif value >= 3.0:
            return "中程度の複雑さのルールを持つ"
        else:
            return "シンプルなルールを持つ"
    
    # デフォルト
    else:
        if value >= 4.0:
            return "高い値を持つ"
        elif value >= 3.0:
            return "中程度の値を持つ"
        else:
            return "低い値を持つ"

def calculate_overall_similarity(
    game1: Dict[str, Any],
    game2: Dict[str, Any]
) -> float:
    """2つのゲーム間の総合的な類似度を計算
    
    Args:
        game1 (Dict[str, Any]): 1つ目のゲームデータ
        game2 (Dict[str, Any]): 2つ目のゲームデータ
        
    Returns:
        float: 総合的な類似度スコア (0.0〜1.0)
    """
    # 類似理由を取得
    similarity_reasons = analyze_similarity_reasons_improved(game1, game2)
    
    if not similarity_reasons:
        return 0.0
    
    # 各類似理由のスコアを合計
    total_score = sum(reason[1] for reason in similarity_reasons)
    
    # スコアを正規化（最大スコアは5.0と仮定）
    normalized_score = min(1.0, total_score / 5.0)
    
    return normalized_score

def get_formatted_similarity_reasons(
    game1: Dict[str, Any],
    game2: Dict[str, Any]
) -> List[str]:
    """類似理由を整形してリストで返す
    
    Args:
        game1 (Dict[str, Any]): 1つ目のゲームデータ
        game2 (Dict[str, Any]): 2つ目のゲームデータ
        
    Returns:
        List[str]: フォーマットされた類似理由のリスト
    """
    reasons = analyze_similarity_reasons_improved(game1, game2)
    
    # スコアは内部的なものなので表示用にフォーマット
    formatted_reasons = [f"{reason[0]}: {reason[2]}" for reason in reasons[:5]]
    
    # 理由がない場合
    if not formatted_reasons:
        return ["テキスト内容の全体的な類似性が見られます"]
    
    return formatted_reasons