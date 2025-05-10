import time
import random
import streamlit as st
import requests
from functools import wraps
from datetime import datetime, timedelta

# Global variable to store API request history
request_history = []
# Cache expiration management
cache_expiry = {}

def rate_limited_request(max_per_minute=30, max_retries=3):
    """
    Decorator to rate-limit BGG API requests
    
    Parameters:
    max_per_minute (int): Maximum number of requests per minute
    max_retries (int): Maximum number of retries on error
    
    Returns:
    function: Decorated function
    """
    # Calculate minimum interval between requests
    min_interval = 60.0 / max_per_minute
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            global request_history
            
            # Remove request history older than 1 minute
            current_time = time.time()
            one_minute_ago = current_time - 60
            request_history = [t for t in request_history if t > one_minute_ago]
            
            # Check number of requests in the past minute
            if len(request_history) >= max_per_minute:
                # Use min_interval to distribute requests evenly
                oldest_request = min(request_history) if request_history else current_time - 60
                time_since_oldest = current_time - oldest_request
                # Calculate wait time based on elapsed time
                wait_time = max(0, min_interval - (time_since_oldest / max(1, len(request_history)))) + random.uniform(0.1, 1.0)
                
                if wait_time > 0:
                    with st.spinner(f"BGG API rate limit reached. Waiting {wait_time:.1f} seconds..."):
                        time.sleep(wait_time)
            
            # Add jitter to avoid simultaneous requests
            jitter = random.uniform(0.2, 1.0)
            time.sleep(jitter)
            
            # Execute request with retry logic
            retries = 0
            while retries <= max_retries:
                try:
                    # Record request history
                    request_history.append(time.time())
                    
                    # Actual function call
                    result = func(*args, **kwargs)
                    return result
                    
                except requests.exceptions.HTTPError as e:
                    retries += 1
                    if e.response.status_code == 429:  # Too Many Requests
                        # In case of rate limit error
                        retry_after = int(e.response.headers.get('Retry-After', 30))
                        wait_time = retry_after + random.uniform(1, 5)
                        
                        with st.spinner(f"BGG API rate limit reached. Waiting {wait_time:.1f} seconds... (Attempt {retries}/{max_retries})"):
                            time.sleep(wait_time)
                    
                    elif e.response.status_code >= 500:
                        # Backoff and retry for server errors
                        wait_time = (2 ** retries) + random.uniform(0, 1)
                        
                        with st.spinner(f"BGG API server error (Status {e.response.status_code}). Retrying in {wait_time:.1f} seconds... (Attempt {retries}/{max_retries})"):
                            time.sleep(wait_time)
                    
                    else:
                        # Other HTTP errors
                        st.error(f"API call error: {e.response.status_code} - {e.response.reason}")
                        raise
                
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    # In case of connection error or timeout
                    retries += 1
                    wait_time = (2 ** retries) + random.uniform(0, 1)
                    
                    # Adjust error message based on exception type
                    error_type = "Timeout" if isinstance(e, requests.exceptions.Timeout) else "Connection error"
                    with st.spinner(f"{error_type} occurred. Retrying in {wait_time:.1f} seconds... (Attempt {retries}/{max_retries})"):
                        time.sleep(wait_time)
                        
                # When maximum retries reached
                if retries > max_retries:
                    st.error(f"Maximum retries ({max_retries}) reached. Please try again later.")
                    raise Exception("Maximum API request retries reached")
                    
        return wrapper
    return decorator

def ttl_cache(ttl_hours=24):
    """
    Decorator to implement Time-to-Live (TTL) cache
    
    Parameters:
    ttl_hours (int): Cache validity period (hours)
    
    Returns:
    function: Decorated function
    """
    def decorator(func):
        # Function to generate cache key
        def make_key(args, kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            return hash(key)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            global cache_expiry
            
            # Generate cache key
            key = make_key(args, kwargs)
            
            # Cache key name
            cache_key = f"bgg_cache_{func.__name__}_{key}"
            
            # Check expiration
            current_time = datetime.now()
            expired = False
            
            if cache_key in cache_expiry:
                if current_time > cache_expiry[cache_key]:
                    # Cache expired
                    expired = True
                    st.session_state.pop(cache_key, None)
                    cache_expiry.pop(cache_key, None)
            
            # Return cached data if available and not expired
            if not expired and cache_key in st.session_state:
                return st.session_state[cache_key]
            
            # Execute function if no cache or expired
            result = func(*args, **kwargs)
            
            # Save result to cache
            st.session_state[cache_key] = result
            # Set expiration
            cache_expiry[cache_key] = current_time + timedelta(hours=ttl_hours)
            
            return result
        
        return wrapper
    return decorator

# Below are usage examples
# For actual application usage, import and use in bgg_api.py

@ttl_cache(ttl_hours=24)
@rate_limited_request(max_per_minute=20)
def search_games_improved(query, exact=False):
    """
    Function to search games by name (with rate limiting and caching)
    
    Parameters:
    query (str): Game name to search
    exact (bool): Whether to perform exact match search
    
    Returns:
    list: List of search results
    """
    # Replace spaces with +
    query = query.replace(" ", "+")
    
    # If exact is 1, perform exact match search
    exact_param = "1" if exact else "0"
    url = f"https://boardgamegeek.com/xmlapi2/search?query={query}&type=boardgame&exact={exact_param}"
    
    with st.spinner(f"Searching for '{query}'..."):
        response = requests.get(url)
    
    # Check response code
    response.raise_for_status()  # Throw exception if error
    
    if response.status_code == 200:
        # XML parsing code goes here
        # (Specific implementation should be migrated from bgg_api.py)
        return []  # Dummy return value
    
    return []  # This should not normally be reached

@ttl_cache(ttl_hours=48)  # Game details have low update frequency, so longer cache period
@rate_limited_request(max_per_minute=15)  # Stricter rate limit as details API is more resource-intensive
def get_game_details_improved(game_id):
    """
    Function to get game details (with rate limiting and caching)
    
    Parameters:
    game_id (int or str): BoardGameGeek game ID
    
    Returns:
    dict: Dictionary of game details
    """
    # Implementation should be migrated to bgg_api.py
    return {}