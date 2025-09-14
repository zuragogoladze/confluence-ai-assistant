"""
AI Assistant for answering questions based on Confluence data - No OpenAI version.
This version works without OpenAI API for testing and basic functionality.
"""

import os
import tiktoken
from typing import List, Dict, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceAIAssistantNoOpenAI:
    """AI Assistant that answers questions based on Confluence content without OpenAI."""
    
    def __init__(self, confluence_client):
        """
        Initialize the AI assistant.
        
        Args:
            confluence_client: ConfluenceClient instance
        """
        self.confluence_client = confluence_client
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
    
    def search_relevant_content(self, question: str, max_results: int = 10) -> List[Dict]:
        """
        Search for content relevant to the question.
        
        Args:
            question: User's question
            max_results: Maximum number of search results
            
        Returns:
            List of relevant content dictionaries
        """
        # Try multiple search strategies
        all_results = []
        
        # Strategy 1: Search with the full question
        search_results = self.confluence_client.search_content(question, limit=max_results)
        all_results.extend(search_results)
        
        # Strategy 2: Extract key terms and search with them
        import re
        # Extract potential keywords (words longer than 3 characters)
        keywords = re.findall(r'\b\w{4,}\b', question.lower())
        if keywords:
            # Try searching with individual keywords
            for keyword in keywords[:3]:  # Limit to first 3 keywords
                keyword_results = self.confluence_client.search_content(keyword, limit=max_results//2)
                all_results.extend(keyword_results)
        
        # Strategy 3: If still no results, try getting recent pages
        if not all_results:
            logger.info("No search results found, trying recent pages...")
            recent_pages = self.confluence_client.get_recent_pages(max_results)
            all_results.extend(recent_pages)
        
        # Remove duplicates based on page ID
        seen_ids = set()
        unique_results = []
        for result in all_results:
            page_id = result.get('id')
            if page_id and page_id not in seen_ids:
                seen_ids.add(page_id)
                unique_results.append(result)
        
        # Process and enrich the results
        enriched_results = []
        for result in unique_results[:max_results]:
            # Get full page content if we only have a summary
            if 'body' not in result or 'storage' not in result.get('body', {}):
                page_id = result.get('id')
                if page_id:
                    full_content = self.confluence_client.get_page_content(page_id)
                    if full_content:
                        result = full_content
            
            # Extract text content
            storage_content = result.get('body', {}).get('storage', {}).get('value', '')
            text_content = self.confluence_client.extract_text_from_storage(storage_content)
            
            if text_content:
                enriched_result = {
                    'id': result.get('id'),
                    'title': result.get('title', ''),
                    'url': result.get('_links', {}).get('webui', ''),
                    'space': result.get('space', {}).get('name', ''),
                    'content': text_content,
                    'last_modified': result.get('version', {}).get('when', ''),
                    'type': result.get('type', 'page')
                }
                enriched_results.append(enriched_result)
        
        return enriched_results
    
    def create_context_from_content(self, content_list: List[Dict], max_tokens: int = 4000) -> str:
        """
        Create context string from content list, respecting token limits.
        
        Args:
            content_list: List of content dictionaries
            max_tokens: Maximum number of tokens for context
            
        Returns:
            Formatted context string
        """
        context_parts = []
        current_tokens = 0
        
        for content in content_list:
            # Format the content
            content_text = f"""
Title: {content['title']}
Space: {content['space']}
URL: {content['url']}
Last Modified: {content['last_modified']}

Content:
{content['content']}

---
"""
            
            content_tokens = self.count_tokens(content_text)
            
            # Check if adding this content would exceed the limit
            if current_tokens + content_tokens > max_tokens:
                break
            
            context_parts.append(content_text)
            current_tokens += content_tokens
        
        return "\n".join(context_parts)
    
    def answer_question(self, question: str, max_context_tokens: int = 4000) -> Dict:
        """
        Answer a question based on Confluence content without OpenAI.
        
        Args:
            question: User's question
            max_context_tokens: Maximum tokens for context
            
        Returns:
            Dictionary containing answer and metadata
        """
        try:
            # Search for relevant content
            logger.info(f"Searching for content related to: {question}")
            relevant_content = self.search_relevant_content(question)
            
            if not relevant_content:
                # Try to get some general content to provide context
                recent_pages = self.confluence_client.get_recent_pages(5)
                if recent_pages:
                    return {
                        'answer': f"I couldn't find specific information about '{question}' in your Confluence documentation. However, I found some recent pages that might be relevant. You may want to check your Confluence space for more specific information or try rephrasing your question with different keywords.",
                        'sources': [{'title': page.get('title', 'Untitled'), 'url': page.get('_links', {}).get('webui', ''), 'space': page.get('space', {}).get('name', '')} for page in recent_pages[:3]],
                        'confidence': 'low'
                    }
                else:
                    return {
                        'answer': f"I couldn't find any relevant information about '{question}' in your Confluence documentation. This could be because:\n\n1. The information might not be documented yet\n2. It might be in a different space or page\n3. The search terms might need to be adjusted\n\nTry searching for different keywords or check if the information exists in your Confluence space.",
                        'sources': [],
                        'confidence': 'low'
                    }
            
            # Create context from relevant content
            context = self.create_context_from_content(relevant_content, max_context_tokens)
            
            # Generate a simple answer based on the content
            answer_parts = []
            answer_parts.append(f"Based on your Confluence documentation, I found {len(relevant_content)} relevant pages:")
            answer_parts.append("")
            
            for i, content in enumerate(relevant_content[:5], 1):
                answer_parts.append(f"{i}. **{content['title']}** (in {content['space']})")
                answer_parts.append(f"   Last modified: {content['last_modified']}")
                
                # Extract a summary from the content
                content_preview = content['content'][:300] + "..." if len(content['content']) > 300 else content['content']
                answer_parts.append(f"   Preview: {content_preview}")
                answer_parts.append("")
            
            answer_parts.append("You can click on the links below to view the full content.")
            
            # Prepare sources
            sources = [
                {
                    'title': content['title'],
                    'url': content['url'],
                    'space': content['space']
                }
                for content in relevant_content
            ]
            
            return {
                'answer': "\n".join(answer_parts),
                'sources': sources,
                'confidence': 'high' if len(relevant_content) > 0 else 'medium'
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                'answer': f"I encountered an error while processing your question: {str(e)}",
                'sources': [],
                'confidence': 'low'
            }
    
    def get_recent_updates_summary(self, days: int = 7) -> Dict:
        """
        Get a summary of recent Confluence updates without OpenAI.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Summary of recent updates
        """
        try:
            recent_pages = self.confluence_client.get_recent_pages(limit=20)
            
            if not recent_pages:
                return {
                    'summary': "No recent updates found.",
                    'pages': []
                }
            
            # Create a simple summary of recent updates
            page_summaries = []
            for page in recent_pages[:10]:  # Limit to 10 most recent
                title = page.get('title', 'Untitled')
                space = page.get('space', {}).get('name', 'Unknown Space')
                last_modified = page.get('version', {}).get('when', 'Unknown')
                
                page_summaries.append({
                    'title': title,
                    'space': space,
                    'last_modified': last_modified,
                    'url': page.get('_links', {}).get('webui', '')
                })
            
            # Generate simple summary
            summary_parts = []
            summary_parts.append(f"Found {len(page_summaries)} recent pages in your Confluence space:")
            summary_parts.append("")
            
            for page in page_summaries[:5]:
                summary_parts.append(f"• {page['title']} (in {page['space']}) - {page['last_modified']}")
            
            if len(page_summaries) > 5:
                summary_parts.append(f"... and {len(page_summaries) - 5} more pages")
            
            return {
                'summary': "\n".join(summary_parts),
                'pages': page_summaries
            }
            
        except Exception as e:
            logger.error(f"Error getting recent updates: {e}")
            return {
                'summary': f"Error retrieving recent updates: {str(e)}",
                'pages': []
            }
