from openai import OpenAI
from typing import Dict, Any, Optional
from config.settings import (
    OPENAI_API_KEY, 
    OPENAI_MODEL, 
    OPENAI_MAX_TOKENS, 
    OPENAI_TEMPERATURE,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE
)
from src.utils import log_message, truncate_text


class AIGenerator:
    def __init__(self):
        if not OPENAI_API_KEY:
            log_message("OPENAI_API_KEY не найден!", 'error')
            self.client = None
        else:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
        
        self.model = OPENAI_MODEL
        self.max_tokens = OPENAI_MAX_TOKENS
        self.temperature = OPENAI_TEMPERATURE
        self.system_prompt = SYSTEM_PROMPT
        self.user_template = USER_PROMPT_TEMPLATE

    def generate_post(self, news: Dict[str, Any]) -> Optional[str]:
        """
        Генерирует пост для Telegram на основе новости
        """
        if not self.client:
            log_message("OpenAI клиент не инициализирован", 'error')
            return None
        
        try:
            # Подготовка данных
            title = news.get('title', '')
            description = news.get('description', '')
            source = news.get('source', 'Unknown')
            
            # Обрезаем описание если слишком длинное
            description = truncate_text(description, 500)
            
            # Формируем запрос
            user_prompt = self.user_template.format(
                title=title,
                source=source,
                description=description
            )
            
            log_message(f"Генерация поста для: {title[:50]}...")
            
            # Запрос к API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Извлечение текста
            post_text = response.choices[0].message.content.strip()
            
            if not post_text:
                log_message("Пустой ответ от OpenAI", 'warning')
                return None
            
            log_message(f"Пост сгенерирован, длина: {len(post_text)} символов")
            return post_text
            
        except Exception as e:
            log_message(f"Ошибка при генерации поста: {e}", 'error')
            return None
    
    def generate_daily_digest(self, news_list: list) -> Optional[str]:
        """
        Генерирует дайджест из нескольких новостей (для ручного запуска)
        """
        if not self.client or not news_list:
            return None
        
        try:
            # Собираем краткое содержание всех новостей
            summary = "Вот главные новости крипторынка за сегодня:\n\n"
            for i, news in enumerate(news_list[:5], 1):
                title = news.get('title', '')
                description = news.get('description', '')[:200]
                summary += f"{i}. {title}\n   {description}...\n\n"
            
            prompt = f"""
            Сделай дайджест криптоновостей за сегодня на основе этого списка.
            Напиши вступление и краткое описание каждой новости.
            Используй дружелюбный и экспертный тон.
            
            {summary}
            
            Формат:
            1. Вступление (2-3 предложения о состоянии рынка)
            2. Каждая новость - отдельный абзац с эмодзи
            3. Заключение с прогнозом на завтра
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты крипто-аналитик. Делай краткие, но информативные дайджесты."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            log_message(f"Ошибка при генерации дайджеста: {e}", 'error')
            return None
