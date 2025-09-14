"""
Example usage of Confluence AI Assistant components.
"""

import os
from dotenv import load_dotenv
from confluence_client import ConfluenceClient
from ai_assistant import ConfluenceAIAssistant
from config import Config

# Load environment variables
load_dotenv()


def example_basic_usage():
    """Basic usage example."""
    print("=== Basic Usage Example ===")
    
    # Initialize clients
    confluence_config = Config.get_confluence_config()
    confluence_client = ConfluenceClient(**confluence_config)
    
    openai_config = Config.get_openai_config()
    ai_assistant = ConfluenceAIAssistant(
        openai_api_key=openai_config['api_key'],
        confluence_client=confluence_client
    )
    
    # Test connection
    if not confluence_client.test_connection():
        print("❌ Failed to connect to Confluence")
        return
    
    print("✅ Connected to Confluence successfully!")
    
    # Ask a question
    question = "What are the main features of our product?"
    print(f"\nQuestion: {question}")
    
    result = ai_assistant.answer_question(question)
    print(f"\nAnswer: {result['answer']}")
    
    if result['sources']:
        print(f"\nSources:")
        for source in result['sources']:
            print(f"  • {source['title']} - {source['space']}")


def example_search_content():
    """Example of searching content."""
    print("\n=== Search Content Example ===")
    
    confluence_config = Config.get_confluence_config()
    confluence_client = ConfluenceClient(**confluence_config)
    
    if not confluence_client.test_connection():
        print("❌ Failed to connect to Confluence")
        return
    
    # Search for content
    search_query = "API documentation"
    print(f"Searching for: {search_query}")
    
    results = confluence_client.search_content(search_query, limit=5)
    
    if results:
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.get('title', 'Untitled')}")
            print(f"   Space: {result.get('space', {}).get('name', 'Unknown')}")
            print(f"   Type: {result.get('type', 'page')}")
    else:
        print("No results found.")


def example_recent_updates():
    """Example of getting recent updates."""
    print("\n=== Recent Updates Example ===")
    
    confluence_config = Config.get_confluence_config()
    confluence_client = ConfluenceClient(**confluence_config)
    
    openai_config = Config.get_openai_config()
    ai_assistant = ConfluenceAIAssistant(
        openai_api_key=openai_config['api_key'],
        confluence_client=confluence_client
    )
    
    if not confluence_client.test_connection():
        print("❌ Failed to connect to Confluence")
        return
    
    # Get recent updates
    recent_updates = ai_assistant.get_recent_updates_summary()
    
    print("Recent Updates Summary:")
    print(recent_updates['summary'])
    
    if recent_updates['pages']:
        print(f"\nRecent Pages ({len(recent_updates['pages'])}):")
        for page in recent_updates['pages'][:5]:
            print(f"  • {page['title']} - {page['space']}")


def example_space_specific_search():
    """Example of searching within a specific space."""
    print("\n=== Space-Specific Search Example ===")
    
    # Initialize with space key
    confluence_config = Config.get_confluence_config()
    confluence_client = ConfluenceClient(
        url=confluence_config['url'],
        username=confluence_config['username'],
        api_token=confluence_config['api_token'],
        space_key="YOUR_SPACE_KEY"  # Replace with actual space key
    )
    
    if not confluence_client.test_connection():
        print("❌ Failed to connect to Confluence")
        return
    
    # Search within specific space
    search_query = "user guide"
    print(f"Searching for '{search_query}' in specific space...")
    
    results = confluence_client.search_content(search_query, limit=3)
    
    if results:
        print(f"Found {len(results)} results in the space:")
        for result in results:
            print(f"  • {result.get('title', 'Untitled')}")
    else:
        print("No results found in the specified space.")


def example_custom_parameters():
    """Example with custom parameters."""
    print("\n=== Custom Parameters Example ===")
    
    confluence_config = Config.get_confluence_config()
    confluence_client = ConfluenceClient(**confluence_config)
    
    openai_config = Config.get_openai_config()
    ai_assistant = ConfluenceAIAssistant(
        openai_api_key=openai_config['api_key'],
        confluence_client=confluence_client
    )
    
    if not confluence_client.test_connection():
        print("❌ Failed to connect to Confluence")
        return
    
    # Ask question with custom parameters
    question = "How do I troubleshoot common issues?"
    print(f"Question: {question}")
    
    # Use custom max context tokens
    result = ai_assistant.answer_question(question, max_context_tokens=2000)
    
    print(f"\nAnswer: {result['answer']}")
    print(f"Confidence: {result['confidence']}")


def example_error_handling():
    """Example of error handling."""
    print("\n=== Error Handling Example ===")
    
    try:
        # This will fail if credentials are invalid
        confluence_client = ConfluenceClient(
            url="https://invalid-url.atlassian.net",
            username="invalid@email.com",
            api_token="invalid-token"
        )
        
        if confluence_client.test_connection():
            print("✅ Connection successful")
        else:
            print("❌ Connection failed (expected)")
            
    except Exception as e:
        print(f"❌ Error occurred: {e}")


def main():
    """Run all examples."""
    print("Confluence AI Assistant - Usage Examples")
    print("=" * 50)
    
    # Validate configuration first
    is_valid, errors = Config.validate()
    if not is_valid:
        print("Configuration Error:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease check your .env file.")
        return
    
    try:
        # Run examples
        example_basic_usage()
        example_search_content()
        example_recent_updates()
        example_custom_parameters()
        example_error_handling()
        
        # Uncomment to test space-specific search
        # example_space_specific_search()
        
    except Exception as e:
        print(f"Error running examples: {e}")


if __name__ == "__main__":
    main()
