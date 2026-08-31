import os

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# News API (бесплатный ключ с newsapi.org)
NEWS_API_KEY = os.getenv('NEWS_API_KEY')

# История отправленных новостей
HISTORY_FILE = 'data/history.json'

# RSS ленты криптоновостей (бесплатные)
RSS_FEEDS = [
    'https://cointelegraph.com/rss',
    'https://cryptopotato.com/feed',
    'https://ambcrypto.com/feed',
    'https://bitcoinist.com/feed',
    'https://coingape.com/feed',
    'https://www.newsbtc.com/feed',
    'https://cryptonews.net/feed/',
]

# Ключевые слова для фильтрации (только важные новости)
KEYWORDS = [
    'bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'sol',
    'xrp', 'cardano', 'ada', 'dogecoin', 'doge',
    'binance', 'coinbase', 'sec', 'etf', 'bullrun',
    'crypto', 'blockchain', 'web3', 'defi', 'nft',
    'token', 'coin', 'market', 'price', 'prediction',
    'analysis', 'update', 'launch', 'partnership', 'investment',
    'regulation', 'adoption', 'mining', 'staking', 'yield',
    'breakout', 'correction', 'rally', 'crash', 'pump'
]

# Исключаем спамные слова (рекламные проекты)
STOP_WORDS = [
    'sponsored', 'press release', 'advertorial', 'partner post',
    'promotion', 'giveaway', 'bonus', 'referral'
]

# Промпт для OpenAI
SYSTEM_PROMPT = """Ты профессиональный крипто-журналист и SMM-менеджер. 
Твоя задача — превращать сухие новости в увлекательные посты для Telegram-канала.

Правила написания:
1. Пиши на русском языке, но сохраняй английские названия токенов и проектов
2. Используй эмодзи для визуального выделения (но не перебарщивай, максимум 3-4 штуки)
3. Структура поста:
   - Заголовок: яркий и кликбейтный (но без лжи)
   - Основной текст: суть новости своими словами, кратко и понятно
   - Вывод: что это значит для рынка (1-2 предложения)
4. Добавь хештеги: #криптовалюта #биткоин и другие по теме
5. Если новость негативная — не паникуй, подай как возможность для покупки
6. Если новость позитивная — подогрей интерес, но без фанатизма

Длина поста: 300-500 символов (оптимально для Telegram)
"""

USER_PROMPT_TEMPLATE = """
Вот сырая новость с крипторынка:

Название: {title}
Источник: {source}
Описание: {description}

Сделай из этого крутой пост для Telegram-канала по правилам, которые я тебе дал.
"""

# Настройки OpenAI
OPENAI_MODEL = 'gpt-3.5-turbo'  # Можно заменить на gpt-4 если есть бюджет
OPENAI_MAX_TOKENS = 500
OPENAI_TEMPERATURE = 0.8

# Лимиты
MAX_POSTS_PER_RUN = 5  # Максимум постов за один запуск
MIN_NEWS_FOR_POST = 1  # Минимум новостей чтобы начать пост
