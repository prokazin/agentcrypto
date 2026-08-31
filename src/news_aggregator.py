import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import re
from datetime import datetime
from config.settings import RSS_FEEDS, ENGLISH_RSS_FEEDS, KEYWORDS, STOP_WORDS
from src.utils import filter_news_by_keywords, log_message, translate_text


class NewsAggregator:
    def __init__(self):
        self.feeds = RSS_FEEDS
        self.english_feeds = ENGLISH_RSS_FEEDS
        self.keywords = [kw.lower() for kw in KEYWORDS]
        self.stop_words = [sw.lower() for sw in STOP_WORDS]
        self.news_list = []

    def clean_text(self, text: str) -> str:
        """Очистка текста от HTML тегов и лишних пробелов"""
        if not text:
            return ''
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        # Удаляем лишние пробелы
        text = ' '.join(text.split())
        return text.strip()

    def is_russian(self, text: str) -> bool:
        """Проверяет, содержит ли текст кириллицу"""
        if not text:
            return False
        # Проверяем наличие русских букв
        russian_chars = re.findall(r'[а-яА-ЯёЁ]', text)
        return len(russian_chars) > 5  # Если больше 5 русских букв

    def parse_date(self, date_str: str) -> str:
        """Парсит дату в читаемый формат"""
        if not date_str:
            return datetime.now().strftime('%d.%m.%Y')
        try:
            # Попытка распарсить RSS дату
            from dateutil import parser
            dt = parser.parse(date_str)
            return dt.strftime('%d.%m.%Y %H:%M')
        except:
            return datetime.now().strftime('%d.%m.%Y')

    def fetch_from_rss(self, feed_url: str, is_russian: bool = True) -> List[Dict[str, Any]]:
        """
        Получение новостей из RSS-потока
        """
        news_items = []
        try:
            log_message(f"Парсинг RSS: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                log_message(f"Ошибка парсинга {feed_url}: {feed.bozo_exception}", 'warning')
                return []
            
            for entry in feed.entries[:15]:
                # Извлечение данных
                title = self.clean_text(entry.get('title', ''))
                link = entry.get('link', '')
                description = self.clean_text(entry.get('description', ''))
                published = entry.get('published', '')
                source = feed_url.split('/')[2]
                
                # Пропускаем пустые новости
                if not title or not description:
                    continue
                
                # Для английских новостей - проверяем что это крипто-новость
                if not is_russian:
                    # Проверяем наличие ключевых слов на английском
                    if not any(kw in title.lower() or kw in description.lower() for kw in ['bitcoin', 'crypto', 'ethereum', 'blockchain']):
                        continue
                
                # Фильтрация по ключевым словам (на русском или английском)
                if not self.filter_keywords(title, description):
                    continue
                
                # Проверка на стоп-слова
                if self.check_stop_words(title, description):
                    continue
                
                news_items.append({
                    'title': title,
                    'link': link,
                    'description': description[:800],
                    'published': self.parse_date(published),
                    'source': source,
                    'is_russian': is_russian,
                    'raw': entry
                })
                
        except Exception as e:
            log_message(f"Ошибка при парсинге {feed_url}: {e}", 'error')
        
        return news_items

    def filter_keywords(self, title: str, description: str) -> bool:
        """Фильтрация по ключевым словам (работает и на русском, и на английском)"""
        text = f"{title} {description}".lower()
        
        # Проверяем ключевые слова
        for keyword in self.keywords:
            if keyword.lower() in text:
                return True
        
        # Дополнительно проверяем английские варианты
        english_keywords = ['bitcoin', 'ethereum', 'crypto', 'blockchain', 'defi', 'nft', 'web3']
        for kw in english_keywords:
            if kw in text:
                return True
                
        return False

    def check_stop_words(self, title: str, description: str) -> bool:
        """Проверка на стоп-слова"""
        text = f"{title} {description}".lower()
        for stop in self.stop_words:
            if stop in text:
                return True
        return False

    def get_all_news(self) -> List[Dict[str, Any]]:
        """
        Сбор всех новостей из RSS-лент (русские и английские)
        """
        all_news = []
        
        # Сбор русских новостей
        for feed in self.feeds:
            news = self.fetch_from_rss(feed, is_russian=True)
            all_news.extend(news)
        
        # Сбор английских новостей (потом переведем)
        for feed in self.english_feeds:
            news = self.fetch_from_rss(feed, is_russian=False)
            all_news.extend(news)
        
        # Удаляем дубликаты по заголовку
        seen_titles = set()
        unique_news = []
        for news in all_news:
            title_hash = news['title'].lower().strip()
            if title_hash not in seen_titles:
                seen_titles.add(title_hash)
                unique_news.append(news)
        
        # Сортируем по дате (свежие сверху)
        unique_news.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        log_message(f"Собрано {len(unique_news)} уникальных новостей")
        return unique_news[:20]  # Берем только 20 последних
