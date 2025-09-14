# Confluence AI Assistant

A powerful Python application that connects to Confluence, retrieves documentation, and answers questions using AI. This tool helps you quickly find information in your Confluence knowledge base through natural language queries.

## Features

- 🔍 **Smart Search**: Search through Confluence content using natural language
- 🤖 **AI-Powered Answers**: Get comprehensive answers using OpenAI's GPT models
- 📊 **Analytics**: View recent updates and content statistics
- 🌐 **Web Interface**: Beautiful Streamlit-based web application
- 💻 **CLI Interface**: Command-line tool for quick queries
- 🔧 **Configurable**: Customizable settings for different use cases

## Prerequisites

- Python 3.8 or higher
- Confluence instance with API access
- OpenAI API key
- Confluence API token

## Installation

1. **Clone or download the project**:
   ```bash
   cd confluence-ai-assistant
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` file with your credentials:
   ```env
   # Confluence Configuration
   CONFLUENCE_URL=https://your-domain.atlassian.net
   CONFLUENCE_USERNAME=your-email@example.com
   CONFLUENCE_API_TOKEN=your-api-token
   
   # OpenAI Configuration
   OPENAI_API_KEY=your-openai-api-key
   
   # Optional: Space key to limit search scope
   CONFLUENCE_SPACE_KEY=YOUR_SPACE_KEY
   ```

## Getting Confluence API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a label (e.g., "Confluence AI Assistant")
4. Copy the generated token
5. Use your email as the username

## Usage

### Web Interface (Recommended)

Start the Streamlit web application:

```bash
streamlit run app.py
```

Open your browser to `http://localhost:8501` and enjoy the interactive interface!

### Command Line Interface

#### Ask a Question
```bash
python cli.py --question "How do I set up authentication?"
```

#### Search Content
```bash
python cli.py --search "API documentation"
```

#### Show Recent Updates
```bash
python cli.py --recent
```

#### Interactive Mode
```bash
python cli.py --interactive
```

### Python API

You can also use the components programmatically:

```python
from confluence_client import ConfluenceClient
from ai_assistant import ConfluenceAIAssistant

# Initialize clients
confluence_client = ConfluenceClient(
    url="https://your-domain.atlassian.net",
    username="your-email@example.com",
    api_token="your-api-token"
)

ai_assistant = ConfluenceAIAssistant(
    openai_api_key="your-openai-api-key",
    confluence_client=confluence_client
)

# Ask a question
result = ai_assistant.answer_question("How do I deploy the application?")
print(result['answer'])
```

## Configuration Options

You can customize the application behavior by setting environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFLUENCE_URL` | Required | Your Confluence base URL |
| `CONFLUENCE_USERNAME` | Required | Your Confluence username/email |
| `CONFLUENCE_API_TOKEN` | Required | Your Confluence API token |
| `CONFLUENCE_SPACE_KEY` | None | Limit search to specific space |
| `OPENAI_API_KEY` | Required | Your OpenAI API key |
| `OPENAI_MODEL` | gpt-3.5-turbo | OpenAI model to use |
| `MAX_SEARCH_RESULTS` | 10 | Maximum search results |
| `MAX_CONTEXT_TOKENS` | 4000 | Maximum context tokens for AI |
| `CHUNK_SIZE` | 1000 | Text chunk size for processing |
| `CHUNK_OVERLAP` | 200 | Overlap between text chunks |

## Project Structure

```
confluence-ai-assistant/
├── app.py                 # Streamlit web application
├── cli.py                 # Command-line interface
├── confluence_client.py   # Confluence API client
├── ai_assistant.py       # AI question answering system
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── env.example          # Environment variables template
└── README.md            # This file
```

## How It Works

1. **Content Retrieval**: The application connects to Confluence using the REST API
2. **Search & Filter**: It searches for content relevant to your question
3. **Content Processing**: Text is extracted and cleaned from HTML content
4. **AI Processing**: Relevant content is sent to OpenAI with your question
5. **Answer Generation**: AI generates a comprehensive answer with sources

## Troubleshooting

### Common Issues

**Connection Failed**
- Verify your Confluence URL is correct
- Check your username and API token
- Ensure your Confluence instance allows API access

**No Results Found**
- Try broader search terms
- Check if your space key is correct
- Verify you have access to the content

**AI Errors**
- Verify your OpenAI API key is valid
- Check your OpenAI account has sufficient credits
- Try reducing MAX_CONTEXT_TOKENS if you hit token limits

### Debug Mode

Enable debug logging by setting:
```env
LOG_LEVEL=DEBUG
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Open an issue with detailed information about your setup

## Changelog

### v1.0.0
- Initial release
- Web interface with Streamlit
- Command-line interface
- Confluence API integration
- OpenAI-powered question answering
- Content search and analytics
