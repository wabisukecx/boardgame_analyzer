import os
import yaml
from datetime import datetime, timedelta

# Path to YAML file
MECHANICS_DATA_FILE = "config/mechanics_data.yaml"

# Global variables for caching
_mechanics_cache = None
_mechanics_cache_timestamp = None
_mechanics_cache_ttl = timedelta(minutes=10)  # Cache validity period (10 minutes)

def load_mechanics_data(force_reload=False):
    """
    Load mechanics complexity data from YAML file
    Utilize cache to reduce number of reads
    
    Parameters:
    force_reload (bool): Force reload ignoring cache
    
    Returns:
    dict: Dictionary with mechanic name as key and complexity as value
    """
    global _mechanics_cache, _mechanics_cache_timestamp
    
    current_time = datetime.now()
    
    # Return from cache if cache is valid
    if not force_reload and _mechanics_cache is not None and _mechanics_cache_timestamp is not None:
        if current_time - _mechanics_cache_timestamp < _mechanics_cache_ttl:
            return _mechanics_cache
    
    try:
        # Return empty dictionary if file doesn't exist
        if not os.path.exists(MECHANICS_DATA_FILE):
            _mechanics_cache = {}
            _mechanics_cache_timestamp = current_time
            return _mechanics_cache
        
        with open(MECHANICS_DATA_FILE, 'r', encoding='utf-8') as file:
            complexity_data = yaml.safe_load(file)
            
        # Return empty dictionary if None
        if complexity_data is None:
            complexity_data = {}
            
        # Update cache
        _mechanics_cache = complexity_data
        _mechanics_cache_timestamp = current_time
            
        return complexity_data
    except Exception as e:
        print(f"Error loading mechanics data: {str(e)}")
        return {}

def save_mechanics_data(complexity_data):
    """
    Save mechanics complexity data to YAML file
    Update cache after save
    
    Parameters:
    complexity_data (dict): Dictionary with mechanic name as key and complexity as value
    
    Returns:
    bool: Whether save was successful
    """
    global _mechanics_cache, _mechanics_cache_timestamp
    
    try:
        with open(MECHANICS_DATA_FILE, 'w', encoding='utf-8') as file:
            yaml.dump(complexity_data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        # Update cache
        _mechanics_cache = complexity_data
        _mechanics_cache_timestamp = datetime.now()
        
        return True
    except Exception as e:
        print(f"Error saving mechanics data: {str(e)}")
        return False

# Buffer for temporarily storing new mechanics additions
_pending_mechanics = {}
_pending_mechanics_count = 0
_max_pending_mechanics = 10  # Batch save when this number is reached

def add_missing_mechanic(mechanic_name, default_complexity=2.5):
    """
    Add non-existent mechanic to buffer and batch save when buffer is full
    
    Parameters:
    mechanic_name (str): Mechanic name to add
    default_complexity (float): Default complexity value
    
    Returns:
    bool: Whether addition was successful
    """
    global _pending_mechanics, _pending_mechanics_count
    
    try:
        # Load current data (from cache)
        complexity_data = load_mechanics_data()
        
        # Do nothing if already exists
        if mechanic_name in complexity_data:
            return True
        
        # Do nothing if already in buffer
        if mechanic_name in _pending_mechanics:
            return True
        
        # Add to buffer
        _pending_mechanics[mechanic_name] = {
            'complexity': default_complexity,
            'strategic_value': 3.0,
            'interaction_value': 3.0,
            'description': f"Auto-added mechanic (default values)"
        }
        
        _pending_mechanics_count += 1
        
        # Batch save when buffer is full
        if _pending_mechanics_count >= _max_pending_mechanics:
            return _save_pending_mechanics()
        
        return True
    except Exception as e:
        print(f"Error adding mechanic: {str(e)}")
        return False

def _save_pending_mechanics():
    """Batch save all pending mechanics in buffer"""
    global _pending_mechanics, _pending_mechanics_count
    
    if _pending_mechanics_count == 0:
        return True
        
    try:
        # Load current data (force reload)
        complexity_data = load_mechanics_data(force_reload=True)
        
        # Add buffer contents
        for mechanic_name, mechanic_data in _pending_mechanics.items():
            if mechanic_name not in complexity_data:
                complexity_data[mechanic_name] = mechanic_data
        
        # Save
        success = save_mechanics_data(complexity_data)
        
        if success:
            # Clear buffer
            _pending_mechanics = {}
            _pending_mechanics_count = 0
            
        return success
    except Exception as e:
        print(f"Error saving pending mechanics: {str(e)}")
        return False

def get_complexity(mechanic_name, default_value=2.5):
    """
    Get complexity for specified mechanic
    Get from cache and add to buffer if doesn't exist
    
    Parameters:
    mechanic_name (str): Mechanic name to get complexity for
    default_value (float): Default value if not exists
    
    Returns:
    float: Mechanic complexity
    """
    # Check buffer first
    global _pending_mechanics
    
    if mechanic_name in _pending_mechanics:
        pending_data = _pending_mechanics[mechanic_name]
        if isinstance(pending_data, dict) and 'complexity' in pending_data:
            return pending_data['complexity']
        elif isinstance(pending_data, (int, float)):
            return pending_data
        else:
            return default_value
    
    # Get data from cache
    complexity_data = load_mechanics_data()
    
    # Check if mechanic exists
    if mechanic_name in complexity_data:
        if isinstance(complexity_data[mechanic_name], dict) and 'complexity' in complexity_data[mechanic_name]:
            return complexity_data[mechanic_name]['complexity']
        elif isinstance(complexity_data[mechanic_name], (int, float)):
            return complexity_data[mechanic_name]
        else:
            return default_value
    
    # Add to buffer if doesn't exist
    add_missing_mechanic(mechanic_name, default_value)
    
    return default_value

# Function to flush buffer when application exits
def flush_pending_mechanics():
    """Save all pending mechanics"""
    return _save_pending_mechanics()