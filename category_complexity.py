import os
import yaml
import streamlit as st

# YAMLファイルのパス
CATEGORIES_DATA_FILE = "categories_data.yaml"

def log_error(message):
    """エラーメッセージをログに記録する関数（Streamlitのページ設定後に呼び出される）"""
    st.error(message)

def load_categories_data():
    """
    カテゴリの複雑さデータをYAMLファイルから読み込む
    
    Returns:
    dict: カテゴリ名をキー、複雑さを値とする辞書
    """
    try:
        # ファイルが存在しない場合は空の辞書を返す
        if not os.path.exists(CATEGORIES_DATA_FILE):
            return {}
        
        with open(CATEGORIES_DATA_FILE, 'r', encoding='utf-8') as file:
            complexity_data = yaml.safe_load(file)
            
        # Noneの場合は空の辞書を返す
        if complexity_data is None:
            return {}
            
        return complexity_data
    except Exception as e:
        # エラーメッセージを直接表示せず、エラー情報を返す
        print(f"カテゴリデータの読み込みエラー: {str(e)}")
        return {}

def save_categories_data(complexity_data):
    """
    カテゴリの複雑さデータをYAMLファイルに保存する
    
    Parameters:
    complexity_data (dict): カテゴリ名をキー、複雑さを値とする辞書
    
    Returns:
    bool: 保存が成功したかどうか
    """
    try:
        with open(CATEGORIES_DATA_FILE, 'w', encoding='utf-8') as file:
            yaml.dump(complexity_data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        print(f"カテゴリデータの保存エラー: {str(e)}")
        return False

def add_missing_category(category_name, default_complexity=2.5):
    """
    存在しないカテゴリをYAMLファイルに追加する
    
    Parameters:
    category_name (str): 追加するカテゴリ名
    default_complexity (float): デフォルトの複雑さ値（未設定）
    
    Returns:
    bool: 追加が成功したかどうか
    """
    try:
        # 現在のデータを読み込む
        complexity_data = load_categories_data()
        
        # 既に存在する場合は何もしない
        if category_name in complexity_data:
            return True
        
        # 存在しない場合は追加
        complexity_data[category_name] = default_complexity
        
        # 保存
        return save_categories_data(complexity_data)
    except Exception as e:
        print(f"カテゴリの追加エラー: {str(e)}")
        return False

def get_category_complexity(category_name, default_value=2.5):
    """
    指定されたカテゴリの複雑さを取得する
    存在しない場合はデフォルト値を返し、自動的にデータベースに追加する
    
    Parameters:
    category_name (str): 複雑さを取得するカテゴリ名
    default_value (float): 存在しない場合のデフォルト値
    
    Returns:
    float: カテゴリの複雑さ
    """
    complexity_data = load_categories_data()
    
    # カテゴリが存在するか確認
    if category_name in complexity_data:
        return complexity_data[category_name]
    
    # 存在しない場合は追加して保存
    add_missing_category(category_name, default_value)
    
    return default_value

def calculate_category_complexity(categories):
    """
    カテゴリリストから全体の複雑さスコアを計算する
    
    Parameters:
    categories (list): カテゴリ辞書のリスト
    
    Returns:
    float: カテゴリの総合複雑さスコア（1.0〜5.0の範囲）
    """
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

# データが空の場合はサンプルデータを提供
def initialize_categories_data():
    """
    カテゴリデータが存在しない場合、初期データを作成する
    """
    if not os.path.exists(CATEGORIES_DATA_FILE) or os.path.getsize(CATEGORIES_DATA_FILE) == 0:
        # サンプルデータ
        sample_data = {
            "Abstract Strategy": 3.2,
            "Adventure": 3.5,
            "Animals": 1.8,
            "Area Control / Area Influence": 4.2,
            "Card Game": 2.5,
            "Children's Game": 1.0,
            "City Building": 3.7,
            "Civilization": 4.5,
            "Deduction": 3.3,
            "Dice": 2.0,
            "Economic": 4.0,
            "Educational": 2.0,
            "Family Game": 2.0,
            "Fantasy": 3.0,
            "Farming": 3.3,
            "Fighting": 3.0,
            "Historical": 3.8,
            "Horror": 3.2,
            "Medieval": 3.5,
            "Memory": 1.5,
            "Miniatures": 3.7,
            "Multiplayer Solitaire": 2.7,
            "Mythology": 3.3,
            "Negotiation": 3.8,
            "Party Game": 1.7,
            "Political": 4.0,
            "Puzzle": 2.8,
            "Racing": 2.3,
            "Real-time": 3.0,
            "Science Fiction": 3.5,
            "Strategy": 4.2,
            "Territory Building": 3.8,
            "Trading": 3.0,
            "Wargame": 4.5,
            "Word Game": 2.2
        }
        save_categories_data(sample_data)

# プログラム起動時にデータの初期化を行う
initialize_categories_data()

# 後方互換性のため、グローバル辞書を維持
COMPLEXITY_BY_CATEGORY = load_categories_data()