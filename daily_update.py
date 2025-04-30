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
import random
import xml.etree.ElementTree as ET
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/daily_update.log',
    filemode='a'
)
logger = logging.getLogger('daily_update')

# 定数
BASE_DIR = Path('.')
GAME_DATA_DIR = BASE_DIR / 'game_data'
CONFIG_DIR = BASE_DIR / 'config'
BACKUP_DIR = BASE_DIR / 'backup'
LOGS_DIR = BASE_DIR / 'logs'

# API呼び出し用のキャッシュとレート制限 
_cache = {}
_cache_ttl = {}
_request_history = []

# シンプルなキャッシュ実装
def simple_cache(ttl_hours=24):
    """シンプルなキャッシュ機能を提供するデコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # キャッシュキーを生成
            key = str(args) + str(sorted(kwargs.items()))
            key_hash = hash(key)
            cache_key = f"{func.__name__}_{key_hash}"
            
            # キャッシュが有効な場合はキャッシュから返す
            current_time = time.time()
            if cache_key in _cache and _cache_ttl.get(cache_key, 0) > current_time:
                logger.debug(f"キャッシュからデータを返します: {cache_key}")
                return _cache[cache_key]
            
            # キャッシュがない場合や期限切れの場合は関数を実行
            result = func(*args, **kwargs)
            
            # 結果をキャッシュに保存
            _cache[cache_key] = result
            # 有効期限を設定（秒単位）
            _cache_ttl[cache_key] = current_time + (ttl_hours * 3600)
            
            return result
        return wrapper
    return decorator

# レート制限実装
def rate_limited_request(max_per_minute=15, max_retries=3):
    """BGG APIリクエストをレート制限するデコレータ"""
    # リクエスト間の最小間隔を計算
    min_interval = 60.0 / max_per_minute
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            global _request_history
            
            # 1分以上経過したリクエスト履歴を削除
            current_time = time.time()
            one_minute_ago = current_time - 60
            _request_history = [t for t in _request_history if t > one_minute_ago]
            
            # 過去1分間のリクエスト数をチェック
            if len(_request_history) >= max_per_minute:
                # min_intervalを使用して均等にリクエストを分散
                oldest_request = min(_request_history) if _request_history else current_time - 60
                time_since_oldest = current_time - oldest_request
                # 経過時間に基づく待機時間を計算
                wait_time = max(0, min_interval - (time_since_oldest / max(1, len(_request_history)))) + random.uniform(0.1, 1.0)
                
                if wait_time > 0:
                    logger.info(f"BGG APIレート制限に達しました。{wait_time:.1f}秒待機しています...")
                    time.sleep(wait_time)
            
            # ジッター（ばらつき）を追加して、同時リクエストを避ける
            jitter = random.uniform(0.2, 1.0)
            time.sleep(jitter)
            
            # リクエスト実行（再試行ロジック付き）
            retries = 0
            while retries <= max_retries:
                try:
                    # リクエスト履歴を記録
                    _request_history.append(time.time())
                    
                    # 実際の関数呼び出し
                    result = func(*args, **kwargs)
                    return result
                    
                except requests.exceptions.HTTPError as e:
                    retries += 1
                    if e.response.status_code == 429:  # Too Many Requests
                        # レート制限エラーの場合
                        retry_after = int(e.response.headers.get('Retry-After', 30))
                        wait_time = retry_after + random.uniform(1, 5)
                        
                        logger.warning(f"BGG APIレート制限に達しました。{wait_time:.1f}秒待機しています... (試行 {retries}/{max_retries})")
                        time.sleep(wait_time)
                    
                    elif e.response.status_code >= 500:
                        # サーバーエラーの場合はバックオフして再試行
                        wait_time = (2 ** retries) + random.uniform(0, 1)
                        
                        logger.warning(f"BGG APIサーバーエラー (ステータス {e.response.status_code})。{wait_time:.1f}秒後に再試行します... (試行 {retries}/{max_retries})")
                        time.sleep(wait_time)
                    
                    else:
                        # その他のHTTPエラー
                        logger.error(f"API呼び出しエラー: {e.response.status_code} - {e.response.reason}")
                        raise
                
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    # 接続エラーやタイムアウトの場合
                    retries += 1
                    wait_time = (2 ** retries) + random.uniform(0, 1)
                    
                    # 例外の種類に基づいてエラーメッセージを調整
                    error_type = "タイムアウト" if isinstance(e, requests.exceptions.Timeout) else "接続エラー"
                    logger.warning(f"{error_type}が発生しました。{wait_time:.1f}秒後に再試行します... (試行 {retries}/{max_retries})")
                    time.sleep(wait_time)
                    
                # 最大再試行回数に達した場合
                if retries > max_retries:
                    logger.error(f"最大再試行回数({max_retries})に達しました。後でもう一度お試しください。")
                    raise Exception("APIリクエストの最大再試行回数に達しました")
        
        return wrapper
    return decorator

@simple_cache(ttl_hours=48)
@rate_limited_request(max_per_minute=15)
def get_game_details(game_id):
    """ゲームの詳細情報を取得する"""
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={game_id}&stats=1"
    logger.info(f"ゲームID {game_id} の詳細情報を取得中...")
    
    response = requests.get(url)
    
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        game = {}
        
        item = root.find(".//item")
        if item is not None:
            game["id"] = item.get("id")
            game["type"] = item.get("type")
            
            # プライマリ名を取得
            name_element = item.find(".//name[@type='primary']")
            if name_element is not None:
                game["name"] = name_element.get("value")
            
            # 代替名（日本語名を含む）を取得
            alternate_names = []
            for name_elem in item.findall(".//name"):
                name_value = name_elem.get("value")
                name_type = name_elem.get("type")
                
                # プライマリ名は既に取得済みなのでスキップ
                if name_type == "primary":
                    continue
                
                alternate_names.append(name_value)
                
                # 言語属性がある場合はチェック
                if "language" in name_elem.attrib:
                    lang = name_elem.get("language")
                    if lang == "ja" or lang == "jp" or lang == "jpn":
                        game["japanese_name"] = name_value
            
            if alternate_names:
                game["alternate_names"] = alternate_names
                
                # 日本語タイトルがまだ見つかっていない場合
                if "japanese_name" not in game:
                    # 日本語文字を含むものを探す
                    for alt_name in alternate_names:
                        # ひらがなかカタカナが含まれているか確認（より信頼性が高い日本語判定）
                        has_japanese = any(
                            '\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF'
                            for c in alt_name
                        )
                        if has_japanese:
                            game["japanese_name"] = alt_name
                            break
            
            # 発行年を取得
            year_element = item.find(".//yearpublished")
            if year_element is not None:
                game["year_published"] = year_element.get("value")
            
            # サムネイルURLを取得
            thumbnail_element = item.find(".//thumbnail")
            if thumbnail_element is not None and thumbnail_element.text:
                game["thumbnail_url"] = thumbnail_element.text
            
            # パブリッシャー設定のプレイ人数を取得
            minplayers_element = item.find(".//minplayers")
            if minplayers_element is not None:
                game["publisher_min_players"] = minplayers_element.get("value")
                
            maxplayers_element = item.find(".//maxplayers")
            if maxplayers_element is not None:
                game["publisher_max_players"] = maxplayers_element.get("value")
                
            # パブリッシャー設定のプレイ時間を取得
            playtime_element = item.find(".//playingtime")
            if playtime_element is not None:
                game["playing_time"] = playtime_element.get("value")
                
            # パブリッシャー設定の推奨年齢を取得
            age_element = item.find(".//minage")
            if age_element is not None:
                game["publisher_min_age"] = age_element.get("value")
                
            # BGGコミュニティの推奨プレイ人数を取得
            poll = item.findall(".//poll[@name='suggested_numplayers']/results")
            community_players = {"best": [], "recommended": [], "not_recommended": []}
            
            for numplayer_result in poll:
                num_players = numplayer_result.get("numplayers")
                
                # 最も投票が多い推奨度を見つける
                best_votes = 0
                best_recommendation = "not_recommended"
                
                for result in numplayer_result.findall("./result"):
                    vote_count = int(result.get("numvotes", "0"))
                    value = result.get("value")
                    
                    if vote_count > best_votes:
                        best_votes = vote_count
                        best_recommendation = value
                
                # 推奨度に基づいてプレイ人数を分類
                if best_recommendation == "Best":
                    community_players["best"].append(num_players)
                elif best_recommendation == "Recommended":
                    community_players["recommended"].append(num_players)
                elif best_recommendation == "Not Recommended":
                    community_players["not_recommended"].append(num_players)
            
            # 最適人数を設定
            if community_players["best"]:
                # 数値として解釈できる場合にソート
                try:
                    community_players["best"] = sorted(
                        community_players["best"],
                        key=lambda x: float(x.replace("+", ""))
                    )
                except ValueError:
                    pass
                game["community_best_players"] = ", ".join(community_players["best"])
            
            if community_players["recommended"]:
                try:
                    community_players["recommended"] = sorted(
                        community_players["recommended"],
                        key=lambda x: float(x.replace("+", ""))
                    )
                except ValueError:
                    pass
                game["community_recommended_players"] = ", ".join(
                    community_players["recommended"]
                )
            
            # BGGコミュニティの推奨年齢を取得
            suggested_age_poll = item.find(".//poll[@name='suggested_playerage']")
            if suggested_age_poll is not None:
                age_results = suggested_age_poll.findall("./results/result")
                best_age_votes = 0
                community_age = None
                
                for age_result in age_results:
                    vote_count = int(age_result.get("numvotes", "0"))
                    age_value = age_result.get("value")
                    
                    if vote_count > best_age_votes:
                        best_age_votes = vote_count
                        community_age = age_value
                
                if community_age:
                    game["community_min_age"] = community_age
            
            # 説明文を取得
            description_element = item.find(".//description")
            if description_element is not None and description_element.text:
                game["description"] = description_element.text
            
            # メカニクス（ゲームの種類）を取得
            mechanics = []
            for mechanic in item.findall(".//link[@type='boardgamemechanic']"):
                mechanics.append({
                    "id": mechanic.get("id"),
                    "name": mechanic.get("value")
                })
            game["mechanics"] = mechanics
            
            # カテゴリを取得
            categories = []
            for category in item.findall(".//link[@type='boardgamecategory']"):
                categories.append({
                    "id": category.get("id"),
                    "name": category.get("value")
                })
            game["categories"] = categories
            
            # デザイナー情報を取得
            designers = []
            for designer in item.findall(".//link[@type='boardgamedesigner']"):
                designers.append({
                    "id": designer.get("id"),
                    "name": designer.get("value")
                })
            game["designers"] = designers
            
            # パブリッシャー情報を取得
            publishers = []
            for publisher in item.findall(".//link[@type='boardgamepublisher']"):
                publishers.append({
                    "id": publisher.get("id"),
                    "name": publisher.get("value")
                })
            game["publishers"] = publishers
            
            # 評価情報を取得
            ratings = item.find(".//ratings")
            if ratings is not None:
                avg_rating = ratings.find(".//average")
                if avg_rating is not None:
                    game["average_rating"] = avg_rating.get("value")
                
                # 重量（複雑さ）を取得
                weight_element = ratings.find(".//averageweight")
                if weight_element is not None:
                    game["weight"] = weight_element.get("value")
                
                # ランク情報
                ranks = []
                for rank in ratings.findall(".//rank"):
                    if rank.get("value") != "Not Ranked":
                        ranks.append({
                            "type": rank.get("name"),
                            "id": rank.get("id"),
                            "rank": rank.get("value")
                        })
                game["ranks"] = ranks
        
        return game
    else:
        logger.error(f"エラー: ステータスコード {response.status_code}")
        return None

def save_game_data_to_yaml(game_data, custom_filename=None):
    """ゲームデータをYAMLファイルに保存する"""
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

        # 学習曲線分析の追加（Streamlitの依存なしで実装）
        if ('learning_analysis' not in game_data_safe and 
            'description' in game_data_safe and 
            'mechanics' in game_data_safe and 
            'weight' in game_data_safe):
            try:
                # 独立したモジュールを使用して学習曲線分析を追加
                from learning_curve_for_daily_update import calculate_learning_curve
                game_data_safe['learning_analysis'] = calculate_learning_curve(game_data_safe)
                logger.info(f"ゲームID {game_id} の学習曲線分析を追加しました")
            except Exception as e:
                logger.warning(f"学習曲線の計算中にエラーが発生しました: {str(e)}")
        
        # YAMLに変換して保存する前に全角スペースを半角スペースに変換
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
            yaml.dump(game_data_safe, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return True, file_path, None
    except Exception as e:
        logger.error(f"ファイル保存エラー: {str(e)}")
        return False, None, str(e)

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
        match = re.match(r"(\d+)_(.*?)\.yaml", yaml_file.name)
        if match:
            game_id = match.group(1)
            if game_id:
                game_ids.append(game_id)
    
    logger.info(f"ローカルから{len(game_ids)}個のゲームIDを取得しました")
    return game_ids

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