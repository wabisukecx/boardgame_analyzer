import os
import yaml
from datetime import datetime, timedelta

# YAMLファイルのパス
MECHANICS_DATA_FILE = "config/mechanics_data.yaml"

# キャッシュ用のグローバル変数
_mechanics_cache = None
_mechanics_cache_timestamp = None
_mechanics_cache_ttl = timedelta(minutes=10)  # キャッシュの有効期間（10分）

def load_mechanics_data(force_reload=False):
    """
    メカニクスの複雑さデータをYAMLファイルから読み込む
    キャッシュを活用して読み込み回数を削減
    
    Parameters:
    force_reload (bool): キャッシュを無視して強制的に再読み込みする
    
    Returns:
    dict: メカニクス名をキー、複雑さを値とする辞書
    """
    global _mechanics_cache, _mechanics_cache_timestamp
    
    current_time = datetime.now()
    
    # キャッシュが有効な場合はキャッシュから返す
    if not force_reload and _mechanics_cache is not None and _mechanics_cache_timestamp is not None:
        if current_time - _mechanics_cache_timestamp < _mechanics_cache_ttl:
            return _mechanics_cache
    
    try:
        # ファイルが存在しない場合は空の辞書を返す
        if not os.path.exists(MECHANICS_DATA_FILE):
            _mechanics_cache = {}
            _mechanics_cache_timestamp = current_time
            return _mechanics_cache
        
        with open(MECHANICS_DATA_FILE, 'r', encoding='utf-8') as file:
            complexity_data = yaml.safe_load(file)
            
        # Noneの場合は空の辞書を返す
        if complexity_data is None:
            complexity_data = {}
            
        # キャッシュを更新
        _mechanics_cache = complexity_data
        _mechanics_cache_timestamp = current_time
            
        return complexity_data
    except Exception as e:
        print(f"メカニクスデータの読み込みエラー: {str(e)}")
        return {}

def save_mechanics_data(complexity_data):
    """
    メカニクスの複雑さデータをYAMLファイルに保存する
    保存後はキャッシュを更新
    
    Parameters:
    complexity_data (dict): メカニクス名をキー、複雑さを値とする辞書
    
    Returns:
    bool: 保存が成功したかどうか
    """
    global _mechanics_cache, _mechanics_cache_timestamp
    
    try:
        with open(MECHANICS_DATA_FILE, 'w', encoding='utf-8') as file:
            yaml.dump(complexity_data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        # キャッシュを更新
        _mechanics_cache = complexity_data
        _mechanics_cache_timestamp = datetime.now()
        
        return True
    except Exception as e:
        print(f"メカニクスデータの保存エラー: {str(e)}")
        return False

# 新規メカニクス追加の一時保存用バッファ
_pending_mechanics = {}
_pending_mechanics_count = 0
_max_pending_mechanics = 10  # この数に達すると一括保存

def add_missing_mechanic(mechanic_name, default_complexity=2.5):
    """
    存在しないメカニクスをバッファに追加し、バッファがいっぱいになったら一括保存
    
    Parameters:
    mechanic_name (str): 追加するメカニクス名
    default_complexity (float): デフォルトの複雑さ値
    
    Returns:
    bool: 追加処理が成功したかどうか
    """
    global _pending_mechanics, _pending_mechanics_count
    
    try:
        # 現在のデータを読み込む（キャッシュから）
        complexity_data = load_mechanics_data()
        
        # 既に存在する場合は何もしない
        if mechanic_name in complexity_data:
            return True
        
        # 既にバッファにある場合も何もしない
        if mechanic_name in _pending_mechanics:
            return True
        
        # バッファに追加
        _pending_mechanics[mechanic_name] = {
            'complexity': default_complexity,
            'strategic_value': 3.0,
            'interaction_value': 3.0,
            'description': f"自動追加されたメカニクス（デフォルト値）"
        }
        
        _pending_mechanics_count += 1
        
        # バッファがいっぱいになったら一括保存
        if _pending_mechanics_count >= _max_pending_mechanics:
            return _save_pending_mechanics()
        
        return True
    except Exception as e:
        print(f"メカニクスの追加エラー: {str(e)}")
        return False

def _save_pending_mechanics():
    """バッファにあるすべての保留中のメカニクスを一括保存"""
    global _pending_mechanics, _pending_mechanics_count
    
    if _pending_mechanics_count == 0:
        return True
        
    try:
        # 現在のデータを読み込む（強制リロード）
        complexity_data = load_mechanics_data(force_reload=True)
        
        # バッファの内容を追加
        for mechanic_name, mechanic_data in _pending_mechanics.items():
            if mechanic_name not in complexity_data:
                complexity_data[mechanic_name] = mechanic_data
        
        # 保存
        success = save_mechanics_data(complexity_data)
        
        if success:
            # バッファをクリア
            _pending_mechanics = {}
            _pending_mechanics_count = 0
            
        return success
    except Exception as e:
        print(f"保留中メカニクスの保存エラー: {str(e)}")
        return False

def get_complexity(mechanic_name, default_value=2.5):
    """
    指定されたメカニクスの複雑さを取得する
    キャッシュから取得し、存在しない場合はバッファに追加
    
    Parameters:
    mechanic_name (str): 複雑さを取得するメカニクス名
    default_value (float): 存在しない場合のデフォルト値
    
    Returns:
    float: メカニクスの複雑さ
    """
    # まずバッファをチェック
    global _pending_mechanics
    
    if mechanic_name in _pending_mechanics:
        pending_data = _pending_mechanics[mechanic_name]
        if isinstance(pending_data, dict) and 'complexity' in pending_data:
            return pending_data['complexity']
        elif isinstance(pending_data, (int, float)):
            return pending_data
        else:
            return default_value
    
    # キャッシュからデータを取得
    complexity_data = load_mechanics_data()
    
    # メカニクスが存在するか確認
    if mechanic_name in complexity_data:
        if isinstance(complexity_data[mechanic_name], dict) and 'complexity' in complexity_data[mechanic_name]:
            return complexity_data[mechanic_name]['complexity']
        elif isinstance(complexity_data[mechanic_name], (int, float)):
            return complexity_data[mechanic_name]
        else:
            return default_value
    
    # 存在しない場合はバッファに追加
    add_missing_mechanic(mechanic_name, default_value)
    
    return default_value

# アプリケーション終了時にバッファをフラッシュする関数
def flush_pending_mechanics():
    """保留中のすべてのメカニクスを保存する"""
    return _save_pending_mechanics()