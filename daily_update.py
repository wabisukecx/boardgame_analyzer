#!/usr/bin/env python3
"""
毎日0時に実行するBoardgame Analyzerのデータ更新スクリプト
- 前日のゲームデータをバックアップする
- ローカルのYAMLファイルからゲームIDリストを取得する
- BGG APIを使用して各ゲームの詳細情報を取得し直す
- configファイルの更新があれば、バックアップフォルダ名を変更する
"""

import os
import sys
import shutil
import yaml
import requests
import time
import datetime
import logging
from pathlib import Path
import re

# Boardgame Analyzer のモジュールをインポート
sys.path.append('/home/pi/boardgame_analyzer')
from src.api.bgg_api import get_game_details
from src.data.data_handler import save_game_data_to_yaml

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='/home/pi/boardgame_analyzer/logs/daily_update.log',
    filemode='a'
)
logger = logging.getLogger('daily_update')

# 定数
BASE_DIR = Path('/home/pi/boardgame_analyzer')
GAME_DATA_DIR = BASE_DIR / 'game_data'
CONFIG_DIR = BASE_DIR / 'config'
CONFIG_BACKUP_DIR = BASE_DIR / 'config_backup'
LOGS_DIR = BASE_DIR / 'logs'

def setup_directories():
    """必要なディレクトリを作成"""
    GAME_DATA_DIR.mkdir(exist_ok=True)
    CONFIG_BACKUP_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)

def backup_game_data():
    """前日までのgame_dataをバックアップする"""
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    backup_folder_name = yesterday.strftime('%y%m%d')
    
    backup_dir = BASE_DIR / f'backup_{backup_folder_name}'
    
    # game_dataフォルダが存在するか確認
    if not GAME_DATA_DIR.exists():
        logger.warning(f"ゲームデータフォルダが見つかりません: {GAME_DATA_DIR}")
        return False, None
    
    # バックアップフォルダを作成
    os.makedirs(backup_dir, exist_ok=True)
    
    # game_dataの内容をバックアップ
    file_count = 0
    for file in GAME_DATA_DIR.glob('*.yaml'):
        shutil.copy2(file, backup_dir)
        file_count += 1
    
    logger.info(f"{file_count}個のYAMLファイルをバックアップしました: {backup_dir}")
    
    # game_dataディレクトリをクリア
    for file in GAME_DATA_DIR.glob('*.yaml'):
        os.remove(file)
    
    logger.info("game_dataディレクトリをクリアしました")
    return True, backup_dir

def check_config_updated():
    """configファイルが更新されたかをチェック"""
    # 初回実行時のバックアップ作成
    if not CONFIG_BACKUP_DIR.exists():
        os.makedirs(CONFIG_BACKUP_DIR, exist_ok=True)
        for file in CONFIG_DIR.glob('*.yaml'):
            shutil.copy2(file, CONFIG_BACKUP_DIR / file.name)
        return False
    
    # 各configファイルを比較
    updated = False
    for file in CONFIG_DIR.glob('*.yaml'):
        backup_file = CONFIG_BACKUP_DIR / file.name
        
        if not backup_file.exists():
            # バックアップに無いファイルがある場合
            shutil.copy2(file, backup_file)
            updated = True
            continue
        
        # ファイル内容を比較
        with open(file, 'r', encoding='utf-8') as f1, open(backup_file, 'r', encoding='utf-8') as f2:
            if f1.read() != f2.read():
                updated = True
                # バックアップを更新
                shutil.copy2(file, backup_file)
    
    return updated

def rename_backup_folder_if_config_updated(backup_folder):
    """configが更新された場合、バックアップフォルダ名を変更"""
    if check_config_updated():
        new_name = f"{backup_folder}_config_update"
        os.rename(backup_folder, new_name)
        logger.info(f"configファイルが更新されたためフォルダ名を変更: {new_name}")
        return new_name
    return backup_folder

