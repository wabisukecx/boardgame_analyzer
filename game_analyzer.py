"""
game_analyzer.py - ボードゲームの自動評価・分析モジュール
"""

from learning_curve import get_player_type_display, get_replayability_display

def analyze_game_summary(game_data, learning_curve):
    """
    ゲームデータから包括的な分析サマリーを生成する
    
    Parameters:
    game_data (dict): ゲームの詳細情報
    learning_curve (dict): ラーニングカーブの情報
    
    Returns:
    dict: 分析結果を含む辞書
    """
    analysis = {}
    
    # 基本情報
    analysis['name'] = game_data.get('japanese_name', game_data.get('name', '不明'))
    analysis['year'] = game_data.get('year_published', '不明')
    
    # BGG評価情報
    analysis['average_rating'] = float(game_data.get('average_rating', 0))
    analysis['bgg_weight'] = float(game_data.get('weight', 0))
    
    # ランキング情報の取得
    analysis['bgg_rank'] = None
    for rank_info in game_data.get('ranks', []):
        if rank_info.get('type') == 'boardgame':
            try:
                analysis['bgg_rank'] = int(rank_info.get('rank'))
            except (ValueError, TypeError):
                pass
    
    # カテゴリとメカニクス分析
    analysis['categories'] = [c.get('name') for c in game_data.get('categories', [])]
    analysis['mechanics'] = [m.get('name') for m in game_data.get('mechanics', [])]
    analysis['mechanics_count'] = len(analysis['mechanics'])
    analysis['categories_count'] = len(analysis['categories'])
    
    # 学習曲線データ
    analysis['initial_barrier'] = learning_curve.get('initial_barrier', 0)
    analysis['strategic_depth'] = learning_curve.get('strategic_depth', 0)
    analysis['rules_complexity'] = learning_curve.get('rules_complexity', 0)
    analysis['replayability'] = learning_curve.get('replayability', 0)
    analysis['decision_points'] = learning_curve.get('decision_points', 0)
    analysis['interaction_complexity'] = learning_curve.get('interaction_complexity', 0)
    
    # 対象プレイヤーとマスター時間
    analysis['player_types'] = learning_curve.get('player_types', [])
    analysis['mastery_time'] = learning_curve.get('mastery_time', 'medium')
    
    # プレイ情報
    analysis['playing_time'] = int(game_data.get('playing_time', 0))
    analysis['min_players'] = int(game_data.get('publisher_min_players', 1))
    analysis['max_players'] = int(game_data.get('publisher_max_players', 4))
    analysis['best_players'] = game_data.get('community_best_players', '')
    
    # 特徴分析
    analysis['complexity_level'] = get_complexity_level(analysis['bgg_weight'])
    analysis['depth_level'] = get_depth_level(analysis['strategic_depth'])
    analysis['popularity'] = get_popularity_level(analysis['bgg_rank'])

    return analysis

def get_complexity_level(weight):
    """複雑さレベルの説明を取得する"""
    if weight >= 4.0:
        return "非常に高く"
    elif weight >= 3.5:
        return "高く"
    elif weight >= 2.8:
        return "中〜高程度で"
    elif weight >= 2.0:
        return "中程度で"
    elif weight >= 1.5:
        return "中〜低程度で"
    else:
        return "低く"

def get_depth_level(depth):
    """戦略的深さの説明を取得する"""
    if depth >= 4.5:
        return "非常に深い"
    elif depth >= 4.0:
        return "深い"
    elif depth >= 3.5:
        return "中〜高の深さ"
    elif depth >= 3.0:
        return "中程度の深さ"
    elif depth >= 2.5:
        return "中〜低の深さ"
    elif depth >= 2.0:
        return "浅め"
    else:
        return "浅い"

def get_popularity_level(rank):
    """人気レベルの説明を取得する"""
    if rank is None:
        return "新作または評価収集中"
    elif rank <= 100:
        return "最高レベルの人気"
    elif rank <= 500:
        return "非常に高い人気"
    elif rank <= 1000:
        return "高い人気"
    elif rank <= 2000:
        return "一定の人気"
    else:
        return "ニッチな人気"

