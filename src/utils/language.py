"""
Module for managing multi-language support
Provides language resource management, text retrieval, and game name display switching
"""

import streamlit as st
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class LanguageManager:
    """Class for managing multi-language support"""
    
    def __init__(self):
        self.languages_dir = Path("config/languages")
        self.supported_languages = {
            "ja": "日本語",
            "en": "English"
        }
    
    def initialize(self):
        """Initialize language settings and resources"""
        # Set default language
        if 'language' not in st.session_state:
            st.session_state.language = 'ja'
        
        # Initialize language resources if not exists
        if 'language_resources' not in st.session_state:
            st.session_state.language_resources = {}
        
        # Load language resources
        self._load_language_resources()
    
    def _load_language_resources(self):
        """Load language resource files"""
        # If current language resources are not loaded
        if st.session_state.language not in st.session_state.language_resources:
            language_file = self.languages_dir / f"{st.session_state.language}.json"
            
            try:
                with open(language_file, 'r', encoding='utf-8') as f:
                    st.session_state.language_resources[st.session_state.language] = json.load(f)
            except FileNotFoundError:
                st.error(f"Language file not found: {language_file}")
                # Use Japanese as fallback
                if st.session_state.language != 'ja':
                    st.session_state.language = 'ja'
                    self._load_language_resources()
            except json.JSONDecodeError as e:
                st.error(f"Error loading language file {language_file}: {e}")
                # Use empty dictionary as fallback
                st.session_state.language_resources[st.session_state.language] = {}
    
    def get_text(self, key_path: str, **kwargs) -> str:
        """
        Get text from language resources
        
        Args:
            key_path: Dot-separated key path (e.g., "search.title")
            **kwargs: Arguments for variable substitution in text
        
        Returns:
            str: Text corresponding to the language
        """
        # Check if language_resources exists
        if 'language_resources' not in st.session_state:
            self.initialize()
        
        keys = key_path.split('.')
        text = st.session_state.language_resources.get(st.session_state.language, {})
        
        for key in keys:
            if isinstance(text, dict):
                text = text.get(key, None)
            else:
                text = None
                break
        
        # Return key path if text not found
        if text is None:
            return key_path
        
        # Variable substitution
        if kwargs and isinstance(text, str):
            try:
                text = text.format(**kwargs)
            except KeyError as e:
                st.warning(f"Missing variable in translation: {e}")
                return text
        
        return text
    
    def switch_language(self, language_code: str):
        """Switch language"""
        if language_code in self.supported_languages:
            st.session_state.language = language_code
            self._load_language_resources()
            st.rerun()
    
    def get_current_language(self) -> str:
        """Get current language code"""
        return st.session_state.language
    
    def is_japanese(self) -> bool:
        """Check if current language is Japanese"""
        return st.session_state.language == 'ja'
    
    def is_english(self) -> bool:
        """Check if current language is English"""
        return st.session_state.language == 'en'

# Global instance - create but do not initialize
language_manager = LanguageManager()

# Convenience functions
def t(key_path: str, **kwargs) -> str:
    """Shortcut function for text retrieval"""
    return language_manager.get_text(key_path, **kwargs)

def get_game_display_name(game_data: Dict[str, Any]) -> str:
    """
    Get game name according to language setting
    
    Args:
        game_data: Dictionary of game data
    
    Returns:
        str: Game name according to the language
    """
    if language_manager.is_japanese():
        # Japanese priority
        return game_data.get('japanese_name', '') or game_data.get('name', '名称不明')
    else:
        # English priority
        return game_data.get('name', '') or game_data.get('japanese_name', 'Unknown')

def get_game_secondary_name(game_data: Dict[str, Any]) -> Optional[str]:
    """
    Get game name in secondary language (for caption display)
    
    Args:
        game_data: Dictionary of game data
    
    Returns:
        Optional[str]: Game name in secondary language, None if not available
    """
    if language_manager.is_japanese():
        # Return English name in Japanese mode
        english_name = game_data.get('name', '')
        return english_name if english_name else None
    else:
        # Return Japanese name in English mode
        japanese_name = game_data.get('japanese_name', '')
        return japanese_name if japanese_name else None

