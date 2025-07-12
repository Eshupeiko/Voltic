"""
Демонстрация работы системы поиска по CSV файлу без Telegram бота.
Позволяет протестировать логику поиска ответов на вопросы.
"""

import pandas as pd
import logging
from bot.config import Config
from bot.sheets_manager import CSVManager  
from bot.question_matcher import QuestionMatcher
from utils.logger import setup_logging

def demo_search():
    """Демонстрация поиска ответов на вопросы."""
    
    # Настройка логирования
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("=== Демонстрация работы системы поиска ===")
    print()
    
    try:
        # Создаем упрощенную конфигурацию
        class DemoConfig:
            def __init__(self):
                self.csv_file_path = 'knowledge_base.csv'
                self.max_results = 3
                self.similarity_threshold = 50.0
                self.cache_duration = 30
        
        config = DemoConfig()
        
        # Инициализация компонентов
        csv_manager = CSVManager(config)
        question_matcher = QuestionMatcher(config)
        
        # Загрузка базы знаний
        print("📊 Загрузка базы знаний...")
        knowledge_base = csv_manager.get_knowledge_base()
        
        if knowledge_base.empty:
            print("❌ База знаний пуста!")
            return
        
        print(f"✅ Загружено {len(knowledge_base)} записей")
        print()
        
        # Показываем статистику
        stats = csv_manager.get_stats()
        print("📈 Статистика базы знаний:")
        print(f"   • Всего вопросов: {stats.get('total_questions', 0)}")
        print(f"   • Категорий: {stats.get('categories', 0)}")
        
        if 'category_breakdown' in stats:
            print("   • По категориям:")
            for category, count in stats['category_breakdown'].items():
                print(f"     - {category}: {count}")
        print()
        
        # Примеры вопросов для тестирования
        test_questions = [
            "как взять отпуск",
            "проблема с компьютером", 
            "какой дресс код",
            "VPN доступ",
            "болничный",
            "несуществующий вопрос"
        ]
        
        print("🔍 Тестирование поиска ответов:")
        print("=" * 50)
        
        for question in test_questions:
            print(f"\n❓ Вопрос: '{question}'")
            print("-" * 30)
            
            # Поиск ответов
            matches = question_matcher.find_matches(question, knowledge_base)
            
            if matches:
                print(f"✅ Найдено {len(matches)} совпадений:")
                for i, match in enumerate(matches, 1):
                    print(f"\n{i}. Совпадение {match['score']}%")
                    print(f"   Вопрос: {match['question']}")
                    print(f"   Ответ: {match['answer'][:100]}...")
                    print(f"   Категория: {match['category']}")
            else:
                print("❌ Совпадений не найдено")
        
        print("\n" + "=" * 50)
        print("🎯 Демонстрация завершена!")
        print()
        print("Для запуска полноценного Telegram бота:")
        print("1. Создайте бота через @BotFather в Telegram")
        print("2. Получите токен бота")
        print("3. Добавьте токен в секреты Replit")
        print("4. Запустите основное приложение")
        
    except Exception as e:
        logger.error(f"Ошибка в демонстрации: {str(e)}")
        print(f"❌ Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    demo_search()