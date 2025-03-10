import os
import yaml
import streamlit as st

# YAMLファイルのパス
MECHANICS_DATA_FILE = "mechanics_data.yaml"

# ログメッセージ用の関数
def log_error(message):
    """エラーメッセージをログに記録する関数（Streamlitのページ設定後に呼び出される）"""
    st.error(message)

def load_mechanics_data():
    """
    メカニクスの複雑さデータをYAMLファイルから読み込む
    
    Returns:
    dict: メカニクス名をキー、複雑さを値とする辞書
    """
    try:
        # ファイルが存在しない場合は空の辞書を返す
        if not os.path.exists(MECHANICS_DATA_FILE):
            return {}
        
        with open(MECHANICS_DATA_FILE, 'r', encoding='utf-8') as file:
            complexity_data = yaml.safe_load(file)
            
        # Noneの場合は空の辞書を返す
        if complexity_data is None:
            return {}
            
        return complexity_data
    except Exception as e:
        # エラーメッセージを直接表示せず、エラー情報を返す
        print(f"メカニクスデータの読み込みエラー: {str(e)}")
        return {}

def save_mechanics_data(complexity_data):
    """
    メカニクスの複雑さデータをYAMLファイルに保存する
    
    Parameters:
    complexity_data (dict): メカニクス名をキー、複雑さを値とする辞書
    
    Returns:
    bool: 保存が成功したかどうか
    """
    try:
        with open(MECHANICS_DATA_FILE, 'w', encoding='utf-8') as file:
            yaml.dump(complexity_data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        print(f"メカニクスデータの保存エラー: {str(e)}")
        return False

def add_missing_mechanic(mechanic_name, default_complexity=2.5):
    """
    存在しないメカニクスをYAMLファイルに追加する
    
    Parameters:
    mechanic_name (str): 追加するメカニクス名
    default_complexity (float): デフォルトの複雑さ値（未設定）
    
    Returns:
    bool: 追加が成功したかどうか
    """
    try:
        # 現在のデータを読み込む
        complexity_data = load_mechanics_data()
        
        # 既に存在する場合は何もしない
        if mechanic_name in complexity_data:
            return True
        
        # 存在しない場合は追加
        complexity_data[mechanic_name] = default_complexity
        
        # 保存
        return save_mechanics_data(complexity_data)
    except Exception as e:
        print(f"メカニクスの追加エラー: {str(e)}")
        return False

def get_complexity(mechanic_name, default_value=2.5):
    """
    指定されたメカニクスの複雑さを取得する
    存在しない場合はデフォルト値を返し、自動的にデータベースに追加する
    
    Parameters:
    mechanic_name (str): 複雑さを取得するメカニクス名
    default_value (float): 存在しない場合のデフォルト値
    
    Returns:
    float: メカニクスの複雑さ
    """
    complexity_data = load_mechanics_data()
    
    # メカニクスが存在するか確認
    if mechanic_name in complexity_data:
        return complexity_data[mechanic_name]
    
    # 存在しない場合は追加して保存
    add_missing_mechanic(mechanic_name, default_value)
    
    return default_value

# データが空の場合はサンプルデータを提供
def initialize_mechanics_data():
    """
    メカニクスデータが存在しない場合、初期データを作成する
    """
    if not os.path.exists(MECHANICS_DATA_FILE) or os.path.getsize(MECHANICS_DATA_FILE) == 0:
        # サンプルデータを現在のCOMPLEXITY_BY_MECHANICから取得
        sample_data = {
            "Resource Management": 3.2,
            "Engine Building": 3.8,
            "Income": 2.3,
            # 他のメカニクスデータ...
            'Turn Order: Progressive': 2.3,
            'Turn Order: Claim Action': 2.6,
            'Turn Order: Pass Order': 2.7,
            # 残りのデータ...
        }
        save_mechanics_data(sample_data)

# プログラム起動時にデータの初期化を行う
initialize_mechanics_data()

# 後方互換性のため、グローバル辞書を維持
COMPLEXITY_BY_MECHANIC = load_mechanics_data()