def get_game_filename(game_data: Dict[str, Any], game_id: str = None) -> str:
    """
    Get game name for filename (consistent regardless of language)
    
    Args:
        game_data: Dictionary of game data
        game_id: Game ID (optional)
    
    Returns:
        str: Game name for filename
    """
    # Filename should be consistent regardless of language
    # Use Japanese name if available, otherwise use English name
    game_name = game_data.get('japanese_name', '') or game_data.get('name', '名称不明')
    
    # Convert full-width spaces to half-width spaces
    game_name = game_name.replace('　', ' ')
    
    # Replace special characters
    game_name = game_name.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace(";", "_")
    
    # Add game ID to the beginning if available
    if game_id:
        # Pad game ID to 6 digits
        if game_id.isdigit():
            game_id = game_id.zfill(6)
        return f"{game_id}_{game_name}"
    
    return game_name

def format_language_caption(secondary_name: Optional[str]) -> Optional[str]:
    """
    Format secondary language name for caption
    
    Args:
        secondary_name: Name in secondary language
    
    Returns:
        Optional[str]: Formatted caption, None if not available
    """
    if not secondary_name:
        return None
    
    if language_manager.is_japanese():
        return f"English: {secondary_name}"
    else:
        return f"Japanese: {secondary_name}"

def get_dataframe_column_names() -> Dict[str, str]:
    """
    Return DataFrame column names according to language
    
    Returns:
        Dict[str, str]: Dictionary of column names
    """
    return {
        "id": t("common.game_id"),
        "name": t("common.game_name"),
        "year_published": t("common.year_published"),
        "average_rating": t("common.average_rating"),
        "weight": t("common.complexity"),
        "playing_time": t("common.playing_time"),
        "publisher_min_players": t("common.min_players"),
        "publisher_max_players": t("common.max_players"),
    }

def get_metric_names() -> Dict[str, str]:
    """
    Return metric names according to language
    
    Returns:
        Dict[str, str]: Dictionary of metric names
    """
    return {
        "initial_barrier": t("metrics.initial_barrier"),
        "strategic_depth": t("metrics.strategic_depth"),
        "replayability": t("metrics.replayability"),
        "decision_points": t("metrics.decision_points"),
        "interaction_complexity": t("metrics.interaction_complexity"),
        "rules_complexity": t("metrics.rules_complexity"),
        "bgg_weight": t("metrics.bgg_weight"),
    }

def get_stop_words() -> set:
    """Get stop words for the current language
    
    Returns:
        set: Set of stop words
    """
    if language_manager.is_japanese():
        return {
            # Japanese particles
            'の', 'を', 'に', 'へ', 'と', 'より', 'から', 'で', 'や', 'は', 'が', 'も',
            # Common conjunctions
            'そして', 'しかし', 'また', 'さらに', 'ただし',
            # Common auxiliary words
            'です', 'ます', 'だ', 'である', 'でした', 'ました',
            # Common adverbs
            'とても', 'かなり', 'すこし', 'もっと',
            # Numbers and counters
            '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
            # Common pronouns
            'これ', 'それ', 'あれ', 'この', 'その', 'あの',
            # Also include English stop words as descriptions might be mixed
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'with', 'by', 'about', 'as', 'of', 'from'
        }
    else:
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'with', 'by', 'about', 'as', 'of', 'from', 'that', 'this', 'these', 
            'those', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'can', 
            'could', 'may', 'might', 'must', 'shall'
        }

# Debug function
def debug_language_info():
    """Display language setting debug information"""
    st.sidebar.markdown("### Language Debug Info")
    st.sidebar.write(f"Current language: {language_manager.get_current_language()}")
    st.sidebar.write(f"Is Japanese: {language_manager.is_japanese()}")
    st.sidebar.write(f"Is English: {language_manager.is_english()}")
    if 'language_resources' in st.session_state:
        st.sidebar.write(f"Loaded languages: {list(st.session_state.language_resources.keys())}")