def analyze_complexity_discrepancy(game_data, learning_curve):
    """
    BGGの複雑さ評価と分析結果の差異を評価する
    
    Parameters:
    game_data (dict): ゲームの詳細情報
    learning_curve (dict): ラーニングカーブの情報
    
    Returns:
    dict: 分析結果
    """
    bgg_weight = float(game_data.get('weight', 0))
    rules_complexity = learning_curve.get('rules_complexity', 0)
    
    # 差異の計算
    discrepancy = rules_complexity - bgg_weight
    abs_discrepancy = abs(discrepancy)
    
    result = {
        "discrepancy": discrepancy,
        "abs_discrepancy": abs_discrepancy,
        "significant": abs_discrepancy > 0.8
    }
    
    if abs_discrepancy < 0.5:
        result["description"] = "BGGユーザー評価と分析結果の複雑さ評価は概ね一致しています。"
        return result
    
    if discrepancy > 0:
        # ランキング分析を最優先
        has_family_rank = False
        rank_type = ""
        for rank_info in game_data.get('ranks', []):
            if rank_info.get('type') == 'familygames':
                has_family_rank = True
                rank_type = "ファミリーゲーム"
                break
            elif rank_info.get('type') == 'childrensgames':
                has_family_rank = True
                rank_type = "子供向けゲーム"
                break
            elif rank_info.get('type') == 'abstracts':
                has_family_rank = True
                rank_type = "アブストラクト"
                break
        
        if has_family_rank:
            result["description"] = f"システム分析ではルールが複雑ですが、BGGユーザーはより簡単と評価しています。考えられる理由: {rank_type}カテゴリで高ランクに評価されているため。"
        else:
            # 他の原因分析
            if any(m.get('name') in ['Tile Placement', 'Pattern Building', 'Open Drafting'] 
                   for m in game_data.get('mechanics', [])):
                result["description"] = "システム分析ではルールが複雑ですが、BGGユーザーはより簡単と評価しています。考えられる理由: 視覚的に理解しやすいメカニクスを使用しているため。"
            elif any(c.get('name') in ['Family Game', 'Children\'s Game', 'Animals'] 
                   for c in game_data.get('categories', [])):
                result["description"] = "システム分析ではルールが複雑ですが、BGGユーザーはより簡単と評価しています。考えられる理由: ファミリー向けにデザインされているため。"
            elif int(game_data.get('playing_time', 0)) < 60:
                result["description"] = "システム分析ではルールが複雑ですが、BGGユーザーはより簡単と評価しています。考えられる理由: プレイ時間が短く取っつきやすいため。"
            else:
                result["description"] = "システム分析ではルールが複雑ですが、BGGユーザーはより簡単と評価しています。考えられる理由は不明です。"
    else:
        # BGGの方が複雑と評価している場合
        if any(m.get('name') in ['Worker Placement', 'Engine Building', 'Legacy Game'] 
               for m in game_data.get('mechanics', [])):
            result["description"] = "BGGユーザーは、システム分析より複雑と評価しています。考えられる理由: 上級者向けメカニクスが含まれているため。"
        elif any(c.get('name') in ['Economic', 'Political', 'Wargame'] 
               for c in game_data.get('categories', [])):
            result["description"] = "BGGユーザーは、システム分析より複雑と評価しています。考えられる理由: 複雑なテーマを扱っているため。"
        elif int(game_data.get('playing_time', 0)) > 120:
            result["description"] = "BGGユーザーは、システム分析より複雑と評価しています。考えられる理由: 長いプレイ時間が必要なため。"
        else:
            result["description"] = "BGGユーザーは、システム分析より複雑と評価しています。考えられる理由は不明です。"
    
    return result

def analyze_key_strengths(game_data, learning_curve):
    """ゲームの主な強みを分析"""
    strengths = []
    
    # 高評価関連
    if learning_curve.get('bgg_rank') and learning_curve.get('bgg_rank') < 500:
        strengths.append("ユーザーからの高い評価")
    
    if float(game_data.get('average_rating', 0)) > 7.5:
        strengths.append("高い平均評価")
    
    # 戦略とリプレイ関連
    if learning_curve.get('strategic_depth', 0) > 3.8:
        strengths.append("深い戦略性")
    
    if learning_curve.get('replayability', 0) > 3.8:
        strengths.append("高いリプレイ性")
    
    # アクセシビリティ関連
    if learning_curve.get('initial_barrier', 0) < 2.5:
        strengths.append("高いアクセシビリティ")
    
    # プレイヤー数の柔軟性
    min_players = int(game_data.get('publisher_min_players', 4))
    max_players = int(game_data.get('publisher_max_players', 4))
    if min_players == 1 and max_players >= 4:
        strengths.append("ソロからグループまで対応")
    elif max_players - min_players >= 3:
        strengths.append("柔軟なプレイヤー数対応")
    
    # プレイ時間
    if int(game_data.get('playing_time', 0)) <= 45:
        strengths.append("短時間でプレイ可能")
    
    return strengths[:3]  # 上位3つまで返す

