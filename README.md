# Employee Knowledge Bot

A free Python Telegram bot that answers employee questions using a CSV knowledge base (local file or Google Sheets). Designed to run on Replit's free hosting environment.

## Features

- 🤖 **Telegram Bot Integration**: Responds to employee questions in real-time
- 📊 **Flexible Data Sources**: Supports both local CSV files and Google Sheets
- 🔍 **Fuzzy String Matching**: Finds relevant answers even with typos or different phrasing
- 📋 **Category Support**: Organizes questions by categories for better navigation
- 🔄 **Auto-Caching**: Caches data to reduce API calls and improve performance
- 🛡️ **Error Handling**: Graceful handling of API failures and edge cases
- 📈 **Statistics**: Provides insights into knowledge base usage and content
- 🔄 **Real-time Updates**: Google Sheets integration allows live updates without bot restart

## Setup Instructions

### 1. Prerequisites

- Replit account (free)
- Google Cloud Console access (free)
- Telegram account

### 2. Create a Telegram Bot

1. Message @BotFather on Telegram
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Save the bot token for later

### 3. Setup Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Sheets API
4. Create a Service Account:
   - Go to IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Fill in details and create
   - Generate a JSON key file
5. Share your Google Sheet with the service account email

### 4. Prepare Your Knowledge Base

Create a Google Sheet with the following columns:
- **Category**: Question category (e.g., "HR", "IT", "Policy")
- **Question**: The question text
- **Answer**: The answer text
- **Priority**: Numeric priority (1-10, optional)
- **Last Updated**: Date of last update (optional)

Example:
