import time
import random
import requests
from functools import wraps
from datetime import datetime, timedelta

try:
    import streamlit as st
    _STREAMLIT_AVAILABLE = True
except ImportError:
    _STREAMLIT_AVAILABLE = False

# Global variable to store API request history
request_history = []

def _spinner(msg: str):
    """Return st.spinner context manager if Streamlit is available, else a no-op."""
    if _STREAMLIT_AVAILABLE:
        return st.spinner(msg)
    import contextlib
    @contextlib.contextmanager
    def _noop():
        print(msg)
        yield
    return _noop()

def _show_error(msg: str):
    """Show error via st.error or print depending on environment."""
    if _STREAMLIT_AVAILABLE:
        st.error(msg)
    else:
        print(f"[ERROR] {msg}")

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
                    with _spinner(f"BGG API rate limit reached. Waiting {wait_time:.1f} seconds..."):
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
                        
                        with _spinner(f"BGG API rate limit reached. Waiting {wait_time:.1f} seconds... (Attempt {retries}/{max_retries})"):
                            time.sleep(wait_time)
                    
                    elif e.response.status_code >= 500:
                        # Backoff and retry for server errors
                        wait_time = (2 ** retries) + random.uniform(0, 1)
                        
                        with _spinner(f"BGG API server error (Status {e.response.status_code}). Retrying in {wait_time:.1f} seconds... (Attempt {retries}/{max_retries})"):
                            time.sleep(wait_time)
                    
                    else:
                        # Other HTTP errors
                        _show_error(f"API call error: {e.response.status_code} - {e.response.reason}")
                        raise
                
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    # In case of connection error or timeout
                    retries += 1
                    wait_time = (2 ** retries) + random.uniform(0, 1)
                    
                    # Adjust error message based on exception type
                    error_type = "Timeout" if isinstance(e, requests.exceptions.Timeout) else "Connection error"
                    with _spinner(f"{error_type} occurred. Retrying in {wait_time:.1f} seconds... (Attempt {retries}/{max_retries})"):
                        time.sleep(wait_time)
                        
                # When maximum retries reached
                if retries > max_retries:
                    _show_error(f"Maximum retries ({max_retries}) reached. Please try again later.")
                    raise Exception("Maximum API request retries reached")
                    
        return wrapper
    return decorator

# In-memory cache store (Streamlit-independent)
_memory_cache: dict = {}

def ttl_cache(ttl_hours=24):
    """
    Decorator to implement Time-to-Live (TTL) cache.
    Uses an in-memory dictionary instead of st.session_state
    so it works in both Streamlit and CLI environments.
    
    Parameters:
    ttl_hours (int): Cache validity period (hours)
    
    Returns:
    function: Decorated function
    """
    def decorator(func):
        def make_key(args, kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            return hash(key)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"bgg_cache_{func.__name__}_{make_key(args, kwargs)}"
            current_time = datetime.now()
            
            # Check if cached value exists and is still valid
            if cache_key in _memory_cache:
                value, expires_at = _memory_cache[cache_key]
                if current_time < expires_at:
                    return value
                # Expired — remove from cache
                del _memory_cache[cache_key]
            
            # Execute function and store result
            result = func(*args, **kwargs)
            _memory_cache[cache_key] = (result, current_time + timedelta(hours=ttl_hours))
            return result
        
        return wrapper
    return decorator

# NOTE: search_games_improved / get_game_details_improved はダミー実装のため削除済み。
# 実装は src/api/bgg_api.py の search_games / get_game_details を使用すること。