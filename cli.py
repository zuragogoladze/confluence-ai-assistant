"""
Command-line interface for Confluence AI Assistant.
"""

import argparse
import sys
from typing import Optional
from config import Config
from confluence_client import ConfluenceClient
from ai_assistant import ConfluenceAIAssistant


def setup_cli():
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Confluence AI Assistant - Ask questions about your Confluence documentation"
    )
    
    parser.add_argument(
        '--question', '-q',
        type=str,
        help='Question to ask about Confluence content'
    )
    
    parser.add_argument(
        '--search', '-s',
        type=str,
        help='Search query for Confluence content'
    )
    
    parser.add_argument(
        '--recent', '-r',
        action='store_true',
        help='Show recent updates summary'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Start interactive mode'
    )
    
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=4000,
        help='Maximum context tokens (default: 4000)'
    )
    
    parser.add_argument(
        '--max-results',
        type=int,
        default=10,
        help='Maximum search results (default: 10)'
    )
    
    return parser


def validate_config():
    """Validate configuration and exit if invalid."""
    is_valid, errors = Config.validate()
    
    if not is_valid:
        print("Configuration Error:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease check your .env file or environment variables.")
        sys.exit(1)


def initialize_clients():
    """Initialize Confluence and AI clients."""
    try:
        confluence_config = Config.get_confluence_config()
        confluence_client = ConfluenceClient(**confluence_config)
        
        if not confluence_client.test_connection():
            print("Error: Failed to connect to Confluence. Please check your credentials.")
            sys.exit(1)
        
        openai_config = Config.get_openai_config()
        ai_assistant = ConfluenceAIAssistant(
            openai_api_key=openai_config['api_key'],
            confluence_client=confluence_client
        )
        
        return confluence_client, ai_assistant
        
    except Exception as e:
        print(f"Error initializing clients: {e}")
        sys.exit(1)


def ask_question(ai_assistant: ConfluenceAIAssistant, question: str, max_tokens: int):
    """Ask a question and display the answer."""
    print(f"\nQuestion: {question}")
    print("=" * 50)
    
    result = ai_assistant.answer_question(question, max_tokens)
    
    print(f"\nAnswer:\n{result['answer']}")
    
    if result['sources']:
        print(f"\nSources:")
        for source in result['sources']:
            print(f"  • {source['title']} - {source['space']}")
            print(f"    {source['url']}")
    
    print(f"\nConfidence: {result['confidence'].title()}")


def search_content(confluence_client: ConfluenceClient, query: str, max_results: int):
    """Search for content and display results."""
    print(f"\nSearching for: {query}")
    print("=" * 50)
    
    results = confluence_client.search_content(query, limit=max_results)
    
    if not results:
        print("No results found.")
        return
    
    print(f"Found {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.get('title', 'Untitled')}")
        print(f"   Space: {result.get('space', {}).get('name', 'Unknown')}")
        print(f"   Type: {result.get('type', 'page')}")
        print(f"   Last Modified: {result.get('version', {}).get('when', 'Unknown')}")
        
        if result.get('_links', {}).get('webui'):
            print(f"   URL: {result['_links']['webui']}")
        
        print()


def show_recent_updates(ai_assistant: ConfluenceAIAssistant):
    """Show recent updates summary."""
    print("\nRecent Updates Summary")
    print("=" * 50)
    
    recent_updates = ai_assistant.get_recent_updates_summary()
    
    print(f"\nSummary:\n{recent_updates['summary']}")
    
    if recent_updates['pages']:
        print(f"\nRecent Pages:")
        for page in recent_updates['pages'][:10]:
            print(f"  • {page['title']} - {page['space']} ({page['last_modified']})")


def interactive_mode(confluence_client: ConfluenceClient, ai_assistant: ConfluenceAIAssistant):
    """Start interactive mode."""
    print("\n🤖 Confluence AI Assistant - Interactive Mode")
    print("Type 'help' for commands, 'quit' to exit")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if user_input.lower() == 'help':
                print("\nAvailable commands:")
                print("  ask <question>  - Ask a question about Confluence content")
                print("  search <query>  - Search for content")
                print("  recent         - Show recent updates")
                print("  help           - Show this help")
                print("  quit/exit/q    - Exit the program")
                continue
            
            if user_input.lower() == 'recent':
                show_recent_updates(ai_assistant)
                continue
            
            if user_input.startswith('ask '):
                question = user_input[4:].strip()
                if question:
                    ask_question(ai_assistant, question, Config.MAX_CONTEXT_TOKENS)
                else:
                    print("Please provide a question after 'ask'")
                continue
            
            if user_input.startswith('search '):
                query = user_input[7:].strip()
                if query:
                    search_content(confluence_client, query, Config.MAX_SEARCH_RESULTS)
                else:
                    print("Please provide a search query after 'search'")
                continue
            
            # Default: treat as a question
            if user_input:
                ask_question(ai_assistant, user_input, Config.MAX_CONTEXT_TOKENS)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main CLI function."""
    parser = setup_cli()
    args = parser.parse_args()
    
    # Validate configuration
    validate_config()
    
    # Initialize clients
    confluence_client, ai_assistant = initialize_clients()
    
    # Handle different modes
    if args.interactive:
        interactive_mode(confluence_client, ai_assistant)
    elif args.question:
        ask_question(ai_assistant, args.question, args.max_tokens)
    elif args.search:
        search_content(confluence_client, args.search, args.max_results)
    elif args.recent:
        show_recent_updates(ai_assistant)
    else:
        # No arguments provided, show help
        parser.print_help()


if __name__ == "__main__":
    main()
