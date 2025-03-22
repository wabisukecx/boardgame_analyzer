import yaml
import numpy as np
import os
import glob
import pickle
import voyageai
from sklearn.metrics.pairwise import cosine_similarity
import argparse
from tqdm import tqdm
from typing import Dict, List, Any, Tuple
import asyncio
from dotenv import load_dotenv
import hashlib
import time
import random

# 環境変数の読み込み
load_dotenv()

def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパースする関数"""
    parser = argparse.ArgumentParser(description='ボードゲームデータのエンベディングを計算して保存します')
    parser.add_argument('--model', default='voyage-3-large', 
                      help='エンベディングモデル名（デフォルト: voyage-3-large）')
    parser.add_argument('--data_path', default='game_data/*.yaml', 
                      help='ゲームデータのパス (glob形式)')
    parser.add_argument('--output', default='game_embeddings.pkl', 
                      help='出力ファイル名')
    parser.add_argument('--batch_size', type=int, default=128, 
                      help='APIリクエストのバッチサイズ（デフォルト: 128）')
    parser.add_argument('--max_retries', type=int, default=5,
                      help='APIリクエスト失敗時の再試行回数（デフォルト: 5）')
    parser.add_argument('--request_interval', type=float, default=0.5,
                      help='リクエスト間の待機時間（秒, デフォルト: 0.5）')
    parser.add_argument('--timeout', type=int, default=15,
                      help='APIリクエストのタイムアウト（秒, デフォルト: 15）')
    parser.add_argument('--limit', type=int, default=0,
                      help='処理するファイル数の上限（0=すべて処理）')
    parser.add_argument('--skip', type=int, default=0,
                      help='処理をスキップするファイル数')
    parser.add_argument('--resume', action='store_true',
                      help='前回の処理を途中から再開する（中間ファイルがある場合）')
    parser.add_argument('--force', action='store_true',
                      help='YAMLファイルに変更がなくても強制的に処理を実行する')
    return parser.parse_args()

def load_game_data(file_path: str) -> Dict[str, Any]:
    """YAMLファイルからゲームデータを読み込む関数"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"ファイル {file_path} の読み込みエラー: {e}")
        return {}

def create_game_text(game_data: Dict[str, Any]) -> str:
    """ゲームデータからエンベディング用のテキストを作成する関数（意味コンテキスト強化版）"""
    text = f"Board Game Name: {game_data.get('name', '')}\n"
    text += f"Game Description: {game_data.get('description', '')}\n"
    
    # カテゴリの追加
    if 'categories' in game_data and isinstance(game_data['categories'], list):
        categories = [cat.get('name', '') for cat in game_data['categories'] 
                     if isinstance(cat, dict) and 'name' in cat]
        text += f"Game Categories (game types and classifications): {', '.join(categories)}\n"
    
    # メカニクスの追加
    if 'mechanics' in game_data and isinstance(game_data['mechanics'], list):
        mechanics = [mech.get('name', '') for mech in game_data['mechanics'] 
                    if isinstance(mech, dict) and 'name' in mech]
        text += f"Game Mechanics (rules and systems that define gameplay): {', '.join(mechanics)}\n"
    
    # 戦略的深さの情報を追加
    if 'learning_analysis' in game_data and isinstance(game_data['learning_analysis'], dict):
        learning = game_data['learning_analysis']
        if 'strategic_depth_description' in learning:
            text += f"Strategic Depth Analysis (complexity of decision-making): {learning['strategic_depth_description']}\n"
    
    # 複雑さの情報を追加
    if 'weight' in game_data:
        text += f"Game Complexity (Weight): {game_data.get('weight', '')} on a scale of 1-5, where 5 is most complex\n"
    
    # 発売年を追加
    if 'year_published' in game_data:
        text += f"Year Published (original release date): {game_data.get('year_published', '')}\n"
    
    # プレイ時間を追加
    if 'playing_time' in game_data:
        text += f"Average Playing Time (duration of a typical game): {game_data.get('playing_time', '')} minutes\n"
    
    # プレイ人数を追加（あれば）
    if 'min_players' in game_data and 'max_players' in game_data:
        text += f"Player Count: {game_data.get('min_players', '')} to {game_data.get('max_players', '')} players\n"
    
    # 推奨年齢を追加（あれば）
    if 'min_age' in game_data:
        text += f"Recommended Minimum Age: {game_data.get('min_age', '')} years\n"
    
    # 日本語名を追加（あれば）
    if 'japanese_name' in game_data and game_data['japanese_name']:
        text += f"Japanese Title: {game_data.get('japanese_name', '')}\n"
    
    return text

def save_temp_result(embeddings, last_index, filename="temp_embeddings.pkl"):
    """一時的な結果を保存する関数"""
    try:
        with open(filename, 'wb') as f:
            pickle.dump({
                'embeddings': embeddings,
                'last_index': last_index
            }, f)
        print(f"一時的な結果を{filename}に保存しました（インデックス: {last_index}）")
    except Exception as e:
        print(f"一時ファイルの保存に失敗しました: {e}")