def get_game_ids_from_local():
    """ローカルのYAMLファイルからゲームIDを抽出して返す"""
    game_ids = []
    
    # backup_フォルダからYAMLファイルを探す（前日のバックアップから取得）
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    backup_folder_name = yesterday.strftime('%y%m%d')
    backup_dir = BASE_DIR / f'backup_{backup_folder_name}'
    
    # 前日のバックアップフォルダが見つからない場合は最新のバックアップフォルダを探す
    if not backup_dir.exists():
        backup_dirs = list(BASE_DIR.glob('backup_*'))
        if backup_dirs:
            # 名前順で最新のバックアップを使用
            backup_dirs.sort(reverse=True)
            backup_dir = backup_dirs[0]
            logger.info(f"昨日のバックアップが見つからないため、最新のバックアップを使用します: {backup_dir}")
        else:
            # バックアップが1つも見つからない場合はgame_dataフォルダ内を確認
            backup_dir = GAME_DATA_DIR
            logger.info(f"バックアップフォルダが見つからないため、game_dataフォルダを使用します: {backup_dir}")
    
    # 指定されたディレクトリ内の全YAMLファイルからゲームIDを抽出
    yaml_files = list(backup_dir.glob('*.yaml'))
    
    if not yaml_files:
        logger.warning(f"YAMLファイルが見つかりません: {backup_dir}")
        return []
    
    for yaml_file in yaml_files:
        # ファイル名からゲームIDを抽出 (例: "000013_カタンの開拓者.yaml")
        match = re.match(r"(\d+)_.*\.yaml", yaml_file.name)
        if match:
            game_id = match.group(1).lstrip('0')  # 先頭のゼロを削除
            if game_id:
                game_ids.append(game_id)
    
    logger.info(f"ローカルから{len(game_ids)}個のゲームIDを取得しました")
    return game_ids

def update_game_data(game_ids):
    """ゲームデータを更新する"""
    success_count = 0
    error_count = 0
    
    for i, game_id in enumerate(game_ids):
        try:
            logger.info(f"ゲームデータ取得中 ({i+1}/{len(game_ids)}): {game_id}")
            
            # BGG APIからゲーム詳細を取得
            game_details = get_game_details(game_id)
            
            if not game_details:
                logger.warning(f"ゲームID {game_id} の詳細情報が取得できませんでした")
                error_count += 1
                continue
            
            # YAMLファイルに保存
            success, file_path, error_msg = save_game_data_to_yaml(game_details)
            
            if success:
                logger.info(f"ゲームID {game_id} の情報を保存しました: {file_path}")
                success_count += 1
            else:
                logger.error(f"ゲームID {game_id} の保存に失敗: {error_msg}")
                error_count += 1
            
            # rate_limiterが実装されているはずだが、念のため追加の間隔をあける
            time.sleep(1)
        
        except Exception as e:
            logger.error(f"ゲームID {game_id} の処理中にエラー: {e}")
            error_count += 1
    
    return success_count, error_count

def main():
    """メイン処理"""
    logger.info("日次更新処理を開始します")
    
    try:
        # 必要なディレクトリを作成
        setup_directories()
        
        # 前日までのデータをバックアップ
        backup_success, backup_folder = backup_game_data()
        if not backup_success:
            logger.error("バックアップ処理に失敗しました")
            return
        
        # ローカルYAMLファイルからゲームIDを取得
        game_ids = get_game_ids_from_local()
        if not game_ids:
            logger.error("ローカルからゲームIDを取得できませんでした")
            return
        
        # ゲームデータを更新
        success_count, error_count = update_game_data(game_ids)
        logger.info(f"データ更新完了 - 成功: {success_count}, 失敗: {error_count}")
        
        # configファイルが更新されたかチェックしてバックアップフォルダ名を変更
        rename_backup_folder_if_config_updated(backup_folder)
        
        logger.info("日次更新処理が完了しました")
    
    except Exception as e:
        logger.error(f"処理中に予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    main()