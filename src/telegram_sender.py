import requests
from typing import Optional
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.utils import log_message


class TelegramSender:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
        if not self.token or not self.chat_id:
            log_message("Telegram токен или chat_id не найден!", 'error')
            self.available = False
        else:
            self.available = True

    def send_message(self, text: str, parse_mode: str = 'HTML') -> bool:
        """
        Отправка сообщения в Telegram
        """
        if not self.available:
            log_message("Telegram не доступен", 'error')
            return False
        
        try:
            # Проверка длины сообщения (Telegram лимит - 4096 символов)
            if len(text) > 4096:
                text = text[:4000] + "\n\n... (сообщение обрезано)"
            
            # Замена Markdown на HTML если нужно
            # Telegram поддерживает HTML теги
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                log_message("Сообщение успешно отправлено")
                return True
            else:
                log_message(f"Ошибка отправки: {response.status_code} - {response.text}", 'error')
                return False
                
        except Exception as e:
            log_message(f"Ошибка при отправке в Telegram: {e}", 'error')
            return False
    
    def send_markdown(self, text: str) -> bool:
        """
        Отправка сообщения с Markdown (поддерживается Telegram)
        """
        # Telegram поддерживает MarkdownV2
        # Экранируем специальные символы
        import re
        special_chars = r'[_*[\]()~`>#+\-=|{}.!]'
        text = re.sub(special_chars, r'\\\g<0>', text)
        
        return self.send_message(text, parse_mode='MarkdownV2')
    
    def send_with_buttons(self, text: str, buttons: list) -> bool:
        """
        Отправка сообщения с инлайн-кнопками
        """
        if not self.available:
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            
            # Создаем клавиатуру
            keyboard = {
                'inline_keyboard': [
                    [{'text': btn['text'], 'url': btn['url']} for btn in row]
                    for row in buttons
                ]
            }
            
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML',
                'reply_markup': keyboard,
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            log_message(f"Ошибка отправки с кнопками: {e}", 'error')
            return False
    
    def test_connection(self) -> bool:
        """
        Тестирование подключения к Telegram Bot API
        """
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    log_message(f"Бот подключен: @{data['result']['username']}")
                    return True
            return False
        except Exception as e:
            log_message(f"Ошибка подключения к Telegram: {e}", 'error')
            return False
