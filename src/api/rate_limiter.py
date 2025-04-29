import time
import random
import requests
from functools import wraps
from datetime import datetime, timedelta

# APIリクエスト履歴を保持するグローバル変数
request_history = []
# キャッシュの有効期限管理
cache_expiry = {}

def rate_limited_request(max_per_minute=30, max_retries=3):
    """
    BGG APIリクエストをレート制限するデコレータ
    
    Parameters:
    max_per_minute (int): 1分あたりの最大リクエスト数
    max_retries (int): エラー時の最大再試行回数
    
    Returns:
    function: デコレートされた関数
    """
    # リクエスト間の最小間隔を計算
    min_interval = 60.0 / max_per_minute
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            global request_history
            
            # 1分以上経過したリクエスト履歴を削除
            current_time = time.time()
            one_minute_ago = current_time - 60
            request_history = [t for t in request_history if t > one_minute_ago]
            
            # 過去1分間のリクエスト数をチェック
            if len(request_history) >= max_per_minute:
                # min_intervalを使用して均等にリクエストを分散
                oldest_request = min(request_history) if request_history else current_time - 60
                time_since_oldest = current_time - oldest_request
                # 経過時間に基づく待機時間を計算
                wait_time = max(0, min_interval - (time_since_oldest / max(1, len(request_history)))) + random.uniform(0.1, 1.0)
                
                if wait_time > 0:
                    with st.spinner(f"BGG APIレート制限に達しました。{wait_time:.1f}秒待機しています..."):
                        time.sleep(wait_time)
            
            # ジッター（ばらつき）を追加して、同時リクエストを避ける
            jitter = random.uniform(0.2, 1.0)
            time.sleep(jitter)
            
            # リクエスト実行（再試行ロジック付き）
            retries = 0
            while retries <= max_retries:
                try:
                    # リクエスト履歴を記録
                    request_history.append(time.time())
                    
                    # 実際の関数呼び出し
                    result = func(*args, **kwargs)
                    return result
                    
                except requests.exceptions.HTTPError as e:
                    retries += 1
                    if e.response.status_code == 429:  # Too Many Requests
                        # レート制限エラーの場合
                        retry_after = int(e.response.headers.get('Retry-After', 30))
                        wait_time = retry_after + random.uniform(1, 5)
                        
                        with st.spinner(f"BGG APIレート制限に達しました。{wait_time:.1f}秒待機しています... (試行 {retries}/{max_retries})"):
                            time.sleep(wait_time)
                    
                    elif e.response.status_code >= 500:
                        # サーバーエラーの場合はバックオフして再試行
                        wait_time = (2 ** retries) + random.uniform(0, 1)
                        
                        with st.spinner(f"BGG APIサーバーエラー (ステータス {e.response.status_code})。{wait_time:.1f}秒後に再試行します... (試行 {retries}/{max_retries})"):
                            time.sleep(wait_time)
                    
                    else:
                        # その他のHTTPエラー
                        st.error(f"API呼び出しエラー: {e.response.status_code} - {e.response.reason}")
                        raise
                
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    # 接続エラーやタイムアウトの場合
                    retries += 1
                    wait_time = (2 ** retries) + random.uniform(0, 1)
                    
                    # 例外の種類に基づいてエラーメッセージを調整
                    error_type = "タイムアウト" if isinstance(e, requests.exceptions.Timeout) else "接続エラー"
                    with st.spinner(f"{error_type}が発生しました。{wait_time:.1f}秒後に再試行します... (試行 {retries}/{max_retries})"):
                        time.sleep(wait_time)
                        
                # 最大再試行回数に達した場合
                if retries > max_retries:
                    st.error(f"最大再試行回数({max_retries})に達しました。後でもう一度お試しください。")
                    raise Exception("APIリクエストの最大再試行回数に達しました")
                    
        return wrapper
    return decorator

def ttl_cache(ttl_hours=24):
    """
    Time-to-Live (TTL) キャッシュを実装するデコレータ
    
    Parameters:
    ttl_hours (int): キャッシュの有効期間（時間）
    
    Returns:
    function: デコレートされた関数
    """
    def decorator(func):
        # キャッシュキーを生成する関数
        def make_key(args, kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            return hash(key)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            global cache_expiry
            
            # キャッシュキー生成
            key = make_key(args, kwargs)
            
            # キャッシュキーの名前
            cache_key = f"bgg_cache_{func.__name__}_{key}"
            
            # 有効期限チェック
            current_time = datetime.now()
            expired = False
            
            if cache_key in cache_expiry:
                if current_time > cache_expiry[cache_key]:
                    # キャッシュ期限切れ
                    expired = True
                    st.session_state.pop(cache_key, None)
                    cache_expiry.pop(cache_key, None)
            
            # キャッシュにデータがあり、期限内ならそれを返す
            if not expired and cache_key in st.session_state:
                return st.session_state[cache_key]
            
            # キャッシュがない場合や期限切れの場合は関数を実行
            result = func(*args, **kwargs)
            
            # 結果をキャッシュに保存
            st.session_state[cache_key] = result
            # 有効期限を設定
            cache_expiry[cache_key] = current_time + timedelta(hours=ttl_hours)
            
            return result
        
        return wrapper
    return decorator

# 以下は使用例です
# 実際のアプリケーションで使用する場合は、bgg_api.pyでインポートして使用します

@ttl_cache(ttl_hours=24)
@rate_limited_request(max_per_minute=20)
def search_games_improved(query, exact=False):
    """
    ゲーム名で検索する関数（レート制限とキャッシュ機能付き）
    
    Parameters:
    query (str): 検索するゲーム名
    exact (bool): 完全一致検索を行うかどうか
    
    Returns:
    list: 検索結果のリスト
    """
    # スペースを+に置き換え
    query = query.replace(" ", "+")
    
    # exactが1の場合、完全一致検索
    exact_param = "1" if exact else "0"
    url = f"https://boardgamegeek.com/xmlapi2/search?query={query}&type=boardgame&exact={exact_param}"
    
    with st.spinner(f"「{query}」を検索中..."):
        response = requests.get(url)
    
    # レスポンスコードのチェック
    response.raise_for_status()  # エラーがあれば例外をスロー
    
    if response.status_code == 200:
        # XML解析コードがここに入ります
        # (具体的な実装はbgg_api.pyから移行すべきです)
        return []  # ダミーの戻り値
    
    return []  # 通常ここには到達しないはず

@ttl_cache(ttl_hours=48)  # ゲーム詳細情報は更新頻度が低いのでキャッシュ期間を長めに
@rate_limited_request(max_per_minute=15)  # 詳細情報はAPIの負荷が高いのでレート制限を厳しく
def get_game_details_improved(game_id):
    """
    ゲームの詳細情報を取得する関数（レート制限とキャッシュ機能付き）
    
    Parameters:
    game_id (int or str): BoardGameGeekのゲームID
    
    Returns:
    dict: ゲーム詳細情報の辞書
    """
    # 実装はbgg_api.pyに移行すべきです
    return {}