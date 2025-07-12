# Employee Knowledge Bot

## Overview

This is a Python-based Telegram bot that provides automated employee support by answering questions using a Google Sheets knowledge base. The bot uses fuzzy string matching to find relevant answers even when questions contain typos or different phrasing. It's designed to run on Replit's free hosting environment with a keep-alive mechanism to prevent sleeping.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

### Core Components
- **Telegram Bot Interface**: Handles user interactions through Telegram
- **Google Sheets Integration**: Uses Google Sheets as a knowledge base backend
- **Question Matching Engine**: Implements fuzzy string matching for intelligent question answering
- **Keep-Alive Service**: Maintains application uptime on Replit's free hosting

### Architecture Pattern
The system uses a service-oriented approach with:
- Configuration management for environment variables
- Caching layer to reduce API calls
- Async/await patterns for non-blocking operations
- Error handling and logging throughout

## Key Components

### 1. Telegram Bot Handler (`bot/telegram_bot.py`)
- **Purpose**: Main interface for user interactions
- **Features**: Command handlers, message processing, inline keyboards
- **Commands**: `/start`, `/help`, `/categories`, `/stats`, `/refresh`
- **Design**: Uses python-telegram-bot library with async handlers

### 2. Google Sheets Manager (`bot/sheets_manager.py`)
- **Purpose**: Handles Google Sheets API integration
- **Features**: Authentication, data retrieval, caching
- **Authentication**: Service account credentials from JSON
- **Caching**: Time-based cache to reduce API calls

### 3. Question Matcher (`bot/question_matcher.py`)
- **Purpose**: Intelligent question matching using fuzzy algorithms
- **Algorithm**: Uses fuzzywuzzy library with token sort ratio
- **Features**: Similarity threshold filtering, result ranking
- **Flexibility**: Handles typos and different phrasing

### 4. Configuration Management (`bot/config.py`)
- **Purpose**: Centralized configuration from environment variables
- **Features**: Required variable validation, default values
- **Security**: Handles sensitive credentials securely
- **Google Sheets Support**: Optional GOOGLE_SHEETS_CSV_URL for external data source

### 5. Keep-Alive Service (`utils/keep_alive.py`)
- **Purpose**: Prevents Replit from sleeping the application
- **Implementation**: Simple HTTP server on separate thread
- **Endpoints**: `/` (status), `/health` (health check)

## Data Flow

1. **User Question**: User sends message to Telegram bot
2. **Question Processing**: Bot receives message and cleans/processes it
3. **Knowledge Base Query**: Sheets manager retrieves cached or fresh data
4. **Fuzzy Matching**: Question matcher finds similar questions using fuzzy algorithms
5. **Response Generation**: Bot formats and sends relevant answers back to user
6. **Caching**: Results are cached to improve performance

## External Dependencies

### APIs and Services
- **Telegram Bot API**: For bot functionality and user interactions
- **Google Sheets API**: For knowledge base storage and retrieval
- **Google Drive API**: For spreadsheet access permissions

### Python Libraries
- `python-telegram-bot`: Telegram bot framework
- `gspread`: Google Sheets API client
- `pandas`: Data manipulation and analysis
- `fuzzywuzzy`: Fuzzy string matching
- `google-auth`: Google API authentication

### Environment Configuration
- `TELEGRAM_BOT_TOKEN`: Telegram bot authentication token
- `GOOGLE_SHEETS_ID`: Google Sheets document identifier
- `GOOGLE_CREDENTIALS_JSON`: Service account credentials
- Optional: `MAX_SEARCH_RESULTS`, `SIMILARITY_THRESHOLD`, `SHEET_NAME`, `CACHE_DURATION_MINUTES`

## Deployment Strategy

### Replit Hosting
- **Platform**: Designed for Replit's free hosting environment
- **Keep-Alive**: HTTP server prevents application sleeping
- **Entry Point**: `main.py` orchestrates all components
- **Environment**: Uses environment variables for configuration

### Architecture Benefits
- **Cost-Effective**: Uses free Google Sheets and Replit hosting
- **Scalable**: Modular design allows easy feature additions
- **Maintainable**: Clear separation of concerns and logging
- **Reliable**: Error handling and graceful degradation

### Performance Optimizations
- **Caching**: Reduces Google Sheets API calls
- **Fuzzy Matching**: Efficient question matching algorithms
- **Async Operations**: Non-blocking I/O for better responsiveness
- **Connection Pooling**: Reuses HTTP connections where possible

The system prioritizes simplicity, cost-effectiveness, and reliability while providing intelligent question answering capabilities for employee support scenarios.