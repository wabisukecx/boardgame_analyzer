import os
import yaml
import streamlit as st
import pandas as pd
from learning_curve import calculate_learning_curve

def save_game_data_to_yaml(game_data, custom_filename=None):
    """
    ゲームデータをYAMLファイルに保存する
    
    Parameters:
    game_data (dict): 保存するゲームデータ
    custom_filename (str, optional): カスタムファイル名
    
    Returns:
    tuple: (成功フラグ, ファイルパス, エラーメッセージ)
    """
    # ファイル名の生成
    game_id = game_data.get('id', 'unknown')
    
    # 日本語名がある場合は優先して使用
    game_name = game_data.get('japanese_name', game_data.get('name', '名称不明'))
    
    # プレースホルダーファイル名
    placeholder_filename = f"{game_id}_{game_name}.yaml"
    # 特殊文字を置換
    placeholder_filename = placeholder_filename.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace(";", "_")
    
    # カスタムファイル名の処理
    if not custom_filename:
        filename = placeholder_filename
    else:
        filename = custom_filename
        if not filename.endswith('.yaml'):
            filename += '.yaml'
    
    # データディレクトリの作成
    os.makedirs("game_data", exist_ok=True)
    file_path = os.path.join("game_data", filename)
    
    try:
        # YAMLに変換して保存する前にゲーム名に特殊文字がある場合の対応
        game_data_safe = game_data.copy()
        
        # トップレベルのIDを削除
        if 'id' in game_data_safe:
            del game_data_safe['id']
        
        # ネストされた要素からIDを削除
        for category in ['mechanics', 'categories', 'designers', 'publishers', 'ranks']:
            if (category in game_data_safe and isinstance(game_data_safe[category], list)):
                for item in game_data_safe[category]:
                    if 'id' in item:
                        del item['id']
        
        # ラーニングカーブ情報を追加（まだない場合のみ）
        if ('learning_analysis' not in game_data_safe and 
            'description' in game_data_safe and 
            'mechanics' in game_data_safe and 
            'weight' in game_data_safe):
            game_data_safe['learning_analysis'] = calculate_learning_curve(game_data_safe)
        
        # YAMLに変換して保存
        with open(file_path, 'w', encoding='utf-8') as file:
            yaml.dump(game_data_safe, file, default_flow_style=False, allow_unicode=True)
        
        return True, file_path, None
    except Exception as e:
        return False, None, str(e)

def load_game_data_from_yaml(file_path):
    """
    YAMLファイルからゲームデータを読み込む
    
    Parameters:
    file_path (str): YAMLファイルのパス
    
    Returns:
    dict: ゲームデータ
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            game_data = yaml.safe_load(file)
        return game_data
    except Exception as e:
        st.error(f"ファイル読み込みエラー: {str(e)}")
        return None

def search_results_to_dataframe(results):
    """
    検索結果をDataFrameに変換する
    
    Parameters:
    results (list): 検索結果のリスト
    
    Returns:
    pandas.DataFrame: 検索結果のDataFrame
    """
    if not results:
        return None
    
    # DataFrameに変換
    df = pd.DataFrame(results)
    
    # 列名を日本語に変換
    df = df.rename(columns={
        "id": "ゲームID",
        "name": "ゲーム名",
        "year_published": "発行年"
    })
    
    # NaNを「不明」に置き換え
    df = df.fillna("不明")
    
    # 不要な列を削除
    if "type" in df.columns:
        df = df.drop(columns=["type"])
    
    return df