#!/usr/bin/env python3
"""
Главный скрипт агента для ведения Telegram-канала о криптовалютах.
Запускается через GitHub Actions каждые 30 минут в рабочее время рынка.
"""

import sys
import os
import time
from typing import List, Dict, Any
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import (
    load_history, save_history, create_news_id,
    log_message, get_current_time
)
from src.news_aggregator import NewsAggregator
from src.ai_generator import AIGenerator
from src.telegram_sender import TelegramSender
from config.settings import (
    MAX_POSTS_PER_RUN,
    HISTORY_FILE,
    MARKET_OPEN_HOUR,
    MARKET_CLOSE_HOUR
)


class CryptoTelegramAgent:
    def __init__(self):
        self.news_aggregator = NewsAggregator()
        self.ai_generator = AIGenerator()
        self.telegram = TelegramSender()
        self.history = load_history(HISTORY_FILE)
        self.posts_count = 0
        
        # Проверка времени работы рынка
        self.is_market_hours = self.check_market_hours()
        
        log_message(f"🚀 Агент запущен в {get_current_time()}")
        log_message(f"📊 Найдено {len(self.history)} уже отправленных новостей")
        log_message(f"⏰ Рынок {'активен' if self.is_market_hours else 'закрыт'}")

    def check_market_hours(self) -> bool:
        """Проверяет, сейчас рабочее время рынка"""
        current_hour = datetime.now().hour
        return MARKET_OPEN_HOUR <= current_hour < MARKET_CLOSE_HOUR

    def is_news_sent(self, news_id: str) -> bool:
        """Проверяет, была ли новость уже отправлена"""
        return news_id in self.history

    def mark_as_sent(self, news_id: str):
        """Отмечает новость как отправленную"""
        self.history.append(news_id)
        save_history(HISTORY_FILE, self.history)

    def process_news(self, news: Dict[str, Any]) -> bool:
        """Обрабатывает одну новость"""
        news_id = create_news_id(
            news.get('title', ''),
            news.get('source', '')
        )
        
        if self.is_news_sent(news_id):
            log_message(f"⏭️ Новость уже отправлена: {news.get('title', '')[:50]}...")
            return False
        
        post_text = self.ai_generator.generate_post(news)
        if not post_text:
            log_message("❌ Не удалось сгенерировать пост", 'warning')
            return False
        
        success = self.telegram.send_message(post_text)
        
        if success:
            self.mark_as_sent(news_id)
            self.posts_count += 1
            log_message(f"✅ Пост опубликован! ({self.posts_count}/{MAX_POSTS_PER_RUN})")
            return True
        else:
            log_message("❌ Не удалось отправить пост", 'error')
            return False

    def run(self):
        """Основной цикл работы агента"""
        # Проверяем время
        if not self.is_market_hours:
            log_message("⏰ Рынок закрыт, пропускаем запуск")
            return

        # Проверяем Telegram
        if not self.telegram.test_connection():
            log_message("❌ Бот не подключен к Telegram, завершаем", 'error')
            return

        log_message("📡 Начинаем сбор новостей...")
        
        # Собираем новости
        all_news = self.news_aggregator.get_all_news()
        
        log_message(f"📰 Всего получено новостей: {len(all_news)}")
        
        if not all_news:
            log_message("📭 Нет новых новостей для публикации")
            return
        
        # Обрабатываем новости
        processed = 0
        for news in all_news:
            if self.posts_count >= MAX_POSTS_PER_RUN:
                log_message(f"⏹️ Достигнут лимит постов ({MAX_POSTS_PER_RUN})")
                break
            
            if processed > 0:
                time.sleep(3)  # Пауза между постами
            
            if self.process_news(news):
                processed += 1
        
        # Финальный отчет
        log_message(f"📊 Завершено: опубликовано {self.posts_count} постов из {len(all_news)} новостей")
        
        if self.posts_count == 0:
            save_history(HISTORY_FILE, self.history)


def main():
    """Точка входа"""
    try:
        agent = CryptoTelegramAgent()
        agent.run()
        log_message("✅ Агент завершил работу")
        sys.exit(0)
    except KeyboardInterrupt:
        log_message("⏹️ Агент остановлен пользователем", 'warning')
        sys.exit(0)
    except Exception as e:
        log_message(f"💥 Критическая ошибка: {e}", 'error')
        sys.exit(1)


if __name__ == "__main__":
    main()
