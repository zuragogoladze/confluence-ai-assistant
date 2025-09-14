"""
Streamlit web application for Confluence AI Assistant.
"""

import streamlit as st
import os
from dotenv import load_dotenv
from confluence_client import ConfluenceClient
from ai_assistant import ConfluenceAIAssistant
from ai_assistant_no_openai import ConfluenceAIAssistantNoOpenAI
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Confluence AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_clients():
    """Initialize Confluence and AI clients."""
    # Get configuration from environment
    confluence_url = os.getenv('CONFLUENCE_URL')
    confluence_username = os.getenv('CONFLUENCE_USERNAME')
    confluence_api_token = os.getenv('CONFLUENCE_API_TOKEN')
    confluence_space_key = os.getenv('CONFLUENCE_SPACE_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    # Validate required environment variables
    if not all([confluence_url, confluence_username, confluence_api_token, openai_api_key]):
        st.error("""
        Missing required environment variables. Please ensure you have:
        - CONFLUENCE_URL
        - CONFLUENCE_USERNAME
        - CONFLUENCE_API_TOKEN
        - OPENAI_API_KEY
        
        Copy env.example to .env and fill in your values.
        """)
        return None, None
    
    try:
        # Initialize Confluence client
        confluence_client = ConfluenceClient(
            url=confluence_url,
            username=confluence_username,
            api_token=confluence_api_token,
            space_key=confluence_space_key
        )
        
        # Test connection
        if not confluence_client.test_connection():
            st.error("Failed to connect to Confluence. Please check your credentials.")
            return None, None
        
        # Initialize AI assistant (try OpenAI first, fallback to no-OpenAI)
        try:
            ai_assistant = ConfluenceAIAssistant(
                openai_api_key=openai_api_key,
                confluence_client=confluence_client
            )
            # Test if OpenAI is working
            test_result = ai_assistant.answer_question("test", max_context_tokens=100)
            if "quota" in test_result['answer'].lower() or "error" in test_result['answer'].lower():
                raise Exception("OpenAI quota exceeded")
        except Exception as e:
            logger.warning(f"OpenAI not available ({e}), using fallback mode")
            ai_assistant = ConfluenceAIAssistantNoOpenAI(confluence_client)
        
        return confluence_client, ai_assistant
        
    except Exception as e:
        st.error(f"Error initializing clients: {str(e)}")
        return None, None

def main():
    """Main application function."""
    st.title("🤖 Confluence AI Assistant")
    st.markdown("Ask questions about your Confluence documentation and get AI-powered answers!")
    
    # Initialize clients
    if 'confluence_client' not in st.session_state or 'ai_assistant' not in st.session_state:
        with st.spinner("Initializing connection to Confluence..."):
            confluence_client, ai_assistant = initialize_clients()
            if confluence_client and ai_assistant:
                st.session_state.confluence_client = confluence_client
                st.session_state.ai_assistant = ai_assistant
                st.success("✅ Connected to Confluence successfully!")
            else:
                st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Show current configuration
        st.subheader("Current Settings")
        st.text(f"Confluence URL: {os.getenv('CONFLUENCE_URL', 'Not set')}")
        st.text(f"Space: {os.getenv('CONFLUENCE_SPACE_KEY', 'All spaces')}")
        
        # Show AI mode
        ai_mode = "OpenAI" if isinstance(st.session_state.get('ai_assistant'), ConfluenceAIAssistant) else "Search Only"
        st.text(f"AI Mode: {ai_mode}")
        if ai_mode == "Search Only":
            st.warning("⚠️ OpenAI quota exceeded. Using search-only mode.")
        
        st.subheader("Actions")
        if st.button("🔄 Refresh Connection"):
            st.session_state.pop('confluence_client', None)
            st.session_state.pop('ai_assistant', None)
            st.rerun()
        
        if st.button("📊 Recent Updates"):
            with st.spinner("Getting recent updates..."):
                recent_updates = st.session_state.ai_assistant.get_recent_updates_summary()
                st.subheader("Recent Updates Summary")
                st.write(recent_updates['summary'])
                
                if recent_updates['pages']:
                    st.subheader("Recent Pages")
                    for page in recent_updates['pages'][:5]:
                        st.write(f"• [{page['title']}]({page['url']}) - {page['space']}")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["💬 Ask Questions", "🔍 Search Content", "📈 Analytics"])
    
    with tab1:
        st.header("Ask Questions About Your Documentation")
        
        # Question input
        question = st.text_area(
            "What would you like to know?",
            placeholder="e.g., How do I set up authentication? What are the API endpoints?",
            height=100
        )
        
        # Advanced options
        with st.expander("Advanced Options"):
            max_context_tokens = st.slider(
                "Maximum context tokens",
                min_value=1000,
                max_value=8000,
                value=4000,
                help="Higher values may provide more context but cost more"
            )
        
        if st.button("🚀 Get Answer", type="primary"):
            if question.strip():
                with st.spinner("Searching Confluence and generating answer..."):
                    result = st.session_state.ai_assistant.answer_question(
                        question, 
                        max_context_tokens=max_context_tokens
                    )
                
                # Display answer
                st.subheader("Answer")
                st.write(result['answer'])
                
                # Display sources
                if result['sources']:
                    st.subheader("Sources")
                    for source in result['sources']:
                        st.write(f"• [{source['title']}]({source['url']}) - {source['space']}")
                
                # Display confidence
                confidence_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}
                st.caption(f"Confidence: {confidence_emoji.get(result['confidence'], '❓')} {result['confidence'].title()}")
                
            else:
                st.warning("Please enter a question.")
    
    with tab2:
        st.header("Search Confluence Content")
        
        search_query = st.text_input("Search query", placeholder="Enter keywords to search...")
        
        if st.button("🔍 Search"):
            if search_query.strip():
                with st.spinner("Searching Confluence..."):
                    results = st.session_state.confluence_client.search_content(search_query)
                
                if results:
                    st.subheader(f"Found {len(results)} results")
                    
                    for result in results:
                        with st.expander(f"📄 {result.get('title', 'Untitled')}"):
                            st.write(f"**Space:** {result.get('space', {}).get('name', 'Unknown')}")
                            st.write(f"**Type:** {result.get('type', 'page')}")
                            st.write(f"**Last Modified:** {result.get('version', {}).get('when', 'Unknown')}")
                            
                            if result.get('_links', {}).get('webui'):
                                st.write(f"**URL:** [{result['_links']['webui']}]({result['_links']['webui']})")
                            
                            # Show content preview
                            if 'body' in result and 'storage' in result['body']:
                                content = st.session_state.confluence_client.extract_text_from_storage(
                                    result['body']['storage']['value']
                                )
                                if content:
                                    st.write("**Content Preview:**")
                                    st.write(content[:500] + "..." if len(content) > 500 else content)
                else:
                    st.info("No results found for your search query.")
            else:
                st.warning("Please enter a search query.")
    
    with tab3:
        st.header("Analytics & Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Quick Stats")
            if st.button("📊 Get Statistics"):
                with st.spinner("Gathering statistics..."):
                    # Get recent pages for basic stats
                    recent_pages = st.session_state.confluence_client.get_recent_pages(limit=50)
                    
                    if recent_pages:
                        spaces = {}
                        for page in recent_pages:
                            space_name = page.get('space', {}).get('name', 'Unknown')
                            spaces[space_name] = spaces.get(space_name, 0) + 1
                        
                        st.metric("Recent Pages", len(recent_pages))
                        st.metric("Active Spaces", len(spaces))
                        
                        st.subheader("Pages by Space")
                        for space, count in spaces.items():
                            st.write(f"• {space}: {count} pages")
                    else:
                        st.info("No recent pages found.")
        
        with col2:
            st.subheader("Recent Activity")
            if st.button("🕒 Show Recent Activity"):
                with st.spinner("Getting recent activity..."):
                    recent_updates = st.session_state.ai_assistant.get_recent_updates_summary()
                    
                    st.write("**Summary:**")
                    st.write(recent_updates['summary'])
                    
                    if recent_updates['pages']:
                        st.write("**Recent Pages:**")
                        for page in recent_updates['pages'][:10]:
                            st.write(f"• {page['title']} - {page['space']}")

if __name__ == "__main__":
    main()
