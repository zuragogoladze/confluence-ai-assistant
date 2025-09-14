"""
Configuration management for Confluence AI Assistant.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for the application."""
    
    # Confluence Configuration
    CONFLUENCE_URL: str = os.getenv('CONFLUENCE_URL', '')
    CONFLUENCE_USERNAME: str = os.getenv('CONFLUENCE_USERNAME', '')
    CONFLUENCE_API_TOKEN: str = os.getenv('CONFLUENCE_API_TOKEN', '')
    CONFLUENCE_SPACE_KEY: Optional[str] = os.getenv('CONFLUENCE_SPACE_KEY')
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    OPENAI_MAX_TOKENS: int = int(os.getenv('OPENAI_MAX_TOKENS', '500'))
    OPENAI_TEMPERATURE: float = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
    
    # Application Configuration
    MAX_SEARCH_RESULTS: int = int(os.getenv('MAX_SEARCH_RESULTS', '5'))
    MAX_CONTEXT_TOKENS: int = int(os.getenv('MAX_CONTEXT_TOKENS', '2000'))
    CHUNK_SIZE: int = int(os.getenv('CHUNK_SIZE', '800'))
    CHUNK_OVERLAP: int = int(os.getenv('CHUNK_OVERLAP', '100'))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Validate configuration.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not cls.CONFLUENCE_URL:
            errors.append("CONFLUENCE_URL is required")
        
        if not cls.CONFLUENCE_USERNAME:
            errors.append("CONFLUENCE_USERNAME is required")
        
        if not cls.CONFLUENCE_API_TOKEN:
            errors.append("CONFLUENCE_API_TOKEN is required")
        
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_confluence_config(cls) -> dict:
        """Get Confluence configuration as dictionary."""
        return {
            'url': cls.CONFLUENCE_URL,
            'username': cls.CONFLUENCE_USERNAME,
            'api_token': cls.CONFLUENCE_API_TOKEN,
            'space_key': cls.CONFLUENCE_SPACE_KEY
        }
    
    @classmethod
    def get_openai_config(cls) -> dict:
        """Get OpenAI configuration as dictionary."""
        return {
            'api_key': cls.OPENAI_API_KEY,
            'model': cls.OPENAI_MODEL,
            'max_tokens': cls.OPENAI_MAX_TOKENS,
            'temperature': cls.OPENAI_TEMPERATURE
        }
