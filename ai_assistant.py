"""
AI Assistant for answering questions based on Confluence data.
"""

import os
import tiktoken
from typing import List, Dict, Optional
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceAIAssistant:
    """AI Assistant that answers questions based on Confluence content."""
    
    def __init__(self, openai_api_key: str, confluence_client):
        """
        Initialize the AI assistant.
        
        Args:
            openai_api_key: OpenAI API key
            confluence_client: ConfluenceClient instance
        """
        self.client = OpenAI(api_key=openai_api_key)
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
        Answer a question based on Confluence content.
        
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
            
            # Prepare the prompt
            system_prompt = """You are a helpful assistant that answers questions based on Confluence documentation. 
            Use the provided context to answer the user's question accurately and comprehensively. 
            If the context doesn't contain enough information to answer the question, say so clearly.
            Always cite the sources when possible by mentioning the page titles.
            Be concise but thorough in your responses."""
            
            user_prompt = f"""Context from Confluence documentation:

{context}

Question: {question}

Please provide a comprehensive answer based on the context above. If you reference specific information, mention which page it came from."""

            # Get answer from OpenAI using mini model
            logger.info("Generating answer using OpenAI mini model...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            answer = response.choices[0].message.content
            
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
                'answer': answer,
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
        Get a summary of recent Confluence updates.
        
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
            
            # Create a summary of recent updates
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
            
            # Generate AI summary
            context = "\n".join([
                f"- {p['title']} (in {p['space']}) - {p['last_modified']}"
                for p in page_summaries
            ])
            
            prompt = f"""Based on these recent Confluence page updates, provide a brief summary of what's been happening:

{context}

Please provide a concise summary of the recent activity and key themes."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            return {
                'summary': response.choices[0].message.content,
                'pages': page_summaries
            }
            
        except Exception as e:
            logger.error(f"Error getting recent updates: {e}")
            return {
                'summary': f"Error retrieving recent updates: {str(e)}",
                'pages': []
            }
