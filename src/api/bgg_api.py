import requests
import streamlit as st
import xml.etree.ElementTree as ET
from src.api.rate_limiter import rate_limited_request, ttl_cache

# API access functions
def get_game_mechanics(game_id):
    """
    Get mechanics (game types) information for specified game ID
    
    Parameters:
    game_id (int or str): BoardGameGeek game ID
    
    Returns:
    list: List of game mechanics
    """
    st.cache_data()  # Use cache feature to avoid duplicate requests
    
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={game_id}"
    with st.spinner(f"Retrieving mechanics for game ID {game_id}..."):
        response = requests.get(url)
    
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        mechanics = []
        
        # Get all elements with link type "boardgamemechanic"
        mechanic_elements = root.findall(".//link[@type='boardgamemechanic']")
        
        for mechanic in mechanic_elements:
            mechanics.append({
                "id": mechanic.get("id"),
                "name": mechanic.get("value")
            })
        
        return mechanics
    else:
        st.error(f"Error: Status code {response.status_code}")
        return None

@ttl_cache(ttl_hours=48)
@rate_limited_request(max_per_minute=15)
def get_game_details(game_id):
    """
    Get detailed game information (name, year, mechanics, categories, etc.)
    
    Parameters:
    game_id (int or str): BoardGameGeek game ID
    
    Returns:
    dict: Dictionary containing game details
    """
    st.cache_data()  # Use cache feature
    
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={game_id}&stats=1"
    with st.spinner(f"Retrieving detailed information for game ID {game_id}..."):
        response = requests.get(url)
    
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        game = {}
        
        item = root.find(".//item")
        if item is not None:
            game["id"] = item.get("id")
            game["type"] = item.get("type")
            
            # Get primary name
            name_element = item.find(".//name[@type='primary']")
            if name_element is not None:
                game["name"] = name_element.get("value")
            
            # Get alternate names (including Japanese names)
            alternate_names = []
            for name_elem in item.findall(".//name"):
                name_value = name_elem.get("value")
                name_type = name_elem.get("type")
                
                # Skip primary name as already retrieved
                if name_type == "primary":
                    continue
                
                alternate_names.append(name_value)
                
                # Check if language attribute exists
                if "language" in name_elem.attrib:
                    lang = name_elem.get("language")
                    if lang == "ja" or lang == "jp" or lang == "jpn":
                        game["japanese_name"] = name_value
            
            if alternate_names:
                game["alternate_names"] = alternate_names
                
                # If Japanese title not found yet
                if "japanese_name" not in game:
                    # Look for strings containing Japanese characters
                    for alt_name in alternate_names:
                        # Check for hiragana or katakana (more reliable Japanese detection)
                        has_japanese = any(
                            '\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF'
                            for c in alt_name
                        )
                        if has_japanese:
                            game["japanese_name"] = alt_name
                            break
            
            # Get year published
            year_element = item.find(".//yearpublished")
            if year_element is not None:
                game["year_published"] = year_element.get("value")
            
            # Get thumbnail URL
            thumbnail_element = item.find(".//thumbnail")
            if thumbnail_element is not None and thumbnail_element.text:
                game["thumbnail_url"] = thumbnail_element.text
            
            # Get publisher's player count settings
            minplayers_element = item.find(".//minplayers")
            if minplayers_element is not None:
                game["publisher_min_players"] = minplayers_element.get("value")
                
            maxplayers_element = item.find(".//maxplayers")
            if maxplayers_element is not None:
                game["publisher_max_players"] = maxplayers_element.get("value")
                
            # Get publisher's playing time
            playtime_element = item.find(".//playingtime")
            if playtime_element is not None:
                game["playing_time"] = playtime_element.get("value")
                
            # Get publisher's recommended age
            age_element = item.find(".//minage")
            if age_element is not None:
                game["publisher_min_age"] = age_element.get("value")
                
            # Get BGG community's recommended player count
            poll = item.findall(".//poll[@name='suggested_numplayers']/results")
            community_players = {"best": [], "recommended": [], "not_recommended": []}
            
            for numplayer_result in poll:
                num_players = numplayer_result.get("numplayers")
                
                # Find the most voted recommendation
                best_votes = 0
                best_recommendation = "not_recommended"
                
                for result in numplayer_result.findall("./result"):
                    vote_count = int(result.get("numvotes", "0"))
                    value = result.get("value")
                    
                    if vote_count > best_votes:
                        best_votes = vote_count
                        best_recommendation = value
                
                # Classify player count based on recommendation
                if best_recommendation == "Best":
                    community_players["best"].append(num_players)
                elif best_recommendation == "Recommended":
                    community_players["recommended"].append(num_players)
                elif best_recommendation == "Not Recommended":
                    community_players["not_recommended"].append(num_players)
            
            # Set best player count
            if community_players["best"]:
                # Sort if can be interpreted as numbers
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
            
            # Get BGG community's recommended age
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
            
            # Get description
            description_element = item.find(".//description")
            if description_element is not None and description_element.text:
                game["description"] = description_element.text
            
            # Get mechanics (game types)
            mechanics = []
            for mechanic in item.findall(".//link[@type='boardgamemechanic']"):
                mechanics.append({
                    "id": mechanic.get("id"),
                    "name": mechanic.get("value")
                })
            game["mechanics"] = mechanics
            
            # Get categories
            categories = []
            for category in item.findall(".//link[@type='boardgamecategory']"):
                categories.append({
                    "id": category.get("id"),
                    "name": category.get("value")
                })
            game["categories"] = categories
            
            # Get designer information
            designers = []
            for designer in item.findall(".//link[@type='boardgamedesigner']"):
                designers.append({
                    "id": designer.get("id"),
                    "name": designer.get("value")
                })
            game["designers"] = designers
            
            # Get publisher information
            publishers = []
            for publisher in item.findall(".//link[@type='boardgamepublisher']"):
                publishers.append({
                    "id": publisher.get("id"),
                    "name": publisher.get("value")
                })
            game["publishers"] = publishers
            
            # Get rating information
            ratings = item.find(".//ratings")
            if ratings is not None:
                avg_rating = ratings.find(".//average")
                if avg_rating is not None:
                    game["average_rating"] = avg_rating.get("value")
                
                # Get weight (complexity)
                weight_element = ratings.find(".//averageweight")
                if weight_element is not None:
                    game["weight"] = weight_element.get("value")
                
                # Ranking information
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
        st.error(f"Error: Status code {response.status_code}")
        return None

@ttl_cache(ttl_hours=24)
@rate_limited_request(max_per_minute=20)
def search_games(query, exact=False):
    """
    Search by game name
    
    Parameters:
    query (str): Game name to search
    exact (bool): Whether to perform exact match search
    
    Returns:
    list: List of search results
    """
    st.cache_data()  # Use cache feature
    
    # Replace spaces with +
    query = query.replace(" ", "+")
    
    # If exact is 1, perform exact match search
    exact_param = "1" if exact else "0"
    url = f"https://boardgamegeek.com/xmlapi2/search?query={query}&type=boardgame&exact={exact_param}"
    
    with st.spinner(f"Searching for '{query}'..."):
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
        st.error(f"Error: Status code {response.status_code}")
        return None