def analyze_key_challenges(game_data, learning_curve):
    """ゲームの主な課題や注意点を分析"""
    challenges = []
    
    # 複雑さ関連
    if learning_curve.get('initial_barrier', 0) > 4.0:
        challenges.append("学習障壁が高い")
    
    # 戦略関連
    if learning_curve.get('strategic_depth', 0) < 2.5:
        challenges.append("戦略的深さが限られている")
    
    # リプレイ関連
    if learning_curve.get('replayability', 0) < 3.0:
        challenges.append("リプレイ性に課題")
    
    # プレイ時間
    if int(game_data.get('playing_time', 0)) > 120:
        challenges.append("長いプレイ時間")
    
    # 特定メカニクスの問題
    problematic_mechanics = ['Player Elimination', 'Roll / Spin and Move', 'Memory']
    for mech in problematic_mechanics:
        if any(m.get('name') == mech for m in game_data.get('mechanics', [])):
            challenges.append(f"{mech}メカニクスの存在")
    
    # ランダム性
    if any(m.get('name') in ['Dice Rolling', 'Random Production'] 
           for m in game_data.get('mechanics', [])):
        challenges.append("ランダム要素への依存")
    
    return challenges[:3]  # 上位3つまで返す

def generate_game_summary(game_data, learning_curve):
    """
    ゲームの総合サマリーテキストを生成する
    
    Parameters:
    game_data (dict): ゲームの詳細情報
    learning_curve (dict): ラーニングカーブの情報
    
    Returns:
    str: 生成されたサマリーテキスト
    """
    # 分析データを取得
    analysis = analyze_game_summary(game_data, learning_curve)
    
    # ゲーム名と年
    game_name = analysis['name']
    year = analysis['year']
    
    # カテゴリとメカニクス
    categories = analysis['categories'][:3]  # 最大3つまで
    mechanics = analysis['mechanics'][:3]    # 最大3つまで
    
    # 分析データ
    complexity = analysis['complexity_level']
    depth = analysis['depth_level']
    popularity = analysis['popularity']
    
    # プレイヤータイプとリプレイ性
    player_types_display = [get_player_type_display(pt) for pt in analysis['player_types'][:2]]
    
    # 数値を言葉での表現に変換
    initial_barrier = analysis['initial_barrier']
    replayability = analysis['replayability']
    
    # 初期学習障壁の言葉での表現
    if initial_barrier >= 4.5:
        barrier_text = "非常に高い（学習に長い時間を要する）"
    elif initial_barrier >= 4.0:
        barrier_text = "高い（学習に時間を要する）"
    elif initial_barrier >= 3.5:
        barrier_text = "やや高い（学習にやや時間を要する）"
    elif initial_barrier >= 3.0:
        barrier_text = "中程度（基本的な学習が必要）"
    elif initial_barrier >= 2.0:
        barrier_text = "低め（簡単に学べる）"
    else:
        barrier_text = "低い（すぐに始められる）"
        
    # リプレイ性の言葉での表現
    replayability_text = get_replayability_display(replayability)
    
    # 基本サマリー
    categories_text = "、".join(categories) if categories else "特定のテーマがない"
    mechanics_text = "、".join(mechanics) if mechanics else "特徴的なメカニクスがない"
    
    summary = (
        f"{game_name}（{year}年）は、{categories_text}をテーマにしたボードゲームです。"
        f"複雑さは{complexity}、戦略深度は{depth}です。主な特徴として{mechanics_text}などの"
        f"要素を含み、{popularity}"
        f"{'のためランキング情報はない' if popularity == '新作または評価収集中' else ''}です。\n\n"
    
        f"初期学習障壁は{barrier_text}、リプレイ性は{replayability_text}です。"
        f"このゲームは特に{', '.join(player_types_display)}に適しています。"
    )
    
    return summary