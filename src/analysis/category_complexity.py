import os
import yaml

# Path to YAML file
CATEGORIES_DATA_FILE = "config/categories_data.yaml"

def load_categories_data():
    """
    Load category complexity data from YAML file
    
    Returns:
    dict: Dictionary with category name as key and complexity as value
    """
    try:
        # Return empty dictionary if file doesn't exist
        if not os.path.exists(CATEGORIES_DATA_FILE):
            return {}
        
        with open(CATEGORIES_DATA_FILE, 'r', encoding='utf-8') as file:
            complexity_data = yaml.safe_load(file)
            
        # Return empty dictionary if None
        if complexity_data is None:
            return {}
            
        return complexity_data
    except Exception as e:
        # Return error info without directly displaying error message
        print(f"Error loading category data: {str(e)}")
        return {}

def save_categories_data(complexity_data):
    """
    Save category complexity data to YAML file
    
    Parameters:
    complexity_data (dict): Dictionary with category name as key and complexity as value
    
    Returns:
    bool: Whether save was successful
    """
    try:
        with open(CATEGORIES_DATA_FILE, 'w', encoding='utf-8') as file:
            yaml.dump(complexity_data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        print(f"Error saving category data: {str(e)}")
        return False

def add_missing_category(category_name, default_complexity=2.5):
    """
    Add non-existent category to YAML file
    
    Parameters:
    category_name (str): Category name to add
    default_complexity (float): Default complexity value (when not set)
    
    Returns:
    bool: Whether addition was successful
    """
    try:
        # Load current data
        complexity_data = load_categories_data()
        
        # Do nothing if already exists
        if category_name in complexity_data:
            return True
        
        # Add if doesn't exist - Add in dictionary format to match new structure
        complexity_data[category_name] = {
            'complexity': default_complexity,
            'strategic_value': 3.0,  # Default value
            'interaction_value': 3.0,  # Default value
            'description': f"Auto-added category (default values)"
        }
        
        # Save
        return save_categories_data(complexity_data)
    except Exception as e:
        print(f"Error adding category: {str(e)}")
        return False

def get_category_complexity(category_name, default_value=2.5):
    """
    Get complexity for specified category
    Automatically adds to database and returns default value if not exists
    
    Parameters:
    category_name (str): Category name to get complexity for
    default_value (float): Default value if not exists
    
    Returns:
    float: Category complexity
    """
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