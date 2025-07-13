"""
Telegram bot implementation for employee knowledge base.
Handles user interactions and provides answers from Google Sheets.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from typing import List, Dict
import asyncio
from datetime import datetime

from .sheets_manager import CSVManager
from .question_matcher import QuestionMatcher

logger = logging.getLogger(__name__)

class TelegramBot:
    """Main Telegram bot class."""
    
    def __init__(self, config):
        """Initialize the Telegram bot."""
        self.config = config
        self.csv_manager = CSVManager(config)
        self.question_matcher = QuestionMatcher(config)
        self.application = None
        self._setup_bot()
    
    def _setup_bot(self):
        """Setup the Telegram bot application."""
        try:
            # Create application
            self.application = Application.builder().token(self.config.telegram_token).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("categories", self.categories_command))
            self.application.add_handler(CommandHandler("stats", self.stats_command))
            self.application.add_handler(CommandHandler("refresh", self.refresh_command))
            
            # Callback query handler for buttons
            self.application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Message handler for questions
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_question))
            
            logger.info("Настройка бота Telegram завершена")
            
        except Exception as e:
            logger.error(f"Failed to setup Telegram bot: {str(e)}")
            raise
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = """
🤖 **Employee Knowledge Bot**

Привет!Я Voltic - твой цифровой напарник-электромонтер! ✨

**Как со мной работать:**
• Просто введи свой вопрос, и я поищу информацию в нашей базе знаний.
• Используйте /categories, чтобы увидеть доступные темы.
• Используйте /help, чтобы получить дополнительную информацию.

**Например:**
• "Напиши мне закон ОМА"
• "Как рассчитать силу тока?"
• "Какое напряжение в домашней розетке?"

Расскажите, что вас интересует!  🚀
        """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = """
📚 **Available Commands:**

/start - Welcome message and instructions
/help - Show this help message
/categories - View available question categories
/stats - Show knowledge base statistics
/refresh - Refresh the knowledge base cache

**How to ask questions:**
Just type your question naturally! I'll search for the most relevant answers using fuzzy matching.

**Tips for better results:**
• Use clear, specific questions
• Include relevant keywords
• Try different phrasings if you don't get good results

**Example questions:**
• "vacation policy"
• "how to submit expenses"
• "IT support contact"
• "meeting room booking"

