"""
Телеграм-бот помощник электромонтера.
"""
from groq import Groq
import httpx
import os
import logging #Модуль стандартной библиотеки Python для логирования событий
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from typing import List, Dict



from .sheets_manager import CSVManager
from .question_matcher import QuestionMatcher

logger = logging.getLogger(__name__)

class TelegramBot:
    """Main Telegram bot class."""

    def __init__(self, config):
        """Инициализация Telegram-бота."""
        self.config = config
        self.csv_manager = CSVManager(config)
        self.question_matcher = QuestionMatcher(config)
        #self.application = None
        #self._setup_bot()
        # Инициализация Groq клиента
        self.groq_api_key = config.groq_api_key or os.getenv("GROQ_API_KEY")
        self.groq_client = None
        if self.groq_api_key:
            try:
                # Инициализация Groq клиента только с API ключом (для Railway совместимости)
                self.groq_client = Groq(
                    api_key=self.groq_api_key,
                    timeout=30.0
                )
                logger.info("Groq API успешно инициализирован")

                        # Проверка доступных моделей
                try:
                    models = self.groq_client.models.list()
                    logger.info(f"Доступные модели: {[m.id for m in models.data]}")
                except Exception as e:
                    logger.warning(f"Ошибка проверки моделей: {str(e)}")
            except Exception as e:
                logger.error(f"Ошибка инициализации Groq: {str(e)}")
                logger.error(f"Тип ошибки: {type(e).__name__}")

        self.application = None
        self._setup_bot()

    def _setup_bot(self):
        """Настройка приложения Telegram-бот."""
        try:
            # Добавить приложение
            self.application = Application.builder().token(self.config.telegram_token).build()

            # Добавить обработчики
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
            logger.error(f"Не удалось настроить Telegram-бот: {str(e)}")
            raise

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = """

Привет!Я Voltic🤖- твой цифровой напарник-электромонтер! ✨

**Как со мной работать:**
• Просто введи свой вопрос, и я поищу информацию в нашей базе знаний.
• Используйте /categories, чтобы увидеть доступные темы.
• Используйте /help, чтобы получить дополнительную информацию.

Давай попробуем, это просто!  🚀
        """

        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def get_groq_response(self, user_question: str) -> str:
        """Получить ответ от Groq API."""
        # Добавляем подробное логирование
        logger.info(f"Получен запрос к Groq API: {user_question}")

        if not self.groq_client:
            logger.error("Groq клиент не инициализирован")
            return "Извините, сервис ИИ временно недоступен."

        if not self.groq_api_key:
            logger.error("API ключ Groq не установлен")
            return "Извините, конфигурация ИИ не завершена."

        try:
            logger.info(f"Отправка запроса к модели: meta-llama/llama-4-scout-17b-16e-instruct")
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system",
                     "content": "Ты - профессиональный помощник электромонтера. Отвечай на вопросы по электротехнике точно, кратко и по делу на русском языке."},
                    {"role": "user", "content": user_question}
                ],
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0.3,
                max_tokens=512
            )
            response = chat_completion.choices[0].message.content
            logger.info(f"Получен ответ от Groq API: {response[:100]}...")
            return response
        except Exception as e:
            logger.exception(f"КРИТИЧЕСКАЯ ОШИБКА при запросе к Groq API: {str(e)}")
            return "Извините, произошла ошибка при обработке вашего запроса."

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
            logger.error(f"Ошибка в команде категорий: {str(e)}")
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
            logger.error(f"Ошибка в команде статистики: {str(e)}")
            await update.message.reply_text("Извините, мне не удалось получить статистику прямо сейчас. Попробуйте позже.")

    async def refresh_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /refresh command."""
        try:
            await update.message.reply_text("🔄 Обновление базы знаний...")

            self.csv_manager.refresh_cache()

            await update.message.reply_text("✅ База знаний успешно обновлена!")

        except Exception as e:
            logger.error(f"Ошибка в команде обновления: {str(e)}")
            await update.message.reply_text("❌ Не удалось обновить базу знаний. Повторите попытку позже.")

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
                    await query.edit_message_text(f"В категории не найдено вопросов: {category}")
                    return

                # Show questions in this category
                message = f"📋 **Вопросы в {category}:**\n\n"

                for idx, row in category_questions.head(10).iterrows():
                    message += f"• {row['Question']}\n"

                if len(category_questions) > 10:
                    message += f"\n... и {len(category_questions) - 10} еще вопросы"

                message += "\n\nПросто введите свой вопрос и получите ответ!"

                await query.edit_message_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Ошибка в кнопке обратного вызова: {str(e)}")
            await query.edit_message_text("Извините, что-то пошло не так. Попробуйте ещё раз.")

    async def handle_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user questions."""
        user_question = update.message.text
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"

        logger.info(f"Вопрос от пользователя {username} ({user_id}): {user_question}")

        try:
            # Get knowledge base
            knowledge_base = self.csv_manager.get_knowledge_base()

            if knowledge_base.empty:
                await update.message.reply_text(
                    "Извините, база знаний сейчас пуста или обновляется.Попробуйте обратится немного позже."
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
            logger.error(f"Вопрос об обработке ошибок: {str(e)}")
            await update.message.reply_text(
                "Извините, при поиске ответа произошла ошибка. Повторите попытку позже."
            )

    async def _send_answer(self, update: Update, match: Dict, total_matches: int):
        """Send the answer to the user."""
        answer_message = f"""
🎯 **Вот что мне удалось найти!


{match['answer']}

**Категория:** {match['category']}
**(Совпадение: {match['score']}%)
        """

        #**Твой вопрос:** {match['question']}

        if total_matches > 1:
            answer_message += f"\n💡 Найдены {total_matches} похожих ответа"

        await update.message.reply_text(answer_message, parse_mode='Markdown')

    async def _send_alternative_answers(self, update: Update, alternatives: List[Dict]):
        """Send alternative answers if available."""
        if not alternatives:
            return

        alt_message = "🔍 **Другие похожие вопросы:**\n\n"

        for i, alt in enumerate(alternatives[:3], 1):  # Show max 3 alternatives
            alt_message += f"**{i}.** {alt['question']}\n"
            alt_message += f"*Совпадение: {alt['score']}%*\n\n"

        alt_message += "Введите более конкретный вопрос, чтобы получить точный ответ, который вам нужен!"

        await update.message.reply_text(alt_message, parse_mode='Markdown')

    async def _send_no_matches_response(self, update: Update, user_question: str):
        """Send response when no matches are found and use Groq API to get an answer."""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"

        # Логируем вопрос в CSV как неотвеченный
        self.csv_manager.log_unanswered_question(user_question, user_id, username)

        # Отправляем сообщение о том, что ищем ответ через ИИ
        await update.message.reply_text("🔍 Не найдено в базе знаний... Запрашиваю у ИИ-помощника...")

        # Получаем ответ от Groq
        ai_response = await self.get_groq_response(user_question)

        # Сохраняем новый вопрос и ответ в CSV
        self.csv_manager.add_question_answer(user_question, ai_response, "AI_Generated")

        # Формируем и отправляем ответ пользователю
        response_message = f"""
    🤖 **Ответ от ИИ-помощника:**
    {ai_response}

    💡 Этот ответ был сгенерирован и добавлен в нашу базу знаний.
    Если ответ неточный или неполный, пожалуйста, уточните свой вопрос.
        """
        await update.message.reply_text(response_message, parse_mode='Markdown')

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
