import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Dict, Any
import re
import hashlib

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_history(file_path: str) -> List[str]:
    """Загружает историю отправленных новостей"""
    if not os.path.exists(file_path):
        logger.info(f"Файл истории {file_path} не найден, создаем новый")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                logger.warning("Неверный формат истории, сбрасываем")
                return []
    except Exception as e:
        logger.error(f"Ошибка загрузки истории: {e}")
        return []


def save_history(file_path: str, history: List[str]) -> bool:
    """Сохраняет историю отправленных новостей"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения истории: {e}")
        return False


def create_news_id(title: str, source: str) -> str:
    """Создает уникальный ID для новости"""
    text = f"{title}_{source}".lower().strip()
    # Удаляем все лишние символы для стабильности
    text = re.sub(r'[^a-zа-яё0-9]', '', text)
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def filter_news_by_keywords(title: str, description: str, keywords: List[str], stop_words: List[str]) -> bool:
    """Фильтрует новости по ключевым словам"""
    text = f"{title} {description}".lower()
    
    # Проверка на стоп-слова
    for stop in stop_words:
        if stop.lower() in text:
            return False
    
    # Проверка на ключевые слова
    for keyword in keywords:
        if keyword.lower() in text:
            return True
    
    return False


def truncate_text(text: str, max_length: int = 5000) -> str:
    """Обрезает текст до определенной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def log_message(message: str, level: str = 'info'):
    """Логирование сообщений"""
    if level == 'info':
        logger.info(message)
    elif level == 'warning':
        logger.warning(message)
    elif level == 'error':
        logger.error(message)
    else:
        logger.info(message)


def get_current_time() -> str:
    """Возвращает текущее время"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def translate_text(text: str, target_lang: str = 'ru') -> str:
    """
    Простая функция перевода (без API)
    Используется для английских новостей
    """
    # База простых переводов для крипто-терминов
    translations = {
        'bitcoin': 'биткоин',
        'ethereum': 'эфириум',
        'crypto': 'криптовалюта',
        'blockchain': 'блокчейн',
        'token': 'токен',
        'coin': 'монета',
        'market': 'рынок',
        'price': 'цена',
        'increase': 'рост',
        'decrease': 'падение',
        'high': 'максимум',
        'low': 'минимум',
        'investment': 'инвестиция',
        'investor': 'инвестор',
        'trading': 'трейдинг',
        'exchange': 'биржа',
        'wallet': 'кошелек',
        'mining': 'майнинг',
        'staking': 'стейкинг',
        'defi': 'дефи',
        'nft': 'нфт',
        'web3': 'веб3',
        'update': 'обновление',
        'launch': 'запуск',
        'partnership': 'партнерство',
        'regulation': 'регулирование',
        'sec': 'SEC',
        'etf': 'ETF',
        'bull': 'бычий',
        'bear': 'медвежий',
        'rally': 'ралли',
        'crash': 'обвал',
        'pump': 'памп',
        'dump': 'дамп',
    }
    
    # Простая замена слов (для крипто-новостей достаточно)
    for eng, rus in translations.items():
        text = text.replace(eng, rus)
        text = text.replace(eng.capitalize(), rus.capitalize())
    
    return text
