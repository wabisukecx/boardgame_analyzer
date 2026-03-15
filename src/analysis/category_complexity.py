import os
import yaml
from datetime import datetime, timedelta

# Path to YAML file
CATEGORIES_DATA_FILE = "config/categories_data.yaml"

# Global variables for caching
_categories_cache = None
_categories_cache_timestamp = None
_categories_cache_ttl = timedelta(minutes=10)  # Cache validity period (10 minutes)

def load_categories_data(force_reload=False):
    """
    Load category complexity data from YAML file
    Utilize cache to reduce number of reads

    Parameters:
    force_reload (bool): Force reload ignoring cache

    Returns:
    dict: Dictionary with category name as key and complexity as value
    """
    global _categories_cache, _categories_cache_timestamp

    current_time = datetime.now()

    # Return from cache if cache is valid
    if not force_reload and _categories_cache is not None and _categories_cache_timestamp is not None:
        if current_time - _categories_cache_timestamp < _categories_cache_ttl:
            return _categories_cache

    try:
        # Return empty dictionary if file doesn't exist
        if not os.path.exists(CATEGORIES_DATA_FILE):
            _categories_cache = {}
            _categories_cache_timestamp = current_time
            return _categories_cache

        with open(CATEGORIES_DATA_FILE, 'r', encoding='utf-8') as file:
            complexity_data = yaml.safe_load(file)

        # Return empty dictionary if None
        if complexity_data is None:
            complexity_data = {}

        # Update cache
        _categories_cache = complexity_data
        _categories_cache_timestamp = current_time

        return complexity_data
    except Exception as e:
        # Return error info without directly displaying error message
        print(f"Error loading category data: {str(e)}")
        return {}

def save_categories_data(complexity_data):
    """
    Save category complexity data to YAML file
    Update cache after save

    Parameters:
    complexity_data (dict): Dictionary with category name as key and complexity as value

    Returns:
    bool: Whether save was successful
    """
    global _categories_cache, _categories_cache_timestamp

    try:
        with open(CATEGORIES_DATA_FILE, 'w', encoding='utf-8') as file:
            yaml.dump(complexity_data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)

        # Update cache
        _categories_cache = complexity_data
        _categories_cache_timestamp = datetime.now()

        return True
    except Exception as e:
        print(f"Error saving category data: {str(e)}")
        return False


# Buffer for temporarily storing new category additions
_pending_categories = {}
_pending_categories_count = 0
_max_pending_categories = 10  # Batch save when this number is reached


def add_missing_category(category_name, default_complexity=2.5):
    """
    Add non-existent category to buffer and batch save when buffer is full

    Parameters:
    category_name (str): Category name to add
    default_complexity (float): Default complexity value (when not set)

    Returns:
    bool: Whether addition was successful
    """
    global _pending_categories, _pending_categories_count

    try:
        # Load current data (from cache)
        complexity_data = load_categories_data()

        # Do nothing if already exists
        if category_name in complexity_data:
            return True

        # Do nothing if already in buffer
        if category_name in _pending_categories:
            return True

        # Add to buffer
        _pending_categories[category_name] = {
            'complexity': default_complexity,
            'strategic_value': 3.0,
            'interaction_value': 3.0,
            'description': f"Auto-added category (default values)"
        }

        _pending_categories_count += 1

        # Batch save when buffer is full
        if _pending_categories_count >= _max_pending_categories:
            return _save_pending_categories()

        return True
    except Exception as e:
        print(f"Error adding category: {str(e)}")
        return False


def _save_pending_categories():
    """Batch save all pending categories in buffer"""
    global _pending_categories, _pending_categories_count

    if _pending_categories_count == 0:
        return True

    try:
        # Load current data (force reload)
        complexity_data = load_categories_data(force_reload=True)

        # Add buffer contents
        for category_name, category_data in _pending_categories.items():
            if category_name not in complexity_data:
                complexity_data[category_name] = category_data

        # Save
        success = save_categories_data(complexity_data)

        if success:
            # Clear buffer
            _pending_categories = {}
            _pending_categories_count = 0

        return success
    except Exception as e:
        print(f"Error saving pending categories: {str(e)}")
        return False


def flush_pending_categories():
    """Save all pending categories"""
    return _save_pending_categories()

def get_category_complexity(category_name, default_value=2.5):
    """
    Get complexity for specified category
    Get from cache and add to buffer if doesn't exist

    Parameters:
    category_name (str): Category name to get complexity for
    default_value (float): Default value if not exists

    Returns:
    float: Category complexity
    """
    # Check buffer first
    global _pending_categories

    if category_name in _pending_categories:
        pending_data = _pending_categories[category_name]
        if isinstance(pending_data, dict) and 'complexity' in pending_data:
            return pending_data['complexity']
        elif isinstance(pending_data, (int, float)):
            return pending_data
        else:
            return default_value

    complexity_data = load_categories_data()
    
    # Check if category exists
    if category_name in complexity_data:
        # New structure: complexity_data[category_name] is a dictionary
        # with a 'complexity' key inside
        if isinstance(complexity_data[category_name], dict) and 'complexity' in complexity_data[category_name]:
            return complexity_data[category_name]['complexity']
        # Support backward compatibility if value is stored directly
        elif isinstance(complexity_data[category_name], (int, float)):
            return complexity_data[category_name]
        # Return default value if neither case
        else:
            return default_value
    
    # Add and save if doesn't exist
    add_missing_category(category_name, default_value)
    
    return default_value

def calculate_category_complexity(categories):
    """
    Calculate overall complexity score from category list
    
    Parameters:
    categories (list): List of category dictionaries
    
    Returns:
    float: Overall category complexity score (range 1.0-5.0)
    """
    if not categories:
        return 2.5  # Default value
    
    # Get complexity for each category
    complexity_scores = [get_category_complexity(cat['name']) for cat in categories]
    
    # Calculate average complexity
    avg_complexity = sum(complexity_scores) / len(complexity_scores)
    
    # Adjustment based on number of categories (games with diverse categories are more complex)
    category_count_factor = min(1.3, 1.0 + (len(categories) - 1) * 0.05)
    adjusted_complexity = avg_complexity * category_count_factor
    
    # Limit to 1.0-5.0 range
    return min(5.0, max(1.0, adjusted_complexity))