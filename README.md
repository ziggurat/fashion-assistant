# 👗 Fashion Assistant - AI-Powered Fashion Recommendations

An intelligent fashion assistant application built with **Streamlit**, **SQLite**, and **AI (Claude/OpenAI)** for personalized fashion recommendations and outfit suggestions.

## ✨ Features

- **🤖 AI-Powered Recommendations**: Intelligent conversation with Claude or GPT for fashion advice
- **💬 Interactive Chat**: Natural language interface for fashion queries
- **🛍️ Product Catalog**: Browse and search through curated fashion items
- **👗 Outfit Planning**: Get complete outfit suggestions based on occasion, style, and budget
- **📦 Inventory Management**: Real-time stock checking and availability
- **🎨 Style Analysis**: Compatibility checking for outfit combinations

## 🏗️ Project Structure

```
fashion-assistant/
├── app/
│   ├── main.py          # Streamlit web application - main entry point with chat UI and product display
│   ├── agent.py         # AI agent using LangChain with Claude/OpenAI integration for fashion recommendations
│   ├── database.py      # SQLite database models, connection, and sample data seeding
│   ├── config.py        # Application configuration and environment variable management
│   ├── services.py      # Business logic: product search, inventory checking, style compatibility analysis
│   ├── utils.py         # UI utilities: product card display, formatting helpers, emoji functions
│   └── __init__.py      # Package initialization
├── data/                # SQLite database files (auto-generated)
├── .env                 # Environment variables (API keys, database path)
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker container configuration
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

### 📁 Component Details

- **`app/main.py`**: The main Streamlit application providing:
  - Chat interface for user interactions with the AI assistant
  - Product catalog browsing with sidebar filters
  - Responsive layout with chat history and product display columns
  - Session management for conversations and product recommendations

- **`app/agent.py`**: AI agent implementation featuring:
  - LangChain integration with Claude (Anthropic) or GPT (OpenAI)
  - Tools for product search, inventory verification, and image analysis
  - System prompt optimized for fashion expertise and natural conversation
  - Asynchronous message processing for responsive chat

- **`app/database.py`**: Data persistence layer including:
  - SQLAlchemy ORM with SQLite database
  - Product model with comprehensive attributes (colors, styles, occasions, pricing)
  - Automatic seeding of sample fashion catalog (10 products)
  - Database connection management and utilities

- **`app/services.py`**: Core business logic providing:
  - Advanced product search with multiple filter criteria
  - Real-time inventory availability checking
  - Outfit compatibility analysis and scoring
  - Color and style matching algorithms

- **`app/utils.py`**: User interface helpers including:
  - Product card rendering with images, attributes, and pricing
  - Price formatting and currency display
  - Color and category emoji mappings for visual enhancement
  - Responsive UI component functions

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker (optional, but recommended)
- Anthropic API key (for Claude) or OpenAI API key (for GPT) or Google API key (for gemini)

### 1. Environment Setup

Create a `.env` file in the root directory:

```bash
# For Claude (default)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Or for OpenAI (alternative)
OPENAI_API_KEY=your_openai_api_key_here

GOOGLE_API_KEY=your_google_api_key_here
```

### 2. Running with Docker (Recommended)

Build and run the containerized application:

```bash
# Build the Docker image
docker build -t fashion-assistant .

# Run the application
docker run -p 8501:8501 --env-file .env -v $(pwd)/data:/app/data fashion-assistant
```

**Alternative Docker command** (with inline environment variable):

```bash
docker run -p 8501:8501 -e ANTHROPIC_API_KEY=your_api_key fashion-assistant
```

The application will be available at: **http://localhost:8501**

### 3. Running Directly with Streamlit

For local development or quick testing:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit application
streamlit run app/main.py
```

The application will automatically open in your default browser at: **http://localhost:8501**

## 💡 Usage Guide

### Sample Queries

The AI assistant can help with:
- "Show me elegant dresses for a formal event"
- "I need comfortable shoes for everyday wear under $80"
- "What accessories would match this red dress?"
- "Suggest a complete outfit for a summer party"
- "Find black pants that are professional looking"

### Key Functionality

- **Smart Search**: Filter by category, color, style, occasion, and price range
- **Inventory Awareness**: Only recommends products that are in stock
- **Style Compatibility**: Analyzes how well different items work together
- **Conversation Memory**: Maintains context throughout the chat session
- **Visual Product Cards**: Rich display with images, details, and availability

### Resetting Conversations

Use the "🔄 Nueva Conversación" button in the sidebar to start fresh conversations.

## 🗄️ Database

The application uses SQLite with a pre-seeded catalog of 10 sample products:

- **3 Dresses**: Evening gown, floral midi dress, classic cocktail dress
- **3 Shoes**: Black stilettos, gold sandals, nude heels
- **2 Accessories**: Gold clutch, black leather handbag
- **1 Pants**: Black formal trousers
- **1 Blouse**: White silk blouse

### Database Location

- **Docker**: `/app/data/fashion_catalog.db`
- **Local**: `./data/fashion_catalog.db` (automatically created)

### Managing Data

```bash
# Reset database (removes all data and recreates sample catalog)
rm -f data/fashion_catalog.db

# Database will be recreated automatically on next application start
```

## 🔧 Customization

### Switching AI Providers

Edit `app/config.py` or environment variables:

```python
# In app/config.py
DEFAULT_LLM_PROVIDER = "anthropic"  # or "openai"
DEFAULT_MODEL = "claude-3-sonnet-20240229"  # or "gpt-4-turbo"
```

### Adding Products

Modify the `seed_sample_data()` function in `app/database.py` to add more products to the catalog.

### Styling and UI

Customize the Streamlit interface by modifying the CSS and layout in `app/main.py`.

## 🐛 Troubleshooting

### Application Won't Start

**Check API Key**:
```bash
# Verify .env file exists and contains valid keys
cat .env
```

**Docker Issues**:
```bash
# Check Docker is running
docker ps

# View container logs
docker logs <container_id>

# Rebuild and restart
docker build -t fashion-assistant .
docker run -p 8501:8501 --env-file .env fashion-assistant
```

### No Products Displayed

**Reset Database**:
```bash
# Remove existing database to trigger reseeding
rm -f data/fashion_catalog.db
```

**Check File Permissions** (Docker):
```bash
# Ensure data directory is writable
docker run -it --rm -v $(pwd)/data:/app/data alpine ls -la /app/data/
```

### API Connection Errors

**Network Issues**: Ensure your environment can reach Anthropic/OpenAI APIs
**Rate Limits**: Check your API usage limits and billing status
**Model Availability**: Verify the configured model is available in your region

## 📊 Technical Details

- **Frontend**: Streamlit for responsive web interface
- **Backend**: Pure Python with async/await patterns
- **Database**: SQLite with SQLAlchemy ORM
- **AI Integration**: LangChain framework with Claude/OpenAI models
- **Containerization**: Docker for consistent deployment
- **Dependencies**: Managed via requirements.txt (see file for full list)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (both Docker and direct Streamlit modes)
5. Submit a pull request

## 📄 License

MIT License - see repository for details.

## 💬 Support

For questions or issues:
- Open a GitHub issue
- Check the troubleshooting section above
- Review the code comments for implementation details

---

