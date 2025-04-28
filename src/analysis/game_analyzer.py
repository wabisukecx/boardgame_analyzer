"""
game_analyzer.py - ボードゲームの評価・分析モジュール
現在のアプリケーションで実際に使われている関数のみを含む整理版
"""

def get_complexity_level(weight):
    """複雑さレベルの説明を取得する
    
    Parameters:
    weight (float): ゲームの複雑さ数値
    
    Returns:
    str: 複雑さレベルの説明テキスト
    """
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
    """戦略的深さの説明を取得する
    
    Parameters:
    depth (float): ゲームの戦略的深さ数値
    
    Returns:
    str: 戦略的深さの説明テキスト
    """
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
    """人気レベルの説明を取得する
    
    Parameters:
    rank (int or None): ゲームのBGGランキング順位
    
    Returns:
    str: 人気レベルの説明テキスト
    """
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

def generate_game_summary(game_data, learning_curve):
    """
    ゲームの総合サマリーテキストを生成する
    
    Parameters:
    game_data (dict): ゲームの詳細情報
    learning_curve (dict): ラーニングカーブの情報
    
    Returns:
    str: 生成されたサマリーテキスト
    """
    # ゲーム名と年
    game_name = game_data.get('japanese_name', game_data.get('name', '不明'))
    year = game_data.get('year_published', '不明')
    
    # カテゴリとメカニクス
    categories = [cat.get('name', '') for cat in game_data.get('categories', [])][:3]  # 最大3つまで
    mechanics = [mech.get('name', '') for mech in game_data.get('mechanics', [])][:3]  # 最大3つまで
    
    # BGGランキング情報
    bgg_rank = None
    for rank_info in game_data.get('ranks', []):
        if rank_info.get('type') == 'boardgame':
            try:
                bgg_rank = int(rank_info.get('rank'))
                break
            except (ValueError, TypeError):
                pass
    
    # 分析データ
    complexity = get_complexity_level(float(game_data.get('weight', 3.0)))
    depth = get_depth_level(learning_curve.get('strategic_depth', 3.0))
    popularity = get_popularity_level(bgg_rank)
    
    # プレイヤータイプ
    from src.analysis.learning_curve import get_player_type_display, get_replayability_display
    player_types_display = [get_player_type_display(pt) for pt in learning_curve.get('player_types', [])[:2]]
    
    # 初期学習障壁とリプレイ性
    initial_barrier = learning_curve.get('initial_barrier', 3.0)
    
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
        
    # リプレイ性
    replayability = learning_curve.get('replayability', 3.0)
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