If you can't find what you're looking for, try rephrasing your question or contact HR directly.
        """
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def categories_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /categories command."""
        try:
            knowledge_base = self.csv_manager.get_knowledge_base()
            categories = self.question_matcher.get_categories(knowledge_base)
            
            if not categories:
                await update.message.reply_text("No categories available at the moment.")
                return
            
            # Create inline keyboard with categories
            keyboard = []
            for i in range(0, len(categories), 2):
                row = [InlineKeyboardButton(categories[i], callback_data=f"cat_{categories[i]}")]
                if i + 1 < len(categories):
                    row.append(InlineKeyboardButton(categories[i + 1], callback_data=f"cat_{categories[i + 1]}"))
                keyboard.append(row)
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = "📋 **Available Categories:**\n\nClick on a category to browse questions:"
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in categories command: {str(e)}")
            await update.message.reply_text("Sorry, I couldn't retrieve the categories right now. Please try again later.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        try:
            stats = self.csv_manager.get_stats()
            
            if "error" in stats:
                await update.message.reply_text("Sorry, I couldn't retrieve the statistics right now.")
                return
            
            message = f"""
📊 **Knowledge Base Statistics:**

• Total Questions: {stats.get('total_questions', 0)}
• Categories: {stats.get('categories', 0)}
• Last Updated: {stats.get('last_updated', 'Unknown')}

**Category Breakdown:**
            """
            
            if "category_breakdown" in stats:
                for category, count in stats["category_breakdown"].items():
                    message += f"• {category}: {count} questions\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in stats command: {str(e)}")
            await update.message.reply_text("Sorry, I couldn't retrieve the statistics right now. Please try again later.")
    
    async def refresh_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /refresh command."""
        try:
            await update.message.reply_text("🔄 Refreshing knowledge base...")
            
            self.csv_manager.refresh_cache()
            
            await update.message.reply_text("✅ Knowledge base refreshed successfully!")
            
        except Exception as e:
            logger.error(f"Error in refresh command: {str(e)}")
            await update.message.reply_text("❌ Failed to refresh knowledge base. Please try again later.")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks."""
        query = update.callback_query
        await query.answer()
        
        try:
            data = query.data
            
            if data.startswith("cat_"):
                # Category selection
                category = data[4:]  # Remove "cat_" prefix
                
                knowledge_base = self.csv_manager.get_knowledge_base()
                category_questions = knowledge_base[
                    knowledge_base['Category'].str.lower() == category.lower()
                ]
                
                if category_questions.empty:
                    await query.edit_message_text(f"No questions found in category: {category}")
                    return
                
                # Show questions in this category
                message = f"📋 **Questions in {category}:**\n\n"
                
                for idx, row in category_questions.head(10).iterrows():
                    message += f"• {row['Question']}\n"
                
                if len(category_questions) > 10:
                    message += f"\n... and {len(category_questions) - 10} more questions"
                
                message += "\n\nJust type your question to get an answer!"
                
                await query.edit_message_text(message, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error in button callback: {str(e)}")
            await query.edit_message_text("Sorry, something went wrong. Please try again.")
    
    async def handle_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user questions."""
        user_question = update.message.text
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logger.info(f"Question from user {username} ({user_id}): {user_question}")
        
        try:
            # Get knowledge base
            knowledge_base = self.csv_manager.get_knowledge_base()
            
            if knowledge_base.empty:
                await update.message.reply_text(
                    "Sorry, the knowledge base is currently empty. Please try again later or contact support."
                )
                return
            
            # Find matches
            matches = self.question_matcher.find_matches(user_question, knowledge_base)
            
            if not matches:
                # No matches found
                await self._send_no_matches_response(update, user_question)
                return
            
            # Send the best match
            best_match = matches[0]
            await self._send_answer(update, best_match, len(matches))
            
            # If there are multiple good matches, offer alternatives
            if len(matches) > 1:
                await self._send_alternative_answers(update, matches[1:])
                
        except Exception as e:
            logger.error(f"Error handling question: {str(e)}")
            await update.message.reply_text(
                "Sorry, I encountered an error while searching for your answer. Please try again later."
            )
    
    async def _send_answer(self, update: Update, match: Dict, total_matches: int):
        """Send the answer to the user."""
        answer_message = f"""
🎯 **Answer Found** (Score: {match['score']}%)

**Question:** {match['question']}

**Answer:** {match['answer']}

**Category:** {match['category']}
        """
        
        if total_matches > 1:
            answer_message += f"\n💡 Found {total_matches} related answers"
        
        await update.message.reply_text(answer_message, parse_mode='Markdown')
    
    async def _send_alternative_answers(self, update: Update, alternatives: List[Dict]):
        """Send alternative answers if available."""
        if not alternatives:
            return
        
        alt_message = "🔍 **Other related answers:**\n\n"
        
        for i, alt in enumerate(alternatives[:3], 1):  # Show max 3 alternatives
            alt_message += f"**{i}.** {alt['question']}\n"
            alt_message += f"*Score: {alt['score']}%*\n\n"
        
        alt_message += "Type a more specific question to get the exact answer you need!"
        
        await update.message.reply_text(alt_message, parse_mode='Markdown')
    
    async def _send_no_matches_response(self, update: Update, user_question: str):
        """Send response when no matches are found."""
        no_match_message = f"""
🤔 **No direct matches found**

I couldn't find a good answer for: "{user_question}"

**Try these suggestions:**
• Rephrase your question with different keywords
• Use more specific terms
• Check available categories with /categories
• Contact HR or IT support directly

**Example rephrasing:**
• Instead of "time off" try "vacation policy" or "leave request"
• Instead of "computer problem" try "IT support" or "technical issue"
        """
        
        await update.message.reply_text(no_match_message, parse_mode='Markdown')
    
    async def run(self):
        """Start the bot."""
        try:
            logger.info("Starting Telegram bot...")
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            
            # Start polling
            await self.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
            logger.info("Bot is running and polling for updates...")
            
            # Keep the bot running
            import signal
            import asyncio
            
            # Create a future that will be resolved when a signal is received
            stop_signals = (signal.SIGTERM, signal.SIGINT)
            loop = asyncio.get_running_loop()
            
            for sig in stop_signals:
                loop.add_signal_handler(sig, lambda s=sig: loop.stop())
            
            # Run until stopped
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                pass
            
        except Exception as e:
            logger.error(f"Error running bot: {str(e)}")
            raise
        finally:
            # Cleanup
            await self.application.stop()
            await self.application.shutdown()
