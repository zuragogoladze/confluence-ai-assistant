"""
Confluence API Client for retrieving and processing Confluence data.
"""

import os
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceClient:
    """Client for interacting with Confluence API."""
    
    def __init__(self, url: str, username: str, api_token: str, space_key: Optional[str] = None):
        """
        Initialize Confluence client.
        
        Args:
            url: Confluence base URL
            username: Confluence username/email
            api_token: Confluence API token
            space_key: Optional space key to limit search scope
        """
        self.url = url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.space_key = space_key
        self.session = requests.Session()
        self.session.auth = (username, api_token)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def search_content(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search for content in Confluence.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of content dictionaries
        """
        try:
            # Build search parameters
            params = {
                'cql': f'text ~ "{query}"',
                'limit': limit,
                'expand': 'body.storage,version,space,ancestors'
            }
            
            if self.space_key:
                params['cql'] = f'space = "{self.space_key}" AND text ~ "{query}"'
            
            response = self.session.get(
                f"{self.url}/wiki/rest/api/content/search",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('results', [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching Confluence: {e}")
            return []
    
    def get_page_content(self, page_id: str) -> Optional[Dict]:
        """
        Get detailed content of a specific page.
        
        Args:
            page_id: Confluence page ID
            
        Returns:
            Page content dictionary or None if error
        """
        try:
            response = self.session.get(
                f"{self.url}/wiki/rest/api/content/{page_id}",
                params={'expand': 'body.storage,version,space,ancestors,descendants'}
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting page content: {e}")
            return None
    
    def extract_text_from_storage(self, storage_content: str) -> str:
        """
        Extract clean text from Confluence storage format.
        
        Args:
            storage_content: HTML content from Confluence storage
            
        Returns:
            Clean text content
        """
        if not storage_content:
            return ""
        
        # Parse HTML and extract text
        soup = BeautifulSoup(storage_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it up
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def get_recent_pages(self, limit: int = 20) -> List[Dict]:
        """
        Get recently updated pages.
        
        Args:
            limit: Maximum number of pages
            
        Returns:
            List of recent pages
        """
        try:
            # Use basic content endpoint with space filter
            params = {
                'limit': limit * 2,  # Get more to account for filtering
                'expand': 'body.storage,version,space,ancestors'
            }
            
            if self.space_key:
                params['spaceKey'] = self.space_key
            
            response = self.session.get(
                f"{self.url}/wiki/rest/api/content",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            all_results = data.get('results', [])
            
            # Sort by lastModified and return the most recent
            sorted_results = sorted(
                all_results, 
                key=lambda x: x.get('version', {}).get('when', ''), 
                reverse=True
            )
            
            return sorted_results[:limit]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting recent pages: {e}")
            return []
    
    def get_space_content(self, space_key: str, limit: int = 100) -> List[Dict]:
        """
        Get all content from a specific space.
        
        Args:
            space_key: Confluence space key
            limit: Maximum number of pages
            
        Returns:
            List of pages in the space
        """
        try:
            # Use CQL search for space content
            cql_query = f'space = "{space_key}"'
            
            params = {
                'cql': cql_query,
                'limit': limit,
                'expand': 'body.storage,version,space,ancestors'
            }
            
            response = self.session.get(
                f"{self.url}/wiki/rest/api/content/search",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('results', [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting space content: {e}")
            return []
    
    def test_connection(self) -> bool:
        """
        Test the connection to Confluence.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.session.get(f"{self.url}/wiki/rest/api/user/current")
            response.raise_for_status()
            logger.info("Confluence connection successful")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Confluence connection failed: {e}")
            return False
