import os
import streamlit as st
import yaml
import pandas as pd
import re
from pathlib import Path
from src.utils.language import t, get_game_display_name, get_game_filename, get_dataframe_column_names

def save_game_data_to_yaml(game_data, custom_filename=None):
    """
    Save game data to YAML file
    
    Parameters:
    game_data (dict): Game data to save
    custom_filename (str, optional): Custom filename
    
    Returns:
    tuple: (success flag, file path, error message)
    """
    # Generate filename
    game_id = game_data.get('id', 'unknown')
    
    # Pad game ID to 6 digits
    if game_id != 'unknown' and game_id.isdigit():
        game_id = game_id.zfill(6)
    
    # Generate consistent filename regardless of language
    placeholder_filename = get_game_filename(game_data, game_id) + ".yaml"
    
    # Process custom filename
    if not custom_filename:
        filename = placeholder_filename
    else:
        # Convert full-width spaces to half-width
        custom_filename = custom_filename.replace('　', ' ')
        filename = custom_filename
        if not filename.endswith('.yaml'):
            filename += '.yaml'
    
    # Create data directory
    os.makedirs("game_data", exist_ok=True)
    file_path = os.path.join("game_data", filename)
    
    try:
        # Copy game data for safety before conversion
        game_data_safe = game_data.copy()
        
        # Remove top-level ID
        if 'id' in game_data_safe:
            del game_data_safe['id']
        
        # Remove IDs from nested elements
        for category in ['mechanics', 'categories', 'designers', 'publishers', 'ranks']:
            if (category in game_data_safe and isinstance(game_data_safe[category], list)):
                for item in game_data_safe[category]:
                    if 'id' in item:
                        del item['id']
        
        # Add learning curve information (only if not already present)
        if ('learning_analysis' not in game_data_safe and 
            'description' in game_data_safe and 
            'mechanics' in game_data_safe and 
            'weight' in game_data_safe):
            # Use in this block without Streamlit dependencies
            try:
                from src.analysis.learning_curve import calculate_learning_curve
                game_data_safe['learning_analysis'] = calculate_learning_curve(game_data_safe)
            except Exception as e:
                    st.warning(t("errors.learning_curve_calculation", error=str(e)))
        
        # Convert full-width spaces to half-width before saving
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
        
        # Convert to YAML and save
        with open(file_path, 'w', encoding='utf-8') as file:
            yaml.dump(game_data_safe, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return True, file_path, None
    except Exception as e:
        return False, None, str(e)

def load_game_data_from_yaml(file_path):
    """
    Load game data from YAML file
    
    Parameters:
    file_path (str): Path to YAML file
    
    Returns:
    dict: Game data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            game_data = yaml.safe_load(file)
        return game_data
    except Exception as e:
        # Error display that doesn't depend on Streamlit
        st.warning(t("errors.file_read", error=str(e)))
        return None

def search_results_to_dataframe(results):
    """
    Convert search results to DataFrame
    
    Parameters:
    results (list): List of search results
    
    Returns:
    pandas.DataFrame: DataFrame of search results
    """
    if not results:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Get language-aware column names
    column_names = get_dataframe_column_names()
    
    # Rename columns
    df = df.rename(columns={
        "id": column_names.get("id", "Game ID"),
        "name": column_names.get("name", "Game Name"),
        "year_published": column_names.get("year_published", "Year Published")
    })
    
    # Replace NaN with appropriate unknown text
    df = df.fillna(t("common.unknown"))
    
    # Remove unnecessary columns
    if "type" in df.columns:
        df = df.drop(columns=["type"])
    
    return df

def load_all_game_data():
    """
    Load all game data from YAML files in game_data folder
    
    Returns:
    dict: Dictionary with game ID (string) as key and game data as value
    """
    game_data_dict = {}
    
    # Check if game_data folder exists
    if not os.path.exists("game_data"):
        return game_data_dict
    
    # Search for YAML files
    for filename in os.listdir("game_data"):
        if filename.endswith(".yaml"):
            # Extract game ID from filename (e.g., "167791_Terraforming_Mars.yaml")
            match = re.match(r"(\d+)_(.*?)\.yaml", filename)
            if match:
                game_id = match.group(1)
                file_path = os.path.join("game_data", filename)
                
                # Load YAML file
                game_data = load_game_data_from_yaml(file_path)
                if game_data:
                    game_data_dict[game_id] = game_data
    
    return game_data_dict

def get_yaml_game_list():
    """
    Scan YAML files in game_data folder and return list of game IDs and titles
    
    Returns:
        list: List of (game ID, filename, display name) tuples
    """
    game_list = []
    # Check if game_data folder exists
    if not os.path.exists("game_data"):
        return game_list
        
    # Search for YAML files
    for filename in os.listdir("game_data"):
        if filename.endswith(".yaml"):
            # Extract game ID from filename (e.g., "167791_Terraforming_Mars.yaml")
            match = re.match(r"(\d+)_(.*?)\.yaml", filename)
            if match:
                game_id = match.group(1)
                file_path = os.path.join("game_data", filename)
                
                # Load game data to get language-aware display name
                game_data = load_game_data_from_yaml(file_path)
                if game_data:
                    display_name = get_game_display_name(game_data)
                    game_list.append((game_id, filename, f"{game_id} - {display_name}"))
                else:
                    # Fallback if data can't be loaded
                    game_name = match.group(2)
                    display_name = game_name.replace("_", " ")
                    game_list.append((game_id, filename, f"{game_id} - {display_name}"))
    
    # Sort by ID
    game_list.sort(key=lambda x: int(x[0]))
    return game_list

def compare_game_data(old_data, new_data):
    """
    Compare two game data sets and return whether there are changes and description of changes
    
    Parameters:
        old_data (dict): Existing game data
        new_data (dict): Newly retrieved game data
    
    Returns:
        tuple: (whether there are changes, description of changes)
    """
    if not old_data or not new_data:
        return True, t("compare.incomplete_data")
    
    # Define important keys
    important_keys = {
        'name': t("common.english_name"),
        'japanese_name': t("common.japanese_name"),
        'year_published': t("common.year_published"),
        'average_rating': t("common.average_rating"),
        'weight': t("common.complexity"),
        # Mechanics and categories are complex structures so handle separately
    }
    
    changes = []
    has_changes = False
    
    # Compare basic fields
    for key, display_name in important_keys.items():
        old_value = old_data.get(key)
        new_value = new_data.get(key)
        
        # Consider data type differences (string vs number case)
        if isinstance(old_value, (int, float)) and isinstance(new_value, str):
            try:
                new_value = float(new_value) if '.' in new_value else int(new_value)
            except ValueError:
                pass
        elif isinstance(new_value, (int, float)) and isinstance(old_value, str):
            try:
                old_value = float(old_value) if '.' in old_value else int(old_value)
            except ValueError:
                pass
        
        if old_value != new_value:
            has_changes = True
            if key in ['average_rating', 'weight'] and isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
                # Round numbers to 2 decimal places
                old_str = f"{old_value:.2f}" if isinstance(old_value, float) else str(old_value)
                new_str = f"{new_value:.2f}" if isinstance(new_value, float) else str(new_value)
                changes.append(f"- {display_name}: {old_str} → {new_str}")
            else:
                changes.append(f"- {display_name}: {old_value} → {new_value}")
    
    # Compare mechanics
    old_mechanics = set(m.get('name', '') for m in old_data.get('mechanics', []))
    new_mechanics = set(m.get('name', '') for m in new_data.get('mechanics', []))
    
    if old_mechanics != new_mechanics:
        has_changes = True
        added = new_mechanics - old_mechanics
        removed = old_mechanics - new_mechanics
        
        if added:
            changes.append(f"- {t('compare.mechanics_added')}: {', '.join(added)}")
        if removed:
            changes.append(f"- {t('compare.mechanics_removed')}: {', '.join(removed)}")
    
    # Compare categories
    old_categories = set(c.get('name', '') for c in old_data.get('categories', []))
    new_categories = set(c.get('name', '') for c in new_data.get('categories', []))
    
    if old_categories != new_categories:
        has_changes = True
        added = new_categories - old_categories
        removed = old_categories - new_categories
        
        if added:
            changes.append(f"- {t('compare.categories_added')}: {', '.join(added)}")
        if removed:
            changes.append(f"- {t('compare.categories_removed')}: {', '.join(removed)}")
    
    # Combine change descriptions
    change_description = '\n'.join(changes) if changes else t("compare.no_changes")
    
    return has_changes, change_description