import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from config.settings import RSS_FEEDS, KEYWORDS, STOP_WORDS
from src.utils import filter_news_by_keywords, log_message


class NewsAggregator:
    def __init__(self):
        self.feeds = RSS_FEEDS
        self.keywords = KEYWORDS
        self.stop_words = STOP_WORDS
        self.news_list = []

    def fetch_from_rss(self, feed_url: str) -> List[Dict[str, Any]]:
        """
        Получение новостей из одного RSS-потока
        """
        news_items = []
        try:
            log_message(f"Парсинг RSS: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:  # Ошибка парсинга
                log_message(f"Ошибка парсинга {feed_url}: {feed.bozo_exception}", 'warning')
                return []
            
            for entry in feed.entries[:10]:  # Берем только 10 последних
                # Извлечение данных
                title = entry.get('title', '').strip()
                link = entry.get('link', '')
                description = entry.get('description', '').strip()
                published = entry.get('published', '')
                source = feed_url.split('/')[2]  # Домен источника
                
                # Очистка HTML из описания
                if description:
                    soup = BeautifulSoup(description, 'html.parser')
                    description = soup.get_text().strip()
                
                # Пропускаем пустые новости
                if not title or not description:
                    continue
                
                # Фильтрация по ключевым словам
                if not filter_news_by_keywords(title, description, self.keywords, self.stop_words):
                    continue
                
                news_items.append({
                    'title': title,
                    'link': link,
                    'description': description[:1000],  # Обрезаем до 1000 символов
                    'published': published,
                    'source': source,
                    'raw': entry
                })
                
        except Exception as e:
            log_message(f"Ошибка при парсинге {feed_url}: {e}", 'error')
        
        return news_items

    def get_all_news(self) -> List[Dict[str, Any]]:
        """
        Сбор всех новостей из всех RSS-лент
        """
        all_news = []
        
        for feed in self.feeds:
            news = self.fetch_from_rss(feed)
            all_news.extend(news)
        
        # Удаляем дубликаты по заголовку
        seen_titles = set()
        unique_news = []
        for news in all_news:
            title_hash = news['title'].lower().strip()
            if title_hash not in seen_titles:
                seen_titles.add(title_hash)
                unique_news.append(news)
        
        log_message(f"Собрано {len(unique_news)} уникальных новостей")
        return unique_news
    
    def get_news_from_api(self) -> List[Dict[str, Any]]:
        """
        Дополнительный метод для получения новостей через NewsAPI (если есть ключ)
        """
        import os
        from config.settings import NEWS_API_KEY
        
        if not NEWS_API_KEY:
            return []
        
        try:
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': 'cryptocurrency OR bitcoin OR ethereum',
                'language': 'en',
                'sortBy': 'publishedAt',
                'apiKey': NEWS_API_KEY,
                'pageSize': 20
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                news_items = []
                for article in data.get('articles', []):
                    title = article.get('title', '').strip()
                    description = article.get('description', '').strip()
                    
                    if not title or not description:
                        continue
                    
                    if not filter_news_by_keywords(title, description, self.keywords, self.stop_words):
                        continue
                    
                    news_items.append({
                        'title': title,
                        'link': article.get('url', ''),
                        'description': description[:1000],
                        'published': article.get('publishedAt', ''),
                        'source': article.get('source', {}).get('name', 'NewsAPI'),
                        'raw': article
                    })
                
                log_message(f"Получено {len(news_items)} новостей из NewsAPI")
                return news_items
            else:
                log_message(f"Ошибка NewsAPI: {response.status_code}", 'warning')
                
        except Exception as e:
            log_message(f"Ошибка при запросе к NewsAPI: {e}", 'error')
        
        return []
