import os
import yaml
import streamlit as st
import pandas as pd
import re
from src.analysis.learning_curve import calculate_learning_curve

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
    
    # ゲームIDを6桁に揃える処理を追加
    if game_id != 'unknown' and game_id.isdigit():
        game_id = game_id.zfill(6)  # 6桁になるように左側に0を埋める
    
    # 日本語名がある場合は優先して使用
    game_name = game_data.get('japanese_name', game_data.get('name', '名称不明'))
    
    # 全角スペースを半角スペースに変換
    game_name = game_name.replace('　', ' ')
    
    # プレースホルダーファイル名
    placeholder_filename = f"{game_id}_{game_name}.yaml"
    # 特殊文字を置換
    placeholder_filename = placeholder_filename.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace(";", "_")
    
    # カスタムファイル名の処理
    if not custom_filename:
        filename = placeholder_filename
    else:
        # カスタムファイル名も全角スペースを半角に変換
        custom_filename = custom_filename.replace('　', ' ')
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
        
        # YAMLに変換して保存する前に全角スペースを半角スペースに変換
        # ディープコピーして全角スペースを変換
        def replace_fullwidth_spaces(obj):
            if isinstance(obj, str):
                return obj.replace('　', ' ')
            elif isinstance(obj, dict):
                return {k: replace_fullwidth_spaces(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_fullwidth_spaces(item) for item in obj]
            else:
                return obj
        
        game_data_safe = replace_fullwidth_spaces(game_data_safe)
        
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

def load_all_game_data():
    """
    game_dataフォルダ内のすべてのYAMLファイルからゲームデータを読み込む
    
    Returns:
    dict: ゲームID(文字列)をキー、ゲームデータを値とする辞書
    """
    game_data_dict = {}
    
    # game_dataフォルダが存在するか確認
    if not os.path.exists("game_data"):
        return game_data_dict
    
    # YAMLファイルを検索
    for filename in os.listdir("game_data"):
        if filename.endswith(".yaml"):
            # ファイル名からゲームIDを抽出 (例: "167791_テラフォーミング・マーズ.yaml")
            match = re.match(r"(\d+)_(.*?)\.yaml", filename)
            if match:
                game_id = match.group(1)
                file_path = os.path.join("game_data", filename)
                
                # YAMLファイルを読み込む
                game_data = load_game_data_from_yaml(file_path)
                if game_data:
                    game_data_dict[game_id] = game_data
    
    return game_data_dict