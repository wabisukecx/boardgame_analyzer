import requests
import streamlit as st
import xml.etree.ElementTree as ET
from src.api.rate_limiter import rate_limited_request, ttl_cache

# APIアクセス関数
def get_game_mechanics(game_id):
    """
    指定されたゲームIDのメカニクス（ゲームの種類）情報を取得する
    
    Parameters:
    game_id (int or str): BoardGameGeekのゲームID
    
    Returns:
    list: ゲームメカニクスのリスト
    """
    st.cache_data()  # キャッシュ機能を使用して同じリクエストの重複を避ける
    
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={game_id}"
    with st.spinner(f"ゲームID {game_id} のメカニクスを取得中..."):
        response = requests.get(url)
    
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        mechanics = []
        
        # リンクタイプ「boardgamemechanic」を持つ要素を全て取得
        mechanic_elements = root.findall(".//link[@type='boardgamemechanic']")
        
        for mechanic in mechanic_elements:
            mechanics.append({
                "id": mechanic.get("id"),
                "name": mechanic.get("value")
            })
        
        return mechanics
    else:
        st.error(f"エラー: ステータスコード {response.status_code}")
        return None

@ttl_cache(ttl_hours=48)
@rate_limited_request(max_per_minute=15)
def get_game_details(game_id):
    """
    ゲームの詳細情報を取得する（名前、年、メカニクス、カテゴリなど）
    
    Parameters:
    game_id (int or str): BoardGameGeekのゲームID
    
    Returns:
    dict: ゲーム詳細情報の辞書
    """
    st.cache_data()  # キャッシュ機能を使用
    
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={game_id}&stats=1"
    with st.spinner(f"ゲームID {game_id} の詳細情報を取得中..."):
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
        st.error(f"エラー: ステータスコード {response.status_code}")
        return None

@ttl_cache(ttl_hours=24)
@rate_limited_request(max_per_minute=20)
def search_games(query, exact=False):
    """
    ゲーム名で検索する
    
    Parameters:
    query (str): 検索するゲーム名
    exact (bool): 完全一致検索を行うかどうか
    
    Returns:
    list: 検索結果のリスト
    """
    st.cache_data()  # キャッシュ機能を使用
    
    # スペースを+に置き換える
    query = query.replace(" ", "+")
    
    # exactが1の場合、完全一致検索
    exact_param = "1" if exact else "0"
    url = f"https://boardgamegeek.com/xmlapi2/search?query={query}&type=boardgame&exact={exact_param}"
    
    with st.spinner(f"「{query}」を検索中..."):
        response = requests.get(url)
    
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        results = []
        
        for item in root.findall(".//item"):
            game = {
                "id": item.get("id"),
                "type": item.get("type")
            }
            
            name = item.find(".//name")
            if name is not None:
                game["name"] = name.get("value")
                
            year_published = item.find(".//yearpublished")
            if year_published is not None:
                game["year_published"] = year_published.get("value")
                
            results.append(game)
            
        return results
    else:
        st.error(f"エラー: ステータスコード {response.status_code}")
        return None