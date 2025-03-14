import os
import yaml
import streamlit as st
import math

# YAMLファイルのパス
RANK_COMPLEXITY_FILE = "rank_complexity.yaml"

def log_error(message):
    """エラーメッセージをログに記録する関数（Streamlitのページ設定後に呼び出される）"""
    st.error(message)

def load_rank_complexity_data():
    """
    ランキング種別の複雑さデータをYAMLファイルから読み込む
    
    Returns:
    dict: ランキング種別をキー、複雑さを値とする辞書
    """
    try:
        # ファイルが存在しない場合は空の辞書を返す
        if not os.path.exists(RANK_COMPLEXITY_FILE):
            return {}
        
        with open(RANK_COMPLEXITY_FILE, 'r', encoding='utf-8') as file:
            complexity_data = yaml.safe_load(file)
            
        # Noneの場合は空の辞書を返す
        if complexity_data is None:
            return {}
            
        return complexity_data
    except Exception as e:
        # エラーメッセージを直接表示せず、エラー情報を返す
        print(f"ランキング複雑さデータの読み込みエラー: {str(e)}")
        return {}

def save_rank_complexity_data(complexity_data):
    """
    ランキング種別の複雑さデータをYAMLファイルに保存する
    
    Parameters:
    complexity_data (dict): ランキング種別をキー、複雑さを値とする辞書
    
    Returns:
    bool: 保存が成功したかどうか
    """
    try:
        with open(RANK_COMPLEXITY_FILE, 'w', encoding='utf-8') as file:
            yaml.dump(complexity_data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        print(f"ランキング複雑さデータの保存エラー: {str(e)}")
        return False

def add_missing_rank_type(rank_type, default_complexity=3.0):
    """
    存在しないランキング種別をYAMLファイルに追加する
    
    Parameters:
    rank_type (str): 追加するランキング種別
    default_complexity (float): デフォルトの複雑さ値
    
    Returns:
    bool: 追加が成功したかどうか
    """
    try:
        # 現在のデータを読み込む
        complexity_data = load_rank_complexity_data()
        
        # 既に存在する場合は何もしない
        if rank_type in complexity_data:
            return True
        
        # 存在しない場合は追加
        complexity_data[rank_type] = default_complexity
        
        # 保存
        return save_rank_complexity_data(complexity_data)
    except Exception as e:
        print(f"ランキング種別の追加エラー: {str(e)}")
        return False

def get_rank_complexity_value(rank_type, default_value=3.0):
    """
    指定されたランキング種別の複雑さを取得する
    存在しない場合はデフォルト値を返し、自動的にデータベースに追加する
    
    Parameters:
    rank_type (str): 複雑さを取得するランキング種別
    default_value (float): 存在しない場合のデフォルト値
    
    Returns:
    float: ランキング種別の複雑さ
    """
    complexity_data = load_rank_complexity_data()
    
    # ランキング種別が存在するか確認
    if rank_type in complexity_data:
        return complexity_data[rank_type]
    
    # 存在しない場合は追加して保存
    add_missing_rank_type(rank_type, default_value)
    
    return default_value

def calculate_rank_position_score(rank_value):
    """
    ランキングの順位からゲームの人気/品質スコアを計算する
    順位が高い（数値が小さい）ほど人気/品質スコアが高くなる
    
    Parameters:
    rank_value (int or str): ランキングの順位
    
    Returns:
    float: ランキング順位に基づく人気/品質スコア（1.0〜5.0の範囲）
    """
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
    """
    ランキング情報から複雑さスコアを計算する
    ランキング種別の複雑さを主に考慮し、順位は二次的要素として扱う
    
    Parameters:
    ranks (list): ランキング情報のリスト
    
    Returns:
    float: ランキングに基づく複雑さスコア（1.0〜5.0の範囲）
    """
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
            # 高ランキングだと若干複雑さが上がる傾向を反映するが、主要因ではない
            adjusted_score = (type_complexity * 0.8 + (popularity_score - 3.0) * 0.2)
            
            # 重み付けはランキング種別の重要度（boardgameは1.0、他は種別ごとに設定）
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

# データが空の場合はサンプルデータを提供
def initialize_rank_complexity_data():
    """
    ランキング種別の複雑さデータが存在しない場合、初期データを作成する
    """
    if not os.path.exists(RANK_COMPLEXITY_FILE) or os.path.getsize(RANK_COMPLEXITY_FILE) == 0:
        # サンプルデータ - ランキング種別ごとの複雑さ基準値
        sample_data = {
            "boardgame": 3.0,       # 総合ランキング（標準）
            "strategygames": 4.2,    # 戦略ゲーム（複雑）
            "familygames": 2.3,      # ファミリーゲーム（やや簡単）
            "partygames": 1.8,       # パーティーゲーム（簡単）
            "thematic": 3.5,         # テーマティックゲーム（やや複雑）
            "wargames": 4.5,         # ウォーゲーム（非常に複雑）
            "abstracts": 3.7,        # 抽象ゲーム（やや複雑）
            "childrensgames": 1.5,   # 子供向けゲーム（簡単）
            "customizable": 3.8      # カスタマイズ可能なゲーム（やや複雑）
        }
        save_rank_complexity_data(sample_data)

# プログラム起動時にデータの初期化を行う
initialize_rank_complexity_data()

# 後方互換性のため、グローバル辞書を維持
COMPLEXITY_BY_RANK_TYPE = load_rank_complexity_data()