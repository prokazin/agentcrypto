import requests
import json
from typing import Dict, Any, Optional
from config.settings import (
    OPENAI_API_KEY,
    DEEPSEEK_API_KEY,
    OPENAI_MODEL,
    DEEPSEEK_MODEL,
    OPENAI_MAX_TOKENS,
    OPENAI_TEMPERATURE,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE
)
from src.utils import log_message, truncate_text


class AIGenerator:
    def __init__(self):
        # Приоритет: DeepSeek (бесплатный), потом OpenAI
        self.use_deepseek = bool(DEEPSEEK_API_KEY)
        
        if self.use_deepseek:
            log_message("Используется DeepSeek API (бесплатный)")
            self.api_key = DEEPSEEK_API_KEY
            self.model = DEEPSEEK_MODEL
            self.api_url = "https://api.deepseek.com/v1/chat/completions"
        elif OPENAI_API_KEY:
            log_message("Используется OpenAI API")
            self.api_key = OPENAI_API_KEY
            self.model = OPENAI_MODEL
            self.api_url = "https://api.openai.com/v1/chat/completions"
        else:
            log_message("⚠️ Нет API ключей! Будет использован режим шаблонов", 'warning')
            self.api_key = None
            self.model = None
            self.api_url = None
        
        self.max_tokens = OPENAI_MAX_TOKENS
        self.temperature = OPENAI_TEMPERATURE
        self.system_prompt = SYSTEM_PROMPT
        self.user_template = USER_PROMPT_TEMPLATE

    def generate_post(self, news: Dict[str, Any]) -> Optional[str]:
        """
        Генерирует пост для Telegram на русском языке
        """
        # Если нет API - используем шаблонный режим
        if not self.api_key:
            return self.generate_template_post(news)
        
        try:
            # Подготовка данных
            title = news.get('title', '')
            description = news.get('description', '')
            source = news.get('source', 'Unknown')
            date = news.get('published', '')
            
            # Обрезаем описание
            description = truncate_text(description, 600)
            
            # Формируем запрос
            user_prompt = self.user_template.format(
                title=title,
                source=source,
                date=date,
                description=description
            )
            
            log_message(f"Генерация поста для: {title[:50]}...")
            
            # Подготовка payload
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Отправка запроса
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                post_text = result['choices'][0]['message']['content'].strip()
                
                if not post_text:
                    log_message("Пустой ответ от API", 'warning')
                    return self.generate_template_post(news)
                
                log_message(f"✅ Пост сгенерирован, длина: {len(post_text)} символов")
                return post_text
            else:
                log_message(f"Ошибка API: {response.status_code} - {response.text}", 'error')
                # Если API не работает - используем шаблон
                return self.generate_template_post(news)
                
        except Exception as e:
            log_message(f"Ошибка при генерации поста: {e}", 'error')
            return self.generate_template_post(news)
    
    def generate_template_post(self, news: Dict[str, Any]) -> str:
        """
        Генерация поста по шаблону (без API)
        """
        title = news.get('title', '')
        description = news.get('description', '')
        source = news.get('source', 'Unknown')
        date = news.get('published', '')
        
        # Убираем лишние пробелы
        description = ' '.join(description.split())[:300]
        
        # Определяем эмодзи в зависимости от содержания
        emoji = self.detect_emoji(title + description)
        
        post = f"""{emoji} **{title}**

{description}

📊 **Вывод:** Рынок продолжает развиваться, следим за ситуацией. Не забывайте про управление рисками!

📌 Источник: {source}
📅 {date}

#криптовалюта #биткоин #новости #аналитика #трейдинг
"""
        return post
    
    def detect_emoji(self, text: str) -> str:
        """Определяет эмодзи по содержанию новости"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['рост', 'вырос', 'повышение', 'рекорд', 'максимум']):
            return '🚀'
        elif any(word in text_lower for word in ['падение', 'упал', 'снижение', 'минимум', 'коррекция']):
            return '📉'
        elif any(word in text_lower for word in ['обновление', 'апгрейд', 'запуск', 'новый']):
            return '🆕'
        elif any(word in text_lower for word in ['sec', 'регулирование', 'закон', 'суд']):
            return '⚖️'
        elif any(word in text_lower for word in ['партнерство', 'сотрудничество', 'инвестиция']):
            return '🤝'
        elif any(word in text_lower for word in ['биткоин', 'bitcoin', 'btc']):
            return '₿'
        elif any(word in text_lower for word in ['эфириум', 'ethereum', 'eth']):
            return '⟠'
        else:
            return '📰'
