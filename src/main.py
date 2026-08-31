#!/usr/bin/env python3
"""
Главный скрипт агента для ведения Telegram-канала о криптовалютах.
Запускается через GitHub Actions каждые 20 минут.
"""

import sys
import os
import time
from typing import List, Dict, Any

# Добавляем путь к корневой папке
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import (
    load_history, save_history, create_news_id, 
    log_message, get_current_time
)
from src.news_aggregator import NewsAggregator
from src.ai_generator import AIGenerator
from src.telegram_sender import TelegramSender
from config.settings import MAX_POSTS_PER_RUN, HISTORY_FILE


class CryptoTelegramAgent:
    def __init__(self):
        self.news_aggregator = NewsAggregator()
        self.ai_generator = AIGenerator()
        self.telegram = TelegramSender()
        self.history = load_history(HISTORY_FILE)
        self.posts_count = 0
        
        log_message(f"Агент запущен в {get_current_time()}")
        log_message(f"Найдено {len(self.history)} уже отправленных новостей")

    def is_news_sent(self, news_id: str) -> bool:
        """
        Проверяет, была ли новость уже отправлена
        """
        return news_id in self.history

    def mark_as_sent(self, news_id: str):
        """
        Отмечает новость как отправленную
        """
        self.history.append(news_id)
        # Сохраняем историю после каждого поста
        save_history(HISTORY_FILE, self.history)

    def process_news(self, news: Dict[str, Any]) -> bool:
        """
        Обрабатывает одну новость: генерирует пост и отправляет
        """
        # Создаем ID новости
        news_id = create_news_id(
            news.get('title', ''),
            news.get('source', '')
        )
        
        # Проверяем, не отправляли ли уже
        if self.is_news_sent(news_id):
            log_message(f"Новость уже отправлена: {news.get('title', '')[:50]}...")
            return False
        
        # Генерируем пост
        post_text = self.ai_generator.generate_post(news)
        if not post_text:
            log_message("Не удалось сгенерировать пост", 'warning')
            return False
        
        # Отправляем в Telegram
        success = self.telegram.send_message(post_text)
        
        if success:
            # Отмечаем как отправленное
            self.mark_as_sent(news_id)
            self.posts_count += 1
            log_message(f"✅ Пост опубликован! ({self.posts_count})")
            return True
        else:
            log_message("❌ Не удалось отправить пост", 'error')
            return False

    def run(self):
        """
        Основной цикл работы агента
        """
        # Проверяем подключение к Telegram
        if not self.telegram.test_connection():
            log_message("❌ Бот не подключен к Telegram, завершаем", 'error')
            return

        log_message("Начинаем сбор новостей...")
        
        # Собираем новости из RSS
        rss_news = self.news_aggregator.get_all_news()
        
        # Дополнительно из API (если есть ключ)
        api_news = self.news_aggregator.get_news_from_api()
        
        # Объединяем
        all_news = rss_news + api_news
        
        # Сортируем по дате (если есть)
        all_news.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        log_message(f"Всего получено новостей: {len(all_news)}")
        
        if not all_news:
            log_message("Нет новых новостей для публикации")
            return
        
        # Обрабатываем новости
        processed = 0
        for news in all_news:
            if self.posts_count >= MAX_POSTS_PER_RUN:
                log_message(f"Достигнут лимит постов ({MAX_POSTS_PER_RUN})")
                break
            
            # Добавляем небольшую задержку между постами
            if processed > 0:
                time.sleep(2)
            
            if self.process_news(news):
                processed += 1
        
        # Финальный отчет
        log_message(f"Завершено: опубликовано {self.posts_count} постов из {len(all_news)} новостей")
        
        # Если не было постов, сохраняем историю все равно
        if self.posts_count == 0:
            save_history(HISTORY_FILE, self.history)


def main():
    """
    Точка входа
    """
    try:
        agent = CryptoTelegramAgent()
        agent.run()
        log_message("Агент завершил работу")
        sys.exit(0)
    except KeyboardInterrupt:
        log_message("Агент остановлен пользователем", 'warning')
        sys.exit(0)
    except Exception as e:
        log_message(f"Критическая ошибка: {e}", 'error')
        sys.exit(1)


if __name__ == "__main__":
    main()
