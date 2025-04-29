#!/usr/bin/env python3
"""
毎日0時に実行するBoardgame Analyzerのデータ更新スクリプト
- YAMLデータをbackupフォルダにYYMMDD形式で保存する
- ローカルのYAMLファイルからゲームIDリストを取得する
- BGG APIを使用して各ゲームの詳細情報を取得し直す
- configファイルの更新があれば、変更内容をログに出力する
"""

import os
import sys
import shutil
import yaml
import requests
import time
import datetime
import logging
import difflib
from pathlib import Path
import re

# Boardgame Analyzer のモジュールをインポート
sys.path.append('')
from src.api.bgg_api import get_game_details
from src.data.data_handler import save_game_data_to_yaml

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/daily_update.log',
    filemode='a'
)
logger = logging.getLogger('daily_update')

# 定数
BASE_DIR = Path('')
GAME_DATA_DIR = BASE_DIR / 'game_data'
CONFIG_DIR = BASE_DIR / 'config'
BACKUP_DIR = BASE_DIR / 'backup'
LOGS_DIR = BASE_DIR / 'logs'

def setup_directories():
    """必要なディレクトリを作成"""
    GAME_DATA_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)

def backup_game_data():
    """
    game_dataをバックアップする
    
    Returns:
    tuple: (成功フラグ, バックアップディレクトリのパス)
    """
    today = datetime.datetime.now()
    backup_folder_name = today.strftime('%y%m%d')
    
    backup_dir = BACKUP_DIR / backup_folder_name
    
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
    
    return True, backup_dir

def get_file_content(file_path):
    """ファイルの内容を取得する"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"ファイル読み込みエラー: {str(e)}")
        return ""

def check_config_updated():
    """
    configファイルが更新されたかをチェック
    更新があった場合は変更内容をログに出力
    
    Returns:
    tuple: (更新フラグ, 更新内容の説明)
    """
    updated = False
    update_details = []
    
    # 前回のバックアップを探す（最新のもの）
    previous_backups = sorted([d for d in BACKUP_DIR.glob('*') if d.is_dir()], reverse=True)
    if not previous_backups:
        logger.info("前回のバックアップが見つかりません。初回実行とみなします。")
        return False, "初回実行"
    
    # 最新のバックアップディレクトリを取得
    last_backup = previous_backups[0]
    last_config_backup = last_backup / 'config'
    
    # 前回のバックアップにconfigフォルダがない場合
    if not last_config_backup.exists():
        logger.info("前回のバックアップにconfigフォルダがありません")
        return False, "前回のconfigバックアップなし"
    
    # 各configファイルを比較
    for file in CONFIG_DIR.glob('*.yaml'):
        old_file = last_config_backup / file.name
        
        if not old_file.exists():
            # 新しいファイルが追加された場合
            updated = True
            update_details.append(f"新規ファイル追加: {file.name}")
            continue
        
        # ファイル内容を比較
        old_content = get_file_content(old_file)
        new_content = get_file_content(file)
        
        if old_content != new_content:
            updated = True
            
            # diffを取得して変更内容を詳細に記録
            diff = list(difflib.unified_diff(
                old_content.splitlines(),
                new_content.splitlines(),
                fromfile=str(old_file),
                tofile=str(file),
                lineterm=''
            ))
            
            update_details.append(f"ファイル変更: {file.name}")
            for line in diff[:20]:  # 最初の20行のdiffだけ表示（長すぎるのを防ぐ）
                update_details.append(f"  {line}")
            
            if len(diff) > 20:
                update_details.append(f"  ... その他 {len(diff) - 20} 行の変更があります")
    
    # CONFIG_DIRにあるがlast_config_backupにないファイルを探す（新規追加）
    for old_file in last_config_backup.glob('*.yaml'):
        new_file = CONFIG_DIR / old_file.name
        if not new_file.exists():
            updated = True
            update_details.append(f"ファイル削除: {old_file.name}")
    
    return updated, "\n".join(update_details)

def backup_config_files(backup_dir):
    """
    現在のconfigファイルをバックアップする
    
    Parameters:
    backup_dir (Path): バックアップディレクトリ
    """
    config_backup_dir = backup_dir / 'config'
    config_backup_dir.mkdir(exist_ok=True)
    
    for file in CONFIG_DIR.glob('*.yaml'):
        shutil.copy2(file, config_backup_dir)
    
    logger.info(f"configファイルをバックアップしました: {config_backup_dir}")

def get_game_ids_from_local():
    """ローカルのYAMLファイルからゲームIDを抽出して返す"""
    game_ids = []
    
    # game_dataフォルダからYAMLファイルを探す
    yaml_files = list(GAME_DATA_DIR.glob('*.yaml'))
    
    if not yaml_files:
        logger.warning(f"YAMLファイルが見つかりません: {GAME_DATA_DIR}")
        return []
    
    for yaml_file in yaml_files:
        # ファイル名からゲームIDを抽出 (例: "000013_カタンの開拓者.yaml")
        match = re.match(r"(\d+)_.*\.yaml", yaml_file.name)
        if match:
            game_id = match.group(1)
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
        
        # データをバックアップ
        backup_success, backup_dir = backup_game_data()
        if not backup_success:
            logger.error("バックアップ処理に失敗しました")
            return
        
        # configファイルが更新されたかチェック
        config_updated, update_details = check_config_updated()
        
        # configファイルをバックアップ（毎回行う）
        backup_config_files(backup_dir)
        
        # configの更新があった場合はログに詳細を記録
        if config_updated:
            logger.info("configファイルに更新がありました:")
            logger.info(update_details)
            
            # バックアップフォルダにマーカーファイルを作成
            config_update_marker = backup_dir / 'CONFIG_UPDATED.txt'
            with open(config_update_marker, 'w', encoding='utf-8') as f:
                f.write(f"Config files updated on {datetime.datetime.now()}\n\n")
                f.write(update_details)
            
            logger.info(f"configの更新マーカーファイルを作成: {config_update_marker}")
        
        # ローカルYAMLファイルからゲームIDを取得
        game_ids = get_game_ids_from_local()
        if not game_ids:
            logger.error("ローカルからゲームIDを取得できませんでした")
            return
        
        # ゲームデータを更新
        success_count, error_count = update_game_data(game_ids)
        logger.info(f"データ更新完了 - 成功: {success_count}, 失敗: {error_count}")
        
        logger.info("日次更新処理が完了しました")
    
    except Exception as e:
        logger.error(f"処理中に予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    main()