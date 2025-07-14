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

Привет!Я Voltic🤖- твой цифровой напарник-электромонтер! ✨

**Как со мной работать:**
• Просто введи свой вопрос, и я поищу информацию в нашей базе знаний.
• Используйте /categories, чтобы увидеть доступные темы.
• Используйте /help, чтобы получить дополнительную информацию.

**Например:**
• "Напиши мне закон ОМА"
• "Как рассчитать силу тока?"
• "Какое напряжение в домашней розетке?"

Давай попробуем, это просто!  🚀
        """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = """
📚 **Доступные команды:**

/start - приветственное сообщение и инструкции;
/help - справочное сообщение;
/categories - список категорий;
/stats - показать статистику базы знаний;
/refresh - обновить кэш базы знаний.

**Как задавать вопросы:**
Просто введите и отправьте свой вопрос в поле для ввода текста! Я найду наиболее релевантные ответы, используя возможные соответствия.

**Советы для достижения наилучших результатов:**
• Задавайте четкие и конкретные вопросы;
• Используйте релевантные ключевые слова;
• Попробуйте другие формулировки, если результаты неудовлетворительны.

**Примеры вопросов:**
• "Напиши закон Ома";
• "Формула для расчета мощности электродвигателя";
• "Какая допустимая перегрузка электродвигателя?".

Если Вы не нашли то, что искали, попробуйте перефразировать свой вопрос и я обязательно помогу Вам!
        """
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def categories_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /categories command."""
        try:
            knowledge_base = self.csv_manager.get_knowledge_base()
            categories = self.question_matcher.get_categories(knowledge_base)
            
            if not categories:
                await update.message.reply_text("На данный момент категории недоступны.")
                return
            
            # Create inline keyboard with categories
            keyboard = []
            for i in range(0, len(categories), 2):
                row = [InlineKeyboardButton(categories[i], callback_data=f"cat_{categories[i]}")]
                if i + 1 < len(categories):
                    row.append(InlineKeyboardButton(categories[i + 1], callback_data=f"cat_{categories[i + 1]}"))
                keyboard.append(row)
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = "📋 **Доступные категории:**\n\nНажмите на категорию, чтобы просмотреть вопросы:"
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in categories command: {str(e)}")
            await update.message.reply_text("Извините, мне не удалось получить категории прямо сейчас. Попробуйте позже.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        try:
            stats = self.csv_manager.get_stats()
            
            if "error" in stats:
                await update.message.reply_text("Извините, я не смог сейчас получить статистику.")
                return
            
            message = f"""
📊 **Статистика базы знаний:**

• Всего вопросов: {stats.get('total_questions', 0)}
• Категории: {stats.get('categories', 0)}
• Последнее обновление: {stats.get('last_updated', 'Unknown')}

**Разбивка по категориям:**
            """
            
            if "category_breakdown" in stats:
                for category, count in stats["category_breakdown"].items():
                    message += f"• {category}: {count} вопрос\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in stats command: {str(e)}")
            await update.message.reply_text("Извините, мне не удалось получить статистику прямо сейчас. Попробуйте позже.")
    
    async def refresh_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /refresh command."""
        try:
            await update.message.reply_text("🔄 Обновление базы знаний...")
            
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
🎯 **Вот что мне удалось найти!** (Score: {match['score']}%)

**Твой вопрос:** {match['question']}

**Найденный ответ:** {match['answer']}

**Категория:** {match['category']}
        """
        
        if total_matches > 1:
            answer_message += f"\n💡 Found {total_matches} related answers"
        
        await update.message.reply_text(answer_message, parse_mode='Markdown')
    
    async def _send_alternative_answers(self, update: Update, alternatives: List[Dict]):
        """Send alternative answers if available."""
        if not alternatives:
            return
        
        alt_message = "🔍 **Другие похожие ответы:**\n\n"
        
        for i, alt in enumerate(alternatives[:3], 1):  # Show max 3 alternatives
            alt_message += f"**{i}.** {alt['question']}\n"
            alt_message += f"*Score: {alt['score']}%*\n\n"
        
        alt_message += "Введите более конкретный вопрос, чтобы получить точный ответ, который вам нужен!"
        
        await update.message.reply_text(alt_message, parse_mode='Markdown')
    
    async def _send_no_matches_response(self, update: Update, user_question: str):
        """Send response when no matches are found."""
        no_match_message = f"""
🤔 **Хммм...Что-то я не смог найти хороший ответ на твой вопрос: "{user_question}"**

**👉Попробуйте следующие варианты:**
• Перефразируйте свой вопрос, используя другие ключевые слова;
• Используйте более конкретные термины;
• Проверьте доступные категории с помощью /categories.
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