def load_temp_result(filename="temp_embeddings.pkl"):
    """一時的な結果を読み込む関数"""
    if os.path.exists(filename):
        try:
            with open(filename, 'rb') as f:
                data = pickle.load(f)
            print(f"一時的な結果を{filename}から読み込みました（インデックス: {data.get('last_index', 0)}）")
            return data.get('embeddings', []), data.get('last_index', 0)
        except Exception as e:
            print(f"一時ファイルの読み込みに失敗しました: {e}")
    return [], 0

def get_file_hash(file_path: str) -> str:
    """ファイルのハッシュ値を計算する関数"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        # ファイルが読み込めない場合は、現在時刻をハッシュ化して返す
        return hashlib.md5(str(time.time()).encode()).hexdigest()

def create_file_metadata(file_paths: List[str]) -> Dict[str, str]:
    """ファイルのメタデータ（ハッシュ値）を作成する関数"""
    metadata = {}
    for file_path in file_paths:
        metadata[file_path] = get_file_hash(file_path)
    return metadata

def load_previous_metadata(output_file: str) -> Dict[str, Any]:
    """前回の処理結果からメタデータを読み込む関数"""
    if not os.path.exists(output_file):
        return {}
        
    try:
        with open(output_file, 'rb') as f:
            data = pickle.load(f)
            return data.get('metadata', {})
    except Exception as e:
        print(f"前回の処理結果の読み込みエラー: {e}")
        return {}

def check_files_changed(new_metadata: Dict[str, str], old_metadata: Dict[str, str]) -> bool:
    """ファイルに変更があるかチェックする関数"""
    # ファイル数が変わっていればTrue
    if len(new_metadata) != len(old_metadata):
        return True
    
    # ハッシュ値を比較
    for file_path, hash_value in new_metadata.items():
        if file_path not in old_metadata or old_metadata[file_path] != hash_value:
            return True
    
    return False

async def get_embeddings_with_backoff(
    client,
    batch_texts: List[str],
    model: str,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.1
) -> List[List[float]]:
    """エクスポネンシャルバックオフを使用して非同期的にエンベディングを取得する関数"""
    delay = initial_delay
    
    for retry in range(max_retries):
        try:
            # エンベディング取得
            response = await client.embed(batch_texts, model=model)
            
            # 新しいAPIレスポンス形式に対応
            if hasattr(response, 'embeddings'):
                return response.embeddings
            else:
                # 古いレスポンス形式の場合（念のため）
                return [item for item in response]
                
        except Exception as e:
            # 最後のリトライでもエラーの場合は例外を発生させる
            if retry == max_retries - 1:
                print(f"最大リトライ回数に達しました: {e}")
                # エラーの場合は空のベクトルを返す
                return [[0.0] * 1024 for _ in range(len(batch_texts))]  # voyage-3-large の次元数は 1024
            
            # ジッターを追加した待機時間を計算
            jitter_amount = random.uniform(-jitter, jitter) * delay
            wait_time = delay + jitter_amount
            
            print(f"エラー発生: {e}. {wait_time:.2f}秒後にリトライします (リトライ {retry+1}/{max_retries})")
            await asyncio.sleep(wait_time)
            
            # 次回の待機時間を増加
            delay *= backoff_factor

async def get_embeddings(
    texts: List[str],
    model: str,
    batch_size: int,
    max_retries: int,
    request_interval: float,
    timeout: int,
    resume: bool
) -> List[List[float]]:
    """非同期的にエンベディングを取得する関数"""
    # Voyage AI非同期クライアントの初期化
    api_key = os.getenv("VOYAGE_API_KEY")
    if not api_key:
        print("VOYAGE_API_KEYが.envファイルに設定されていません")
        raise ValueError("API キーが設定されていません")
        
    client = voyageai.AsyncClient(api_key=api_key, max_retries=max_retries, timeout=timeout)
    
    all_embeddings = []
    start_idx = 0
    
    # 途中結果がある場合はロード
    if resume:
        all_embeddings, start_idx = load_temp_result()
    
    for i in tqdm(range(start_idx, len(texts), batch_size), desc="エンベディング取得中"):
        batch_texts = texts[i:i+batch_size]
        
        # エクスポネンシャルバックオフでエンベディング取得
        batch_embeddings = await get_embeddings_with_backoff(
            client,
            batch_texts,
            model,
            max_retries
        )
        
        all_embeddings.extend(batch_embeddings)
        
        # 途中結果を保存
        save_temp_result(all_embeddings, i + batch_size)
        
        # 次のリクエストまで待機（レート制限対策）
        if i + batch_size < len(texts):
            print(f"次のリクエストまで{request_interval}秒待機します...")
            await asyncio.sleep(request_interval)
    
    return all_embeddings

def calculate_similarity_matrix(embeddings_array: np.ndarray) -> np.ndarray:
    """エンベディングから類似度行列を計算する関数"""
    print("類似度行列を計算中...")
    return cosine_similarity(embeddings_array)

def save_results(
    output_file: str,
    games: List[Dict[str, Any]],
    game_data_list: List[Dict[str, Any]],
    embeddings_array: np.ndarray,
    similarity_matrix: np.ndarray,
    file_metadata: Dict[str, str]
) -> None:
    """結果をファイルに保存する関数"""
    print(f"結果を{output_file}に保存中...")
    try:
        with open(output_file, 'wb') as f:
            pickle.dump({
                'games': games,
                'game_data_list': game_data_list,
                'embeddings': embeddings_array,
                'similarity_matrix': similarity_matrix,
                'metadata': file_metadata  # ファイルメタデータを保存
            }, f)
        print("保存が完了しました")
        
        # 一時ファイルを削除
        if os.path.exists("temp_embeddings.pkl"):
            os.remove("temp_embeddings.pkl")
            print("一時ファイルを削除しました")
    except Exception as e:
        print(f"保存中にエラーが発生しました: {e}")

def process_game_files(file_paths: List[str], limit: int = 0, skip: int = 0) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """ゲームファイルを処理してデータを抽出する関数"""
    games = []
    game_data_list = []
    game_texts = []
    
    # 対象ファイルの選択（スキップと上限の適用）
    if skip > 0:
        print(f"最初の{skip}ファイルをスキップします")
        file_paths = file_paths[skip:]
    
    if limit > 0 and limit < len(file_paths):
        print(f"処理するファイル数を{limit}に制限します")
        file_paths = file_paths[:limit]
    
    print("ゲームデータを読み込み中...")
    for file_path in tqdm(file_paths):
        game_data = load_game_data(file_path)
        if not game_data:
            continue
            
        game_name = game_data.get('name', os.path.basename(file_path))
        game_text = create_game_text(game_data)
        
        games.append({
            "name": game_name,
            "file": file_path,
            "japanese_name": game_data.get('japanese_name', '')
        })
        game_data_list.append(game_data)
        game_texts.append(game_text)
    
    print(f"{len(games)}個のゲームデータを処理しました")
    return games, game_data_list, game_texts

def load_previous_results(output_file: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], np.ndarray, np.ndarray]:
    """前回の処理結果を読み込む関数"""
    try:
        with open(output_file, 'rb') as f:
            data = pickle.load(f)
            return (
                data.get('games', []),
                data.get('game_data_list', []),
                data.get('embeddings', np.array([])),
                data.get('similarity_matrix', np.array([]))
            )
    except Exception as e:
        print(f"前回の処理結果の読み込みエラー: {e}")
        return [], [], np.array([]), np.array([])

async def main_async():
    """メイン関数（非同期版）"""
    try:
        args = parse_args()
        
        # ゲームファイルを検索
        print(f"ゲームデータを検索中: {args.data_path}")
        game_files = glob.glob(args.data_path)
        print(f"{len(game_files)}個のファイルが見つかりました")
        
        if not game_files:
            print("ゲームファイルが見つかりません。data_pathを確認してください。")
            return
        
        # ファイルのメタデータを作成
        current_metadata = create_file_metadata(game_files)
        
        # 前回のメタデータを読み込む
        previous_metadata = load_previous_metadata(args.output)
        
        # 変更があるかチェック
        files_changed = check_files_changed(current_metadata, previous_metadata)
        
        # 変更がなく、forceフラグがオフなら処理をスキップ
        if not files_changed and not args.force and os.path.exists(args.output):
            print("YAMLファイルに変更がないため、処理をスキップします。")
            print("強制的に処理を実行するには --force オプションを使用してください。")
            return
        
        # 変更があるか強制実行の場合は処理を続行
        if files_changed:
            print("YAMLファイルに変更が検出されました。処理を続行します。")
        elif args.force:
            print("--force オプションにより、強制的に処理を実行します。")
        
        # ゲームデータの処理
        games, game_data_list, game_texts = process_game_files(game_files, args.limit, args.skip)
        
        if not games:
            print("有効なゲームデータがありません。")
            return
        
        # エンベディングの取得
        print(f"エンベディングを計算中... モデル: {args.model}, バッチサイズ: {args.batch_size}")
        embeddings = await get_embeddings(
            game_texts, 
            args.model,
            args.batch_size,
            args.max_retries,
            args.request_interval,
            args.timeout,
            args.resume
        )
        
        # エンベディングの配列をNumPy配列に変換
        embeddings_array = np.array(embeddings)
        
        # 類似度行列の計算
        similarity_matrix = calculate_similarity_matrix(embeddings_array)
        
        # 結果の保存（メタデータを含める）
        save_results(args.output, games, game_data_list, embeddings_array, similarity_matrix, current_metadata)
        
        print(f"処理が完了しました。{len(embeddings)}個のエンベディングを生成しました。")
        
    except Exception as e:
        print(f"プログラム実行中にエラーが発生しました: {e}")
        exit(1)

def main() -> None:
    """メイン関数"""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()